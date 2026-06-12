"""42 workflows intégrés — DAG steps, agents/sub-agents, situations."""
from __future__ import annotations

from ciel.workflow.models import Situation, Step, StepType, Workflow

BUILTIN_WORKFLOWS: list[Workflow] = []


def api(sid: str, method: str, endpoint: str, desc: str = "",
        body: dict | None = None, params: dict | None = None,
        nxt: list[str] | None = None,
        ok: str = "", fail: str = "", timeout: float = 30.0) -> Step:
    return Step(id=sid, type=StepType.API_CALL, description=desc,
                endpoint=endpoint, method=method,
                body=body, params=params,
                next_steps=nxt, on_success=ok, on_failure=fail, timeout=timeout)


def agent(sid: str, task: str, desc: str = "",
          complex: bool = False, parallel: int = 1,
          nxt: list[str] | None = None, timeout: float = 300.0) -> Step:
    return Step(id=sid, type=StepType.AGENT, description=desc,
                agent_task=task,
                agent_config={"complex": complex, "parallel": parallel},
                next_steps=nxt, timeout=timeout)


def parallel(sid: str, steps: list[str], desc: str = "",
             nxt: list[str] | None = None) -> Step:
    return Step(id=sid, type=StepType.PARALLEL, description=desc,
                parallel_steps=steps, next_steps=nxt)


def condition(sid: str, expr: str, desc: str = "",
              ok: str = "", fail: str = "") -> Step:
    return Step(id=sid, type=StepType.CONDITION, description=desc,
                condition_expr=expr, on_success=ok, on_failure=fail)


def time_sit(seconds: float) -> list[Situation]:
    return [Situation(type="time", interval_seconds=seconds)]


