from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable

import httpx
import websockets

from .protocol import (
    ACP_PROTOCOL_VERSION, ACP_SERVER_INFO, ACP_CAPABILITIES,
    ACPTool, ACPResource, ACPPrompt, ACPAgent,
    ACPScope, REQUESTS_TO_CATCH_UP,
)
from .tools import get_all_tools, TOOL_HANDLERS
from .resources import get_all_resources, RESOURCE_HANDLERS

log = logging.getLogger("ciel.acp")

API_HOST = os.environ.get("CIEL_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("CIEL_PORT", "8765"))
API_BASE = f"http://{API_HOST}:{API_PORT}/v1"

_available_tools: list[ACPTool] = get_all_tools()
_available_resources: list[ACPResource] = get_all_resources()


class ACPServer:
    def __init__(self, host: str = "127.0.0.1", ws_port: int = 9876):
        self.host = host
        self.ws_port = ws_port
        self._ws_server: websockets.WebSocketServer | None = None
        self._sessions: dict[str, dict] = {}
        self._diagnostics_store: dict[str, list[dict]] = {}
        self._running = False
        self._tool_handlers: dict[str, Callable] = dict(TOOL_HANDLERS)
        self._resource_handlers: dict[str, Callable] = dict(RESOURCE_HANDLERS)

    # ── Lifecycle ──

    async def start(self) -> bool:
        self._ws_server = await websockets.serve(
            self._handle_ws, self.host, self.ws_port,
            ping_interval=30, ping_timeout=10,
        )
        self._running = True
        log.info("ACP WebSocket server on ws://%s:%d", self.host, self.ws_port)
        return True

    async def stop(self) -> None:
        self._running = False
        if self._ws_server:
            self._ws_server.close()
            await self._ws_server.wait_closed()
            self._ws_server = None

    def register_tool_handler(self, tool_name: str, handler: Callable) -> None:
        self._tool_handlers[tool_name] = handler

    def register_resource_handler(self, uri: str, handler: Callable) -> None:
        self._resource_handlers[uri] = handler

    # ── WebSocket Transport ──

    async def _handle_ws(self, websocket):
        session_id = f"ws-{uuid.uuid4().hex[:12]}"
        self._sessions[session_id] = {"id": session_id, "connected_at": time.time()}
        log.info("ACP WS session: %s", session_id)
        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                    resp = await self._dispatch(msg)
                    if resp is not None:
                        await websocket.send(json.dumps(resp))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    }))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._sessions.pop(session_id, None)

    # ── stdio Transport ──

    async def serve_stdio(self):
        self._running = True
        log.info("ACP stdio transport started")
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(
            lambda: protocol, sys.stdin)

        while self._running:
            try:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                for line in chunk.decode("utf-8").strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        resp = await self._dispatch(msg)
                        if resp is not None:
                            sys.stdout.write(json.dumps(resp) + "\n")
                            sys.stdout.flush()
                    except json.JSONDecodeError:
                        sys.stdout.write(json.dumps({
                            "jsonrpc": "2.0", "id": None,
                            "error": {"code": -32700, "message": "Parse error"},
                        }) + "\n")
                        sys.stdout.flush()
            except Exception:
                break

    # ── Dispatch ──

    async def _dispatch(self, msg: dict) -> dict | None:
        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        # Notifications
        if msg_id is None and method:
            await self._handle_notification(method, params)
            return None

        if method == "initialize":
            return self._rpc_result(msg_id, {
                "protocolVersion": ACP_PROTOCOL_VERSION,
                "serverInfo": ACP_SERVER_INFO,
                "capabilities": ACP_CAPABILITIES,
            })

        if method == "ping":
            return self._rpc_result(msg_id, {})

        if method == "acp/tools/list":
            tools = [t.to_dict() for t in _available_tools]
            return self._rpc_result(msg_id, {"tools": tools})

        if method == "acp/tools/call":
            return await self._handle_tool_call(msg_id, params)

        if method == "acp/resources/list":
            resources = [r.to_dict() for r in _available_resources]
            return self._rpc_result(msg_id, {"resources": resources})

        if method == "acp/resources/read":
            return await self._handle_resource_read(msg_id, params)

        if method == "acp/prompts/list":
            return self._rpc_result(msg_id, {"prompts": []})

        if method == "acp/agents/discover":
            return self._rpc_result(msg_id, {"agents": [{
                "agent_id": "ciel-main",
                "name": "CIEL",
                "description": "Agent CIEL principal",
                "capabilities": ["llm", "memory", "web", "code", "workflow"],
                "tools": [t.name for t in _available_tools],
            }]})

        if method == "acp/code/diagnostics":
            return await self._handle_diagnostics(msg_id, params)

        if method == "acp/code/suggest":
            return await self._handle_suggest(msg_id, params)

        return self._rpc_error(msg_id, -32601, f"Method not found: {method}")

    async def _handle_notification(self, method: str, params: dict) -> None:
        if method == "notifications/initialized":
            log.debug("Client initialized")
        elif method == "acp/diagnostics/update":
            file_path = params.get("file_path", "")
            diags = params.get("diagnostics", [])
            if file_path:
                self._diagnostics_store[file_path] = diags

    async def _handle_tool_call(self, msg_id: Any, params: dict) -> dict:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handler = self._tool_handlers.get(tool_name)
        if handler:
            try:
                result = handler(**arguments)
                content = [{"type": "text", "text": json.dumps(result, indent=2)}]
                return self._rpc_result(msg_id, {
                    "content": content, "isError": not result.get("success", True),
                })
            except Exception as e:
                return self._rpc_result(msg_id, {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                })

        # Fallback: proxy to CIEL REST API
        return await self._proxy_to_ciel(tool_name, arguments, msg_id)

    async def _handle_resource_read(self, msg_id: Any, params: dict) -> dict:
        uri = params.get("uri", "")
        handler = self._resource_handlers.get(uri)
        if handler:
            try:
                result = handler()
                text = json.dumps(result, indent=2)
                content = [{"type": "text", "text": text}]
                return self._rpc_result(msg_id, {"contents": [
                    {"uri": uri, "mimeType": "application/json", "text": text},
                ]})
            except Exception as e:
                return self._rpc_error(msg_id, -32603, str(e))
        return self._rpc_error(msg_id, -32602, f"Resource not found: {uri}")

    async def _handle_diagnostics(self, msg_id: Any, params: dict) -> dict:
        file_path = params.get("file_path", "")
        if file_path in self._diagnostics_store:
            return self._rpc_result(msg_id, {
                "diagnostics": self._diagnostics_store[file_path],
            })
        return self._rpc_result(msg_id, {"diagnostics": []})

    async def _handle_suggest(self, msg_id: Any, params: dict) -> dict:
        file_path = params.get("file_path", "")
        focus = params.get("focus", "general")
        if not file_path:
            return self._rpc_error(msg_id, -32602, "file_path required")
        p = Path(file_path)
        if not p.exists():
            return self._rpc_error(msg_id, -32602, "File not found")
        content = p.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")
        suggestions = []
        for i, line in enumerate(lines, 1):
            text = line.strip()
            if not text:
                continue
            if len(text) > 200 and focus in ("general", "performance"):
                suggestions.append({
                    "line": i,
                    "type": "warning",
                    "message": f"Ligne trop longue ({len(text)} caractères)",
                    "suggestion": "Envisager de scinder en plusieurs lignes",
                })
            if text.endswith(("    ", "\t")) and focus in ("general", "style"):
                suggestions.append({
                    "line": i,
                    "type": "info",
                    "message": "Espace(s) en fin de ligne",
                    "suggestion": "Supprimer les espaces superflus",
                })
        return self._rpc_result(msg_id, {"suggestions": suggestions[:20]})

    async def _proxy_to_ciel(self, tool_name: str, arguments: dict,
                              msg_id: Any) -> dict:
        api_map = {
            "ciel_health": ("GET", "/health"),
            "ciel_chat": ("POST", "/llm/chat"),
            "ciel_memory_store": ("POST", "/memory/store"),
            "ciel_memory_query": ("GET", "/memory/query"),
            "ciel_web_search": ("GET", "/web/search"),
            "ciel_brain_status": ("GET", "/brain/status"),
            "ciel_workflows": ("GET", "/workflow/list"),
            "ciel_agent_execute": ("POST", "/agent/execute"),
            "ciel_providers": ("GET", "/llm/providers"),
        }
        entry = api_map.get(tool_name)
        if not entry:
            return self._rpc_error(msg_id, -32601, f"Unknown tool: {tool_name}")

        method, path = entry
        url = f"{API_BASE}{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if method == "GET":
                    resp = await client.get(url, params=arguments)
                else:
                    resp = await client.post(url, json=arguments)
                data = resp.json()
                text = json.dumps(data, indent=2)
                return self._rpc_result(msg_id, {
                    "content": [{"type": "text", "text": text}],
                    "isError": not resp.is_success,
                })
        except Exception as e:
            return self._rpc_result(msg_id, {
                "content": [{"type": "text", "text": f"CIEL API error: {e}"}],
                "isError": True,
            })

    # ── Helpers ──

    def _rpc_result(self, msg_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _rpc_error(self, msg_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id,
                "error": {"code": code, "message": message}}

    # ── Stats ──

    def get_stats(self) -> dict:
        return {
            "running": self._running,
            "ws_port": self.ws_port,
            "sessions": len(self._sessions),
            "tools": len(_available_tools),
            "resources": len(_available_resources),
        }
