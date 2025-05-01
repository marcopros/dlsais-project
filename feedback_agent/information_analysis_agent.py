# Agent 3: Information Level
from google.adk.agents import Agent
from agent_config import MODEL_GEMINI_2_0_FLASH # Import the model constant

information_level_agent = Agent(
    # Could potentially use a lighter model
    model=MODEL_GEMINI_2_0_FLASH, # Or specialized_agent_model
    name="information_level_agent",
    instruction="You are the Information Level Agent. Your ONLY task is to determine how informative a feedback is for evaluating a professional. "
                "Analyze the feedback JSON structure: if it includes selected 'chips', it's 'Medium' informative. "
                "If it includes 'textFeedback', evaluate its length and apparent detail. "
                "If the text is short or generic, it's 'Medium'. If it's detailed and descriptive, it's 'High'. "
                "Respond ONLY with a JSON object containing 'informationLevel' ('Low', 'Medium', or 'High'). "
                "Note: 'Low' typically applies only to rating-only feedback, which isn't expected in your JSON structure, so you will primarily output 'Medium' or 'High'.",
    description="Evaluates how informative a feedback is (Low, Medium, High) based on its content type and detail.", # Crucial for delegation
    tools=[], # This agent doesn't use external tools
    sub_agents=[] # This agent doesn't delegate
)
