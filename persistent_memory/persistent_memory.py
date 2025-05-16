# persistent_memory.py
from pymongo import MongoClient
from datetime import datetime, timezone
from typing import Optional
import os
import uuid

from google.adk.sessions.session import Session
from google.adk.events.event import Event
from google.adk.sessions.base_session_service import BaseSessionService, ListSessionsResponse, ListEventsResponse, GetSessionConfig

def wrap_raw_event(raw_event: dict) -> Event:
    """
    Converts a simplified raw event dict into a full Event object.
    
    Args:
        raw_event (dict): Must contain 'author' and 'content' keys.

    Returns:
        Event: Reconstructed Event object with minimal required fields.
    """
    author = raw_event["author"]
    content = raw_event["content"]

    event = Event(
        author=author,
        content=content
    )

    return event

def sanitize_mongo_input(data):
    """
    Recursively converts unsupported types to MongoDB-compatible ones.
    - Converts sets to lists
    - Removes None values from dicts (optional)
    """
    if isinstance(data, dict):
        return {
            key: sanitize_mongo_input(value)
            for key, value in data.items()
            if value is not None  # Optional: skip None values
        }
    elif isinstance(data, list):
        return [sanitize_mongo_input(item) for item in data]
    elif isinstance(data, set):
        return [sanitize_mongo_input(item) for item in data]
    else:
        return data

class MongoSessionService(BaseSessionService):
    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise EnvironmentError("Environment variable MONGODB_URI not set.")

        self.client = MongoClient(uri)
        self.db = self.client["dlsais_memory_2"]
        self.collection = self.db["sessions"]

        # Ensure index on _id for fast access
        self.collection.create_index([("_id", 1)], name="session_id_index")

    def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        """Creates a new session in MongoDB."""
        session_id = session_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).timestamp()

        session_data = {
            "_id": session_id,
            "app_name": app_name,
            "user_id": user_id,
            "state": state or {},
            "events": [],
            "created_at": now,
            "updated_at": now
        }

        self.collection.insert_one(session_data)

        return Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            events=[]
        )

    def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        """Retrieves a session by session_id, optionally filtered by app/user."""
        doc = self.collection.find_one({"_id": session_id})
        if not doc or doc["app_name"] != app_name or doc["user_id"] != user_id:
            return None

        
        raw_events = doc.get("events", [])
        events = [wrap_raw_event(e) for e in raw_events]

        if config and config.num_recent_events:
            events = events[-config.num_recent_events:]

        return Session(
            id=doc["_id"],
            app_name=doc["app_name"],
            user_id=doc["user_id"],
            state=doc["state"],
            events=events
        )

    def list_sessions(
        self, *, app_name: str, user_id: str
    ) -> ListSessionsResponse:
        """Lists all sessions for a given app and user."""
        docs = self.collection.find({
            "app_name": app_name,
            "user_id": user_id
        })

        sessions = [
            Session(
                id=doc["_id"],
                app_name=doc["app_name"],
                user_id=doc["user_id"],
                state=doc["state"],
                events=[]  # Do not include events here
            )
            for doc in docs
        ]

        return ListSessionsResponse(sessions=sessions)

    def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        """Deletes a session by session_id."""
        self.collection.delete_one({
            "_id": session_id,
            "app_name": app_name,
            "user_id": user_id
        })

    def list_events(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
    ) -> ListEventsResponse:
        """Returns all events for a session."""
        doc = self.collection.find_one({
            "_id": session_id,
            "app_name": app_name,
            "user_id": user_id
        })

        if not doc:
            return ListEventsResponse(events=[])

        return ListEventsResponse(events=doc.get("events", []))

    def append_event(self, session: Session, event: Event) -> Event:
        """Appends an event to the session and persists it."""
        super().append_event(session, event)

        # Extract only 'author' and 'content' from the event
        event_data = {
            "author": event.author,
            "content": event.content.model_dump()
        }

        # Sanitize before saving to MongoDB
        sanitized_event = sanitize_mongo_input(event_data)

        # Save only the simplified event to MongoDB
        self.collection.update_one(
            {"_id": session.id},
            {
                "$push": {"events": sanitized_event},
                "$set": {
                    "state": session.state,
                    "updated_at": datetime.now(timezone.utc).timestamp()
                }
            }
        )

        return event