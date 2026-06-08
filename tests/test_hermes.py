from __future__ import annotations

import pytest

from ciel.hermes.core import HermesEngine
from ciel.hermes import HermesEngine as HermesEngineAlias


class TestHermesEngine:
    def test_init(self):
        eng = HermesEngine()
        assert eng.state is not None
        assert eng.get_stats()["messages_processed"] == 0

    def test_process_create_session(self):
        eng = HermesEngine()
        r = eng.process({"action": "create_session", "platform": "cli"})
        assert r["success"] is True
        assert "session_id" in r

    def test_process_send(self):
        eng = HermesEngine()
        sr = eng.process({"action": "create_session", "platform": "cli"})
        sid = sr["session_id"]
        r = eng.process({"action": "send", "session_id": sid, "content": "hello"})
        assert r["success"] is True
        assert r["message_id"] >= 0

    def test_process_history(self):
        eng = HermesEngine()
        sr = eng.process({"action": "create_session", "platform": "test"})
        sid = sr["session_id"]
        eng.process({"action": "send", "session_id": sid, "content": "msg1"})
        eng.process({"action": "send", "session_id": sid, "content": "msg2", "role": "assistant"})
        r = eng.process({"action": "history", "session_id": sid})
        assert r["success"] is True
        assert len(r["messages"]) == 2

    def test_process_sessions(self):
        eng = HermesEngine()
        eng.process({"action": "create_session", "platform": "cli"})
        eng.process({"action": "create_session", "platform": "telegram"})
        r = eng.process({"action": "sessions"})
        assert r["success"] is True
        assert len(r["sessions"]) == 2

    def test_process_close(self):
        eng = HermesEngine()
        sr = eng.process({"action": "create_session", "platform": "cli"})
        sid = sr["session_id"]
        r = eng.process({"action": "close", "session_id": sid})
        assert r["success"] is True

    def test_process_stats(self):
        eng = HermesEngine()
        r = eng.process({"action": "stats"})
        assert r["success"] is True
        assert "stats" in r

    def test_process_unknown_action(self):
        eng = HermesEngine()
        r = eng.process({"action": "nonexistent"})
        assert r["success"] is False
        assert "unknown action" in r["error"]

    def test_process_invalid_input(self):
        eng = HermesEngine()
        r = eng.process("not a dict")
        assert r["success"] is False

    def test_api_convenience(self):
        eng = HermesEngine()
        sid = eng.create_session("telegram", "chat_1")
        assert sid != ""
        eng.send_message(sid, "hi")
        msgs = eng.get_history(sid)
        assert len(msgs) == 1
        sessions = eng.list_sessions()
        assert len(sessions) > 0
        eng.close_session(sid)

    def test_module_export(self):
        assert HermesEngine is HermesEngineAlias


if __name__ == "__main__":
    pytest.main([__file__])
