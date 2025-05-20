from datetime import datetime
import asyncio
import uvicorn
import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
from A2A.client import A2ACardResolver, A2AClient

from pymongo import MongoClient
from bson.json_util import dumps

from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="client/static"), name="static")
templates = Jinja2Templates(directory="client/template")

# Configure basic logging to output logs at the INFO level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

mongo_uri = os.getenv("MONGODB_URI")
client_mongo = MongoClient(mongo_uri)
db = client_mongo["home_repair_assistant"]  # <-- cambia con il nome vero
appointments_col = db["appointments"]

# Agent config
AGENT_URL = "http://localhost:8000/"

# Global session ID
SESSION_ID = str(uuid.uuid4())

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "session_id": SESSION_ID})

@app.get("/chat", response_class=HTMLResponse)
async def a2a_chat(request: Request):
    return templates.TemplateResponse("a2a_chat.html", {"request": request, "session_id": SESSION_ID})

@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "session_id": SESSION_ID})

@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page(
    request: Request,
    professional_id: str,
    job: str,
    name: Optional[str] = None,
):
    return templates.TemplateResponse(
        "submit-feedback.html",
        {
            "request": request,
            "professional_id": professional_id,
            "job": job,
            "name": name or "Professional",
        }
    )

from fastapi.responses import JSONResponse

@app.get("/appointments")
async def get_appointments():
    appointments = list(appointments_col.find())
    return JSONResponse(content=dumps(appointments), media_type="application/json")


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


from fastapi import Path
from pydantic import BaseModel

class AppointmentUpdate(BaseModel):
    status: str

@app.patch("/appointments/{appointment_id}")
async def update_appointment_status(appointment_id: str, payload: AppointmentUpdate):
    result = appointments_col.update_one(
        {"id": appointment_id},
        {
            "$set": {
                "status": payload.status,
                "updatedAt": datetime.utcnow()
            }
        }
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"success": True, "updated": result.modified_count}



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
async def send_message(data: dict):
    user_text = data.get("message")
    response = await ask_agent_with_a2a(AGENT_URL, SESSION_ID, user_text)
    return {"response": response}


if __name__ == "__main__":
    uvicorn.run("client.server:app", host="0.0.0.0", port=9000, reload=False)