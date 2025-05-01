# @title Define the Weather Agent
# Use one of the model constants defined earlier
from google.adk.agents import Agent
from tools import get_weather # Import the tool function directly
from farewell_agent import farewell_agent # Import the farewell agent
from greeting_agent import greeting_agent # Import the greeting agent
from agent_config import MODEL_GEMINI_2_0_FLASH # Import the model constant

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH # Starting with Gemini

weather_agent_team = Agent(
        name="weather_agent_v4_stateful", # New version name
        model=AGENT_MODEL,
        description="Main agent: Provides weather (state-aware unit), delegates greetings/farewells, saves report to state.",
        instruction="You are the main Weather Agent. Your job is to provide weather using 'get_weather'. "
                    "The tool will format the temperature based on user preference stored in state. "
                    "Delegate simple greetings to 'greeting_agent' and farewells to 'farewell_agent'. "
                    "Handle only weather requests, greetings, and farewells.",
        tools=[get_weather], # Use the state-aware tool
        sub_agents=[greeting_agent, farewell_agent], # Include sub-agents
        output_key="last_weather_report" # <<< Auto-save agent's final weather response
    )

print(f"Agent '{weather_agent.name}' created using model '{AGENT_MODEL}'.")