"""
CIEL TUI Gateway Server
JSON-RPC 2.0 over stdio — bridges Ink TUI to CIEL backend.
"""

import asyncio
import inspect
import json
import traceback
from typing import Any

from ciel.interfaces.tui.gateway.transport import StdioTransport
from ciel.interfaces.tui.gateway.methods.chat import ChatMethods
from ciel.interfaces.tui.gateway.methods.sessions import SessionMethods
from ciel.interfaces.tui.gateway.methods.tools import ToolMethods
from ciel.interfaces.tui.gateway.methods.completions import CompletionMethods
from ciel.interfaces.tui.gateway.methods.config import ConfigMethods
from ciel.interfaces.tui.gateway.events.emitter import GatewayEventEmitter

VERSION = "0.1.0"


class GatewayServer:
    """
    JSON-RPC 2.0 server over stdio transport.
    Routes method calls to handlers and emits events back to the TUI.
    """

    def __init__(self):
        self.transport = StdioTransport()
        self.emitter = GatewayEventEmitter(self.transport)
        self._methods: dict[str, Any] = {}
        self._running = False

    async def start(self):
        """Initialize gateway and send ready event to TUI."""
        self._running = True

        # Register method handlers
        chat = ChatMethods(self)
        sessions = SessionMethods(self)
        tools = ToolMethods(self)
        completions = CompletionMethods(self)
        config = ConfigMethods(self)

        self._methods.update(chat.get_methods())
        self._methods.update(sessions.get_methods())
        self._methods.update(tools.get_methods())
        self._methods.update(completions.get_methods())
        self._methods.update(config.get_methods())

        # Send gateway.ready event
        await self.emitter.ready(
            version=VERSION,
            capabilities=list(self._methods.keys()),
        )

        # Start reading stdin
        reader_task = self.transport.create_reader(self._on_message)
        await reader_task

    def _on_message(self, msg: dict):
        """Handle a parsed JSON-RPC message."""
        asyncio.create_task(self._dispatch(msg))

    async def _dispatch(self, msg: dict):
        """Parse and dispatch a single JSON-RPC message."""
        msg_id = msg.get("id")
        method_name = msg.get("method")
        params = msg.get("params", {})

        if not method_name:
            await self._send_error(msg_id, -32600, "Invalid Request: no method")
            return

        # Notification (no id) — just log, no response
        if msg_id is None:
            return

        handler = self._methods.get(method_name)
        if handler is None:
            await self._send_error(msg_id, -32601, f"Method not found: {method_name}")
            return

        try:
            if inspect.iscoroutinefunction(handler):
                result = await handler(params)
            else:
                result = handler(params)

            # Streaming methods handle their own response
            if params.get("stream") and isinstance(result, type(None)):
                return

            await self._send_result(msg_id, result)

        except json.JSONDecodeError as e:
            await self._send_error(msg_id, -32700, f"Parse error: {e}")
        except Exception as e:
            traceback.print_exc()
            await self._send_error(
                msg_id, -32603, f"Internal error: {e}",
                data={"traceback": traceback.format_exc()},
            )

    async def _send_result(self, msg_id: Any, result: Any):
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
        }
        await self.transport.send(json.dumps(response))

    async def _send_error(self, msg_id: Any, code: int, message: str, data=None):
        error = {"code": code, "message": message}
        if data:
            error["data"] = data

        response = {
            "jsonrpc": "2.0",
            "id": msg_id if msg_id is not None else None,
            "error": error,
        }
        await self.transport.send(json.dumps(response))

    def stop(self):
        self._running = False


async def main():
    server = GatewayServer()
    try:
        await server.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


if __name__ == "__main__":
    asyncio.run(main())
