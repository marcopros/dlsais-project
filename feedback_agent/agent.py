from agents import Agent, Runner, RunContextWrapper, handoff, FunctionTool
from agents.extensions.visualization import draw_graph
from dotenv import load_dotenv
from tools import (
    get_rating_scoring,
    get_tag_scoring,
    get_time_decay,
    get_trust_score,
    update_professional_trust_score,
)
import os
import json
import asyncio

# Load environment variables from .env file
load_dotenv()

test_review = """{
  "jobInfo": {
    "jobTitle": "Electrical Repair",
    "professional": "Marco Bianchi, Electrician",
    "date": "2025-04-28"
  },
  "rating": 4,
  "feedbackType": "chips",
  "textFeedback": "",
  "selectedTags": [
    {
      "id": "p1",
      "text": "👍 Professional",
      "category": "positive"
    },
    {
      "id": "p7",
      "text": "📱 Excellent communication",
      "category": "positive"
    },
    {
      "id": "n2",
      "text": "💸 Too expensive",
      "category": "negative"
    }
  ]
}"""


sentiment_agent = Agent(
    name="Sentiment Analysis Agent",
    instructions="""You are a helpful assistant that will analyse the sentiment of the text feedback provided by the user. 
                    You must follow this flow:
                    1. If the field 'feedbackType' is 'text' and the field 'textFeedback' is not empty, then compute the sentiment score.
                    2. If the field 'feedbackType' is 'chips', Do NOT compute the sentiment score.
                    Output the sentiment score as a float between 0 and 1, where 0 is very negative, 0.5 is NEUTRAL, and 1 is very positive.
                    """,
    model="gpt-4.1-nano",
    output_type=float,
)
  

feedback_agent = Agent(
    name="Agent to orchestrate the analysis of feedback on a service provided by a professional",
    instructions="""You are a helpful assistant that will orchestrate the analysis of feedback on a service provided by a professional in order to compute and update the trust score of the professional. 
                    You must follow this flow:
                    1. compute the rating scoring by using the tool 'get_rating_scoring'
                    2. compute the tag scoring by using the tool 'get_tag_scoring' by providing the number of positive and negative tags (see the field 'category' in each tag to determine if it is positive or negative)
                    3. compute time decay by using the tool 'get_time_decay'
                    4. If the field 'feedbackType' is 'text' and the field 'textFeedback' is not empty, then compute the sentiment score by using the handoff 'sentiment_agent'
                    5. Finally, compute the trust score by using the tool 'get_trust_score', update professional's score by using 'update_professional_trust_score' and write a brief summary of the analysis.
                    """,
    model="gpt-4.1-mini",
    tools=[get_rating_scoring, get_tag_scoring, get_time_decay, get_trust_score, update_professional_trust_score],
    handoffs=[sentiment_agent],
)


async def main():
    #draw_graph(feedback_agent, filename="feedback_agent_graph.png")
    result = await Runner.run(feedback_agent, str(test_review))
    print(result.final_output)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    

