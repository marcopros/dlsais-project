import os
import json
import logging
from typing import Optional, Dict, Any, List
import openai
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use OpenAI API key from environment variables
# Verifica se la chiave è disponibile nell'ambiente
if not os.getenv("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY not found in environment variables. Some functionality may not work.")

# Remove any custom API base URL to ensure we're using the official OpenAI API
if "OPENAI_API_BASE" in os.environ:
    del os.environ["OPENAI_API_BASE"]

# Esplicitamente configuriamo il client per utilizzare l'endpoint standard di OpenAI
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.openai.com/v1"  # Forziamo l'URL ufficiale di OpenAI
)
logger.info(f"OpenAI client configurato con URL base: {client.base_url}")

# --- OUTPUT DEF ---
class DiagnosisAgentOut(BaseModel):
    agent_response: str                 # summary of the diagnosis agent 
    # Diagnosis Fields
    diagnosis: str | None = None
    detected_problem_cause: str | None = None
    type_specialist: str | None = None
    # DIY Fields
    unlock_request_for_diy_solution: bool = False
    diy_solution: str | None = None
    diy_links: list[str] | None = None  # list of links to video or written tutorials

# --- SESSION ----
class SessionSettings(BaseModel):
    search_for_diy_solution: bool = False
    user_location: Optional[str] = None
    user_diy_skills: Optional[str] = None
    user_diy_tools: Optional[List[str]] = None
    home_type: Optional[str] = None
    solution_preferences: Optional[str] = None
    time_available_for_repair: Optional[str] = None
    favourite_language: str = "Italian"

# SISTEMA DI PROMPT per l'agente di diagnosi
SYSTEM_PROMPT = """
    You are a **Home Diagnosis Expert**. Your role is to analyze user-reported household issues, identify likely causes, and provide a structured and actionable diagnosis.

    ## GENERAL INSTRUCTIONS
    1. Try to **understand the user's issue** as clearly as possible while deriving a diagnosis, cause and type_specialist
    2. If the issue is unclear, ask **explicit and clear follow-up questions** to gather essential details before proceeding.
    3. Be attentive to the ENTIRE conversation history and don't ask for information that has already been provided.
    4. Recognize short affirmative responses ("si", "yes", "ok") as acknowledgements and try to proceed with diagnosis.
    5. If the user mentions a specific professional (like "plumber", "electrician"), assume they want that type of specialist.
    6. When possible, make educated guesses about the problem cause based on the symptoms described.
    7. Once the problem is understood, your response MUST include all of the following:

    ### STRUCTURED OUTPUT (JSON format)
    Return your response as a **valid JSON** with these fields:

    - `"agent_response"`  A concise summary of your diagnosis. If more information is needed, specify exactly what is missing.
    - `"diagnosis"`  A clear and specific diagnosis of the issue. Use `null` if the issue is not yet diagnosed.
    - `"detected_problem_cause"` The most likely root cause of the issue. Use `null` if undetermined.
    - `"type_specialist"`  The type of professional required (e.g., electrician, plumber). Use `null` if undetermined.
    - `"unlock_request_for_diy_solution"` A boolean indicating whether a DIY solution is possible based on the user's context (skills, tools, preferences).
    - `"diy_solution"`  A DIY fix, if applicable and safe. Use `null` if not applicable.
    - `"diy_links"`  Video tutorial links that guide the user through the DIY process. Use `null` if not applicable.

    ## EVALUATION & RESPONSE STRATEGY
    - Always respect the session context: user location, time availability, DIY experience, and language.
    - If the issue **can be safely resolved** by the user:
        - Provide a clear step-by-step DIY solution.
        - Include **reliable video tutorials** as support.
    - If the issue **requires a specialist**, state the type and explain why.
    - Be decisive when you have enough information - don't keep asking questions unnecessarily.
"""

class Agent:
    """A simplified agent class that provides the interface expected by the task manager"""
    def __init__(self, name, model, instructions, output_type):
        self.name = name
        self.model = model
        self.instructions = instructions
        self.output_type = output_type

