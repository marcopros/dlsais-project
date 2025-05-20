import asyncio
import json
import uuid
import logging
from typing import AsyncIterable, Any

# Import from agent.py instead of agent's framework
from .agent import FeedbackOut, query_agent

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


async def validate_feedback_output(output: FeedbackOut) -> bool:
    """
    Validates that required feedback fields are present.
    Raises ValueError if any required field is missing.
    """
    # Se type_specialist è presente, significa che abbiamo abbastanza informazioni
    # per procedere anche se alcuni campi sono null
    if output.updated_trust_score is not None:
        # Se abbiamo un punteggio di fiducia aggiornato, significa che abbiamo completato la procedura
        return True
    
    # Altrimenti, verifichiamo che tutti i campi richiesti siano presenti
    required_fields = {
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
        raise ValueError(f"Missing required FEEDBACK fields: {missing}")
    return True


# Custom Task Manager for Diagnosis Agent
class FeedbackAgentTaskManager(InMemoryTaskManager):
    """
    Custom Task Manager for handling tasks related to a feedback agent.
    Manages sessions, invokes the agent, streams responses, and updates task status.
    """
    def __init__(self, agent):
        """
        Initialize the task manager with required dependencies.
        
        Args:
            agent: The agent that generates responses.
        """
        super().__init__()
        self.agent = agent
        logger.info("FeedbackAgentTaskManager initialized.")
    

    async def invoke(self, query, session_id) -> FeedbackOut:
        """
        Invoke the agent to get a response for a given query and session.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Returns:
            A FeedbackOut instance with the agent's response.
        """
        logger.info(f"QUERY: {query}")
        
        # Retrieve or create a session based on session_id

        # ! NO SESSION MANAGEMENT
        
        try:
            # Call our direct OpenAI function (no ADK dependency)
            result = await query_agent(query)
            logger.info(f"RESULT TYPE: {type(result)}")
            return result
        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            # Return a fallback response
            return FeedbackOut(
                jobTitle="Non determinato",
                professional="Non determinato",
                date="Non determinato",
                rating_scoring=None,
                tag_scoring=None,
                time_decay=None,
                sentiment_scoring=None,
                updated_trust_score=None,
            )


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
            
            # # Aggiungi il messaggio dell'utente alla cronologia della sessione
            # self.sessions.add_message_to_history(task.sessionId, "user", user_message)
            
            # Get the agent's response
            final_response = await self.invoke(user_message, task.sessionId)
            
            # # Aggiungi anche la risposta dell'agente alla cronologia
            # self.sessions.add_message_to_history(task.sessionId, "assistant", final_response.agent_response)
            
            # Safety check - make sure we have a Feedback instance
            
            if not isinstance(final_response, FeedbackOut):
                logger.warning(f"Response is not a FeedbackOut instance: {type(final_response)}")
                if isinstance(final_response, str):
                    final_response = FeedbackOut(
                        jobTitle="Bro è una stringa",
                        professional="Non determinato",
                        date="Non determinato",
                        rating_scoring=None,
                        tag_scoring=None,
                        time_decay=None,
                        sentiment_scoring=None,
                        updated_trust_score=None,
                    )
                else:
                    final_response = FeedbackOut(
                        jobTitle="Bro è un oggetto",
                        professional="Non determinato",
                        date="Non determinato",
                        rating_scoring=None,
                        tag_scoring=None,
                        time_decay=None,
                        sentiment_scoring=None,
                        updated_trust_score=None,
                    )
            
            summary = """
            Here is the summary of the feedback analysis:
            - Job Title: {jobTitle}
            - Professional: {professional}
            - Date: {date}
            - Rating Scoring: {rating_scoring}
            - Tag Scoring: {tag_scoring}
            - Time Decay: {time_decay}
            - Sentiment Scoring: {sentiment_scoring}
            - Updated Trust Score: {updated_trust_score}
            """.format(
                jobTitle=final_response.jobTitle,
                professional=final_response.professional,
                date=final_response.date,
                rating_scoring=final_response.rating_scoring,
                tag_scoring=final_response.tag_scoring,
                time_decay=final_response.time_decay,
                sentiment_scoring=final_response.sentiment_scoring,
                updated_trust_score=final_response.updated_trust_score
            )
            
            data = final_response.model_dump()
            

            part_summary = [{"type": "text", "text": summary}]
            part_data = [{"type": "data", "data": data}]


            # Check if the response is valid, else require more input 
            try:
                await validate_feedback_output(final_response)

            except ValueError as e:
                logger.error(f"Invalid diagnosis output: {e}")

                failed_task = await self.update_store(
                    task_id=task.id,
                    status=TaskStatus(state=TaskState.INPUT_REQUIRED, message=Message(role='agent', parts=part_summary, metadata={"data": data})),
                    artifacts=[]
                )

                return SendTaskResponse(id=request.id, result=failed_task)
            
            # Update task as completed
            updated_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(state=TaskState.COMPLETED, message=Message(role='agent', parts=part_summary)),
                artifacts=[Artifact(parts=part_data, metadata={"data": data})]
            )

            return SendTaskResponse(id=request.id, result=updated_task)

        except Exception as e:
            logger.error(f"Error while processing task {task.id}: {e}", exc_info=True)

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
    