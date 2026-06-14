from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Theme:
    name: str
    description: str = ""
    colors: dict[str, str] = field(default_factory=dict)
    is_dark: bool = True


CIEL_DARK = Theme(
    name="ciel-dark",
    description="Theme CIEL sombre par défaut",
    is_dark=True,
    colors={
        "primary": "#6C5CE7",
        "secondary": "#A29BFE",
        "accent": "#FD79A8",
        "success": "#55E6C1",
        "warning": "#FECA57",
        "error": "#FF6B6B",
        "dim": "#636E72",
        "text": "#DFE6E9",
        "surface": "#1a1a2e",
        "background": "#0f0f23",
        "banner_border": "#6C5CE7",
        "banner_title": "#A29BFE",
        "banner_accent": "#FD79A8",
        "banner_dim": "#636E72",
        "banner_text": "#DFE6E9",
        "response_border": "#6C5CE7",
        "tool_output": "#55E6C1",
        "muted": "#636E72",
    },
)

CIEL_LIGHT = Theme(
    name="ciel-light",
    description="Theme CIEL clair",
    is_dark=False,
    colors={
        "primary": "#6C5CE7",
        "secondary": "#A29BFE",
        "accent": "#E84393",
        "success": "#00B894",
        "warning": "#FDCB6E",
        "error": "#D63031",
        "dim": "#B2BEC3",
        "text": "#2D3436",
        "surface": "#FFFFFF",
        "background": "#F5F6FA",
        "banner_border": "#6C5CE7",
        "banner_title": "#A29BFE",
        "banner_accent": "#E84393",
        "banner_dim": "#B2BEC3",
        "banner_text": "#2D3436",
        "response_border": "#6C5CE7",
        "tool_output": "#00B894",
        "muted": "#B2BEC3",
    },
)

NORD = Theme(
    name="nord",
    description="Nord — Arctic, north-bluish color palette",
    is_dark=True,
    colors={
        "primary": "#88C0D0",
        "secondary": "#81A1C1",
        "accent": "#BF616A",
        "success": "#A3BE8C",
        "warning": "#EBCB8B",
        "error": "#BF616A",
        "dim": "#4C566A",
        "text": "#D8DEE9",
        "surface": "#2E3440",
        "background": "#3B4252",
        "banner_border": "#88C0D0",
        "banner_title": "#81A1C1",
        "banner_accent": "#BF616A",
        "banner_dim": "#4C566A",
        "banner_text": "#D8DEE9",
        "response_border": "#88C0D0",
        "tool_output": "#A3BE8C",
        "muted": "#4C566A",
    },
)

DRACULA = Theme(
    name="dracula",
    description="Dracula — dark theme with vibrant accents",
    is_dark=True,
    colors={
        "primary": "#BD93F9",
        "secondary": "#FF79C6",
        "accent": "#FF5555",
        "success": "#50FA7B",
        "warning": "#F1FA8C",
        "error": "#FF5555",
        "dim": "#6272A4",
        "text": "#F8F8F2",
        "surface": "#44475A",
        "background": "#282A36",
        "banner_border": "#BD93F9",
        "banner_title": "#FF79C6",
        "banner_accent": "#FF5555",
        "banner_dim": "#6272A4",
        "banner_text": "#F8F8F2",
        "response_border": "#BD93F9",
        "tool_output": "#50FA7B",
        "muted": "#6272A4",
    },
)

TOKYO_NIGHT = Theme(
    name="tokyo-night",
    description="Tokyo Night — deep blues with neon accents",
    is_dark=True,
    colors={
        "primary": "#7AA2F7",
        "secondary": "#BB9AF7",
        "accent": "#F7768E",
        "success": "#9ECE6A",
        "warning": "#E0AF68",
        "error": "#F7768E",
        "dim": "#565F89",
        "text": "#A9B1D6",
        "surface": "#1A1B26",
        "background": "#16161E",
        "banner_border": "#7AA2F7",
        "banner_title": "#BB9AF7",
        "banner_accent": "#F7768E",
        "banner_dim": "#565F89",
        "banner_text": "#A9B1D6",
        "response_border": "#7AA2F7",
        "tool_output": "#9ECE6A",
        "muted": "#565F89",
    },
)

_ALL_THEMES: dict[str, Theme] = {
    "ciel-dark": CIEL_DARK,
    "ciel-light": CIEL_LIGHT,
    "nord": NORD,
    "dracula": DRACULA,
    "tokyo-night": TOKYO_NIGHT,
}

_current_theme: str = "ciel-dark"


def get_theme(name: str | None = None) -> Theme:
    if name is None:
        name = _current_theme
    return _ALL_THEMES.get(name, CIEL_DARK)


def set_theme(name: str) -> bool:
    global _current_theme
    if name in _ALL_THEMES:
        _current_theme = name
        return True
    return False


def list_themes() -> list[dict[str, Any]]:
    return [
        {"name": t.name, "description": t.description, "is_dark": t.is_dark}
        for t in _ALL_THEMES.values()
    ]


def get_theme_css(theme_name: str | None = None) -> str:
    theme = get_theme(theme_name)
    vars_ = "\n".join(
        f"  --{k.replace('_', '-')}: {v};"
        for k, v in theme.colors.items()
    )
    return f":root {{\n{vars_}\n}}"


def get_theme_tcss(theme_name: str | None = None) -> str:
    theme = get_theme(theme_name)
    vars_ = "\n".join(
        f"${k.replace('_', '-')}: {v};"
        for k, v in theme.colors.items()
    )
    return vars_
