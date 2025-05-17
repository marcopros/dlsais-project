import asyncio
import uvicorn
import logging
import uuid
import json

from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
from bson.objectid import ObjectId

from .auth import create_access_token, decode_token
from A2A.client import A2ACardResolver, A2AClient
from database.utils import registerUser, loginUser, createUserSession


app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="client/static"), name="static")
templates = Jinja2Templates(directory="client/template")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Configure basic logging to output logs at the INFO level
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ID utente predefinito per utenti non autenticati (utente Matteo già nel DB)
DEFAULT_USER_ID = "68274572776ba43fab29640c"

# Per facilitare i test, l'agente può essere cambiato qui
# Valori possibili:
# - "http://localhost:8000/" # orchestrator (inizia qui)
# - "http://localhost:8001/" # diagnosis
# - "http://localhost:8002/" # matching
# - "http://localhost:8003/" # appointment
AGENT_URL = "http://localhost:8000/"        # Orchestrator - il primo da chiamare
SESSION_ID = str(uuid.uuid4())              # Global session ID


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "session_id": SESSION_ID})


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_token(token)
    
    if payload is None:
        # Per utenti non autenticati, restituisci l'ID predefinito
        return DEFAULT_USER_ID
    
    user_id = payload.get("id")
    
    if not user_id:
        raise Exception("User ID missing in token")

    return user_id


