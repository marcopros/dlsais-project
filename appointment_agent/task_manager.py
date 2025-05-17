import asyncio
import json
import logging
import re
from typing import AsyncIterable, Any, Dict, Optional, List, Union

# Google ADK imports for agent execution and session management
from google.genai import types
from google.adk.runners import Runner
from google.adk.agents import Agent
from google.adk.sessions.in_memory_session_service import InMemorySessionService

# Import common A2A server components and types
from A2A.types import (
    SendTaskResponse,
    SendTaskRequest,
    Message,
    Artifact,
    TextPart,
    DataPart,
    TaskStatus,
    TaskState,
    TaskNotFoundError,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    JSONRPCResponse
)
from A2A.server.task_manager import InMemoryTaskManager

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Custom Task Manager for Appointment Agent
class AppointmentAgentTaskManager(InMemoryTaskManager):
    """
    Custom Task Manager for handling tasks related to an appointment agent.
    Manages sessions, invokes the agent, streams responses, and updates task status.
    """
    def __init__(self, agent: Agent, runner: Runner, session_service: InMemorySessionService, app_name: str, user_id: str):
        """
        Initialize the task manager with required dependencies.
        
        Args:
            agent: The agent that generates responses.
            runner: Used to run the agent logic.
            session_service: Manages conversation history per session.
            app_name: Name of the application (used for session tracking).
            user_id: ID of the current user (used for session tracking).
        """
        super().__init__()
        self.agent = agent
        self.runner = runner
        self.session_service = session_service
        self.app_name = app_name
        self.user_id = user_id
        logger.info("AppointmentAgentTaskManager initialized.")
    
    def extract_appointment_data(self, response_text: str) -> dict:
        """
        Extract appointment confirmation data from the response text.
        Expects a line in format: 
        "APPOINTMENT_CONFIRMED: appt_id USER: user_id PROFESSIONAL: professional_id"
        
        Args:
            response_text: The agent's response text.
            
        Returns:
            Dictionary with appointment_id, user_id and professional_id if found, empty dict otherwise.
        """
        # Use regex to find the confirmation line
        pattern = r"APPOINTMENT_CONFIRMED:\s*(\S+)\s*USER:\s*(\S+)\s*PROFESSIONAL:\s*(\S+)"
        match = re.search(pattern, response_text)
        
        if match:
            return {
                "appointment_id": match.group(1),
                "user_id": match.group(2),
                "professional_id": match.group(3),
                "status": "confirmed"
            }
        return {}
        
    def _create_or_update_task(self, task_id, session_id=None, status=None, history=None, artifacts=None):
        """
        Create or update a task with the given parameters.
        
        Args:
            task_id: ID of the task.
            session_id: ID of the session.
            status: Status of the task.
            history: Message history.
            artifacts: Artifacts associated with the task.
            
        Returns:
            The created or updated task.
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]  # task is a dictionary here
            if status:
                task['status'] = status  # Use dictionary key access
            if history:
                task['history'] = history  # Use dictionary key access
            if artifacts:
                task['artifacts'] = artifacts  # Use dictionary key access
            return task
        else:
            task = {
                "id": task_id,
                "sessionId": session_id,
                "status": status if status else TaskStatus(state=TaskState.PENDING),
                "history": history if history else [],
                "artifacts": artifacts if artifacts else []
            }
            self.tasks[task_id] = task
            return task
        
    def _create_error_response(self, error):
        """
        Create a JSON-RPC error response from an exception.
        
        Args:
            error: The exception to convert to an error response.
            
        Returns:
            A JSON-RPC error object.
        """
        message = str(error)
        code = -32603  # Internal error
        
        # Create a more specific error code based on the type of exception
        if isinstance(error, TaskNotFoundError):
            code = -32000
            
        return {
            "code": code,
            "message": message
        }

    async def invoke(self, query, session_id) -> str:
        """
        Synchronously invoke the agent to get a final response for a given query and session.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Returns:
            Final response from the agent as a string.
        """
        # Retrieve or create a session based on session_id
        session = self.runner.session_service.get_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=session_id,
        )

        # If session is None, create a new session
        if session is None:
            logger.info(f"Session not found. Creating a new session with ID: {session_id}")
            session = self.runner.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                state={},
                session_id=session_id,
            )
        else:
            logger.info(f"Session found with ID: {session_id}") 
        
        # Wrap the user message in a types.Content object (Format understandable by ADK Agent)
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=query)]
        )

        # Run the agent synchronously with the user message and session
        events = list(
            self.runner.run(
                user_id=self.user_id,
                session_id=session.id,
                new_message=content,
            )
        )

        # Check if the last event is a final response
        if not events or not events[-1].content or not events[-1].content.parts:
            return "Agent did not produce a final response."
        
        # Extract the text from the last event's content parts
        return '\n'.join([p.text for p in events[-1].content.parts if p.text])


    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        """
        Stream partial results from the agent asynchronously.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Yields:
            Dictionary containing either intermediate updates or final response.
        """
        # Retrieve or create a session based on session_id
        session = self.runner.session_service.get_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=session_id,
        )

        # If session is None, create a new session
        if session is None:
            logger.info(f"Session not found. Creating a new session with ID: {session_id}")
            session = self.runner.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                state={},
                session_id=session_id,
            )
        else:
            logger.info(f"Session found with ID: {session_id}") 
        
        # Wrap the user message in a types.Content object (Format understandable by ADK Agent)
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=query)]
        )

        # Run the agent asynchronously and process each event
        async for event in self.runner.run_async(
            user_id=self.user_id, session_id=session.id, new_message=content
        ):
            # Handle final response
            if event.is_final_response():
                response = ''
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = '\n'.join(
                        [p.text for p in event.content.parts if p.text]
                    )
                elif (event.content and event.content.parts and any([True for p in event.content.parts if p.function_response])):
                    try:
                        response = next(
                            p.function_response.model_dump()
                            for p in event.content.parts
                            if hasattr(p, 'function_response') and p.function_response
                        )
                    except (StopIteration, AttributeError) as e:
                        logger.error(f"Error extracting function response: {str(e)}")
                        response = {"status": "error", "error_message": "Failed to process agent response"}
                yield {
                    'is_task_complete': True,
                    'content': response,
                }
            # Handle intermediate updates
            else:
                update = ''
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    update = '\n'.join(
                        [p.text for p in event.content.parts if p.text]
                    )
                elif (event.content and event.content.parts and any([True for p in event.content.parts if hasattr(p, 'function_response') and p.function_response])):
                    try:
                        update = next(
                            p.function_response.model_dump()
                            for p in event.content.parts
                            if hasattr(p, 'function_response') and p.function_response
                        )
                    except (StopIteration, AttributeError) as e:
                        logger.error(f"Error extracting function response: {str(e)}")
                        update = {"status": "error", "error_message": "Failed to process agent response"}
                yield {
                    'is_task_complete': False,
                    'updates': update,
                }


    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle non-streaming task submission.

        Args:
            request: Contains the task details.

        Returns:
            Response with updated task state and result.
        """
        logger.info(f"Received task submission: {request.params.id}")

        # Save the task to the store
        task = await self.upsert_task(request.params)

        try:
            # Find the latest user message from the task
            user_message = "No input"
            if task.history:
                for msg in reversed(task.history):
                    if msg.role == "user":
                        if msg.parts and len(msg.parts) > 0 and isinstance(msg.parts[0], dict):
                            user_message = msg.parts[0].get("text", "No input")
                        elif hasattr(msg.parts[0], "text"):
                            user_message = msg.parts[0].text
                        break
            
            # Get the agent's response
            final_response_text = await self.invoke(user_message, task.sessionId)
            
            # Extract appointment data if present
            appointment_data = self.extract_appointment_data(final_response_text)
            
            # Create text part for the response
            text_part = TextPart(type="text", text=final_response_text)
            parts = [text_part]
            
            # Create artifacts with appointment data if available
            artifacts = []
            if appointment_data:
                data_part = DataPart(type="data", data=appointment_data)
                artifacts = [Artifact(parts=[data_part])]
                logger.info(f"Extracted appointment data from response: {appointment_data}")

            # Create a response message
            response_message = Message(
                role="agent",
                parts=parts
            )

            # Update task as completed
            updated_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(state=TaskState.COMPLETED, message=response_message),
                artifacts=artifacts
            )

            return SendTaskResponse(id=request.id, result=updated_task)

        except Exception as e:
            logger.error(f"Error while processing task {task.id}: {e}")
            
            # Create an error response
            error_message = Message(
                role="agent",
                parts=[TextPart(type="text", text=f"Error occurred: {str(e)}")]
            )
            
            # Update task as failed
            failed_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(state=TaskState.FAILED, message=error_message)
            )
            
            return SendTaskResponse(id=request.id, result=failed_task)


    async def on_send_task_subscribe(self, request: SendTaskStreamingRequest) -> AsyncIterable[SendTaskStreamingResponse]:
        """
        Handle streaming task submission.

        Args:
            request: The A2A streaming task request.

        Returns:
            A stream of responses.
        """
        logger.info(f"Handling streaming task request: {request.params.id}")

        try:
            # Extract the last message content from the user
            message_content = request.params.message.parts[0].text
            session_id = request.params.sessionId
            task_id = request.params.id

            # Create initial task status with 'working' state
            task_status = TaskStatus(
                state=TaskState.WORKING
            )

            # Initialize the task in the task store
            task = self._create_or_update_task(
                task_id=task_id,
                session_id=session_id,
                status=task_status,
                history=[request.params.message]
            )

            # Yield initial status update
            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(
                    id=task_id,
                    status=task_status,
                    final=False
                )
            )

            try:
                # Start streaming response from the agent
                async for update in self.stream(message_content, session_id):
                    if update.get('is_task_complete', False):
                        # Final response is ready
                        response_text = update.get('content', '')
                        
                        # Check if response is a dictionary and handle it
                        if isinstance(response_text, dict) and not isinstance(response_text, str):
                            # Get the status safely with a default
                            status_value = response_text.get('status', '')
                            
                            if status_value == 'error':
                                error_message = response_text.get('error_message', 'Unknown error occurred')
                                # Create error task status
                                task_status = TaskStatus(
                                    state=TaskState.FAILED,
                                    message=Message(
                                        role="agent",
                                        parts=[TextPart(type="text", text=error_message)]
                                    )
                                )
                            else:
                                # Format the response as a readable message
                                formatted_response = self._format_dict_response(response_text)
                                task_status = TaskStatus(
                                    state=TaskState.COMPLETED,
                                    message=Message(
                                        role="agent",
                                        parts=[TextPart(type="text", text=formatted_response)]
                                    )
                                )
                        else:
                            # Normal text response
                            task_status = TaskStatus(
                                state=TaskState.COMPLETED,
                                message=Message(
                                    role="agent",
                                    parts=[TextPart(type="text", text=str(response_text))]
                                )
                            )
                        
                        # Update task with final status
                        self._create_or_update_task(
                            task_id=task_id,
                            session_id=session_id,
                            status=task_status
                        )
                        
                        # Yield final status update
                        yield SendTaskStreamingResponse(
                            id=request.id,
                            result=TaskStatusUpdateEvent(
                                id=task_id,
                                status=task_status,
                                final=True
                            )
                        )
                    else:
                        # Intermediate update - no action needed at this time
                        pass
            except Exception as e:
                logger.error(f"Error processing streaming task: {str(e)}")
                # Create error task status
                task_status = TaskStatus(
                    state=TaskState.FAILED,
                    message=Message(
                        role="agent",
                        parts=[TextPart(type="text", text=f"Error: {str(e)}")]
                    )
                )
                
                # Update task with error status
                self._create_or_update_task(
                    task_id=task_id,
                    session_id=session_id,
                    status=task_status
                )
                
                # Yield error status update
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result=TaskStatusUpdateEvent(
                        id=task_id,
                        status=task_status,
                        final=True
                    )
                )

        except Exception as e:
            logger.error(f"Error setting up streaming task: {e}")
            # Generate error response
            error_response = JSONRPCResponse(
                id=request.id,
                error=self._create_error_response(e)
            )
            # Yield error as StreamingResponse instead of returning
            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(
                    id=request.params.id,
                    status=TaskStatus(
                        state=TaskState.FAILED,
                        message=Message(
                            role="agent",
                            parts=[TextPart(type="text", text=f"Error: {str(e)}")]
                        )
                    ),
                    final=True
                )
            )
    
    def _format_dict_response(self, response_dict: Dict[str, Any]) -> str:
        """
        Format a dictionary response into a readable string.
        
        Args:
            response_dict: The dictionary response from a tool.
            
        Returns:
            A formatted string representation of the dictionary.
        """
        if not isinstance(response_dict, dict):
            return str(response_dict)
        
        # Handle different response types based on status
        status = response_dict.get('status', '')
        
        if status == 'success':
            # Format successful appointment details
            if 'appointment_details' in response_dict:
                details = response_dict['appointment_details']
                return (
                    f"Appointment successfully scheduled!\n\n"
                    f"Date: {details.get('date', 'Not specified')}\n"
                    f"Time: {details.get('time', 'Not specified')}\n"
                    f"Issue: {details.get('issue', 'Not specified')}\n"
                    f"Location: {details.get('location', 'Not specified')}\n"
                    f"Notes: {details.get('notes', '')}"
                )
            # Format successful availability check
            elif 'available_slots' in response_dict:
                slots = response_dict.get('available_slots', [])
                if slots:
                    slots_text = "\n".join([f"- {slot}" for slot in slots[:10]])
                    remaining = len(slots) - 10 if len(slots) > 10 else 0
                    
                    result = f"Available slots:\n{slots_text}"
                    if remaining > 0:
                        result += f"\n...and {remaining} more options."
                    return result
                else:
                    return "No available slots found."
            else:
                # Generic success message
                return response_dict.get('message', 'Operation completed successfully.')
        
        elif status == 'error':
            # Format error message
            return f"Error: {response_dict.get('error_message', 'Unknown error occurred')}"
        
        elif status == 'warning':
            # Format warning message
            if 'appointment_details' in response_dict:
                details = response_dict['appointment_details']
                return (
                    f"Appointment scheduled with warning: {response_dict.get('message', '')}\n\n"
                    f"Date: {details.get('date', 'Not specified')}\n"
                    f"Time: {details.get('time', 'Not specified')}\n"
                    f"Issue: {details.get('issue', 'Not specified')}\n"
                    f"Location: {details.get('location', 'Not specified')}\n"
                    f"Notes: {details.get('notes', '')}"
                )
            else:
                return f"Warning: {response_dict.get('message', 'Unknown warning')}"
        
        # Default case: just return a JSON string of the dictionary
        return json.dumps(response_dict, indent=2) 