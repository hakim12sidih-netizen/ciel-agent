from __future__ import annotations

import pytest

from ciel.messaging.core import MessagingEngine
from ciel.messaging import MessagingEngine as MessagingEngineAlias


class TestMessagingEngine:
    def test_init(self):
        eng = MessagingEngine()
        assert eng.gateway is not None
        assert eng.skills is not None

    def test_process_stats(self):
        eng = MessagingEngine()
        r = eng.process({"action": "stats"})
        assert r["success"] is True
        assert "stats" in r

    def test_process_execute(self):
        eng = MessagingEngine()

        def dummy(ctx):
            return {"done": True, "ctx": ctx}

        eng.register_skill("test_skill", dummy, "dummy skill")
        r = eng.process({"action": "execute", "skill": "test_skill", "context": {"x": 1}})
        assert r["success"] is True
        assert r["result"]["done"] is True

    def test_execute_missing_skill(self):
        eng = MessagingEngine()
        result = eng.execute_skill("nonexistent")
        assert "error" in result

    def test_register_channel(self):
        from ciel.messaging.channels.base import ChannelAdapter, ChannelConfig, ChannelMessage

        class DummyAdapter(ChannelAdapter):
            async def start(self):
                pass
            async def stop(self):
                pass
            async def send_message(self, message: ChannelMessage) -> str:
                return ""
            def is_running(self):
                return False

        eng = MessagingEngine()
        cfg = ChannelConfig(channel="dummy")
        adp = DummyAdapter(cfg)
        eng.register_channel("dummy", adp)
        stats = eng.get_stats()
        assert "dummy" in stats["channels"]

    def test_process_unknown_action(self):
        eng = MessagingEngine()
        r = eng.process({"action": "nonexistent"})
        assert r["success"] is False
        assert "unknown action" in r["error"]

    def test_process_invalid_input(self):
        eng = MessagingEngine()
        r = eng.process(42)
        assert r["success"] is False

    def test_register_and_stats(self):
        eng = MessagingEngine()

        def f(ctx):
            return None

        eng.register_skill("alpha", f, "first skill")
        eng.register_skill("beta", f, "second skill")
        stats = eng.get_stats()
        assert stats["skills_registered"] == 2

    def test_gateway_status(self):
        eng = MessagingEngine()
        status = eng.gateway.status()
        assert status["running"] is False
        assert status["host"] == "0.0.0.0"

    def test_add_route(self):
        eng = MessagingEngine()
        eng.add_route("/test", "dummy", "GET")
        stats = eng.get_stats()
        assert stats["routes"] == 1

    def test_module_export(self):
        assert MessagingEngine is MessagingEngineAlias


if __name__ == "__main__":
    pytest.main([__file__])
