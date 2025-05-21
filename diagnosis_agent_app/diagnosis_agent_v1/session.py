from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from bson import ObjectId
from typing import Optional
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId

# Load environment variables from a .env file if present
load_dotenv()
# MongoDB connection
mongo_uri = os.getenv("MONGODB_URI")

# Connessione al database
client = MongoClient(mongo_uri)
db = client["home_repair_assistant"]
user_collection = db["users"]


class SessionSettings(BaseModel):
    user_id: str
    search_for_diy_solution: bool = False
    user_location: str = None
    user_diy_skills: str = None
    user_diy_tools: List[str] = []
    home_type: str = None
    solution_preferences: str = None
    time_available_for_repair: str = None
    favourite_language: str = "English"


class SessionService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.sessions: dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str, session_data: Optional[dict] = None) -> Dict[str, Any]:
        """
        Creates a new session with default values or provided session data.
        """
        
        session = self.fetch_user_settings()
        
        if session is not None:
            # If session already exists, return it
            return session
        
        # Create default session dictionary
        default_session = {
            "search_for_diy_solution": False,
            "user_location": None,
            "user_diy_skills": None,
            "user_diy_tools": [],
            "home_type": None,
            "solution_preferences": None,
            "time_available_for_repair": None,
            "favourite_language": "English"
        }
        
        # Update with provided data if any
        if session_data:
            default_session.update(session_data)
            
        # Store in the sessions dictionary
        self.sessions[session_id] = default_session
        return default_session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    
    def fetch_user_settings(self) -> Optional[SessionSettings]:
        user = user_collection.find_one(
            {"id": self.user_id},
            {"settings": 1, "_id": 0}
        )

        if not user or "settings" not in user:
            return None

        settings_dict = user["settings"]
        return SessionSettings(user_id=str(self.user_id), **settings_dict)
