"""
CIEL API CLI — Pilote le serveur CIEL via l'API REST.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

console = Console()

API_HOST = os.environ.get("CIEL_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("CIEL_PORT", "8765"))
API_BASE = f"http://{API_HOST}:{API_PORT}/v1"


def _get_token() -> str:
    """Récupère un token d'authentification."""
    cfg_file = Path.home() / ".ciel" / "ciel.json"
    if cfg_file.exists():
        try:
            cfg = json.loads(cfg_file.read_text())
            keys = cfg.get("security", {}).get("api_keys", [])
            if keys:
                r = httpx.post(f"{API_BASE}/auth/token",
                               json={"api_key": keys[0]}, timeout=5)
                if r.is_success:
                    return r.json().get("token", "")
        except Exception:
            pass
    return os.environ.get("CIEL_TOKEN", "")


def _headers() -> dict:
    token = _get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _api_url(path: str) -> str:
    return f"{API_BASE}{path}"


def _get(path: str) -> dict:
    r = httpx.get(_api_url(path), headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def _post(path: str, json_data: dict | None = None,
          params: dict | None = None,
          stream: bool = False) -> dict:
    kwargs = {"headers": _headers(), "params": params, "timeout": 30}
    if json_data is not None:
        kwargs["json"] = json_data
    if stream:
        kwargs["timeout"] = None
    r = httpx.post(_api_url(path), **kwargs)
    if not stream:
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return {}  # streaming handled separately


def _do_chat_stream(body: dict) -> str:
    """Chat en streaming SSE — imprime chaque token au fur et à mesure.

    Retourne le contenu complet une fois le stream terminé.
    """
    full = ""
    with httpx.stream(
        "POST", _api_url("/llm/chat"),
        headers=_headers(), json=body, timeout=None,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
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
                t = data["token"]
                full += t
                sys.stdout.write(t)
                sys.stdout.flush()

            if "done" in data:
                full = data.get("full_content", full)
                break

    console.print()
    return full


# ── Groupes API ──


@click.group(name="api")
def api_group():
    """Interagit avec le serveur CIEL via l'API REST."""


@api_group.command()
def status():
    """État du serveur, provider actif, uptime."""
    try:
        h = _get("/health")
        ac = _get("/llm/active")
    except Exception as e:
        console.print(f"[red]✗ Serveur injoignable sur {API_BASE}: {e}[/]")
        return

    console.print(Panel.fit(
        f"[bold cyan]CIEL v∞.8[/] — [green]✓ En ligne[/]\n\n"
        f"  Uptime      : [yellow]{h.get('uptime', 0):.1f}s[/]\n"
        f"  Modules     : [blue]{h.get('modules_active', '?')}[/] actifs\n"
        f"  Cycles      : [blue]{h.get('cycles', '?')}[/]\n"
        f"  Provider    : [green]{ac.get('provider', '?')}[/]\n"
        f"  Modèle      : [yellow]{ac.get('model', '?')}[/]",
        title="[bold]CIEL Status[/]",
        border_style="cyan",
    ))


@api_group.command(name="providers")
@click.option("--all", "show_all", is_flag=True, help="Afficher tous les providers")
def list_providers(show_all: bool):
    """Liste les fournisseurs LLM."""
    try:
        d = _get("/llm/providers")
    except Exception as e:
        console.print(f"[red]✗ {e}[/]")
        return

    table = Table(box=box.HEAVY_EDGE)
    table.add_column("", width=4)
    table.add_column("Provider", style="cyan")
    table.add_column("Service", style="yellow")
    table.add_column("Mode API")
    table.add_column("Modèles")
    table.add_column("Clé")

    avail = {p["name"] for p in d.get("available", [])}
    providers = d.get("providers", [])
    for p in providers:
        if not show_all and p["name"] not in avail:
            continue
        ok = p["name"] in avail
        icon = "✓" if ok else "✗"
        style = "green" if ok else "red"
        models = ", ".join(p.get("models", [])[:3])
        if len(p.get("models", [])) > 3:
            models += "…"
        key_status = "✓" if ok else "—"
        table.add_row(
            f"[{style}]{icon}[/]",
            p["name"],
            p.get("display_name", ""),
            p.get("api_mode", ""),
            models,
            key_status,
        )
    console.print(table)


@api_group.command()
@click.argument("provider")
@click.argument("model", required=False)
def switch(provider: str, model: str | None):
    """Change de fournisseur/modèle (hot-swap)."""
    body: dict = {"provider": provider}
    if model:
        body["model"] = model
    try:
        r = _post("/llm/provider", json_data=body)
        if r.get("ok"):
            console.print(f"[green]✓[/] Provider: [cyan]{r['provider']}[/] / Modèle: [yellow]{r['model']}[/]")
        else:
            console.print(f"[red]✗ {r.get('error', 'Erreur inconnue')}[/]")
    except Exception as e:
        console.print(f"[red]✗ {e}[/]")


@api_group.command()
@click.argument("key", required=False)
def config(key: str | None):
    """Affiche la configuration (ou une clé spécifique)."""
    try:
        d = _post("/config/build")
    except Exception as e:
        console.print(f"[red]✗ {e}[/]")
        return

    cfg = d.get("result", {}).get("config", d)

    if key:
        parts = key.split(".")
        val: Any = cfg
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                val = None
                break
        if val is not None:
            if isinstance(val, dict):
                console.print_json(json.dumps(val, indent=2, default=str))
            else:
                console.print(f"[cyan]{key}[/] = [yellow]{val}[/]")
        else:
            console.print(f"[red]✗[/] Clé introuvable. Sections: [cyan]api[/], [cyan]llm[/], [cyan]brain[/], [cyan]security[/], etc.")
    else:
        table = Table(box=box.HEAVY_EDGE)
        table.add_column("Section", style="cyan")
        table.add_column("Clés", style="yellow")
        for section, values in sorted(cfg.items()):
            if isinstance(values, dict):
                keys_summary = ", ".join(list(values.keys())[:6])
                if len(values) > 6:
                    keys_summary += "…"
            else:
                keys_summary = str(values)
            table.add_row(section, keys_summary)
        console.print(table)
        console.print("\n[dim]Utilisation: [cyan]ciel api config <section.clé>[/][/dim]")


@api_group.command(name="config-set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Définit une valeur de configuration."""
    try:
        r = _post("/config", params={"key": key, "value": value})
        result = r.get("result", r)
        if result.get("status") == "ok":
            console.print(f"[green]✓[/] [cyan]{key}[/] = [yellow]{value}[/]")
        else:
            console.print(f"[red]✗ {result.get('error', 'Erreur')}[/]")
    except Exception as e:
        console.print(f"[red]✗ {e}[/]")


@api_group.command()
def workflows():
    """Liste les workflows et leur état."""
    try:
        d = _get("/workflow/list")
    except Exception as e:
        console.print(f"[red]✗ {e}[/]")
        return

    wfs = d.get("workflows", d.get("result", []))
    if not wfs:
        console.print("[yellow]Aucun workflow trouvé[/]")
        return

    table = Table(box=box.HEAVY_EDGE)
    table.add_column("Workflow", style="cyan")
    table.add_column("Étapes")
    table.add_column("État")
    table.add_column("Dernière exéc.")
    for w in wfs:
        name = w.get("name", w.get("id", "?"))
        steps = str(len(w.get("steps", w.get("workflow", {}).get("steps", []))))
        status = w.get("status", w.get("state", "?"))
        last_run = w.get("last_run", w.get("updated_at", ""))
        table.add_row(name, steps, status, str(last_run)[:19])
    console.print(table)


@api_group.command()
@click.option("--provider", default="", help="Provider à utiliser")
@click.option("--model", default="", help="Modèle à utiliser")
@click.option("--stream", "-s", is_flag=True, default=False, help="Streaming token par token")
def chat(provider: str, model: str, stream: bool):
    """Chat interactif avec CIEL via l'API."""
    try:
        h = _get("/health")
    except Exception as e:
        console.print(f"[red]✗ Serveur injoignable: {e}[/]")
        return

    console.print(Panel.fit(
        f"[bold cyan]Chat CIEL[/] — [green]{h.get('modules_active', '?')} modules[/]",
        border_style="cyan",
    ))
    msgs: list[dict] = []
    if provider or model:
        console.print(f"[dim]Provider: {provider or 'défaut'} / Modèle: {model or 'défaut'}[/]")

    while True:
        try:
            user_input = console.input("[bold green]▸ vous[/] ")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[cyan]👋[/]")
            break

        text = user_input.strip()
        if not text:
            continue
        if text.lower() in ("exit", "quit", "q"):
            break

        msgs.append({"role": "user", "content": text})

        body: dict = {"messages": msgs}
        if provider:
            body["provider"] = provider
        if model:
            body["model"] = model

        try:
            if stream:
                body["stream"] = True
                full_content = _do_chat_stream(body)
                content = full_content
            else:
                resp = _post("/llm/chat", json_data=body, stream=False)
                content = resp.get("content", json.dumps(resp))
                p_name = resp.get("provider", "")
                m_name = resp.get("model", "")
                console.print(f"[bold cyan]▸ ciel[/] [dim]({p_name}/{m_name})[/]")

            if "```" in content or "#" in content or "**" in content:
                console.print(Markdown(content))
            else:
                console.print(content)

            msgs.append({"role": "assistant", "content": content})
        except Exception as e:
            console.print(f"[red]✗ Erreur: {e}[/]")
            msgs.pop()


if __name__ == "__main__":
    api_group()
