"""
Stdio transport for JSON-RPC 2.0.
Reads newline-delimited JSON from stdin, writes to stdout.
Uses asyncio's connect_read_pipe for non-blocking reads.
"""

import asyncio
import json
import sys
from typing import Callable


class StdioTransport:
    """
    Handles low-level stdio communication.
    Writes JSON-RPC messages as newline-delimited JSON to stdout.
    """

    async def send(self, message: str):
        """Write a message to stdout (newline-terminated)."""
        data = (message + "\n").encode("utf-8")
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()

    async def send_event(self, method: str, params: dict | None = None):
        """Send a JSON-RPC 2.0 notification (event)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }
        await self.send(json.dumps(notification, default=str))

    def create_reader(self, on_message: Callable[[dict], None]) -> asyncio.Task:
        """
        Create an asyncio task that reads lines from stdin.
        Calls on_message for each parsed JSON-RPC message.
        """
        return asyncio.create_task(self._read_loop(on_message))

    async def _read_loop(self, on_message: Callable[[dict], None]):
        """Read lines from stdin in a loop."""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                raw = line.decode("utf-8", errors="replace").strip()
                if not raw:
                    continue

                msg = json.loads(raw)
                on_message(msg)

            except (EOFError, ConnectionResetError):
                break
            except json.JSONDecodeError:
                continue
