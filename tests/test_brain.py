from __future__ import annotations

import pytest
from ciel.brain.core import CIELBrain, CIELState, ProcessStatus


class TestCIELState:
    def test_create(self):
        s = CIELState()
        assert s.uptime == 0.0
        assert s.n_cycles == 0
        assert s.modules_loaded == []
        assert s.status == ProcessStatus.IDLE


class TestCIELBrain:
    def test_create(self):
        b = CIELBrain()
        assert b.name == "CIEL v∞.3"
        assert b.state.status == ProcessStatus.IDLE

    def test_load_module(self):
        b = CIELBrain()
        b.load_module("test", {"key": "val"})
        assert b.has_module("test") is True
        assert b.get_module("test")["key"] == "val"

    def test_hooks(self):
        b = CIELBrain()
        calls = []
        b.register_hook("test.event", lambda **kw: calls.append(kw))
        b.emit("test.event", x=1)
        assert len(calls) == 1
        assert calls[0]["x"] == 1

    def test_start_stop(self):
        b = CIELBrain()
        events = []
        b.register_hook("brain.start", lambda **kw: events.append("start"))
        b.register_hook("brain.stop", lambda **kw: events.append("stop"))
        b.start()
        assert b.state.status == ProcessStatus.RUNNING
        b.stop()
        assert b.state.status == ProcessStatus.TERMINATED
        assert "start" in events
        assert "stop" in events

    def test_cycle(self):
        b = CIELBrain()
        b.start()
        result = b.cycle()
        assert result["cycle"] == 1
        assert result["modules_active"] == 0

    def test_pause_resume(self):
        b = CIELBrain()
        b.start()
        b.pause()
        assert b.state.status == ProcessStatus.PAUSED
        b.resume()
        assert b.state.status == ProcessStatus.RUNNING

    def test_status_report(self):
        b = CIELBrain()
        b.start()
        report = b.status_report()
        assert report["name"] == "CIEL v∞.3"
        assert "status" in report
        assert "modules" in report

    def test_process_passthrough(self):
        b = CIELBrain()
        b.load_module("identity", type("", (), {"process": lambda self, x: x})())
        result = b.process({"hello": "world"})
        assert result == {"hello": "world"}

    def test_process_error(self):
        b = CIELBrain()
        b.load_module("bad", type("", (), {"process": lambda self, x: 1/0})())
        b.process({"data": 1})
        assert "bad.process" in b.state.last_error

    def test_load_all_modules(self):
        b = CIELBrain()
        b.load_all_modules(peer_id="test-node")
        assert b.has_module("analysis") is True
        assert b.has_module("animus") is True
        assert b.has_module("conscience") is True
        assert b.has_module("economy") is True
        assert b.has_module("math") is True
        assert b.has_module("meta") is True
        assert b.has_module("noosphere") is True
        assert b.has_module("perception") is True
        assert b.has_module("quantum") is True
        assert b.has_module("security") is True
        assert b.has_module("skills") is True
        assert b.has_module("swarm") is True
        assert len(b.state.modules_loaded) == 14

    def test_process_across_all_modules(self):
        b = CIELBrain()
        b.load_all_modules(peer_id="test-node")
        b.start()

        result = b.process({"action": "stats"})
        assert result["success"] is True
        assert "stats" in result

        result = b.process({"action": "feel", "emotion": "joy", "intensity": 0.8})
        assert result["success"] is True

        result = b.process({"action": "perceive", "modality": "visual", "content": "hello"})
        assert result["success"] is True

    def test_process_via_swarm(self):
        b = CIELBrain()
        b.load_all_modules(peer_id="int-node")
        b.start()

        result = b.process({"action": "set_role", "role": "reine"})
        assert result["success"] is True

        result = b.process({"action": "discover"})
        assert result["success"] is True

    def test_cycle_with_modules(self):
        b = CIELBrain()
        b.load_all_modules()
        b.start()
        for i in range(5):
            b.cycle()
        assert b.state.n_cycles == 5

    def test_brain_name_custom(self):
        b = CIELBrain(name="CIEL-ALPHA")
        assert b.name == "CIEL-ALPHA"
