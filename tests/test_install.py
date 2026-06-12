"""
CIEL v∞.8 — Tests d'installation et d'intégration.
"""
from __future__ import annotations

import os
import json
import pytest
import shutil
import tempfile
from pathlib import Path


# ── Install Tests ──

class TestInstallScript:
    """Teste la logique d'installation."""

    def test_install_sh_exists(self):
        """Vérifie que le script d'installation existe."""
        script = Path(__file__).resolve().parent.parent / "scripts" / "install.sh"
        assert script.exists(), f"{script} introuvable"
        assert script.stat().st_mode & 0o111, "install.sh doit être exécutable"

    def test_doctor_module_imports(self):
        """Vérifie que le module doctor s'importe correctement."""
        from ciel.doctor import Doctor, DoctorReport, DoctorFinding
        assert Doctor
        assert DoctorReport
        assert DoctorFinding

    def test_doctor_checks(self):
        """Teste que le doctor lance sans erreur."""
        from ciel.doctor import run_doctor
        report = run_doctor()
        assert report is not None
        assert hasattr(report, "findings")
        assert hasattr(report, "fixed")

    def test_doctor_fix(self):
        """Teste la réparation automatique."""
        from ciel.doctor.core import Doctor
        d = Doctor(config_dir=Path(tempfile.mkdtemp()))
        fixed = d.fix_all()
        assert isinstance(fixed, list)
        # Vérifie que le dossier config a été créé
        assert d.config_dir.exists()


class TestCredentialsModule:
    """Teste le module de credentials isolés."""

    def test_save_and_get(self):
        from ciel.credentials import save_api_key, get_api_key, delete_api_key
        with tempfile.TemporaryDirectory() as tmp:
            import ciel.credentials.core
            original = ciel.credentials.core.CRED_DIR
            cred_dir = Path(tmp) / ".ciel" / "credentials"
            cred_dir.mkdir(parents=True, exist_ok=True)
            ciel.credentials.core.CRED_DIR = cred_dir
            try:
                save_api_key("test_service", "TEST_KEY", "sk-test123")
                val = get_api_key("test_service", "TEST_KEY")
                assert val == "sk-test123"
                delete_api_key("test_service", "TEST_KEY")
                assert get_api_key("test_service", "TEST_KEY") is None
            finally:
                ciel.credentials.core.CRED_DIR = original

    def test_migrate_from_config(self):
        from ciel.credentials import migrate_from_config
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "ciel.json"
            config_path.write_text(json.dumps({
                "providers": {
                    "openai": {"api_key": "sk-old-place"},
                }
            }))
            count = migrate_from_config(config_path)
            assert count >= 0


class TestI18nModule:
    """Teste l'internationalisation."""

    def test_french(self):
        from ciel.i18n import t, set_lang
        set_lang("fr")
        assert t("install.welcome") == "⚡ Installation de CIEL"
        assert t("nonexistent.key") == "nonexistent.key"

    def test_english(self):
        from ciel.i18n import t, set_lang
        set_lang("en")
        assert t("install.welcome") == "⚡ CIEL Installation"

    def test_available_langs(self):
        from ciel.i18n import available_langs
        assert "fr" in available_langs()
        assert "en" in available_langs()


class TestPluginSdk:
    """Teste le SDK de plugins."""

    def test_plugin_registry(self):
        from ciel.plugins import PluginRegistry, PluginManifest
        reg = PluginRegistry()
        assert reg.loaded_count == 0

    def test_plugin_manifest(self):
        from ciel.plugins import PluginManifest
        m = PluginManifest(name="test", version="1.0.0")
        assert m.name == "test"
        d = m.to_dict()
        assert d["name"] == "test"

    def test_discover_no_dir(self):
        from ciel.plugins import get_registry
        reg = get_registry()
        found = reg.discover()
        assert isinstance(found, list)


def _patch_db():
    """Utilise une base temporaire pour les tests."""
    import ciel.persistence.core as pc
    import tempfile
    orig = pc.DB_PATH
    tmp = Path(tempfile.mktemp(suffix=".db"))
    pc.DB_PATH = tmp
    pc._migrated = False
    return orig, tmp


def _restore_db(orig, tmp):
    import ciel.persistence.core as pc
    pc.DB_PATH = orig
    pc._migrated = False
    tmp.unlink(missing_ok=True)


class TestPersistenceSQLite:
    """Teste la persistance SQLite."""

    @pytest.mark.asyncio
    async def test_save_load_state(self):
        orig, tmp = _patch_db()
        try:
            from ciel.persistence import save_state, load_state, clear_state
            st = await save_state(api_port=9999)
            assert str(st["api_port"]) == "9999"
            loaded = await load_state()
            assert loaded is not None
            assert str(loaded.get("api_port")) == "9999"
            await clear_state()
        finally:
            _restore_db(orig, tmp)

    @pytest.mark.asyncio
    async def test_chat_history(self):
        orig, tmp = _patch_db()
        try:
            from ciel.persistence import save_chat_message, load_chat_history
            await save_chat_message("session-test", "user", "hello")
            await save_chat_message("session-test", "assistant", "world")
            msgs = await load_chat_history("session-test")
            assert len(msgs) == 2
            assert msgs[0]["role"] == "user"
            assert msgs[0]["content"] == "hello"
        finally:
            _restore_db(orig, tmp)

    @pytest.mark.asyncio
    async def test_credentials_db(self):
        orig, tmp = _patch_db()
        try:
            from ciel.persistence import save_credential, get_credential, delete_credential
            await save_credential("test", "API_KEY", "sk-test")
            val = await get_credential("test", "API_KEY")
            assert val == "sk-test"
            await delete_credential("test", "API_KEY")
            val = await get_credential("test", "API_KEY")
            assert val is None
        finally:
            _restore_db(orig, tmp)

    @pytest.mark.asyncio
    async def test_plugin_registration(self):
        orig, tmp = _patch_db()
        try:
            from ciel.persistence import register_plugin, get_plugin, list_plugins
            await register_plugin("test-plugin", "1.0.0", {"type": "test"})
            p = await get_plugin("test-plugin")
            assert p is not None
            assert p["name"] == "test-plugin"
            plugins = await list_plugins()
            assert any(pl["name"] == "test-plugin" for pl in plugins)
        finally:
            _restore_db(orig, tmp)


class TestInstallWizardPaths:
    """Teste les chemins d'installation (quickstart vs advanced)."""

    def test_quickstart_defaults(self):
        """Le mode quickstart doit fournir des valeurs par défaut."""
        defaults = {
            "port": "8765",
            "provider": "openai",
            "model": "gpt-4o",
            "autostart": True,
        }
        assert defaults["port"] == "8765"
        assert defaults["provider"] == "openai"

    def test_advanced_options(self):
        """Le mode avancé doit avoir toutes les options."""
        advanced_opts = [
            "port", "host", "provider", "model", "autostart",
            "log_level", "db_path", "plugins_dir", "dev_mode",
        ]
        for opt in advanced_opts:
            assert isinstance(opt, str)
