import asyncio
import json
from operator import call
import uuid
import logging
from typing import AsyncIterable, Any

from agents import Agent, Runner, trace

from .session import SessionService, SessionSettings
from .agent import DiagnosisAgentOut, DiagnosisContext

from agents import (
    Agent, 
    Runner, 
    trace,
    TResponseInputItem,
)

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


def extract_agent_message(task_result):
    try:
        # Verifica se ci sono artifacts con testo
        artifacts = getattr(task_result.result, "artifacts", [])
        for artifact in artifacts:
            if hasattr(artifact, "text") and artifact.text:
                return artifact.text

        # Se non ci sono artifacts validi, passa allo status.message
        status = getattr(task_result.result, "status", None)
        if (
            status and
            hasattr(status, "message") and
            status.message and
            hasattr(status.message, "parts") and
            status.message.parts
        ):
            return status.message.parts[0].text

        return "[NESSUN MESSAGGIO RICEVUTO]"

    except Exception as e:
        return f"[ERRORE ESTRAZIONE]: {type(e).__name__} - {e}"


async def validate_diagnosis_output(output: DiagnosisAgentOut):
    """
    Validates that required diagnosis fields are present.
    Raises ValueError if any required field is missing.
    """
    required_fields = {
        "agent_response": output.agent_response,
        # "diagnosis": output.diagnosis,
        # "detected_problem_cause": output.detected_problem_cause,
        # "type_specialist": output.type_specialist,
    }

    missing = [field for field, value in required_fields.items() if value is None]
    if missing:
        raise ValueError(f"Missing required diagnosis fields: {missing}")
    return True


# Custom Task Manager for Diagnosis Agent
class DiagnosisAgentTaskManager(InMemoryTaskManager):
    """
    Custom Task Manager for handling tasks related to a diagnosis agent.
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
        self.input_items: list[TResponseInputItem] = []
        self.sessions = SessionService()
        self.context = DiagnosisContext(
            # search_for_diy_solution=False,
            # user_location=None,
            # user_diy_skills=None,
            # user_diy_tools=[],
            # home_type=None,
            # solution_preferences=None,
            # time_available_for_repair=None,
            # favourite_language="English",
            previous_agent_response="",
            diagnosis=None,
            detected_problem_cause=None,
            type_specialist=None,
            unlock_request_for_diy_solution=False,
            diy_solution=None,
            diy_links=[],
            call_professional=False
        )

        logger.info("DiagnosisAgentTaskManager initialized.")
    

    async def invoke(self, query, session_id) -> str:
        """
        Synchronously invoke the agent to get a final response for a given query and session.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Returns:
            Final response from the agent as a string.
        """
        logger.info(f"QUERY: {query}")
        # Retrieve or create a session based on session_id
        session = self.sessions.get_session(session_id)

        # If session is None, create a new session
        if session is None:
            logger.info(f"Session not found. Creating a new default session with ID: {session_id}")
            session = self.sessions.create_session(session_id)
        else:
            logger.info(f"Session found with ID: {session_id}") 
        
        print("***CONTEXT***")
        print(self.context.model_dump(exclude_none=True))
        
        # Run the agent synchronously with the user message and session
        with trace(f"Session {session_id}"):
            self.input_items.append({"content": query, "role": "user"})
            result = await Runner.run( self.agent, input=self.input_items, context=self.context )

        logger.info(f"RESULT: {result.final_output.model_dump(exclude_none=True)}")
        
        updated_context = DiagnosisContext(
            # search_for_diy_solution=session.search_for_diy_solution,
            # user_location=session.user_location,
            # user_diy_skills=session.user_diy_skills,
            # user_diy_tools=session.user_diy_tools,
            # home_type=session.home_type,
            # solution_preferences=session.solution_preferences,
            # time_available_for_repair=session.time_available_for_repair,
            # favourite_language=session.favourite_language,
            previous_agent_response=result.final_output.agent_response,
            diagnosis=result.final_output.diagnosis,
            detected_problem_cause=result.final_output.detected_problem_cause,
            type_specialist=result.final_output.type_specialist,
            unlock_request_for_diy_solution=result.final_output.unlock_request_for_diy_solution,
            diy_solution=result.final_output.diy_solution,
            diy_links=result.final_output.diy_links,
            call_professional=result.final_output.call_professional
        )
        
        self.context = updated_context
        
        # updated_session = SessionSettings(
        #     search_for_diy_solution=updated_context.search_for_diy_solution,
        #     user_location=updated_context.user_location,
        #     user_diy_skills=updated_context.user_diy_skills,
        #     user_diy_tools=updated_context.user_diy_tools,
        #     home_type=updated_context.home_type,
        #     solution_preferences=updated_context.solution_preferences,
        #     time_available_for_repair=updated_context.time_available_for_repair,
        #     favourite_language=updated_context.favourite_language
        # )
        
        # self.sessions.update_session(session_id, updated_session)
        
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
            yt_link = final_response.diy_links if final_response.diy_links else []

            part_summary = [{"type": "text", "text": summary}]
            part_data = [{"type": "data", "data": data}]


            # Check if the response is valid, else require more input 
            try:
                await validate_diagnosis_output(final_response)

            except ValueError as e:
                logger.error(f"Invalid diagnosis output: {e}")

                failed_task = await self.update_store(
                    task_id=task.id,
                    status=TaskStatus(state=TaskState.INPUT_REQUIRED, message=Message(role='agent', parts=part_summary, metadata={"data": data, "yt_links": yt_link})),
                    artifacts=[]
                )

                return SendTaskResponse(id=request.id, result=failed_task)
            
            # Update task as completed
            updated_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(state=TaskState.COMPLETED, message=Message(role='agent', parts=part_summary)),
                artifacts=[Artifact(parts=part_data, metadata={"data": data, "yt_links": yt_link})]
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

    