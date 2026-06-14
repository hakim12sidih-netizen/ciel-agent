from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..capabilities import get_detector, TerminalCapabilityDetector

log = logging.getLogger("ciel.interfaces.backend")


@dataclass(slots=True)
class BackendSession:
    session_id: str
    mode: str
    terminal_emulator: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    active: bool = True


class InterfaceBackend(ABC):
    """Abstract base class for all interface backends.

    A backend is an interface mode (CLI, TUI, Web, Voice, etc.)
    with a lifecycle, session management, and terminal-specific
    adaptation.
    """

    def __init__(self, name: str, mode: str):
        self.name = name
        self.mode = mode
        self._sessions: dict[str, BackendSession] = {}
        self._running = False
        self._detector = get_detector()

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def required_dependencies(self) -> list[str]:
        ...

    @abstractmethod
    def start(self) -> bool:
        ...

    @abstractmethod
    def stop(self) -> bool:
        ...

    def is_available(self) -> bool:
        for dep in self.required_dependencies:
            import shutil
            if not shutil.which(dep):
                return False
        return True

    def create_session(self, **metadata) -> BackendSession:
        import uuid
        session = BackendSession(
            session_id=f"{self.mode}-{uuid.uuid4().hex[:8]}",
            mode=self.mode,
            terminal_emulator=self._detector.emulator(),
            metadata=metadata,
        )
        self._sessions[session.session_id] = session
        return session

    def close_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def get_sessions(self) -> list[BackendSession]:
        return list(self._sessions.values())

    def get_stats(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "name": self.name,
            "running": self._running,
            "sessions": len(self._sessions),
            "available": self.is_available(),
        }

    def terminal_info(self) -> dict[str, Any]:
        return self._detector.to_dict()
