from __future__ import annotations

import pytest

from ciel.evolution.abductive_inference import AbductiveInference, Hypothesis, PhiStatus


class TestHypothesis:
    def test_create(self):
        h = Hypothesis(explanation="test", plausibility=0.8, evidence=["a", "b"])
        assert h.explanation == "test"
        assert h.plausibility == 0.8
        assert h.evidence == ["a", "b"]


class TestPhiStatus:
    def test_create(self):
        ps = PhiStatus(phi=1.5, free_energy=0.3, attractor_stability=0.9)
        assert ps.phi == 1.5
        assert ps.free_energy == 0.3

    def test_defaults(self):
        ps = PhiStatus()
        assert ps.phi == 0.0
        assert ps.free_energy == 0.0


class TestAbductiveInference:
    def test_instantiate(self):
        ai = AbductiveInference()
        assert ai is not None

    def test_generate_hypotheses(self):
        ai = AbductiveInference()
        hs = ai.generate_hypotheses()
        assert isinstance(hs, list)
        for h in hs:
            assert isinstance(h, Hypothesis)

    def test_get_best_explanation(self):
        ai = AbductiveInference()
        best = ai.get_best_explanation()
        assert isinstance(best, Hypothesis)

    def test_get_best_explanation_with_phi(self):
        ai = AbductiveInference()
        ps = PhiStatus(phi=2.0, free_energy=0.8, attractor_stability=0.5)
        best = ai.get_best_explanation(ps)
        assert isinstance(best, Hypothesis)
        assert best.plausibility > 0

    def test_process_with_data(self):
        ai = AbductiveInference()
        r = ai.process({"phi": 2.0, "free_energy": 0.8, "attractor_stability": 0.5})
        assert "best_explanation" in r
        assert "best_plausibility" in r
        assert "hypotheses" in r
        assert isinstance(r["hypotheses"], list)

    def test_process_empty_input(self):
        ai = AbductiveInference()
        r = ai.process({})
        assert "best_explanation" in r

    def test_process_state(self):
        ai = AbductiveInference()
        r = ai.process({"action": "state"})
        assert "best_explanation" in r

    def test_process_bad_input(self):
        ai = AbductiveInference()
        r = ai.process("bad")
        assert "best_explanation" in r  # gracefully handled

    def test_process_unknown_action(self):
        ai = AbductiveInference()
        r = ai.process({"action": "nonexistent"})
        assert "best_explanation" in r

    def test_hypotheses_sorted_by_plausibility(self):
        ai = AbductiveInference()
        ps = PhiStatus(phi=2.0, free_energy=0.9, attractor_stability=0.5)
        hs = ai.generate_hypotheses(ps)
        plausibilities = [h.plausibility for h in hs]
        assert plausibilities == sorted(plausibilities, reverse=True)
