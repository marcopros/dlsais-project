import logging
import uuid
from datetime import datetime

from enum import Enum

from diagnosis_agent_app.agent import DiagnosisAgentOut

from A2A.client import A2ACardResolver, A2AClient

# Configure basic logging to output logs at the INFO level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AGENTS(Enum):
    DIAGNOSIS_AGENT = "http://localhost:8001/"
    MATCHING_AGENT = "http://localhost:8002/"
    APPOINTMENT_AGENT = "http://localhost:8003/"
    FEEDBACK_AGENT = "http://localhost:8004/"

    @classmethod
    def list_agent_names(cls):
        """Returns a list of all agent names"""
        return [agent.name for agent in cls]
    



# Validation function
async def validate_diagnosis_output(output: DiagnosisAgentOut) -> bool:
    required_fields = {
        "diagnosis": output.diagnosis,
        "detected_problem_cause": output.detected_problem_cause,
        "type_specialist": output.type_specialist,
        "city": output.city
    }
    missing = [field for field, value in required_fields.items() if value is None]
    if missing:
        raise ValueError(f"Missing required diagnosis fields: {missing}")
    return True


async def validate_diagnosis_output(output):
    """
    Validates that required diagnosis fields are present.
    Raises ValueError if any required field is missing.
    """
    required_fields = {
        "diagnosis": output.diagnosis,
        "detected_problem_cause": output.detected_problem_cause,
        "type_specialist": output.type_specialist,
        "city": output.city
    }

    missing = [field for field, value in required_fields.items() if value is None]
    if missing:
        raise False
    return True


async def diagnosis_agent_send_task(
        self, agent_name: str, message: str, sessionId:str
    ):
        """Sends a task either streaming (if supported) or non-streaming.

        This will send a message to the remote agent named agent_name.

        Args:
          agent_name: The name of the agent to send the task to.
          message: The message to send to the agent for the task.
          sessionId: The session id of the conversation

        Yields:
          A dictionary of JSON data.
        """

        # Get the connection with the Diagnosis Agent
        card_resolver = A2ACardResolver(AGENTS.DIAGNOSIS_AGENT.value)
        card = card_resolver.get_agent_card()
        client = A2AClient(card)

        if not client:
            raise ValueError(f'Client not available for {agent_name}')
        
        # Generate a new unique task ID for this interaction
        task_id = str(uuid.uuid4())

        # Check if the agent supports streaming responses
        streaming = card.capabilities.streaming
        #streaming = False  # Uncomment to force non-streamed mode

        # Prepare the task payload to be sent to the agent
        payload = {
            "id": task_id,
            "sessionId": sessionId,
            "message": {
                "role": "user",
                "parts": [
                    {"type": "text", "text": message}
                ],
                "id": str(uuid.uuid4()),
                "timestamp": int(datetime.now().timestamp() * 1000)         # Current time in milliseconds
            }
        }

        # Send the task and receive the response based on streaming capability
        if streaming:
            # Stream the response as it becomes available
            taskResultStream = client.send_task_streaming(payload) 
            yield taskResultStream        

        else:
            # Send a one-time request and wait for final result
            taskResult = await client.send_task(payload)
            yield taskResult 



async def matching_agent_send_task(
        self, message: str, sessionId:str
    ):
        """Sends a task to the Matching Agent.

        Args:
          message: The message to send to the agent for the task.
          sessionId: The session id of the conversation

        Yields:
          A dictionary of JSON data.
        """

        # Get the connection with the Diagnosis Agent
        card_resolver = A2ACardResolver(AGENTS.MATCHING_AGENT.value)
        card = card_resolver.get_agent_card()
        client = A2AClient(card)

        if not client:
            raise ValueError(f'Client not available for Diagnosis Agent')
        
        # Generate a new unique task ID for this interaction
        task_id = str(uuid.uuid4())

        # Check if the agent supports streaming responses
        streaming = card.capabilities.streaming
        #streaming = False  # Uncomment to force non-streamed mode

        # Prepare the task payload to be sent to the agent
        payload = {
            "id": task_id,
            "sessionId": sessionId,
            "message": {
                "role": "user",
                "parts": [
                    {"type": "text", "text": message}
                ],
                "id": str(uuid.uuid4()),
                "timestamp": int(datetime.now().timestamp() * 1000)         # Current time in milliseconds
            }
        }

        # Send the task and receive the response based on streaming capability
        if streaming:
            # Stream the response as it becomes available
            taskResultStream = client.send_task_streaming(payload) 
            yield taskResultStream        

        else:
            # Send a one-time request and wait for final result
            taskResult = await client.send_task(payload)
            yield taskResult 