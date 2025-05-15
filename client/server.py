import asyncio
import uvicorn
import logging
import uuid

from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Dict, Any

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


AGENT_URL = "http://localhost:8000/"        # Agent url
SESSION_ID = str(uuid.uuid4())              # Global session ID


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "session_id": SESSION_ID})


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_token(token)
    
    if payload is None:
        return '0'
    
    user_id = payload.get("id")
    
    if not user_id:
        raise Exception("User ID missing in token")

    return user_id


# Define the format of the message to the client 
def extract_agent_message(task_result):
    try:
        # Try to extract from artifacts first
        artifacts = getattr(task_result.result, "artifacts", [])
        for artifact in artifacts:
            if hasattr(artifact, "text") and artifact.text:
                agent = getattr(artifact, "metadata", {}).get("agent", "Unknown Agent")
                return {"text": artifact.text, "agent": agent}

        # If no artifacts, fall back to status.message.parts
        status = getattr(task_result.result, "status", None)
        if (
            status and
            hasattr(status, "message") and
            status.message and
            hasattr(status.message, "parts") and
            status.message.parts
        ):
            part = status.message.parts[0]
            if hasattr(part, "text") and part.text:
                agent = getattr(part, "metadata", {}).get("agent", "ERROR")
                return {"text": part.text, "agent": agent}

        return {"text": "[NESSUN MESSAGGIO RICEVUTO]", "agent": "ERROR"}

    except Exception as e:
        return {
            "text": f"[ERRORE ESTRAZIONE]: {type(e).__name__} - {e}",
            "agent": "ERROR"
        }


# Reuse your async ask_agent_with_a2a function here
async def ask_agent_with_a2a(agent_url: str, session_id: str, user_text: str):
    try:
        card_resolver = A2ACardResolver(agent_url)
        agent_card = card_resolver.get_agent_card()
        client = A2AClient(agent_card=agent_card)
        task_id = str(uuid.uuid4())

        # streaming = agent_card.capabilities.streaming
        streaming = False       # Streming is not alware implemented 

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
            logger.info(f'RESPONSE: {full_response}')
            return full_response.strip()
        else:
            taskResult = await client.send_task(payload)
            logger.info(f'RESPONSE: {taskResult}')
            return extract_agent_message(taskResult)

    except Exception as e:
        return f"[ERRORE]: {type(e).__name__} - {e}"




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

        # Use provided session ID or create a new one
        if not session_id:
            logger.info(f"No session_id provided, creating new one for user: {current_user}")
            
            # Call createUserSession and handle possible errors
            session_result = createUserSession(current_user)
            if not session_result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create session: {session_result['message']}"
                )
            session_id = session_result["session_id"]

        logger.info(f"Using session_id: {session_id} for user: {current_user}")

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