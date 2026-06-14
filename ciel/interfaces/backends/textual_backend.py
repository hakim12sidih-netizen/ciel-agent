from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys

from .base import InterfaceBackend

log = logging.getLogger("ciel.interfaces.backends.textual")


class TextualBackend(InterfaceBackend):
    def __init__(self):
        super().__init__(name="Textual TUI", mode="tui")

    @property
    def description(self) -> str:
        return "Terminal UI basé sur Textual (Python). Interface complète avec chat, sessions, dashboard."

    @property
    def required_dependencies(self) -> list[str]:
        return []

    def start(self) -> bool:
        self._running = True
        log.info("Textual TUI backend ready")
        return True

    def stop(self) -> bool:
        self._running = False
        return True

    def launch(self, args: list[str] | None = None) -> int:
        """Lance l'application Textual TUI."""
        from ciel.interfaces.tui.textual.app import CielTUI
        app = CielTUI()
        return app.run()
