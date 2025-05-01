from google.adk.agents import Agent
from tools import say_goodbye # Import the tool function directly
from agent_config import MODEL_GEMINI_2_0_FLASH # Import the model constant

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH # Starting with Gemini

farewell_agent = Agent(
    # Can use the same or a different model
    model = MODEL_GEMINI_2_0_FLASH,
    # model=LiteLlm(model=MODEL_GPT_4O), # If you would like to experiment with other models
    name="farewell_agent",
    instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message. "
                "Use the 'say_goodbye' tool when the user indicates they are leaving or ending the conversation "
                "(e.g., using words like 'bye', 'goodbye', 'thanks bye', 'see you'). "
                "Do not perform any other actions.",
    description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.", # Crucial for delegation
    tools=[say_goodbye],
)