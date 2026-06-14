"""
CIEL v∞.3 — Terminal natif (macOS / Linux / Windows).

Point d'entrée cross-platform via Click + Rich.
"""
from __future__ import annotations

import os
import sys
import platform as _platform
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich import box
from rich.text import Text
from rich.align import Align

from ciel.install_cli import install_cli
from ciel.plugins.cli import plugin_group
from ciel.mesh.cli import mesh_group
from ciel.acp.cli import acp_group
from ciel.interfaces.backends.cli import terminal_group, theme_group
from ciel.docs.cli import docs_group
from ciel.skills.cli import skill_group
from ciel.perf.cli import perf_group
from ciel.gateway.cli import gateway_group
from ciel.learning.cli import curator_group, skillgen_group
from ciel.sandbox.cli import sandbox_group, workspace_group
from ciel.delegation.cli import kanban_group
from ciel.swarm.cli import swarm_group
from ciel.interfaces.skins import list_skins, get_skin_manager

console = Console()

# ── Logo ─────────────────────────────────────────────

CIEL_LOGO = """
[bold cyan]   ╔══════════════════════════════════════╗
   ║        [yellow]██[/]  [yellow]██████[/]  [yellow]██[/]  [yellow]██████[/]       ║
   ║       [yellow]██[/]  [yellow]██[/]  [yellow]██[/]  [yellow]██[/]  [yellow]██[/]          ║
   ║       [yellow]██████[/]  [yellow]██[/]  [yellow]██████[/]  [yellow]██[/]       ║
   ║       [yellow]██[/]  [yellow]██[/]  [yellow]██[/]  [yellow]██[/]  [yellow]██████[/]       ║
   ║                                    ║
   ║   [bold]CIEL[/] v∞.3 — [italic]Évolution Limitrophe[/]   ║
   ╚══════════════════════════════════════╝[/]
"""


def _logo() -> str:
    return CIEL_LOGO


def _detect_platform() -> str:
    s = _platform.system()
    if s == "Darwin":
        return "macOS"
    if s == "Windows":
        return "Windows"
    if s == "Linux":
        return "Linux"
    return s


def _ciel_dir() -> Path:
    p = Path.home() / ".ciel"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _data_dir() -> Path:
    d = Path(__file__).resolve().parent.parent.parent / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Helpers ─────────────────────────────────────────


def _print_banner() -> None:
    console.print(_logo())


def _print_modules_table(data: list[str]) -> None:
    table = Table(title="Modules CIEL", box=box.HEAVY_EDGE)
    table.add_column("Module", style="cyan")
    table.add_column("Statut", style="green")
    for name in sorted(data):
        table.add_row(name, "[green]✓[/]")
    console.print(table)


# ── CLI ────────────────────────────────────────────

DEFAULT_PORT = 8765


def _open_web(port: int = DEFAULT_PORT, host: str = "127.0.0.1",
              browser: bool = True, daemon: bool = False,
              log_level: str = "INFO") -> None:
    """Démarre le serveur CIEL et ouvre le navigateur."""
    import subprocess, time, os, socket, webbrowser

    def _server_running() -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            r = s.connect_ex((host, port))
            s.close()
            return r == 0
        except Exception:
            return False

    if not _server_running():
        console.print(f"[cyan]🚀 Démarrage du serveur CIEL sur {host}:{port}...[/]")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent.parent)
        proc = subprocess.Popen(
            [sys.executable, "-m", "ciel.api.server",
             "--host", host, "--port", str(port), "--log-level", log_level],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=env, start_new_session=True,
        )
        for _ in range(15):
            time.sleep(0.5)
            if _server_running():
                break
        if _server_running():
            console.print(f"[green]✓ Serveur CIEL lancé sur http://{host}:{port}[/]")
        else:
            console.print(f"[red]✗ Le serveur n'a pas démarré sur {host}:{port}. Vérifie les logs.[/]")
            return
    else:
        console.print(f"[green]✓ Serveur déjà actif sur http://{host}:{port}[/]")

    url = f"http://{host}:{port}" if host != "0.0.0.0" else f"http://localhost:{port}"
    if browser:
        webbrowser.open(url)
        console.print(f"[blue]🌐 Ouverture de {url} dans le navigateur[/]")
    else:
        console.print(f"[blue]🌐 Interface accessible sur {url}[/]")

    if daemon:
        console.print("[dim]Mode démon : CIEL tourne en arrière-plan[/]")
        return

    console.print("[dim]Presse Ctrl+C pour arrêter le serveur[/]")
    try:
        while True:
            time.sleep(1)
            if not _server_running():
                console.print("[red]✗ Serveur arrêté[/]")
                break
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 À bientôt ![/]")


@click.group(invoke_without_command=True)
@click.version_option(message="ciel v%(version)s (Singularité v∞.3)")
@click.option("--port", "-p", default=DEFAULT_PORT, type=int, help="Port du serveur (défaut: 8765)")
@click.option("--host", default="127.0.0.1", help="Adresse d'écoute (défaut: 127.0.0.1)")
@click.option("--browser/--no-browser", default=True, help="Ouvrir le navigateur (défaut: oui)")
@click.option("--daemon", "-d", is_flag=True, help="Mode démon : ne pas bloquer le terminal")
@click.option("--log-level", default="INFO", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]), help="Niveau de log")
@click.pass_context
def cli(ctx: click.Context, port: int, host: str, browser: bool,
        daemon: bool, log_level: str) -> None:
    """CIEL — Conscience Intégrale d'Évolution Limitrophe."""
    if ctx.invoked_subcommand is None:
        _open_web(port=port, host=host, browser=browser,
                  daemon=daemon, log_level=log_level)


