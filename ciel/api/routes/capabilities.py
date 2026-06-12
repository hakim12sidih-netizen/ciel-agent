"""Routes pour les nouvelles capacités : vision, contrôle, sandbox, etc."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette.requests import Request

from ciel.api.tool_registry import TOOL_REGISTRY, get_categories, get_tool_list

router = APIRouter(tags=["capabilities"])


@router.get("/capabilities/tools")
async def capabilities_tools():
    """Retourne le registre complet de tous les outils et capacités CIEL."""
    return TOOL_REGISTRY


@router.get("/capabilities/tools/categories")
async def capabilities_categories():
    """Retourne les catégories d'outils."""
    return get_categories()


@router.get("/capabilities/tools/list")
async def capabilities_tools_list():
    """Retourne la liste plate de tous les outils."""
    return get_tool_list()


class AgentExecuteRequest(BaseModel):
    task: str
    mode: str = "auto"  # auto, simulate, live
    session_id: str = ""


class AgentExecuteResponse(BaseModel):
    success: bool
    output: str = ""
    actions: list[dict] = []
    error: str = ""
    session_id: str = ""


def get_brain(request: Request):
    brain = request.app.state.brain
    if not brain:
        raise HTTPException(503, "CIEL brain not initialized")
    return brain


def _engine_response(name: str, brain, input_data: dict) -> dict:
    engine = brain.get_module(name)
    if not engine:
        raise HTTPException(503, f"{name} engine unavailable")
    result = engine.process(input_data)
    return {"success": True, "result": result}


# ── ToolForge ──

@router.post("/toolforge/forge")
async def tool_forge(name: str, description: str = "",
                     tags: str = "", body: str = "result = None",
                     brain=Depends(get_brain)):
    return _engine_response("toolforge", brain, {
        "action": "forge", "name": name, "description": description,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "body": body,
    })

@router.get("/toolforge/find")
async def tool_find(query: str, brain=Depends(get_brain)):
    return _engine_response("toolforge", brain, {
        "action": "find", "query": query,
    })

@router.post("/toolforge/run/{tool_id}")
async def tool_run(tool_id: str, brain=Depends(get_brain)):
    return _engine_response("toolforge", brain, {
        "action": "run", "tool_id": tool_id,
    })

@router.post("/toolforge/suggest")
async def tool_suggest(problem: str, brain=Depends(get_brain)):
    return _engine_response("toolforge", brain, {
        "action": "suggest", "problem": problem,
    })


# ── Vision ──

@router.post("/vision/screenshot")
async def vision_screenshot(brain=Depends(get_brain)):
    return _engine_response("vision", brain, {"action": "screenshot"})

@router.post("/vision/webcam")
async def vision_webcam(brain=Depends(get_brain)):
    return _engine_response("vision", brain, {"action": "webcam"})

@router.get("/vision/last")
async def vision_last(brain=Depends(get_brain)):
    return _engine_response("vision", brain, {"action": "last"})


# ── Control ──

@router.post("/control/move")
async def control_move(x: int, y: int, brain=Depends(get_brain)):
    return _engine_response("control", brain, {
        "action": "move", "x": x, "y": y,
    })

@router.post("/control/click")
async def control_click(button: str = "left", x: int = 0, y: int = 0,
                        brain=Depends(get_brain)):
    return _engine_response("control", brain, {
        "action": "click", "button": button, "x": x, "y": y,
    })

@router.post("/control/type")
async def control_type(text: str, brain=Depends(get_brain)):
    return _engine_response("control", brain, {
        "action": "type", "text": text,
    })

@router.post("/control/key")
async def control_key(key: str, brain=Depends(get_brain)):
    return _engine_response("control", brain, {
        "action": "key", "key": key,
    })

@router.post("/control/clipboard")
async def control_clipboard(text: str, brain=Depends(get_brain)):
    return _engine_response("control", brain, {
        "action": "clipboard_set", "text": text,
    })

