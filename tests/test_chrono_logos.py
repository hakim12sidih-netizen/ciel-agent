from __future__ import annotations

import pytest

from ciel.evolution.chrono_logos import ChronoLogos, ProphecyResult


class TestProphecyResult:
    def test_create(self):
        pr = ProphecyResult(prophecy="doom", probability=0.9, prophecy_count=1)
        assert pr.prophecy == "doom"
        assert pr.probability == 0.9


class TestChronoLogos:
    def test_instantiate(self):
        cl = ChronoLogos()
        assert cl is not None

    def test_record_narrative(self):
        cl = ChronoLogos()
        cl.record_narrative("The system is stable.")
        assert len(cl._narrative_history) == 1

    def test_forecast_divergence_insufficient_data(self):
        cl = ChronoLogos()
        prophecy = cl.forecast_divergence()
        assert "Insufficient" in prophecy

    def test_forecast_divergence_stable(self):
        cl = ChronoLogos()
        prophecy = cl.forecast_divergence(
            "Everything is calm. " * 30
        )
        assert "STABILITY ASCENDANT" in prophecy

    def test_forecast_divergence_drift(self):
        cl = ChronoLogos()
        prophecy = cl.forecast_divergence("DISSONANCE " * 15 + "HIGH " * 5)
        assert ("DRIFT" in prophecy) or ("WARNING" in prophecy)

    def test_forecast_divergence_collapse(self):
        cl = ChronoLogos()
        prophecy = cl.forecast_divergence("DISSONANCE " * 20 + "HIGH " * 20)
        assert "WARNING" in prophecy

    def test_process_with_narrative(self):
        cl = ChronoLogos()
        r = cl.process({"narrative": "DISSONANCE " * 20})
        assert "prophecy" in r
        assert "prophecy_count" in r
        assert r["prophecy_count"] >= 1

    def test_process_state(self):
        cl = ChronoLogos()
        r = cl.process({"action": "state"})
        assert "prophecy" in r

    def test_process_bad_input(self):
        cl = ChronoLogos()
        r = cl.process("bad")
        assert "prophecy" in r

    def test_process_unknown_action(self):
        cl = ChronoLogos()
        r = cl.process({"action": "nonexistent"})
        assert "prophecy" in r

    def test_prophecy_count_increments(self):
        cl = ChronoLogos()
        cl.process({"narrative": "test " * 50})
        cl.process({"narrative": "test " * 50})
        assert cl._prophecy_count == 2
