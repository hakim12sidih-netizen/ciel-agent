from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ciel.learning import Curator, SkillGen

console = Console()


@click.group(name="curator")
def curator_group():
    """Curateur — archivage et épinglage automatique.

    Nettoie les skills/sessions inutilisés, épingle les critiques.
    """


@curator_group.command()
@click.option("--archive", default=30, help="Jours avant archivage (défaut: 30)")
@click.option("--promote", default=10, help="Utilisations avant épinglage (défaut: 10)")
@click.option("--dry-run", is_flag=True, help="Simulation sans modification")
def scan(archive: int, promote: int, dry_run: bool):
    """Analyse et archive/épingle les items."""
    curator = Curator()
    if dry_run:
        items = curator.get_items()
        to_archive = [i for i in items if not i.archived and not i.pinned]
        console.print(f"[cyan]Scan simulé : {len(to_archive)} candidats à l'archivage[/]")
        for item in to_archive[:10]:
            console.print(f"  [dim]{item.type}[/] {item.name}")
        return

    changes = curator.scan(
        age_days_archive=archive,
        usage_threshold=promote,
    )
    console.print(f"[green]✓ Scan terminé : {len(changes)} changements[/]")
    for c in changes:
        console.print(f"  [dim]{c}[/]")
    console.print(curator.summary())


@curator_group.command()
def stats():
    """Statistiques du curateur."""
    curator = Curator()
    items = curator.get_items()
    total = len(items)
    active = len([i for i in items if not i.archived])
    pinned = len([i for i in items if i.pinned])
    archived = len([i for i in items if i.archived])

    table = Table(box=box.HEAVY_EDGE)
    table.add_column("Métrique", style="cyan")
    table.add_column("Valeur", style="green")
    table.add_row("Total items", str(total))
    table.add_row("Actifs", str(active))
    table.add_row("Épinglés", str(pinned))
    table.add_row("Archivés", str(archived))
    table.add_row("Scans", str(curator.get_stats()["total_scans"]))
    console.print(table)
    console.print(curator.summary())


@curator_group.command()
@click.option("--type", "type_", default="", help="Filtrer par type")
@click.option("--archived/--no-archived", default=None, help="Filtrer archivés")
@click.option("--pinned/--no-pinned", default=None, help="Filtrer épinglés")
def list(type_: str, archived: bool | None, pinned: bool | None):
    """Liste les items suivis par le curateur."""
    curator = Curator()
    items = curator.get_items(type_=type_, archived=archived, pinned=pinned)
    if not items:
        console.print("[yellow]Aucun item trouvé[/]")
        return
    table = Table(box=box.ROUNDED)
    table.add_column("Nom", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Utilisations", justify="right")
    table.add_column("Score")
    table.add_column("État")
    for item in items:
        status = ""
        if item.pinned:
            status = "[green]📌 épinglé[/]"
        elif item.archived:
            status = "[dim]archivé[/]"
        else:
            status = "[blue]actif[/]"
        table.add_row(
            item.name[:30],
            item.type,
            str(item.usage_count),
            f"{item.score:.1f}",
            status,
        )
    console.print(table)


@curator_group.command()
@click.argument("item_id")
@click.option("--pin", is_flag=True, help="Épingler l'item")
@click.option("--unpin", is_flag=True, help="Désépingler l'item")
def item(item_id: str, pin: bool, unpin: bool):
    """Gère un item spécifique."""
    curator = Curator()
    if pin:
        curator.pin(item_id)
        console.print(f"[green]✓ Item {item_id[:16]}... épinglé[/]")
    elif unpin:
        curator.unpin(item_id)
        console.print(f"[green]✓ Item {item_id[:16]}... désépinglé[/]")
    else:
        i = curator.get_item(item_id)
        if i:
            console.print(Panel(
                f"  Nom : {i.name}\n  Type : {i.type}\n"
                f"  Utilisations : {i.usage_count}\n  Score : {i.score:.1f}\n"
                f"  Épinglé : {'✓' if i.pinned else '✗'}\n"
                f"  Archivé : {'✓' if i.archived else '✗'}",
                title=f"Item {item_id[:16]}",
                box=box.ROUNDED,
            ))
        else:
            console.print(f"[red]✗ Item {item_id[:16]}... introuvable[/]")


@click.group(name="skillgen")
def skillgen_group():
    """Génération automatique de skills.

    Analyse les tâches complexes et crée des skills réutilisables.
    """


@skillgen_group.command()
def list():
    """Liste les skills générés automatiquement."""
    gen = SkillGen()
    skills = gen.list_generated()
    if not skills:
        console.print("[yellow]Aucun skill généré[/]")
        return
    table = Table(box=box.ROUNDED)
    table.add_column("Nom", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Version", style="yellow")
    for s in skills:
        table.add_row(s.name, s.description[:60], s.version)
    console.print(table)


@skillgen_group.command()
def stats():
    """Statistiques de génération de skills."""
    gen = SkillGen()
    stats = gen.stats()
    console.print(f"[cyan]Skills générés :[/] {stats['total_generated']}")
    console.print(f"[cyan]Répertoire :[/] {stats['skills_dir']}")
