# persistent_memory.py

from google.adk.sessions.session import Session
from google.adk.events.event import Event
from google.adk.sessions.base_session_service import BaseSessionService, ListSessionsResponse, ListEventsResponse, GetSessionConfig
from typing import Optional
import uuid

from .utils import (
    create_session_in_db,
    get_session_from_db,
    list_sessions_for_user,
    delete_session_from_db,
    list_events_from_db,
    append_event_to_db
)

def wrap_raw_event(raw_event: dict) -> Event:
    """
    Converts a simplified raw event dict into a full Event object.
    """
    return Event(
        author=raw_event["author"],
        content=raw_event["content"]
    )


class MongoSessionService(BaseSessionService):
    def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        session_id = session_id or str(uuid.uuid4())
        state = state or {}

        create_session_in_db(
            session_id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state
        )

        return Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state,
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
        doc = get_session_from_db(
            session_id=session_id,
            app_name=app_name,
            user_id=user_id,
            num_recent_events=config.num_recent_events if config else None
        )
        if not doc:
            return None

        events = [wrap_raw_event(e) for e in doc.get("events", [])]

        return Session(
            id=doc["_id"],
            app_name=doc["app_name"],
            user_id=doc["user_id"],
            state=doc["state"],
            events=events
        )

    def list_sessions(self, *, app_name: str, user_id: str) -> ListSessionsResponse:
        sessions_data = list_sessions_for_user(app_name=app_name, user_id=user_id)
        sessions = [
            Session(
                id=doc["_id"],
                app_name=doc["app_name"],
                user_id=doc["user_id"],
                state=doc["state"],
                events=[]  # Do not include events here
            )
            for doc in sessions_data
        ]
        return ListSessionsResponse(sessions=sessions)

    def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        delete_session_from_db(session_id=session_id, app_name=app_name, user_id=user_id)

    def list_events(self, *, app_name: str, user_id: str, session_id: str) -> ListEventsResponse:
        events = list_events_from_db(session_id=session_id, app_name=app_name, user_id=user_id)
        return ListEventsResponse(events=events)

    def append_event(self, session: Session, event: Event) -> Event:
        super().append_event(session, event)

        event_data = {
            "author": event.author,
            "content": event.content.model_dump()
        }

        append_event_to_db(
            session_id=session.id,
            event=event_data,
            updated_state=session.state
        )

        return event