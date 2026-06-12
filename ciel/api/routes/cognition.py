"""Routes et moteur pour le workflow agentique CIEL.
Workflow obligatoire : Question → Réflexion → Plan → Outils → Réponse.
"""
from __future__ import annotations

import json
import uuid
import re
import subprocess
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.requests import Request

from ciel.api.models import (
    AffectTriggerRequest, AffectVectorResponse, ConsciousnessStateResponse,
)
from ciel.api.tool_registry import WORKFLOW_TOOLS_PROMPT

router = APIRouter(tags=["cognition"])


class ProcessRequest(BaseModel):
    input: str
    session_id: str = ""
    provider: str = "openai"
    model: str = ""
    workflow: str = "strict"  # strict | simple
    max_steps: int = 10


class ProcessResponse(BaseModel):
    output: str
    thinking: str = ""
    plan: list[str] = []
    actions: list[dict] = []
    session_id: str
    provider: str
    model: str
    timestamp: str


def get_brain(request: Request):
    brain = request.app.state.brain
    if not brain:
        raise HTTPException(503, "CIEL brain not initialized")
    return brain


def _get_provider(provider_name: str = "openai", model_name: str = ""):
    from ciel.llmbridge.providers import (
        OpenAIProvider, GeminiProvider, AnthropicProvider,
    )
    import os

    configs = {
        "openai":    (OpenAIProvider,    "OPENAI_API_KEY",    "gpt-4o",            ""),
        "google":    (GeminiProvider,    "GOOGLE_API_KEY",    "gemini-2.0-flash",  ""),
        "anthropic": (AnthropicProvider, "ANTHROPIC_API_KEY", "claude-3-5-sonnet-latest", ""),
        "deepseek":  (OpenAIProvider,    "DEEPSEEK_API_KEY",  "deepseek-chat",     "https://api.deepseek.com/v1/chat/completions"),
        "mistral":   (OpenAIProvider,    "MISTRAL_API_KEY",   "mistral-large-latest", "https://api.mistral.ai/v1/chat/completions"),
        "groq":      (OpenAIProvider,    "GROQ_API_KEY",      "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1/chat/completions"),
        "ollama":    (OpenAIProvider,    "",                  "llama3.2",          "http://localhost:11434/v1/chat/completions"),
    }

    entry = configs.get(provider_name)
    if not entry:
        raise HTTPException(400, f"Provider inconnu: {provider_name}")
    cls, env_key, default_model, base_url = entry
    api_key = os.environ.get(env_key, "") if env_key else ""
    model = model_name or default_model
    return cls(api_key=api_key, model=model, base_url=base_url)


# ── Système de workflow agentique ──

WORKFLOW_PROMPT = """Tu es CIEL, un assistant cognitif avec accès à des outils.
Tu dois OBLIGATOIREMENT suivre ce workflow pour CHAQUE question:

## Étape 1 : Réfléchis (<thinking>)
Analyse la question, décompose-la, identifie ce qui est nécessaire.
Format: <thinking>ta réflexion ici</thinking>

## Étape 2 : Planifie (<plan>)
Décompose la tâche en étapes concrètes avec les outils nécessaires.
Format: <plan><step>outil: description</step><step>...</step></plan>

## Étape 3 : Exécute (<tool>)
Utilise UN outil à la fois. Attends le résultat avant de continuer.
Format: <tool nom="outil">{"param": "valeur"}</tool>

## Étape 4 : Continue ou réponds
- Si le plan n'est pas fini, répète étape 3
- Si le plan est fini, réponds en français normalement

Outils disponibles:
- shell: {"cmd": "commande bash"} — Exécute une commande système
- sandbox: {"code": "python code"} — Exécute du Python isolé
- type: {"text": "texte"} — Tape au clavier
- click: {"button": "left|right", "x": 0, "y": 0} — Clique souris
- move: {"x": 100, "y": 200} — Déplace la souris
- key: {"key": "enter"} — Presse une touche
- screenshot: {} — Capture d'écran
- notify: {"title": "...", "message": "..."} — Notification
- clipboard: {} — Lit le presse-papier
- clipboard_set: {"text": "..."} — Écrit dans le presse-papier
- browse: {"url": "https://..."} — Ouvre une URL
- search: {"query": "..."} — Cherche sur le web
- wait: {"seconds": 2} — Attend

EXEMPLE:
User: ouvre la météo de Paris
Assistant:
<thinking>L'utilisateur veut voir la météo de Paris. Je dois ouvrir un navigateur et chercher.</thinking>
<plan><step>shell: ouvrir Firefox sur une recherche météo</step><step>search: obtenir la météo</step></plan>
<tool nom="shell">{"cmd": "firefox --new-window 'https://www.google.com/search?q=m%C3%A9t%C3%A9o+Paris'"}</tool>
Résultat: Firefox ouvert.
<thinking>Firefox est ouvert avec la recherche météo. La tâche est terminée.</thinking>
Voici la météo de Paris ! Le navigateur est ouvert sur la recherche.

IMPORTANT: N'oublie JAMAIS les balises. Commence TOUJOURS par <thinking>."""


