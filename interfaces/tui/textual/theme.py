"""
Theme configuration for Textual TUI.
Mirrors the Ink TUI skin config for visual consistency.
"""

from __future__ import annotations

from typing import ClassVar

from textual.theme import Theme


class CielTheme:
    """CIEL dark theme constants — shared between Ink and Textual."""

    PRIMARY = "#6C5CE7"
    SECONDARY = "#A29BFE"
    ACCENT = "#FD79A8"
    SUCCESS = "#55E6C1"
    WARNING = "#FECA57"
    ERROR = "#FF6B6B"
    DIM = "#636E72"
    TEXT = "#DFE6E9"
    SURFACE = "#1a1a2e"
    BACKGROUND = "#0f0f23"
    TOOL_OUTPUT = "#55E6C1"
    RESPONSE_BORDER = "#74B9FF"

    @classmethod
    def to_textual_theme(cls) -> Theme:
        return Theme(
            name="ciel-dark",
            primary=cls.PRIMARY,
            secondary=cls.SECONDARY,
            accent=cls.ACCENT,
            success=cls.SUCCESS,
            warning=cls.WARNING,
            error=cls.ERROR,
            surface=cls.SURFACE,
            background=cls.BACKGROUND,
            dark=True,
            variables={
                "dim": cls.DIM,
                "text": cls.TEXT,
                "tool-output": cls.TOOL_OUTPUT,
                "response-border": cls.RESPONSE_BORDER,
            },
        )

    @classmethod
    def to_css(cls) -> str:
        return f"""
$primary: {cls.PRIMARY};
$secondary: {cls.SECONDARY};
$accent: {cls.ACCENT};
$success: {cls.SUCCESS};
$warning: {cls.WARNING};
$error: {cls.ERROR};
$dim: {cls.DIM};
$text: {cls.TEXT};
$surface: {cls.SURFACE};
$background: {cls.BACKGROUND};
$tool-output: {cls.TOOL_OUTPUT};
$response-border: {cls.RESPONSE_BORDER};
"""
