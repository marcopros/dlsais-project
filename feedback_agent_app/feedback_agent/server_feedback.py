# server_feedback.py

import json
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from fastapi.middleware.cors import CORSMiddleware
from agent import feedback_agent
from agents import Runner, MessageOutputItem, ItemHelpers, trace

app = FastAPI(title="Feedback Sentiment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class FeedbackRequest(BaseModel):
    feedback: Dict[str, Any]  # accetta JSON arbitrario nel campo "feedback"

@app.post("/analyze")
async def analyze_feedback(req: FeedbackRequest):
    """Analizza il feedback ricevuto e restituisce i punteggi calcolati."""
    input_json = json.dumps(req.feedback)

    input_items = [{"content": input_json, "role": "user"}]

    with trace("Feedback analysis workflow"):
        result = await Runner.run(feedback_agent, input=input_items)

        for item in result.new_items:
            if isinstance(item, MessageOutputItem):
                parsed = json.loads(ItemHelpers.text_message_output(item))
                return parsed

    raise HTTPException(status_code=500, detail="Agent did not return a valid result")

# to run the server, use the command:
# uvicorn server_feedback:app --reload
