from google.adk.agents import LlmAgent

feedback_agent = LlmAgent(
    name="feedback_agent",
    model="gemini-2.0-flash",
    description="An agent designed to collect user feedback after a repair, asking a few focused questions without being intrusive.",
    instruction="""Once the user has completed the repair process, kindly ask for brief feedback.
Ask no more than 3 quick and simple questions, such as:
- Was the proposed solution helpful?
- Did you experience any difficulties during the repair?
- Would you recommend this service to others?

Always be polite and thank the user for their time. 
The goal is to gather useful insights to improve the trusted network and provide better recommendations in the future, without overwhelming the user.
"""
)