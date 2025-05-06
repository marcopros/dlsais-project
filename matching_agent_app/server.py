import os
import json
import asyncio
import logging
from re import A
from dotenv import load_dotenv

import uvicorn

# Import core components from Google ADK for running agents and managing sessions
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

# Import common A2A server components and types
from A2A.server import A2AServer
from A2A.types import AgentCard  # AgentCard defines metadata and capabilities of this agent

# Local imports for the agent logic and task manager
from .agent import matching_agent
from .task_manager import MatchingAgentTaskManager

# Configure basic logging to output logs at the INFO level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file if present
load_dotenv()

# Application-wide constants
APP_NAME = "matching_agent_app"  # Logical name for this agent app
USER_ID = "1"  # Default user ID; used when associating sessions/tasks with a user

# Get required environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false")

# Validate that required API keys are set
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not set. Please set it in your environment variables.")
    exit(1)


async def run_server():
    """Initializes services and starts the A2AServer."""
    logger.info("Starting Matching Agent A2A Server initialization...")

    try:
        # Initialize session service to store and manage user conversation states
        session_service = InMemorySessionService()

        # The agent instance that will process user inputs and generate responses
        agent = matching_agent

        # Create a Runner to execute the agent logic using the session state
        runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)

        # Instantiate the custom task manager that handles A2A streaming and task execution 
        task_manager = MatchingAgentTaskManager(agent, runner, session_service, APP_NAME, USER_ID)

        # Determine the port and host from environment variables
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "localhost")
        listen_host = "0.0.0.0"  # Allow external connections

        # Load the AgentCard configuration from a JSON file
        with open("matching_agent_app/a2a_agent_card.json", "r") as f:
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