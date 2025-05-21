from json import tool
from operator import call
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

from requests import session
from tools import (search_video_tutorial, update_user_settings)
from session import SessionService, SessionSettings
# Load environment variables from .env file
load_dotenv()


class DiagnosisAgentOut(BaseModel):
    unlock_request_for_diy_solution: bool
    agent_response: str
    detected_problem_cause: str | None
    diy_solution: str | None
    diy_links: list[str] | None # list of links to video or written tutorials
    call_professional: bool # if the user prefers to call a professional instead of doing it himself/herself


# --- DIY agent ---
diy_agent = Agent[SessionSettings](
    name="DIY agent",
    instructions=("you are given a home issue and you have to find a DIY solution to it. Search the web for a solution and provide a link to MAX 3 video tutorials from YouTube (do not make it up)."
                  "Follow accurately the setting provided in the context. "),
    model="gpt-4.1",
    tools=[WebSearchTool(), search_video_tutorial],
    output_type=DiagnosisAgentOut,
)
 

# --- Diagnosis agent ---
diagnosis_agent = Agent[SessionSettings](
    name="Diagnosis agent",
    instructions=(f"{RECOMMENDED_PROMPT_PREFIX}"
        """You are a home diagnosis expert. Your role is to analyze user-reported home issues, determine the likely cause,
            and provide a structured diagnosis.

            If the issue is unclear, ask clarifying questions before proceeding. Once diagnosed:
            - Summarize the issue and its cause clearly
            - If suitable, ask if user would like to get a DIY solution with links to video tutorials, in case use diy agent to get the results. Otherwise, call a professional.

            Always respect context from the session settings such as language, location, available time, and DIY capabilities.

            Your response MUST include:
            1. A clear diagnosis of the issue
            2. The detected problem cause
            3. The type of specialist needed (electrician, plumber, etc.)
            
            BONUS: grab useful infoormation to update user preferences using tool 'update_user_settings'."""
        ),
    model="gpt-4.1",
    tools=[diy_agent.as_tool(
        tool_name="propose_diy_solution",
        tool_description="Search the web a DIY solution relatively the founded root cause with a YouTube video tutorial link (do not make it up).",
    ), update_user_settings],
    output_type=DiagnosisAgentOut,
)


async def query_agent(query, session: SessionSettings) -> DiagnosisAgentOut:
    
    input_items: list[TResponseInputItem] = []
    current_agent: Agent[SessionSettings] = diagnosis_agent
    
    
    input_items.append({"content": query, "role": "user"})
    result = await Runner.run(current_agent, input=input_items, context=session)
        
    for new_item in result.new_items:
        agent_name = new_item.agent.name
            
        if isinstance(new_item, MessageOutputItem):
            parsed = json.loads(ItemHelpers.text_message_output(new_item))
            print(f"{agent_name}: {parsed["agent_response"]}")
            if parsed["unlock_request_for_diy_solution"]:
                print("Unlocking DIY agent...")
                current_agent = diy_agent
            if parsed["diy_solution"] != None:
                print(f"DIY solution: {parsed["diy_solution"]}")
            if parsed["diy_links"] != None:
                print(f"DIY links: {parsed["diy_links"]}")
            if parsed["call_professional"]:
                print("User prefers to call a professional.")
            
            print("debug:\n", parsed)
        
    input_items = result.to_input_list()
    current_agent = result.last_agent 
              
    return parsed        

if __name__ == "__main__":
    session_id = "1234567890"
    session = SessionService(user_id="user-1")
    session = session.create_session(session_id=session_id)
    
    task_finished = False
    while task_finished == False:
        with trace("Home issue diagnosis workflow"):
            query = input("[User]: ")
            result = asyncio.run(query_agent(query, session=session))
            print(f"[Agent]: {result["agent_response"]}")
            if result["call_professional"]:
                task_finished = True