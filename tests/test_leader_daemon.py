from __future__ import annotations

import asyncio

import pytest

from ciel.evolution.leader_daemon import LeaderDaemon


class TestLeaderDaemon:
    def test_instantiate(self):
        ld = LeaderDaemon()
        assert ld is not None

    def test_set_factions(self):
        ld = LeaderDaemon()
        ld.set_factions(["f1", "f2"])
        assert len(ld._factions) == 2

    def test_set_population(self):
        ld = LeaderDaemon()
        ld.set_population(["g1", "g2"])
        assert len(ld._population) == 2

    def test_set_imperial_order(self):
        ld = LeaderDaemon()
        ld.set_imperial_order("Explore")
        assert ld._current_imperial_order == "Explore"

    def test_start_stop(self):
        ld = LeaderDaemon()
        asyncio.run(ld.start())
        assert ld._task is not None
        asyncio.run(ld.stop())
        assert ld._task is None

    def test_start_twice_raises(self):
        ld = LeaderDaemon()
        asyncio.run(ld.start())
        with pytest.raises(RuntimeError, match="already started"):
            asyncio.run(ld.start())
        asyncio.run(ld.stop())

    def test_process_with_order(self):
        ld = LeaderDaemon()
        r = ld.process({"imperial_order": "Conquer"})
        assert ld._current_imperial_order == "Conquer"
        assert "factions_count" in r
        assert "active" in r

    def test_process_state(self):
        ld = LeaderDaemon()
        r = ld.process({"action": "state"})
        assert "factions_count" in r
        assert r["factions_count"] == 0

    def test_process_bad_input(self):
        ld = LeaderDaemon()
        r = ld.process("bad")
        assert "factions_count" in r

    def test_process_unknown_action(self):
        ld = LeaderDaemon()
        r = ld.process({"action": "nonexistent"})
        assert "factions_count" in r
