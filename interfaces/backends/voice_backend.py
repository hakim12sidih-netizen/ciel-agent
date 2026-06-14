from __future__ import annotations

import logging
import shutil

from .base import InterfaceBackend

log = logging.getLogger("ciel.interfaces.backends.voice")


class VoiceBackend(InterfaceBackend):
    def __init__(self):
        super().__init__(name="Voice Interface", mode="voice")

    @property
    def description(self) -> str:
        return "Interface vocale avec STT (Google Web Speech) et TTS (Microsoft Edge)."

    @property
    def required_dependencies(self) -> list[str]:
        deps = []
        if not shutil.which("sox"):
            deps.append("sox")
        return deps

    def start(self) -> bool:
        self._running = True
        log.info("Voice backend ready")
        return True

    def stop(self) -> bool:
        self._running = False
        return True
