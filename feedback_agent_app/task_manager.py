import asyncio
import json
import uuid
import logging
from typing import AsyncIterable, Any

# Google ADK imports for agent execution and session management
from agents import Agent, Runner, trace

#from .feedback_agent_app.session import SessionService
from feedback_agent_app.agent import feedback_agent, FeedbackOut
# help(Runner)                      # To see the available methods and attributes of the Runner class
# help(InMemorySessionService)      # To see the available methods and attributes of the InMemoryMemoryService class#

# Import common A2A server components and types
from A2A.types import (
    SendTaskResponse,
    SendTaskRequest,
    Message,
    Artifact,
    TextPart,
    TaskStatus,
    TaskState,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
)
from A2A.server.task_manager import InMemoryTaskManager

# Setup basic logging to help debug and trace execution flow
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def validate_diagnosis_output(output: FeedbackOut):
    """
    Validates that required diagnosis fields are present.
    Raises ValueError if any required field is missing.
    """
    
    required_fields={
        "jobTitle": output.jobTitle,
        "professional": output.professional,
        "date": output.date,
        "rating_scoring": output.rating_scoring,
        "tag_scoring": output.tag_scoring,
        "time_decay": output.time_decay,
        "sentiment_scoring": output.sentiment_scoring,
        "updated_trust_score": output.updated_trust_score,
    }

    missing = [field for field, value in required_fields.items() if value is None]
    if missing:
        raise ValueError(f"Missing required diagnosis fields: {missing}")
    return True


# Custom Task Manager for Diagnosis Agent
class FeedbackAgentTaskManager(InMemoryTaskManager):
    """
    Custom Task Manager for handling tasks related to a feedback agent.
    Manages sessions, invokes the agent, streams responses, and updates task status.
    """
    def __init__(self, agent: Agent):
        """
        Initialize the task manager with required dependencies.
        
        Args:
            agent: The agent that generates responses.
        """
        super().__init__()
        self.agent = agent
        # self.sessions = SessionService()
        logger.info("FeedbackAgentTaskManager initialized.")
    

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
        session = self.sessions.get_session(session_id)

        # If session is None, create a new session
        if session is None:
            logger.info(f"Session not found. Creating a new default session with ID: {session_id}")
            session = self.sessions.create_session(session_id)
        else:
            logger.info(f"Session found with ID: {session_id}") 
        
        
        # Run the agent synchronously with the user message and session
        with trace(f"Session {session_id}"):
            result = await Runner.run( self.agent, input=query, context=session )
        
        return result.final_output


    # TO DO
    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        """
        Stream partial results from the agent asynchronously.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Yields:
            Dictionary containing either intermediate updates or final response.
        """


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
            
            # Assume final_response is a DiagnosisAgentOut instance
            summary = final_response.agent_response
            data = final_response.model_dump()

            part_summary = [{"type": "text", "text": summary}]
            part_data = [{"type": "data", "data": data}]


            # Check if the response is valid, else require more input 
            try:
                await validate_diagnosis_output(final_response)
            except ValueError as e:
                logger.error(f"Invalid diagnosis output: {e}")
                error_message = Message(
                    role="agent",
                    parts=[TextPart(type="text", text=f"Analysis incomplete: {str(e)}")],
                )
                failed_task = await self.update_store(
                    task_id=task.id,
                    status=TaskStatus(state=TaskState.INPUT_REQUIRED, message=Message(role='agent', parts=part_summary)),
                    artifacts=[]
                )
                return SendTaskResponse(id=request.id, result=failed_task)
            
            # Update task as completed
            updated_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(state=TaskState.COMPLETED, message=Message(role='agent', parts=part_summary)),
                artifacts=[Artifact(parts=part_data)]
            )

            return SendTaskResponse(id=request.id, result=updated_task)

        except Exception as e:
            logger.error(f"Error while processing task {task.id}: {e}")

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

            # Aggiorna lo stato con errore
            failed_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(state=TaskState.FAILED, message=error_message),
                artifacts=[]
            )

            return SendTaskResponse(id=request.id, result=failed_task)


            
    # TO DO
    async def on_send_task_subscribe(self, request: SendTaskStreamingRequest) -> AsyncIterable[SendTaskStreamingResponse]:
        """
        Handle streaming task subscription. Streams updates back to the client.

        Args:
            request: Streaming request with task info.

        Yields:
            Status updates and artifact changes as they happen.
        """
        logger.info(f"Subscribing to task stream: {request.params.id}")

        # Create or retrieve the task
        task = await self.upsert_task(request.params)

        # Dummy status update — simulate starting the task
        yield SendTaskStreamingResponse(
            id=request.id,
            result={
                "id": task.id,
                "status": TaskStatus(state=TaskState.WORKING),
                "updates": {"message": "Task started (fake stream)"},
            },
        )

        # Simulate some processing delay
        await asyncio.sleep(1)

        # Dummy final update — simulate completion
        yield SendTaskStreamingResponse(
            id=request.id,
            result={
                "id": task.id,
                "status": TaskStatus(state=TaskState.COMPLETED),
                "artifacts": [Artifact(parts=[TextPart(type="text", text="Fake final response")])],
            },
        )

    