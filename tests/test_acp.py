from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ciel.acp.protocol import (
    ACPTool, ACPResource, ACPPrompt, ACPAgent,
    ACPScope, ACP_PROTOCOL_VERSION,
)
from ciel.acp.tools import (
    get_all_tools, get_tools_by_category,
    CODE_TOOLS, CIEL_TOOLS, TOOL_HANDLERS,
    handle_analyze_code, handle_search_code,
    handle_read_file, handle_write_file,
    handle_list_directory, handle_run_command,
)
from ciel.acp.resources import get_all_resources, RESOURCE_HANDLERS
from ciel.acp.server import ACPServer
from ciel.acp.ide import (
    generate_vscode_extension, generate_cursor_rules,
    VSCODE_EXTENSION_MANIFEST, CURSOR_RULES,
)


# ═══════════════════════════════════════════════════════════
# Protocol Types
# ═══════════════════════════════════════════════════════════

class TestProtocolTypes:
    def test_tool_to_dict(self):
        tool = ACPTool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            scope=ACPScope.ADMIN,
            categories=["test"],
        )
        d = tool.to_dict()
        assert d["name"] == "test_tool"
        assert d["scope"] == "admin"
        assert d["categories"] == ["test"]

    def test_tool_default_scope(self):
        tool = ACPTool(name="t", description="d", input_schema={})
        assert tool.scope == ACPScope.PUBLIC

    def test_resource_to_dict(self):
        r = ACPResource(
            uri="test://resource",
            name="Test Resource",
            description="A test resource",
            mime_type="text/plain",
        )
        d = r.to_dict()
        assert d["uri"] == "test://resource"
        assert d["mimeType"] == "text/plain"

    def test_prompt_to_dict(self):
        p = ACPPrompt(
            name="test_prompt",
            description="A test prompt",
            arguments=[{"name": "input", "type": "string"}],
        )
        d = p.to_dict()
        assert d["name"] == "test_prompt"
        assert len(d["arguments"]) == 1

    def test_agent_to_dict(self):
        a = ACPAgent(
            agent_id="agent-1",
            name="Agent 1",
            capabilities=["llm", "code"],
            tools=["analyze_code"],
        )
        d = a.to_dict()
        assert d["agent_id"] == "agent-1"
        assert len(d["tools"]) == 1

    def test_protocol_version(self):
        assert ACP_PROTOCOL_VERSION == "2026-06-14"


# ═══════════════════════════════════════════════════════════
# Tools
# ═══════════════════════════════════════════════════════════

class TestTools:
    def test_get_all_tools_contains_code_and_ciel(self):
        tools = get_all_tools()
        names = [t.name for t in tools]
        assert "analyze_code" in names
        assert "ciel_chat" in names
        assert "read_file" in names
        assert len(tools) == len(CODE_TOOLS) + len(CIEL_TOOLS)

    def test_get_tools_by_category(self):
        code_tools = get_tools_by_category("code")
        assert len(code_tools) >= 5
        ciel_tools = get_tools_by_category("ciel")
        assert len(ciel_tools) >= 3

    def test_tool_has_valid_schema(self):
        for tool in get_all_tools():
            assert tool.name
            assert tool.description
            assert tool.input_schema["type"] == "object"
            assert "properties" in tool.input_schema

    def test_code_tools_have_required_fields(self):
        for tool in CODE_TOOLS:
            assert "file_path" in str(tool.input_schema) or \
                   "pattern" in str(tool.input_schema) or \
                   "command" in str(tool.input_schema) or \
                   "path" in str(tool.input_schema)

    def test_tool_handlers_registered(self):
        assert "analyze_code" in TOOL_HANDLERS
        assert "search_code" in TOOL_HANDLERS
        assert "read_file" in TOOL_HANDLERS
        assert "write_file" in TOOL_HANDLERS
        assert "list_directory" in TOOL_HANDLERS
        assert "run_command" in TOOL_HANDLERS


