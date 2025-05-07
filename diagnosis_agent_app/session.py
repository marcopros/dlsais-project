from pydantic import BaseModel
from typing import List, Optional


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
        self.sessions: dict[str, SessionSettings] = {}

    def create_session(self, session_id: str, session_data: Optional[dict] = None) -> SessionSettings:
        """
        Creates a new session from a dictionary of settings. Uses defaults if no data is provided.
        """
        # Create a new SessionSettings using the provided data
        settings = SessionSettings(**(session_data or {}))
        self.sessions[session_id] = settings
        return settings

    def get_session(self, session_id: str) -> Optional[SessionSettings]:
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False