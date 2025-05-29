from email import message
from typing import List, Optional, Dict

from agents import Agent, function_tool, WebSearchTool

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel

from json import load, tool
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

from instructions import actor_agent_instructions
from agent import diagnosis_agent, DiagnosisAgentOut, DiagnosisContext

load_dotenv()

    
    
actor_agent = Agent(
    name="Actor agent",
    instructions=actor_agent_instructions,
    model="gpt-4.1"
)


Message = Dict[str, str]        # {"role": "user"/"agent", "content": "...", links: "..."}
Conversation = List[Message]


async def simulate_case(test_case: Dict[str, str], max_turn_pairs: int = 11,):
    """
        Run a back-and-forth chat between two agents until the actor emits 'END'
        or the max number of turn-pairs is reached.

        Parameters
        ----------
        test_case        minimal keys: 'category', 'user_scenario'
        actor_agent      fn(context, conversation) -> next user message
        diagnosis_agent  fn(conversation_so_far)   -> next diagnosis reply
        max_turn_pairs   safety cap against infinite loops

        Returns
        -------
        conversation : list[{"role": "...", "content": "..."}]
    """
    
    
    # Initialize diagnosis context
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
    
   
    convo: Conversation = []
    first_message = {
        "user_scenario": test_case["user_scenario"],
        "category": test_case["category"],
    }
    first_message = json.dumps(first_message)  # Convert to JSON string for the agent input
    
    input_actor_items: list[TResponseInputItem] = []
    input_diagnosis_items: list[TResponseInputItem] = []

    input_actor_items.append({"content": first_message, "role": "user"})
    
    diagnosis = None
    diy_solution = None
    diy_links = None
    
    for _ in range(max_turn_pairs):
        
        # 1) actor creates the next USER turn
        actor_result = await Runner.run(actor_agent, input=input_actor_items)
        print(f"🎭 Actor: {actor_result.final_output}")
        
        convo.append({"role": "user", "content": actor_result.final_output})
        if "END" in actor_result.final_output:
            print("🏁 END of conversation")
            break

        # 2) diagnosis agent answers
        input_diagnosis_items.append({"content": actor_result.final_output, "role": "user"})
        diagnosis_result = await Runner.run(diagnosis_agent, input=input_diagnosis_items, context=settings)
        print(f"🩺 Diagnosis: {diagnosis_result.final_output.agent_response}")
        
        message_output = {"role": "agent", "content": diagnosis_result.final_output.agent_response} # prepare the message output to append to the conversation
        
        diagnosis_msg = diagnosis_result.final_output.agent_response
        
        # update outputs
        diagnosis = diagnosis_result.final_output.diagnosis
        diy_solution = diagnosis_result.final_output.diy_solution
        
        # 3) check if the diagnosis agent provided tutorial links
        if diagnosis_result.final_output.diy_links is not None:
            print(f"🎥 DIY links: {diagnosis_result.final_output.diy_links}")
            yt_links = diagnosis_result.final_output.diy_links
            message_output["tutorial_links"] = yt_links     # add links to the message output
            diagnosis_msg += f"\nTutorial Links: {yt_links}"
            diy_links = diagnosis_result.final_output.diy_links
        
        convo.append(message_output)
        input_actor_items.append({"content": diagnosis_msg, "role": "user"}) # prepare the next input for the actor agent

    return convo, diagnosis, diy_solution, diy_links
    
            

# --- your async simulator ----------------------------------------------------
# assume simulate_case(case)  ->  list[{"role": "...", "content": "..."}]
# -----------------------------------------------------------------------------


async def main(
    in_path: str = "test_cases.json",
    out_path: str = "test_cases_with_conversations.json",
):
    # 1. Load the original list of cases
    with open(in_path, "r", encoding="utf-8") as f:
        cases = json.load(f)  # list[dict]

    # 2. Run one simulation per case
    for i, c in enumerate(cases):
        print(f"\nSimulating case {i + 1}/{len(cases)}: {c['category']} – {c.get('id', 'no-id')}")

        # Run simulation
        conversation, diagnosis, diy_solution, links = await simulate_case(c)

        # Save results in current case
        c["conversation"] = conversation
        c["diagnosis"] = diagnosis
        c["diy_solution"] = diy_solution
        c["diy_links"] = links

        # Save progress so far (overwrite the file each time)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(cases, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Failed to save after case {i + 1}: {e}")

    print(f"\n✅ Saved all {len(cases)} cases to {out_path}")

# -----------------------------------------------------------------------------  
# kick the coroutine
# -----------------------------------------------------------------------------  
if __name__ == "__main__":
    asyncio.run(main())
