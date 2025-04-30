# Import necessary modules
import asyncio
import os
import random
from dotenv import load_dotenv

import google.genai
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

# Load environment variables
load_dotenv()

APP_NAME = "feedback_agent_app"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY is None:
    print("GOOGLE_API_KEY not set. Please set it in your environment variables.")
    exit(1)

# 1. Setup Memory Service and Session
session_service = InMemorySessionService()
SESSION_ID = "session_001"
USER_ID = "user_1"

session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
if not session:
    session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    print(f"Created new session: {SESSION_ID}")
else:
    print(f"Loaded existing session: {SESSION_ID}")

# 2. Setup the Agent
from agent import feedback_agent  # Ensure 'agent.py' exists in the same directory

# 3. Setup the Runner
runner = Runner(
    agent=feedback_agent,
    session_service=session_service,
    app_name=APP_NAME,
)

def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor

spinner = spinning_cursor()

async def ask_agent(query: str):
    """Sends a query to the agent and prints the final response with a spinning indicator during processing."""
    print(f"\n>>> User Query: {query}")

    content = types.Content(role='user', parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response after retries."

    max_retries = 3
    initial_delay = 1.0
    max_delay = 100.0

    for attempt in range(max_retries + 1):
        try:
            async def stream_response():
                nonlocal final_response_text
                async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            texts = []
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    texts.append(part.text)
                            final_response_text = "\n".join(texts)
                        elif event.actions and event.actions.escalate:
                            final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                        yield "FINAL"
                        break
                    else:
                        for part in event.content.parts:
                             if hasattr(part, 'function_call') and part.function_call:
                                 print(f"\n[DEBUG] Function Call: {part.function_call.name}({part.function_call.args})")
                             elif hasattr(part, 'function_response') and part.function_response:
                                 print(f"[DEBUG] Function Response: {part.function_response.response}\n")
                        yield "PROCESSING"

            async def display_spinner():
                while True:
                    print(f"\r[AGENT]: Thinking {next(spinner)}", end="", flush=True)
                    await asyncio.sleep(0.1)

            processing_task = asyncio.create_task(display_spinner())
            response_stream = stream_response()
            async for status in response_stream:
                if status == "FINAL":
                    processing_task.cancel()
                    print(f"\r[AGENT]: {final_response_text}")
                    break

            if not processing_task.done():
                processing_task.cancel()

            break

        except google.genai.errors.ServerError as e:
            status_code = getattr(e, 'status_code', None)
            if status_code in [500, 503] and attempt < max_retries:
                wait_time = min(initial_delay * (2 ** attempt), max_delay)
                wait_time += random.uniform(0, wait_time * 0.1)
                print(f"\n[RETRY] Server error ({status_code}). Retrying in {wait_time:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                content = types.Content(role='user', parts=[types.Part(text=query)])
            else:
                print(f"[ERROR] Non-retryable server error ({status_code}) or max retries reached. Error: {e}")
                final_response_text = f"Agent failed after retries. Last error: {e}"
                print(f"[AGENT]: {final_response_text}")
                break
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")
            final_response_text = f"Agent failed due to an unexpected error: {e}"
            print(f"[AGENT]: {final_response_text}")
            break

async def main():
    print("🛎️ Feedback Agent Ready. Type 'quit' to exit.")
    while True:
        user_in = input("[USER]: ")
        if user_in.lower() == 'quit':
            break
        await ask_agent(user_in)

if __name__ == "__main__":
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY is None:
        print("GOOGLE_API_KEY not set. Please set it in your environment variables.")
        exit(1)
    asyncio.run(main())