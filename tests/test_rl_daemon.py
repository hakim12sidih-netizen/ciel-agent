from __future__ import annotations

import asyncio

import pytest

from ciel.evolution.rl_daemon import RLDaemon, RLBenchmarkResult


class TestRLBenchmarkResult:
    def test_create(self):
        r = RLBenchmarkResult(
            genome_id="g1", fitness=100.0, duration_ms=50.0,
            success=True, polyglot_used=False, docker_synergy=False,
        )
        assert r.genome_id == "g1"
        assert r.success is True


class TestRLDaemon:
    def test_instantiate(self):
        daemon = RLDaemon()
        assert daemon is not None

    def test_get_results_empty(self):
        daemon = RLDaemon()
        assert daemon.get_results() == []

    def test_set_genomes(self):
        daemon = RLDaemon()
        daemon.set_genomes(["g1", "g2"])
        assert len(daemon._genomes) == 2

    def test_start_stop(self):
        daemon = RLDaemon()
        asyncio.run(daemon.start())
        assert daemon._task is not None
        asyncio.run(daemon.stop())
        assert daemon._task is None

    def test_start_twice_raises(self):
        daemon = RLDaemon()
        asyncio.run(daemon.start())
        with pytest.raises(RuntimeError, match="already started"):
            asyncio.run(daemon.start())
        asyncio.run(daemon.stop())

    def test_benchmark_next_no_genomes(self):
        daemon = RLDaemon()
        asyncio.run(daemon._benchmark_next())
        assert len(daemon.get_results()) == 0

    def test_process_state(self):
        daemon = RLDaemon()
        r = daemon.process({"action": "state"})
        assert "benchmarks_completed" in r
        assert r["benchmarks_completed"] == 0

    def test_process_bad_input(self):
        daemon = RLDaemon()
        r = daemon.process("bad")
        assert "benchmarks_completed" in r

    def test_process_unknown_action(self):
        daemon = RLDaemon()
        r = daemon.process({"action": "nonexistent"})
        assert "benchmarks_completed" in r
