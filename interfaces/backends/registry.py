from __future__ import annotations

import logging
from typing import Any

from .base import InterfaceBackend

log = logging.getLogger("ciel.interfaces.backends.registry")

_backends: dict[str, InterfaceBackend] = {}


def register(backend: InterfaceBackend) -> None:
    _backends[backend.mode] = backend
    log.info("Backend registered: %s (%s)", backend.name, backend.mode)


def get(mode: str) -> InterfaceBackend | None:
    return _backends.get(mode)


def get_all() -> list[InterfaceBackend]:
    return list(_backends.values())


def get_available() -> list[InterfaceBackend]:
    return [b for b in _backends.values() if b.is_available()]


def get_stats() -> dict[str, Any]:
    return {
        "total": len(_backends),
        "available": len(get_available()),
        "backends": {m: b.get_stats() for m, b in _backends.items()},
    }


def load_default_backends() -> None:
    from .textual_backend import TextualBackend
    from .web_backend import WebBackend
    from .voice_backend import VoiceBackend

    for backend_cls in [TextualBackend, WebBackend, VoiceBackend]:
        try:
            b = backend_cls()
            if b.is_available():
                register(b)
        except Exception as e:
            log.debug("Failed to load backend %s: %s", backend_cls.__name__, e)


def _get_adapter_info(emulator: str, detector: Any) -> dict[str, Any]:
    db = {
        "kitty": {
            "adapter": "kitty-terminal",
            "features": ["true_color", "images", "hyperlinks", "tabs", "remote_control"],
            "hints": "Use icat for images, kitty @ for remote control",
        },
        "iTerm2": {
            "adapter": "iterm2-terminal",
            "features": ["true_color", "images", "shell_integration", "tmux"],
            "hints": "Use imgcat for images, shell integration for marks",
        },
        "tmux": {
            "adapter": "tmux-terminal",
            "features": ["multiplexer", "pane_split", "detach", "status_line"],
            "hints": "Use prefix keys for panes, :new for windows",
        },
        "foot": {
            "adapter": "foot-terminal",
            "features": ["true_color", "sixel", "scrollback_search"],
            "hints": "Use Ctrl+Shift+R for scrollback search",
        },
        "WezTerm": {
            "adapter": "wezterm-terminal",
            "features": ["true_color", "multiplexer", "ssh_domain", "hyperlinks"],
            "hints": "Use wezterm cli for remote control",
        },
        "Windows Terminal": {
            "adapter": "windows-terminal-backend",
            "features": ["true_color", "tabs", "panes", "acrylic"],
            "hints": "Use Ctrl+Shift+T for tabs, Alt+Shift+D for panes",
        },
        "vscode": {
            "adapter": "vscode-terminal-backend",
            "features": ["true_color", "link_detection", "task_integration"],
            "hints": "Use tasks.json for automation, Ctrl+` to toggle",
        },
        "ghostty": {
            "adapter": "ghostty-terminal",
            "features": ["true_color", "sixel", "kitty_graphics", "tabs"],
            "hints": "Multi-protocol support: sixel + kitty graphics",
        },
        "Alacritty": {
            "adapter": "alacritty-terminal",
            "features": ["true_color", "minimal"],
            "hints": "Fast, minimal. No tabs or panes.",
        },
        "xterm": {
            "adapter": "xterm-backend",
            "features": ["8-bit_color", "legacy"],
            "hints": "Limited features, use a modern terminal for best experience",
        },
    }
    return db.get(emulator, db["xterm"])


def get_terminal_adapters() -> dict[str, dict[str, Any]]:
    detector = __import__("ciel.interfaces.capabilities", fromlist=["get_detector"]).get_detector()
    info = detector.detect()
    emulator = info.get("emulator", "unknown")
    return {emulator: _get_adapter_info(emulator, detector)}