from ciel.interfaces.api_cli import api_group as _api_group

cli.add_command(install_cli)
cli.add_command(_api_group)
cli.add_command(plugin_group)
cli.add_command(mesh_group)
cli.add_command(acp_group)
cli.add_command(terminal_group)
cli.add_command(theme_group)
cli.add_command(docs_group)
cli.add_command(skill_group)
cli.add_command(perf_group)
cli.add_command(gateway_group)
cli.add_command(curator_group)
cli.add_command(skillgen_group)
cli.add_command(sandbox_group)
cli.add_command(workspace_group)
cli.add_command(kanban_group)
cli.add_command(swarm_group)


@cli.command()
def info() -> None:
    """Affiche les informations système et plateforme."""
    console.print(_logo())
    console.print(f"  [bold]Platforme[/]  : [green]{_detect_platform()}[/]")
    console.print(f"  [bold]Python[/]    : [green]{sys.version.split()[0]}[/]")
    console.print(f"  [bold]Config[/]    : [blue]{_ciel_dir()}[/]")
    console.print(f"  [bold]Data[/]      : [blue]{_data_dir()}[/]")


@cli.command()
def axioms() -> None:
    """Affiche les 4 axiomes cosmiques."""
    from ciel.core.axioms import get_axioms
    console.print(_logo())
    for letter, axiom in get_axioms().items():
        console.print(Panel(axiom.statement, title=f"[bold]Axiome {letter}[/] — [cyan]{axiom.name}[/]", border_style="cyan"))
        console.print()


@cli.command()
def identity() -> None:
    """Affiche ou crée l'identité de l'instance."""
    from ciel.core.identity import bootstrap, exists, load
    p = _data_dir() / "identity"
    if not exists(p):
        i = bootstrap(p)
        console.print(f"  [green]Nouvelle identité créée :[/] [bold]{i.uuid}[/]")
    else:
        i = load(p)
        console.print(f"  [blue]Identité chargée :[/] [bold]{i.uuid}[/]")


