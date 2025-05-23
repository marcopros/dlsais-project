import os
import json
import asyncio
import logging
from dotenv import load_dotenv

import uvicorn

# Import common A2A server components and types
from A2A.server import A2AServer
from A2A.types import AgentCard, MissingAPIKeyError  # AgentCard defines metadata and capabilities of this agent

# Local imports for the agent logic and task manager
from .agent import appointment_agent
from .task_manager import AppointmentAgentTaskManager

# Configure basic logging to output logs at the INFO level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file if present
load_dotenv()

# Import e configura Google Generative AI
import google.generativeai as genai

# Load environment variables from a .env file if present
load_dotenv()

# Application-wide constants
APP_NAME = "appointment_agent_app"  # Logical name for this agent app
USER_ID = "1"  # Default user ID; used when associating sessions/tasks with a user


async def run_server():
    """Initializes services and starts the A2AServer."""

    # Verifica che la chiave Google API sia configurata
    if not os.getenv('GOOGLE_API_KEY'):
        raise MissingAPIKeyError(
            'GOOGLE_API_KEY environment variable not set'
        )
    
    # Configura l'SDK di Google Generative AI
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    logger.info("Google Generative AI SDK configured.")

    logger.info("Starting Appointment Agent A2A Server initialization...")

    logger.info("Starting Appointment Agent A2A Server initialization...")

    try:
        # Initialize session service to store and manage user conversation states
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        session_service = InMemorySessionService()

        # The agent instance that will process user inputs and generate responses
        agent = appointment_agent

        # Create a Runner to execute the agent logic using the session state
        from google.adk.runners import Runner
        runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)

        # Instantiate the custom task manager that handles A2A streaming and task execution 
        task_manager = AppointmentAgentTaskManager(agent, runner, session_service, APP_NAME, USER_ID)

        # Determine the port and host from environment variables
        port = int(os.getenv("PORT_APPOINTMENT", "8003"))  # Using port 8003 for appointment agent
        host = os.getenv("HOST", "localhost")
        listen_host = "0.0.0.0"  # Allow external connections

        # Load the AgentCard configuration from a JSON file
        with open("appointment_agent/a2a_agent_card.json", "r") as f:
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