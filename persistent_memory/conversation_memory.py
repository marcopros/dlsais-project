"""
Persistenza conversazionale per il sistema A2A multi-agent.

- MongoDB come backend (usa database/utils.get_mongodb_connection se presente)
- API sincrona (facile da integrare ovunque)
- Modello dominio minimale: AgentType ▶ MessageAuthor ▶ ConversationMessage
- Classe ConversationMemory: CRUD + estrazione contesto
- Facade A2AConversationLogger: shortcut per gli agent
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Union

from bson import ObjectId          # non strettamente necessario ma utile se ti servisse
from pymongo import MongoClient, ASCENDING

# se esiste usiamo il vostro helper che legge .env + gestisce retry
try:
    from database.utils import get_mongodb_connection        # type: ignore
except ModuleNotFoundError:
    get_mongodb_connection = None      # fallback in test locali


# ───────────────────────── MODELLI ────────────────────────── #

class AgentType(str, Enum):
    ORCHESTRATOR      = "orchestrator"
    DIAGNOSIS_AGENT   = "diagnosis_agent"
    MATCHING_AGENT    = "matching_agent"
    APPOINTMENT_AGENT = "appointment_agent"
    FEEDBACK_AGENT    = "feedback_agent"
    USER              = "user"

    @classmethod
    def from_any(cls, value: Union[str, "AgentType"]) -> "AgentType":
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            return cls.USER       # default di fallback


class MessageAuthor:
    """Rappresenta chi ha scritto il messaggio (utente o agent)."""
    __slots__ = ("type", "agent_name")

    def __init__(self, author_type: Union[AgentType, str], *, agent_name: Optional[str] = None):
        self.type: AgentType = AgentType.from_any(author_type)
        self.agent_name = agent_name or self.type.value

    def to_dict(self) -> Dict[str, str]:
        """
        Serializza l’autore in forma compatta:
        - { "type": "user" }                   se è l’utente
        - { "type": "agent", "agent_name": … } se è un agente
        """
        if self.type == AgentType.USER:
            return {"type": "user"}
        return {"type": "agent", "agent_name": self.agent_name}

    @classmethod
    def from_dict(cls, raw: Dict[str, str]) -> "MessageAuthor":
        if raw["type"] == "user":
            return cls(AgentType.USER)
        # raw["type"] == "agent"
        return cls(raw.get("agent_name", AgentType.ORCHESTRATOR))   # fallback sicuro


class ConversationMessage:
    """Singolo turno di conversazione salvato a DB."""
    __slots__ = ("session_id", "user_id", "author", "content", "timestamp", "metadata")

    def __init__(
        self,
        *,
        session_id: str,
        user_id: str,
        author: MessageAuthor,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.author = author
        self.content = content
        self.timestamp = (timestamp or datetime.now(tz=timezone.utc)).replace(tzinfo=timezone.utc)
        self.metadata = metadata or {}

    # ◁─── serializzazione
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "author": self.author.to_dict(),
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, raw: Dict) -> "ConversationMessage":
        return cls(
            session_id=raw["session_id"],
            user_id=raw["user_id"],
            author=MessageAuthor.from_dict(raw["author"]),
            content=raw["content"],
            timestamp=raw.get("timestamp"),
            metadata=raw.get("metadata", {}),
        )

    # formato “umano” (utile in debug / prompt)
    def pretty(self, with_ts: bool = True) -> str:
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if with_ts else ""
        who = (
            "user"
            if self.author.type == AgentType.USER
            else self.author.agent_name            # es. “Diagnosis Agent”
        )
        prefix = f"[{ts}] " if with_ts else ""
        return f"{prefix}{who}: {self.content}"


# ───────────────────── PERSISTENCE LAYER ───────────────────── #

# ─── PERSISTENCE LAYER v2 ────────────────────────────────────────────
class ConversationMemory:
    """
    Un documento per conversazione (chiave = session_id).
    messages è un array - appendiamo con $push.
    """
    def __init__(self, *, db_name: str = "dev", collection_name: str = "conversations", mongo_uri: str | None = None):
        if get_mongodb_connection and mongo_uri is None:
            client, db = get_mongodb_connection()
            self._client, self._db = client, db
        else:
            self._client = MongoClient(mongo_uri or "mongodb://localhost:27017")
            self._db = self._client[db_name]

        self._col = self._db[collection_name]
        self._ensure_indexes()

    # ---------- index ---------- #
    def _ensure_indexes(self):
        self._col.create_index("session_id", unique=True)
        self._col.create_index("user_id")

    # ---------- write ---------- #
    def save_message(self, msg: ConversationMessage) -> str:
        """Upsert documento della sessione e push del nuovo messaggio."""
        doc = msg.to_dict()
        self._col.update_one(
            {"session_id": msg.session_id},
            {
                "$setOnInsert": {
                    "session_id": msg.session_id,
                    "user_id": msg.user_id,
                },
                "$push": {"messages": {
                    "author": doc["author"],
                    "content": doc["content"],
                    "timestamp": doc["timestamp"],
                    "metadata": doc["metadata"],
                }}
            },
            upsert=True,
        )
        # restituisco id documento per logging/debug
        return msg.session_id
    
    # ─── helper convenienza per il façade ─── #
    def log_user_message(self, *, session_id: str, user_id: str, text: str):
        return self.save_message(
            ConversationMessage(
                session_id=session_id,
                user_id=user_id,
                author=MessageAuthor(AgentType.USER),
                content=text,
            )
        )

    def log_agent_message(
        self,
        *,
        session_id: str,
        user_id: str,
        agent_type: AgentType | str,
        text: str,
        metadata: dict | None = None,
    ):
        return self.save_message(
            ConversationMessage(
                session_id=session_id,
                user_id=user_id,
                author=MessageAuthor(agent_type),
                content=text,
                metadata=metadata,
            )
        )

    # ---------- read ---------- #
    def get_session_messages(self, session_id: str) -> list[ConversationMessage]:
        doc = self._col.find_one({"session_id": session_id}, {"_id": 0, "messages": 1})
        if not doc:
            return []
        return [
            ConversationMessage(
                session_id=session_id,
                user_id="",                        # non serve nel contesto
                author=MessageAuthor.from_dict(m["author"]),
                content=m["content"],
                timestamp=m["timestamp"],
                metadata=m["metadata"],
            )
            for m in doc["messages"]
        ]

    def get_user_sessions(self, user_id: str) -> list[str]:
        return [d["session_id"] for d in self._col.find({"user_id": user_id}, {"session_id": 1})]

    def get_recent_context(self, *, user_id: str, current_session_id: str, max_messages: int = 40):
        current = self.get_session_messages(current_session_id)
        needed = max_messages - len(current)
        if needed <= 0:
            return current
        # pesca per data decrescente tutte le altre sessioni dell'utente
        other = (
            self._col.find(
                {"user_id": user_id, "session_id": {"$ne": current_session_id}},
                {"messages": {"$slice": -needed}}
            )
            .sort("messages.timestamp", -1)
        )
        prev_msgs: list[ConversationMessage] = []
        for doc in other:
            prev_msgs.extend(
                ConversationMessage(
                    session_id=doc["session_id"],
                    user_id=user_id,
                    author=MessageAuthor.from_dict(m["author"]),
                    content=m["content"],
                    timestamp=m["timestamp"],
                    metadata=m["metadata"],
                )
                for m in doc["messages"]
            )
            if len(prev_msgs) >= needed:
                break
        prev_msgs = prev_msgs[-needed:]
        return prev_msgs + current
    
    # ---------- helper per l’Orchestrator ---------- #
    def format_context(
        self,
        *,
        user_id: str,
        current_session_id: str,
        max_messages: int = 40,
        with_ts: bool = True,
    ) -> str:
        """
        Restituisce una stringa con gli ultimi `max_messages`
        (sessione corrente + storico) già formattati per il prompt.
        """
        messages = self.get_recent_context(
            user_id=user_id,
            current_session_id=current_session_id,
            max_messages=max_messages,
        )
        # ConversationMessage.pretty() ora usa author.agent_name,
        # quindi non serve più pescare msg.type a mano.
        return "\n".join(m.pretty(with_ts=with_ts) for m in messages)

    # ---------- GDPR helpers ---------- #
    def delete_session(self, session_id: str) -> int:
        return self._col.delete_one({"session_id": session_id}).deleted_count

    def delete_user(self, user_id: str) -> int:
        return self._col.delete_many({"user_id": user_id}).deleted_count



# ──────────────────── FAÇADE PER GLI AGENT ─────────────────── #

class A2AConversationLogger:
    """
    Piccolo façade che incapsula ConversationMemory con metodi
    user()/orchestrator()/agent() così da non duplicare logica negli agent.
    """
    def __init__(self, memory: ConversationMemory):
        self._mem = memory

    def user(self, *, session_id: str, user_id: str, text: str) -> str:
        return self._mem.log_user_message(session_id=session_id, user_id=user_id, text=text)

    def orchestrator(self, *, session_id: str, user_id: str, text: str, metadata: Optional[Dict] = None):
        return self._mem.log_agent_message(
            session_id=session_id, user_id=user_id, agent_type=AgentType.ORCHESTRATOR, text=text, metadata=metadata
        )

    def agent(self, *, session_id: str, user_id: str, agent_type: Union[AgentType, str], text: str, metadata: Optional[Dict] = None):
        return self._mem.log_agent_message(
            session_id=session_id, user_id=user_id, agent_type=agent_type, text=text, metadata=metadata
        )