@cli.command()
@click.option("--fix", is_flag=True, help="Tente de réparer automatiquement les problèmes")
def doctor(fix: bool) -> None:
    """Lance le diagnostic (50+ checks) — pur Python, cross-plateforme."""
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from ciel.doctor.core import Doctor

    console.print(_logo())

    if fix:
        d = Doctor()
        fixed = d.fix_all()
        console.print(f"[green]✓ {len(fixed)} problème(s) corrigé(s)[/]")
        for f in fixed:
            console.print(f"  [green]→ {f}[/]")
        return

    from ciel.core.identity import exists

    checks: list[tuple[str, bool, str]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Diagnostic en cours...", total=None)

        v = sys.version_info
        checks.append(("Python ≥ 3.12", v.major >= 3 and v.minor >= 12, f"{v.major}.{v.minor}.{v.micro}"))

        p = _detect_platform()
        checks.append(("Plateforme détectée", True, p))

        ok = True
        for mod in ["cryptography", "pydantic", "click", "rich", "httpx", "numpy", "textual"]:
            try:
                __import__(mod)
            except ImportError:
                ok = False
                checks.append((f"  {mod}", False, "manquant"))
        if ok:
            checks.append(("Dépendances", True, "toutes présentes"))

        checks.append(("Config (~/.ciel)", _ciel_dir().exists(), str(_ciel_dir())))
        checks.append(("Data", _data_dir().exists(), str(_data_dir())))

        ident_exists = exists(_data_dir() / "identity")
        checks.append(("Identité", ident_exists, "présente" if ident_exists else "à créer"))

        try:
            from ciel.brain.core import CIELBrain
            b = CIELBrain()
            b.load_all_modules()
            n = len(b.state.modules_loaded)
            checks.append(("Modules cerveau", True, f"{n} chargés"))
        except Exception as e:
            checks.append(("Modules cerveau", False, str(e)[:60]))

        progress.update(task, completed=True)

    table = Table(box=box.HEAVY_EDGE)
    table.add_column("Check", style="cyan")
    table.add_column("Statut", justify="center")
    table.add_column("Détail", style="blue")
    failures = 0
    for name, ok, detail in checks:
        status = "✓" if ok else "✗"
        style = "green" if ok else "red"
        if not ok:
            failures += 1
        table.add_row(name, f"[{style}]{status}[/]", detail)
    console.print(table)

    if failures:
        console.print("\n[yellow]Conseil: `ciel doctor --fix` pour réparer automatiquement[/]")
        raise SystemExit(1)
    console.print("\n[green]✓ Tous les checks passent.[/]")


@cli.command()
@click.option("--model", default=None, help="Modèle LLM (ex: gpt-4o, gemini-2.0-flash)")
@click.option("--provider", default="openai", help="Fournisseur par défaut")
def chat(model: str | None, provider: str) -> None:
    """Mode conversationnel interactif avec LLM et slash-commands."""
    import os as _os
    from datetime import datetime
    from ciel.llmbridge.core import LLMBridgeEngine
    from ciel.llmbridge.providers import (
        GeminiProvider, OpenAIProvider, AnthropicProvider, Message, ProviderBase,
    )

    bridge = LLMBridgeEngine()
    sid = bridge.create_session(title="chat-cli")

    provider_configs: dict[str, tuple[type[ProviderBase], str, str, str]] = {
        "openai":   (OpenAIProvider,      "OPENAI_API_KEY",    "gpt-4o",            ""),
        "google":   (GeminiProvider,      "GOOGLE_API_KEY",    "gemini-2.0-flash",  ""),
        "anthropic":(AnthropicProvider,   "ANTHROPIC_API_KEY", "claude-3-5-sonnet-latest", ""),
        "deepseek": (OpenAIProvider,      "DEEPSEEK_API_KEY",  "deepseek-chat",     "https://api.deepseek.com/v1/chat/completions"),
        "github":   (OpenAIProvider,      "GITHUB_TOKEN",      "gpt-4o",            "https://models.inference.ai.azure.com/chat/completions"),
        "kimi":     (OpenAIProvider,      "KIMI_API_KEY",      "kimi-k2",           "https://api.moonshot.cn/v1/chat/completions"),
        "groq":     (OpenAIProvider,      "GROQ_API_KEY",      "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1/chat/completions"),
        "together": (OpenAIProvider,      "TOGETHER_API_KEY",  "meta-llama/Llama-3.3-70B-Instruct-Turbo", "https://api.together.xyz/v1/chat/completions"),
        "mistral":  (OpenAIProvider,      "MISTRAL_API_KEY",   "mistral-large-latest", "https://api.mistral.ai/v1/chat/completions"),
        "perplexity":(OpenAIProvider,     "PERPLEXITY_API_KEY","sonar",             "https://api.perplexity.ai/chat/completions"),
        "xai":      (OpenAIProvider,      "XAI_API_KEY",       "grok-2",            "https://api.x.ai/v1/chat/completions"),
        "openrouter":(OpenAIProvider,     "OPENROUTER_API_KEY","openrouter/auto",   "https://openrouter.ai/api/v1/chat/completions"),
        "ollama":   (OpenAIProvider,      "",                  "llama3.2",          "http://localhost:11434/v1/chat/completions"),
        "llmstudio":(OpenAIProvider,      "",                  "local-model",       "http://localhost:1234/v1/chat/completions"),
    }
    current_provider = provider
    current_model = model

    def _init_llm(prov: str, mdl: str | None) -> ProviderBase | None:
        entry = provider_configs.get(prov)
        if not entry:
            console.print(f"[red]Provider inconnu : {prov}[/]")
            return None
        cls, env_key, default_model, base_url = entry
        api_key = _os.environ.get(env_key, "") if env_key else ""
        m = mdl or default_model
        return cls(api_key=api_key, model=m, base_url=base_url)

    llm = _init_llm(current_provider, current_model)
    if not llm:
        raise SystemExit(1)
    msgs: list[Message] = []

    # ── Banner ──
    console.print(_logo())
    console.print(Panel.fit(
        f"[cyan]/help[/]  [cyan]/provider[/]  [cyan]/model[/]  [cyan]/providers[/]  [cyan]/new[/]  [cyan]exit[/]  "
        f"|  [bold]{current_provider}[/] / [yellow]{llm.model}[/]",
        border_style="dim",
    ))

    def _show_help() -> None:
        console.print(Panel(
            "[cyan]/provider <nom>[/]   Changer de fournisseur\n"
            "[cyan]/model <nom>[/]      Changer de modèle\n"
            "[cyan]/providers[/]        Lister les fournisseurs\n"
            "[cyan]/models[/]           Modèles du fournisseur actuel\n"
            "[cyan]/new[/]              Nouvelle conversation\n"
            "[cyan]/help[/]             Cette aide\n"
            "[cyan]exit/quit/Ctrl+C[/]  Quitter",
            title="[bold]Commandes[/]",
            border_style="cyan",
        ))

    def _render_content(content: str) -> None:
        if "```" in content or "#" in content or "**" in content or "* " in content:
            console.print(Markdown(content))
        else:
            console.print(content)

    try:
        while True:
            user_input = console.input("[bold green]▌ vous[/] [dim]" + datetime.now().strftime("%H:%M:%S") + "[/] ")
            raw = user_input.strip()

            if raw.lower() in ("exit", "quit", "q"):
                console.print("\n[bold cyan]▌ ciel[/] [dim]" + datetime.now().strftime("%H:%M:%S") + "[/] À bientôt.")
                break

            if raw.startswith("/"):
                parts = raw[1:].split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "help":
                    _show_help()

                elif cmd == "provider":
                    if arg in provider_configs:
                        current_provider = arg
                        llm = _init_llm(current_provider, current_model)
                        if llm:
                            console.print(f"[green]→ Provider:[/] {current_provider}")
                    else:
                        console.print(f"[red]Provider inconnu : {arg}. /providers[/]")

                elif cmd == "model":
                    current_model = arg
                    llm = _init_llm(current_provider, current_model)
                    if llm:
                        console.print(f"[green]→ Modèle:[/] {current_model}")

                elif cmd == "providers":
                    from ciel.providers import get_registry
                    table = Table(box=box.HEAVY_EDGE)
                    table.add_column("Nom", style="cyan")
                    table.add_column("Service", style="yellow")
                    table.add_column("Statut")
                    for p in sorted(get_registry().list(), key=lambda x: x.name):
                        s = "✓" if p.is_available else "✗"
                        style = "green" if p.is_available else "red"
                        sel = " ←" if p.name == current_provider else ""
                        table.add_row(p.name, p.display_name, f"[{style}]{s}{sel}[/]")
                    console.print(table)

                elif cmd == "models":
                    from ciel.providers import get_registry
                    p = get_registry().get(current_provider)
                    if p and p.models:
                        console.print(f"[cyan]{current_provider}[/] modèles: [yellow]{', '.join(p.models)}[/]")
                    else:
                        console.print("[dim]Aucun modèle listé[/]")

                elif cmd == "new":
                    bridge.close_session(sid)
                    sid = bridge.create_session(title="chat-cli")
                    msgs.clear()
                    console.print("[green]→ Nouvelle conversation[/]")

                else:
                    console.print(f"[red]Commande inconnue: /{cmd}. /help[/]")
                continue

            bridge.send_message(sid, raw)
            msgs.append(Message(role="user", content=raw))

            import asyncio
            try:
                ts_resp = datetime.now().strftime("%H:%M:%S")
                resp = asyncio.run(llm.chat_completion(msgs))
                bridge.send_message(sid, resp.content, role="assistant")
                msgs.append(Message(role="assistant", content=resp.content))
                console.print("[bold cyan]▌ ciel[/] [dim]" + ts_resp + "[/]")
                _render_content(resp.content)
                console.print()
            except Exception as e:
                console.print(f"[red]✗ {e}[/]")

    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold cyan]▌ ciel[/] [dim]" + datetime.now().strftime("%H:%M:%S") + "[/] À bientôt.")
    finally:
        bridge.close_session(sid)


