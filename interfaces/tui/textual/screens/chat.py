"""
Textual Chat Screen — main chat interface with message list, composer, and status bar.
Connects to the CIEL Gateway or directly to the LLM bridge.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
)
from textual.widgets._list_item import ListItem

from ciel.interfaces.tui.textual.theme import CielTheme


class GatewayConnection:
    """
    Manages a gateway subprocess (JSON-RPC 2.0 over stdio).
    Textual is async, so we use a background thread for the subprocess I/O.
    """

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._msg_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._reader_task: asyncio.Task | None = None
        self.ready_event: asyncio.Event = asyncio.Event()
        self.skin_config: dict | None = None
        self.capabilities: list[str] = []
        self.event_callbacks: dict[str, list] = {}

    async def connect(self, cwd: str | None = None):
        """Start the gateway subprocess."""
        cwd = cwd or str(Path(__file__).resolve().parents[5])
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "ciel.interfaces.tui.gateway.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True,
            bufsize=1,
        )
        self._reader_task = asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        """Read stdout lines from the gateway process."""
        loop = asyncio.get_event_loop()
        while self._proc and self._proc.stdout:
            line = await loop.run_in_executor(None, self._proc.stdout.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            if "id" in msg:
                fut = self._pending.pop(msg["id"], None)
                if fut and not fut.done():
                    if "error" in msg:
                        fut.set_exception(RuntimeError(msg["error"]["message"]))
                    else:
                        fut.set_result(msg.get("result"))
            else:
                method = msg.get("method", "")
                params = msg.get("params", {})
                if method == "gateway.ready":
                    self.skin_config = params.get("skin")
                    self.capabilities = params.get("capabilities", [])
                    self.ready_event.set()
                # Dispatch events to callbacks
                callbacks = self.event_callbacks.get(method, [])
                for cb in callbacks:
                    cb(params)

    def on(self, method: str, callback):
        """Register an event callback."""
        self.event_callbacks.setdefault(method, []).append(callback)

    async def request(self, method: str, params: dict | None = None) -> Any:
        """Send a JSON-RPC request and wait for response."""
        with self._lock:
            self._msg_id += 1
            msg_id = self._msg_id
            req = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": method,
                "params": params or {},
            }
            if self._proc and self._proc.stdin:
                self._proc.stdin.write(json.dumps(req) + "\n")
                self._proc.stdin.flush()

        fut = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = fut
        try:
            return await asyncio.wait_for(fut, timeout=60)
        except asyncio.TimeoutError:
            self._pending.pop(msg_id, None)
            raise TimeoutError(f"Gateway request {method} timed out")

    async def disconnect(self):
        if self._reader_task:
            self._reader_task.cancel()
        if self._proc:
            self._proc.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, self._proc.wait),
                    timeout=5,
                )
            except asyncio.TimeoutError:
                self._proc.kill()


class MessageWidget(Static):
    """A single chat message."""

    def __init__(self, role: str, content: str, reasoning: str = "", **kwargs):
        super().__init__("", **kwargs)
        self._role = role
        self._content = content
        self._reasoning = reasoning
        self._show_reasoning = False

    def on_mount(self):
        self._render()

    def _render(self):
        c = CielTheme
        lines = []

        if self._role == "user":
            lines.append(f"[bold {c.ACCENT}]❯[/]")
            lines.append(f"[{c.TEXT}]{self._content}[/]")
        elif self._role == "assistant":
            lines.append(f"[bold {c.RESPONSE_BORDER}]◈ CIEL[/]")
            if self._reasoning:
                label = "[dim]reasoning...[/]" if self._show_reasoning else "[dim italic]+ reasoning[/]"
                lines.append(f"  {label}")
                if self._show_reasoning:
                    lines.append(f"  [{c.DIM} italic]{self._reasoning}[/]")
            lines.append(f"  [{c.TEXT}]{self._content}[/]")
        elif self._role == "tool":
            lines.append(f"[{c.TOOL_OUTPUT}]🔧 tool[/]")
            content = self._content[:200] + "..." if len(self._content) > 200 else self._content
            lines.append(f"  [{c.DIM}]{content}[/]")
        elif self._role == "system":
            lines.append(f"[{c.DIM} italic]{self._content}[/]")

        self.update("\n".join(lines))


class ComposerWidget(Static):
    """Input area at the bottom."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._input = Input(placeholder="Type a message...", id="composer-input")
        self._status = Label("", id="composer-status")

    def compose(self):
        with Container(id="composer-box"):
            yield self._input
            yield self._status

    def set_status(self, text: str):
        self._status.update(text)

    @property
    def input(self) -> Input:
        return self._input


