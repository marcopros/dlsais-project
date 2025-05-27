import os
import json
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Union, AsyncIterable

# Import common A2A types and components
from A2A.server.task_manager import InMemoryTaskManager
from A2A.types import (
    Task, TaskStatus, TaskState, Message, TextPart,
    DataPart, Artifact, SendTaskResponse, SendTaskStreamingResponse, TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent, JSONRPCResponse, JSONRPCError
)

# Import the query_agent function from the direct_agent module
from .direct_agent import query_agent

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AppointmentAgentTaskManager(InMemoryTaskManager):
    """
    Task manager per l'Appointment Agent che utilizza OpenRouter invece di Google ADK.
    Gestisce l'esecuzione dei task, l'orchestrazione delle richieste e la conversione 
    dei risultati in formato A2A.
    """
    
    def __init__(self, agent, runner, session_service, app_name, user_id):
        """
        Initializes the AppointmentAgentTaskManager.
        
        Args:
            agent: L'istanza dell'agente (conservato per retrocompatibilità)
            runner: Runner per il modello (conservato per retrocompatibilità)
            session_service: Servizio per la gestione delle sessioni
            app_name: Nome dell'applicazione
            user_id: ID utente default
        """
        self.agent = agent
        self.runner = runner
        self.session_service = session_service
        self.app_name = app_name
        self.user_id = user_id
        
        # Dizionario per memorizzare i task attivi
        self.tasks: Dict[str, Task] = {}
        
    async def process_task(self, task: Task) -> Task:
        """
        Elabora un task utilizzando l'ADK Runner.

        Args:
            task: Il task A2A da processare

        Returns:
            Il task aggiornato con lo stato e il risultato
        """
        try:
            # Find the latest user message from the task history
            user_message_content = None
            if task.history:
                for msg in reversed(task.history):
                    if msg.role == "user":
                        # Assuming the user message is text
                        text_parts = [p.text for p in msg.parts if hasattr(p, "text") and p.text]
                        if text_parts:
                            user_message_content = text_parts[0]
                            break

            if user_message_content is None:
                 # If no user message found, maybe it's a task update or initial request without message
                 # We might need to handle this case differently or assume a user message is always present for new tasks
                 # For now, let's assume a user message is required to trigger agent processing.
                 logger.warning(f"No user message found in task {task.id} history.")
                 # Return the task as is, or mark it as failed/completed based on expected behavior
                 return task # Or raise an error if a message is strictly required

            logger.info(f"Processing task {task.id} with user query: {user_message_content}")

            # Retrieve or create a session based on task.sessionId
            session = self.runner.session_service.get_session(
                app_name=self.app_name,
                user_id=self.user_id, # Using default user_id for now
                session_id=task.sessionId,
            )

            if session is None:
                logger.info(f"Session not found for task {task.id}. Creating a new session with ID: {task.sessionId}")
                session = self.runner.session_service.create_session(
                    app_name=self.app_name,
                    user_id=self.user_id, # Using default user_id for now
                    state={}, # Initial session state
                    session_id=task.sessionId,
                )
            else:
                logger.info(f"Session found for task {task.id} with ID: {task.sessionId}")


            # Wrap the user message in a types.Content object for the ADK Runner
            from google.genai import types
            user_content = types.Content(
                role='user', parts=[types.Part.from_text(text=user_message_content)]
            )

            # Run the agent asynchronously using the runner
            # The runner will handle the agent's logic, tool calls, and session state updates
            agent_response_events = []
            async for event in self.runner.run_async(
                user_id=self.user_id, # Using default user_id
                session_id=session.id,
                new_message=user_content,
            ):
                 agent_response_events.append(event)
                 # In a real streaming scenario, you would yield partial results here
                 # For this non-streaming process_task, we collect all events

            # Process the final event from the runner
            if not agent_response_events:
                logger.warning(f"ADK Runner for task {task.id} produced no events.")
                # Handle case where agent produces no response
                task.status.state = TaskState.COMPLETED
                task.status.message = Message(role="agent", parts=[TextPart(type="text", text="No response from agent.")])
                return task

            final_event = agent_response_events[-1]
            final_content = final_event.content

            # Convert the ADK Content response to A2A Message and Artifacts
            agent_message_parts = []
            artifacts_data = []

            if final_content and final_content.parts:
                for part in final_content.parts:
                    if part.text:
                        agent_message_parts.append(TextPart(type="text", text=part.text))
                    # Handle tool responses or structured data from the agent/tools
                    # The structure of tool responses depends on how the tools return data
                    # and how the agent processes it. Assuming tools might return structured data.
                    elif part.function_response:
                        # Assuming function_response contains structured data
                        try:
                             # The tool response is in part.function_response.response
                             # We need to check if this response contains the structured data we expect
                             # from tools like schedule_appointment
                             tool_response_data = part.function_response.response
                             # Example: Check if it's a dict and has a 'status' key
                             if isinstance(tool_response_data, dict) and 'status' in tool_response_data:
                                  artifacts_data.append(DataPart(type="data", data=tool_response_data))
                                  # Also add a text part for readability in the chat
                                  if 'message' in tool_response_data:
                                       agent_message_parts.append(TextPart(type="text", text=tool_response_data['message']))
                             else:
                                  # If not the expected structured data, represent it as text or generic data
                                  agent_message_parts.append(TextPart(type="text", text=f"Tool response: {json.dumps(tool_response_data)}"))
                        except Exception as e:
                            logger.error(f"Error processing tool response part for task {task.id}: {e}")
                            agent_message_parts.append(TextPart(type="text", text=f"Error processing tool response: {str(e)}"))
                    # Add other part types if necessary (e.g., file_data, etc.)

            # If no text parts generated by the agent, add a default message
            if not any(isinstance(part, TextPart) for part in agent_message_parts):
                 if artifacts_data:
                      # If there's structured data but no text, indicate data is available
                      agent_message_parts.append(TextPart(type="text", text="Processed request. Structured data available."))
                 else:
                      # Fallback if no meaningful output
                      agent_message_parts.append(TextPart(type="text", text="Task processed."))


            # Create A2A Message
            agent_message = Message(
                role="agent",
                parts=agent_message_parts
            )

            # Create A2A Artifacts if there is structured data
            artifacts = [Artifact(parts=artifacts_data, index=0)] if artifacts_data else []

            # Determine final task state based on agent's response or session state
            # This is a simplified logic; you might need more complex state management
            # based on the conversation flow (e.g., PENDING for waiting user input, COMPLETED after booking)
            # For now, let's assume process_task is called when the agent has a final response or action.
            final_state = TaskState.COMPLETED # Default to completed for now

            # Update the task status and artifacts
            task.status = TaskStatus(
                state=final_state,
                message=agent_message
            )
            task.artifacts = artifacts

            logger.info(f"Task {task.id} processed. Final state: {final_state}")
            return task

        except Exception as e:
            logger.error(f"Error processing task {task.id} with ADK Runner: {str(e)}", exc_info=True)
            # In case of error, return an error message
            error_message = Message(
                role="agent",
                parts=[TextPart(type="text", text=f"An error occurred during task processing: {str(e)}")]
            )
            task.status = TaskStatus(
                state=TaskState.FAILED, # Mark as failed
                message=error_message
            )
            task.history.append(error_message) # Add error message to history
            return task


    async def upsert_task(self, request) -> Task:
        """
        Crea o aggiorna un task.

        Args:
            request: Richiesta di creazione/aggiornamento task

        Returns:
            Il task creato o aggiornato
        """
        # If task ID is not provided, create a new one
        task_id = request.id if hasattr(request, 'id') and request.id else str(uuid.uuid4())

        # If session ID is not provided, create a new one
        session_id = request.sessionId if hasattr(request, 'sessionId') and request.sessionId else str(uuid.uuid4())

        # Retrieve existing task or create a new one
        task = self.tasks.get(task_id)
        if task is None:
             logger.info(f"Creating new task with ID: {task_id}")
             task = Task(
                 id=task_id,
                 sessionId=session_id,
                 status=TaskStatus(
                     state=TaskState.SUBMITTED,
                     message=None
                 ),
                 history=[],
                 artifacts=[],
                 metadata=None
             )
             self.tasks[task_id] = task
        else:
             logger.info(f"Updating existing task with ID: {task_id}")
             # Update existing task properties if provided in the request
             if hasattr(request, 'sessionId') and request.sessionId:
                  task.sessionId = request.sessionId
             if hasattr(request, 'status') and request.status:
                  task.status = request.status # This might overwrite state incorrectly if not careful
             if hasattr(request, 'artifacts') and request.artifacts:
                  task.artifacts = request.artifacts # This might overwrite artifacts incorrectly if not careful
             # Note: Merging history and artifacts might be more appropriate depending on A2A spec

        # Add new message to history if provided in the request
        if hasattr(request, 'message') and request.message:
             task.history.append(request.message)
             logger.info(f"Added new message to task {task_id} history.")


        # Don't automatically process tasks here - let the calling method handle processing
        # This avoids conflicts between automatic processing and manual processing
        logger.info(f"Task {task_id} created/updated. Processing will be handled by calling method.")

        return task




    async def get_task(self, id: str) -> Optional[Task]:
        """
        Ottiene un task dal suo ID.

        Args:
            id: ID del task

        Returns:
            Il task se trovato, altrimenti None
        """
        logger.info(f"Retrieving task with ID: {id}")
        return self.tasks.get(id)


    async def on_send_task(self, request) -> SendTaskResponse:
        """
        Handle non-streaming task submission.
        Processes the task and returns the final result.

        Args:
            request: Contains the task details.

        Returns:
            Response with updated task state and result.
        """
        logger.info(f"Received non-streaming task submission: {request.params.id}")

        # Create/update the task in the store
        task = await self.upsert_task(request.params)

        # Since this is non-streaming, we wait for the processing to complete
        # The _process_and_update_task function is already scheduled by upsert_task
        # We need a way to wait for it to finish.
        # A simple way for non-streaming is to call process_task directly here
        # instead of scheduling it in upsert_task, but that would duplicate logic.
        # A better way is to modify upsert_task to return the task and then
        # explicitly wait for its state to change in on_send_task.
        # However, the current structure of upsert_task schedules the processing
        # and returns immediately.

        # Let's simplify for now and call process_task directly here for non-streaming.
        # This means upsert_task should *not* schedule processing for non-streaming tasks.
        # We'll need to adjust upsert_task accordingly.

        # --- Adjustment: Modify upsert_task to NOT schedule processing for 'send' tasks ---
        # (This adjustment needs to be done in the apply_diff for upsert_task, assuming it's next)

        # For now, let's assume upsert_task just creates/updates the task without processing.
        # Process the task immediately for non-streaming requests
        try:
            processed_task = await self.process_task(task)
            # Update the task in the store after processing
            self.tasks[task.id] = processed_task

            return SendTaskResponse(id=request.id, result=processed_task)

        except Exception as e:
            logger.error(f"Error processing non-streaming task {task.id}: {str(e)}", exc_info=True)
            error_message = Message(
                role="agent",
                parts=[TextPart(type="text", text=f"An error occurred: {str(e)}")]
            )
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=error_message
            )
            self.tasks[task.id] = task # Update store with failed state
            return SendTaskResponse(id=request.id, result=task)


    async def on_send_task_subscribe(self, request) -> AsyncIterable[SendTaskStreamingResponse]:
        """
        Handle streaming task subscription. Streams updates back to the client.
        Uses the ADK Runner for asynchronous agent execution and streaming.

        Args:
            request: Streaming request with task info.

        Yields:
            Status updates and artifact changes as they happen.
        """
        logger.info(f"Subscribing to task stream: {request.params.id}")

        # Create/update the task in the store
        task = await self.upsert_task(request.params)

        try:
            # Find the latest user message from the task history
            user_message_content = None
            if task.history:
                for msg in reversed(task.history):
                    if msg.role == "user":
                        text_parts = [p.text for p in msg.parts if hasattr(p, "text") and p.text]
                        if text_parts:
                            user_message_content = text_parts[0]
                            break

            if user_message_content is None:
                logger.warning(f"No user message found in task {task.id} history for streaming.")
                # Yield an error or a completion event
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result=TaskStatusUpdateEvent(
                        id=task.id,
                        status=TaskStatus(state=TaskState.FAILED, message=Message(role="agent", parts=[TextPart(type="text", text="No user input for streaming.")])),
                        final=True
                    )
                )
                return # Stop the generator

            logger.info(f"Starting streaming processing for task {task.id} with user query: {user_message_content}")

            # Retrieve or create a session
            session = self.runner.session_service.get_session(
                app_name=self.app_name,
                user_id=self.user_id, # Using default user_id
                session_id=task.sessionId,
            )

            if session is None:
                logger.info(f"Session not found for task {task.id} streaming. Creating new session with ID: {task.sessionId}")
                session = self.runner.session_service.create_session(
                    app_name=self.app_name,
                    user_id=self.user_id, # Using default user_id
                    state={},
                    session_id=task.sessionId,
                )

            # Wrap user message for ADK Runner
            from google.genai import types
            user_content = types.Content(
                role='user', parts=[types.Part.from_text(text=user_message_content)]
            )

            # Use the ADK Runner's async streaming method
            full_agent_response_content = "" # To build the full text response
            artifacts_data = [] # To collect structured data for artifacts

            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=session.id,
                new_message=user_content,
            ):
                # Process each event from the runner
                if event.content and event.content.parts:
                    current_text_chunk = ""
                    current_artifacts_chunk_data = []

                    for part in event.content.parts:
                        if part.text:
                            current_text_chunk += part.text
                            full_agent_response_content += part.text # Accumulate for final message
                        elif part.function_response:
                            try:
                                 tool_response_data = part.function_response.response
                                 if isinstance(tool_response_data, dict) and 'status' in tool_response_data:
                                      current_artifacts_chunk_data.append(tool_response_data)
                                      artifacts_data.append(tool_response_data) # Accumulate for final artifacts
                                      # Optionally add a text representation of the tool response
                                      if 'message' in tool_response_data:
                                           current_text_chunk += f"\nTool response: {tool_response_data['message']}\n"
                            except Exception as e:
                                 logger.error(f"Error processing streamed tool response part for task {task.id}: {e}")
                                 current_text_chunk += f"\nError processing tool response: {str(e)}\n"

                    # Yield text updates as they arrive
                    if current_text_chunk:
                        yield SendTaskStreamingResponse(
                            id=request.id,
                            result=TaskStatusUpdateEvent(
                                id=task.id,
                                status=TaskStatus(
                                    state=TaskState.WORKING, # Or another appropriate intermediate state
                                    message=Message(role="agent", parts=[TextPart(type="text", text=current_text_chunk)])
                                ),
                                final=False # Not the final event
                            )
                        )

                    # Yield artifact updates if structured data is available
                    if current_artifacts_chunk_data:
                        # You might want to yield each artifact data chunk as a separate artifact update event
                        # or accumulate and send periodically/at the end.
                        # For simplicity now, let's accumulate and send a final artifact.
                        pass # Will handle artifacts at the end

            # After the runner stream is done, determine the final state and send final events

            # Determine final state based on the last event or session state
            final_state = TaskState.COMPLETED # Default final state
            # You might check the content of the last event or session state to refine this
            # Example: if the last event indicates waiting for user input, set state to INPUT_REQUIRED

            # Create the final agent message from accumulated text
            final_agent_message_parts = [TextPart(type="text", text=full_agent_response_content)] if full_agent_response_content else []

            # Add structured data to final artifacts
            final_artifacts = [Artifact(parts=[DataPart(type="data", data=data)], index=i) for i, data in enumerate(artifacts_data)]


            # Update the task in the store with the final state and content
            final_task_status = TaskStatus(
                state=final_state,
                message=Message(role="agent", parts=final_agent_message_parts)
            )
            task.status = final_task_status
            task.artifacts = final_artifacts # Set final artifacts
            task.history.append(final_task_status.message) # Add final message to history
            self.tasks[task.id] = task # Update the stored task

            logger.info(f"Streaming for task {task.id} finished. Final state: {final_state}. Yielding final events.")

            # Yield final artifact updates
            for artifact in final_artifacts:
                 yield SendTaskStreamingResponse(
                     id=request.id,
                     result=TaskArtifactUpdateEvent(
                         id=task.id,
                         artifact=artifact,
                     ),
                 )

            # Yield the final status update
            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(
                    id=task.id,
                    status=final_task_status,
                    final=True # This is the last event for this task
                )
            )

        except Exception as e:
            logger.error(f"Error during streaming task {task.id} with ADK Runner: {str(e)}", exc_info=True)
            # Yield an error event
            error_message = Message(
                role="agent",
                parts=[TextPart(type="text", text=f"An error occurred during streaming: {str(e)}")]
            )
            task.status = TaskStatus(
                state=TaskState.FAILED, # Mark as failed
                message=error_message
            )
            self.tasks[task.id] = task # Update the stored task state
            task.history.append(error_message) # Add error message to history

            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(
                    id=task.id,
                    status=task.status,
                    final=True # This is the last event
                )
            )