@router.get("/control/clipboard")
async def control_clipboard_get(brain=Depends(get_brain)):
    return _engine_response("control", brain, {"action": "clipboard_get"})

@router.post("/control/live")
async def control_live(enabled: bool, brain=Depends(get_brain)):
    return _engine_response("control", brain, {
        "action": "live_mode", "enabled": enabled,
    })


# ── Sandbox ──

@router.post("/sandbox/run")
async def sandbox_run(code: str, language: str = "python",
                      timeout: int = 30, brain=Depends(get_brain)):
    return _engine_response("sandbox", brain, {
        "action": "run", "code": code,
        "language": language, "timeout": timeout,
    })


# ── Clones ──

@router.post("/clones/spawn")
async def clone_spawn(name: str = "clone", clone_type: str = "worker",
                      task: str = "", brain=Depends(get_brain)):
    return _engine_response("clones", brain, {
        "action": "spawn", "name": name,
        "type": clone_type, "task": task,
    })

@router.get("/clones/list")
async def clone_list(brain=Depends(get_brain)):
    return _engine_response("clones", brain, {"action": "list"})

@router.post("/clones/terminate")
async def clone_terminate(clone_id: str, brain=Depends(get_brain)):
    return _engine_response("clones", brain, {
        "action": "terminate", "clone_id": clone_id,
    })

@router.post("/clones/task")
async def clone_task(clone_id: str, task: str, brain=Depends(get_brain)):
    return _engine_response("clones", brain, {
        "action": "task", "clone_id": clone_id, "task": task,
    })

@router.post("/clones/recall_all")
async def clone_recall_all(brain=Depends(get_brain)):
    return _engine_response("clones", brain, {"action": "recall_all"})


# ── WebSearch ──

@router.get("/web/search")
async def web_search(query: str, max_results: int = 8,
                     brain=Depends(get_brain)):
    return _engine_response("websearch", brain, {
        "action": "search", "query": query, "max": max_results,
    })

@router.post("/web/fetch")
async def web_fetch(url: str, brain=Depends(get_brain)):
    return _engine_response("websearch", brain, {
        "action": "fetch", "url": url,
    })


# ── Database ──

@router.post("/db/init")
async def db_initialize(brain=Depends(get_brain)):
    return _engine_response("database", brain, {"action": "initialize"})

@router.post("/db/register_table")
async def db_register_table(name: str, columns: str, primary_key: str = "id",
                             indexes: str = "", brain=Depends(get_brain)):
    cols = {k.strip(): v.strip() for k, v in
            (pair.split(":") for pair in columns.split(",") if ":" in pair)}
    idx_list = [i.strip() for i in indexes.split(",") if i.strip()]
    return _engine_response("database", brain, {
        "action": "register_table",
        "table_def": {"name": name, "columns": cols,
                       "primary_key": primary_key, "indexes": idx_list},
    })

@router.post("/db/insert")
async def db_insert(table: str, data: str, brain=Depends(get_brain)):
    import json
    parsed = json.loads(data)
    return _engine_response("database", brain, {
        "action": "insert", "table": table, "data": parsed,
    })

@router.get("/db/query")
async def db_query(table: str, filters: str = "{}", limit: int = 100,
                   offset: int = 0, order_by: str = "",
                   brain=Depends(get_brain)):
    import json
    flt = json.loads(filters)
    qdef = {"table": table, "filters": flt, "limit": limit,
            "offset": offset}
    if order_by:
        qdef["order_by"] = order_by
    return _engine_response("database", brain, {
        "action": "query", "query": qdef,
    })

@router.post("/db/update")
async def db_update(table: str, id: str, data: str,
                    brain=Depends(get_brain)):
    import json
    parsed = json.loads(data)
    return _engine_response("database", brain, {
        "action": "update", "table": table, "id": id, "data": parsed,
    })

@router.post("/db/delete")
async def db_delete(table: str, id: str, brain=Depends(get_brain)):
    return _engine_response("database", brain, {
        "action": "delete", "table": table, "id": id,
    })

