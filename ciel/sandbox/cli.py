from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ciel.sandbox import (
    SandboxEngine, SandboxPolicy,
    detect_best_backend, BACKENDS, LANGUAGES,
)
from ciel.workspace import WorkspaceManager, POLICIES

console = Console()


@click.group(name="sandbox")
def sandbox_group():
    """Sandbox — exécution sécurisée multi-backend.

    Backends : docker (défaut), local, ssh
    Politiques : restricted, default, permissive
    """


@sandbox_group.command()
@click.argument("code")
@click.option("--lang", default="python", help="Langage")
@click.option("--backend", default=None, help="Backend (docker/local/ssh)")
@click.option("--timeout", default=30, type=int, help="Timeout (s)")
@click.option("--policy", default="default", help="Politique de sécurité")
def run(code: str, lang: str, backend: str | None, timeout: int, policy: str):
    """Exécute du code dans un sandbox."""
    sbx = SandboxEngine(
        backend=backend,
        policy=POLICIES.get(policy, POLICIES["default"]),
    )
    result = sbx.execute(code, lang, timeout)
    if result.error:
        console.print(f"[red]✗ {result.error}[/]")
        return
    if result.stdout:
        console.print(Panel(result.stdout.strip(), title="stdout", border_style="green"))
    if result.stderr:
        console.print(Panel(result.stderr.strip(), title="stderr", border_style="red"))
    console.print(f"[dim]exit={result.exit_code}  duration={result.duration_ms:.0f}ms[/]")


@sandbox_group.command()
@click.option("--backend", default=None, help="Backend spécifique")
def info(backend: str | None):
    """Info sur les backends et politiques disponibles."""
    if backend:
        cls = BACKENDS.get(backend)
        if not cls:
            console.print(f"[red]Backend inconnu : {backend}[/]")
            return
        avail = cls.is_available()
        console.print(Panel(
            f"  Nom      : {backend}\n"
            f"  Classe   : {cls.__name__}\n"
            f"  Disponible : {'✓' if avail else '✗'}",
            title=f"Backend {backend}",
            box=box.ROUNDED,
        ))
        return

    best = detect_best_backend()
    table = Table(box=box.HEAVY_EDGE)
    table.add_column("Backend", style="cyan")
    table.add_column("Disponible")
    table.add_column("Langages supportés")
    for name in BACKENDS:
        cls = BACKENDS[name]
        avail = cls.is_available()
        status = "✓" if avail else "✗"
        style = "green" if avail else "red"
        best_mark = " ← meilleur" if name == best else ""
        table.add_row(
            f"{name}{best_mark}",
            f"[{style}]{status}[/]",
            ", ".join(LANGUAGES.keys()),
        )
    console.print(table)

    pol_table = Table(title="Politiques de sécurité", box=box.ROUNDED)
    pol_table.add_column("Politique", style="cyan")
    pol_table.add_column("Réseau", justify="center")
    pol_table.add_column("FS Write", justify="center")
    pol_table.add_column("GPU", justify="center")
    pol_table.add_column("Mémoire", justify="right")
    pol_table.add_column("Timeout", justify="right")
    for name, pol in POLICIES.items():
        pol_table.add_row(
            name,
            "✓" if pol.allow_network else "✗",
            "✓" if pol.allow_filesystem_write else "✗",
            "✓" if pol.allow_gpu else "✗",
            f"{pol.max_memory_mb}MB",
            f"{pol.timeout_seconds}s",
        )
    console.print(pol_table)


@click.group(name="workspace")
def workspace_group():
    """Workspaces — environnements isolés pour agents.

    Chaque workspace = sandbox + skills + état persistant.
    """


@workspace_group.command()
@click.argument("name")
@click.option("--backend", default=None, help="Backend sandbox")
@click.option("--policy", default="default", help="Politique de sécurité")
@click.option("--agent", default="", help="ID de l'agent associé")
@click.option("--skills", default="", help="Skills (virgule séparés)")
def create(name: str, backend: str | None, policy: str,
           agent: str, skills: str):
    """Crée un workspace isolé."""
    wm = WorkspaceManager()
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    ws = wm.create(
        name=name, sandbox_backend=backend or "",
        policy=policy, agent_id=agent, skills=skill_list,
    )
    console.print(f"[green]✓[/] Workspace créé : {ws.id}")
    console.print(f"  Nom     : {ws.name}")
    console.print(f"  Backend : {ws.sandbox_backend}")
    console.print(f"  Policy  : {ws.policy}")


@workspace_group.command()
@click.argument("workspace_id")
@click.argument("code")
@click.option("--lang", default="python", help="Langage")
@click.option("--timeout", default=30, type=int, help="Timeout (s)")
def exec(workspace_id: str, code: str, lang: str, timeout: int):
    """Exécute du code dans un workspace."""
    wm = WorkspaceManager()
    result = wm.execute(workspace_id, code, lang, timeout)
    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/]")
        return
    console.print(Panel(result.get("stdout", "").strip(), title="stdout", border_style="green"))
    if result.get("stderr"):
        console.print(Panel(result["stderr"].strip(), title="stderr", border_style="red"))
    console.print(f"[dim]exit={result['exit']}  duration={result['duration_ms']:.0f}ms[/]")


@workspace_group.command()
@click.argument("workspace_id")
def delete(workspace_id: str):
    """Supprime un workspace."""
    wm = WorkspaceManager()
    if wm.delete(workspace_id):
        console.print(f"[green]✓[/] Workspace {workspace_id[:16]}... supprimé")
    else:
        console.print(f"[red]✗[/] Workspace introuvable")


@workspace_group.command()
@click.option("--all", "show_all", is_flag=True, help="Inclure les inactifs")
@click.option("--name", default="", help="Filtrer par nom")
def list(show_all: bool, name: str):
    """Liste les workspaces."""
    wm = WorkspaceManager()
    workspaces = wm.list(active_only=not show_all)
    if name:
        workspaces = [w for w in workspaces if name.lower() in w.name.lower()]
    if not workspaces:
        console.print("[yellow]Aucun workspace[/]")
        return
    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("Nom", style="cyan")
    table.add_column("Backend", style="yellow")
    table.add_column("Policy")
    table.add_column("Agent")
    table.add_column("État")
    for ws in workspaces:
        status = "[green]actif[/]" if ws.active else "[dim]inactif[/]"
        table.add_row(
            ws.id[:16], ws.name, ws.sandbox_backend,
            ws.policy, ws.agent_id[:12] or "-", status,
        )
    console.print(table)
    console.print(f"\n[dim]Total: {len(workspaces)}[/]")


@workspace_group.command()
@click.argument("workspace_id")
@click.argument("key")
@click.argument("value")
def set(workspace_id: str, key: str, value: str):
    """Définit une clé d'état dans le workspace."""
    wm = WorkspaceManager()
    wm.update_state(workspace_id, key, value)
    console.print(f"[green]✓[/] {key} = {value}")


@workspace_group.command()
@click.argument("workspace_id")
@click.argument("key")
def get(workspace_id: str, key: str):
    """Récupère une clé d'état du workspace."""
    wm = WorkspaceManager()
    value = wm.get_state(workspace_id, key)
    if value is None:
        console.print(f"[yellow]Clé '{key}' introuvable[/]")
    else:
        console.print(f"{key} = {value}")


@workspace_group.command()
def stats():
    """Statistiques des workspaces."""
    wm = WorkspaceManager()
    s = wm.stats()
    console.print(f"  Workspaces : {s['total']} ({s['active']} actifs)")