# Define the format of the message to the client 
def extract_agent_message(task_result):
    try:
        logger.info(f"Extracting message from task_result type: {type(task_result)}")
        
        # Check if task_result is a string (already formatted error message)
        if isinstance(task_result, str):
            if "[ERRORE]" in task_result:
                return {"text": task_result, "agent": "ERROR"}
            return {"text": task_result, "agent": "Agent"}
        
        # Handle Task objects (which don't have a get method)
        if hasattr(task_result, 'result'):
            result_obj = task_result.result
            
            # Try to determine agent type from task result
            agent_type = "Agent"
            
            # Check URL in task.source if available to determine agent type
            if hasattr(result_obj, 'source') and result_obj.source:
                url = str(result_obj.source).lower()
                if 'diagnosis' in url:
                    agent_type = "Diagnosis Agent"
                elif 'matching' in url:
                    agent_type = "Matching Agent"
                elif 'appointment' in url:
                    agent_type = "Appointment Agent"
                elif 'feedback' in url:
                    agent_type = "Feedback Agent"
                elif 'orchestrator' in url:
                    agent_type = "Orchestrator"
            
            # Check if result contains status with message
            if hasattr(result_obj, 'status') and hasattr(result_obj.status, 'message'):
                message = result_obj.status.message
                if hasattr(message, 'parts') and message.parts:
                    for part in message.parts:
                        if hasattr(part, 'text') and part.text:
                            return {
                                "text": part.text,
                                "agent": agent_type
                            }
            
            # Check for artifacts
            if hasattr(result_obj, 'artifacts') and result_obj.artifacts:
                for artifact in result_obj.artifacts:
                    if hasattr(artifact, 'parts') and artifact.parts:
                        for part in artifact.parts:
                            if hasattr(part, 'text') and part.text:
                                try:
                                    diag_data = json.loads(part.text)
                                    if isinstance(diag_data, dict):
                                        # Format diagnosis nicely if it's JSON data
                                        text = diag_data.get('agent_response', '')
                                        if diag_data.get('diagnosis'):
                                            text += f"\n\nDiagnosi: {diag_data.get('diagnosis')}"
                                        if diag_data.get('detected_problem_cause'):
                                            text += f"\nCausa: {diag_data.get('detected_problem_cause')}"
                                        if diag_data.get('type_specialist'):
                                            text += f"\nSpecialista: {diag_data.get('type_specialist')}"
                                        return {"text": text, "agent": agent_type}
                                except:
                                    # If not JSON, return as is
                                    return {"text": part.text, "agent": agent_type}
        
        # Handle dictionary results
        if isinstance(task_result, dict):
            # Check if it already contains 'text' and 'agent'
            if 'text' in task_result and 'agent' in task_result:
                return task_result
                
            # Determine agent type from task result if available
            agent_type = "Agent"
            
            # Try to identify agent type from the content
            content = str(task_result).lower()
            if "diagnosis" in content:
                agent_type = "Diagnosis Agent"
            elif "matching" in content or "professionals" in content or "plumber" in content or "electrician" in content:
                agent_type = "Matching Agent"
            elif "appointment" in content or "scheduling" in content or "schedule" in content:
                agent_type = "Appointment Agent"
            elif "feedback" in content or "review" in content:
                agent_type = "Feedback Agent"
                
            # Check for various dictionary formats...
            if 'result' in task_result:
                result = task_result['result']
                if isinstance(result, dict):
                    # Format 1: Direct text in result
                    if 'text' in result:
                        return {
                            "text": result['text'], 
                            "agent": result.get('agent', agent_type)
                        }
                        
                    # Format 2: status/message in result 
                    if 'status' in result and 'message' in result['status']:
                        msg = result['status']['message']
                        if isinstance(msg, dict) and 'text' in msg:
                            return {
                                "text": msg['text'],
                                "agent": msg.get('agent', agent_type)
                            }
                        elif isinstance(msg, dict) and 'parts' in msg:
                            for part in msg['parts']:
                                if 'text' in part:
                                    return {
                                        "text": part['text'],
                                        "agent": agent_type
                                    }
                            
                    # Format 3: artifacts in result
                    if 'artifacts' in result and result['artifacts']:
                        for artifact in result['artifacts']:
                            if 'parts' in artifact and artifact['parts']:
                                for part in artifact['parts']:
                                    if 'text' in part:
                                        try:
                                            # Try to parse as JSON (diagnosis agent format)
                                            diag_data = json.loads(part['text'])
                                            if isinstance(diag_data, dict):
                                                text = diag_data.get('agent_response', '')
                                                if diag_data.get('diagnosis'):
                                                    text += f"\n\nDiagnosi: {diag_data.get('diagnosis')}"
                                                if diag_data.get('detected_problem_cause'):
                                                    text += f"\nCausa: {diag_data.get('detected_problem_cause')}"
                                                if diag_data.get('type_specialist'):
                                                    text += f"\nSpecialista: {diag_data.get('type_specialist')}"
                                                return {"text": text, "agent": "Diagnosis Agent"}
                                        except:
                                            # Not JSON, return as is
                                            return {
                                                "text": part['text'],
                                                "agent": agent_type
                                            }
            
            # Check if it contains direct diagnosis info
            if 'diagnosis' in task_result:
                # Handle diagnosis agent format
                text = task_result.get('agent_response', '')
                if task_result.get('diagnosis'):
                    text += f"\n\nDiagnosi: {task_result.get('diagnosis')}"
                if task_result.get('detected_problem_cause'):
                    text += f"\nCausa: {task_result.get('detected_problem_cause')}"
                if task_result.get('type_specialist'):
                    text += f"\nSpecialista: {task_result.get('type_specialist')}"
                return {"text": text, "agent": "Diagnosis Agent"}

        logger.warning(f"Could not extract message, returning default message")
        return {
            "text": "Non ho capito la risposta dell'agente. Prova a riformulare la domanda.", 
            "agent": "System"
        }

    except Exception as e:
        logger.error(f"Error extracting message: {str(e)}", exc_info=True)
        return {
            "text": f"[ERRORE]: {type(e).__name__} - {str(e)}",
            "agent": "ERROR"
        }


