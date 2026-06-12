"""Tests for CIEL ConfigEngine — layered configuration."""
from __future__ import annotations

import os

import pytest

from ciel.config.core import ConfigEngine


@pytest.fixture
def engine(tmp_path):
    cfg_path = str(tmp_path / "ciel.json")
    return ConfigEngine(config_path=cfg_path)


class TestConfigEngine:
    def test_defaults_exist(self, engine):
        config = engine.build()
        assert "api" in config
        assert config["api"]["port"] == 8765

    def test_get_nested_key(self, engine):
        val = engine.get("api.port")
        assert val == 8765

    def test_get_default(self, engine):
        val = engine.get("nonexistent.key", "fallback")
        assert val == "fallback"

    def test_set_and_persist(self, engine):
        r = engine.set("api.port", 9999)
        assert r["status"] == "ok"
        val = engine.get("api.port")
        assert val == 9999

    def test_env_variables_override(self, engine):
        os.environ["CIEL_API__PORT"] = "8080"
        try:
            config = engine.build()
            assert config["api"]["port"] == 8080
        finally:
            del os.environ["CIEL_API__PORT"]

    def test_env_bool_parsing(self, engine):
        os.environ["CIEL_CONTROL__LIVE_MODE"] = "true"
        try:
            config = engine.build()
            assert config["control"]["live_mode"] is True
        finally:
            del os.environ["CIEL_CONTROL__LIVE_MODE"]

    def test_env_int_parsing(self, engine):
        os.environ["CIEL_CACHE__MAX_SIZE"] = "500"
        try:
            config = engine.build()
            assert config["cache"]["max_size"] == 500
        finally:
            del os.environ["CIEL_CACHE__MAX_SIZE"]

    def test_cli_overrides(self, engine):
        config = engine.build(cli_overrides={"api": {"port": 3000}})
        assert config["api"]["port"] == 3000

    def test_cli_overrides_beat_defaults(self, engine):
        os.environ["CIEL_API__PORT"] = "8080"
        try:
            config = engine.build(cli_overrides={"api": {"port": 3000}})
            assert config["api"]["port"] == 3000
        finally:
            del os.environ["CIEL_API__PORT"]

    def test_reset(self, engine):
        engine.set("api.port", 1111)
        r = engine.reset()
        assert r["status"] == "ok"

    def test_get_stats(self, engine):
        stats = engine.get_stats()
        assert "layers" in stats
        assert "keys" in stats

    def test_deep_merge(self, engine):
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"b": 99, "d": 3}}
        merged = ConfigEngine._deep_merge(base, override)
        assert merged["a"]["b"] == 99
        assert merged["a"]["c"] == 2
        assert merged["a"]["d"] == 3

    def test_parse_val_bool(self):
        assert ConfigEngine._parse_val("true") is True
        assert ConfigEngine._parse_val("false") is False

    def test_parse_val_int(self):
        assert ConfigEngine._parse_val("42") == 42

    def test_parse_val_float(self):
        assert ConfigEngine._parse_val("3.14") == 3.14

    def test_parse_val_none(self):
        assert ConfigEngine._parse_val("null") is None

    def test_parse_val_list(self):
        assert ConfigEngine._parse_val("[1,2,3]") == [1, 2, 3]

    def test_process_build(self, engine):
        r = engine.process({"action": "build"})
        assert r["status"] == "ok"
        assert "api" in r["config"]

    def test_process_get(self, engine):
        r = engine.process({"action": "get", "key": "api.port"})
        assert r["status"] == "ok"
        assert r["value"] == 8765

    def test_process_set(self, engine):
        r = engine.process({"action": "set", "key": "api.port",
                            "value": 7777})
        assert r["status"] == "ok"
        val = engine.get("api.port")
        assert val == 7777

    def test_process_reset(self, engine):
        r = engine.process({"action": "reset"})
        assert r["status"] == "ok"

    def test_process_stats(self, engine):
        r = engine.process({"action": "stats"})
        assert "layers" in r

    def test_file_persistence(self, engine):
        engine.set("test.key", "stored")
        engine2 = ConfigEngine(config_path=engine._config_path)
        val = engine2.get("test.key")
        assert val == "stored"

    def test_multiple_layers(self, engine):
        config = engine.build()
        layers = engine._layers
        priorities = [l.priority for l in layers]
        assert priorities == sorted(priorities)
