from datetime import datetime
import asyncio
import uvicorn
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from A2A.client import A2ACardResolver, A2AClient

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


# Agent config
AGENT_URL = "http://localhost:8000/"

# Global session ID
SESSION_ID = str(uuid.uuid4())

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "session_id": SESSION_ID})

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
            return taskResult.model_dump(exclude_none=True).get('content', '')

    except Exception as e:
        return f"[ERRORE]: {type(e).__name__} - {e}"


@app.post("/send_message")
async def send_message(data: dict):
    user_text = data.get("message")
    response = await ask_agent_with_a2a(AGENT_URL, SESSION_ID, user_text)
    return {"response": response}


if __name__ == "__main__":
    uvicorn.run("client.server:app", host="0.0.0.0", port=9000, reload=False)