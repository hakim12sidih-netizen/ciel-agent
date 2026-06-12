"""
Serveur MCP (Model Context Protocol) pour CIEL.

Expose les capacités CIEL comme outils MCP — utilisable depuis
Claude Desktop, Cursor, et tout client MCP.

Protocol: JSON-RPC 2.0 sur stdio (transport MCP standard).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger("ciel.mcp")

API_HOST = os.environ.get("CIEL_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("CIEL_PORT", "8765"))
API_BASE = f"http://{API_HOST}:{API_PORT}/v1"

_MCP_VERSION = "2025-03-26"
_SERVER_INFO = {"name": "ciel-mcp", "version": "0.1.0"}


def _get_headers() -> dict:
    cfg_file = Path.home() / ".ciel" / "ciel.json"
    if cfg_file.exists():
        try:
            cfg = json.loads(cfg_file.read_text())
            keys = cfg.get("security", {}).get("api_keys", [])
            if keys:
                r = httpx.post(f"{API_BASE}/auth/token",
                               json={"api_key": keys[0]}, timeout=5)
                if r.is_success:
                    return {"Authorization": f"Bearer {r.json()['token']}"}
        except Exception:
            pass
    return {}


def _api(path: str, method: str = "GET",
          json_data: dict | None = None,
          params: dict | None = None) -> dict | list:
    hdrs = _get_headers()
    async_resp = httpx.request(method, f"{API_BASE}{path}",
                                headers=hdrs, json=json_data,
                                params=params, timeout=30)
    async_resp.raise_for_status()
    return async_resp.json()


# ── Définition des outils MCP ──

TOOLS: list[dict] = [
    {
        "name": "ciel_health",
        "description": "Vérifier l'état du serveur CIEL (uptime, modules actifs)",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ciel_chat",
        "description": "Envoyer un message au LLM actif de CIEL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Le message à envoyer"},
                "provider": {"type": "string", "description": "Provider LLM (optionnel)"},
                "model": {"type": "string", "description": "Modèle LLM (optionnel)"},
            },
            "required": ["message"],
        },
    },
    {
        "name": "ciel_providers",
        "description": "Lister les fournisseurs LLM disponibles et leur statut",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ciel_switch_provider",
        "description": "Changer de fournisseur/modèle LLM (hot-swap)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "Nom du provider (ollama, groq, openai…)"},
                "model": {"type": "string", "description": "Nom du modèle (optionnel)"},
            },
            "required": ["provider"],
        },
    },
    {
        "name": "ciel_memory_store",
        "description": "Stocke une information dans la mémoire de CIEL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Contenu à mémoriser"},
                "tags": {"type": "string", "description": "Tags séparés par des virgules (optionnel)"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "ciel_memory_query",
        "description": "Interroge la mémoire de CIEL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Requête de recherche"},
                "limit": {"type": "number", "description": "Nombre max de résultats (défaut: 10)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "ciel_web_search",
        "description": "Effectue une recherche web",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "La recherche à effectuer"},
                "count": {"type": "number", "description": "Nombre de résultats (défaut: 8)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "ciel_web_fetch",
        "description": "Récupère le contenu d'une URL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "L'URL à récupérer"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "ciel_config_get",
        "description": "Lit une valeur de configuration CIEL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Clé de config (ex: llm.default_provider)"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "ciel_workflows",
        "description": "Liste les workflows CIEL et leur état",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ciel_brain_status",
        "description": "État complet du cerveau CIEL (modules, cycles)",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ciel_agent_execute",
        "description": "Exécute une tâche via le système agent CIEL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Description de la tâche à exécuter"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "ciel_voice_speak",
        "description": "Synthèse vocale — convertit du texte en parole",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texte à prononcer"},
                "voice": {"type": "string", "description": "Voix TTS (défaut: fr-FR-HenriNeural)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "ciel_voice_transcribe",
        "description": "Transcrit un fichier audio en texte",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Chemin du fichier audio (wav, mp3)"},
            },
            "required": ["file_path"],
        },
    },
]


async def _call_tool(name: str, args: dict) -> Any:
    """Exécute un outil CIEL et retourne le résultat."""
    try:
        if name == "ciel_health":
            d = _api("/health")
            return f"CIEL en ligne • uptime: {d.get('uptime',0):.0f}s • modules: {d.get('modules_active','?')}"

        elif name == "ciel_chat":
            msgs = [{"role": "user", "content": args["message"]}]
            body = {"messages": msgs, "stream": True}
            if args.get("provider"):
                body["provider"] = args["provider"]
            if args.get("model"):
                body["model"] = args["model"]

            import httpx as _httpx
            full = ""
            async with _httpx.AsyncClient(headers=_get_headers(), timeout=None) as client:
                async with client.stream("POST", f"{API_BASE}/llm/chat", json=body) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if not payload:
                            continue
                        try:
                            data = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        if "token" in data:
                            full += data["token"]
                        if "done" in data:
                            full = data.get("full_content", full)
                            break
            return full

        elif name == "ciel_providers":
            d = _api("/llm/providers")
            avail = {p["name"] for p in d.get("available", [])}
            lines = ["## Fournisseurs LLM CIEL\n"]
            for p in d.get("providers", []):
                ok = "✓" if p["name"] in avail else "✗"
                lines.append(f"- {ok} **{p['display_name']}** (`{p['name']}`) — {p['api_mode']}")
            return "\n".join(lines)

        elif name == "ciel_switch_provider":
            body = {"provider": args["provider"]}
            if args.get("model"):
                body["model"] = args["model"]
            d = _api("/llm/provider", method="POST", json_data=body)
            if d.get("ok"):
                return f"✓ Provider: {d['provider']} / Modèle: {d['model']}"
            return f"✗ {d.get('error', 'Erreur inconnue')}"

        elif name == "ciel_memory_store":
            body = {"content": args["content"]}
            if args.get("tags"):
                body["tags"] = [t.strip() for t in args["tags"].split(",")]
            d = _api("/memory/store", method="POST", json_data=body)
            return f"✓ Mémoire sauvegardée: {d.get('result', {}).get('status', 'ok')}"

        elif name == "ciel_memory_query":
            params = {"query": args["query"], "limit": args.get("limit", 10)}
            d = _api("/memory/query", params=params)
            results = d.get("result", d)
            if isinstance(results, dict):
                items = results.get("results", results.get("items", [results]))
            elif isinstance(results, list):
                items = results
            else:
                items = []
            lines = [f"## Mémoire CIEL: {args['query']}\n"]
            for item in items[:10]:
                if isinstance(item, dict):
                    lines.append(f"- {item.get('content', json.dumps(item))[:200]}")
                else:
                    lines.append(f"- {str(item)[:200]}")
            return "\n".join(lines) if len(lines) > 1 else "Aucun résultat"

        elif name == "ciel_web_search":
            params = {"query": args["query"], "count": args.get("count", 8)}
            d = _api("/web/search", params=params)
            results = d.get("results", d.get("result", []))
            if isinstance(results, dict):
                results = results.get("results", [results])
            lines = [f"## Résultats web: {args['query']}\n"]
            for r in (results if isinstance(results, list) else [results])[:8]:
                if isinstance(r, dict):
                    lines.append(f"- [{r.get('title', '?')}]({r.get('url', '')})")
                else:
                    lines.append(f"- {r}")
            return "\n".join(lines)

        elif name == "ciel_web_fetch":
            d = _api("/web/fetch", method="POST",
                     json_data={"url": args["url"]})
            content = d.get("content", d.get("result", json.dumps(d)))
            return str(content)[:5000]

        elif name == "ciel_config_get":
            d = _api("/config/build", method="POST")
            cfg = d.get("result", {}).get("config", d)
            parts = args["key"].split(".")
            val: Any = cfg
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p)
                else:
                    val = None
                    break
            if val is not None:
                formatted = json.dumps(val, indent=2, default=str)[:2000]
                return f"`{args['key']}` = {formatted}"
            return f"Clé introuvable: {args['key']}"

        elif name == "ciel_workflows":
            d = _api("/workflow/list")
            wfs = d.get("workflows", d.get("result", []))
            if not wfs:
                return "Aucun workflow actif"
            lines = ["## Workflows CIEL\n"]
            for w in wfs[:20]:
                name = w.get("name", w.get("id", "?"))
                steps = len(w.get("steps", w.get("workflow", {}).get("steps", [])))
                status = w.get("status", w.get("state", "?"))
                lines.append(f"- **{name}** — {steps} étapes, état: {status}")
            return "\n".join(lines)

        elif name == "ciel_brain_status":
            d = _api("/brain/status")
            s = d.get("status", d.get("result", d))
            modules = s.get("modules", [])
            return (
                f"## Cerveau CIEL\n\n"
                f"- **Nom**: {s.get('name', 'CIEL')}\n"
                f"- **État**: {s.get('status', '?')}\n"
                f"- **Cycles**: {s.get('cycles', 0)}\n"
                f"- **Modules**: {len(modules)} chargés\n"
                f"- **Uptime**: {s.get('uptime', 0):.0f}s"
            )

        elif name == "ciel_agent_execute":
            d = _api("/agent/execute", method="POST",
                     json_data={"task": args["task"]})
            result = d.get("output", d.get("result", d))
            return str(result)[:5000]

        elif name == "ciel_voice_speak":
            from ciel.interfaces.voice import speak as _voice_speak
            voice = args.get("voice", "fr-FR-HenriNeural")
            _voice_speak(args["text"], voice=voice)
            return f"✓ Synthèse vocale: \"{args['text'][:100]}\""

        elif name == "ciel_voice_transcribe":
            from ciel.interfaces.voice import transcribe as _voice_transcribe
            text = _voice_transcribe(args["file_path"])
            return text if text else "Aucun texte détecté"

        return f"Outil inconnu: {name}"

    except httpx.HTTPStatusError as e:
        return f"Erreur API CIEL ({e.response.status_code}): {e.response.text[:300]}"
    except httpx.RequestError as e:
        return f"Serveur CIEL injoignable sur {API_BASE}: {e}"
    except Exception as e:
        return f"Erreur: {e}\n{traceback.format_exc()[:500]}"


# ── Serveur MCP (JSON-RPC 2.0 sur stdio) ──

def _rpc_error(id: Any, code: int, message: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": id,
                       "error": {"code": code, "message": message}})


def _rpc_result(id: Any, result: Any) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": id, "result": result})


def _rpc_notification(method: str, params: dict | None = None) -> str:
    msg: dict = {"jsonrpc": "2.0", "method": method}
    if params:
        msg["params"] = params
    return json.dumps(msg)


import asyncio


async def _serve_stdio():
    """Boucle principale : lit JSON-RPC sur stdin, écrit sur stdout."""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(
        lambda: protocol, sys.stdin)

    initialized = False
    buf = ""

    while True:
        try:
            chunk = await reader.read(4096)
            if not chunk:
                break
            buf += chunk.decode("utf-8")
        except Exception:
            break

        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            method = msg.get("method", "")
            msg_id = msg.get("id")
            params = msg.get("params", {})

            if method == "initialize":
                capabilities = {"tools": {}, "resources": {}, "prompts": {}}
                resp = {
                    "protocolVersion": _MCP_VERSION,
                    "serverInfo": _SERVER_INFO,
                    "capabilities": capabilities,
                }
                sys.stdout.write(_rpc_result(msg_id, resp) + "\n")
                sys.stdout.flush()
                initialized = True
                sys.stdout.write(
                    _rpc_notification("notifications/initialized") + "\n")
                sys.stdout.flush()

            elif method == "ping":
                sys.stdout.write(_rpc_result(msg_id, {}) + "\n")
                sys.stdout.flush()

            elif method == "tools/list":
                if not initialized:
                    sys.stdout.write(
                        _rpc_error(msg_id, -32000, "Not initialized") + "\n")
                    sys.stdout.flush()
                    continue
                sys.stdout.write(
                    _rpc_result(msg_id, {"tools": TOOLS}) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                if not initialized:
                    sys.stdout.write(
                        _rpc_error(msg_id, -32000, "Not initialized") + "\n")
                    sys.stdout.flush()
                    continue
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                result = await _call_tool(tool_name, tool_args)
                content = [{"type": "text", "text": str(result)}]
                sys.stdout.write(
                    _rpc_result(msg_id, {"content": content,
                                         "isError": False}) + "\n")
                sys.stdout.flush()

            else:
                if msg_id is not None:
                    sys.stdout.write(
                        _rpc_result(msg_id, {}) + "\n")
                    sys.stdout.flush()


async def _main():
    await _serve_stdio()


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()
