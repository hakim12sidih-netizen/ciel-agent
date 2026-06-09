from __future__ import annotations

import asyncio

import pytest

from ciel.evolution.distiller_daemon import DistillerDaemon, DistillationRecord


class TestDistillationRecord:
    def test_create(self):
        dr = DistillationRecord(
            topic="AI", input_text="in", reasoning="r", lecture="l", output="out", timestamp=100.0
        )
        assert dr.topic == "AI"
        assert dr.output == "out"


class TestDistillerDaemon:
    def test_instantiate(self):
        dd = DistillerDaemon()
        assert dd is not None

    def test_get_records_empty(self):
        dd = DistillerDaemon()
        assert dd.get_records() == []

    def test_start_stop(self):
        dd = DistillerDaemon()
        asyncio.run(dd.start(interval_ms=3_600_000))
        assert dd._task is not None
        asyncio.run(dd.stop())
        assert dd._task is None

    def test_process_state(self):
        dd = DistillerDaemon()
        r = dd.process({"action": "state"})
        assert "distillation_count" in r
        assert r["distillation_count"] == 0

    def test_process_trigger(self):
        dd = DistillerDaemon()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            r = dd.process({"trigger": True})
            assert "distillation_count" in r
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_process_bad_input(self):
        dd = DistillerDaemon()
        r = dd.process("bad")
        assert "distillation_count" in r

    def test_process_unknown_action(self):
        dd = DistillerDaemon()
        r = dd.process({"action": "nonexistent"})
        assert "distillation_count" in r

    def test_start_while_running(self):
        dd = DistillerDaemon()
        asyncio.run(dd.start())
        asyncio.run(dd.start())  # no-op
        assert dd._task is not None
        asyncio.run(dd.stop())