# ════════════════════════════════════════
# 1  Santé
# ════════════════════════════════════════
w = Workflow("health_monitor", "Surveille santé", "sante", situations=time_sit(30))
w.add_step(api("h", "GET", "/v1/health", "Santé", nxt=["b"]))
w.add_step(api("b", "GET", "/v1/brain/status", "Cerveau", nxt=["e"]))
w.add_step(api("e", "GET", "/v1/engines", "Moteurs"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 2  Mémoire
# ════════════════════════════════════════
w = Workflow("memory_audit", "Stocke→rappel", "memoire", situations=time_sit(120))
w.add_step(api("s", "POST", "/v1/memory/store", "Stocke",
               body={"type": "semantic", "content": {"text": "beat"},
                     "tags": ["auto"]}, nxt=["q"]))
w.add_step(api("q", "POST", "/v1/memory/query", "Rappelle",
               body={"action": "recall", "query": "beat", "type": "semantic"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 3  Conscience
# ════════════════════════════════════════
w = Workflow("consciousness_cycle", "Cycle conscience", "conscience", situations=time_sit(60))
w.add_step(api("st", "GET", "/v1/consciousness/state", "État", nxt=["af"]))
w.add_step(api("af", "GET", "/v1/affect/vector", "Affect", nxt=["lv"]))
w.add_step(api("lv", "GET", "/v1/consciousness/level", "Niveau", nxt=["tr"]))
w.add_step(api("tr", "POST", "/v1/affect/trigger", "Émotion",
               body={"emotion": "curiosite", "intensity": 0.3}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 4  Conscience Focus
# ════════════════════════════════════════
w = Workflow("consciousness_focus_wf", "Focus cognitif", "conscience", situations=time_sit(300))
w.add_step(api("f", "POST", "/v1/consciousness/focus", "Focus", params={"target": "evolution"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 5  Cognition agent
# ════════════════════════════════════════
w = Workflow("cognition_agent", "Agent sub-agents", "cognition", situations=time_sit(300))
w.add_step(agent("an",
    "Analyser état CIEL\nVérifier modules\nIdentifier anomalies\n"
    "Proposer optimisations\nCohérence mémoire\nCharge cognitive\n"
    "Latence réponses\nGoulots étranglement",
    "4 sub-agents", True, 4, nxt=["rp"]))
w.add_step(api("rp", "POST", "/v1/cognition/process", "Synthèse",
               body={"input": "analyse", "workflow": "simple", "max_steps": 1}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 6  Cognition WS
# ════════════════════════════════════════
w = Workflow("cognition_ws", "WebSocket ping", "cognition", situations=time_sit(60))
w.add_step(api("ws", "GET", "/v1/health", "Ping WS (health proxy)"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 7  Évolution complète
# ════════════════════════════════════════
w = Workflow("evolution_full", "DAG évolution", "evolution", situations=time_sit(300))
w.add_step(api("st", "GET", "/v1/evolution/status", "Statut", nxt=["ck"]))
w.add_step(condition("ck", "st is not None", "Actif ?",
                     ok="par", fail="fallback"))
w.add_step(parallel("par", ["ev", "pop", "best"], "Évoluer+Pop+Best", nxt=["meta"]))
w.add_step(api("ev", "POST", "/v1/evolution/evolve", "Évoluer",
               body={"generations": 1, "elite_pct": 0.2, "mut_rate": 0.1}))
w.add_step(api("pop", "GET", "/v1/evolution/population", "Population"))
w.add_step(api("best", "GET", "/v1/evolution/best", "Best"))
w.add_step(api("meta", "POST", "/v1/evolution/metamorphic/cycle", "Méta",
               params={"r": 1}, nxt=["imp"]))
w.add_step(api("imp", "POST", "/v1/evolution/imperial/cycle", "Impérial",
               params={"r": 1}))
w.add_step(api("fallback", "GET", "/v1/evolution/population", "Fallback pop"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 8  Économie
# ════════════════════════════════════════
w = Workflow("economy_check", "Marché", "economie", situations=time_sit(120))
w.add_step(api("st", "GET", "/v1/economy/status", "Statut", nxt=["w"]))
w.add_step(api("w", "GET", "/v1/economy/wealth", "Richesse", nxt=["p"]))
w.add_step(api("p", "GET", "/v1/economy/prices", "Prix"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 9  Économie register
# ════════════════════════════════════════
w = Workflow("economy_register_wf", "Enregistrement agent", "economie", situations=time_sit(3600))
w.add_step(api("r", "POST", "/v1/economy/register", "Register",
               params={"agent_id": "wf_eco", "balance": 500}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 10  Économie trade
# ════════════════════════════════════════
w = Workflow("economy_trade_wf", "Échange économique", "economie", situations=time_sit(600))
w.add_step(api("t", "POST", "/v1/economy/trade", "Trade",
               body={"seller": "wf_eco", "buyer": "system",
                     "item": "compute", "price": 10}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 11  Économie regulate
# ════════════════════════════════════════
w = Workflow("economy_regulate_wf", "Régulation", "economie", situations=time_sit(1800))
w.add_step(api("r", "POST", "/v1/economy/regulate", "Réguler",
               body={"action": "adjust_taxes", "rate": 0.05}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 12  ToolForge
# ════════════════════════════════════════
w = Workflow("toolforge_cycle", "Cycle ToolForge", "outils", situations=time_sit(600))
w.add_step(api("reg", "GET", "/v1/capabilities/tools", "Registre", nxt=["cat", "list"]))
w.add_step(api("cat", "GET", "/v1/capabilities/tools/categories", "Catégories"))
w.add_step(api("list", "GET", "/v1/capabilities/tools/list", "Liste"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 13  ToolForge forge
# ════════════════════════════════════════
w = Workflow("toolforge_forge_wf", "Forger outil", "outils", situations=time_sit(3600))
w.add_step(api("f", "POST", "/v1/toolforge/forge", "Forger",
               body={"name": "wf_tool", "description": "auto", "code": "print('ok')"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 14  ToolForge find
# ════════════════════════════════════════
w = Workflow("toolforge_find_wf", "Trouver outil", "outils", situations=time_sit(600))
w.add_step(api("f", "GET", "/v1/toolforge/find", "Trouver", params={"q": "tool"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 15  ToolForge suggest
# ════════════════════════════════════════
w = Workflow("toolforge_suggest_wf", "Suggestion outil", "outils", situations=time_sit(1800))
w.add_step(api("s", "POST", "/v1/toolforge/suggest", "Suggérer",
               body={"task": "analyse", "context": "monitoring"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 16  Vision
# ════════════════════════════════════════
w = Workflow("vision_capture", "Capture vision", "vision", situations=time_sit(600))
w.add_step(api("ss", "POST", "/v1/vision/screenshot", "Screenshot"))
w.add_step(api("last", "GET", "/v1/vision/last", "Dernière capture"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 17  Contrôle
# ════════════════════════════════════════
w = Workflow("control_check", "Test contrôle", "controle", situations=time_sit(600))
w.add_step(api("clip", "POST", "/v1/control/clipboard", "Presse-papier",
               body={"text": "wf_test"}))
w.add_step(api("clip_get", "GET", "/v1/control/clipboard", "Lire presse-papier"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 18  Sandbox
# ════════════════════════════════════════
w = Workflow("sandbox_run", "Exécution sandbox", "sandbox", situations=time_sit(600))
w.add_step(api("run", "POST", "/v1/sandbox/run", "Exécuter",
               body={"language": "python", "code": "print(42)", "timeout": 10}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 19  Clones
# ════════════════════════════════════════
w = Workflow("clone_manager", "Gestion clones", "clones", situations=time_sit(180))
w.add_step(api("list", "GET", "/v1/clones/list", "Lister", nxt=["dec"]))
w.add_step(condition("dec", "list is not None", "Spawn ?", ok="spawn"))
w.add_step(api("spawn", "POST", "/v1/clones/spawn", "Spawn",
               body={"role": "worker", "name": "wf_clone"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 20  Clones task
# ════════════════════════════════════════
w = Workflow("clone_task_wf", "Tâche clone", "clones", situations=time_sit(600))
w.add_step(api("task", "POST", "/v1/clones/task", "Task",
               body={"task": "analyse", "target": "system"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 21  Web search
# ════════════════════════════════════════
w = Workflow("web_search_wf", "Recherche web", "web", situations=time_sit(600))
w.add_step(api("s", "GET", "/v1/web/search", "Chercher", params={"query": "CIEL AI"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 22  Web fetch
# ════════════════════════════════════════
w = Workflow("web_fetch_wf", "Fetch web", "web", situations=time_sit(600))
w.add_step(api("f", "POST", "/v1/web/fetch", "Fetch",
               body={"url": "https://example.com"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 23  Database — parallèle
# ════════════════════════════════════════
w = Workflow("db_health", "Santé DB", "database", situations=time_sit(300))
w.add_step(api("st", "GET", "/v1/db/stats", "Stats DB"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 24  Database CRUD
# ════════════════════════════════════════
w = Workflow("db_crud", "CRUD DB", "database", situations=time_sit(3600))
w.add_step(api("init", "POST", "/v1/db/init", "Init", body={}))
w.add_step(api("reg", "POST", "/v1/db/register_table", "Register",
               body={"table": "wf_test", "schema": {"id": "INTEGER", "val": "TEXT"}},
               nxt=["ins"]))
w.add_step(api("ins", "POST", "/v1/db/insert", "Insert",
               body={"table": "wf_test", "data": {"id": 1, "val": "hello"}},
               nxt=["q"]))
w.add_step(api("q", "GET", "/v1/db/query", "Query",
               params={"table": "wf_test", "where": "id=1"}, nxt=["up"]))
w.add_step(api("up", "POST", "/v1/db/update", "Update",
               body={"table": "wf_test", "where": "id=1",
                     "data": {"val": "world"}}, nxt=["del"]))
w.add_step(api("del", "POST", "/v1/db/delete", "Delete",
               body={"table": "wf_test", "where": "id=1"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 25  Config
# ════════════════════════════════════════
w = Workflow("config_check", "Config système", "infrastructure", situations=time_sit(120))
w.add_step(api("st", "GET", "/v1/config/stats", "Stats"))
w.add_step(api("cfg", "GET", "/v1/config", "Config"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 26  Config set
# ════════════════════════════════════════
w = Workflow("config_set_wf", "Écriture config", "infrastructure", situations=time_sit(3600))
w.add_step(api("set", "POST", "/v1/config", "Set",
               params={"key": "wf_key", "value": "wf_val"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 27  Cache
# ════════════════════════════════════════
w = Workflow("cache_check", "Cache R/W", "infrastructure", situations=time_sit(120))
w.add_step(api("st", "GET", "/v1/cache/stats", "Stats"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 28  Cache CRUD
# ════════════════════════════════════════
w = Workflow("cache_crud", "Cache CRUD", "infrastructure", situations=time_sit(3600))
w.add_step(api("set", "POST", "/v1/cache/wf_key", "Set",
               body={"value": "wf_val"}, nxt=["get"]))
w.add_step(api("get", "GET", "/v1/cache/wf_key", "Get", nxt=["del"]))
w.add_step(api("del", "DELETE", "/v1/cache/wf_key", "Delete"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 29  LLM providers
# ════════════════════════════════════════
w = Workflow("llm_check", "Vérification LLM", "llm", situations=time_sit(120))
w.add_step(api("pr", "GET", "/v1/llm/providers", "Providers", nxt=["md", "ac"]))
w.add_step(api("md", "GET", "/v1/llm/models", "Modèles", params={"provider": "ollama"}))
w.add_step(api("ac", "GET", "/v1/llm/active", "Actif"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 30  LLM set
# ════════════════════════════════════════
w = Workflow("llm_set_wf", "Changement LLM", "llm", situations=time_sit(3600))
w.add_step(api("pr", "POST", "/v1/llm/provider", "Provider",
               body={"provider": "ollama", "model": "phi3"}, nxt=["md"]))
w.add_step(api("md", "POST", "/v1/llm/model", "Modèle",
               body={"model": "phi3"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 31  LLM chat
# ════════════════════════════════════════
w = Workflow("llm_chat_wf", "Chat LLM", "llm", situations=time_sit(600))
w.add_step(api("ch", "POST", "/v1/llm/chat", "Chat",
               body={"message": "Hello CIEL", "provider": "ollama", "model": "phi3"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 32  Persistance
# ════════════════════════════════════════
w = Workflow("persist_check", "Persistance", "persistance", situations=time_sit(300))
w.add_step(api("st", "GET", "/v1/persist/status", "Statut"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 33  Persistance save
# ════════════════════════════════════════
w = Workflow("persist_save_wf", "Sauvegarde", "persistance", situations=time_sit(600))
w.add_step(api("sv", "POST", "/v1/persist/save", "Save"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 34  UI
# ════════════════════════════════════════
w = Workflow("ui_health", "Interface HDLM", "ui", situations=time_sit(60))
w.add_step(parallel("par", ["hdlm", "logo"], "UI+Logo"))
w.add_step(api("hdlm", "GET", "/", "HDLM"))
w.add_step(api("logo", "GET", "/static/ciel_logo.png", "Logo"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 35  Éthique
# ════════════════════════════════════════
w = Workflow("ethics_audit", "Audit éthique", "ethique", situations=time_sit(600))
w.add_step(api("ch", "POST", "/v1/ethics/check", "Vérif",
               body={"action": "auto-audit"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 36  Messaging
# ════════════════════════════════════════
w = Workflow("messaging_check", "Messagerie", "messaging", situations=time_sit(120))
w.add_step(api("st", "GET", "/v1/messaging/status", "Statut"))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 37  Messaging platforms
# ════════════════════════════════════════
w = Workflow("messaging_platforms_wf", "Plateformes", "messaging", situations=time_sit(3600))
w.add_step(api("tel", "POST", "/v1/messaging/telegram/test", "Telegram test",
               body={"message": "WF test"}))
w.add_step(api("disc", "POST", "/v1/messaging/discord/test", "Discord test",
               body={"message": "WF test"}))
w.add_step(api("slack", "POST", "/v1/messaging/slack/test", "Slack test",
               body={"message": "WF test"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 38  Moteur
# ════════════════════════════════════════
w = Workflow("engine_health", "Moteurs CIEL", "moteur", situations=time_sit(60))
w.add_step(api("eng", "GET", "/v1/engine/llmbridge/status", "LLMBridge", nxt=["proc"]))
w.add_step(api("proc", "POST", "/v1/process", "Pipeline",
               body={"input": "health check"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 39  Auth
# ════════════════════════════════════════
w = Workflow("auth_check", "Authentification", "auth", situations=time_sit(3600))
w.add_step(api("tk", "POST", "/v1/auth/token", "Token",
               body={"api_key": "ciel_dev_key", "identity": "wf"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 40  Agent complexe
# ════════════════════════════════════════
w = Workflow("agent_complex_task", "Agent sub-agents", "agent", situations=time_sit(600))
w.add_step(agent("main",
    "Analyser métriques\nCharge CPU\nMémoire\nConnexions\n"
    "Erreurs récentes\nRapport santé\nActions correctives\nMaintenance",
    "6 sub-agents", True, 6, nxt=["rp"]))
w.add_step(api("rp", "POST", "/v1/agent/execute", "Rapport",
               body={"task": "rapport final", "provider": "ollama", "model": "phi3"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 41  Agent simple
# ════════════════════════════════════════
w = Workflow("agent_simple_wf", "Agent simple", "agent", situations=time_sit(300))
w.add_step(api("ex", "POST", "/v1/agent/execute", "Exécuter",
               body={"task": "echo test", "provider": "ollama", "model": "phi3"}))
BUILTIN_WORKFLOWS.append(w)

# ════════════════════════════════════════
# 42  Infrastructure — DB + Config + Cache parallèle
# ════════════════════════════════════════
w = Workflow("infra_health", "Infra parallèle", "infrastructure", situations=time_sit(120))
w.add_step(parallel("par", ["db_st", "cfg_st", "cache_st"], "DB+Config+Cache"))
w.add_step(api("db_st", "GET", "/v1/db/stats", "DB"))
w.add_step(api("cfg_st", "GET", "/v1/config/stats", "Config"))
w.add_step(api("cache_st", "GET", "/v1/cache/stats", "Cache"))
BUILTIN_WORKFLOWS.append(w)
