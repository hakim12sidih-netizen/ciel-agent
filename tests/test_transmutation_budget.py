from __future__ import annotations

import pytest

from ciel.evolution.transmutation_budget import TransmutationBudget, BudgetConfig, BudgetCheck


class TestBudgetConfig:
    def test_create(self):
        c = BudgetConfig(max_transmutations=10, window_ms=60_000.0)
        assert c.max_transmutations == 10
        assert c.window_ms == 60_000.0

    def test_defaults(self):
        c = BudgetConfig()
        assert c.max_transmutations == 5
        assert "src/evolution/" in c.allowed_paths


class TestBudgetCheck:
    def test_create(self):
        bc = BudgetCheck(allowed=True, reason="OK", message="all good")
        assert bc.allowed is True
        assert bc.reason == "OK"


class TestTransmutationBudget:
    def test_instantiate(self):
        b = TransmutationBudget()
        assert b is not None

    def test_check_forbidden_path(self):
        b = TransmutationBudget()
        bc = b.check("package.json")
        assert bc.allowed is False
        assert bc.reason == "FORBIDDEN"

    def test_check_not_in_whitelist(self):
        b = TransmutationBudget()
        bc = b.check("/etc/passwd")
        assert bc.allowed is False
        assert bc.reason == "WHITELIST"

    def test_check_depth_exceeded(self):
        b = TransmutationBudget()
        bc = b.check("src/evolution/foo.py", depth=10)
        assert bc.allowed is False
        assert bc.reason == "DEPTH_EXCEEDED"

    def test_check_allowed(self):
        b = TransmutationBudget()
        bc = b.check("src/evolution/test.py")
        assert bc.allowed is True

    def test_record_and_rate_limit(self):
        config = BudgetConfig(max_transmutations=1, window_ms=60_000.0)
        b = TransmutationBudget(config=config)
        bc1 = b.check("src/evolution/a.py")
        assert bc1.allowed is True
        b.record_transmutation("src/evolution/a.py")
        bc2 = b.check("src/evolution/b.py")
        assert bc2.allowed is False
        assert bc2.reason == "RATE_LIMIT"

    def test_reset(self):
        b = TransmutationBudget()
        b.record_transmutation("src/evolution/a.py")
        b.reset()
        stats = b.get_stats()
        assert stats["transmutations_in_window"] == 0

    def test_get_stats(self):
        b = TransmutationBudget()
        stats = b.get_stats()
        assert "transmutations_in_window" in stats
        assert "max_transmutations" in stats

    def test_process_with_file(self):
        b = TransmutationBudget()
        r = b.process({"file_path": "src/evolution/foo.py"})
        assert "allowed" in r
        assert r["allowed"] is True

    def test_process_forbidden_file(self):
        b = TransmutationBudget()
        r = b.process({"file_path": "package.json"})
        assert r["allowed"] is False
        assert r["reason"] == "FORBIDDEN"

    def test_process_state(self):
        b = TransmutationBudget()
        r = b.process({"action": "state"})
        assert "transmutations_in_window" in r

    def test_process_bad_input(self):
        b = TransmutationBudget()
        r = b.process("bad")
        assert "transmutations_in_window" in r

    def test_process_unknown_action(self):
        b = TransmutationBudget()
        r = b.process({"action": "nonexistent"})
        assert "transmutations_in_window" in r
