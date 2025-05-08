from datetime import datetime

import asyncio
import uuid

from A2A.client import A2ACardResolver, A2AClient
from A2A.types import TaskState


def print_organized(data, indent=0):
    """Stampa il contenuto del dizionario JSON con indentazione, senza parentesi."""
    spacing = '  ' * indent  # 2 spazi per livello

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{spacing}{key}:")
                print_organized(value, indent + 1)
            else:
                print(f"{spacing}{key}: {value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                print(f"{spacing}-")
                print_organized(item, indent + 1)
            else:
                print(f"{spacing}- {item}")
    else:
        print(f"{spacing}{data}")


async def ask_agent_with_a2a(agent_url: str, session_id: str, user_text: str, task_id: str = None):
    """
    Sends a message to an agent using A2AClient and returns the response.
    If task_id is provided, continues the same task.

    Returns:
        Tuple of (task_result, new_task_id)
    """
    try:
        # Download the agent card that describes the agent's capabilities
        card_resolver = A2ACardResolver(agent_url)
        agent_card = card_resolver.get_agent_card()
        print(f"[DEBUG] Agent Card upload for {agent_url}")

        # Create an A2A client instance using the agent card
        client = A2AClient(agent_card=agent_card)

        # Generate a new unique task ID if none provided
        if task_id is None:
            task_id = str(uuid.uuid4())

        # Check if the agent supports streaming responses
        streaming = agent_card.capabilities.streaming
        #streaming = False  # Uncomment to force non-streamed mode
        #print(f"[DEBUG] Streming Option {streaming}")

        # Prepare the task payload to be sent to the agent
        payload = {
            "id": task_id,
            "sessionId": session_id,
            "acceptedOutputModes": ["text"],
            "message": {
                "role": "user",
                "parts": [
                    {"type": "text", "text": user_text}
                ],
                "id": str(uuid.uuid4()),
                "timestamp": int(datetime.now().timestamp() * 1000)         # Current time in milliseconds
            }
        }

        # Send the task and receive the response based on streaming capability
        if streaming:
            # Stream the response as it becomes available
            response_stream = client.send_task_streaming(payload)
            print(f"[AGENT]: ", end="", flush=True)
            
            async for result in response_stream:
                # Print full JSON of each streaming event
                print(
                    f'stream event => {result.model_dump_json(exclude_none=True)}'                  
                    # Alternatively, extract only text:
                    # f'\tstream event => {get_result_text(result.model_dump(exclude_none=True))}'
                )
            print()         # New line after streaming

        else:
            # Send a one-time request and wait for final result
            taskResult = await client.send_task(payload)
            print(f"[AGENT]: ")
            print_organized(taskResult.model_dump())

            return taskResult, task_id
            
    except Exception as e:
        # Log any errors that occur during the interaction
        print(f"[ERRORE]: {type(e).__name__} - {e}")
        return None, task_id


async def main():
    """
    Interactive chat client that communicates with an A2A agent.
    Keeps the session alive across multiple messages.
    """
    url = "http://localhost:8003/"      # URL of the agent service
    session_id = str(uuid.uuid4())      # Unique ID for the entire chat session

    print("Chat Client A2A Started")
    print(f"\tSession ID: {session_id}")
    print(f"\tConnected to: {url}")
    print("Type 'quit' or ':q' to exit.")

    task_id = None

    while True:
        try:
            # Prompt the user for input
            user_input = input("[User]: ")
            if user_input.strip().lower() in ("quit", ":q"):
                print("Terminated chat.")
                break
            
            # Send the user’s message to the agent
            task_result, task_id = await ask_agent_with_a2a(url, session_id, user_input, task_id)

            # If no more input are required to resolve the task pass to a new task

            if task_result and task_result.result.status.state.name != TaskState.INPUT_REQUIRED.name:
                task_id = None
            else:
                print('TASK ID: ', task_id)


        except KeyboardInterrupt:
        # Handle user interruption gracefully
            print("\nInterrupted by user.")
            break


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())