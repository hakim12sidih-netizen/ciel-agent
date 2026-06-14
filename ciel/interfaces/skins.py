from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.interfaces.themes import get_theme, list_themes, get_theme_css, get_theme_tcss


@dataclass
class Skin:
    name: str
    display_name: str
    description: str
    theme_name: str = "ciel-dark"
    colors: dict[str, str] = field(default_factory=dict)
    ui: dict[str, Any] = field(default_factory=lambda: {
        "borders": "rounded",
        "show_header": True,
        "show_footer": True,
        "animations": True,
        "compact": False,
    })

    def get_css_vars(self) -> str:
        parts = []
        for k, v in self.colors.items():
            parts.append(f"  --{k.replace('_', '-')}: {v};")
        return "\n".join(parts)

    def get_tcss_vars(self) -> str:
        parts = []
        for k, v in self.colors.items():
            parts.append(f"${k.replace('_', '-')}: {v};")
        return "\n".join(parts)


# ── Built-in skins ─────────────────────────────────

BUILTIN_SKINS: dict[str, Skin] = {
    "ciel-dark": Skin(
        name="ciel-dark", display_name="CIEL Dark",
        description="Thème CIEL sombre par défaut",
        theme_name="ciel-dark",
        colors={
            "primary": "#6C5CE7", "secondary": "#A29BFE",
            "accent": "#FD79A8", "success": "#55E6C1",
            "warning": "#FECA57", "error": "#FF6B6B",
            "dim": "#636E72", "text": "#DFE6E9",
            "surface": "#1a1a2e", "background": "#0f0f23",
            "input-bg": "#16213e", "input-fg": "#DFE6E9",
            "border": "#6C5CE7", "header-bg": "#1a1a2e",
        },
    ),
    "ciel-light": Skin(
        name="ciel-light", display_name="CIEL Light",
        description="Thème CIEL clair",
        theme_name="ciel-light",
        colors={
            "primary": "#6C5CE7", "secondary": "#A29BFE",
            "accent": "#E84393", "success": "#00B894",
            "warning": "#FDCB6E", "error": "#D63031",
            "dim": "#B2BEC3", "text": "#2D3436",
            "surface": "#FFFFFF", "background": "#F5F6FA",
            "input-bg": "#FFFFFF", "input-fg": "#2D3436",
            "border": "#6C5CE7", "header-bg": "#FFFFFF",
        },
    ),
    "nord": Skin(
        name="nord", display_name="Nord",
        description="Nord — Arctic, north-bluish",
        theme_name="nord",
        colors={
            "primary": "#88C0D0", "secondary": "#81A1C1",
            "accent": "#BF616A", "success": "#A3BE8C",
            "warning": "#EBCB8B", "error": "#BF616A",
            "dim": "#4C566A", "text": "#D8DEE9",
            "surface": "#2E3440", "background": "#3B4252",
            "input-bg": "#434C5E", "input-fg": "#D8DEE9",
            "border": "#88C0D0", "header-bg": "#2E3440",
        },
    ),
    "dracula": Skin(
        name="dracula", display_name="Dracula",
        description="Dracula — dark with vibrant accents",
        theme_name="dracula",
        colors={
            "primary": "#BD93F9", "secondary": "#FF79C6",
            "accent": "#FF5555", "success": "#50FA7B",
            "warning": "#F1FA8C", "error": "#FF5555",
            "dim": "#6272A4", "text": "#F8F8F2",
            "surface": "#44475A", "background": "#282A36",
            "input-bg": "#44475A", "input-fg": "#F8F8F2",
            "border": "#BD93F9", "header-bg": "#282A36",
        },
    ),
    "tokyo-night": Skin(
        name="tokyo-night", display_name="Tokyo Night",
        description="Tokyo Night - deep blues with neon accents",
        theme_name="tokyo-night",
        colors={
            "primary": "#7AA2F7", "secondary": "#BB9AF7",
            "accent": "#F7768E", "success": "#9ECE6A",
            "warning": "#E0AF68", "error": "#F7768E",
            "dim": "#565F89", "text": "#A9B1D6",
            "surface": "#1A1B26", "background": "#16161E",
            "input-bg": "#24253A", "input-fg": "#A9B1D6",
            "border": "#7AA2F7", "header-bg": "#1A1B26",
        },
    ),
    "kawaii": Skin(
        name="kawaii", display_name="Kawaii",
        description="Pastel kawaii theme",
        theme_name="ciel-dark",
        colors={
            "primary": "#FF9FF3", "secondary": "#F368E0",
            "accent": "#FF6B6B", "success": "#1dd1a1",
            "warning": "#feca57", "error": "#ee5a24",
            "dim": "#8395a7", "text": "#2d3436",
            "surface": "#ffeaa7", "background": "#fdcb6e",
            "input-bg": "#ffeaa7", "input-fg": "#2d3436",
            "border": "#FF9FF3", "header-bg": "#fdcb6e",
        },
        ui={"compact": True, "animations": True},
    ),
    "professional": Skin(
        name="professional", display_name="Professional",
        description="Clean, minimal, enterprise-ready",
        theme_name="ciel-light",
        colors={
            "primary": "#0984e3", "secondary": "#74b9ff",
            "accent": "#e17055", "success": "#00b894",
            "warning": "#fdcb6e", "error": "#d63031",
            "dim": "#b2bec3", "text": "#2d3436",
            "surface": "#ffffff", "background": "#f5f6fa",
            "input-bg": "#ffffff", "input-fg": "#2d3436",
            "border": "#0984e3", "header-bg": "#f5f6fa",
        },
        ui={"borders": "solid", "show_header": True, "animations": False},
    ),
    "minimal": Skin(
        name="minimal", display_name="Minimal",
        description="Minimalist monochrome",
        theme_name="ciel-dark",
        colors={
            "primary": "#b2bec3", "secondary": "#dfe6e9",
            "accent": "#74b9ff", "success": "#55efc4",
            "warning": "#ffeaa7", "error": "#fab1a0",
            "dim": "#636e72", "text": "#dfe6e9",
            "surface": "#1a1a2e", "background": "#0f0f23",
            "input-bg": "#16213e", "input-fg": "#dfe6e9",
            "border": "#636e72", "header-bg": "#0f0f23",
        },
        ui={"borders": "none", "show_header": False, "show_footer": False},
    ),
}


