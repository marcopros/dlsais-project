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
    handoff
)
from diagnosis_instructions import instructions as diagnosis_instructs
from diy_instructions import diy_instucts
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables from .env file
load_dotenv()

# --- Guardrail ---
class HomeIssueOutput(BaseModel):
    is_home_issue: bool
    reason: str
    
guardrail_agent = Agent(
    name="Guardrail agent",
    instructions="""
    Your job is to check if the input is a home issue or not.
    If it is a home issue, return True and the reason. If it is not, return False and the reason.
    """,
    model="gpt-4.1",
    output_type=HomeIssueOutput,
)

@input_guardrail
async def issue_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """
    This guardrail checks if the input is a home issue or not. Consider also that agent can ask for a series of details to understand the problem, so if the user responds to them it's ok.
    If it is a home issue, return True and the reason. If it is not, return False and the reason.
    """
    # Call the guardrail agent to check if the input is a home issue or not
    result = await Runner.run(guardrail_agent, input=input, context=ctx.context)
    
    # print("guardrail: ", result.final_output)
    # Return the result of the guardrail agent
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=(not result.final_output.is_home_issue), # Guardrail trigegrs tripwire in case the input is not related to the question
    )
   

# --- diagnosis agent ---
class HomeIssueOutput(BaseModel):
    found_root_cause: bool
    agent_response: str
    root_cause_info: str
    diy_solution: str | None

# --- DIY agent ---
diy_agent = Agent(
    name="DIY agent",
    instructions=diy_instucts,
    model="gpt-4.1",
    tools=[WebSearchTool()],
    output_type=HomeIssueOutput
)
 

async def on_diy_handoff(ctx: RunContextWrapper[None], input_data: HomeIssueOutput):
    print(f"DIY agent is looking for a solution for: {input_data.root_cause_info}")

diy_handoff = handoff(
    agent=diy_agent,
    on_handoff=on_diy_handoff,
    input_type=HomeIssueOutput
)

diagnosis_agent = Agent(
    name="Agent that seeks to find the root cause of a home issue",
    instructions=diagnosis_instructs,
    model="gpt-4.1",
    #input_guardrails=[issue_guardrail],
    output_type=HomeIssueOutput,
    handoffs=[diy_handoff]
)

async def main():
    
    with trace("Home issue diagnosis workflow"):
        try:
            result = await Runner.run(diagnosis_agent, input="My window is broken")
            print("Agent:", result.final_output.agent_response)
            
            while not result.final_output.found_root_cause:
                user_prompt = input("User: ")
                result = await Runner.run(diagnosis_agent, input=user_prompt)
                print("Agent:", result.final_output.agent_response)
                
            print("Detected cause of the problem: ", result.final_output.root_cause_info)
            print("DIY solution: ", result.final_output.diy_solution)
                
        except InputGuardrailTripwireTriggered as e:
            print(e.guardrail_result.output.output_info.reason)
            
            

if __name__ == "__main__":

    asyncio.run(main())

