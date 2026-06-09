from __future__ import annotations

import time

import pytest

from ciel.evolution.ascension_protocol import AscensionProtocol, AscensionRecord, SubClone


class TestAscensionRecord:
    def test_create(self):
        r = AscensionRecord(clone_id="c1", domain="Neural", ascension_time=100.0)
        assert r.clone_id == "c1"
        assert r.domain == "Neural"


class TestSubClone:
    def test_create(self):
        sc = SubClone(clone_id="c1", name="test", status="idle", clone_class="FREE", created_at=time.time())
        assert sc.clone_id == "c1"
        assert sc.status == "idle"


class TestAscensionProtocol:
    def test_instantiate(self):
        ap = AscensionProtocol()
        assert ap is not None

    def test_get_ascended_leaders_empty(self):
        ap = AscensionProtocol()
        assert ap.get_ascended_leaders() == []

    def test_trigger_ascension(self):
        ap = AscensionProtocol()
        ap.trigger_ascension("c1", "clone1", "Neural_Optimization")
        leaders = ap.get_ascended_leaders()
        assert len(leaders) == 1
        assert leaders[0].clone_id == "c1"
        assert leaders[0].domain == "Neural_Optimization"

    def test_trigger_ascension_dedup(self):
        ap = AscensionProtocol()
        ap.trigger_ascension("c1", "clone1", "Neural_Optimization")
        ap.trigger_ascension("c1", "clone1", "Memory_Hegemony")
        assert len(ap.get_ascended_leaders()) == 1

    def test_on_ascension_callback(self):
        ap = AscensionProtocol()
        calls = []
        ap.on_ascension(lambda cid, dom: calls.append((cid, dom)))
        ap.trigger_ascension("c1", "clone1", "Cyber_Security_Arch")
        assert len(calls) == 1
        assert calls[0] == ("c1", "Cyber_Security_Arch")

    def test_evaluate_low_phi(self):
        ap = AscensionProtocol()
        clones = [SubClone(clone_id="c1", name="t1", status="idle", clone_class="FREE", created_at=time.time() - 120)]
        ap.evaluate_clones_for_ascension(1.0, clones)
        assert ap.get_ascended_leaders() == []  # phi too low

    def test_evaluate_young_clones(self):
        ap = AscensionProtocol()
        clones = [SubClone(clone_id="c1", name="t1", status="idle", clone_class="FREE", created_at=time.time())]
        ap.evaluate_clones_for_ascension(5.0, clones)
        assert ap.get_ascended_leaders() == []  # not old enough

    def test_process_with_phi(self):
        ap = AscensionProtocol()
        r = ap.process({"current_phi": 6.0, "clones": []})
        assert "ascended_leaders" in r

    def test_process_state(self):
        ap = AscensionProtocol()
        r = ap.process({"action": "state"})
        assert "ascended_leaders" in r

    def test_process_bad_input(self):
        ap = AscensionProtocol()
        r = ap.process("bad")
        assert "ascended_leaders" in r

    def test_process_unknown_action(self):
        ap = AscensionProtocol()
        r = ap.process({"action": "nonexistent"})
        assert "ascended_leaders" in r