@router.get("/db/export/{table}")
async def db_export(table: str, brain=Depends(get_brain)):
    return _engine_response("database", brain, {
        "action": "export", "table": table,
    })

@router.get("/db/stats")
async def db_stats(brain=Depends(get_brain)):
    return _engine_response("database", brain, {"action": "stats"})


# ── Config ──

@router.get("/config")
async def config_get(key: str = "", brain=Depends(get_brain)):
    return _engine_response("config", brain,
                            {"action": "get", "key": key})

@router.post("/config")
async def config_set(key: str, value: str = "", brain=Depends(get_brain)):
    import json
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        parsed = value
    return _engine_response("config", brain,
                            {"action": "set", "key": key, "value": parsed})

@router.post("/config/build")
async def config_build(brain=Depends(get_brain)):
    return _engine_response("config", brain, {"action": "build"})

@router.get("/config/stats")
async def config_stats(brain=Depends(get_brain)):
    return _engine_response("config", brain, {"action": "stats"})


# ── Cache ──

@router.get("/cache/{key}")
async def cache_get(key: str, brain=Depends(get_brain)):
    return _engine_response("cache", brain, {"action": "get", "key": key})

@router.post("/cache/{key}")
async def cache_set(key: str, value: str = "", ttl: float = 300.0,
                    brain=Depends(get_brain)):
    import json
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        parsed = value
    return _engine_response("cache", brain,
                            {"action": "set", "key": key,
                             "value": parsed, "ttl": ttl})

@router.delete("/cache/{key}")
async def cache_delete(key: str, brain=Depends(get_brain)):
    return _engine_response("cache", brain,
                            {"action": "delete", "key": key})

@router.post("/cache/clear")
async def cache_clear(brain=Depends(get_brain)):
    return _engine_response("cache", brain, {"action": "clear"})

@router.get("/cache/stats")
async def cache_stats(brain=Depends(get_brain)):
    return _engine_response("cache", brain, {"action": "stats"})


# ── Agent Execution (Control + Sandbox) ──

