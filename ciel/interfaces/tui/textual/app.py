"""
CIEL Textual TUI — main application entry point.

Usage:
    python3 -m ciel.interfaces.tui.textual.app
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from textual import work
from textual.app import App
from textual.binding import Binding

from ciel.interfaces.tui.textual.screens.chat import ChatScreen
from ciel.interfaces.tui.textual.screens.dashboard import DashboardScreen
from ciel.interfaces.tui.textual.theme import CielTheme

CSS_PATH = Path(__file__).parent / "ciel_textual.tcss"


class CielTUI(App):
    """
    CIEL Terminal UI — Textual-based chat interface.

    Features:
      - Chat with streaming LLM responses
      - Session management (create, list, switch, delete)
      - Command palette
      - Tool output display
      - Status bar
      - Dark theme
    """

    TITLE = "CIEL"
    SUB_TITLE = "Cognitive Interactive Evolution Layer"
    CSS_PATH = str(CSS_PATH)

    BINDINGS = [
        Binding("ctrl+d", "toggle_dashboard", "Dashboard"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "toggle_sessions", "Sessions"),
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("/", "focus_input", "Type"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chat_screen: ChatScreen | None = None
        self._dashboard_visible = False

    def on_mount(self):
        """Register the dark theme and push the chat screen."""
        self.register_theme(CielTheme.to_textual_theme())
        self.theme = "ciel-dark"

        self._chat_screen = ChatScreen()
        self.push_screen(self._chat_screen)

    def action_toggle_dashboard(self):
        """Toggle the dashboard screen."""
        if self._dashboard_visible:
            self.pop_screen()
            self._dashboard_visible = False
        else:
            self.push_screen(DashboardScreen())
            self._dashboard_visible = True

    def action_toggle_sessions(self):
        """Delegate to chat screen's session toggle."""
        if self._chat_screen:
            self._chat_screen.action_toggle_sessions()

    def action_clear_chat(self):
        """Clear the chat screen messages."""
        if self._chat_screen:
            self._chat_screen.action_clear()

    def action_focus_input(self):
        """Focus the input field."""
        if self._chat_screen:
            self._chat_screen.action_focus_input()


def main():
    app = CielTUI()
    app.run()


if __name__ == "__main__":
    main()
