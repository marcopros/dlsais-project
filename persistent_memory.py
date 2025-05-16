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
        self.collection.create_index([("username", 1), ("app_name", 1)])

    def add_session_to_memory(self, session: Session, username: str):
        """Aggiorna il documento esistente o ne crea uno nuovo per l'utente e l'app."""
        # Estrai eventi dalla sessione
        events = []
        for e in session.events:
            text = e.content.parts[0].text if (e.content and e.content.parts) else ""
            timestamp = getattr(e, "timestamp", datetime.now(timezone.utc).timestamp())
            events.append({
                "author": e.author,
                "text": text,
                "timestamp": timestamp,
                "session_id": session.id  # Aggiunto l'ID sessione per tracciare le sessioni diverse
            })
        
        # Trova il documento esistente per questo utente e app utilizzando l'username
        filter_query = {
            "username": username,
            "app_name": session.app_name
        }
        
        # Aggiornamento in stile upsert (update o insert se non esiste)
        update_operation = {
            "$push": {
                "events": {"$each": events}
            },
            "$set": {
                "current_session_id": session.id,
                "state": session.state.copy(),
                "updated_at": datetime.now(timezone.utc)
            },
            "$setOnInsert": {
                "user_id": session.user_id,  # Manteniamo anche l'ID utente per retrocompatibilità
                "created_at": datetime.now(timezone.utc)
            }
        }
        
        # Eseguire l'upsert
        self.collection.update_one(
            filter_query, 
            update_operation, 
            upsert=True
        )
        
        print(f"[DEBUG] Memoria aggiornata per utente {username}")

    def search_memory(self, username: str, app_name: str, limit=None):
        """Restituisce tutti gli eventi per un dato utente e app."""
        doc = self.collection.find_one({
            "username": username,
            "app_name": app_name
        })
        
        if doc:
            events = doc.get("events", [])
            # Se viene specificato un limite, restituisce solo gli ultimi N eventi
            if limit and isinstance(limit, int) and limit > 0:
                return events[-limit:]
            return events
        return []

    def get_last_session_state(self, username: str, app_name: str):
        """Restituisce lo stato dell'ultima sessione."""
        doc = self.collection.find_one({
            "username": username, 
            "app_name": app_name
        })
        
        return doc.get("state", {}) if doc else {}

    def get_current_session_id(self, username: str, app_name: str):
        """Restituisce l'ID dell'ultima sessione."""
        doc = self.collection.find_one({
            "username": username, 
            "app_name": app_name
        })
        
        return doc.get("current_session_id") if doc else None
        
    def clear_user_memory(self, username: str, app_name: str):
        """Elimina la memoria per un utente specifico."""
        self.collection.delete_one({
            "username": username,
            "app_name": app_name
        })
        print(f"[DEBUG] Memoria cancellata per utente {username}")