# ── Outils ──

async def _execute_tool(tool_name: str, params: dict, brain=None) -> dict:
    result = {"tool": tool_name, "params": params, "success": True, "output": ""}
    try:
        if tool_name == "shell":
            cmd = params.get("cmd", "")
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            result["output"] = (r.stdout + r.stderr)[:2000]
            result["returncode"] = r.returncode

        elif tool_name == "sandbox":
            code = params.get("code", "")
            engine = brain.get_module("sandbox") if brain else None
            if engine:
                r = engine.process({"action": "run", "code": code, "language": "python"})
                result["output"] = str(r)[:2000]
            else:
                result["output"] = "sandbox non disponible"

        elif tool_name in ("type", "click", "move", "key"):
            engine = brain.get_module("control") if brain else None
            if engine:
                action_map = {
                    "type": {"action": "type", "text": params.get("text", "")},
                    "click": {"action": "click", "button": params.get("button", "left"), "x": params.get("x", 0), "y": params.get("y", 0)},
                    "move": {"action": "move", "x": params.get("x", 0), "y": params.get("y", 0)},
                    "key": {"action": "key", "key": params.get("key", "")},
                }
                r = engine.process(action_map[tool_name])
                result["output"] = str(r)[:1000]
            else:
                result["output"] = "contrôle non disponible (pip install pyautogui)"

        elif tool_name == "screenshot":
            engine = brain.get_module("vision") if brain else None
            if engine:
                engine.process({"action": "screenshot"})
                result["output"] = "capture effectuée"
            else:
                result["output"] = "vision non disponible"

        elif tool_name == "notify":
            engine = brain.get_module("control") if brain else None
            if engine:
                engine.process({"action": "notify", "title": params.get("title", "CIEL"), "message": params.get("message", "")})
            result["output"] = "notification envoyée"

        elif tool_name == "clipboard":
            engine = brain.get_module("control") if brain else None
            if engine:
                r = engine.process({"action": "clipboard_get"})
                result["output"] = str(r)[:1000]
            else:
                result["output"] = "presse-papier non accessible"

        elif tool_name == "clipboard_set":
            engine = brain.get_module("control") if brain else None
            if engine:
                engine.process({"action": "clipboard_set", "text": params.get("text", "")})
            result["output"] = "écrit dans le presse-papier"

        elif tool_name == "browse":
            url = params.get("url", "https://google.com")
            subprocess.Popen(["xdg-open", url], start_new_session=True)
            result["output"] = f"ouvert: {url}"

        elif tool_name == "search":
            try:
                from duckduckgo_search import DDGS
                query = params.get("query", "")
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                result["output"] = json.dumps(
                    [{"title": r["title"], "body": r["body"][:300]} for r in results],
                    ensure_ascii=False,
                )[:3000]
            except Exception as e:
                result["output"] = f"recherche impossible: {e}"

        elif tool_name == "wait":
            seconds = int(params.get("seconds", 1))
            time.sleep(seconds)
            result["output"] = f"attente {seconds}s"

        else:
            result["success"] = False
            result["output"] = f"outil inconnu: {tool_name}"

    except subprocess.TimeoutExpired:
        result["success"] = False
        result["output"] = "temps dépassé (30s)"
    except Exception as e:
        result["success"] = False
        result["output"] = str(e)[:1000]

    return result


# ── Parsing du workflow ──

_RE_THINKING = re.compile(r'<thinking>(.*?)</thinking>', re.DOTALL)
_RE_PLAN = re.compile(r'<plan>(.*?)</plan>', re.DOTALL)
_RE_STEP = re.compile(r'<step>(.*?)</step>', re.DOTALL)
_RE_TOOL = re.compile(r'<tool\s+nom=["\'](\w+)["\']\s*>(.*?)</tool>', re.DOTALL)


def _extract_thinking(text: str) -> str:
    m = _RE_THINKING.search(text)
    return m.group(1).strip() if m else ""


def _extract_plan(text: str) -> list[str]:
    m = _RE_PLAN.search(text)
    if m:
        return [s.strip() for s in _RE_STEP.findall(m.group(1))]
    return []


def _extract_tool(text: str) -> tuple[str, dict] | None:
    m = _RE_TOOL.search(text)
    if m:
        try:
            params = json.loads(m.group(2).strip())
        except json.JSONDecodeError:
            params = {"raw": m.group(2).strip()}
        return m.group(1), params
    return None


