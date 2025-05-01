# Agent 1: Text Analysis
from google.adk.agents import Agent
from agent_config import MODEL_GEMINI_2_0_FLASH # Import the model constant

def get_professional_history_tool():
    # Placeholder for the actual tool implementation
    print("Professional history tool called")

def get_user_history_tool():
    # Placeholder for the actual tool implementation
    print("User history tool called")


# Agent 2: Fakeness Detection
fakeness_detection_agent = Agent(
    # May require a more capable model for complex reasoning about patterns
    model=MODEL_GEMINI_2_0_FLASH, # Or a capable specialized model
    name="fakeness_detection_agent",
    instruction="You are the Fakeness Detection Agent. Your task is to assess the likelihood that a given feedback is fake (fraudulent or sabotage). "
                "Analyze the provided feedback JSON for internal inconsistencies (rating vs. content). "
                "Use the 'get_professional_history' tool (and 'get_user_history' if user ID is provided in the input) to check for suspicious patterns in historical data, such as sudden rating changes or unusual user review behavior. "
                "Based on your analysis, determine a 'fakeConfidence' score (0.0-1.0) and provide a brief 'fakeReasoning'. "
                "Respond ONLY with a JSON object containing 'fakeConfidence' and 'fakeReasoning'.",
    description="Assesses the likelihood of a feedback being fake by analyzing current feedback and historical data.", # Crucial for delegation
    tools=[get_professional_history_tool, get_user_history_tool], # Uses historical data tools
    sub_agents=[] # This agent doesn't delegate
)

