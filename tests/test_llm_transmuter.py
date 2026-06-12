from __future__ import annotations

import asyncio
import os
import tempfile

import pytest

from ciel.evolution.llm_transmuter import LLMTransmuter, TransmutationProposal
from ciel.evolution.transmutation_budget import TransmutationBudget


def _make_evol_file(content: str = "x = 1\n") -> str:
    d = os.path.join(tempfile.gettempdir(), "src", "evolution")
    os.makedirs(d, exist_ok=True)
    fd, path = tempfile.mkstemp(suffix=".py", prefix="test_", dir=d)
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


class TestTransmutationResult:
    def test_create(self):
        tr = TransmutationResult(status="applied", file_path="/tmp/test.py", reason="ok")
        assert tr.status == "applied"
        assert tr.file_path == "/tmp/test.py"


class TestArchitecturalGene:
    def test_create(self):
        g = ArchitecturalGene(id="g1", module_name="mod1", interfaces=["i1"], dependencies=["d1"])
        assert g.id == "g1"
        assert g.fitness == 0.5


class TestLLMTransmuter:
    def test_instantiate(self):
        t = LLMTransmuter()
        assert t is not None

    def test_get_stats_default(self):
        t = LLMTransmuter()
        stats = t.get_stats()
        assert stats["total_transmutations"] == 0
        assert "budget" in stats

    def test_transmutate_no_file(self):
        t = LLMTransmuter()
        result = asyncio.run(t.transmutate("src/evolution/nonexistent.py", "fix bug"))
        assert result.status == "apply_failed"
        assert "File not found" in result.reason

    def test_transmutate_no_llm(self):
        t = LLMTransmuter()
        tmp = _make_evol_file()
        try:
            result = asyncio.run(t.transmutate(tmp, "improve"))
            assert result.status == "llm_error"
            assert "No LLM" in result.reason
        finally:
            os.unlink(tmp)

    def test_transmutate_budget_reject(self):
        config = BudgetConfig(max_transmutations=0)
        budget = TransmutationBudget(config=config)
        t = LLMTransmuter(budget=budget)
        result = asyncio.run(t.transmutate("src/evolution/test.py", "fix"))
        assert result.status == "rejected_by_budget"
        assert "Rate limit" in result.reason

    def test_transmutate_with_llm(self):
        t = LLMTransmuter(llm_complete_fn=lambda p: "new code")
        tmp = _make_evol_file()
        try:
            result = asyncio.run(t.transmutate(tmp, "improve"))
            assert result.status == "applied"
            assert result.patch_size_bytes > 0
        finally:
            os.unlink(tmp)

    def test_transmutate_aegis_reject(self):
        t = LLMTransmuter(
            llm_complete_fn=lambda p: "new code",
            aegis_verify_fn=lambda path, code: False,
        )
        tmp = _make_evol_file()
        try:
            result = asyncio.run(t.transmutate(tmp, "improve"))
            assert result.status == "rejected_by_aegis"
        finally:
            os.unlink(tmp)

    def test_build_prompt(self):
        t = LLMTransmuter()
        prompt = t._build_prompt("code", "intent", "/tmp/file.py")
        assert "intent" in prompt
        assert "code" in prompt

    def test_process_state(self):
        t = LLMTransmuter()
        r = t.process({"action": "state"})
        assert "total_transmutations" in r

    def test_process_bad_input(self):
        t = LLMTransmuter()
        r = t.process("bad")
        assert "total_transmutations" in r

    def test_process_unknown_action(self):
        t = LLMTransmuter()
        r = t.process({"action": "nonexistent"})
        assert "total_transmutations" in r
