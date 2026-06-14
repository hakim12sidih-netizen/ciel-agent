from __future__ import annotations

import os
import platform
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any


class TerminalColorDepth:
    BITS_4 = "4-bit"       # ANSI 16 colors
    BITS_8 = "8-bit"       # 256 colors
    BITS_24 = "24-bit"     # True color (16M)
    MONOCHROME = "1-bit"   # No color


class TerminalCapability:
    TRUE_COLOR = "true_color"
    UNICODE = "unicode"
    HYPERLINKS = "hyperlinks"
    IMAGES = "images"
    SIXEL = "sixel"
    KITTY_GRAPHICS = "kitty_graphics"
    ITERM2_IMAGES = "iterm2_images"
    BRACKETED_PASTE = "bracketed_paste"
    FOCUS_EVENTS = "focus_events"
    MOUSE_SUPPORT = "mouse_support"
    CLIPBOARD = "clipboard"
    OSC_8 = "osc_8"          # Hyperlinks via OSC 8
    SYNCHRONOUS_UPDATE = "sync_update"  # Synchronous output (DECRQM)
    ALTERNATE_SCREEN = "alternate_screen"
    CURSOR_SHAPE = "cursor_shape"
    COLOR_SPEC = "color_spec"  # OSC 4/10/11 color spec
    DAEMON = "daemon"        # Background execution support


