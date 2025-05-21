from pydantic import BaseModel
from agents import (
    Agent, 
    Runner, 
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
)

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