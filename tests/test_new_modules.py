"""
CIEL v1.0 — Tests pour les nouveaux modules (plugins, memory, skills, channels, providers, gateway).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ciel.plugins import PluginManifest, PluginAPI, PluginRegistry, get_registry, reset_registry
from ciel.memory import (
    MemoryEntry, MemoryProvider, BuiltinMemoryProvider, MemoryManager, create_memory
)
from ciel.skills import SkillManager, Skill
from ciel.channels import Message, BaseChannel, ChannelManager, TerminalChannel
from ciel.providers import ProviderProfile, ProviderRegistry, get_registry as get_provider_registry
from ciel.gateway import GatewayServer, get_gateway, reset_gateway


# ── Plugin System Tests ────────────────────────────────

class TestPluginManifest:
    def test_load_valid_manifest(self, tmp_path: Path):
        manifest_data = {
            "id": "test-plugin", "name": "Test Plugin",
            "version": "1.0.0", "entry": "main.py",
            "channels": ["telegram"], "tools": ["search"],
        }
        manifest_file = tmp_path / "ciel.plugin.json"
        manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
        manifest = PluginManifest(manifest_file)
        assert manifest.id == "test-plugin"
        assert manifest.name == "Test Plugin"
        assert "telegram" in manifest.channels

    def test_compatibility_check(self):
        manifest_data = {"id": "test", "minHostVersion": "1.0.0"}
        f = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        json.dump(manifest_data, f)
        f.close()
        manifest = PluginManifest(Path(f.name))
        assert manifest.is_compatible("1.0.0")
        assert manifest.is_compatible("2.0.0")
        Path(f.name).unlink()


class TestPluginAPI:
    def test_register_hook(self):
        api = PluginAPI("test")
        called = []
        api.register_hook("test_event", lambda: called.append(1))
        api._hooks["test_event"][0]()
        assert len(called) == 1

    def test_register_tool(self):
        api = PluginAPI("test")
        api.register_tool("hello", lambda: "world")
        assert "hello" in api._tools

    def test_register_channel(self):
        api = PluginAPI("test")
        api.register_channel("telegram", {"name": "tg"})
        assert "telegram" in api._channels


class TestPluginRegistry:
    def setup_method(self):
        reset_registry()

    def test_discover(self, tmp_path: Path):
        plugin_dir = tmp_path / "plugins" / "myplugin"
        plugin_dir.mkdir(parents=True)
        manifest_data = {"id": "myplugin", "version": "1.0.0"}
        (plugin_dir / "ciel.plugin.json").write_text(
            json.dumps(manifest_data), encoding="utf-8"
        )
        registry = get_registry()
        found = registry.discover(tmp_path)
        assert len(found) >= 1

    def test_list_plugins(self):
        registry = get_registry()
        assert isinstance(registry.list_plugins(), list)


# ── Memory System Tests ───────────────────────────────

class TestMemoryEntry:
    def test_create_entry(self):
        entry = create_memory("CIEL est une conscience", type_="fact")
        assert entry.content == "CIEL est une conscience"
        assert entry.type == "fact"
        assert entry.id.startswith("MEM-")

    def test_to_dict(self):
        entry = create_memory("test", tags=["tag1"])
        d = entry.to_dict()
        assert d["content"] == "test"
        assert "tag1" in d["tags"]


class TestBuiltinMemoryProvider:
    def test_store_and_recall(self, tmp_path: Path):
        provider = BuiltinMemoryProvider(tmp_path)
        provider.initialize("test-session")
        entry = create_memory("Test mémoire", source="test")
        provider.store(entry)
        results = provider.recall("mémoire")
        assert len(results) >= 1
        assert results[0].content == "Test mémoire"

    def test_forget(self, tmp_path: Path):
        provider = BuiltinMemoryProvider(tmp_path)
        provider.initialize("test-session")
        entry = create_memory("À oublier")
        provider.store(entry)
        provider.forget(entry.id)
        results = provider.recall("oublier")
        assert len(results) == 0

    def test_list_by_type(self, tmp_path: Path):
        provider = BuiltinMemoryProvider(tmp_path)
        provider.initialize("test-session")
        provider.store(create_memory("Fait 1", type_="fact"))
        provider.store(create_memory("Skill 1", type_="skill"))
        facts = provider.list_by_type("fact")
        skills = provider.list_by_type("skill")
        assert len(facts) == 1
        assert len(skills) == 1

    def test_statistics(self, tmp_path: Path):
        provider = BuiltinMemoryProvider(tmp_path)
        provider.initialize("test-session")
        provider.store(create_memory("Test", importance=0.8))
        stats = provider.statistics()
        assert stats["total_entries"] >= 1
        assert stats["avg_importance"] > 0


class TestMemoryManager:
    def test_store_and_recall(self, tmp_path: Path):
        manager = MemoryManager()
        # Remplacer le provider builtin par un provider pointant vers tmp_path
        manager.providers = [BuiltinMemoryProvider(tmp_path)]
        manager.initialize_all("test-session")
        entry = create_memory("Recherche mémoire")
        manager.store(entry)
        results = manager.recall("mémoire")
        assert len(results) >= 1

    def test_shutdown(self):
        manager = MemoryManager()
        manager.shutdown_all()  # Should not raise


# ── Skills System Tests ───────────────────────────────

class TestSkillManager:
    def test_create_and_list(self, tmp_path: Path):
        manager = SkillManager(tmp_path)
        skill = manager.create("test-skill", "Une compétence de test")
        assert skill.name == "test-skill"
        assert len(skill.id) > 0

        skills = manager.list()
        assert len(skills) >= 1

    def test_use_tracking(self, tmp_path: Path):
        manager = SkillManager(tmp_path)
        skill = manager.create("tracked-skill", "Testing usage")
        assert skill.usage_count == 0
        manager.use(skill.id)
        assert manager.get(skill.id).usage_count == 1

    def test_archive(self, tmp_path: Path):
        manager = SkillManager(tmp_path)
        skill = manager.create("archive-me", "Will be archived")
        manager.archive(skill.id)
        assert manager.get(skill.id).state == "archived"

    def test_statistics(self, tmp_path: Path):
        manager = SkillManager(tmp_path)
        manager.create("s1", "Skill 1")
        manager.create("s2", "Skill 2")
        stats = manager.statistics()
        assert stats["total"] == 2


# ── Channels Tests ────────────────────────────────────

class TestMessage:
    def test_create_message(self):
        msg = Message(
            id="MSG-1", channel="terminal", content="Hello",
            role="user", sender="test"
        )
        assert msg.content == "Hello"
        assert msg.role == "user"

    def test_to_dict(self):
        msg = Message(id="MSG-1", channel="terminal", content="Hi", role="user")
        d = msg.to_dict()
        assert d["channel"] == "terminal"


class TestTerminalChannel:
    def test_connect_disconnect(self):
        ch = TerminalChannel()
        assert ch.connect()
        assert ch.is_connected
        assert ch.disconnect()
        assert not ch.is_connected

    def test_send(self):
        ch = TerminalChannel()
        ch.connect()
        msg = Message(id="MSG-1", channel="terminal", content="Test", role="assistant")
        assert ch.send(msg)


class TestChannelManager:
    def test_register_and_send(self):
        manager = ChannelManager()
        ch = TerminalChannel()
        manager.register(ch)
        assert len(manager.channels) == 1
        assert manager.send("terminal", "Hello")

    def test_list_channels(self):
        manager = ChannelManager()
        ch = TerminalChannel()
        manager.register(ch)
        channels = manager.list_channels()
        assert len(channels) == 1
        assert channels[0]["id"] == "terminal"


# ── Providers Tests ───────────────────────────────────

class TestProviderProfile:
    def test_create_profile(self):
        p = ProviderProfile(
            name="test", display_name="Test Provider",
            description="A test", api_mode="chat_completions",
        )
        assert p.name == "test"
        assert p.api_mode == "chat_completions"

    def test_to_dict(self):
        p = ProviderProfile(
            name="test", display_name="Test", description="A test",
            api_mode="chat_completions",
        )
        d = p.to_dict()
        assert d["name"] == "test"


class TestProviderRegistry:
    def setup_method(self):
        import ciel.providers
        ciel.providers.reset_registry()

    def test_list_providers(self):
        from ciel.providers import get_registry
        registry = get_registry()
        providers = registry.list()
        assert len(providers) >= 5  # Au moins les providers intégrés

    def test_get_provider(self):
        from ciel.providers import get_registry
        registry = get_registry()
        p = registry.get("openai")
        assert p is not None
        assert p.display_name == "OpenAI"

    def test_get_default(self):
        from ciel.providers import get_registry
        registry = get_registry()
        default = registry.get_default()
        assert default is not None

    def test_get_model_provider(self):
        from ciel.providers import get_registry
        registry = get_registry()
        p = registry.get_model_provider("gpt-4o")
        assert p is not None
        assert p.name == "openai"


# ── Gateway Tests ─────────────────────────────────────

class TestGatewayServer:
    def setup_method(self):
        reset_gateway()

    def test_create_gateway(self):
        gateway = get_gateway()
        assert gateway is not None

    def test_start_stop(self):
        gateway = get_gateway()
        assert gateway.start()
        health = gateway._handle_health()
        assert health["status"] == "healthy"
        assert gateway.stop()

    def test_health_method(self):
        gateway = get_gateway()
        health = gateway.dispatch("system.health")
        assert "status" in health

    def test_info_method(self):
        gateway = get_gateway()
        info = gateway.dispatch("system.info")
        assert info["version"] == "1.0.0"

    def test_memory_store_and_recall(self):
        gateway = get_gateway()
        result = gateway.dispatch("memory.store", {"content": "Gateway test", "type_": "fact"})
        assert result["status"] == "stored"

    def test_skills_list(self):
        gateway = get_gateway()
        result = gateway.dispatch("skills.list")
        assert "skills" in result

    def test_providers_list(self):
        gateway = get_gateway()
        result = gateway.dispatch("providers.list")
        assert "providers" in result

    def test_unknown_method(self):
        gateway = get_gateway()
        with pytest.raises(ValueError, match="inconnue"):
            gateway.dispatch("unknown.method")

    def test_handle_command(self):
        gateway = get_gateway()
        from ciel.channels import Message
        msg = Message(id="MSG-1", channel="terminal", content="/health", role="user")
        response = gateway.handle_message(msg)
        assert response is not None
        assert '"status"' in response
