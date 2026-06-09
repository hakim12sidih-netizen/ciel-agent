from __future__ import annotations

import asyncio

import pytest

from ciel.evolution.research_daemon import ResearchDaemon


class TestResearchDaemon:
    def test_instantiate(self):
        rd = ResearchDaemon()
        assert rd is not None

    def test_start_stop(self):
        rd = ResearchDaemon()
        asyncio.run(rd.start(interval_ms=900_000))
        assert rd._task is not None
        asyncio.run(rd.stop())
        assert rd._task is None

    def test_start_twice_raises(self):
        rd = ResearchDaemon()
        asyncio.run(rd.start())
        with pytest.raises(RuntimeError, match="already started"):
            asyncio.run(rd.start())
        asyncio.run(rd.stop())

    def test_process_trigger(self):
        rd = ResearchDaemon()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            r = rd.process({"trigger": True})
            assert "researching" in r
            assert "active" in r
            assert r["researching"] is False
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_process_state(self):
        rd = ResearchDaemon()
        r = rd.process({"action": "state"})
        assert "researching" in r
        assert r["active"] is False

    def test_process_bad_input(self):
        rd = ResearchDaemon()
        r = rd.process("bad")
        assert "researching" in r

    def test_process_unknown_action(self):
        rd = ResearchDaemon()
        r = rd.process({"action": "nonexistent"})
        assert "researching" in r

    def test_perform_research_no_llm(self):
        rd = ResearchDaemon()
        asyncio.run(rd._perform_autonomous_research())
        assert rd._is_researching is False
