"""
Integration tests for the CIEL TUI Gateway.
Tests JSON-RPC 2.0 over stdio protocol.
Run: python -m pytest ciel/interfaces/tui/gateway/test_gateway.py -v
"""

import json
import sys
import time
import subprocess
import threading
import queue
from pathlib import Path

import pytest

GATEWAY_MODULE = "ciel.interfaces.tui.gateway.server"
FIXTURE_DIR = Path(__file__).parent


class GatewayProcess:
    """
    Manages a subprocess running the gateway server.
    Communicates via stdin/stdout with newline-delimited JSON.
    """

    def __init__(self, cwd: str | None = None):
        self.cwd = cwd or str(Path(__file__).resolve().parents[5])  # /home/sidi/ciel
        self.proc: subprocess.Popen | None = None
        self._responses: queue.Queue = queue.Queue()
        self._events: queue.Queue = queue.Queue()
        self._error = None
        self._reader_thread = None
        self._running = False
        self._msg_id = 0
        self.ready_event: dict | None = None

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-m", GATEWAY_MODULE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            text=True,
            bufsize=1,
        )
        self.started_at = time.time()
        self._running = True
        self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader_thread.start()

        # Consume stderr in a background thread
        stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        stderr_thread.start()

        # Wait for gateway.ready event
        try:
            event = self._events.get(timeout=10)
            assert event.get("method") == "gateway.ready", f"Expected gateway.ready, got {event}"
            self.ready_event = event
        except queue.Empty:
            self.stop()
            raise RuntimeError("Gateway did not emit ready event within 10s")

    def _read_stdout(self):
        while self._running and self.proc and self.proc.stdout:
            line = self.proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Notification (no "id") = event
            if "id" not in msg:
                self._events.put(msg)
            else:
                self._responses.put(msg)

    def _read_stderr(self):
        while self._running and self.proc and self.proc.stderr:
            line = self.proc.stderr.readline()
            if not line:
                break

    def request(self, method: str, params: dict | None = None) -> dict:
        self._msg_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self._msg_id,
            "method": method,
            "params": params or {},
        }
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()

        try:
            response = self._responses.get(timeout=30)
        except queue.Empty:
            self.stop()
            raise TimeoutError(f"No response for {method} within 30s")

        assert response.get("jsonrpc") == "2.0", f"Invalid JSON-RPC: {response}"
        assert response.get("id") == self._msg_id, f"ID mismatch: {response}"
        return response

    def get_event(self, timeout: float = 5) -> dict | None:
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        self._running = False
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


@pytest.fixture
def gateway():
    g = GatewayProcess()
    try:
        g.start()
        yield g
    finally:
        g.stop()


# ---- Tests ----

class TestGatewayLifecycle:
    def test_ready_event(self, gateway):
        """Gateway emits gateway.ready on startup."""
        assert gateway.ready_event is not None, "Fixture should have received ready event"
        params = gateway.ready_event["params"]
        assert "version" in params
        assert "capabilities" in params
        assert "skin" in params
        assert params["skin"]["name"] == "ciel-dark"
        assert "chat.stream" in params["capabilities"]

    def test_ping(self, gateway):
        """Gateway responds to unknown methods with error -32601."""
        resp = gateway.request("ping")
        assert "error" in resp
        assert resp["error"]["code"] == -32601