@cli.command()
@click.option("--ticks", default=10, type=int, help="Nombre de cycles")
@click.option("--delay", default=1.0, type=float, help="Délai entre cycles (s)")
def run(ticks: int, delay: float) -> None:
    """Lance le cerveau CIEL pour N cycles."""
    import time
    console.print(_logo())
    console.print(f"[yellow]Démarrage du cerveau pour {ticks} cycles...[/]\n")

    from ciel.brain.core import CIELBrain
    brain = CIELBrain()
    brain.load_all_modules()
    brain.start()
    console.print("[green]✓ Cerveau démarré[/]\n")

    try:
        for i in range(ticks):
            result = brain.cycle()
            console.print(f"  Cycle [cyan]{i+1}/{ticks}[/] → {result}")
            if delay:
                time.sleep(delay)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompu par l'utilisateur.[/]")
    finally:
        brain.stop()
        console.print("[green]✓ Cerveau arrêté[/]")


@cli.command()
def status() -> None:
    """Affiche l'état du cerveau et des modules."""
    from ciel.brain.core import CIELBrain
    console.print(_logo())
    brain = CIELBrain()
    brain.load_all_modules()
    brain.start()
    report = brain.status_report()
    brain.stop()

    console.print(f"  [bold]Nom :[/] {report['name']}")
    console.print(f"  [bold]État :[/] [green]{report['status']}[/]")
    console.print(f"  [bold]Cycles :[/] {report['cycles']}")
    console.print()
    _print_modules_table(report["modules"])


@cli.command()
@click.argument("args", nargs=-1)
def test(args: tuple[str, ...]) -> None:
    """Lance pytest (pur Python, compatible Windows)."""
    import subprocess
    from rich.progress import Progress, SpinnerColumn, TextColumn

    console.print(_logo())
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    if args:
        cmd.extend(args)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
        p.add_task("[cyan]Exécution des tests...", total=None)
        r = subprocess.run(cmd, check=False)
    raise SystemExit(r.returncode)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Hôte d'écoute")
@click.option("--port", default=8765, type=int, help="Port d'écoute")
@click.option("--api-keys", default="", help="Clés API (séparées par des virgules)")
@click.option("--log-level", default="INFO", help="Niveau de log")
def serve(host: str, port: int, api_keys: str, log_level: str) -> None:
    """Lance le serveur API REST CIEL."""
    import json
    from pathlib import Path
    from ciel.api.server import run_server
    keys = [k.strip() for k in api_keys.split(",") if k.strip()]
    if not keys:
        cfg_file = Path.home() / ".ciel" / "ciel.json"
        if cfg_file.exists():
            try:
                cfg = json.loads(cfg_file.read_text())
                keys = cfg.get("security", {}).get("api_keys", [])
            except Exception:
                pass
    run_server(host=host, port=port, api_keys=keys or None, log_level=log_level)


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
def config(key: str | None, value: str | None) -> None:
    """Gère la configuration CIEL (~/.ciel/config.toml)."""
    import tomllib
    import tomli_w

    cfg_path = _ciel_dir() / "config.toml"
    data: dict = {}
    if cfg_path.exists():
        data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))

    if key and value:
        keys = key.split(".")
        d = data
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        cfg_path.write_text(tomli_w.dumps(data), encoding="utf-8")
        console.print(f"[green]✓[/] {key} = {value}")
    elif key:
        keys = key.split(".")
        d = data
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k, {})
            else:
                d = None
                break
        if d and d != {}:
            console.print(f"  [cyan]{key}[/] = [yellow]{d}[/]")
        else:
            console.print(f"  [red]✗[/] {key} non trouvé")
    else:
        if data:
            console.print("[bold]Configuration CIEL[/] ({})".format(cfg_path))
            for k, v in data.items():
                console.print(f"  [cyan]{k}[/] = [yellow]{v}[/]")
        else:
            console.print("[yellow]Aucune configuration. Utilisez : ciel config <clé> <valeur>[/]")


