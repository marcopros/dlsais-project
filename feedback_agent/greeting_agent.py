from google.adk.agents import Agent
from tools import say_hello # Import the tool function directly
from agent_config import MODEL_GEMINI_2_0_FLASH # Import the model constant

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH # Starting with Gemini

greeting_agent = Agent(
    # Using a potentially different/cheaper model for a simple task
    model = MODEL_GEMINI_2_0_FLASH,
    # model=LiteLlm(model=MODEL_GPT_4O), # If you would like to experiment with other models
    name="greeting_agent",
    instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting to the user. "
                "Use the 'say_hello' tool to generate the greeting. "
                "If the user provides their name, make sure to pass it to the tool. "
                "Do not engage in any other conversation or tasks.",
    description="Handles simple greetings and hellos using the 'say_hello' tool.", # Crucial for delegation
    tools=[say_hello],
)