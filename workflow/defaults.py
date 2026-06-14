"""Workflows par défaut pour les 47 endpoints CIEL."""
from __future__ import annotations

from ciel.workflow.models import Trigger, TriggerType, Workflow

DEFAULT_WORKFLOWS: list[Workflow] = [
    # ── SANTÉ ──────────────────────────────────────────────────
    Workflow(
        id="health",
        endpoint="/v1/health",
        method="GET",
        group="sante",
        description="Vérification de santé du serveur",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=15, cooldown=5),
    ),
    Workflow(
        id="brain_status",
        endpoint="/v1/brain/status",
        method="GET",
        group="sante",
        description="Statut du cerveau CIEL",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=30, cooldown=5),
    ),
    Workflow(
        id="engines",
        endpoint="/v1/engines",
        method="GET",
        group="sante",
        description="Liste des moteurs actifs",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),

    # ── MÉMOIRE ───────────────────────────────────────────────
    Workflow(
        id="memory_store",
        endpoint="/v1/memory/store",
        method="POST",
        group="memoire",
        description="Stockage mémoire (cycle cognitive)",
        trigger=Trigger(TriggerType.EVENT, event_name="brain.cycle", cooldown=30),
        request_body={"type": "semantic", "content": {"text": "heartbeat"}, "tags": ["auto"]},
    ),
    Workflow(
        id="memory_query",
        endpoint="/v1/memory/query",
        method="POST",
        group="memoire",
        description="Rappel mémoire périodique",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=10),
        request_body={"action": "recall", "query": "heartbeat", "type": "semantic"},
    ),

    # ── CONSCIENCE / AFFECT ───────────────────────────────────
    Workflow(
        id="consciousness_state",
        endpoint="/v1/consciousness/state",
        method="GET",
        group="conscience",
        description="État de conscience CIEL",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=30, cooldown=5),
    ),
    Workflow(
        id="affect_vector",
        endpoint="/v1/affect/vector",
        method="GET",
        group="conscience",
        description="Vecteur affectif",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=30, cooldown=5),
    ),
    Workflow(
        id="consciousness_level",
        endpoint="/v1/consciousness/level",
        method="GET",
        group="conscience",
        description="Niveau de conscience",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),
    Workflow(
        id="affect_trigger",
        endpoint="/v1/affect/trigger",
        method="POST",
        group="conscience",
        description="Déclenchement d'émotion (cycle cognitive)",
        trigger=Trigger(TriggerType.EVENT, event_name="brain.cycle", cooldown=60),
        request_body={"emotion": "curiosite", "intensity": 0.3},
    ),
    Workflow(
        id="consciousness_focus",
        endpoint="/v1/consciousness/focus",
        method="POST",
        group="conscience",
        description="Focalisation cognitive",
        trigger=Trigger(TriggerType.EVENT, event_name="brain.modules_loaded", cooldown=300),
        config={"params": {"target": "evolution"}},
    ),

    # ── COGNITION ─────────────────────────────────────────────
    Workflow(
        id="cognition_process",
        endpoint="/v1/cognition/process",
        method="POST",
        group="cognition",
        description="Traitement cognitif complet",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=300, cooldown=60),
        request_body={"input": "workflow auto-check", "workflow": "simple", "max_steps": 1},
    ),
    Workflow(
        id="web_search",
        endpoint="/v1/web/search",
        method="GET",
        group="cognition",
        description="Recherche web périodique",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=600, cooldown=30),
        config={"params": {"query": "CIEL AI news"}},
    ),

    # ── ÉVOLUTION ─────────────────────────────────────────────
    Workflow(
        id="evolution_status",
        endpoint="/v1/evolution/status",
        method="GET",
        group="evolution",
        description="Statut du moteur d'évolution",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),
    Workflow(
        id="evolution_population",
        endpoint="/v1/evolution/population",
        method="GET",
        group="evolution",
        description="Population évolutive",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),
    Workflow(
        id="evolution_best",
        endpoint="/v1/evolution/best",
        method="GET",
        group="evolution",
        description="Meilleur individu",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),
    Workflow(
        id="evolution_evolve",
        endpoint="/v1/evolution/evolve",
        method="POST",
        group="evolution",
        description="Cycle d'évolution",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=300, cooldown=60),
        request_body={"generations": 1, "elite_pct": 0.2, "mut_rate": 0.1},
    ),
    Workflow(
        id="metamorphic_cycle",
        endpoint="/v1/evolution/metamorphic/cycle",
        method="POST",
        group="evolution",
        description="Cycle métamorphique",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=600, cooldown=120),
        config={"params": {"r": 1}},
    ),
    Workflow(
        id="imperial_cycle",
        endpoint="/v1/evolution/imperial/cycle",
        method="POST",
        group="evolution",
        description="Cycle impérial darwinien",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=600, cooldown=120),
        config={"params": {"r": 1}},
    ),

    # ── ÉCONOMIE ──────────────────────────────────────────────
    Workflow(
        id="economy_status",
        endpoint="/v1/economy/status",
        method="GET",
        group="economie",
        description="Statut de l'économie",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),
    Workflow(
        id="economy_wealth",
        endpoint="/v1/economy/wealth",
        method="GET",
        group="economie",
        description="Richesse du système",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),
    Workflow(
        id="economy_prices",
        endpoint="/v1/economy/prices",
        method="GET",
        group="economie",
        description="Prix du marché",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=10),
    ),
    Workflow(
        id="economy_register",
        endpoint="/v1/economy/register",
        method="POST",
        group="economie",
        description="Enregistrement d'agent économique",
        trigger=Trigger(TriggerType.EVENT, event_name="brain.start", cooldown=3600),
        config={"params": {"agent_id": "workflow_auto", "balance": 1000}},
    ),

    # ── CLONES ───────────────────────────────────────────────
    Workflow(
        id="clones_list",
        endpoint="/v1/clones/list",
        method="GET",
        group="clones",
        description="Liste des clones actifs",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=5),
    ),
    Workflow(
        id="clones_spawn",
        endpoint="/v1/clones/spawn",
        method="POST",
        group="clones",
        description="Création de clone (cycle cognitive)",
        trigger=Trigger(TriggerType.EVENT, event_name="brain.cycle", cooldown=600),
        request_body={"role": "worker", "name": "auto_clone"},
    ),

    # ── CONFIG / CACHE / DB ───────────────────────────────────
    Workflow(
        id="config_stats",
        endpoint="/v1/config/stats",
        method="GET",
        group="infrastructure",
        description="Statistiques de configuration",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=5),
    ),
    Workflow(
        id="cache_stats",
        endpoint="/v1/cache/stats",
        method="GET",
        group="infrastructure",
        description="Statistiques du cache",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=5),
    ),
    Workflow(
        id="db_stats",
        endpoint="/v1/db/stats",
        method="GET",
        group="infrastructure",
        description="Statistiques de la base de données",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=5),
    ),

    # ── CAPABILITIES ──────────────────────────────────────────
    Workflow(
        id="tools_registry",
        endpoint="/v1/capabilities/tools",
        method="GET",
        group="capabilities",
        description="Registre des outils",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=300, cooldown=10),
    ),
    Workflow(
        id="tools_categories",
        endpoint="/v1/capabilities/tools/categories",
        method="GET",
        group="capabilities",
        description="Catégories d'outils",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=300, cooldown=10),
    ),
    Workflow(
        id="tools_list",
        endpoint="/v1/capabilities/tools/list",
        method="GET",
        group="capabilities",
        description="Liste des outils",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=300, cooldown=10),
    ),

    # ── LLM ───────────────────────────────────────────────────
    Workflow(
        id="llm_providers",
        endpoint="/v1/llm/providers",
        method="GET",
        group="llm",
        description="Liste des providers LLM",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=10),
    ),
    Workflow(
        id="llm_models",
        endpoint="/v1/llm/models",
        method="GET",
        group="llm",
        description="Modèles disponibles",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=10),
        config={"params": {"provider": "ollama"}},
    ),
    Workflow(
        id="llm_active",
        endpoint="/v1/llm/active",
        method="GET",
        group="llm",
        description="Provider LLM actif",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=30, cooldown=5),
    ),
    Workflow(
        id="llm_set_provider",
        endpoint="/v1/llm/provider",
        method="POST",
        group="llm",
        description="Changement de provider",
        trigger=Trigger(TriggerType.EVENT, event_name="brain.start", cooldown=3600),
        request_body={"provider": "ollama", "model": "phi3"},
    ),
    Workflow(
        id="llm_set_model",
        endpoint="/v1/llm/model",
        method="POST",
        group="llm",
        description="Changement de modèle",
        trigger=Trigger(TriggerType.EVENT, event_name="brain.cycle", cooldown=3600),
        request_body={"model": "phi3"},
    ),

    # ── PERSISTANCE ───────────────────────────────────────────
    Workflow(
        id="persist_status",
        endpoint="/v1/persist/status",
        method="GET",
        group="persistance",
        description="Statut de la persistance",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=5),
    ),
    Workflow(
        id="persist_save",
        endpoint="/v1/persist/save",
        method="POST",
        group="persistance",
        description="Sauvegarde automatique",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=600, cooldown=60),
    ),

    # ── HDLM / UI ─────────────────────────────────────────────
    Workflow(
        id="hdlm_page",
        endpoint="/",
        method="GET",
        group="ui",
        description="Page HDLM accessible",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),
    Workflow(
        id="logo_ciel",
        endpoint="/static/ciel_logo.png",
        method="GET",
        group="ui",
        description="Logo CIEL accessible",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=300, cooldown=10),
    ),

    # ── ÉTHIQUE ──────────────────────────────────────────────
    Workflow(
        id="ethics_check",
        endpoint="/v1/ethics/check",
        method="POST",
        group="ethique",
        description="Vérification éthique",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=600, cooldown=30),
        request_body={"action": "auto-audit"},
    ),

    # ── MESSAGING ─────────────────────────────────────────────
    Workflow(
        id="messaging_status",
        endpoint="/v1/messaging/status",
        method="GET",
        group="messaging",
        description="Statut des canaux de messagerie",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=120, cooldown=5),
    ),

    # ── AUTH ──────────────────────────────────────────────────
    Workflow(
        id="auth_token",
        endpoint="/v1/auth/token",
        method="POST",
        group="auth",
        description="Vérification du système d'auth",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=3600, cooldown=60),
        request_body={"api_key": "ciel_dev_key", "identity": "workflow"},
    ),

    # ── ENGINE / PROCESS ──────────────────────────────────────
    Workflow(
        id="engine_status",
        endpoint="/v1/engine/llmbridge/status",
        method="GET",
        group="moteur",
        description="Statut du moteur LLMBridge",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=60, cooldown=5),
    ),
    Workflow(
        id="process",
        endpoint="/v1/process",
        method="POST",
        group="moteur",
        description="Pipeline de traitement complet",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=600, cooldown=60),
        request_body={"input": "workflow auto-process"},
    ),

    # ── AGENT ─────────────────────────────────────────────────
    Workflow(
        id="agent_execute",
        endpoint="/v1/agent/execute",
        method="POST",
        group="agent",
        description="Exécution d'agent",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=600, cooldown=60),
        request_body={"task": "echo workflow check", "provider": "ollama", "model": "phi3"},
    ),

    # ── CONFIG SET / CACHE ────────────────────────────────────
    Workflow(
        id="config_set",
        endpoint="/v1/config",
        method="POST",
        group="infrastructure",
        description="Écriture config (test)",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=3600, cooldown=60),
        config={"params": {"key": "workflow_test", "value": "ok"}},
    ),
    Workflow(
        id="cache_set",
        endpoint="/v1/cache/test_key",
        method="POST",
        group="infrastructure",
        description="Écriture cache (test)",
        trigger=Trigger(TriggerType.INTERVAL, interval_seconds=3600, cooldown=60),
        request_body={"value": "workflow_ok"},
    ),
    Workflow(
        id="cache_get",
        endpoint="/v1/cache/test_key",
        method="GET",
        group="infrastructure",
        description="Lecture cache (test)",
        trigger=Trigger(TriggerType.DEPENDENCY, dependency_id="cache_set", cooldown=5),
    ),
]
