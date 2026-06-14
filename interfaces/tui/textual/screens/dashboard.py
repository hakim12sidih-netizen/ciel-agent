"""
Dashboard Screen — live CIEL system stats.
Shows brain status, session stats, evolution, memory, and system info.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Label, Static

from ciel.interfaces.tui.textual.theme import CielTheme


class StatCard(Static):
    """A dashboard card showing a label and value."""

    def __init__(self, title: str, value: str = "—", subtitle: str = "", **kwargs):
        super().__init__(**kwargs)
        self._card_title = title
        self._value = value
        self._subtitle = subtitle

    def on_mount(self):
        self._render()

    def update_value(self, value: str, subtitle: str = ""):
        self._value = value
        if subtitle:
            self._subtitle = subtitle
        self._render()

    def _render(self):
        c = CielTheme
        self.update(
            f"[bold {c.SECONDARY}]{self._card_title}[/]\n"
            f"[{c.ACCENT} bold]{self._value}[/]\n"
            f"[{c.DIM}]{self._subtitle}[/]"
        )
        self.classes = "dashboard-card"


class DashboardScreen(Screen):
    """
    Live system monitoring dashboard.
    Refreshes every 2 seconds.
    """

    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("ctrl+d", "pop_screen", "Close"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._refresh_task: asyncio.Task | None = None
        self._cards: dict[str, StatCard] = {}

    def compose(self):
        yield Header(show_clock=True)

        with Container(id="dashboard-container"):
            yield StatCard("Sessions", "—", "total / active", id="card-sessions")
            yield StatCard("Messages", "—", "total stored", id="card-messages")
            yield StatCard("DB Size", "—", "session.db", id="card-db")
            yield StatCard("Schema", "—", "version", id="card-schema")
            yield StatCard("System", "—", "platform", id="card-system")
            yield StatCard("Uptime", "—", "session duration", id="card-uptime")

    def on_mount(self):
        self._cards = {
            "sessions": self.query_one("#card-sessions", StatCard),
            "messages": self.query_one("#card-messages", StatCard),
            "db": self.query_one("#card-db", StatCard),
            "schema": self.query_one("#card-schema", StatCard),
            "system": self.query_one("#card-system", StatCard),
            "uptime": self.query_one("#card-uptime", StatCard),
        }
        self._start_time = time.time()
        self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def _refresh_loop(self):
        """Refresh dashboard stats every 2 seconds."""
        while True:
            await asyncio.sleep(2)
            try:
                await self._refresh_stats()
            except Exception:
                pass

    async def _refresh_stats(self):
        """Query SessionDB stats and update cards."""
        try:
            from ciel.memory.session_db import SessionDB
            db = SessionDB()
            stats = db.stats()

            self._cards["sessions"].update_value(
                f"{stats['total_sessions']} / {stats['active_sessions']}",
                "total / active",
            )
            self._cards["messages"].update_value(
                f"{stats['total_messages']:,}",
                "total stored",
            )

            db_size = stats.get("db_size", 0)
            if db_size < 1024:
                size_str = f"{db_size} B"
            elif db_size < 1024 * 1024:
                size_str = f"{db_size / 1024:.1f} KB"
            else:
                size_str = f"{db_size / (1024 * 1024):.1f} MB"

            self._cards["db"].update_value(size_str, "session.db")
            self._cards["schema"].update_value(
                f"v{stats['schema_version']}",
                "schema version",
            )

            uptime_secs = time.time() - self._start_time
            uptime_str = (
                f"{int(uptime_secs // 3600)}h {int((uptime_secs % 3600) // 60)}m"
            )
            self._cards["uptime"].update_value(uptime_str, "session duration")

        except ImportError:
            self._cards["sessions"].update_value("—", "SessionDB not available")

        # System info (static)
        import platform
        self._cards["system"].update_value(
            f"{platform.system()} {platform.machine()}",
            "platform",
        )

    def action_refresh(self):
        asyncio.create_task(self._refresh_stats())