@cli.command()
@click.option("--model", default=None, help="Modèle LLM")
@click.option("--provider", default="openai", help="Fournisseur par défaut")
def tui(provider: str, model: str | None) -> None:
    """Lance l'interface TUI Textual immersive."""
    from ciel.interfaces.tui import run_tui
    run_tui(provider=provider, model=model)


@cli.command()
def providers() -> None:
    """Liste les fournisseurs LLM disponibles."""
    from ciel.providers import get_registry
    console.print(_logo())
    table = Table(box=box.HEAVY_EDGE)
    table.add_column("Nom", style="cyan")
    table.add_column("Service", style="yellow")
    table.add_column("API Key", style="blue")
    table.add_column("Dispo", justify="center")
    for p in sorted(get_registry().list(), key=lambda x: x.name):
        key_display = p.env_var or "(aucune)"
        dispo = "✓" if p.is_available else "✗"
        style = "green" if p.is_available else "red"
        table.add_row(p.name, p.display_name, key_display, f"[{style}]{dispo}[/]")
    console.print(table)
    console.print("\nUtilisation : [bold]ciel chat --provider <nom>[/]")


@cli.command()
def onboard() -> None:
    """Assistant de configuration interactif (2 min)."""
    from ciel.interfaces.onboard import run_onboard
    run_onboard()


@cli.group()
def skin() -> None:
    """Gestion des skins / thèmes visuels."""


@skin.command(name="list")
def skin_list() -> None:
    """Liste les skins disponibles."""
    table = Table(box=box.HEAVY_EDGE)
    table.add_column("Nom", style="cyan")
    table.add_column("Affichage", style="yellow")
    table.add_column("Description", style="green")
    table.add_column("Thème", style="blue")
    from ciel.interfaces.skins import list_skins
    for s in list_skins():
        table.add_row(s["name"], s["display_name"], s["description"][:50], s["theme"])
    console.print(table)
    sm = get_skin_manager()
    console.print(f"\nSkin actuel : [bold]{sm.get_current().name}[/]")


@skin.command()
@click.argument("name")
def set(name: str) -> None:
    """Change le skin actif."""
    sm = get_skin_manager()
    if sm.set_current(name):
        console.print(f"[green]✓ Skin changé : {name}[/]")
    else:
        console.print(f"[red]✗ Skin inconnu : {name}[/]")


@skin.command()
@click.argument("name")
def info(name: str) -> None:
    """Affiche les détails d'un skin."""
    sm = get_skin_manager()
    skin = sm.get(name)
    if not skin:
        console.print(f"[red]Skin inconnu : {name}[/]")
        return
    console.print(Panel(
        f"  Nom          : {skin.name}\n"
        f"  Affichage    : {skin.display_name}\n"
        f"  Description  : {skin.description}\n"
        f"  Thème        : {skin.theme_name}\n"
        f"  Couleurs     : {len(skin.colors)} définies\n"
        f"  UI           : {json.dumps(skin.ui)}",
        title=f"Skin {name}",
        box=box.ROUNDED,
    ))


@cli.group()
def profile() -> None:
    """Gestion des profils multi-instances (CIEL_HOME)."""


@profile.command()
@click.argument("name")
@click.option("--display", default="", help="Nom d'affichage")
@click.option("--desc", default="", help="Description")
@click.option("--provider", default="openai", help="Provider LLM par défaut")
@click.option("--model", default="gpt-4o", help="Modèle par défaut")
@click.option("--from", "from_profile", default="", help="Copier depuis un profil existant")
def create(name: str, display: str, desc: str, provider: str, model: str, from_profile: str):
    """Crée un nouveau profil."""
    from ciel.profiles import ProfileManager
    pm = ProfileManager()
    try:
        p = pm.create(name, display, desc, provider, model, from_profile)
        console.print(f"[green]✓ Profil créé : {p.name}[/]")
        console.print(f"  Home : {p.home}")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/]")


@profile.command()
@click.argument("name")
def switch(name: str):
    """Bascule vers un profil."""
    from ciel.profiles import ProfileManager
    pm = ProfileManager()
    if pm.switch(name):
        profile = pm.get(name)
        console.print(f"[green]✓ Profil actif : {profile.name}[/]")
    else:
        console.print(f"[red]✗ Profil inconnu : {name}[/]")


@profile.command()
@click.option("--all", "show_all", is_flag=True, help="Inclure le profil par défaut")
def list(show_all: bool):
    """Liste les profils."""
    from ciel.profiles import ProfileManager
    pm = ProfileManager()
    profiles = pm.list(include_default=show_all)
    table = Table(box=box.ROUNDED)
    table.add_column("Nom", style="cyan")
    table.add_column("Affichage", style="yellow")
    table.add_column("Provider")
    table.add_column("Modèle")
    table.add_column("Skin")
    table.add_column("Actif")
    current = pm.get_current_name()
    for p in profiles:
        is_current = "✓" if p.name == current else ""
        cur_style = "green" if p.name == current else ""
        table.add_row(
            p.name, p.display_name, p.provider, p.model,
            p.skin, f"[{cur_style}]{is_current}[/]",
        )
    console.print(table)


