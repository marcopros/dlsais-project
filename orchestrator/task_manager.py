import asyncio
import json
import uuid
import logging
from typing import AsyncIterable, Any

# Google ADK imports for agent execution and session management
from google.genai import types
from google.adk.runners import Runner
from google.adk.agents import Agent

from persistent_memory.persistent_memory import MongoSessionService

# Import common A2A server components and types
from A2A.types import (
    SendTaskResponse,
    SendTaskRequest,
    Message,
    Artifact,
    TextPart,
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

# Import our custom human-readable logger
import orchestrator
from orchestrator.logging import human_readable_logger

# Setup basic logging to help debug and trace execution flow
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Custom Task Manager for Matching Agent
class OrchestratorTaskManager(InMemoryTaskManager):
    """
    Custom Task Manager for handling tasks related to the orchestrator.
    Manages sessions, invokes the agent, streams responses, and updates task status.
    """
    def __init__(self, agent: Agent, runner: Runner, session_service: MongoSessionService, app_name: str, user_id: str):
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
        logger.info("OrchestratorTaskManager initialized.")
    

    async def invoke(self, query, session_id) -> str:
        """
        Synchronously invoke the agent to get a final response for a given query and session.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Returns:
            Final response from the agent as a string.
        """
        # Log user query in human-readable format
        human_readable_logger.log_user_message(query)
        
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
        
        # Wrap the user message in a types.Content object ( Format understandable by ADK Agent)
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=query)]
        )

        # Let the user know the orchestrator is processing
        human_readable_logger.log_system_message("Processing your request...")

        # Run the agent synchronously with the user message and session
        events = list(
            self.runner.run(
                user_id=self.user_id,
                session_id=session.id,
                new_message=content,
            )
        )

        response = ""                    # Extract agent responses and log them
        agent_name = "Orchestrator"     # The name of the agent that is being called
        if events:
            for event in events:
                # Log function calls (agent interactions)
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            function_name = part.function_call.name
                            if function_name == "diagnosis_agent_send_task":
                                human_readable_logger.log_agent_call("Diagnosis Agent", part.function_call.args.get("message", ""))
                            elif function_name == "matching_agent_send_task":
                                human_readable_logger.log_agent_call("Matching Agent", part.function_call.args.get("message", ""))
                            elif function_name == "appointment_agent_send_task":
                                human_readable_logger.log_agent_call("Appointment Agent", part.function_call.args.get("message", ""))
                        
                        # Log function responses
                        if hasattr(part, 'function_response') and part.function_response:
                            function_name = part.function_response.name
                            if function_name == "diagnosis_agent_send_task":
                                agent_name = "Diagnosis Agent"
                                human_readable_logger.log_agent_response("Diagnosis Agent", part.function_response.response)
                            elif function_name == "matching_agent_send_task":
                                agent_name = "Matching Agent"
                                human_readable_logger.log_agent_response("Matching Agent", part.function_response.response)
                            elif function_name == "appointment_agent_send_task":
                                agent_name = "Appointment Agent"
                                human_readable_logger.log_agent_response("Appointment Agent", part.function_response.response)
                            elif function_name == "validate_diagnosis":
                                result = part.function_response.response.get("result", False)
                                human_readable_logger.log_system_message(f"Diagnosis validation: {'✅ Valid' if result else '❌ Invalid'}")
                        
                        # Log text responses
                        if hasattr(part, 'text') and part.text:
                            human_readable_logger.log_system_message(part.text)
                            response += part.text + "\n"

        # Check if the last event is a final response
        if not events or not events[-1].content or not events[-1].content.parts:
            human_readable_logger.log_system_message("Agent did not produce a final response.")
            return {'agent': agent_name, 'text':"Agent did not produce a final response."}
        
        # Extract the text from the last event's content parts
        return {'agent': agent_name, 'text':'\n'.join([p.text for p in events[-1].content.parts if p.text])}


    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        """
        Stream partial results from the agent asynchronously.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Yields:
            Dictionary containing either intermediate updates or final response.
        """
        # Log user query in human-readable format
        human_readable_logger.log_user_message(query)
        
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
        
        # Wrap the user message in a types.Content object ( Format understandable by ADK Agent)
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=query)]
        )

        # Let the user know the orchestrator is processing
        human_readable_logger.log_system_message("Processing your request...")

        # Run the agent asynchronously and process each event
        async for event in self.runner.run_async(
            user_id=self.user_id, session_id=session.id, new_message=content
        ):
            agent_name = "Orchestrator"    # The name of the agent that is being called  
            # Log function calls and responses
            if event.content and event.content.parts:
                for part in event.content.parts:
                    # Log function calls (agent interactions)
                    if hasattr(part, 'function_call') and part.function_call:
                        function_name = part.function_call.name
                        if function_name == "diagnosis_agent_send_task":
                            human_readable_logger.log_agent_call("Diagnosis Agent", part.function_call.args.get("message", ""))
                        elif function_name == "matching_agent_send_task":
                            human_readable_logger.log_agent_call("Matching Agent", part.function_call.args.get("message", ""))
                        elif function_name == "appointment_agent_send_task":
                            human_readable_logger.log_agent_call("Appointment Agent", part.function_call.args.get("message", ""))
                    
                    # Log function responses
                    if hasattr(part, 'function_response') and part.function_response:
                        function_name = part.function_response.name
                        if function_name == "diagnosis_agent_send_task":
                            agent_name = "Diagnosis Agent"
                            human_readable_logger.log_agent_response("Diagnosis Agent", part.function_response.response)
                        elif function_name == "matching_agent_send_task":
                            agent_name = "Matching Agent"
                            human_readable_logger.log_agent_response("Matching Agent", part.function_response.response)
                        elif function_name == "appointment_agent_send_task":
                            agent_name = "Appointment Agent"
                            human_readable_logger.log_agent_response("Appointment Agent", part.function_response.response)
                        elif function_name == "validate_diagnosis":
                            result = part.function_response.response.get("result", False)
                            human_readable_logger.log_system_message(f"Diagnosis validation: {'✅ Valid' if result else '❌ Invalid'}")
                    
                    # Log text responses
                    if hasattr(part, 'text') and part.text:
                        human_readable_logger.log_system_message(part.text)
            
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
                elif ( event.content and event.content.parts and any([True for p in event.content.parts if p.function_response])):
                    response = next(
                        p.function_response.model_dump()
                        for p in event.content.parts
                    )
                yield {
                    'is_task_complete': True,
                    'content': response,
                    'agent': agent_name,
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
                elif ( event.content and event.content.parts and any([True for p in event.content.parts if p.function_response])):
                    update = next(
                        p.function_response.model_dump()
                        for p in event.content.parts
                    )
                yield {
                    'is_task_complete': True,
                    'updates': update,
                    'agent': agent_name,
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
            # Find the latest user message from the task history
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
            final_response =  await self.invoke(user_message, task.sessionId)
            response_text = final_response['text']
            response_agent = final_response['agent']

            # Create a response message to store in the task
            response_message = Message(
                role="agent",
                parts=[
                    TextPart(
                        type="text",
                        text=response_text,
                        metadata={ "agent": response_agent }
                    )
                ],
                timestamp=int(asyncio.get_running_loop().time() * 1000),
                id=str(uuid.uuid4())
            )

            # Update task as completed
            updated_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(state=TaskState.COMPLETED, message=response_message),
                artifacts=[]
            )

            return SendTaskResponse(id=request.id, result=updated_task)

        except Exception as e:
            logger.error(f"Error while processing task {task.id}: {e}")
            human_readable_logger.log_system_message(f"❌ Error: {str(e)}")

            error_message = Message(
                role="agent",
                parts=[
                    TextPart(
                        type="text",
                        text=f"Error occurred during task processing: {str(e)}"
                    )
                ],
                timestamp=int(asyncio.get_running_loop().time() * 1000),
                id=str(uuid.uuid4())
            )

            # Update status with error
            failed_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(state=TaskState.FAILED, message=error_message),
                artifacts=[]
            )

            return SendTaskResponse(id=request.id, result=failed_task)


    
    async def on_send_task_subscribe(self, request: SendTaskStreamingRequest) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """
        Handle streaming task subscription. Streams updates back to the client.

        Args:
            request: Streaming request with task info.

        Yields:
            Status updates and artifact changes as they happen.
        """
        logger.info(f"Subscribing to task stream: {request.params.id}")
        
        # Salva il task
        task = await self.upsert_task(request.params)

        try:
            # Retrieve the latest user message
            user_message = "No input"
            if task.history:
                for msg in reversed(task.history):
                    if msg.role == "user":
                        if msg.parts and len(msg.parts) > 0 and isinstance(msg.parts[0], dict):
                            user_message = msg.parts[0].get("text", "No input")
                        elif hasattr(msg.parts[0], "text"):
                            user_message = msg.parts[0].text
                        break
            
            # Stream agent response
            async for item in self.stream(user_message, task.sessionId):
                is_task_complete = item.get('is_task_complete', False)

                if not is_task_complete:
                    task_state = TaskState.WORKING
                    parts = [{'type': 'text', 'text': item.get('updates', '')}]
                else:
                    content = item.get('content')  
                    if content is None:
                        logger.warning("Received stream item with no 'content'")
                        continue

                    if isinstance(content, dict):
                        if (
                            'response' in content
                            and 'result' in content['response']
                        ):
                            try:
                                data = json.loads(
                                    content['response']['result']
                                )
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to decode JSON response: {e}")
                                human_readable_logger.log_system_message(f"❌ Error decoding response: {str(e)}")
                                data = {"error": "Invalid JSON response"}
                            task_state = TaskState.INPUT_REQUIRED
                        else:
                            data = content
                            task_state = TaskState.COMPLETED
                        parts = [{'type': 'data', 'data': data}]
                    else:
                        task_state = TaskState.COMPLETED
                        parts = [{'type': 'text', 'text': str(content)}]
                    artifacts = [Artifact(parts=parts, index=0, append=False)]
            
            message = Message(role='agent', parts=parts)
            task_status = TaskStatus(state=task_state, message=message)
            
            await self.update_store(
                task.id, task_status, artifacts
            )

            task_update_event = TaskStatusUpdateEvent(
                id=task.id,
                status=task_status,
                final=False,
            )

            yield SendTaskStreamingResponse(
                id=request.id, result=task_update_event
            )

            # Now yield Artifacts too
            if artifacts:
                for artifact in artifacts:
                    yield SendTaskStreamingResponse(
                        id=request.id,
                        result=TaskArtifactUpdateEvent(
                            id=task.id,
                            artifact=artifact,
                        ),
                    )
            if is_task_complete:
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result=TaskStatusUpdateEvent(
                        id=task.id,
                        status=TaskStatus(
                            state=task_status.state,
                        ),
                        final=True,
                    ),
                )
        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            human_readable_logger.log_system_message(f"❌ Error while streaming response: {str(e)}")
            yield  JSONRPCResponse(id=request.id, error=TaskNotFoundError())

    