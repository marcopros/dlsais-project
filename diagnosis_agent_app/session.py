from pydantic import BaseModel
from typing import List, Optional, Dict


class SessionSettings(BaseModel):
    search_for_diy_solution: bool = False
    user_location: str = None
    user_diy_skills: str = None
    user_diy_tools: List[str] = []
    home_type: str = None
    solution_preferences: str = None
    time_available_for_repair: str = None
    favourite_language: str = "Italian"
    # Cronologia delle conversazioni
    conversation_history: List[Dict[str, str]] = []


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

    def add_message_to_history(self, session_id: str, role: str, content: str) -> bool:
        """
        Aggiunge un messaggio alla cronologia della conversazione per la sessione specificata.
        
        Args:
            session_id: ID della sessione
            role: Ruolo del messaggio ('user' o 'assistant')
            content: Contenuto del messaggio
            
        Returns:
            True se il messaggio è stato aggiunto, False se la sessione non esiste
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        session.conversation_history.append({
            "role": role,
            "content": content
        })
        return True
        
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Recupera la cronologia della conversazione per la sessione specificata.
        
        Args:
            session_id: ID della sessione
            
        Returns:
            Lista di messaggi nella cronologia o lista vuota se la sessione non esiste
        """
        session = self.get_session(session_id)
        if not session:
            return []
            
        return session.conversation_history

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False