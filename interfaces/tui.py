"""
CIEL v∞.3 — TUI (Terminal User Interface) Textual.

Interface immersive avec streaming, markdown, historique, multi-provider.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

from rich.markdown import Markdown as RichMarkdown
from rich.syntax import Syntax
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button, Footer, Header, Input, Label, ListView, ListItem,
    Markdown, RichLog, Select, Static, TabbedContent, TabPane,
)
from textual.worker import Worker, WorkerState


# ── Config providers ─────────────────────────────────


PROVIDER_CONFIG: dict[str, tuple[Any, str, str, str]] = {
    "openai":    (None, "OPENAI_API_KEY",    "gpt-4o",            ""),
    "google":    (None, "GOOGLE_API_KEY",    "gemini-2.0-flash",  ""),
    "anthropic": (None, "ANTHROPIC_API_KEY", "claude-3-5-sonnet-latest", ""),
    "deepseek":  (None, "DEEPSEEK_API_KEY",  "deepseek-chat",     "https://api.deepseek.com/v1/chat/completions"),
    "github":    (None, "GITHUB_TOKEN",      "gpt-4o",            "https://models.inference.ai.azure.com/chat/completions"),
    "kimi":      (None, "KIMI_API_KEY",      "kimi-k2",           "https://api.moonshot.cn/v1/chat/completions"),
    "groq":      (None, "GROQ_API_KEY",      "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1/chat/completions"),
    "together":  (None, "TOGETHER_API_KEY",  "meta-llama/Llama-3.3-70B-Instruct-Turbo", "https://api.together.xyz/v1/chat/completions"),
    "mistral":   (None, "MISTRAL_API_KEY",   "mistral-large-latest", "https://api.mistral.ai/v1/chat/completions"),
    "perplexity":(None, "PERPLEXITY_API_KEY","sonar",             "https://api.perplexity.ai/chat/completions"),
    "xai":       (None, "XAI_API_KEY",       "grok-2",            "https://api.x.ai/v1/chat/completions"),
    "ollama":    (None, "",                  "llama3.2",          "http://localhost:11434/v1/chat/completions"),
    "llmstudio": (None, "",                  "local-model",       "http://localhost:1234/v1/chat/completions"),
}


def _get_llm(provider: str, model: str | None = None):
    from ciel.llmbridge.providers import (
        OpenAIProvider, GeminiProvider, AnthropicProvider,
    )
    mapper = {
        "openai": OpenAIProvider, "google": GeminiProvider,
        "anthropic": AnthropicProvider,
    }
    cls = mapper.get(provider, OpenAIProvider)
    entry = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["openai"])
    _, env_key, default_model, base_url = entry
    api_key = os.environ.get(env_key, "") if env_key else ""
    return cls(api_key=api_key, model=model or default_model, base_url=base_url)


# ── Widgets ──────────────────────────────────────────


class ChatMessage(Static):
    """Un message dans le chat."""

    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.content = content
        prefix = "[bold cyan]CIEL[/]" if role == "assistant" else "[bold green]VOUS[/]"
        self.update(f"{prefix}\n\n{content}")


class StatusBar(Static):
    """Barre de statut avec provider/modèle actuel."""

    provider = reactive("openai")
    model = reactive("gpt-4o")
    tokens = reactive(0)
    msgs = reactive(0)

    def watch_provider(self, val: str) -> None:
        self._render()

    def watch_model(self, val: str) -> None:
        self._render()

    def _render(self) -> None:
        self.update(
            f"  Provider: [bold cyan]{self.provider}[/]  "
            f"Modèle: [bold yellow]{self.model}[/]  "
            f"Messages: {self.msgs}  "
            f"Tokens: {self.tokens}"
        )


# ── Écran principal ─────────────────────────────────


class ChatScreen(Screen):
    """Écran de chat principal."""

    BINDINGS = [
        Binding("/", "focus_input", "Commande", key_display="/"),
        Binding("ctrl+p", "change_provider", "Provider"),
        Binding("ctrl+m", "change_model", "Modèle"),
        Binding("ctrl+l", "clear", "Effacer"),
        Binding("ctrl+n", "new_session", "Nouveau"),
        Binding("ctrl+q", "quit", "Quitter"),
        Binding("escape", "focus_input", "Focus"),
    ]

    def __init__(self, initial_provider: str = "openai", initial_model: str | None = None):
        super().__init__()
        self.current_provider = initial_provider
        self.current_model = initial_model
        self._messages: list[dict[str, str]] = []
        self._session_id = ""
        self._llm = None
        self._bridge = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            yield StatusBar(id="status")
            yield RichLog(id="chat", highlight=True, markup=True, wrap=True)
            with Horizontal(id="input-row"):
                yield Input(
                    placeholder="Tapez votre message... (/) commandes",
                    id="input",
                )
                yield Button("Envoyer", id="send", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self._init_backend()
        chat = self.query_one("#chat", RichLog)
        chat.write("[bold cyan]CIEL v∞.3  —  Chat Terminal[/]")
        chat.write("[dim]/help  Ctrl+P provider  Ctrl+M modèle  Ctrl+N nouveau  Ctrl+L effacer[/]\n")
        self._update_status()

    def _init_backend(self) -> None:
        from ciel.llmbridge.core import LLMBridgeEngine
        self._bridge = LLMBridgeEngine()
        self._session_id = self._bridge.create_session(title="tui")
        self._llm = _get_llm(self.current_provider, self.current_model)

    def _update_status(self) -> None:
        sb = self.query_one("#status", StatusBar)
        sb.provider = self.current_provider
        sb.model = self._llm.model if self._llm else "?"
        sb.msgs = len(self._messages) // 2

    def action_focus_input(self) -> None:
        self.query_one("#input", Input).focus()

    def action_change_provider(self) -> None:
        names = list(PROVIDER_CONFIG.keys())
        idx = names.index(self.current_provider) if self.current_provider in names else 0
        next_idx = (idx + 1) % len(names)
        self.current_provider = names[next_idx]
        self._llm = _get_llm(self.current_provider, self.current_model)
        chat = self.query_one("#chat", RichLog)
        chat.write(f"\n[bold yellow]║ Provider changé : {self.current_provider}[/]\n")
        self._update_status()

    def action_change_model(self) -> None:
        from ciel.providers import get_registry
        p = get_registry().get(self.current_provider)
        if p and p.models:
            models = p.models
            idx = models.index(self.current_model) if self.current_model in models else 0
            next_idx = (idx + 1) % len(models)
            self.current_model = models[next_idx]
        else:
            self.current_model = f"{self.current_model}-next"
        self._llm = _get_llm(self.current_provider, self.current_model)
        chat = self.query_one("#chat", RichLog)
        chat.write(f"\n[bold yellow]║ Modèle changé : {self.current_model}[/]\n")
        self._update_status()

    def action_clear(self) -> None:
        chat = self.query_one("#chat", RichLog)
        chat.clear()
        self._messages.clear()
        chat.write("[dim]Conversation effacée.[/]\n")

    def action_new_session(self) -> None:
        if self._bridge and self._session_id:
            self._bridge.close_session(self._session_id)
        self._init_backend()
        self._messages.clear()
        chat = self.query_one("#chat", RichLog)
        chat.clear()
        chat.write("[bold green]║ Nouvelle conversation démarrée[/]\n")
        self._update_status()

    def action_quit(self) -> None:
        self.app.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._handle_input(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        inp = self.query_one("#input", Input)
        self._handle_input(inp.value)

    def _handle_input(self, text: str) -> None:
        inp = self.query_one("#input", Input)
        chat = self.query_one("#chat", RichLog)

        if not text.strip():
            return

        inp.value = ""

        # Slash commands
        if text.startswith("/"):
            self._handle_command(text[1:].strip(), chat)
            return

        # User message
        self._messages.append({"role": "user", "content": text})
        if self._bridge and self._session_id:
            self._bridge.send_message(self._session_id, text)
        chat.write(f"\n[bold green]▌ VOUS[/]\n{text}\n")
        self._update_status()

        # LLM response (async)
        self._call_llm(chat)

    @work(exclusive=True, thread=True)
    async def _call_llm(self, chat: RichLog) -> None:
        """Appel LLM avec streaming."""
        from ciel.llmbridge.providers import Message as LLMMsg

        msgs = [LLMMsg(role=m["role"], content=m["content"]) for m in self._messages]

        try:
            resp = await self._llm.chat_completion(msgs)
            self.app.call_from_thread(self._handle_response, resp.content, chat)
        except Exception as e:
            self.app.call_from_thread(self._handle_error, str(e), chat)

    def _handle_response(self, content: str, chat: RichLog) -> None:
        content = content.strip()
        self._messages.append({"role": "assistant", "content": content})
        if self._bridge and self._session_id:
            self._bridge.send_message(self._session_id, content, role="assistant")

        # Detect code blocks
        if "```" in content:
            chat.write(f"\n[bold cyan]▌ CIEL[/]\n")
            chat.write(RichMarkdown(content))
        else:
            chat.write(f"\n[bold cyan]▌ CIEL[/]\n{content}\n")
        self._update_status()

    def _handle_error(self, error: str, chat: RichLog) -> None:
        chat.write(f"\n[bold red]║ Erreur : {error}[/]\n")

    def _handle_command(self, cmd_text: str, chat: RichLog) -> None:
        parts = cmd_text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            chat.write("""