# Terminal database: emulator -> detected features and settings
TERMINAL_DB: dict[str, dict[str, Any]] = {
    "kitty": {
        "family": "kitty",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.HYPERLINKS, TerminalCapability.KITTY_GRAPHICS,
            TerminalCapability.IMAGES, TerminalCapability.BRACKETED_PASTE,
            TerminalCapability.FOCUS_EVENTS, TerminalCapability.MOUSE_SUPPORT,
            TerminalCapability.CLIPBOARD, TerminalCapability.OSC_8,
            TerminalCapability.SYNCHRONOUS_UPDATE, TerminalCapability.ALTERNATE_SCREEN,
            TerminalCapability.CURSOR_SHAPE, TerminalCapability.COLOR_SPEC,
            TerminalCapability.DAEMON,
        ],
        "protocol": "kitty",
        "notes": "Kitty protocol for images, graphics, and advanced features",
        "features": {
            "icat": True, "remote_control": True, "tabs": True, "panes": True,
            "unicode": True, "ligatures": True, "shell_integration": True,
        },
    },
    "iTerm2": {
        "family": "iterm2",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.ITERM2_IMAGES, TerminalCapability.IMAGES,
            TerminalCapability.BRACKETED_PASTE, TerminalCapability.CLIPBOARD,
            TerminalCapability.OSC_8, TerminalCapability.ALTERNATE_SCREEN,
            TerminalCapability.CURSOR_SHAPE, TerminalCapability.DAEMON,
        ],
        "protocol": "iterm2",
        "notes": "iTerm2 proprietary escape codes for images, shell integration",
        "features": {
            "imgcat": True, "shell_integration": True, "tabs": True, "panes": True,
            "unicode": True, "tmux_integration": True,
        },
    },
    "tmux": {
        "family": "tmux",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.BRACKETED_PASTE, TerminalCapability.CLIPBOARD,
            TerminalCapability.OSC_8, TerminalCapability.ALTERNATE_SCREEN,
            TerminalCapability.CURSOR_SHAPE, TerminalCapability.DAEMON,
        ],
        "protocol": "passthrough",
        "notes": "Multiplexer. Capabilities depend on inner terminal.",
        "features": {
            "pane_split": True, "session_attach": True, "detach": True,
            "status_line": True, "copy_mode": True, "clipboard": True,
        },
    },
    "foot": {
        "family": "foot",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.SIXEL, TerminalCapability.IMAGES,
            TerminalCapability.BRACKETED_PASTE, TerminalCapability.OSC_8,
            TerminalCapability.ALTERNATE_SCREEN, TerminalCapability.CURSOR_SHAPE,
            TerminalCapability.COLOR_SPEC,
        ],
        "protocol": "sixel",
        "notes": "Wayland-native terminal with Sixel graphics",
        "features": {
            "sixel": True, "scrollback_search": True, "url_open": True,
        },
    },
    "WezTerm": {
        "family": "wezterm",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.HYPERLINKS, TerminalCapability.BRACKETED_PASTE,
            TerminalCapability.FOCUS_EVENTS, TerminalCapability.MOUSE_SUPPORT,
            TerminalCapability.CLIPBOARD, TerminalCapability.OSC_8,
            TerminalCapability.SYNCHRONOUS_UPDATE, TerminalCapability.ALTERNATE_SCREEN,
            TerminalCapability.CURSOR_SHAPE, TerminalCapability.COLOR_SPEC,
        ],
        "protocol": "wezterm",
        "notes": "GPU-accelerated with multiplexer, Lua config",
        "features": {
            "multiplexer": True, "tabs": True, "panes": True, "unicode": True,
            "ligatures": True, "ssh_domain": True,
        },
    },
    "Windows Terminal": {
        "family": "windows-terminal",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.BRACKETED_PASTE, TerminalCapability.FOCUS_EVENTS,
            TerminalCapability.MOUSE_SUPPORT, TerminalCapability.CLIPBOARD,
            TerminalCapability.OSC_8, TerminalCapability.ALTERNATE_SCREEN,
            TerminalCapability.CURSOR_SHAPE, TerminalCapability.COLOR_SPEC,
        ],
        "protocol": "standard",
        "notes": "Windows 10+ modern terminal",
        "features": {
            "tabs": True, "panes": True, "unicode": True, "acrylic": True,
        },
    },
    "vscode": {
        "family": "vscode",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.BRACKETED_PASTE, TerminalCapability.CLIPBOARD,
            TerminalCapability.OSC_8, TerminalCapability.ALTERNATE_SCREEN,
            TerminalCapability.CURSOR_SHAPE,
        ],
        "protocol": "standard",
        "notes": "VS Code integrated terminal (xterm.js-based)",
        "features": {
            "link_detection": True, "task_integration": True, "unicode": True,
        },
    },
    "ghostty": {
        "family": "ghostty",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.HYPERLINKS, TerminalCapability.SIXEL,
            TerminalCapability.KITTY_GRAPHICS, TerminalCapability.IMAGES,
            TerminalCapability.BRACKETED_PASTE, TerminalCapability.OSC_8,
            TerminalCapability.ALTERNATE_SCREEN, TerminalCapability.CURSOR_SHAPE,
            TerminalCapability.COLOR_SPEC,
        ],
        "protocol": "multi",
        "notes": "New GPU-accelerated terminal with multi-protocol support",
        "features": {
            "sixel": True, "kitty_graphics": True, "tabs": True, "unicode": True,
        },
    },
    "Alacritty": {
        "family": "alacritty",
        "color_depth": TerminalColorDepth.BITS_24,
        "unicode": True,
        "capabilities": [
            TerminalCapability.TRUE_COLOR, TerminalCapability.UNICODE,
            TerminalCapability.BRACKETED_PASTE, TerminalCapability.FOCUS_EVENTS,
            TerminalCapability.MOUSE_SUPPORT, TerminalCapability.CLIPBOARD,
            TerminalCapability.OSC_8, TerminalCapability.ALTERNATE_SCREEN,
            TerminalCapability.CURSOR_SHAPE, TerminalCapability.COLOR_SPEC,
        ],
        "protocol": "standard",
        "notes": "GPU-accelerated, minimal features, no tabs/panes",
        "features": {
            "no_tabs": True, "no_panes": True, "unicode": True, "ligatures": True,
        },
    },
    "xterm": {
        "family": "xterm",
        "color_depth": TerminalColorDepth.BITS_8,
        "unicode": False,
        "capabilities": [
            TerminalCapability.BRACKETED_PASTE, TerminalCapability.FOCUS_EVENTS,
            TerminalCapability.MOUSE_SUPPORT, TerminalCapability.ALTERNATE_SCREEN,
            TerminalCapability.CURSOR_SHAPE,
        ],
        "protocol": "standard",
        "notes": "Legacy xterm, minimal capabilities",
        "features": {
            "vt100": True, "vt220": True, "vt340": True, "sixel": False,
        },
    },
    "unknown": {
        "family": "unknown",
        "color_depth": TerminalColorDepth.BITS_8,
        "unicode": False,
        "capabilities": [
            TerminalCapability.ALTERNATE_SCREEN,
        ],
        "protocol": "standard",
        "notes": "Unknown terminal, safe defaults",
        "features": {},
    },
}


