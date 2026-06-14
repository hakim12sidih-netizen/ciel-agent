"""
Session method handler — CRUD for chat sessions.
Uses SessionDB (SQLite + WAL + FTS5) for persistent storage.
"""

from typing import Any

from ciel.memory.session_db import SessionDB

_db = None


def _get_db():
    global _db
    if _db is None:
        _db = SessionDB()
    return _db


def _session_to_dict(s: dict, source: str = "tui") -> dict:
    return {
        "id": s.get("session_id", ""),
        "source": source,
        "platform": s.get("platform", "tui"),
        "title": s.get("title", ""),
        "createdAt": int(datetime.fromisoformat(s["created_at"]).timestamp() * 1000)
        if isinstance(s.get("created_at"), str) else 0,
        "updatedAt": int(datetime.fromisoformat(s["updated_at"]).timestamp() * 1000)
        if isinstance(s.get("updated_at"), str) else 0,
        "messageCount": s.get("message_count", 0),
        "model": s.get("model"),
    }


from datetime import datetime


class SessionMethods:

    def __init__(self, server):
        self.server = server

    def get_methods(self) -> dict[str, Any]:
        return {
            "sessions.create": self.handle_create,
            "sessions.list": self.handle_list,
            "sessions.get": self.handle_get,
            "sessions.delete": self.handle_delete,
        }

    async def handle_create(self, params: dict) -> dict:
        db = _get_db()
        session_id = db.create_session(
            platform=params.get("platform", "tui"),
            title=params.get("title", "TUI Session"),
        )
        session = _session_to_dict(
            db.get_session(session_id),
            source=params.get("source", "tui"),
        )
        await self.server.emitter.session_changed(session)
        return session

    async def handle_list(self, params: dict) -> dict:
        db = _get_db()
        raw = db.list_sessions(
            platform=params.get("platform", ""),
            limit=params.get("limit", 50),
        )
        sessions_list = [
            _session_to_dict(s, source=params.get("source", "tui"))
            for s in raw
        ]
        return {"sessions": sessions_list, "total": len(sessions_list)}

    async def handle_get(self, params: dict) -> dict:
        db = _get_db()
        record = db.get_session(params["id"])
        if record is None:
            return {}
        return _session_to_dict(record)

    async def handle_delete(self, params: dict) -> dict:
        db = _get_db()
        db.delete_session(params["id"])
        await self.server.emitter.session_changed(None)
        return {"success": True}
