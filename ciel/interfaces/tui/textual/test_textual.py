"""
Tests for CIEL Textual TUI.
Run: python3 -m pytest ciel/interfaces/tui/textual/test_textual.py -v
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ciel.interfaces.tui.textual.theme import CielTheme
from ciel.interfaces.tui.textual.screens.chat import ChatScreen, GatewayConnection, MessageWidget
from ciel.interfaces.tui.textual.screens.dashboard import DashboardScreen, StatCard


class TestCielTheme:
    def test_to_textual_theme(self):
        theme = CielTheme.to_textual_theme()
        assert theme.name == "ciel-dark"
        assert theme.primary == "#6C5CE7"
        assert theme.dark is True

    def test_to_css(self):
        css = CielTheme.to_css()
        assert "$primary: #6C5CE7" in css
        assert "$accent: #FD79A8" in css
        assert "$dim: #636E72" in css

    def test_colors_defined(self):
        assert CielTheme.PRIMARY == "#6C5CE7"
        assert CielTheme.SECONDARY == "#A29BFE"
        assert CielTheme.ACCENT == "#FD79A8"
        assert CielTheme.SUCCESS == "#55E6C1"
        assert CielTheme.WARNING == "#FECA57"
        assert CielTheme.ERROR == "#FF6B6B"
        assert CielTheme.DIM == "#636E72"
        assert CielTheme.TEXT == "#DFE6E9"
        assert CielTheme.SURFACE == "#1a1a2e"
        assert CielTheme.BACKGROUND == "#0f0f23"


class TestMessageWidget:
    def test_user_message(self):
        w = MessageWidget("user", "hello")
        assert w._role == "user"
        assert w._content == "hello"

    def test_assistant_message(self):
        w = MessageWidget("assistant", "response", reasoning="thinking")
        assert w._role == "assistant"
        assert w._reasoning == "thinking"

    def test_tool_message_truncation(self):
        long = "x" * 300
        w = MessageWidget("tool", long)
        assert w._content == long

    def test_system_message(self):
        w = MessageWidget("system", "system message")
        assert w._role == "system"

    def test_render_user_message(self):
        w = MessageWidget("user", "test message")
        w._render()
        rendered = w.render()
        text = str(rendered) if hasattr(rendered, '__str__') else rendered
        text_str = rendered.plain if hasattr(rendered, 'plain') else str(text)
        assert "test message" in text_str

    def test_render_assistant_message(self):
        w = MessageWidget("assistant", "response text", reasoning="some reasoning")
        w._render()
        rendered = w.render()
        text_str = rendered.plain if hasattr(rendered, 'plain') else str(rendered)
        assert "CIEL" in text_str
        assert "response text" in text_str
        assert "reasoning" in text_str

    def test_toggle_reasoning(self):
        w = MessageWidget("assistant", "text", reasoning="hidden reasoning")
        w._show_reasoning = True
        w._render()
        rendered = w.render()
        text_str = rendered.plain if hasattr(rendered, 'plain') else str(rendered)
        assert "hidden reasoning" in text_str

    def test_tool_render_with_long_content(self):
        long = "x" * 300
        w = MessageWidget("tool", long)
        w._render()
        rendered = w.render()
        text_str = rendered.plain if hasattr(rendered, 'plain') else str(rendered)
        assert "..." in text_str


class TestGatewayConnection:
    def test_event_callback_registration(self):
        gw = GatewayConnection()
        cb = lambda x: None
        gw.on("test.event", cb)
        assert cb in gw.event_callbacks["test.event"]

    def test_multiple_event_callbacks(self):
        gw = GatewayConnection()
        cb1 = lambda x: None
        cb2 = lambda x: None
        gw.on("test.event", cb1)
        gw.on("test.event", cb2)
        assert len(gw.event_callbacks["test.event"]) == 2

    def test_ready_event_not_set(self):
        gw = GatewayConnection()
        assert not gw.ready_event.is_set()

    def test_initial_state(self):
        gw = GatewayConnection()
        assert gw.skin_config is None
        assert gw.capabilities == []


class TestChatScreen:
    def test_initial_state(self):
        screen = ChatScreen()
        assert screen._session_id is None
        assert screen._streaming is False
        assert screen._current_content == ""

    def test_clear_action(self):
        screen = ChatScreen()
        screen._log = MagicMock()
        screen.action_clear()
        assert screen._current_content == ""

    def test_streaming_state_management(self):
        screen = ChatScreen()
        screen._log = MagicMock()
        assert screen._streaming is False
        screen._streaming = True
        assert screen._streaming is True

    def test_composer_status_non_streaming(self):
        screen = ChatScreen()
        screen._log = MagicMock()
        screen._composer_status()

    def test_msg_widget_updates_on_delta(self):
        screen = ChatScreen()
        screen._log = MagicMock()
        screen._current_msg_widget = MessageWidget("assistant", "", "")
        screen._on_chat_event({"type": "delta", "token": "hello "})
        assert "hello" in screen._current_content

    def test_chat_complete_resets_stream(self):
        screen = ChatScreen()
        screen._log = MagicMock()
        screen._streaming = True
        screen._current_msg_widget = MessageWidget("assistant", "", "")
        screen._on_chat_event({
            "type": "complete",
            "message": {"role": "assistant", "content": "done"},
        })
        assert screen._streaming is False

    def test_chat_error_clears_stream(self):
        screen = ChatScreen()
        screen._log = MagicMock()
        screen._streaming = True
        screen._on_chat_event({"type": "error", "message": "fail"})
        assert screen._streaming is False


class TestDashboard:
    def test_dashboard_screen_import(self):
        screen = DashboardScreen()
        assert screen is not None

    def test_stat_card_creation(self):
        card = StatCard("Test", "42", "subtitle")
        assert card._card_title == "Test"
        assert card._value == "42"
        assert card._subtitle == "subtitle"

    def test_stat_card_update(self):
        card = StatCard("Test", "old")
        card.update_value("new", "updated")
        assert card._value == "new"
        assert card._subtitle == "updated"

    def test_stat_card_render(self):
        card = StatCard("Title", "Value", "Sub")
        card._render()
        rendered = card.render()
        text_str = rendered.plain if hasattr(rendered, 'plain') else str(rendered)
        assert "Title" in text_str
        assert "Value" in text_str

    def test_dashboard_refresh_task(self):
        screen = DashboardScreen()
        screen._cards = {}
        screen._start_time = 0
