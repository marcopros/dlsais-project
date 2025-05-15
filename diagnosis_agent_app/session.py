from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class SessionSettings(BaseModel):
    search_for_diy_solution: bool = False
    user_location: str = None
    user_diy_skills: str = None
    user_diy_tools: List[str] = []
    home_type: str = None
    solution_preferences: str = None
    time_available_for_repair: str = None
    favourite_language: str = "English"


class SessionService:
    def __init__(self):
        self.sessions: dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str, session_data: Optional[dict] = None) -> Dict[str, Any]:
        """
        Creates a new session with default values or provided session data.
        """
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