class SkinManager:
    def __init__(self, skins_dir: str | Path | None = None):
        self._dir = Path(skins_dir or Path.home() / ".ciel" / "skins")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._skins: dict[str, Skin] = dict(BUILTIN_SKINS)
        self._current = "ciel-dark"
        self._load_custom()

    def _load_custom(self) -> None:
        for f in self._dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                skin = Skin(**data)
                self._skins[skin.name] = skin
            except Exception:
                pass

    def get(self, name: str | None = None) -> Skin:
        return self._skins.get(name or self._current, self._skins["ciel-dark"])

    def list(self) -> list[Skin]:
        return list(self._skins.values())

    def set_current(self, name: str) -> bool:
        if name in self._skins:
            self._current = name
            from ciel.interfaces.themes import set_theme
            set_theme(self._skins[name].theme_name)
            return True
        return False

    def get_current(self) -> Skin:
        return self.get(self._current)

    def register_custom(self, skin: Skin) -> None:
        self._skins[skin.name] = skin
        path = self._dir / f"{skin.name}.json"
        path.write_text(json.dumps(vars(skin), indent=2, default=str))

    def generate_tui_css(self, skin_name: str | None = None) -> str:
        skin = self.get(skin_name)
        c = skin.colors
        theme = skin.ui
        return f"""
Screen {{
    background: {c['background']};
}}
#message-container {{
    background: {c['surface']};
}}
#message-list {{
    background: {c['surface']};
    color: {c['text']};
}}
#composer-box {{
    background: {c['input-bg']};
    color: {c['input-fg']};
    border: {theme.get('borders', 'rounded')} {c['border']};
}}
#status-bar {{
    background: {c['header-bg']};
    color: {c['dim']};
}}
.status-key {{
    color: {c['dim']};
}}
.dashboard-card {{
    background: {c['surface']};
    color: {c['text']};
    border: {theme.get('borders', 'rounded')} {c['border']};
}}
"""


_skin_manager: SkinManager | None = None


def get_skin_manager() -> SkinManager:
    global _skin_manager
    if _skin_manager is None:
        _skin_manager = SkinManager()
    return _skin_manager


def list_skins() -> list[dict[str, Any]]:
    return [
        {"name": s.name, "display_name": s.display_name,
         "description": s.description, "theme": s.theme_name}
        for s in get_skin_manager().list()
    ]
