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
        # Creazione di un indice composto per ottimizzare le query
        self.collection.create_index([("user_id", 1), ("app_name", 1)])

    def add_session_to_memory(self, session: Session):
        """Aggiorna il documento esistente o ne crea uno nuovo per l'utente e l'app."""
        # Estrai eventi dalla sessione
        events = []
        for e in session.events:
            text = e.content.parts[0].text if (e.content and e.content.parts) else ""
            timestamp = getattr(e, "timestamp", datetime.now(timezone.utc).timestamp())
            events.append({
                "author": e.author,
                "text": text,
                "timestamp": timestamp
            })
        
        # Trova il documento esistente per questo utente e app
        filter_query = {
            "user_id": session.user_id,
            "app_name": session.app_name
        }
        
        # Aggiornamento in stile upsert (update o insert se non esiste)
        update_operation = {
            "$set": {
                "session_id": session.id,
                "state": session.state.copy(),
                "updated_at": datetime.now(timezone.utc)
            },
            "$push": {
                "events": {"$each": events}
            },
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc)
            }
        }
        
        # Eseguire l'upsert
        self.collection.update_one(
            filter_query, 
            update_operation, 
            upsert=True
        )
        
        print(f"[DEBUG] Memoria aggiornata per utente {session.user_id}")

    def search_memory(self, user_id: str, app_name: str):
        """Restituisce tutti gli eventi per un dato utente e app."""
        doc = self.collection.find_one({
            "user_id": user_id,
            "app_name": app_name
        })
        
        if doc:
            return doc.get("events", [])
        return []

    def get_last_session_state(self, user_id: str, app_name: str):
        """Restituisce lo stato dell'ultima sessione."""
        doc = self.collection.find_one({
            "user_id": user_id, 
            "app_name": app_name
        })
        
        return doc.get("state", {}) if doc else {}

    def get_last_session_id(self, user_id: str, app_name: str):
        """Restituisce l'ID dell'ultima sessione."""
        doc = self.collection.find_one({
            "user_id": user_id, 
            "app_name": app_name
        })
        
        return doc.get("session_id") if doc else None
        
    def clear_user_memory(self, user_id: str, app_name: str):
        """Elimina la memoria per un utente specifico."""
        self.collection.delete_one({
            "user_id": user_id,
            "app_name": app_name
        })
        print(f"[DEBUG] Memoria cancellata per utente {user_id}")