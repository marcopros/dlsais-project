# Import necessary modules
import asyncio
import os
from dotenv import load_dotenv

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
 
# help(Runner)                  # To see the available methods and attributes of the Runner class
# help(InMemorySessionService)   # To see the available methods and attributes of the InMemoryMemoryService class#

# Carica le variabili dal file .env
load_dotenv()

APP_NAME = "matching_agent_app"  # Name of the application
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Fetch the Google API key from environment variables
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")  # Fetch the Vertex AI usage flag from environment variables

if GOOGLE_API_KEY is None:
    print("GOOGLE_API_KEY not set. Please set it in your environment variables.")
    exit(1)


# 1. Setup Memory Service and Session
session_service = InMemorySessionService()  # Using simple in-memory storage for conversation history
SESSION_ID = "session_001"
USER_ID = "user_1"

# Create or retrieve a session
session = session_service.get_session(app_name = APP_NAME, user_id = USER_ID, session_id=SESSION_ID)
if not session:
    session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    print(f"Created new session: {SESSION_ID}")
else:
    print(f"Loaded existing session: {SESSION_ID}")


# 2. Setup the Agent
from agent import matching_agent  # Import the agent from the agent module


# 3. Setup the Runner
runner = Runner(                     # Create a Runner instance to manage the agent's execution
    agent=matching_agent,
    session_service=session_service, # Use the service instance
    app_name=APP_NAME,
)


# 4. Interaction Function
async def ask_agent(query: str):
    # Sends a query to the agent and prints the final response.
    # print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response." # Default

    # Key Concept: run_async executes the agent logic and yields Events.
    # We iterate through events to find the final answer.
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        # You can uncomment the line below to see *all* events during execution
        # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            # Add more checks here if needed (e.g., specific error codes)
            break # Stop processing events once the final response is found

    print(f"[AGENT]: {final_response_text}")


# Example Usage (you could run this in a main block or interactive session)
async def main():
    print("Matching Agent Ready. Type 'quit' to exit.")
    while True:
        user_in = input("[USER]: ")
        if user_in.lower() == 'quit':
            break
        await ask_agent(user_in)

if __name__ == "__main__":
    asyncio.run(main())