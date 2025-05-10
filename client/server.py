import asyncio
import uvicorn
import logging
import uuid

from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr

from .auth import create_access_token, decode_token
from A2A.client import A2ACardResolver, A2AClient
from database.utils import registerUser, loginUser


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


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if payload is None:
        return "0"
    return payload["id"]

def extract_agent_message(task_result):
    try:
        # Verifica se ci sono artifacts con testo
        artifacts = getattr(task_result.result, "artifacts", [])
        for artifact in artifacts:
            if hasattr(artifact, "text") and artifact.text:
                return artifact.text

        # Se non ci sono artifacts validi, passa allo status.message
        status = getattr(task_result.result, "status", None)
        if (
            status and
            hasattr(status, "message") and
            status.message and
            hasattr(status.message, "parts") and
            status.message.parts
        ):
            return status.message.parts[0].text

        return "[NESSUN MESSAGGIO RICEVUTO]"

    except Exception as e:
        return f"[ERRORE ESTRAZIONE]: {type(e).__name__} - {e}"


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
async def send_message(data: dict, current_user: str = Depends(get_current_user)):
    user_text = data.get("message")
    logger.info(f'USER ID SENDER: {current_user}')
    response = await ask_agent_with_a2a(AGENT_URL, SESSION_ID, user_text)
    return {"response": response}



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
        logger.ERRORE(f"400 Bad Request: {message}")
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
    return {"access_token": access_token, "token_type": "bearer"}


if __name__ == "__main__":
    uvicorn.run("client.server:app", host="0.0.0.0", port=9000, reload=False)