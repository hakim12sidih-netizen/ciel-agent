"""
Gateway event emitter.
Sends events back to the TUI client (tool progress, approvals, stream chunks, etc.)
"""

from typing import Any

from ciel.interfaces.tui.gateway.transport import StdioTransport


SKIN_CONFIG = {
    "name": "ciel-dark",
    "description": "CIEL Dark Theme",
    "colors": {
        "bannerBorder": "#6C5CE7",
        "bannerTitle": "#A29BFE",
        "bannerAccent": "#FD79A8",
        "bannerDim": "#636E72",
        "bannerText": "#DFE6E9",
        "responseBorder": "#74B9FF",
        "toolOutput": "#55E6C1",
        "error": "#FF6B6B",
        "warning": "#FECA57",
        "success": "#55E6C1",
        "muted": "#636E72",
    },
    "spinner": {
        "waitingFaces": ["(⌐■_■)", "(¬_¬)", "(•_•)", "(◕‿◕)"],
        "thinkingFaces": ["(⊙_⊙)", "(◉_◉)", "(◎_◎)", "(◉‿◉)"],
        "thinkingVerbs": [
            "contemplating", "synthesizing", "analyzing", "processing",
            "reasoning", "computing", "optimizing", "evolving",
        ],
        "wings": [
            ["★", "✧", "✦", "✧", "★"],
            ["✧", "✦", "★", "✦", "✧"],
        ],
    },
    "branding": {
        "agentName": "CIEL",
        "welcome": "Hello, I'm CIEL",
        "responseLabel": "CIEL",
        "promptSymbol": "❯",
    },
    "toolPrefix": "🔧",
    "toolEmojis": {
        "bash": "💻",
        "read": "📖",
        "write": "✍️",
        "glob": "🔍",
        "grep": "🔎",
        "web_search": "🌐",
        "web_fetch": "📄",
        "edit": "✏️",
        "ask": "❓",
        "computer": "🖥️",
        "voice": "🎤",
        "mcp": "🔌",
    },
}


class GatewayEventEmitter:
    """
    Emits events to the TUI client.
    Events include: gateway.ready, chat deltas, tool calls, approvals, etc.
    """

    def __init__(self, transport: StdioTransport):
        self.transport = transport

    async def _emit(self, method: str, params: dict | None = None):
        await self.transport.send_event(method, params)

    async def ready(self, version: str, capabilities: list[str]):
        await self._emit("gateway.ready", {
            "version": version,
            "skin": SKIN_CONFIG,
            "capabilities": capabilities,
        })

    async def chat_delta(self, token: str, reasoning: str | None = None):
        params: dict[str, Any] = {"type": "delta", "token": token}
        if reasoning:
            params["reasoning"] = reasoning
        await self._emit("chat.stream", params)

    async def chat_reasoning(self, content: str):
        await self._emit("chat.stream", {
            "type": "reasoning",
            "content": content,
        })

    async def chat_tool_call(self, tool_call: dict):
        await self._emit("chat.stream", {
            "type": "tool_call",
            "toolCall": tool_call,
        })

    async def chat_tool_result(self, tool_call_id: str, result: str, error: str | None = None):
        params: dict[str, Any] = {
            "type": "tool_result",
            "toolCallId": tool_call_id,
            "result": result,
        }
        if error:
            params["error"] = error
        await self._emit("chat.stream", params)

    async def chat_complete(self, message: dict, session_id: str, usage: dict | None = None):
        params: dict[str, Any] = {
            "type": "complete",
            "message": message,
            "sessionId": session_id,
        }
        if usage:
            params["usage"] = usage
        await self._emit("chat.stream", params)

    async def chat_error(self, code: str, message: str):
        await self._emit("chat.stream", {
            "type": "error",
            "code": code,
            "message": message,
        })

    async def session_changed(self, session: dict | None):
        await self._emit("session.changed", {"session": session})

    async def tool_progress(self, tool: str, progress: float, message: str | None = None):
        params: dict[str, Any] = {
            "type": "tool.progress",
            "tool": tool,
            "progress": progress,
        }
        if message:
            params["message"] = message
        await self._emit("tool.progress", params)

    async def approval_request(
        self,
        approval_id: str,
        tool: str,
        arguments: dict,
        message: str,
        options: list[str] | None = None,
        default_option: str = "allow",
        timeout: int = 120,
    ):
        await self._emit("approval_request", {
            "id": approval_id,
            "tool": tool,
            "arguments": arguments,
            "message": message,
            "options": options or ["allow", "allow_once", "reject", "reject_forever"],
            "defaultOption": default_option,
            "timeout": timeout,
        })
