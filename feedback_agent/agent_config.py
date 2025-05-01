# @title Configure API Keys (Replace with your actual keys!)

# --- IMPORTANT: Replace placeholders with your real API keys ---
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

def check_and_configure_environment():
    """
    Checks and configures the environment for API keys and settings.
    """
    # Gemini API Key (Get from Google AI Studio: https://aistudio.google.com/app/apikey)
    google_api_key = os.getenv("GOOGLE_API_KEY")

    # --- Verify Keys (Optional Check) ---
    if google_api_key and google_api_key != "YOUR_GOOGLE_API_KEY":
        print("Google API Key set: Yes")
    else:
        print("Google API Key set: No (REPLACE PLACEHOLDER!)")

    # Configure ADK to use API keys directly (not Vertex AI for this multi-model setup)
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

    print("\nEnvironment configured.")

# Call the function to perform the check and configuration
check_and_configure_environment()