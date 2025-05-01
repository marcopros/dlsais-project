# @title Import necessary libraries
import os
import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
from google.genai import types

import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

from agent_config import check_and_configure_environment
from feedback_orchestrator import feedback_orchestrator_agent

async def call_agent_async(query: str, runner, user_id, session_id):
  """Sends a query to the agent and prints the final response."""
  print(f"\n>>> User Query: {query}")

  # Prepare the user's message in ADK format
  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = "Agent did not produce a final response." # Default

  # Key Concept: run_async executes the agent logic and yields Events.
  # We iterate through events to find the final answer.
  async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
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

  print(f"<<< Agent Response: {final_response_text}")

async def run_conversation(USER_ID, SESSION_ID):
    # --- Runner ---
    # Key Concept: Runner orchestrates the agent execution loop.
    runner = Runner(
        agent=weather_agent, # The agent we want to run
        app_name=APP_NAME,   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )
    print(f"Runner created for agent '{runner.agent.name}'.")
    
    await call_agent_async("What is the weather like in London?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

    await call_agent_async("How about Paris?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID) # Expecting the tool's error message

    await call_agent_async("Tell me the weather in New York",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

# Execute the conversation using await in an async context (like Colab/Jupyter)

query_feedback = """{
  "jobInfo": {
    "jobTitle": "Emergency Pipe Repair",
    "professional": "Luca Rossi, Plumber",
    "date": "October 26, 2024"
  },
  "rating": 4,
  "feedbackType": "text",
  "textFeedback": "Luca arrived quickly which was great for an emergency. He fixed the leak efficiently. However, the final bill was a bit higher than the initial estimate, although the work quality was good.",
  "selectedTags": []
}"""

async def run_team_conversation(runner_agent_team, USER_ID, SESSION_ID):
        

        await call_agent_async(query = query_feedback,
                               runner=runner_agent_team,
                               user_id=USER_ID,
                               session_id=SESSION_ID)

async def main():
    
    session_service_stateful = InMemorySessionService()

    # Define constants for identifying the interaction context
    APP_NAME = "feedback_agent_demo" # Name of the app
    SESSION_ID_STATEFUL = "session_state_demo_001"
    USER_ID_STATEFUL = "user_state_demo"# Using a fixed ID for simplicity

    # Define initial state data - user prefers Celsius initially
    initial_state = {
        
    }

    # Create the specific session where the conversation will happen
    session_stateful = session_service_stateful.create_session(
        app_name=APP_NAME,
        user_id=USER_ID_STATEFUL,
        session_id=SESSION_ID_STATEFUL,
        #state=initial_state # Pass the initial
    )
    print(f"Session created: App='{APP_NAME}', User='{USER_ID_STATEFUL}', Session='{SESSION_ID_STATEFUL}'")
    
    # retrieved_session = session_service_stateful.get_session(
    #     app_name=APP_NAME,
    #     user_id=USER_ID_STATEFUL,
    #     session_id=SESSION_ID_STATEFUL
    # )
    
    # print("\n--- Initial Session State ---")
    # if retrieved_session:
    #     print(retrieved_session.state)
    # else:
    #     print("Error: Could not retrieve session.")

    print("\n--- Testing Agent Team Delegation ---")

    actual_root_agent = feedback_orchestrator_agent # The agent we want to run
    runner_agent_team = Runner( # Or use InMemoryRunner
        agent=actual_root_agent,
        app_name=APP_NAME,
        session_service=session_service_stateful
    )
    print(f"Runner created for agent '{actual_root_agent.name}'.")

    await run_team_conversation(runner_agent_team, USER_ID_STATEFUL, SESSION_ID_STATEFUL) # Run the conversation with the team agent


if __name__ == "__main__":
    # Run the main function
    check_and_configure_environment()
    
    asyncio.run(main())