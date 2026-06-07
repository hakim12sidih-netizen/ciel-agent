"""
Tests pour le polyglot bridge (subprocess wrapper).
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from ciel.polyglot.bridge import (
    BridgeConfig,
    BridgeError,
    BridgeProtocolError,
    BridgeTimeout,
    PolyglotBridge,
    BRIDGE_PROTOCOL_VERSION,
)


# ── Helper : crée un faux binaire bridge pour les tests ───

def _create_echo_bridge(path: Path) -> Path:
    """Crée un script bash qui implémente un bridge JSON basique."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Le script lit JSON sur stdin, ajoute "echo":true, écrit sur stdout
    script = """#!/bin/bash
read input
op=$(echo "$input" | python3 -c "import json,sys; print(json.load(sys.stdin).get('op',''))")
echo "{\\"op_received\\":\\"$op\\",\\"input_received\\":$input}"
"""
    path.write_text(script)
    path.chmod(0o755)
    return path


def _create_failing_bridge(path: Path) -> Path:
    """Bridge qui retourne exit code 1."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\necho 'something went wrong' >&2\nexit 1\n")
    path.chmod(0o755)
    return path


def _create_slow_bridge(path: Path) -> Path:
    """Bridge qui prend 5 secondes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\nsleep 5\necho '{}'\n")
    path.chmod(0o755)
    return path


class TestBridgeConfig:
    def test_basic_config(self, tmp_path) -> None:
        cfg = BridgeConfig(binary_path=tmp_path / "binary")
        assert cfg.timeout_s == 30.0
        assert cfg.args == ()
        assert cfg.cwd is None

    def test_custom_config(self, tmp_path) -> None:
        b = tmp_path / "binary"
        cfg = BridgeConfig(
            binary_path=b,
            args=("--mode", "json"),
            env={"DEBUG": "1"},
            cwd=tmp_path,
            timeout_s=10.0,
        )
        assert cfg.args == ("--mode", "json")
        assert cfg.env == {"DEBUG": "1"}


class TestPolyglotBridgeInit:
    def test_init_with_existing_binary(self, tmp_path) -> None:
        b = _create_echo_bridge(tmp_path / "echo.sh")
        bridge = PolyglotBridge(BridgeConfig(binary_path=b))
        assert bridge._call_count == 0
        assert bridge._error_count == 0

    def test_init_fails_on_missing_binary(self, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            PolyglotBridge(BridgeConfig(binary_path=tmp_path / "nope"))

    def test_protocol_version_constant(self) -> None:
        assert BRIDGE_PROTOCOL_VERSION == 1


class TestPolyglotBridgeCall:
    def test_basic_call(self, tmp_path) -> None:
        b = _create_echo_bridge(tmp_path / "echo.sh")
        bridge = PolyglotBridge(BridgeConfig(binary_path=b))
        result = bridge.call({"op": "test_op", "x": 42})
        assert "op_received" in result
        assert result["op_received"] == "test_op"

    def test_call_increments_stats(self, tmp_path) -> None:
        b = _create_echo_bridge(tmp_path / "echo.sh")
        bridge = PolyglotBridge(BridgeConfig(binary_path=b))
        bridge.call({"op": "a"})
        bridge.call({"op": "b"})
        s = bridge.stats()
        assert s["calls"] == 2
        assert s["errors"] == 0

    def test_failing_binary_raises(self, tmp_path) -> None:
        b = _create_failing_bridge(tmp_path / "fail.sh")
        bridge = PolyglotBridge(BridgeConfig(binary_path=b))
        with pytest.raises(BridgeError):
            bridge.call({"op": "x"})
        s = bridge.stats()
        assert s["errors"] == 1

    def test_timeout_raises_bridge_timeout(self, tmp_path) -> None:
        b = _create_slow_bridge(tmp_path / "slow.sh")
        bridge = PolyglotBridge(
            BridgeConfig(binary_path=b, timeout_s=0.5)
        )
        with pytest.raises(BridgeTimeout):
            bridge.call({"op": "x"})

    def test_invalid_payload_raises_typeerror(self, tmp_path) -> None:
        b = _create_echo_bridge(tmp_path / "echo.sh")
        bridge = PolyglotBridge(BridgeConfig(binary_path=b))
        with pytest.raises(TypeError):
            bridge.call("not a dict")  # type: ignore[arg-type]

    def test_protocol_error_on_non_dict_response(self, tmp_path) -> None:
        # Bridge qui retourne un string JSON
        bad = tmp_path / "bad.sh"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("#!/bin/bash\necho '\"just a string\"'\n")
        bad.chmod(0o755)
        bridge = PolyglotBridge(BridgeConfig(binary_path=bad))
        with pytest.raises(BridgeProtocolError):
            bridge.call({"x": 1})


class TestBridgeStats:
    def test_initial_stats(self, tmp_path) -> None:
        b = _create_echo_bridge(tmp_path / "echo.sh")
        bridge = PolyglotBridge(BridgeConfig(binary_path=b))
        s = bridge.stats()
        assert s["calls"] == 0
        assert s["errors"] == 0
        assert s["total_duration_s"] == 0.0
        assert s["avg_duration_s"] == 0.0
        assert s["binary"].endswith("echo.sh")

    def test_avg_duration(self, tmp_path) -> None:
        b = _create_echo_bridge(tmp_path / "echo.sh")
        bridge = PolyglotBridge(BridgeConfig(binary_path=b))
        bridge.call({"op": "x"})
        bridge.call({"op": "y"})
        s = bridge.stats()
        assert s["avg_duration_s"] > 0
        assert s["total_duration_s"] > 0


class TestBridgeConstants:
    def test_protocol_version(self) -> None:
        # Le protocole v1 est la version initiale
        assert BRIDGE_PROTOCOL_VERSION >= 1
