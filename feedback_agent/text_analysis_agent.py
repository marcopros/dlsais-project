# Agent 1: Text Analysis
from google.adk.agents import Agent
from agent_config import MODEL_GEMINI_2_0_FLASH # Import the model constant

text_analysis_agent = Agent(
    # Could potentially use a lighter model if complex text analysis is not needed
    model=MODEL_GEMINI_2_0_FLASH, # Or specialized_agent_model
    name="text_analysis_agent",
    instruction="You are the Text Analysis Agent. Your ONLY task is to analyze a piece of text feedback "
                "and extract the overall sentiment and key features/themes mentioned. "
                "Respond ONLY with a JSON object containing the 'sentiment' and 'extractedFeatures'. "
                "Do not engage in conversation or perform other tasks.",
    description="Analyzes text feedback to extract sentiment and key features.", # Crucial for delegation
    tools=[], # This agent doesn't use external tools
    sub_agents=[] # This agent doesn't delegate
)