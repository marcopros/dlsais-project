import asyncio
import json
import uuid
import logging
from typing import AsyncIterable, Any, Union

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

# Setup basic logging to help debug and trace execution flow
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
            task = self.tasks[task_id]
            if status:
                task.status = status
            if history:
                task.history = history
            if artifacts:
                task.artifacts = artifacts
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
                    response = next(
                        p.function_response.model_dump()
                        for p in event.content.parts
                    )
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
                elif (event.content and event.content.parts and any([True for p in event.content.parts if p.function_response])):
                    update = next(
                        p.function_response.model_dump()
                        for p in event.content.parts
                    )
                yield {
                    'is_task_complete': False,
                    'updates': update,
                }


    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle non-streaming task submission.

        Args:
            request: The A2A send task request.

        Returns:
            Task response with the agent's answer.
        """
        logger.info(f"Handling send task request: {request.params.id}")

        try:
            # Extract the last message content from the user
            message_content = request.params.message.parts[0].text
            session_id = request.params.sessionId

            # Invoke the agent to get a response
            response_text = await self.invoke(message_content, session_id)
            
            # Create a task status with the 'completed' state
            task_status = TaskStatus(
                state=TaskState.COMPLETED,
                message=Message(
                    role="agent",
                    parts=[TextPart(type="text", text=response_text)]
                )
            )

            # Create a full task response
            task = self._create_or_update_task(
                task_id=request.params.id,
                session_id=session_id,
                status=task_status,
                history=[request.params.message]  # Add the user message to history
            )

            logger.info(f"Task completed: {request.params.id}")
            return SendTaskResponse(
                id=request.id,
                result=task
            )

        except Exception as e:
            logger.error(f"Error processing task: {e}")
            return SendTaskResponse(
                id=request.id,
                error=self._create_error_response(e)
            )


    async def on_send_task_subscribe(self, request: SendTaskStreamingRequest) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        """
        Handle streaming task submission.

        Args:
            request: The A2A streaming task request.

        Returns:
            Either a stream of responses or an error response.
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

            # Start streaming response from the agent
            artifact_index = 0
            async for update in self.stream(message_content, session_id):
                if update.get('is_task_complete', False):
                    # Final response is ready
                    response_text = update.get('content', '')
                    
                    # Create completed task status
                    task_status = TaskStatus(
                        state=TaskState.COMPLETED,
                        message=Message(
                            role="agent",
                            parts=[TextPart(type="text", text=response_text)]
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
                    # Intermediate update
                    update_text = update.get('updates', '')
                    
                    # Create artifact for the intermediate update
                    artifact = Artifact(
                        name="intermediate_response",
                        parts=[TextPart(type="text", text=update_text)],
                        index=artifact_index,
                        lastChunk=False
                    )
                    
                    # Yield artifact update
                    yield SendTaskStreamingResponse(
                        id=request.id,
                        result=TaskArtifactUpdateEvent(
                            id=task_id,
                            artifact=artifact
                        )
                    )
                    
                    artifact_index += 1

        except Exception as e:
            logger.error(f"Error processing streaming task: {e}")
            # Per gli errori, non possiamo restituire direttamente nell'async generator,
            # quindi dobbiamo interrompere l'esecuzione o gestire l'errore diversamente
            # Yield un errore specifico dell'evento
            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(
                    id=task_id if 'task_id' in locals() else request.params.id,
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