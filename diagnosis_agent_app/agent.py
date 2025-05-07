import os
import aiohttp

from typing import List, Optional

from agents import Agent, function_tool, WebSearchTool

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel



'''
# Load environment variables from .env file
load_dotenv()

# CONTEXT
class DiagnosisSettingsContext(BaseModel):
    search_for_diy_solution: bool = False
    user_location: str | None = None
    user_diy_skills: Literal['beginner', 'intermediate', 'expert'] = None
    user_diy_tools: list | None = None # screwdriver, hammer, drill, etc.
    home_type: str | None = None #apartment, detached house, villa, other...
    solution_preferences: Literal['temporary', 'permanent'] = None
    time_available_for_repair: Literal['few minutes', 'hours', 'weekend'] = None
    favourite_language: str = "English" # Italian, English, French, etc.
'''    



# --- OUTPUT DEF ---
class DiagnosisAgentOut(BaseModel):
    unlock_request_for_diy_solution: bool
    agent_response: str
    detected_problem_cause: str | None
    diy_solution: str | None
    diy_links: list[str] | None # list of links to video or written tutorials
    call_professional: bool # if the user prefers to call a professional instead of doing it himself/herself


# --- SESSION ----
class SessionSettings(BaseModel):
    search_for_diy_solution: bool = False
    user_location: Optional[str]
    user_diy_skills: Optional[str]
    user_diy_tools: Optional[List[str]]
    home_type: Optional[str]
    solution_preferences: Optional[str]
    time_available_for_repair: Optional[str]
    favourite_language: str = "English"



# --- DIY AGENT ---
@function_tool
async def search_video_tutorial(query: str, hl: str, gl: str) -> List[str]:
    """ Searches YouTube for video tutorials matching the given query.
        Returns a list of YouTube watch URLs.
    Args:
        query (str): The search query for the video tutorial.
        hl (str): The language code for the search results (e.g., 'it' for Italian).
        gl (str): The country code for the search results (e.g., 'it' for Italy).
    """
    # Add the site filter to the query to search only for YouTube videos
    full_query = f"{query} site:youtube.com"
    url = "https://serpapi.com/search"
    params = {
        "q": full_query,
        "hl": hl,
        "gl": gl,
        "engine": "google",
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    # Extract video links from the response
    videos: List[str] = []
    for item in data.get("organic_results", []):
        link = item.get("link", "")
        if "youtube.com/watch" in link:
            videos.append(link)

    # Provide only the first 5 links
    return videos[:5]


diy_agent = Agent[SessionSettings](
    name="DIY agent",
    instructions=(
        "You are given a home issue and you have to find a DIY solution to it. "
        "Search the web for a solution and provide a link to a video tutorial from YouTube."
        "Follow the settings provided in the context."
    ),
    model="gpt-4.1",
    tools=[WebSearchTool(), search_video_tutorial],
    output_type=DiagnosisAgentOut,
)


 

# --- DIAGNOSIS AGENT ---
diagnosis_agent = Agent[SessionSettings](
    name="Diagnosis agent",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}"
        "Your job is to find the root cause of the home issue and ask for a DIY solution or suggest a professional. "
        "Ask clarifications if needed."
    ),
    model="gpt-4.1",
    tools=[diy_agent.as_tool(
        tool_name="propose_diy_solution",
        tool_description="Search the web for a DIY solution with a YouTube video link."
    )],
    output_type=DiagnosisAgentOut,
)






'''
async def main():
    input_items: list[TResponseInputItem] = []
    current_agent: Agent[DiagnosisSettingsContext] = diagnosis_agent
    
    settings = DiagnosisSettingsContext(
        search_for_diy_solution=True,
        user_location="Italy",
        user_diy_skills="intermediate",
        user_diy_tools=["screwdriver", "hammer", "drill"],
        home_type="house",
        solution_preferences="permanent",
        time_available_for_repair="hours",
        favourite_language="Italian"
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
'''
