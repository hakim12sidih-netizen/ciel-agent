from __future__ import annotations

import os
import tempfile

import pytest

from ciel.evolution.heal import Heal


class TestHeal:
    def test_instantiate(self):
        h = Heal()
        assert h is not None

    def test_get_stats_empty(self):
        h = Heal()
        assert h.get_stats() == []

    def test_diagnose_and_repair_missing_file(self):
        h = Heal()
        result = h.diagnose_and_repair("/nonexistent/file.py", "SyntaxError")
        assert result is False

    def test_diagnose_and_repair_no_llm(self):
        h = Heal()
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("x = 1\n")
            tmp = f.name
        try:
            result = h.diagnose_and_repair(tmp, "SyntaxError")
            assert result is False  # no LLM fn
        finally:
            os.unlink(tmp)

    def test_diagnose_and_repair_with_llm(self):
        h = Heal(llm_complete_fn=lambda p: "fixed code")
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("x = 1\n")
            tmp = f.name
        try:
            result = h.diagnose_and_repair(tmp, "SyntaxError")
            assert result is True
            assert h.get_stats() == [(tmp, 1)]
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
            bak = tmp + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)

    def test_process_with_target(self):
        h = Heal()
        r = h.process({"target_file": "/nonexistent/file.py", "error": "bug"})
        assert "repaired" in r
        assert r["repaired"] is False
        assert r["target"] == "/nonexistent/file.py"

    def test_process_state(self):
        h = Heal()
        r = h.process({"action": "state"})
        assert "history" in r

    def test_process_bad_input(self):
        h = Heal()
        r = h.process("bad")
        assert "history" in r

    def test_process_unknown_action(self):
        h = Heal()
        r = h.process({"action": "nonexistent"})
        assert "history" in r

    def test_stats_after_repair(self):
        h = Heal(llm_complete_fn=lambda p: "fixed")
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("x = 1\n")
            tmp = f.name
        try:
            h.diagnose_and_repair(tmp, "err")
            stats = h.get_stats()
            assert len(stats) == 1
            assert stats[0][0] == tmp
            assert stats[0][1] == 1
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
            bak = tmp + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)
