import uuid
import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from agents import (
    Agent,
    Runner,
    trace,
    MessageOutputItem,
    ItemHelpers,
    TResponseInputItem,
    function_tool,
    WebSearchTool
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# carica le variabili d’ambiente (.env)
load_dotenv()

app = FastAPI(title="Home-Repair Multi-Agent API")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"]
)


# ——— MODELLI Pydantic ———
class SessionSettings(BaseModel):
    search_for_diy_solution: bool = False
    user_location: Optional[str]
    user_diy_skills: Optional[str]
    user_diy_tools: Optional[List[str]]
    home_type: Optional[str]
    solution_preferences: Optional[str]
    time_available_for_repair: Optional[str]
    favourite_language: str = "English"

class UserMessage(BaseModel):
    session_id: str
    content: str

class AgentResponse(BaseModel):
    session_id: str
    agent: str
    agent_response: str
    detected_problem_cause: Optional[str]
    diy_solution: Optional[str]
    diy_links: Optional[List[str]]
    call_professional: bool
    diy_agent_unlocked: bool

# ——— INIZIALIZZAZIONE DEGLI AGENTI ———
# (importa o definisci qui search_video_tutorial, diagnosis_agent, diy_agent come nel tuo script)

# …[definizione search_video_tutorial identica al tuo script]…

from agent import search_video_tutorial, diagnosis_agent, diy_agent, DiagnosisAgentOut

# DIY agent
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

# Diagnosis agent
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

# ——— STORAGE DELLE SESSIONI (in memoria) ———
sessions = {}

# struttura interna per ogni sessione
class SessionState:
    def __init__(self, settings: SessionSettings):
        self.settings = settings
        self.input_items: List[TResponseInputItem] = []
        self.current_agent = diagnosis_agent

# ——— ENDPOINTS ———

@app.post("/start", response_model=str)
async def start_session(settings: SessionSettings):
    """Crea una nuova sessione e restituisce lo session_id"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = SessionState(settings)
    return session_id

@app.post("/message", response_model=AgentResponse)
async def handle_message(msg: UserMessage):
    """Riceve un messaggio dall’utente, lo passa all’agente corrente e risponde."""
    state = sessions.get(msg.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1) aggiungi input
    state.input_items.append({"content": msg.content, "role": "user"})

    # 2) esegui Runner
    with trace(f"Session {msg.session_id}"):
        result = await Runner.run(
            state.current_agent,
            input=state.input_items,
            context=state.settings
        )

    # 3) processa l’output
    diy_agent_unlocked = False  # 🔥 aggiunto flag

    for item in result.new_items:
        if isinstance(item, MessageOutputItem):
            parsed = json.loads(ItemHelpers.text_message_output(item))

            # Se viene richiesto lo sblocco, cambia l’agente e imposta il flag
            if parsed.get("unlock_request_for_diy_solution"):
                state.current_agent = diy_agent
                diy_agent_unlocked = True

            # aggiorna input per la prossima chiamata
            state.input_items = result.to_input_list()

            return AgentResponse(
                session_id=msg.session_id,
                agent=item.agent.name,
                agent_response=parsed["agent_response"],
                detected_problem_cause=parsed.get("detected_problem_cause"),
                diy_solution=parsed.get("diy_solution"),
                diy_links=parsed.get("diy_links"),
                call_professional=parsed.get("call_professional", False),
                diy_agent_unlocked=diy_agent_unlocked  # 🔥 incluso nella risposta
            )

    raise HTTPException(status_code=500, detail="Agent did not return a message")


# ——— ESEMPIO DI ESECUZIONE ———
# Avvia con: uvicorn server:app --reload --host 0.0.0.0 --port 8000