# Reuse your async ask_agent_with_a2a function here
async def ask_agent_with_a2a(agent_url: str, session_id: str, user_text: str):
    try:
        logger.info(f"Connecting to agent at {agent_url}")
        # Usa un timeout più breve per evitare attese troppo lunghe
        timeout = 30  # secondi
        
        # Crea un task con timeout
        async with asyncio.timeout(timeout):
            card_resolver = A2ACardResolver(agent_url)
            agent_card = card_resolver.get_agent_card()
            client = A2AClient(agent_card=agent_card)
            task_id = str(uuid.uuid4())

            # streaming = agent_card.capabilities.streaming
            streaming = False       # Streaming is not always implemented 

            payload = {
                "id": task_id,
                "sessionId": session_id,
                "acceptedOutputModes": ["text"],
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": user_text}],
                    "id": str(uuid.uuid4()),
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            }

            if streaming:
                response_stream = client.send_task_streaming(payload)
                full_response = ""
                async for result in response_stream:
                    text = result.model_dump(exclude_none=True)
                    full_response += text.get('content', '')
                logger.info(f'Stream response received')
                return full_response.strip()
            else:
                logger.info(f'Sending task to agent')
                taskResult = await client.send_task(payload)
                logger.info(f'Response received')
                
                # Determine the agent type based on the URL
                agent_type = "Agent"
                if "8000" in agent_url or "orchestrator" in agent_url.lower():
                    agent_type = "Orchestrator"
                elif "8001" in agent_url or "diagnosis" in agent_url.lower():
                    agent_type = "Diagnosis Agent"
                elif "8002" in agent_url or "matching" in agent_url.lower():
                    agent_type = "Matching Agent"
                elif "8003" in agent_url or "appointment" in agent_url.lower():
                    agent_type = "Appointment Agent"
                    
                # Extract the message with the correct agent type
                result = extract_agent_message(taskResult)
                
                # Override the agent type if we detected it from the URL
                if agent_type != "Agent":
                    result["agent"] = agent_type
                    
                return result

    except asyncio.TimeoutError:
        logger.error(f"Timeout connecting to agent at {agent_url}")
        return {
            "text": f"[ERRORE]: Timeout nella connessione all'agente. Assicurati che il servizio dell'agente sia in esecuzione su {agent_url}",
            "agent": "System"
        }
    except Exception as e:
        logger.error(f"Error in ask_agent_with_a2a: {type(e).__name__} - {e}", exc_info=True)
        return {
            "text": f"[ERRORE]: {type(e).__name__} - {str(e)}",
            "agent": "System"
        }




@app.post("/send_message")
async def send_message(
    data: Dict[str, Any],
    current_user: str = Depends(get_current_user)
):
    try:
        user_text = data.get("message")
        session_id = data.get("session_id")

        if not user_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required"
            )

        # Se non c'è una sessione, usa quella di default
        if not session_id:
            logger.info(f"Using default session ID: {SESSION_ID}")
            session_id = SESSION_ID
            
        # Get both text and agent from agent call
        result = await ask_agent_with_a2a(AGENT_URL, session_id, user_text)
        
        return {
            "response": result["text"],         # <-- From agent response
            "agent": result["agent"],           # <-- New field
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Error in /send_message: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred"
        )



class User(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str

@app.post("/register")
async def register_user(user: User):
    result = registerUser(user.name, user.email, user.password, user.phone)
    
    if not result["success"]:
        message = result['message']
        logger.error(f"400 Bad Request: {message}")
        raise HTTPException(status_code=400, detail=message)
    return result



class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/login")
async def login_user(user: LoginRequest):
    result = loginUser(user.email, user.password)

    if not result["success"]:
        message = result['message']
        logger.error(f"401 Unauthorized: {message}")
        raise HTTPException(status_code=401, detail=message)

    user_data = result['user']
    
    access_token = create_access_token(data={"id": user_data["id"]})
    
    return {
        "user": {
            "name": user_data["name"],
            "email": user_data["email"],
            "phone": user_data["phone"]
        },
        "access_token": access_token,
        "token_type": "bearer",
        "sessions": user_data.get("sessions", [])  # <-- Include sessions
    }


if __name__ == "__main__":
    uvicorn.run("client.server:app", host="0.0.0.0", port=9000, reload=False)