def _strip_tags(text: str) -> str:
    return _RE_TOOL.sub('', _RE_THINKING.sub('', _RE_PLAN.sub('', text))).strip()


# ── Moteur du workflow strict ──

async def _run_workflow(provider, llm_msgs: list, brain=None, max_steps: int = 10) -> tuple[str, str, list[str], list[dict]]:
    from ciel.llmbridge.providers import Message as LLMMsg
    import asyncio

    all_thinking = []
    all_plan = []
    all_actions = []

    for turn in range(max_steps):
        resp = await asyncio.wait_for(provider.chat_completion(llm_msgs), timeout=60)
        content = resp.content if hasattr(resp, "content") else (resp.get("content", str(resp)) if isinstance(resp, dict) else str(resp))

        # Extraction
        thinking = _extract_thinking(content)
        plan = _extract_plan(content)
        tool = _extract_tool(content)
        response_text = _strip_tags(content)

        if thinking:
            all_thinking.append(thinking)
        if plan:
            all_plan = plan

        if tool is None:
            # Plus d'outils → réponse finale
            final = response_text or content
            if not final and all_thinking:
                final = all_thinking[-1]
            return final, "\n".join(all_thinking), all_plan, all_actions

        # Exécute l'outil
        tool_name, tool_params = tool
        result = await _execute_tool(tool_name, tool_params, brain)
        all_actions.append(result)

        result_text = result.get("output", "")[:2000]
        if not result["success"]:
            result_text = f"ERREUR: {result_text}"

        # Ajoute au contexte
        llm_msgs.append(LLMMsg(role="assistant", content=content))
        llm_msgs.append(LLMMsg(role="user", content=f"Résultat de {tool_name}: {result_text}\n\nContinue le plan ou réponds si terminé."))

    return "Maximum d'étapes atteint.", "\n".join(all_thinking), all_plan, all_actions


async def _run_simple(provider, llm_msgs: list, brain=None, max_steps: int = 5) -> tuple[str, str, list[str], list[dict]]:
    """Workflow simple : pas de réflexion/plan obligatoire, juste outils."""
    from ciel.llmbridge.providers import Message as LLMMsg
    import asyncio

    all_actions = []

    for turn in range(max_steps):
        resp = await asyncio.wait_for(provider.chat_completion(llm_msgs), timeout=60)
        content = resp.content if hasattr(resp, "content") else (resp.get("content", str(resp)) if isinstance(resp, dict) else str(resp))

        tool = _extract_tool(content)
        if tool is None:
            return content, "", [], all_actions

        tool_name, tool_params = tool
        result = await _execute_tool(tool_name, tool_params, brain)
        all_actions.append(result)

        result_text = result.get("output", "")[:2000]
        if not result["success"]:
            result_text = f"ERREUR: {result_text}"

        llm_msgs.append(LLMMsg(role="assistant", content=content))
        llm_msgs.append(LLMMsg(role="user", content=f"Résultat: {result_text}\nContinue."))

    return "Maximum d'étapes atteint.", "", [], all_actions


# ── API Endpoints ──

@router.post("/cognition/process", response_model=ProcessResponse)
async def cognition_process(req: ProcessRequest, request: Request):
    """Traite avec workflow obligatoire question→réflexion→plan→outils→réponse."""
    session_id = req.session_id or f"web_{uuid.uuid4().hex[:12]}"

    try:
        provider = _get_provider(req.provider, req.model)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erreur provider: {e}")

    from ciel.llmbridge.providers import Message as LLMMsg
    from ciel.persistence import load_chat_history, save_chat_message

    history = await load_chat_history(session_id, limit=10) if session_id else []

    system = WORKFLOW_TOOLS_PROMPT if req.workflow == "strict" else (
        "Tu es CIEL, assistant cognitif. Utilise <tool nom=\"outil\">{\"param\":\"valeur\"}</tool> pour agir."
    )

    llm_msgs = [LLMMsg(role="system", content=system)]
    for h in history:
        role = h.get("role", "user")
        if role in ("user", "assistant"):
            llm_msgs.append(LLMMsg(role=role, content=h.get("content", "")))
    llm_msgs.append(LLMMsg(role="user", content=req.input))

    try:
        if req.workflow == "strict":
            output, thinking, plan, actions = await _run_workflow(provider, llm_msgs, get_brain(request), req.max_steps)
        else:
            output, thinking, plan, actions = await _run_simple(provider, llm_msgs, get_brain(request), req.max_steps)
    except Exception as e:
        output, thinking, plan, actions = f"Erreur: {e}", "", [], []

    await save_chat_message(session_id, "user", req.input)
    await save_chat_message(session_id, "assistant", output)

    return ProcessResponse(
        output=output,
        thinking=thinking,
        plan=plan,
        actions=actions,
        session_id=session_id,
        provider=req.provider,
        model=getattr(provider, "model", req.model or ""),
        timestamp=datetime.now().isoformat(),
    )