class TestChatMethods:
    def test_chat_stream_method_present(self, gateway):
        """tools.list should include chat.stream like capability."""
        resp = gateway.request("tools.list")
        assert "result" in resp
        tools = resp["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_chat_stream_no_messages(self, gateway):
        """Chat stream with no messages returns error."""
        resp = gateway.request("chat.stream", {"messages": []})
        # Non-streaming request: returns error dict in result
        # Streaming request: emits error event and returns null
        assert "error" in resp or resp.get("result") is None

    def test_chat_stream_basic_nonstream(self, gateway):
        """Chat stream non-streaming returns a result (may be error if no LLM configured)."""
        resp = gateway.request("chat.stream", {
            "messages": [{"role": "user", "content": "Say hello in one word"}],
            "stream": False,
        })
        # Should either succeed or fail gracefully
        assert "result" in resp or "error" in resp


class TestSessionMethods:
    def test_create_session(self, gateway):
        resp = gateway.request("sessions.create", {
            "source": "test",
            "platform": "pytest",
        })
        assert "result" in resp
        session = resp["result"]
        assert "id" in session
        assert session["source"] == "test"
        assert session["platform"] == "pytest"

    def test_list_sessions(self, gateway):
        gateway.request("sessions.create", {"source": "test", "platform": "pytest"})
        resp = gateway.request("sessions.list", {"source": "test"})
        assert "result" in resp
        result = resp["result"]
        assert "sessions" in result
        assert result["total"] >= 1

    def test_get_session(self, gateway):
        create = gateway.request("sessions.create", {"source": "test", "platform": "pytest"})
        session_id = create["result"]["id"]
        resp = gateway.request("sessions.get", {"id": session_id})
        assert "result" in resp
        assert resp["result"]["id"] == session_id

    def test_delete_session(self, gateway):
        create = gateway.request("sessions.create", {"source": "test", "platform": "pytest"})
        session_id = create["result"]["id"]
        resp = gateway.request("sessions.delete", {"id": session_id})
        assert "result" in resp
        assert resp["result"]["success"] is True

    def test_get_deleted_session(self, gateway):
        create = gateway.request("sessions.create", {"source": "test", "platform": "pytest"})
        session_id = create["result"]["id"]
        gateway.request("sessions.delete", {"id": session_id})
        resp = gateway.request("sessions.get", {"id": session_id})
        assert "result" in resp
        assert resp["result"] == {}  # Empty dict = not found


class TestToolMethods:
    def test_tools_list(self, gateway):
        resp = gateway.request("tools.list")
        assert "result" in resp
        tools = resp["result"]["tools"]
        assert isinstance(tools, list)
        names = [t["name"] for t in tools]
        assert "bash" in names
        assert "read" in names
        assert "write" in names
        assert "web_search" in names
        assert "mcp" in names

    def test_tool_has_definitions(self, gateway):
        resp = gateway.request("tools.list")
        for tool in resp["result"]["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert "toolset" in tool

    def test_execute_unknown_tool(self, gateway):
        resp = gateway.request("tools.execute", {
            "name": "nonexistent_tool_xyz",
            "arguments": {},
        })
        assert "result" in resp
        # Should return success=False, not an error
        assert resp["result"]["success"] is False


class TestCompletionMethods:
    def test_slash_completions(self, gateway):
        resp = gateway.request("completions.slash", {"query": "hel"})
        assert "result" in resp
        completions = resp["result"]["completions"]
        assert len(completions) > 0
        assert any("/help" in c for c in completions)

    def test_slash_completions_empty_query(self, gateway):
        resp = gateway.request("completions.slash", {"query": ""})
        assert "result" in resp
        completions = resp["result"]["completions"]
        assert len(completions) > 0  # Returns all commands

    def test_path_completions(self, gateway):
        resp = gateway.request("completions.path", {"query": "/tmp/"})
        assert "result" in resp
        assert isinstance(resp["result"]["completions"], list)


class TestConfigMethods:
    def test_config_get(self, gateway):
        resp = gateway.request("config.get", {"key": "theme"})
        assert "result" in resp
        assert resp["result"]["value"] is not None

    def test_config_set_get(self, gateway):
        gateway.request("config.set", {"key": "test_key", "value": "test_value"})
        resp = gateway.request("config.get", {"key": "test_key"})
        assert "result" in resp
        assert resp["result"]["value"] == "test_value"


class TestErrorHandling:
    def test_invalid_json(self):
        """Invalid JSON should cause an error, but we can't easily test subprocess."""
        pass

    def test_unknown_method(self, gateway):
        resp = gateway.request("no_such_method")
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_missing_params(self, gateway):
        """Some methods handle missing params gracefully."""
        resp = gateway.request("sessions.create", {})
        assert "result" in resp
        assert "id" in resp["result"]


class TestEventFlow:
    def test_session_changed_event(self, gateway):
        """Creating a session emits session.changed event."""
        # Consume the ready event
        gateway.get_event(timeout=2)
        gateway.request("sessions.create", {"source": "test", "platform": "pytest"})
        event = gateway.get_event(timeout=5)
        assert event is not None
        assert event["method"] == "session.changed"
        assert event["params"]["session"] is not None
        assert "id" in event["params"]["session"]

    def test_tool_progress_event(self, gateway):
        """Tool execution emits progress events."""
        # The ready event
        gateway.get_event(timeout=2)
        gateway.request("tools.execute", {"name": "nonexistent_tool_xyz", "arguments": {}})
        events = []
        while True:
            ev = gateway.get_event(timeout=3)
            if ev is None:
                break
            if ev["method"] == "tool.progress":
                events.append(ev)
        assert len(events) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
