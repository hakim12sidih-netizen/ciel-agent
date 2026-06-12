from __future__ import annotations

import pytest

from ciel.evolution.faction import FactionManager


class TestFactionManager:
    def test_create_faction(self):
        f = FactionManager.create(leader_id="leader_1", specialties=["Master of Alpha"])
        assert f.leader_id == "leader_1"
        assert f.id.startswith("fac_")
        assert f.prestige == 0.0
        assert f.resources == 100.0

    def test_create_default_specialties(self):
        f = FactionManager.create(leader_id="leader_1")
        assert f.leader_id == "leader_1"

    def test_create_different_titles(self):
        titles = set()
        for _ in range(50):
            f = FactionManager.create(leader_id="l1")
            titles.add(f.title)
        assert len(titles) > 1  # random titles

    def test_set_true_ai_leader(self):
        f = FactionManager.create(leader_id="l1")
        f.set_true_ai_leader("clone_42")
        assert f.leader_clone_id == "clone_42"
        assert "True AI Sovereign" in f.title

    def test_record_success(self):
        f = FactionManager.create(leader_id="l1")
        f.record_success(5.0)
        assert f.prestige == 5.0
        assert f.resources == 150.0

    def test_calculate_dominance(self):
        f = FactionManager.create(leader_id="l1")
        f.calculate_dominance(10)
        assert f.dominance == 0.0  # no adepts

        f.active_adept_ids = ["a1", "a2"]
        f.leader_clone_id = "c1"
        f.calculate_dominance(5)
        assert f.dominance == 0.6  # 3 out of 5

    def test_to_dict(self):
        f = FactionManager.create(leader_id="l1", specialties=["Logic"])
        d = f.to_dict()
        assert d["id"] == f.id
        assert d["name"] == f.name
        assert d["prestige"] == 0.0
        assert d["adept_count"] == 0

    def test_process_create(self):
        r = process({"action": "create", "leader_id": "l1", "specialties": ["Logic"]})
        assert "faction" in r
        assert r["faction"]["leader_id"] == "l1"

    def test_process_state(self):
        r = process({"action": "state"})
        assert "factions" in r

    def test_process_bad_input(self):
        r = process("bad")
        assert "factions" in r

    def test_process_unknown_action(self):
        r = process({"action": "nonexistent"})
        assert "factions" in r
