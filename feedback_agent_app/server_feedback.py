# server_feedback.py

import json
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from orchestrator.server import APP_NAME
from pydantic import BaseModel
from typing import Any, Dict
from fastapi.middleware.cors import CORSMiddleware
from agent import feedback_agent
from agents import Runner, MessageOutputItem, ItemHelpers, trace
from A2A.server import A2AServer
from A2A.types import AgentCard, MissingAPIKeyError
from dotenv import load_dotenv
import uvicorn
import os

# Local imports for the agent logic and task manager
from .agent import feedback_agent
from .task_manager import FeedbackAgentTaskManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

APP_NAME = "feedback_agent_app"  # Logical name for this agent app
USER_ID = "1"  # Default user ID; used when associating sessions/tasks with a user

async def run_server():
    """Initializes services and starts the A2AServer."""

    if not os.getenv('OPENAI_API_KEY'):
        raise MissingAPIKeyError(
            'OPENAI_API_KEY environment variable not set.'
    )


    logger.info("Starting Matching Diagnosis A2A Server initialization...")

    try:
        # The agent instance that will process user inputs and generate responses
        agent = feedback_agent

        # Instantiate the custom task manager that handles A2A streaming and task execution 
        task_manager = DiagnosisAgentTaskManager(agent)

        # Determine the port and host from environment variables
        port = int(os.getenv("PORT", "8003"))
        host = os.getenv("HOST", "localhost")
        listen_host = "0.0.0.0"  # Allow external connections

        # Load the AgentCard configuration from a JSON file
        with open("feedback_agent_app/a2a_agent_card.json", "r") as f:
            agent_card_data = json.load(f)

        # Convert the dictionary into an AgentCard object expected by the A2A framework
        agent_card = AgentCard(**agent_card_data)

        # Initialize the A2A server with the agent card and task manager
        a2a_server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=listen_host,
            port=port
        )

        # Configure Uvicorn (the ASGI server) to run the A2A application
        config = uvicorn.Config(
            app=a2a_server.app,
            host=listen_host,
            port=port,
            log_level="info"
        )

        # Create and start the Uvicorn server
        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        # Log any exceptions during startup and exit gracefully
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    # Run the async server using asyncio
    asyncio.run(run_server())

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