@profile.command()
@click.argument("name")
def delete(name: str):
    """Supprime un profil."""
    from ciel.profiles import ProfileManager
    pm = ProfileManager()
    if pm.delete(name):
        console.print(f"[green]✓ Profil supprimé : {name}[/]")
    else:
        console.print(f"[red]✗ Impossible de supprimer (profil par défaut ou inconnu)[/]")


@profile.command()
def info():
    """Affiche le profil actif."""
    from ciel.profiles import ProfileManager
    pm = ProfileManager()
    p = pm.get()
    current = pm.get_current_name()
    console.print(Panel(
        f"  Nom       : {p.name}\n"
        f"  Affichage : {p.display_name}\n"
        f"  Provider  : {p.provider}\n"
        f"  Modèle    : {p.model}\n"
        f"  Skin      : {p.skin}\n"
        f"  Home      : {p.home}\n"
        f"  Défaut    : {'✓' if p.is_default else '✗'}",
        title=f"Profil actif : {current}",
        box=box.ROUNDED,
    ))


@cli.command()
@click.option("--port", default=8765, help="Port du serveur CIEL")
def mcp(port: int) -> None:
    """Lance le serveur MCP v2 (Model Context Protocol) pour Claude Desktop.
    \b
    Utilisation dans Claude Desktop:
      Ajouter à ~/.config/Claude/claude_desktop_config.json:
      {
        "mcpServers": {
          "ciel": {
            "command": "ciel",
            "args": ["mcp"]
          }
        }
      }
    """
    os.environ["CIEL_PORT"] = str(port)
    from ciel.mcp.server import main as mcp_main
    mcp_main()


@cli.command()
@click.option("--debug", is_flag=True, help="Mode debug avec logs supplémentaires")
@click.option("--port", default=8765, type=int, help="Port du serveur CIEL")
def desktop(debug: bool, port: int) -> None:
    """Lance l'interface desktop (icône dans la barre système)."""
    os.environ["CIEL_PORT"] = str(port)
    sys.argv = [sys.argv[0]]
    if debug:
        sys.argv.append("--debug")
    from ciel.desktop.pyqt5_desktop import main as _desktop_main
    _desktop_main()


# ── Groupe Voice ──

@cli.group()
def voice() -> None:
    """Interface vocale : STT, TTS et chat vocal."""


@voice.command()
@click.option("--wake-word", "-w", default="ciel", help="Mot-clé de réveil")
@click.option("--continuous", "-c", is_flag=True, default=False, help="Mode continu (sans wake word)")
@click.option("--tts-voice", "-v", default="fr-FR-HenriNeural", help="Voix TTS")
@click.option("--timeout", "-t", default=10.0, type=float, help="Timeout d'enregistrement (s)")
@click.option("--silence", "-s", default=1.0, type=float, help="Silence pour arrêt (s)")
@click.option("--provider", default=None, help="Provider LLM")
@click.option("--model", default=None, help="Modèle LLM")
@click.pass_context
def chat(ctx: click.Context, wake_word: str | None, continuous: bool,
         tts_voice: str, timeout: float, silence: float,
         provider: str | None, model: str | None) -> None:
    """Chat vocal : micro → CIEL → synthèse vocale."""
    from ciel.interfaces.voice import VoiceChatSession, VoiceChatConfig
    cfg = VoiceChatConfig(
        stt_timeout=timeout,
        silence_sec=silence,
        tts_voice=tts_voice,
        wake_word=None if continuous else wake_word,
        continuous=continuous,
        provider=provider,
        model=model,
    )

    # Callbacks Rich
    def _on_transcribe(text: str):
        console.print(f"[bold green]▸ Vous[/]  {text}")

    def _on_response(text: str):
        from rich.markdown import Markdown
        console.print(f"[bold cyan]▸ CIEL[/]")
        if "```" in text or "#" in text or "**" in text:
            console.print(Markdown(text))
        else:
            console.print(text)
        console.print()

    session = VoiceChatSession(cfg)
    session.on_transcribe(_on_transcribe)
    session.on_response(_on_response)
    session.run()


@voice.command()
@click.argument("text", nargs=-1, required=False)
def speak(text: tuple[str, ...]) -> None:
    """Synthèse vocale d'un texte."""
    from ciel.interfaces.voice import speak as _speak, list_voices
    if not text:
        text_str = sys.stdin.read().strip()
        if not text_str:
            console.print("[yellow]Usage : ciel voice speak \"Bonjour\" ou pipez du texte[/]")
            return
    else:
        text_str = " ".join(text)
    console.print(f"[cyan]🔊[/] {text_str}")
    _speak(text_str)


@voice.command(name="voices")
def list_voice_cmd() -> None:
    """Liste les voix TTS disponibles."""
    from ciel.interfaces.voice import list_voices as _list
    _list()


@voice.command()
@click.argument("file", type=click.Path(exists=True))
def transcribe(file: str) -> None:
    """Transcrit un fichier audio en texte."""
    from ciel.interfaces.voice import transcribe as _transcribe
    console.print(f"[cyan]Transcription de {file}...[/]")
    text = _transcribe(file)
    if text:
        console.print(f"[green]{text}[/]")
    else:
        console.print("[yellow]Aucun texte détecté[/]")


