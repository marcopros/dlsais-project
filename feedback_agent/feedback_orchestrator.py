from google.adk.agents import Agent
from agent_config import MODEL_GEMINI_2_0_FLASH # Import the model constant

from information_analysis_agent import information_level_agent # Import the information level agent
from text_analysis_agent import text_analysis_agent # Import the text analysis agent
from fakeness_detection_agent import fakeness_detection_agent # Import the fakeness detection agent

from tools import calculate_trust_contribution, update_professional_trust_score # Import the tool functions

# Assume specialized agent instances are defined elsewhere:
# agent1_text_analysis = Agent(...)
# agent2_fakeness_detection = Agent(...)
# agent3_information_level = Agent(...)

# Define the tool function for updating the score (Python code provided below)


# Define the Orchestrator Agent
feedback_orchestrator_agent = Agent(
    name="feedback_orchestrator_agent",
    # Use the main model capable of reasoning and orchestration
    model=MODEL_GEMINI_2_0_FLASH, # Replace with your base model
    description="Central agent that orchestrates the feedback analysis process for professionals. "
                "Delegates analysis to specialists, calculates the trust score contribution, and manages the final update.",
    instruction="You are the Feedback Orchestrator Agent. Your task is to manage the entire flow: "
                "1. Receive the JSON of a new user feedback."
                "2. **IF** the feedback contains free text (`feedbackType` is 'text'), call Agent 1 ('text_analysis_agent') to analyze the text."
                "3. Call Agent 2 ('fakeness_detection_agent') to assess the probability that the feedback is fake."
                "4. Call Agent 3 ('information_level_agent') to evaluate how informative the feedback is."
                "5. Once results from all necessary agents are obtained, **perform the calculation** of the `trustScoreContribution` using the defined formula (calculate_trust_contribution) and passing the input JSON and the output provided by the sub-agents."
                "6. Use the 'update_professional_trust_score' tool to update the professional's trust score with the calculated value."
                "Ensure you pass the correct inputs to each agent and tool and handle the results for the next step. Return a summary of the completed process."
    ,
    tools=[calculate_trust_contribution, update_professional_trust_score], # The orchestrator uses the DB update tool
    # Link the specialized agents as sub-agents
    sub_agents=[text_analysis_agent, fakeness_detection_agent, information_level_agent]
)



# # Example Usage (Illustrative - code managing the Orchestrator would call this)
# if __name__ == '__main__':
#     # Example inputs simulating agent outputs
#     feedback_chip = {
#       "jobInfo": { "jobTitle": "Electrical System Repair", "professional": "Marco Bianchi, Electrician", "date": "April 28, 2025" },
#       "rating": 4,
#       "feedbackType": "chips",
#       "textFeedback": "",
#       "selectedTags": [
#         { "id": "p1", "text": "👍 Professional", "category": "positive" },
#         { "id": "p7", "text": "📱 Excellent communication", "category": "positive" },
#         { "id": "n2", "text": "💸 Too expensive", "category": "negative" }
#       ]
#     }
#     agent1_out_chip = None # Not called for chips
#     agent2_out_chip = {"fakeConfidence": 0.1, "fakeReasoning": "Consistent, history OK"}
#     agent3_out_chip = {"informationLevel": "Medium"}

#     contrib_chip = calculate_trust_contribution(feedback_chip, agent1_out_chip, agent2_out_chip, agent3_out_chip)
#     print(f"\nFeedback Chips Contribution: {contrib_chip}")


#     feedback_text = {
#       "jobInfo": { "jobTitle": "Electrical System Repair", "professional": "Marco Bianchi, Electrician", "date": "April 28, 2025" },
#       "rating": 4,
#       "feedbackType": "text",
#       "textFeedback": "Il tecnico è stato molto professionale e ha risolto il problema rapidamente. Unico neo: il prezzo un po' elevato rispetto a quanto mi aspettavo.",
#       "selectedTags": []
#     }
#     # Simulate Agent 1 output for the text feedback
#     agent1_out_text = {
#       "sentiment": "Misto",
#       "extractedFeatures": ["professionale", "rapido", "prezzo elevato"]
#     }
#     agent2_out_text = {"fakeConfidence": 0.1, "fakeReasoning": "Consistent, history OK"} # Assume low fakeness
#     agent3_out_text = {"informationLevel": "High"} # Assume detailed text -> High info

#     contrib_text = calculate_trust_contribution(feedback_text, agent1_out_text, agent2_out_text, agent3_out_text)
#     print(f"Feedback Text Contribution: {contrib_text}")

#     feedback_fake_text = {
#       "jobInfo": { "jobTitle": "Any Job", "professional": "Fake Pro", "date": "April 28, 2025" },
#       "rating": 5,
#       "feedbackType": "text",
#       "textFeedback": "This guy was absolutely THE BEST EVER!!! Highly recommend!",
#       "selectedTags": []
#     }
#     # Simulate Agent 1 output for the text feedback
#     agent1_out_fake_text = {
#       "sentiment": "Positivo",
#       "extractedFeatures": [] # Generic text, no specific features extracted
#     }
#     agent2_out_fake_text = {"fakeConfidence": 0.8, "fakeReasoning": "Overly generic, hyperbolic, high rating vs potential history"} # Assume high fakeness
#     agent3_out_fake_text = {"informationLevel": "Medium"} # Generic text -> Medium info

#     contrib_fake_text = calculate_trust_contribution(feedback_fake_text, agent1_out_fake_text, agent2_out_fake_text, agent3_out_fake_text)
#     print(f"Feedback Fake Text Contribution: {contrib_fake_text}")

#     # Example with potential error (missing agent2_result)
#     # try:
#     #     calculate_trust_contribution(feedback_chip, agent1_out_chip, None, agent3_out_chip)
#     # except ValueError as e:
#     #     print(f"\nError caught as expected: {e}")