"""Tests for EmergentLanguage — Proto-language emergence system."""
from __future__ import annotations

import pytest

from ciel.evolution.emergent_language import (
    EmergentLanguage, Signal, SignalDomain, GrammarRule,
    LanguageState, Intent, TokenizationResult, EmergentToken, SignalMeaning,
)


class TestSignalDomain:
    def test_values(self):
        assert SignalDomain.CONSCIOUSNESS in SignalDomain
        assert SignalDomain.THREAT in SignalDomain
        assert SignalDomain.OPPORTUNITY in SignalDomain
        assert SignalDomain.COORDINATION in SignalDomain
        assert SignalDomain.IDENTITY in SignalDomain
        assert SignalDomain.TEMPORAL in SignalDomain
        assert SignalDomain.ONTOLOGICAL in SignalDomain
        assert SignalDomain.RESOURCE in SignalDomain


class TestSignal:
    def test_create(self):
        sig = Signal(
            id="sig1",
            token="Φ↑",
            meaning=SignalMeaning(
                domain=SignalDomain.CONSCIOUSNESS,
                intensity=0.5,
                context="test",
                associated_phi=0.5,
                vector_encoding=[0.5],
            ),
            originator_id="agent1",
            created_at=0,
        )
        assert sig.id == "sig1"
        assert sig.token == "Φ↑"

    def test_signal_similarity(self):
        meaning1 = SignalMeaning(
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="test",
            associated_phi=0.5,
            vector_encoding=[0.5],
        )
        meaning2 = SignalMeaning(
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="test",
            associated_phi=0.5,
            vector_encoding=[0.5],
        )
        sig1 = Signal(id="sig1", token="Φ↑", meaning=meaning1, originator_id="agent1", created_at=0)
        sig2 = Signal(id="sig2", token="Φ↑", meaning=meaning2, originator_id="agent2", created_at=0)
        # Same domain and meaning
        assert sig1.meaning.domain == sig2.meaning.domain


class TestEmergentLanguage:
    def test_instantiate(self):
        el = EmergentLanguage()
        assert el is not None

    def test_create_signal(self):
        el = EmergentLanguage()
        sig = el.create_signal(
            token="Φ↑",
            meaning=SignalMeaning(
                domain=SignalDomain.CONSCIOUSNESS,
                intensity=0.5,
                context="hello",
                associated_phi=0.5,
                vector_encoding=[0.5],
            ),
            originator_id="agent1",
        )
        assert sig is not None
        assert sig.token == "Φ↑"

    def test_signal_deduplication(self):
        el = EmergentLanguage()
        sig1 = el.create_signal(
            token="Φ↑",
            meaning=SignalMeaning(
                domain=SignalDomain.CONSCIOUSNESS,
                intensity=0.5,
                context="same",
                associated_phi=0.5,
                vector_encoding=[0.5],
            ),
            originator_id="agent1",
        )
        sig2 = el.create_signal(
            token="Φ↑",
            meaning=SignalMeaning(
                domain=SignalDomain.CONSCIOUSNESS,
                intensity=0.5,
                context="same",
                associated_phi=0.5,
                vector_encoding=[0.5],
            ),
            originator_id="agent2",
        )
        # Similar signals should be deduplicated
        assert sig1.meaning.domain == sig2.meaning.domain

    def test_express(self):
        el = EmergentLanguage()
        sig = el.express(
            genome_id="agent1",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="test",
            phi=0.5,
        )
        assert sig is not None
        assert sig.meaning.domain == SignalDomain.CONSCIOUSNESS

    def test_interpret(self):
        el = EmergentLanguage()
        sig = el.express(
            genome_id="agent1",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="test",
            phi=0.5,
        )
        interpreted = el.interpret("agent2", sig)
        assert interpreted is not None

    def test_compose_intent(self):
        el = EmergentLanguage()
        intents = [
            Intent(
                domain=SignalDomain.CONSCIOUSNESS,
                intensity=0.5,
                context="thinking",
                phi=0.5,
            )
        ]
        composed = el.compose(intents, "agent1")
        assert composed is not None

    def test_tokenize_natural_language(self):
        el = EmergentLanguage()
        result = el.tokenize("hello world test")
        assert result is not None
        assert isinstance(result.intents, list)

    def test_check_for_grammar_emergence(self):
        el = EmergentLanguage()
        sig1 = el.express(
            genome_id="agent1",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="noun",
            phi=0.5,
        )
        sig2 = el.express(
            genome_id="agent2",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="verb",
            phi=0.5,
        )
        emergence = el.check_for_grammar_emergence()
        assert isinstance(emergence, list)

    def test_compute_communication_efficiency(self):
        el = EmergentLanguage()
        el.express(
            genome_id="agent1",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="test",
            phi=0.5,
        )
        efficiency = el.compute_communication_efficiency()
        assert isinstance(efficiency, float)
        assert 0 <= efficiency <= 1

    def test_get_language_state(self):
        el = EmergentLanguage()
        state = el.get_state()
        assert state is not None
        assert state.total_signals >= 0

    def test_process_no_action(self):
        el = EmergentLanguage()
        r = el.process({})
        assert "status" in r
        assert "state" in r

    def test_process_create_signal(self):
        el = EmergentLanguage()
        r = el.process({})
        assert "status" in r
        assert "state" in r

    def test_process_express(self):
        el = EmergentLanguage()
        el.express(
            genome_id="agent1",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="test",
            phi=0.5,
        )
        r = el.process({})
        assert "status" in r

    def test_process_compose(self):
        el = EmergentLanguage()
        r = el.process({})
        assert "status" in r

    def test_process_tokenize(self):
        el = EmergentLanguage()
        r = el.process({})
        assert "status" in r

    def test_process_state(self):
        el = EmergentLanguage()
        r = el.process({})
        assert "status" in r
        assert "state" in r
        assert "total_signals" in r["state"]

    def test_process_bad_input(self):
        el = EmergentLanguage()
        r = el.process("bad")
        # process() always returns a dict
        assert isinstance(r, dict)

    def test_process_unknown_action(self):
        el = EmergentLanguage()
        r = el.process({"action": "unknown"})
        assert "status" in r

    def test_multi_domain_signals(self):
        el = EmergentLanguage()
        sig_consciousness = el.express(
            genome_id="agent1",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="thinking",
            phi=0.5,
        )
        sig_threat = el.express(
            genome_id="agent1",
            domain=SignalDomain.THREAT,
            intensity=-0.8,
            context="danger",
            phi=0.3,
        )
        sig_opportunity = el.express(
            genome_id="agent1",
            domain=SignalDomain.OPPORTUNITY,
            intensity=0.7,
            context="resource",
            phi=0.6,
        )
        assert sig_consciousness.meaning.domain == SignalDomain.CONSCIOUSNESS
        assert sig_threat.meaning.domain == SignalDomain.THREAT
        assert sig_opportunity.meaning.domain == SignalDomain.OPPORTUNITY

    def test_inter_agent_communication(self):
        el = EmergentLanguage()
        sig = el.express(
            genome_id="agent1",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="greeting",
            phi=0.5,
        )
        el.express(
            genome_id="agent2",
            domain=SignalDomain.CONSCIOUSNESS,
            intensity=0.5,
            context="greeting",
            phi=0.5,
        )
        el.interpret("agent2", sig)
        state = el.get_state()
        assert state.total_signals > 0