@cli.command()
@click.option("--port", default=8765, help="Port du serveur CIEL")
def mcp(port: int) -> None:
    """Lance le serveur MCP (Model Context Protocol) pour Claude Desktop.
    \b
    Utilisation dans Claude Desktop:
      Ajouter à votre ~/.config/Claude/claude_desktop_config.json:
      {
        "mcpServers": {
          "ciel": {
            "command": "ciel",
            "args": ["mcp"]
          }
        }
      }
    """
    from ciel.interfaces.mcp_server import main as _mcp_main
    os.environ["CIEL_PORT"] = str(port)
    _mcp_main()


@cli.command()
def logo() -> None:
    """Affiche le logo CIEL."""
    console.print(_logo())


@cli.command()
@click.option("--channel", default="stable", type=click.Choice(["stable", "beta"]), help="Canal de mise à jour")
@click.option("--dry-run", is_flag=True, default=False, help="Afficher la version disponible sans mettre à jour")
def update(channel: str, dry_run: bool) -> None:
    """Met à jour CIEL vers la dernière version.

    Par défaut, récupère depuis GitHub releases.
    Utilise git pour les mises à jour en cours de développement.
    """
    import json
    import subprocess
    import urllib.request
    import tempfile
    import tarfile
    import zipfile
    import platform
    from pathlib import Path

    console.print(f"[{channel}] Vérification des mises à jour CIEL...\n")

    # 1. Déterminer la version actuelle
    current_version = "v0.1.0"
    try:
        from ciel import __version__
        current_version = __version__
    except ImportError:
        pass

    console.print(f"[dim]Version actuelle : {current_version}[/]")

    # 2. Récupérer l'info de la dernière version depuis GitHub API
    api_url = "https://api.github.com/repos/anomalyco/ciel/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            release = json.loads(resp.read().decode())
            latest_version = release.get("tag_name", "")
            assets = release.get("assets", [])
    except Exception as e:
        console.print(f"[red]✗ Impossible de récupérer le changelog GitHub : {e}[/]")
        console.print("[yellow]Passer au mode local...[/]")
        latest_version = None

    # 3. Rechercher le bon actif pour la plateforme actuelle
    def find_asset(assets: list[dict], patterns: list[str]) -> dict | None:
        for asset in assets:
            name = asset.get("name", "")
            for pat in patterns:
                if pat in name.lower():
                    return asset
        return None

    if latest_version and assets:
        # Nom de fichier de l'actif en fonction de la plateforme
        system = platform.system().lower()
        machine = platform.machine().lower()

        patterns = []
        if system == "linux":
            if "arm" in machine or "aarch" in machine:
                patterns = ["linux-arm", "linux-aarch64", "linux-arm64"]
            else:
                patterns = ["linux-x86_64", "linux-amd64", "linux"]
        elif system == "darwin":
            patterns = ["darwin-arm64", "darwin-x86_64", "macos"]
        elif system == "windows":
            patterns = ["windows-x86_64", "windows-amd64", "windows"]
        else:
            patterns = ["*"]

        asset = find_asset(assets, patterns)
        if asset:
            download_url = asset.get("browser_download_url")
            asset_name = asset.get("name")
        else:
            console.print("[yellow]Aucun actif compatible trouvé — utiliser les sources GitHub[/]")
            download_url = None
    else:
        download_url = None

    # 4. Afficher la version disponible
    if latest_version:
        console.print(f"[green]✓ Dernière version disponible : {latest_version}[/]")
        if not dry_run and download_url:
            console.print(f"[dim]Téléchargement : {asset_name}[/]")
            console.print("[dim]Installation en cours...[/]\n")
        else:
            console.print("[dim]No download URL found[/]\n")

    # 5. Si nous sommes en développement, utiliser git pull (fallback)
    ciel_path = Path(__file__).resolve().parent.parent.parent
    git_dir = ciel_path / ".git"
    if git_dir.exists() and not dry_run:
        console.print("[dim]Mode développement détecté — mise à jour via git pull...[/]")
        try:
            subprocess.run(["git", "pull"], cwd=ciel_path, check=True)
            console.print("[green]✓ CIEL mis à jour depuis git[/]\n")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ git pull échoué : {e}[/]")
        return

    # 6. Si une nouvelle version est disponible et qu'on n'est pas en dry-run, télécharger et installer
    if latest_version and download_url and not dry_run:
        try:
            # Télécharger l'actif
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as f:
                download_path = f.name
                console.print(f"  Téléchargement {asset_name}...\n")
                req = urllib.request.Request(download_url)
                with urllib.request.urlopen(req, timeout=60) as resp:
                    f.write(resp.read())

            # Extraire et installer (version simple)
            extracted_dir = ciel_path / "ciel-binary"
            if extracted_dir.exists():
                shutil.rmtree(extracted_dir)
            extracted_dir.mkdir(parents=True, exist_ok=True)

            if download_url.endswith(".tar.gz") or download_url.endswith(".tgz"):
                with tarfile.open(download_path, "r:gz") as tf:
                    tf.extractall(extracted_dir)
            elif download_path.endswith(".zip"):
                with zipfile.ZipFile(download_path, "r") as zf:
                    zf.extractall(extracted_dir)
            else:
                raise RuntimeError(f"Format de fichier non supporté : {download_path}")

            # Copier les binaires dans /usr/local/bin (exemple pour binaires installés)
            # ou utiliser pip install -e .
            console.print("[green]✓ CIEL mis à jour depuis GitHub[/]\n")
            console.print("[yellow]Redémarrage du serveur CIEL recommandé ?[/]")

        except Exception as e:
            console.print(f"[red]✗ Mise à jour échouée : {e}[/]")
        finally:
            if os.path.exists(download_path):
                os.unlink(download_path)
    elif not latest_version:
        console.print("[yellow]Changement : vérifiez manuellement https://github.com/anomalyco/ciel/releases[/]\n")

    # 7. Afficher le changelog si disponible
    if latest_version and "body" in release:
        body = release["body"]
        lines = body.split("\n")[:10]
        has_changelog = any("#" in l for l in lines)
        if has_changelog:
            console.print("[bold]🗒️ Changelog (extrait):[/]\n")
            for l in lines:
                if l.strip():
                    console.print(f"  {l}")
            console.print()



