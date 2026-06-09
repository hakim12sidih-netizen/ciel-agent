from __future__ import annotations

import asyncio
import json
import os
import tempfile

import pytest

from ciel.evolution.torch_rl_bridge import TorchRLBridge, RLState, RLStepResult, DIM


class TestRLState:
    def test_create(self):
        s = RLState(state=[1.0] * 12)
        assert len(s.state) == 12
        assert s.state[0] == 1.0

    def test_defaults(self):
        s = RLState()
        assert len(s.state) == 12
        assert len(s.weights) == 12
        assert len(s.bias) == 12


class TestRLStepResult:
    def test_create(self):
        r = RLStepResult(status="success", loss=0.5, iterations=1)
        assert r.status == "success"
        assert r.loss == 0.5


class TestTorchRLBridge:
    def test_instantiate(self):
        bridge = TorchRLBridge()
        assert bridge is not None

    def test_initial_stats(self):
        bridge = TorchRLBridge()
        stats = bridge.get_stats()
        assert stats["call_count"] == 0
        assert stats["fallback_count"] == 0

    def test_train_step(self):
        async def _test():
            bridge = TorchRLBridge()
            result = await bridge.train_step([1.0] * DIM, [0.5] * DIM)
            assert result.status == "fallback"
            assert result.fallback is True
            assert result.iterations == 1
            assert len(result.weights) == DIM
            assert len(result.bias) == DIM
        asyncio.run(_test())

    def test_train_step_force_fallback(self):
        async def _test():
            bridge = TorchRLBridge(force_fallback=True)
            result = await bridge.train_step([1.0] * DIM, [0.5] * DIM)
            assert result.fallback is True
            stats = bridge.get_stats()
            assert stats["fallback_count"] == 1
        asyncio.run(_test())

    def test_load_checkpoint_none(self):
        bridge = TorchRLBridge(checkpoint_path="/nonexistent/hydra_rl_checkpoint.json")
        assert bridge.load_checkpoint() is None

    def test_checkpoint_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            ckpt_path = f.name
        try:
            bridge = TorchRLBridge(checkpoint_path=ckpt_path)
            async def _test():
                await bridge.train_step([1.0] * DIM, [0.5] * DIM)
            asyncio.run(_test())
            loaded = bridge.load_checkpoint()
            assert loaded is not None
            assert len(loaded.weights) == DIM
            assert len(loaded.bias) == DIM
        finally:
            if os.path.exists(ckpt_path):
                os.unlink(ckpt_path)

    def test_reset_checkpoint(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"state": [0.0] * DIM}, f)
            ckpt_path = f.name
        try:
            bridge = TorchRLBridge(checkpoint_path=ckpt_path)
            bridge.reset_checkpoint()
            assert not os.path.exists(ckpt_path)
        finally:
            if os.path.exists(ckpt_path):
                os.unlink(ckpt_path)

    def test_process_with_data(self):
        bridge = TorchRLBridge()
        r = bridge.process({"state": [1.0] * DIM, "reward": [0.5] * DIM})
        assert "status" in r
        assert "loss" in r
        assert "mean_reward" in r
        assert r["fallback"] is True

    def test_process_state(self):
        bridge = TorchRLBridge()
        r = bridge.process({"action": "state"})
        assert "status" in r
        assert "fallback" in r

    def test_process_bad_input(self):
        bridge = TorchRLBridge()
        r = bridge.process("bad")
        assert "call_count" in r

    def test_process_unknown_action(self):
        bridge = TorchRLBridge()
        r = bridge.process({"action": "nonexistent"})
        assert "status" in r
        assert "fallback" in r