class TestToolHandlers:
    def test_analyze_code_nonexistent_file(self):
        result = handle_analyze_code(file_path="/nonexistent/file.py")
        assert result["success"] is False

    def test_analyze_code_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\n\n\ndef hello():\n    pass\n")
            f.flush()
            result = handle_analyze_code(file_path=f.name)
            assert result["success"] is True
            assert result["language"] == "py"
            assert result["lines"] >= 4
            os.unlink(f.name)

    def test_analyze_code_long_line(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = " + "a" * 250 + "\n")
            f.flush()
            result = handle_analyze_code(file_path=f.name)
            assert len(result["issues"]) >= 1
            assert any("long" in i["message"].lower() for i in result["issues"])
            os.unlink(f.name)

    def test_read_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            f.flush()
            result = handle_read_file(file_path=f.name, offset=2, limit=3)
            assert result["success"] is True
            assert result["offset"] == 2
            content_lines = result["content"].split("\n")
            assert len(content_lines) >= 3
            os.unlink(f.name)

    def test_read_file_nonexistent(self):
        result = handle_read_file(file_path="/nonexistent")
        assert result["success"] is False

    def test_write_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.txt"
            result = handle_write_file(file_path=str(path), content="hello")
            assert result["success"] is True
            assert path.read_text() == "hello"

    def test_list_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "file1.txt").write_text("a")
            Path(tmp, "file2.txt").write_text("b")
            Path(tmp, "subdir").mkdir()
            result = handle_list_directory(path=tmp)
            assert result["success"] is True
            assert result["count"] == 3

    def test_list_directory_nonexistent(self):
        result = handle_list_directory(path="/nonexistent")
        assert result["success"] is False

    def test_run_command(self):
        result = handle_run_command(command="echo hello")
        assert result["success"] is True
        assert "hello" in result["stdout"]

    def test_run_command_failure(self):
        result = handle_run_command(command="false")
        assert result["success"] is False

    def test_search_code_no_ripgrep(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = handle_search_code(pattern="test")
            assert result["success"] is False
            assert "ripgrep" in result["error"]


# ═══════════════════════════════════════════════════════════
# Resources
# ═══════════════════════════════════════════════════════════

class TestResources:
    def test_get_all_resources(self):
        resources = get_all_resources()
        uris = [r.uri for r in resources]
        assert "project://structure" in uris
        assert "ciel://status" in uris
        assert len(resources) >= 3

    def test_resource_handlers(self):
        assert "project://structure" in RESOURCE_HANDLERS
        assert "ciel://status" in RESOURCE_HANDLERS


# ═══════════════════════════════════════════════════════════
# ACP Server
# ═══════════════════════════════════════════════════════════

class TestACPServer:
    def _dispatch(self, server, msg):
        return asyncio.run(server._dispatch(msg))
    def test_init(self):
        server = ACPServer(host="127.0.0.1", ws_port=9876)
        assert server.host == "127.0.0.1"
        assert server.ws_port == 9876
        assert not server._running

    def test_rpc_result(self):
        server = ACPServer()
        resp = server._rpc_result(1, {"status": "ok"})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 1
        assert resp["result"]["status"] == "ok"

    def test_rpc_error(self):
        server = ACPServer()
        resp = server._rpc_error(1, -32601, "Method not found")
        assert resp["error"]["code"] == -32601
        assert resp["error"]["message"] == "Method not found"

    def test_register_tool_handler(self):
        server = ACPServer()
        handler = MagicMock()
        server.register_tool_handler("custom_tool", handler)
        assert "custom_tool" in server._tool_handlers

    def test_register_resource_handler(self):
        server = ACPServer()
        handler = MagicMock()
        server.register_resource_handler("custom://resource", handler)
        assert "custom://resource" in server._resource_handlers

    def test_dispatch_initialize(self):
        server = ACPServer()
        resp = self._dispatch(server, {"id": 1, "method": "initialize", "params": {}})
        assert resp["result"]["protocolVersion"] == ACP_PROTOCOL_VERSION
        assert "tools" in resp["result"]["capabilities"]

    def test_dispatch_ping(self):
        server = ACPServer()
        resp = self._dispatch(server, {"id": 1, "method": "ping", "params": {}})
        assert resp["result"] == {}

    def test_dispatch_tools_list(self):
        server = ACPServer()
        resp = self._dispatch(server, {"id": 1, "method": "acp/tools/list", "params": {}})
        assert "tools" in resp["result"]
        assert len(resp["result"]["tools"]) > 0

    def test_dispatch_resources_list(self):
        server = ACPServer()
        resp = self._dispatch(server, {"id": 1, "method": "acp/resources/list", "params": {}})
        assert "resources" in resp["result"]
        assert len(resp["result"]["resources"]) > 0

    def test_dispatch_agents_discover(self):
        server = ACPServer()
        resp = self._dispatch(server, {"id": 1, "method": "acp/agents/discover", "params": {}})
        assert "ciel-main" in [a["agent_id"] for a in resp["result"]["agents"]]

    def test_dispatch_unknown_method(self):
        server = ACPServer()
        resp = self._dispatch(server, {"id": 1, "method": "nonexistent", "params": {}})
        assert resp["error"]["code"] == -32601

    def test_dispatch_notification(self):
        server = ACPServer()
        resp = self._dispatch(server, {"method": "notifications/initialized", "params": {}})
        assert resp is None

    def test_tool_call_analyze_code(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            server = ACPServer()
            resp = self._dispatch(server, {
                "id": 1,
                "method": "acp/tools/call",
                "params": {"name": "analyze_code", "arguments": {"file_path": f.name}},
            })
            assert "content" in resp["result"]
            os.unlink(f.name)

    def test_tool_call_unknown_tool(self):
        server = ACPServer()
        resp = self._dispatch(server, {
            "id": 1,
            "method": "acp/tools/call",
            "params": {"name": "ciel_health", "arguments": {}},
        })
        # Falls back to CIEL API proxy, which will fail since server not running
        assert "content" in resp["result"]

    def test_diagnostics_update(self):
        server = ACPServer()
        self._dispatch(server, {
            "method": "acp/diagnostics/update",
            "params": {"file_path": "/test.py", "diagnostics": [{"line": 1, "msg": "error"}]},
        })
        assert "/test.py" in server._diagnostics_store
        assert len(server._diagnostics_store["/test.py"]) == 1

    def test_get_diagnostics(self):
        server = ACPServer()
        server._diagnostics_store["/test.py"] = [{"line": 1, "msg": "error"}]
        resp = self._dispatch(server, {
            "id": 1,
            "method": "acp/code/diagnostics",
            "params": {"file_path": "/test.py"},
        })
        assert len(resp["result"]["diagnostics"]) == 1

    def test_code_suggest(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = " + "a" * 250 + "\n")
            f.flush()
            server = ACPServer()
            resp = self._dispatch(server, {
                "id": 1,
                "method": "acp/code/suggest",
                "params": {"file_path": f.name},
            })
            assert len(resp["result"]["suggestions"]) >= 1
            os.unlink(f.name)

    def test_get_stats(self):
        server = ACPServer()
        stats = server.get_stats()
        assert stats["running"] is False
        assert stats["tools"] > 0
        assert stats["resources"] > 0


# ═══════════════════════════════════════════════════════════
# IDE Integration
# ═══════════════════════════════════════════════════════════

class TestIDEIntegration:
    def test_vscode_manifest(self):
        assert VSCODE_EXTENSION_MANIFEST["name"] == "ciel-acp"
        assert len(VSCODE_EXTENSION_MANIFEST["contributes"]["commands"]) == 5
        assert "ciel.openChat" in [c["command"] for c in VSCODE_EXTENSION_MANIFEST["contributes"]["commands"]]

    def test_generate_vscode_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = generate_vscode_extension(tmp)
            assert "package.json" in files
            assert "src/extension.ts" in files
            assert "src/acpClient.ts" in files
            assert "src/panel.ts" in files
            assert Path(tmp, "package.json").exists()
            assert Path(tmp, "src", "extension.ts").exists()

    def test_cursor_rules_non_empty(self):
        assert len(CURSOR_RULES) > 100
        assert "analyze_code" in CURSOR_RULES
        assert "search_code" in CURSOR_RULES

    def test_generate_cursor_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_cursor_rules(tmp)
            assert Path(tmp, ".cursorrules").exists()
            assert Path(tmp, ".cursor", "rules", "ciel-agent.mdc").exists()

    def test_vscode_panel_html(self):
        from ciel.acp.ide import VSCODE_PANEL_SRC
        assert "CIEL Chat" in VSCODE_PANEL_SRC
        assert "acquireVsCodeApi" in VSCODE_PANEL_SRC

    def test_vscode_acp_client(self):
        from ciel.acp.ide import VSCODE_ACP_CLIENT_SRC
        assert "class ACPClient" in VSCODE_ACP_CLIENT_SRC
        assert "callTool" in VSCODE_ACP_CLIENT_SRC


# ═══════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_get_tools_by_category_empty(self):
        tools = get_tools_by_category("nonexistent")
        assert tools == []

    def test_tool_empty_scope_defaults(self):
        t = ACPTool(name="n", description="d", input_schema={})
        assert t.scope == ACPScope.PUBLIC

    def test_server_init_defaults(self):
        server = ACPServer()
        assert server.host == "127.0.0.1"
        assert server.ws_port == 9876
        assert server._sessions == {}
        assert server._diagnostics_store == {}