[bold]Commandes :[/]
  [cyan]/provider <nom>[/]   Changer de fournisseur
  [cyan]/model <nom>[/]      Changer de modèle
  [cyan]/providers[/]         Lister les providers
  [cyan]/new[/]              Nouvelle conversation
  [cyan]/clear[/]            Effacer l'écran
  [cyan]/help[/]             Cette aide

[bold]Raccourcis :[/]
  [cyan]Ctrl+P[/]  Provider suivant     [cyan]Ctrl+M[/]  Modèle suivant
  [cyan]Ctrl+N[/]  Nouveau              [cyan]Ctrl+L[/]  Effacer
  [cyan]Ctrl+Q[/]  Quitter              [cyan]Esc[/]     Focus input
""")
        elif cmd == "provider":
            if arg in PROVIDER_CONFIG:
                self.current_provider = arg
                self._llm = _get_llm(self.current_provider, self.current_model)
                chat.write(f"\n[bold green]║ Provider → {arg}[/]\n")
                self._update_status()
            else:
                chat.write(f"\n[bold red]║ Provider inconnu : {arg}[/]\n")

        elif cmd == "model":
            self.current_model = arg
            self._llm = _get_llm(self.current_provider, self.current_model)
            chat.write(f"\n[bold green]║ Modèle → {arg}[/]\n")
            self._update_status()

        elif cmd == "providers":
            from ciel.providers import get_registry
            r = get_registry()
            lines = ["[bold]Providers disponibles :[/]"]
            for p in sorted(r.list(), key=lambda x: x.name):
                status = "✓" if p.is_available else "✗"
                sel = " ←" if p.name == self.current_provider else ""
                lines.append(f"  [{('green' if p.is_available else 'red')}]{status}[/] {p.name}{sel}")
            chat.write("\n" + "\n".join(lines) + "\n")

        elif cmd == "new":
            self.action_new_session()

        elif cmd == "clear":
            self.action_clear()

        else:
            chat.write(f"\n[bold red]║ Commande inconnue : /{cmd}[/]\n")


# ── App ───────────────────────────────────────────────


class CIELTUI(App):
    """CIEL v∞.3 — Terminal User Interface."""

    TITLE = "CIEL v∞.3"
    SUB_TITLE = "Chat Terminal"
    CSS = """
    Screen {
        background: #1a1b26;
    }
    #main {
        height: 100%;
    }
    #status {
        height: 1;
        background: #24253a;
        color: #a9b1d6;
        padding: 0 1;
    }
    #chat {
        height: 1fr;
        border: none;
        padding: 1 2;
        overflow-y: auto;
    }
    #input-row {
        height: 3;
        padding: 0 1 1 1;
    }
    #input {
        width: 1fr;
        background: #24253a;
        color: #c0caf5;
        border: none;
    }
    #send {
        width: 10;
        background: #7aa2f7;
        color: #1a1b26;
        border: none;
    }
    Header {
        background: #1a1b26;
        color: #7aa2f7;
    }
    Footer {
        background: #24253a;
        color: #565f89;
    }
    """

    def __init__(self, provider: str = "openai", model: str | None = None):
        super().__init__()
        self._provider = provider
        self._model = model

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ChatScreen(self._provider, self._model)
        yield Footer()

    def on_screen_resume(self, screen: Screen) -> None:
        self.refresh()


def run_tui(provider: str = "openai", model: str | None = None) -> None:
    """Lance l'interface TUI Textual."""
    app = CIELTUI(provider=provider, model=model)
    app.run()


if __name__ == "__main__":
    run_tui()