@router.post("/agent/execute", response_model=AgentExecuteResponse)
async def agent_execute(req: AgentExecuteRequest, request: Request):
    """Exécute une tâche sur l'ordinateur via contrôle souris/clavier + sandbox."""
    import subprocess
    import os
    from pathlib import Path
    from datetime import datetime

    brain = get_brain(request)
    session_id = req.session_id or f"exec_{os.urandom(4).hex()}"
    actions = []

    # 1. LLM planification
    try:
        llm = getattr(request.app.state, "llm_bridge", None)
        if not llm:
            from ciel.llmbridge.core import LLMBridgeEngine
            llm = LLMBridgeEngine()
            request.app.state.llm_bridge = llm
            llm_bridge = llm
        else:
            llm_bridge = llm

        from ciel.llmbridge.providers import OpenAIProvider
        import os as _os
        api_key = _os.environ.get("OPENAI_API_KEY", "")
        provider = OpenAIProvider(api_key=api_key, model="gpt-4o")

        plan_prompt = f"""Tu es CIEL, un assistant capable d'agir sur l'ordinateur.
Tâche: {req.task}
Décompose en actions élémentaires. Réponds en JSON avec une liste d'actions:
{{"actions": [{{"type": "shell|type|click|move|key|sandbox|wait|screenshot|done", "params": {{...}}}}]}}
Actions disponibles:
- shell: exécute une commande shell (params: cmd)
- type: tape du texte (params: text)
- click: clique (params: button, x, y optionnel)
- move: déplace la souris (params: x, y)
- key: presse une touche (params: key)
- sandbox: exécute du code Python isolé (params: code)
- wait: attend (params: seconds)
- screenshot: capture d'écran
- done: tâche terminée

Exemple pour "ouvrir firefox et chercher météo":
{{"actions": [
  {{"type": "shell", "params": {{"cmd": "firefox --new-window 'https://google.com'"}}}},
  {{"type": "wait", "params": {{"seconds": 3}}}},
  {{"type": "done", "params": {{"message": "Firefox ouvert"}}}}
]}}"""

        from ciel.llmbridge.providers import Message as LLMMsg
        import asyncio
        plan_resp = await asyncio.wait_for(
            provider.chat_completion([LLMMsg(role="user", content=plan_prompt)]),
            timeout=30,
        )
        if isinstance(plan_resp, dict):
            plan_text = plan_resp.get("content", str(plan_resp))
        else:
            plan_text = plan_resp.content if hasattr(plan_resp, "content") else str(plan_resp)
    except Exception as e:
        plan_text = f'{{"actions": [{{"type": "done", "params": {{"message": "Erreur planification: {e}"}}}}]}}'

    # Parse le plan
    import json as _json
    try:
        plan = _json.loads(plan_text)
        plan_actions = plan.get("actions", [])
    except Exception:
        plan_actions = [{"type": "done", "params": {"message": f"Plan JSON invalide: {plan_text[:200]}"}}]

    live = req.mode == "live"

    # 2. Exécution
    for action in plan_actions:
        atype = action.get("type", "")
        params = action.get("params", {})

        try:
            if atype == "shell":
                cmd = params.get("cmd", "")
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                output = r.stdout[:500] + (r.stderr[:200] if r.stderr else "")
                actions.append({"type": "shell", "cmd": cmd, "output": output[:200], "returncode": r.returncode})

            elif atype == "type" and live:
                text = params.get("text", "")
                engine = brain.get_module("control")
                if engine:
                    engine.process({"action": "type", "text": text})
                actions.append({"type": "type", "text": text[:100]})

            elif atype == "click" and live:
                button = params.get("button", "left")
                x = params.get("x", 0)
                y = params.get("y", 0)
                engine = brain.get_module("control")
                if engine:
                    engine.process({"action": "click", "button": button, "x": x, "y": y})
                actions.append({"type": "click", "button": button, "x": x, "y": y})

            elif atype == "move" and live:
                x = params.get("x", 0)
                y = params.get("y", 0)
                engine = brain.get_module("control")
                if engine:
                    engine.process({"action": "move", "x": x, "y": y})
                actions.append({"type": "move", "x": x, "y": y})

            elif atype == "key" and live:
                key = params.get("key", "")
                engine = brain.get_module("control")
                if engine:
                    engine.process({"action": "key", "key": key})
                actions.append({"type": "key", "key": key})

            elif atype == "sandbox":
                code = params.get("code", "")
                engine = brain.get_module("sandbox")
                result = {}
                if engine:
                    result = engine.process({"action": "run", "code": code, "language": "python"})
                    if isinstance(result, dict):
                        out = result.get("result", result.get("output", ""))
                        actions.append({"type": "sandbox", "output": str(out)[:300]})
                    else:
                        actions.append({"type": "sandbox", "output": str(result)[:300]})

            elif atype == "wait":
                seconds = int(params.get("seconds", 1))
                import time
                time.sleep(seconds)
                actions.append({"type": "wait", "seconds": seconds})

            elif atype == "screenshot":
                engine = brain.get_module("vision")
                if engine:
                    result = engine.process({"action": "screenshot"})
                    actions.append({"type": "screenshot", "result": str(result)[:200]})
                else:
                    actions.append({"type": "screenshot", "result": "vision engine unavailable"})

            elif atype == "done":
                msg = params.get("message", "Tâche terminée")
                actions.append({"type": "done", "message": msg})
                break

        except Exception as e:
            actions.append({"type": atype, "error": str(e)})

    # 3. Résumé final
    success = all(a.get("error") is None for a in actions if a["type"] not in ("done", "wait"))

    return AgentExecuteResponse(
        success=success,
        output=actions[-1].get("message", actions[-1].get("output", "") if actions else ""),
        actions=actions,
        session_id=session_id,
    )
