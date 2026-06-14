from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ciel.delegation import Kanban, Delegator, TaskStatus

console = Console()


@click.group(name="kanban")
def kanban_group():
    """Kanban — file d'attente multi-agents.

    Gère les tâches asynchrones avec priorités et dispatch.
    """


@kanban_group.command()
@click.argument("description")
@click.option("--agent", default="", help="Agent cible")
@click.option("--workspace", default="", help="Workspace isolé")
@click.option("--priority", default=0, type=int, help="Priorité (défaut: 0)")
def add(description: str, agent: str, workspace: str, priority: int):
    """Ajoute une tâche à la file."""
    kanban = Kanban()
    tid = kanban.enqueue(description, agent, workspace, priority)
    console.print(f"[green]✓[/] Tâche ajoutée : {tid}")


@kanban_group.command()
@click.option("--agent", default="", help="Agent cible")
def next(agent: str):
    """Récupère la prochaine tâche en attente."""
    kanban = Kanban()
    task = kanban.dequeue(agent)
    if task:
        console.print(Panel(
            f"  ID          : {task.id}\n"
            f"  Description : {task.description}\n"
            f"  Agent       : {task.agent_id or '-'}\n"
            f"  Priorité    : {task.priority}\n"
            f"  Workspace   : {task.workspace_id or '-'}",
            title="Tâche assignée",
            border_style="cyan",
        ))
    else:
        console.print("[yellow]Aucune tâche en attente[/]")


@kanban_group.command()
@click.argument("task_id")
@click.argument("result", default="")
def done(task_id: str, result: str):
    """Marque une tâche comme terminée."""
    kanban = Kanban()
    if kanban.complete(task_id, result):
        console.print(f"[green]✓[/] Tâche {task_id[:16]}... terminée")
    else:
        console.print(f"[red]✗[/] Tâche introuvable")


@kanban_group.command()
@click.argument("task_id")
@click.argument("error", default="")
def fail(task_id: str, error: str):
    """Marque une tâche comme échouée."""
    kanban = Kanban()
    if kanban.fail(task_id, error):
        console.print(f"[yellow]⚠[/] Tâche {task_id[:16]}... marquée échouée")
    else:
        console.print(f"[red]✗[/] Tâche introuvable")


@kanban_group.command()
@click.argument("task_id")
def cancel(task_id: str):
    """Annule une tâche."""
    kanban = Kanban()
    if kanban.cancel(task_id):
        console.print(f"[yellow]⚠[/] Tâche {task_id[:16]}... annulée")
    else:
        console.print(f"[red]✗[/] Tâche introuvable ou déjà terminée")


@kanban_group.command()
@click.option("--status", default="", help="Filtrer par statut (pending/running/done/failed)")
@click.option("--agent", default="", help="Filtrer par agent")
def list(status: str, agent: str):
    """Liste les tâches."""
    kanban = Kanban()
    status_filter = TaskStatus(status) if status else None
    tasks = kanban.list(status=status_filter, agent_id=agent)

    if not tasks:
        console.print("[yellow]Aucune tâche[/]")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("Description", style="cyan")
    table.add_column("Statut")
    table.add_column("Agent")
    table.add_column("Priorité", justify="right")
    table.add_column("Durée", justify="right")
    for t in tasks:
        status_style = {
            "pending": "yellow", "running": "blue",
            "done": "green", "failed": "red", "cancelled": "dim",
        }.get(t.status.value, "")
        dur = f"{t._duration():.1f}s" if t._duration() else "-"
        table.add_row(
            t.id[:12], t.description[:40],
            f"[{status_style}]{t.status.value}[/]",
            t.agent_id[:12] or "-",
            str(t.priority),
            dur,
        )
    console.print(table)


@kanban_group.command()
def stats():
    """Statistiques du kanban."""
    kanban = Kanban()
    s = kanban.stats()
    console.print(f"  Total  : {s['total']}")
    console.print(f"  En attente : {s['pending']}")
    console.print(f"  En cours   : {s['running']}")
    for status, count in s["by_status"].items():
        console.print(f"  {status} : {count}")
