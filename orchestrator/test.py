from datetime import datetime

import asyncio
import uuid

from A2A.client import A2ACardResolver, A2AClient


async def ask_agent_with_a2a(agent_url: str, session_id: str, user_text: str):
    """
    Sends a message to an agent using A2AClient and returns the response.

    Args:
        agent_url: URL where the agent is hosted (e.g., http://localhost:8000/)
        session_id: Unique identifier for this conversation session
        user_text: The message from the user to send to the agent
    """
    try:
        # Download the agent card that describes the agent's capabilities
        card_resolver = A2ACardResolver(agent_url)
        agent_card = card_resolver.get_agent_card()
        print(f"[DEBUG] Agent Card caricata per {agent_url}")

        # Create an A2A client instance using the agent card
        client = A2AClient(agent_card=agent_card)

        # Generate a new unique task ID for this interaction
        task_id = str(uuid.uuid4())

        # Check if the agent supports streaming responses
        streaming = agent_card.capabilities.streaming
        #streaming = False  # Uncomment to force non-streamed mode

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
            print(f'[AGENT]:{taskResult.model_dump_json(exclude_none=True)}')
        

    except Exception as e:
        # Log any errors that occur during the interaction
        print(f"[ERRORE]: {type(e).__name__} - {e}")


async def main():
    """
    Interactive chat client that communicates with an A2A agent.
    Keeps the session alive across multiple messages.
    """
    url = "http://localhost:8000/"      # URL of the agent service
    session_id = str(uuid.uuid4())      # Unique ID for the entire chat session

    print("Chat Client A2A Started")
    print(f"\tSession ID: {session_id}")
    print(f"\tConnected to: {url}")
    print("Type 'quit' or ':q' to exit.")

    while True:
        try:
            # Prompt the user for input
            user_input = input("[User]: ")
            if user_input.strip().lower() in ("quit", ":q"):
                print("Terminated chat.")
                break
            
            # Send the user’s message to the agent
            await ask_agent_with_a2a(url, session_id, user_input)

        except KeyboardInterrupt:
        # Handle user interruption gracefully
            print("\nInterrupted by user.")
            break


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())