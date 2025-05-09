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
    

def validate_diagnosis(diagnosi: dict) -> bool:
    """
    Validates that required diagnosis fields are present.
    Raises ValueError if any required field is missing.
    """
    required_keys = ["diagnosis", "detected_problem_cause", "type_specialist"]
    
    missing = [key for key in required_keys if diagnosi.get(key) in (None, "")]
    
    if missing:
        return False
    
    return True


async def diagnosis_agent_send_task( message: str, sessionId:str ) -> dict:
        """Sends a task either streaming (if supported) or non-streaming.

        This will send a message to the remote agent named agent_name.

        Args:
          message: The message to send to the agent for the diagnosis.
          sessionId: The session id of the conversation

        Yields:
          A dictionary of JSON data.
        """

        # Get the connection with the Diagnosis Agent
        card_resolver = A2ACardResolver(AGENTS.DIAGNOSIS_AGENT.value)
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
            full_response = {}
            async for chunk in client.send_task_streaming(payload):
                full_response.update(chunk)  # Merge each chunk into final result
            return full_response

        else:
            # Send a one-time request and wait for final result
            return await client.send_task(payload)



async def matching_agent_send_task( message: str, sessionId:str ) -> dict:
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
        # streaming = card.capabilities.streaming
        streaming = False  # Uncomment to force non-streamed mode

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
            full_response = {}
            async for chunk in client.send_task_streaming(payload):
                full_response.update(chunk)  # Merge each chunk into final result
            return full_response

        else:
            # Send a one-time request and wait for final result
             return await client.send_task(payload)