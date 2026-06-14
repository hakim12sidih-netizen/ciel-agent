"""
CIEL v1.0 — MCP Server v2.

Serveur MCP (Model Context Protocol) exposant les outils CIEL
via le gateway et les modules natifs.

Protocol: JSON-RPC 2.0 sur stdio (transport MCP standard).
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any

from ciel.gateway import GatewayServer, get_gateway
from ciel.sandbox import detect_best_backend
from ciel.skills import SkillManager
from ciel.memory.fts5 import FTS5Memory

log = logging.getLogger("ciel.mcp")

MCP_VERSION = "2025-03-26"
SERVER_INFO = {"name": "ciel-mcp", "version": "1.0.0"}


class MCPServer:
    def __init__(self, gateway: GatewayServer | None = None):
        self.gateway = gateway or get_gateway()
        self._running = False
        self._request_id = 0

    def _rpc_result(self, msg_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _rpc_error(self, msg_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

    def _send(self, msg: dict) -> None:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()

    def _read(self) -> str:
        return sys.stdin.readline()

    def _handle_initialize(self, msg_id: Any, params: dict) -> dict:
        return self._rpc_result(msg_id, {
            "protocolVersion": MCP_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
            },
        })

    def _handle_list_tools(self, msg_id: Any) -> dict:
        tools = [
            {
                "name": "ciel_chat",
                "description": "Chat avec l'agent CIEL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message à envoyer"},
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "ciel_health",
                "description": "État de santé de CIEL",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "ciel_memory_search",
                "description": "Recherche full-text dans la mémoire CIEL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Requête de recherche"},
                        "limit": {"type": "integer", "description": "Nombre de résultats"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "ciel_code_execute",
                "description": "Exécute du code dans un sandbox isolé",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code à exécuter"},
                        "language": {"type": "string", "description": "Langage (python, bash, js, go, rust)"},
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "ciel_gateway_status",
                "description": "État du gateway multi-plateforme",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "ciel_skills_list",
                "description": "Liste les skills disponibles",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "ciel_workspace_exec",
                "description": "Exécute du code dans un workspace isolé",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace_id": {"type": "string", "description": "ID du workspace"},
                        "code": {"type": "string", "description": "Code à exécuter"},
                        "language": {"type": "string", "description": "Langage"},
                    },
                    "required": ["workspace_id", "code"],
                },
            },
        ]
        return self._rpc_result(msg_id, {"tools": tools})

    def _handle_call_tool(self, msg_id: Any, params: dict) -> dict:
        name = params.get("name", "")
        args = params.get("arguments", {})

        handlers = {
            "ciel_chat": self._tool_chat,
            "ciel_health": self._tool_health,
            "ciel_memory_search": self._tool_memory_search,
            "ciel_code_execute": self._tool_code_execute,
            "ciel_gateway_status": self._tool_gateway_status,
            "ciel_skills_list": self._tool_skills_list,
            "ciel_workspace_exec": self._tool_workspace_exec,
        }

        handler = handlers.get(name)
        if handler:
            try:
                result = handler(**args)
                return self._rpc_result(msg_id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                })
            except Exception as e:
                return self._rpc_result(msg_id, {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                })

        return self._rpc_error(msg_id, -32601, f"Unknown tool: {name}")

    def _tool_chat(self, message: str = "", **kwargs: Any) -> dict:
        from ciel.llmbridge.core import LLMBridgeEngine
        engine = LLMBridgeEngine()
        response = engine.chat(message)
        return {"response": str(response) if response else "No response"}

    def _tool_health(self, **kwargs: Any) -> dict:
        st = self.gateway.status()
        return {
            "running": st["running"],
            "channels": len(st["channels"]),
            "uptime_s": st["uptime_s"],
        }

    def _tool_memory_search(self, query: str = "", limit: int = 10, **kwargs: Any) -> dict:
        memory = FTS5Memory()
        results = memory.search(query, limit)
        return {
            "query": query,
            "results": [r.to_dict() for r in results],
            "count": len(results),
        }

    def _tool_code_execute(self, code: str = "", language: str = "python", **kwargs: Any) -> dict:
        from ciel.sandbox import SandboxEngine
        sbx = SandboxEngine()
        result = sbx.execute(code, language)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "error": result.error,
        }

    def _tool_gateway_status(self, **kwargs: Any) -> dict:
        return self.gateway.status()

    def _tool_skills_list(self, **kwargs: Any) -> dict:
        sm = SkillManager()
        return {"skills": [s.to_dict() for s in sm.list()]}

    def _tool_workspace_exec(self, workspace_id: str = "", code: str = "",
                              language: str = "python", **kwargs: Any) -> dict:
        from ciel.workspace import WorkspaceManager
        wm = WorkspaceManager()
        result = wm.execute(workspace_id, code, language)
        return result

    def _dispatch(self, msg: dict) -> dict | None:
        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            return self._handle_initialize(msg_id, params)
        if method == "tools/list":
            return self._handle_list_tools(msg_id)
        if method == "tools/call":
            return self._handle_call_tool(msg_id, params)
        if method == "ping":
            return self._rpc_result(msg_id, {})
        return self._rpc_error(msg_id, -32601, f"Method not found: {method}")

    def serve_stdio(self) -> None:
        self._running = True
        log.info("MCP server started on stdio")

        # Send initialize notification
        self._send({"jsonrpc": "2.0", "method": "initialized", "params": {}})

        while self._running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    resp = self._dispatch(msg)
                    if resp is not None:
                        self._send(resp)
                except json.JSONDecodeError:
                    self._send(self._rpc_error(None, -32700, "Parse error"))
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception:
                log.exception("MCP dispatch error")

    def stop(self) -> None:
        self._running = False


def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    server = MCPServer()
    server.serve_stdio()


if __name__ == "__main__":
    main()