@router.websocket("/cognition/ws")
async def cognition_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = f"ws_{uuid.uuid4().hex[:12]}"
    provider_name = "openai"
    workflow_mode = "strict"
    provider = None

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "config":
                provider_name = msg.get("provider", "openai")
                workflow_mode = msg.get("workflow", "strict")
                try:
                    provider = _get_provider(provider_name, msg.get("model", ""))
                    await websocket.send_text(json.dumps({
                        "type": "config_ok", "provider": provider_name,
                        "model": getattr(provider, "model", "") if provider else "",
                    }))
                except Exception as e:
                    await websocket.send_text(json.dumps({"type": "error", "message": f"Provider: {e}"}))
                continue

            if msg.get("type") != "message":
                continue

            user_input = msg.get("text", "")
            if not user_input:
                continue

            from ciel.llmbridge.providers import Message as LLMMsg
            system = WORKFLOW_TOOLS_PROMPT if workflow_mode == "strict" else (
                "Tu es CIEL. Utilise <tool nom=\"outil\">params JSON</tool> pour agir."
            )
            llm_msgs = [LLMMsg(role="system", content=system), LLMMsg(role="user", content=user_input)]

            try:
                from ciel.persistence import save_chat_message
                await save_chat_message(session_id, "user", user_input)
            except Exception:
                pass

            if provider is None:
                try:
                    provider = _get_provider(provider_name)
                except Exception as e:
                    await websocket.send_text(json.dumps({"type": "error", "message": f"Provider: {e}"}))
                    continue

            brain = getattr(websocket.app.state, "brain", None)
            try:
                output, thinking, plan, actions = await _run_workflow(provider, llm_msgs, brain)

                await websocket.send_text(json.dumps({
                    "type": "response", "content": output,
                    "thinking": thinking, "plan": plan, "actions": actions,
                    "session_id": session_id, "provider": provider_name,
                    "model": getattr(provider, "model", ""),
                }))

                try:
                    await save_chat_message(session_id, "assistant", output)
                except Exception:
                    pass
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))

    except WebSocketDisconnect:
        pass
    except Exception:
        pass


# ── Routes cognition existantes ──

@router.get("/consciousness/state", response_model=ConsciousnessStateResponse)
async def consciousness_state(brain=Depends(get_brain)):
    engine = brain.get_module("conscience")
    if not engine:
        raise HTTPException(503, "consciousness engine unavailable")
    result = engine.process({"action": "state"})
    level = "none"
    awareness = 0.0
    qualia = {}
    if isinstance(result, dict):
        level = result.get("level", "none")
        awareness = result.get("awareness", 0.0)
        qualia = result.get("qualia", {})
    return ConsciousnessStateResponse(level=level, awareness=awareness, qualia=qualia)


@router.get("/affect/vector", response_model=AffectVectorResponse)
async def affect_vector(brain=Depends(get_brain)):
    engine = brain.get_module("animus") or brain.get_module("affect")
    if not engine:
        raise HTTPException(503, "affect engine unavailable")
    result = engine.process({"action": "vector"})
    if isinstance(result, dict):
        vec = result.get("vector", result)
        return AffectVectorResponse(
            dominant=vec.get("dominant", "neutral"),
            intensity=vec.get("intensity", 0.0),
            valence=vec.get("valence", 0.0),
            arousal=vec.get("arousal", 0.0),
            all_emotions=vec.get("all", {}),
        )
    return AffectVectorResponse(dominant="neutral", all_emotions={})


@router.post("/affect/trigger")
async def affect_trigger(req: AffectTriggerRequest, brain=Depends(get_brain)):
    engine = brain.get_module("animus") or brain.get_module("affect")
    if not engine:
        raise HTTPException(503, "affect engine unavailable")
    result = engine.process({"action": "trigger", "emotion": req.emotion, "intensity": req.intensity})
    return {"success": True, "result": result}


@router.get("/consciousness/level")
async def consciousness_level(brain=Depends(get_brain)):
    engine = brain.get_module("conscience")
    if not engine:
        return {"level": "unknown"}
    result = engine.process({"action": "level"})
    return result if isinstance(result, dict) else {"level": str(result)}


@router.post("/consciousness/focus")
async def consciousness_focus(target: str, brain=Depends(get_brain)):
    engine = brain.get_module("conscience")
    if not engine:
        raise HTTPException(503, "consciousness engine unavailable")
    result = engine.process({"action": "focus", "target": target})
    return {"success": True, "result": result}