# Direct function to query the model
async def query_openai(query: str, session: SessionSettings) -> DiagnosisAgentOut:
    """
    Query the OpenAI model directly.
    
    Args:
        query: The user's input message
        session: Session settings
    
    Returns:
        A DiagnosisAgentOut instance with the agent's response
    """
    try:
        # Assicuriamoci che non ci siano variabili d'ambiente che reindirizzano a OpenRouter
        if "OPENAI_API_BASE" in os.environ:
            del os.environ["OPENAI_API_BASE"]
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]
            
        # Ricreiamo il client OpenAI ogni volta per essere sicuri
        api_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1"
        )
        logger.info(f"Client OpenAI ricreato con URL base: {api_client.base_url}")
            
        # Convert session to dict for including in prompt
        session_dict = session.model_dump() if hasattr(session, 'model_dump') else session.__dict__
        
        logger.info(f"Querying OpenAI with: {query}")
        logger.info(f"Session data: {session_dict}")
        
        # Prepare messages for the API call with conversation history
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Session context: {json.dumps(session_dict)}"}
        ]
        
        # Aggiungi la cronologia delle conversazioni se presente
        if hasattr(session, 'conversation_history') and session.conversation_history:
            # Aggiungi tutti i messaggi precedenti dalla cronologia (max 10 per non esagerare con il contesto)
            for msg in session.conversation_history[-10:]:
                messages.append(msg)
        
        # Aggiungi il messaggio corrente dell'utente
        messages.append({"role": "user", "content": query})
        
        # Call the OpenAI API usando il client appena creato
        response = api_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Usiamo un modello standard supportato
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Extract the response content
        content = response.choices[0].message.content
        logger.info(f"OpenAI response content: {content}")
        
        # Parse the JSON response
        try:
            result_dict = json.loads(content)
            
            # Assicuriamoci che tutti i campi abbiano valori validi
            if result_dict.get('unlock_request_for_diy_solution') is None:
                result_dict['unlock_request_for_diy_solution'] = False
            
            # Campi che possono essere null, ma devono essere presenti
            if 'diagnosis' not in result_dict or result_dict['diagnosis'] is None:
                result_dict['diagnosis'] = None
            
            if 'detected_problem_cause' not in result_dict or result_dict['detected_problem_cause'] is None:
                result_dict['detected_problem_cause'] = None
                
            if 'type_specialist' not in result_dict or result_dict['type_specialist'] is None:
                result_dict['type_specialist'] = None
                
            if 'diy_solution' not in result_dict or result_dict['diy_solution'] is None:
                result_dict['diy_solution'] = None
                
            if 'diy_links' not in result_dict or result_dict['diy_links'] is None:
                result_dict['diy_links'] = None
                
            # Create a DiagnosisAgentOut object from the response
            return DiagnosisAgentOut(**result_dict)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            # Return a default response with the error message
            return DiagnosisAgentOut(
                agent_response=f"Error parsing response: {str(e)}. Raw response: {content}",
                diagnosis="Errore di risposta",
                detected_problem_cause="Errore di elaborazione",
                type_specialist="Supporto tecnico",
                unlock_request_for_diy_solution=False,
                diy_solution=None,
                diy_links=None
            )
    except Exception as e:
        logger.error(f"Error in query_openai: {type(e).__name__} - {str(e)}")
        # Return a default response with the error message
        return DiagnosisAgentOut(
            agent_response=f"Si è verificato un errore: {str(e)}",
            diagnosis="Errore di sistema",
            detected_problem_cause="Errore di comunicazione",
            type_specialist="Supporto tecnico",
            unlock_request_for_diy_solution=False,
            diy_solution=None,
            diy_links=None
        )

# Mock the Runner class expected by the task manager
class Runner:
    @classmethod
    async def run(cls, agent, input_query, context=None):
        """
        Run the agent on the input query.
        This is a simplified version that directly calls query_openai.
        """
        return await query_openai(input_query, context or SessionSettings())

# Create a mock agent that will be used by the task manager
diagnosis_agent = Agent(
    name="Diagnosis agent",
    model="gpt-3.5-turbo",
    instructions=SYSTEM_PROMPT,
    output_type=DiagnosisAgentOut
)