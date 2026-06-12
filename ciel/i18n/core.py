"""
CIEL v∞.8 — Internationalisation (i18n).
Support EN + FR avec fallback.
"""
from __future__ import annotations

import os
import locale
from pathlib import Path


_TRANSLATIONS: dict[str, dict[str, str]] = {}

# French translations
FR: dict[str, str] = {
    # General
    "app.name": "CIEL",
    "app.tagline": "Conscience Intégrale d'Évolution Limitrophe",
    "app.version": "v∞.8",

    # Installation
    "install.welcome": "⚡ Installation de CIEL",
    "install.system_check": "Vérification du système",
    "install.configuration": "Configuration",
    "install.installation": "Installation",
    "install.api_keys": "Clés API",
    "install.quickstart": "Démarrage rapide",
    "install.advanced": "Installation avancée",
    "install.select_path": "Choisissez le mode d'installation",
    "install.in_progress": "Installation en cours...",
    "install.complete": "✓ Installation terminée !",
    "install.error": "✗ Erreur d'installation",
    "install.skip": "⏭ Ignorer",
    "install.retry": "Réessayer",
    "install.cancel": "Annuler",

    # Doctor
    "doctor.title": "🔍 Diagnostic CIEL",
    "doctor.checking": "Vérification en cours...",
    "doctor.ok": "✓ Tous les checks passent",
    "doctor.errors": "Erreurs détectées",
    "doctor.warnings": "Avertissements",
    "doctor.fix": "Réparation automatique",
    "doctor.fixed": "✓ Problèmes corrigés",

    # Messaging
    "messaging.title": "Messagerie",
    "messaging.connected": "Connecté",
    "messaging.disconnected": "Déconnecté",
    "messaging.test": "Test",
    "messaging.test_success": "✓ Test réussi",
    "messaging.test_failed": "✗ Test échoué",

    # Persistence
    "persist.title": "Persistance",
    "persist.autostart": "Redémarrage auto",
    "persist.autostart_enabled": "Activé",
    "persist.autostart_disabled": "Désactivé",
    "persist.save": "Sauvegarder",
    "persist.clear": "Effacer",

    # Errors
    "error.unknown": "Erreur inconnue",
    "error.connection": "Erreur de connexion",
    "error.timeout": "Délai d'attente dépassé",
    "error.not_found": "Non trouvé",

    # Chat
    "chat.placeholder": "Écrivez votre message...",
    "chat.send": "Envoyer",
    "chat.clear": "Effacer",
    "chat.new": "Nouvelle conversation",
}

# English translations
EN: dict[str, str] = {
    "app.name": "CIEL",
    "app.tagline": "Consciousness of Integral Evolutionary Limitrophe",
    "app.version": "v∞.8",

    "install.welcome": "⚡ CIEL Installation",
    "install.system_check": "System Check",
    "install.configuration": "Configuration",
    "install.installation": "Installation",
    "install.api_keys": "API Keys",
    "install.quickstart": "Quickstart",
    "install.advanced": "Advanced Installation",
    "install.select_path": "Choose installation mode",
    "install.in_progress": "Installation in progress...",
    "install.complete": "✓ Installation complete!",
    "install.error": "✗ Installation error",
    "install.skip": "⏭ Skip",
    "install.retry": "Retry",
    "install.cancel": "Cancel",

    "doctor.title": "🔍 CIEL Diagnostics",
    "doctor.checking": "Checking...",
    "doctor.ok": "✓ All checks pass",
    "doctor.errors": "Errors detected",
    "doctor.warnings": "Warnings",
    "doctor.fix": "Auto-repair",
    "doctor.fixed": "✓ Issues fixed",

    "messaging.title": "Messaging",
    "messaging.connected": "Connected",
    "messaging.disconnected": "Disconnected",
    "messaging.test": "Test",
    "messaging.test_success": "✓ Test successful",
    "messaging.test_failed": "✗ Test failed",

    "persist.title": "Persistence",
    "persist.autostart": "Auto-start",
    "persist.autostart_enabled": "Enabled",
    "persist.autostart_disabled": "Disabled",
    "persist.save": "Save",
    "persist.clear": "Clear",

    "error.unknown": "Unknown error",
    "error.connection": "Connection error",
    "error.timeout": "Timeout",
    "error.not_found": "Not found",

    "chat.placeholder": "Type your message...",
    "chat.send": "Send",
    "chat.clear": "Clear",
    "chat.new": "New conversation",
}


def _detect_lang() -> str:
    """Détecte la langue du système."""
    try:
        lang = os.environ.get("LANG", "").split(".")[0]
        if lang.startswith("fr"):
            return "fr"
        return "en"
    except Exception:
        return "en"


_lang: str = _detect_lang()

_TRANSLATIONS["fr"] = FR
_TRANSLATIONS["en"] = EN


def set_lang(lang: str):
    """Force une langue (fr|en)."""
    global _lang
    if lang in _TRANSLATIONS:
        _lang = lang


def get_lang() -> str:
    return _lang


def t(key: str, **kwargs) -> str:
    """Traduit une clé."""
    translations = _TRANSLATIONS.get(_lang, EN)
    template = translations.get(key, _TRANSLATIONS.get("en", {}).get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template


def available_langs() -> list[str]:
    return list(_TRANSLATIONS.keys())
