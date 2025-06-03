
import os
import aiohttp

from typing import List, Optional

from agents import Agent, function_tool, WebSearchTool

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel

from json import tool
#from operator import call
from typing import Literal, List
import aiohttp
from unittest.mock import Base
import uuid
from agents import (
    Agent, 
    Runner, 
    trace, 
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
    WebSearchTool,
    handoff,
    MessageOutputItem,
    ItemHelpers,
    HandoffOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
    function_tool
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from numpy import diag
from regex import W
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import asyncio
import json

# --- OUTPUT DEF ---
class DiagnosisAgentOut(BaseModel):
    agent_response: str                 # summary of the diagnosis agent 
    # Diagnosis Fields
    diagnosis: str | None
    detected_problem_cause: str | None
    type_specialist: str | None
    # DIY Fields
    unlock_request_for_diy_solution: bool
    diy_solution: str | None
    diy_links: list[str] | None # list of links to video or written tutorials
    call_professional: bool = False     # if the user prefers to call a professional instead of DIY solution
    


# --- SESSION ----
class DiagnosisContext(BaseModel):
    # search_for_diy_solution: bool = False
    # user_location: Optional[str]
    # user_diy_skills: Optional[str]
    # user_diy_tools: Optional[List[str]]
    # home_type: Optional[str]
    # solution_preferences: Optional[str]
    # time_available_for_repair: Optional[str]
    # favourite_language: str = "English"
    previous_agent_response: str                 # summary of the diagnosis agent 
    # Diagnosis Fields
    diagnosis: str | None
    detected_problem_cause: str | None
    type_specialist: str | None
    # DIY Fields
    unlock_request_for_diy_solution: bool
    diy_solution: str | None
    diy_links: list[str] | None # list of links to video or written tutorials,
    call_professional: bool = False     # if the user prefers to call a professional instead of DIY solution



# --- DIY AGENT ---
# @function_tool
# async def search_video_tutorial(query: str, hl: str, gl: str) -> List[str]:
#     """ Searches YouTube for video tutorials matching the given query.
#         Returns a list of YouTube watch URLs.
#     Args:
#         query (str): The search query for the video tutorial.
#         hl (str): The language code for the search results (e.g., 'it' for Italian).
#         gl (str): The country code for the search results (e.g., 'it' for Italy).
#     """
#     # Add the site filter to the query to search only for YouTube videos
#     full_query = f"{query} site:youtube.com"
#     url = "https://serpapi.com/search"
#     params = {
#         "q": full_query,
#         "hl": hl,
#         "gl": gl,
#         "engine": "google",
#         "api_key": os.getenv("SERPAPI_API_KEY"),
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, params=params) as resp:
#             resp.raise_for_status()
#             data = await resp.json()

#     # Extract video links from the response
#     videos: List[str] = []
#     for item in data.get("organic_results", []):
#         link = item.get("link", "")
#         if "youtube.com/watch" in link:
#             videos.append(link)

#     # Provide only the first 6 links
#     return videos[:6]

@function_tool
async def search_video_tutorial(query: str, hl: str, gl: str) -> List[str]:
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 6,
        "relevanceLanguage": hl,
        "regionCode": gl,
        "key": os.getenv("YOUTUBE_API_KEY"),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    videos: List[str] = []
    for item in data.get("items", []):
        video_id = item["id"].get("videoId")
        if video_id:
            videos.append(f"https://www.youtube.com/watch?v={video_id}")

    return videos

diy_agent = Agent[DiagnosisContext](
    name="DIY agent",
    instructions=(
        "you are given a home issue and you have to find a DIY solution to it. "
        "Use the 'search_video_tutorial' tool to find a YouTube video tutorial link that solve user's problem. DO NOT MAKE UP ANYTHING."
        "if the user writes in a language different from English, search for results in that language. #! DO NOT INCLUDE THE VIDEO TUTORIAL LINK IN THE RESPONSE, but in the output field 'diy_links' write the list of links to video tutorials and in 'diy_solution' write a summary of the solution."
    ),
    model="gpt-4.1",
    tools=[search_video_tutorial],
    output_type=DiagnosisAgentOut,
)

 

# --- DIAGNOSIS AGENT ---
diagnosis_agent = Agent[DiagnosisContext](
    name="Diagnosis agent",
    instructions=(f"{RECOMMENDED_PROMPT_PREFIX}"
        "Your job is to find the root cause of the home issue and ask for a DIY solution if the user is interested or if the users prefers a professional to cope with the problem (if it does set the relative output flag to true)." 
        "Ask few clarification if needed."
        "if user is interested in a DIY solution and video tutorials, use the agent tool at your disposal. #!IMPORTANT! DO NOT INCLUDE VIDEO TUTORIAL'S LINKS in the response, but in the output field 'diy_links' and 'diy_solution' write a summary of the solution.!#"
        "Follow accurately the setting provided in the context and adapt to the user preferences (language, location, time to solve the issue). If users writes in a language find results in that language, if the user is located in Italy, search for results in Italian and so on."
        "Do not ask twice question to detect the problem, work with the context provided and the previous agent response. "
        # "when you are done write as last word 'END' to signal the end of the conversation. "
    ),
    model="gpt-4.1",
    tools=[diy_agent.as_tool(
        tool_name="propose_diy_solution",
        tool_description="Search the web a DIY solution relatively the founded root cause with a YouTube video tutorial link (do not make it up)."
    )],
    output_type=DiagnosisAgentOut,
)


import asyncio

load_dotenv()

async def main():
    input_items: list[TResponseInputItem] = []
    current_agent: Agent[DiagnosisContext] = diagnosis_agent
    
    settings = DiagnosisContext(
        previous_agent_response="",
        diagnosis=None,
        detected_problem_cause=None,
        type_specialist=None,
        unlock_request_for_diy_solution=False,
        diy_solution=None,
        diy_links=None,
        call_professional=False
    )
    
    while True:
        user_prompt = input("User: ")
        with trace("Home issue diagnosis workflow"):
            input_items.append({"content": user_prompt, "role": "user"})
            result = await Runner.run(current_agent, input=input_items, context=settings)
                
            for new_item in result.new_items:
                agent_name = new_item.agent.name
                   
                if isinstance(new_item, MessageOutputItem):
                    parsed = json.loads(ItemHelpers.text_message_output(new_item))
                    print(f"{agent_name}: {parsed['agent_response']}")
                    if parsed["unlock_request_for_diy_solution"]:
                        print("Unlocking DIY agent...")
                        current_agent = diy_agent
                    if parsed["diy_solution"] != None:
                        print(f"DIY solution: {parsed['diy_solution']}")
                    if parsed["diy_links"] != None:
                        print(f"DIY links: {parsed['diy_links']}")
                    if parsed["call_professional"]:
                        print("User prefers to call a professional.")
                        break
                    
                    #print("debug:", parsed)
                
            input_items = result.to_input_list()
            current_agent = result.last_agent           
            

if __name__ == "__main__":

    asyncio.run(main())