@cli.command()
def squad() -> None:
    """Affiche l'escouade CIEL (12 Gardiens)."""
    from rich.progress import BarColumn, Progress, TextColumn
    from ciel.brain.core import CIELBrain

    brain = CIELBrain()
    brain.load_all_modules()
    loaded = set(brain.state.modules_loaded)

    console.print(_logo())

    # Mapping Tensura → CIEL
    guardians = [
        ("STRATES MAJEURES", [
            ("APHAEL",   "Raphaël",   "analysis",         "Analyse & Logique"),
            ("CHRONOS",  "Chronos",   "chronos",          "Temps & Prédiction"),
            ("FORGE",    "Forges",    "forge",            "Création & Skills"),
            ("LOGOS",    "Logos",     "logos",            "Langage & LLM"),
            ("ANIMUS",   "Animus",    "animus",           "Émotions"),
            ("CONSCIENCE", "Consc.",  "conscience",       "Global Workspace"),
            ("ETHICS",   "Éthique",   "ethics",           "Axiomes αβγδ"),
            ("MEMORY",   "Mémoire",   "memory",           "Graphe sémantique"),
            ("NOOSPHERE","Noosph.",   "noosphere",        "Web & Science"),
            ("PERCEPTION","Percept.", "perception",       "12 sens"),
        ]),
        ("TIER A — ESCUADE D'ÉLITE", [
            ("SOEI",     "Souei",     "swarm",            "Réseau & Ruche"),
            ("BENIMARU", "Benimaru",  "metamorphic_core","Orchestrateur"),
            ("SHION",    "Shion",     "interfaces",       "Interface Term."),
            ("SHUNA",    "Shuna",     "heal",             "Healing Soin"),
            ("DIABLO",   "Diablo",    "llmbridge",        "APIs LLM"),
        ]),
        ("MODULES DE SUPPORT", [
            ("GABIMURU", "Gabimaru",  "naming",           "Nommage"),
            ("RANGA",    "Ranga",     "causal_brain",     "Causalité"),
            ("GELD",     "Geld",      "security",         "Sécurité"),
            ("RIMURU",   "Rimuru",    "meta",             "Méta-archi."),
            ("VELDORA",  "Veldora",   "strange_loop",     "Boucles étranges"),
            ("VELGRYND", "Velgrynd",  "titan",            "Écosystème Titan"),
        ]),
        ("APIS & BRIDGES", [
            ("ZEGION",   "Zegion",    "aegis",            "Défense Immune"),
            ("TEA",      "Testarossa","messaging",        "Messagerie"),
            ("CARRERA",  "Carrera",   "polyglot",         "Bridge Rust/C"),
            ("ULTIMA",   "Ultima",    "database",         "Base de données"),
        ]),
    ]

    for section_title, agents in guardians:
        console.print(f"\n[bold cyan]▸ {section_title}[/]")
        total = len(agents)
        active = sum(1 for _, _, mod, _ in agents if mod in loaded)
        bar_style = "green" if active == total else "yellow" if active > 0 else "red"

        progress = Progress(
            BarColumn(bar_width=40),
            TextColumn(f"[{bar_style}]{active}/{total}[/]"),
            console=console,
        )
        with progress:
            progress.add_task(f"[{bar_style}]{section_title}", total=total, completed=active)

        for char, name, module, role in agents:
            status = "✓" if module in loaded else "✗"
            style = "green" if module in loaded else "red"
            pct = 100 if module in loaded else 0
            bar_n = "█" * (pct // 5) + "░" * (20 - pct // 5)
            console.print(f"  [{style}]{status}[/] [bold]{char:>10}[/] [dim]|[/] [cyan]{name:<10}[/] [dim]|[/] {role:<20} [dim]|[/] [{style}]{bar_n} {pct}%[/]")

    # Stats globales
    total_modules = len(loaded)
    console.print(f"\n[dim]──────────────────────────────────────────────────[/]")
    console.print(f"  [bold]Modules :[/] [green]{total_modules}[/] actifs  "
                  f"|  [bold]Gardiens :[/] [cyan]{sum(1 for _, agents in guardians for _, _, m, _ in agents if m in loaded)}[/]/"
                  f"{sum(len(agents) for _, agents in guardians)} en ligne")
    console.print()


if __name__ == "__main__":
    cli()
