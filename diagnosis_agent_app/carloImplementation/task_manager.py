import asyncio
import json
import uuid
import logging
from typing import AsyncIterable, Any, Dict, Optional

from .direct_agent import query_agent
from .session import SessionService

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


async def validate_diagnosis_output(output) -> bool:
    """
    Validates that required diagnosis fields are present.
    
    Args:
        output: Dictionary containing diagnosis data
        
    Returns:
        True if validation passes
        Raises ValueError if any required field is missing
    """
    logger.info(f"Validating diagnosis output: {output}")
    
    required_fields = ["diagnosis", "detected_problem_cause", "type_specialist"]
    
    # Check if output is None or not a dictionary
    if not output or not isinstance(output, dict):
        raise ValueError("Invalid diagnosis output format: expected dictionary")
        
    missing = [field for field in required_fields if field not in output or output[field] is None]
    if missing:
        raise ValueError(f"Missing required diagnosis fields: {missing}")
    
    return True



# Custom Task Manager for Diagnosis Agent
class DiagnosisAgentTaskManager(InMemoryTaskManager):
    """
    Custom Task Manager for handling tasks related to a diagnosis agent.
    Manages sessions, invokes the agent, streams responses, and updates task status.
    """
    def __init__(self, agent=None):
        """
        Initialize the task manager with required dependencies.
        
        Args:
            agent: Optional agent parameter (kept for compatibility)
        """
        super().__init__()
        self.agent = agent  # Not used anymore, kept for compatibility
        self.sessions = SessionService()
        logger.info("DiagnosisAgentTaskManager initialized.")
    

    async def invoke(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Synchronously invoke the direct agent to get a final response for a given query and session.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Returns:
            Final response from the agent as a dictionary.
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
        
        
        # Query the direct agent with the user message and session
        try:
            result = await query_agent(query, session)
            logger.info(f"RESULT: {result}")
                
            return result
        except Exception as e:
            logger.error(f"Error during agent invocation: {e}")
            raise


    async def stream(self, query: str, session_id: str) -> AsyncIterable[Dict[str, Any]]:
        """
        Stream partial results from the agent asynchronously.

        Args:
            query: User input as text.
            session_id: Unique identifier for the session.

        Yields:
            Dictionary containing either intermediate updates or final response.
        """
        # TO DO: Implement streaming functionality
        result = await self.invoke(query, session_id)
        yield {"status": "completed", "result": result}


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
                        if msg.parts and len(msg.parts) > 0:
                            # Handle both dictionary and object parts
                            if isinstance(msg.parts[0], dict):
                                user_message = msg.parts[0].get("text", "No input")
                            elif hasattr(msg.parts[0], "text"):
                                user_message = msg.parts[0].text
                        break
            
            # Get the agent's response (now a dictionary)
            response_dict = await self.invoke(user_message, task.sessionId)
            logger.info(f"Agent response: {response_dict}")
            summary_part = TextPart(type="text", text=response_dict.get("agent_response", ""))
            
            # Check if the response is valid, else require more input 
            try:
                await validate_diagnosis_output(response_dict)
                
                # Update task as completed
                updated_task = await self.update_store(
                    task_id=task.id,
                    status=TaskStatus(
                        state=TaskState.COMPLETED, 
                        message=Message(role='agent', parts=[summary_part])
                    ),
                    artifacts=[Artifact(parts=[TextPart(type="data", text=json.dumps(response_dict))])]
                )
                
                return SendTaskResponse(id=request.id, result=updated_task)
                
            except ValueError as e:
                logger.error(f"Invalid diagnosis output: {e}")
                
                # Create a proper error message
                error_text = f"Diagnosis incomplete: {str(e)}"
                error_part = TextPart(type="text", text=error_text)
                response_part = TextPart(type="text", text=response_dict.get("agent_response", ""))
                
                # Update task as requiring input
                failed_task = await self.update_store(
                    task_id=task.id,
                    status=TaskStatus(
                        state=TaskState.INPUT_REQUIRED, 
                        message=Message(role='agent', parts=[error_part,response_part])
                    ),
                    artifacts=[]
                )
                
                return SendTaskResponse(id=request.id, result=failed_task)
                
        except Exception as e:
            logger.error(f"Error while processing task {task.id}: {e}")

            # Create a proper error message with TextPart
            error_text = f"Error occurred during task processing: {str(e)}"
            error_part = TextPart(type="text", text=error_text)
            
            # Update task as failed
            failed_task = await self.update_store(
                task_id=task.id,
                status=TaskStatus(
                    state=TaskState.FAILED, 
                    message=Message(
                        role="agent",
                        parts=[error_part],
                        timestamp=int(asyncio.get_running_loop().time() * 1000),
                        id=str(uuid.uuid4())
                    )
                ),
                artifacts=[]
            )

            return SendTaskResponse(id=request.id, result=failed_task)

            
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

        try:
            # Find the latest user message
            user_message = "No input"
            if task.history:
                for msg in reversed(task.history):
                    if msg.role == "user" and msg.parts and len(msg.parts) > 0:
                        if isinstance(msg.parts[0], dict):
                            user_message = msg.parts[0].get("text", "No input")
                        elif hasattr(msg.parts[0], "text"):
                            user_message = msg.parts[0].text
                        break
            
            # Notify client that task is starting
            yield SendTaskStreamingResponse(
                id=request.id,
                result={
                    "id": task.id,
                    "status": TaskStatus(state=TaskState.WORKING),
                    "updates": {"message": "Task started"},
                },
            )

            # Process the task (using stream method to get progressive updates)
            async for update in self.stream(user_message, task.sessionId):
                # Send intermediate updates
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result={
                        "id": task.id,
                        "status": TaskStatus(state=TaskState.WORKING),
                        "updates": update,
                    },
                )
                
                # Brief pause to avoid flooding client
                await asyncio.sleep(0.1)
                
            # Get final result
            final_result = await self.invoke(user_message, task.sessionId)
            
            # Validate the result
            try:
                await validate_diagnosis_output(final_result)
                
                # Complete the task successfully
                updated_task = await self.update_store(
                    task_id=task.id,
                    status=TaskStatus(
                        state=TaskState.COMPLETED,
                        message=Message(
                            role="agent",
                            parts=[TextPart(type="text", text=final_result.get("agent_response", "Task completed"))]
                        )
                    ),
                    artifacts=[Artifact(parts=[TextPart(type="data", text=json.dumps(final_result))])]
                )
                
                # Send final completion response
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result={
                        "id": task.id,
                        "status": TaskStatus(state=TaskState.COMPLETED),
                        "artifacts": updated_task.artifacts,
                    },
                )
                
            except ValueError as e:
                # Send error response for missing fields
                error_message = f"Diagnosis incomplete: {str(e)}"
                
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result={
                        "id": task.id,
                        "status": TaskStatus(
                            state=TaskState.INPUT_REQUIRED,
                            message=Message(
                                role="agent",
                                parts=[TextPart(type="text", text=error_message)]
                            )
                        )
                    },
                )
                
        except Exception as e:
            logger.error(f"Error in streaming task {task.id}: {e}")
            
            # Send error response
            yield SendTaskStreamingResponse(
                id=request.id,
                result={
                    "id": task.id,
                    "status": TaskStatus(
                        state=TaskState.FAILED,
                        message=Message(
                            role="agent",
                            parts=[TextPart(type="text", text=f"Error occurred: {str(e)}")]
                        )
                    )
                },
            )