class SessionScreen(Screen):
    """Session management screen."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("n", "new_session", "New"),
        Binding("delete", "delete_session", "Delete"),
    ]

    def __init__(self, gateway: GatewayConnection, **kwargs):
        super().__init__(**kwargs)
        self._gateway = gateway
        self._sessions: list[dict] = []

    def compose(self):
        yield Header(show_clock=True)
        yield Label("[bold]Sessions[/]  (Esc: back, n: new, del: delete)", id="session-header")
        yield ListView(id="session-list")

    def on_mount(self):
        self._load_sessions()

    async def _load_sessions(self):
        try:
            result = await self._gateway.request("sessions.list", {"limit": 50})
            self._sessions = result.get("sessions", [])
            lv = self.query_one("#session-list", ListView)
            lv.clear()
            for s in self._sessions:
                sid = s.get("id", "")[:8]
                title = s.get("title", "Chat")
                count = s.get("messageCount", 0)
                lv.append(ListItem(
                    Label(f"[bold]{sid}[/]  {title}  [dim]{count} msgs[/]")
                ))
        except Exception as e:
            self.query_one("#session-list", ListView).append(
                ListItem(Label(f"[red]Error: {e}[/]"))
            )

    def on_list_view_selected(self, event: ListView.Selected):
        if event.item and self._sessions:
            idx = self.query_one("#session-list", ListView).index
            if idx < len(self._sessions):
                session = self._sessions[idx]
                self.dismiss(session.get("id"))

    def action_new_session(self):
        self.dismiss("__new__")

    def action_delete_session(self):
        lv = self.query_one("#session-list", ListView)
        idx = lv.index
        if idx < len(self._sessions):
            sid = self._sessions[idx]["id"]
            asyncio.create_task(self._delete_and_refresh(sid))

    async def _delete_and_refresh(self, session_id: str):
        try:
            await self._gateway.request("sessions.delete", {"id": session_id})
        except Exception:
            pass
        await self._load_sessions()


class ChatScreen(Screen):
    """
    Main chat screen — message history, composer, status bar, session sidebar.
    """

    BINDINGS = [
        Binding("ctrl+p", "toggle_sessions", "Sessions"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("/", "focus_input", "Type"),
    ]

    def __init__(self, gateway: GatewayConnection | None = None, **kwargs):
        super().__init__(**kwargs)
        self._gateway = gateway or GatewayConnection()
        self._session_id: str | None = None
        self._streaming = False
        self._current_msg_widget: MessageWidget | None = None
        self._current_content = ""
        self._current_reasoning = ""
        self._log = None  # Set in on_mount

    def compose(self):
        yield Header(show_clock=True)

        with VerticalScroll(id="message-container"):
            yield RichLog(id="message-list", highlight=True, markup=True)

        yield ComposerWidget()

        with Horizontal(id="status-bar"):
            yield Label("CIEL", id="status-agent", classes="status-item")
            yield Label("●", id="status-connection", classes="status-item")
            yield Label("—", id="status-session", classes="status-item")
            yield Label("", id="status-streaming", classes="status-item")
            yield Container()
            yield Label("^P sessions", classes="status-key")
            yield Label("^L clear", classes="status-key")
            yield Label("^C quit", classes="status-key")

    async def on_mount(self):
        c = CielTheme
        self._log = self.query_one("#message-list", RichLog)

        # Show welcome
        self._log.write(f"\n\n  [bold {c.SECONDARY}]Hello, I'm CIEL[/]")
        self._log.write(f"  [{c.DIM}]Type a message to start chatting. ^P for sessions.[/]\n")

        # Connect to gateway
        await self._gateway.connect()
        await self._gateway.ready_event.wait()

        # Subscribe to events
        self._gateway.on("chat.stream", self._on_chat_event)
        self._gateway.on("session.changed", self._on_session_changed)

        # Update status
        self._update_status("session", "—")
        self._update_status("connection", f"[green]● connected[/]")

        # Create initial session
        try:
            result = await self._gateway.request("sessions.create", {
                "source": "textual",
                "platform": "textual",
            })
            self._session_id = result.get("id")
            self._update_status("session", f"#{self._session_id[:8]}")
        except Exception as e:
            self._log.write(f"[red]Session create error: {e}[/]")

    def _on_chat_event(self, params: dict):
        """Handle streaming chat events from the gateway."""
        ev_type = params.get("type")

        if ev_type == "delta":
            token = params.get("token", "")
            if token:
                self._current_content += token
                if self._current_msg_widget:
                    msg = self._current_msg_widget
                    msg._content = self._current_content
                    msg._render()
                self._update_status("streaming", "[yellow]⟳[/]")

        elif ev_type == "reasoning":
            content = params.get("content", "")
            if content:
                self._current_reasoning += content

        elif ev_type == "tool_call":
            tc = params.get("toolCall", {})
            name = tc.get("function", {}).get("name", "tool")
            self._log.write(f"[{CielTheme.TOOL_OUTPUT}]🔧 {name}[/]")

        elif ev_type == "complete":
            msg = params.get("message", {})
            content = msg.get("content", "")
            if content and self._current_msg_widget:
                self._current_msg_widget._content = content
                self._current_msg_widget._reasoning = self._current_reasoning
                self._current_msg_widget._render()
            self._streaming = False
            self._current_msg_widget = None
            self._current_content = ""
            self._current_reasoning = ""
            self._update_status("streaming", "")
            self._update_status("session", f"#{self._session_id[:8]}" if self._session_id else "—")

        elif ev_type == "error":
            self._log.write(f"[red]Error: {params.get('message', 'Unknown')}[/]")
            self._streaming = False
            self._update_status("streaming", "")

    def _on_session_changed(self, params: dict):
        session = params.get("session")
        if session:
            self._session_id = session.get("id")
            self._update_status("session", f"#{self._session_id[:8]}")

    def _update_status(self, key: str, text: str):
        widget_id = f"status-{key}"
        try:
            self.query_one(f"#{widget_id}", Label).update(text)
        except Exception:
            pass

    async def on_input_submitted(self, event: Input.Submitted):
        """Handle user input submission."""
        text = event.value.strip()
        if not text or self._streaming:
            return

        self.query_one("#composer-input", Input).clear()
        self._composer_status()

        # Display user message
        self._log.write(f"\n[bold {CielTheme.ACCENT}]❯[/] [{CielTheme.TEXT}]{text}[/]")

        # Start streaming assistant message
        self._streaming = True
        self._current_content = ""
        self._current_reasoning = ""
        self._current_msg_widget = MessageWidget(
            "assistant", "", "",
            classes="message-row",
        )
        self._log.write(self._current_msg_widget)
        self._update_status("streaming", "[yellow]⟳[/]")

        # Send to gateway
        try:
            await self._gateway.request("chat.stream", {
                "messages": [{"role": "user", "content": text}],
                "sessionId": self._session_id,
            })
        except Exception as e:
            self._log.write(f"[red]Error: {e}[/]")
            self._streaming = False
            self._update_status("streaming", "")

    def _composer_status(self):
        c = CielTheme
        try:
            input_w = self.query_one("#composer-input", Input)
            status = self.query_one("#composer-status", Label)
            if self._streaming:
                status.update(f"[{c.DIM}]⟳ streaming[/]")
            elif input_w and input_w.value:
                status.update(f"[{c.DIM}]{len(input_w.value)} chars[/]")
            else:
                status.update(f"[{c.DIM}]⏎ send[/]")
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed):
        self._composer_status()

    def action_toggle_sessions(self):
        self.push_screen(SessionScreen(self._gateway), self._on_session_selected)

    async def _on_session_selected(self, session_id: str | None):
        if session_id == "__new__":
            try:
                result = await self._gateway.request("sessions.create", {
                    "source": "textual",
                    "platform": "textual",
                })
                self._session_id = result.get("id")
                self._update_status("session", f"#{self._session_id[:8]}")
            except Exception:
                pass
        elif session_id:
            self._session_id = session_id
            self._update_status("session", f"#{session_id[:8]}")

    def action_clear(self):
        self._current_content = ""
        self._current_reasoning = ""
        self._current_msg_widget = None
        if self._log:
            self._log.clear()
            self._log.write(f"\n[bold {CielTheme.SECONDARY}]Cleared[/]")

    def action_focus_input(self):
        try:
            self.query_one("#composer-input", Input).focus()
        except Exception:
            pass
