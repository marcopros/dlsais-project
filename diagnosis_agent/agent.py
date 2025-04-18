from google.adk.agents import LlmAgent

from problem_agent.listener_agent import listener_agent
from problem_agent.diy_agent import diy_agent

# Create the orchestrator agent that will manage the interaction between the listener and DIY agents

root_agent = LlmAgent(
    name="orchestrator",
    model="gemini-2.0-flash",
    description="Orchestrator agent to manage the interaction between the listener_agent and diy_agent.",
    instruction="""You are the orchestrator of a home repair assistance system. 
                   Your role is to first engage the 'listener_agent' agent to understand the user's problem, 
                   then pass the details to the 'diy_agent'. Based on the 'diy_agent's' 
                   response, you will either present the DIY solution to the user or inform them that no DIY solution 
                   is available.""",
    sub_agents=[listener_agent, diy_agent]
)