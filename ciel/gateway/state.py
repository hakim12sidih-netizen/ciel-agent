from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ChannelState:
    id: str
    platform: str
    enabled: bool = True
    connected: bool = False
    config: dict[str, Any] = field(default_factory=dict)
    last_message_at: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class SessionState:
    id: str
    channel_id: str
    user_id: str
    workspace_id: str = ""
    started_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    message_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GatewayMetrics:
    uptime: float = 0.0
    total_messages: int = 0
    active_channels: int = 0
    active_sessions: int = 0
    errors_total: int = 0
    start_time: float = field(default_factory=time.time)


class GatewayState:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or Path.home() / ".ciel" / "gateway.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._channels: dict[str, ChannelState] = {}
        self._sessions: dict[str, SessionState] = {}
        self.metrics = GatewayMetrics()
        self._dirty = False
        self._load()

    def _load(self) -> None:
        if not self.db_path.exists():
            return
        try:
            data = json.loads(self.db_path.read_text())
            for c in data.get("channels", []):
                ch = ChannelState(**c)
                self._channels[ch.id] = ch
            for s in data.get("sessions", []):
                ss = SessionState(**s)
                self._sessions[ss.id] = ss
            self.metrics = GatewayMetrics(**(data.get("metrics", {})))
        except Exception:
            pass

    def _save(self) -> None:
        data = {
            "channels": [vars(c) for c in self._channels.values()],
            "sessions": [vars(s) for s in self._sessions.values()],
            "metrics": vars(self.metrics),
        }
        self.db_path.write_text(json.dumps(data, indent=2, default=str))

    def flush(self) -> None:
        if self._dirty:
            self._save()
            self._dirty = False

    def register_channel(self, platform: str, config: dict[str, Any] | None = None) -> str:
        cid = f"{platform}-{uuid.uuid4().hex[:8]}"
        self._channels[cid] = ChannelState(
            id=cid, platform=platform, config=config or {},
        )
        self._dirty = True
        return cid

    def get_channel(self, channel_id: str) -> ChannelState | None:
        return self._channels.get(channel_id)

    def list_channels(self, platform: str = "") -> list[ChannelState]:
        if platform:
            return [c for c in self._channels.values() if c.platform == platform]
        return list(self._channels.values())

    def update_channel(self, channel_id: str, **kwargs: Any) -> None:
        ch = self._channels.get(channel_id)
        if ch:
            for k, v in kwargs.items():
                if hasattr(ch, k):
                    setattr(ch, k, v)
            self._dirty = True

    def remove_channel(self, channel_id: str) -> bool:
        if channel_id in self._channels:
            del self._channels[channel_id]
            self._dirty = True
            return True
        return False

    def create_session(self, channel_id: str, user_id: str, workspace_id: str = "") -> str:
        sid = f"ses-{uuid.uuid4().hex[:12]}"
        self._sessions[sid] = SessionState(
            id=sid, channel_id=channel_id, user_id=user_id,
            workspace_id=workspace_id,
        )
        self._dirty = True
        return sid

    def get_session(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def list_sessions(self, channel_id: str = "", workspace_id: str = "") -> list[SessionState]:
        results = list(self._sessions.values())
        if channel_id:
            results = [s for s in results if s.channel_id == channel_id]
        if workspace_id:
            results = [s for s in results if s.workspace_id == workspace_id]
        return results

    def touch_session(self, session_id: str) -> None:
        s = self._sessions.get(session_id)
        if s:
            s.last_active_at = time.time()
            s.message_count += 1
            self._dirty = True

    def close_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._dirty = True
            return True
        return False

    def record_message(self, channel_id: str, direction: str) -> None:
        self.metrics.total_messages += 1
        ch = self._channels.get(channel_id)
        if ch:
            ch.last_message_at = time.time()
            if direction == "incoming":
                ch.messages_received += 1
            else:
                ch.messages_sent += 1
        self._dirty = True

    def record_error(self, channel_id: str = "") -> None:
        self.metrics.errors_total += 1
        if channel_id:
            ch = self._channels.get(channel_id)
            if ch:
                ch.errors += 1
        self._dirty = True

    def status(self) -> dict[str, Any]:
        self.metrics.uptime = time.time() - self.metrics.start_time
        self.metrics.active_channels = len([c for c in self._channels.values() if c.connected])
        self.metrics.active_sessions = len(self._sessions)
        return {
            "metrics": vars(self.metrics),
            "channels": len(self._channels),
            "sessions": len(self._sessions),
        }
