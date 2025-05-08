import os
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.adk.sessions import Session

load_dotenv()

class MongoMemoryService:
    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise EnvironmentError("Variabile d'ambiente MONGODB_URI non trovata")
        self.client = MongoClient(uri)
        self.db = self.client["dlsais_memory"]
        self.collection = self.db["user_conversations"]
        self.collection.create_index([("user_id", 1), ("app_name", 1), ("session_id", 1)])

    def add_session_to_memory(self, session: Session):
        """Salva events e state della sessione come memoria a lungo termine."""
        events = []
        for e in session.events:
            text = e.content.parts[0].text if (e.content and e.content.parts) else ""
            timestamp = getattr(e, "timestamp", datetime.now(timezone.utc).timestamp())
            events.append({
                "author": e.author,
                "text": text,
                "timestamp": timestamp
            })

        doc = {
            "user_id": session.user_id,
            "session_id": session.id,
            "app_name": session.app_name,
            "events": events,
            "state": session.state.copy(),
            "saved_at": datetime.now(timezone.utc)
        }

        self.collection.insert_one(doc)

    def search_memory(self, user_id: str, app_name: str):
        cursor = self.collection.find({
            "user_id": user_id,
            "app_name": app_name
        }).sort("saved_at", 1)

        memory = []
        for doc in cursor:
            memory.extend(doc.get("events", []))
        return memory

    def get_last_session_state(self, user_id: str, app_name: str):
        doc = self.collection.find_one(
            {"user_id": user_id, "app_name": app_name},
            sort=[("saved_at", -1)]
        )
        return doc.get("state", {}) if doc else {}

    def get_last_session_id(self, user_id: str, app_name: str):
        doc = self.collection.find_one(
            {"user_id": user_id, "app_name": app_name},
            sort=[("saved_at", -1)]
        )
        return doc["session_id"] if doc else None