class TerminalCapabilityDetector:
    def __init__(self):
        self._cached: dict[str, Any] = {}

    def detect(self, force: bool = False) -> dict[str, Any]:
        if self._cached and not force:
            return self._cached
        term_env = os.environ.get("TERM", "").lower()
        colorterm_env = os.environ.get("COLORTERM", "").lower()
        term_program = os.environ.get("TERM_PROGRAM", "").lower()
        term_program_version = os.environ.get("TERM_PROGRAM_VERSION", "")

        emulator, confidence = self._identify_emulator(
            term_env, colorterm_env, term_program, term_program_version
        )
        info = dict(TERMINAL_DB.get(emulator, TERMINAL_DB["unknown"]))
        info["emulator"] = emulator
        info["confidence"] = confidence
        info["term_env"] = term_env
        info["colorterm_env"] = colorterm_env

        if self._is_tmux():
            info = self._adjust_for_tmux(info)
        if self._is_ssh():
            info = self._adjust_for_ssh(info)

        info["size"] = self._get_size()
        info["is_windows"] = platform.system() == "Windows"
        self._cached = info
        return info

    def _identify_emulator(self, term_env: str, colorterm_env: str,
                           term_program: str, term_program_version: str) -> tuple[str, float]:
        # Direct TERM_PROGRAM detection (most reliable)
        tp_map = {
            "vscode": "vscode",
            "wezterm": "WezTerm",
            "ghostty": "ghostty",
            "iterm.app": "iTerm2",
            "apple_terminal": "Apple Terminal",
        }
        for key, val in tp_map.items():
            if key in term_program:
                return val, 1.0

        # COLORTERM hints
        if "24bit" in colorterm_env or "truecolor" in colorterm_env:
            pass  # Proceed with TERM-based detection

        # TERM-based detection
        term_lower = term_env
        if "kitty" in term_lower:
            return "kitty", 0.9
        if "foot" in term_lower:
            return "foot", 0.8
        if "alacritty" in term_lower:
            return "Alacritty", 0.9
        if "xterm" in term_lower or "xterm-" in term_lower:
            return "xterm", 0.6
        if "screen" in term_lower:
            return "tmux", 0.5
        if "tmux" in term_lower:
            return "tmux", 0.9
        if "vt100" in term_lower or "vt220" in term_lower:
            return "xterm", 0.4

        # Check for 256 color capability as fallback
        if "256color" in term_lower:
            return "unknown", 0.3

        return "unknown", 0.2

    def _is_tmux(self) -> bool:
        return "TMUX" in os.environ

    def _is_ssh(self) -> bool:
        return "SSH_CONNECTION" in os.environ or "SSH_CLIENT" in os.environ

    def _adjust_for_tmux(self, info: dict) -> dict:
        info["emulator"] = "tmux"
        info["is_tmux"] = True
        return info

    def _adjust_for_ssh(self, info: dict) -> dict:
        info["is_ssh"] = True
        return info

    def _get_size(self) -> dict[str, int]:
        try:
            cols, rows = shutil.get_terminal_size()
            return {"columns": cols, "lines": rows}
        except Exception:
            return {"columns": 80, "lines": 24}

    def has_capability(self, cap: str) -> bool:
        return cap in self._cached.get("capabilities", [])

    def color_depth(self) -> str:
        return self._cached.get("color_depth", TerminalColorDepth.BITS_8)

    def supports_true_color(self) -> bool:
        return self.color_depth() == TerminalColorDepth.BITS_24

    def supports_images(self) -> bool:
        return any(c in self._cached.get("capabilities", []) for c in
                   [TerminalCapability.IMAGES, TerminalCapability.SIXEL,
                    TerminalCapability.KITTY_GRAPHICS, TerminalCapability.ITERM2_IMAGES])

    def supports_unicode(self) -> bool:
        return self._cached.get("unicode", False)

    def emulator(self) -> str:
        return self._cached.get("emulator", "unknown")

    def protocol(self) -> str:
        return self._cached.get("protocol", "standard")

    def features(self) -> dict[str, bool]:
        return dict(self._cached.get("features", {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "emulator": self.emulator(),
            "color_depth": self.color_depth(),
            "supports_true_color": self.supports_true_color(),
            "supports_images": self.supports_images(),
            "supports_unicode": self.supports_unicode(),
            "protocol": self.protocol(),
            "size": self._cached.get("size", {"columns": 80, "lines": 24}),
            "features": self.features(),
        }


_detector: TerminalCapabilityDetector | None = None


def get_detector() -> TerminalCapabilityDetector:
    global _detector
    if _detector is None:
        _detector = TerminalCapabilityDetector()
        _detector.detect()
    return _detector


def reset_detector() -> None:
    global _detector
    _detector = None
