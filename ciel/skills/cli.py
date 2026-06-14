from __future__ import annotations

import json
import logging

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.markdown import Markdown

from ciel.skills.marketplace import SkillMarketplace
from ciel.skills.models import SkillManager

console = Console()
log = logging.getLogger("ciel.skills.cli")


@click.group(name="skill")
def skill_group():
    """Gestion des compétences (skills) CIEL.

    Marketplace, catalogue, installation, publication.
    """


@skill_group.group(name="marketplace")
def marketplace_group():
    """Marketplace de compétences.

    Cherche, installe, et publie des skills depuis le
    catalogue intégré ou des sources distantes.
    """


@marketplace_group.command(name="search")
@click.argument("query", default="")
@click.option("--category", "-c", default="", help="Filtrer par catégorie")
@click.option("--tag", "-t", default="", help="Filtrer par tag")
@click.option("--min-stars", "-s", default=0, type=int, help="Stars minimum")
@click.option("--limit", "-l", default=20, type=int, help="Max résultats")
def search_cmd(query: str, category: str, tag: str, min_stars: int, limit: int):
    """Cherche des skills dans le marketplace."""
    mkt = SkillMarketplace()
    results = mkt.search(query=query, category=category, tag=tag, min_stars=min_stars)

    if not results:
        console.print("[yellow]Aucun résultat trouvé[/]")
        return

    table = Table(
        title=f"Marketplace — {len(results)} résultat(s)",
        box=box.ROUNDED,
    )
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nom", style="green")
    table.add_column("Catégorie", style="yellow")
    table.add_column("Tags", style="dim")
    table.add_column("Stars", style="magenta", justify="right")
    table.add_column("Installs", style="blue", justify="right")

    for entry in results[:limit]:
        table.add_row(
            entry.id,
            entry.name,
            entry.category,
            ", ".join(entry.tags[:3]),
            str(entry.stars),
            str(entry.installs),
        )
    console.print(table)
    if len(results) > limit:
        console.print(f"[dim]… et {len(results) - limit} de plus[/]")


@marketplace_group.command(name="info")
@click.argument("skill_id")
def info_cmd(skill_id: str):
    """Affiche les détails d'un skill du catalogue."""
    mkt = SkillMarketplace()
    entry = mkt.get(skill_id)

    if not entry:
        # try search
        results = mkt.search(query=skill_id)
        if len(results) == 1:
            entry = results[0]
        elif len(results) > 1:
            console.print("[yellow]Plusieurs résultats. Affinez votre recherche :[/]")
            for r in results[:5]:
                console.print(f"  {r.id} — {r.name}")
            return
        else:
            console.print(f"[red]Skill '{skill_id}' introuvable[/]")
            return

    console.print(Panel(
        f"[bold]{entry.name}[/] v{entry.version}\n"
        f"[dim]{entry.id}[/]\n\n"
        f"{entry.description}\n\n"
        f"[yellow]Catégorie:[/] {entry.category}\n"
        f"[yellow]Tags:[/] {', '.join(entry.tags)}\n"
        f"[yellow]Auteur:[/] {entry.author}\n"
        f"[yellow]Stars:[/] {entry.stars}  [yellow]Installs:[/] {entry.installs}\n"
        f"[yellow]Source:[/] {entry.source}",
        title="Skill Info",
        box=box.ROUNDED,
    ))

    if entry.body:
        console.print("\n[bold]Body:[/]")
        console.print(Panel(entry.body[:500], box=box.SIMPLE))


@marketplace_group.command(name="install")
@click.argument("skill_id")
@click.option("--category", "-c", default=None, help="Catégorie locale (défaut: celle du catalogue)")
def install_cmd(skill_id: str, category: str | None):
    """Installe un skill du marketplace dans le gestionnaire local."""
    mkt = SkillMarketplace()
    local_id = mkt.install(skill_id, category=category)

    if local_id:
        mkt.record_install(skill_id)
        console.print(f"[green]✓[/] Skill installé : [bold]{local_id}[/]")
    else:
        console.print(f"[red]✗[/] Échec de l'installation de '{skill_id}'")
        console.print("Utilisez 'ciel skill marketplace search' pour trouver des skills.")


@marketplace_group.command(name="list")
@click.option("--category", "-c", default="", help="Filtrer par catégorie")
def list_cmd(category: str):
    """Liste le catalogue complet du marketplace."""
    mkt = SkillMarketplace()
    results = mkt.search(category=category)

    if not results:
        console.print("[yellow]Aucun skill dans le catalogue[/]")
        return

    # Group by category
    by_cat: dict[str, list] = {}
    for e in results:
        by_cat.setdefault(e.category, []).append(e)

    for cat, entries in sorted(by_cat.items()):
        table = Table(title=f"[bold]{cat}[/] ({len(entries)})", box=box.SIMPLE)
        table.add_column("ID", style="cyan")
        table.add_column("Nom", style="green")
        table.add_column("Stars", style="magenta", justify="right")
        for e in entries:
            table.add_row(e.id, e.name, str(e.stars))
        console.print(table)
        console.print("")


@marketplace_group.command(name="categories")
def categories_cmd():
    """Liste les catégories disponibles."""
    mkt = SkillMarketplace()
    cats = mkt.categories()

    table = Table(title="Catégories", box=box.ROUNDED)
    table.add_column("Catégorie", style="cyan")
    table.add_column("Skills", style="green", justify="right")

    for c in cats:
        table.add_row(c["name"], str(c["count"]))
    console.print(table)


@marketplace_group.command(name="sources")
def sources_cmd():
    """Liste et gère les sources distantes."""
    mkt = SkillMarketplace()
    sources = mkt.list_sources()

    if not sources:
        console.print("[yellow]Aucune source distante configurée[/]")
        console.print("Ajoutez-en avec 'ciel skill marketplace add-source <url>'")
    else:
        table = Table(title="Sources distantes", box=box.ROUNDED)
        table.add_column("URL", style="cyan")
        for url in sources:
            table.add_row(url)
        console.print(table)


@marketplace_group.command(name="add-source")
@click.argument("url")
def add_source_cmd(url: str):
    """Ajoute une source distante au catalogue."""
    mkt = SkillMarketplace()
    if mkt.add_source(url):
        console.print(f"[green]✓[/] Source ajoutée : {url}")
    else:
        console.print(f"[yellow]Déjà présente : {url}[/]")


@marketplace_group.command(name="remove-source")
@click.argument("url")
def remove_source_cmd(url: str):
    """Retire une source distante."""
    mkt = SkillMarketplace()
    if mkt.remove_source(url):
        console.print(f"[green]✓[/] Source retirée : {url}")
    else:
        console.print(f"[yellow]Source introuvable : {url}[/]")


@marketplace_group.command(name="refresh")
def refresh_cmd():
    """Recharge le catalogue depuis les sources distantes."""
    mkt = SkillMarketplace()
    count = mkt.refresh()
    console.print(f"[green]✓[/] Catalogue rafraîchi : {count} entrées ajoutées")


@marketplace_group.command(name="stats")
def stats_cmd():
    """Statistiques du marketplace."""
    mkt = SkillMarketplace()
    stats = mkt.stats()
    console.print(Panel(
        f"[bold]Marketplace Stats[/]\n\n"
        f"Total skills: {stats['total']}\n"
        f"Catégories:  {stats['categories']}\n"
        f"Sources:     {stats['sources']}\n"
        f"Intégrés:    {stats['builtin']}",
        box=box.ROUNDED,
    ))


# ── Gestion locale ──


@skill_group.command(name="list")
@click.option("--category", "-c", default="", help="Filtrer par catégorie")
@click.option("--state", "-s", default="", help="Filtrer par état (active|stale|archived)")
def list_local_cmd(category: str, state: str):
    """Liste les skills installés localement."""
    mgr = SkillManager()
    mgr.discover()
    skills = mgr.list(
        category=category if category else None,
        state=state if state else None,
    )

    if not skills:
        console.print("[yellow]Aucun skill local[/]")
        console.print("Installez-en avec 'ciel skill marketplace install <id>'")
        return

    table = Table(title=f"Skills locaux ({len(skills)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nom", style="green")
    table.add_column("Catégorie", style="yellow")
    table.add_column("État", style="magenta")
    table.add_column("Usages", style="blue", justify="right")

    for s in skills:
        state_style = {"active": "green", "stale": "yellow", "archived": "red"}.get(s.state, "white")
        table.add_row(
            s.id,
            s.name,
            s.category,
            f"[{state_style}]{s.state}[/]",
            str(s.usage_count),
        )
    console.print(table)

    stats = mgr.statistics()
    console.print(f"\n[dim]Total: {stats['total']} skills, "
                  f"{stats['total_usage']} utilisations[/]")


@skill_group.command(name="info")
@click.argument("skill_id")
def local_info_cmd(skill_id: str):
    """Affiche les détails d'un skill local."""
    mgr = SkillManager()
    mgr.discover()
    skill = mgr.get(skill_id)

    if not skill:
        # try name search
        skills = mgr.list()
        skill = next((s for s in skills if s.name == skill_id), None)

    if not skill:
        console.print(f"[red]Skill '{skill_id}' introuvable[/]")
        return

    state_style = {"active": "green", "stale": "yellow", "archived": "red"}.get(skill.state, "white")

    console.print(Panel(
        f"[bold]{skill.name}[/] v{skill.version}\n"
        f"[dim]{skill.id}[/]\n\n"
        f"{skill.description}\n\n"
        f"[yellow]Catégorie:[/] {skill.category}\n"
        f"[yellow]Tags:[/] {', '.join(skill.tags)}\n"
        f"[yellow]État:[/] [{state_style}]{skill.state}[/]\n"
        f"[yellow]Usages:[/] {skill.usage_count}\n"
        f"[yellow]Dépendances:[/] {', '.join(skill.dependencies) if skill.dependencies else '(aucune)'}",
        title="Skill Local",
        box=box.ROUNDED,
    ))

    if skill.body:
        console.print("\n[bold]Body:[/]")
        console.print(Panel(skill.body[:500], box=box.SIMPLE))


@skill_group.command(name="create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Description courte")
@click.option("--category", "-c", default="general", help="Catégorie")
@click.option("--tags", "-t", default="", help="Tags (virgule)")
@click.option("--body", "-b", default="", help="Corps du skill")
def create_cmd(name: str, description: str, category: str, tags: str, body: str):
    """Crée un nouveau skill local."""
    mgr = SkillManager()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    skill = mgr.create(
        name=name, description=description or name,
        category=category, tags=tag_list, body=body,
    )
    console.print(f"[green]✓[/] Skill créé : [bold]{skill.id}[/] ({skill.name})")


@skill_group.command(name="publish")
@click.argument("skill_id")
@click.option("--output", "-o", default="", help="Fichier de sortie JSON")
@click.option("--author", "-a", default="CIEL", help="Nom de l'auteur")
def publish_cmd(skill_id: str, output: str, author: str):
    """Exporte un skill local au format catalogue (pour publication)."""
    mkt = SkillMarketplace()
    export = mkt.publish(skill_id, author=author, export_path=output if output else None)

    if export:
        console.print("[green]✓[/] Skill exporté :")
        console.print(json.dumps(export, indent=2))
        if output:
            console.print(f"   → [bold]{output}[/]")
    else:
        console.print(f"[red]✗[/] Skill '{skill_id}' introuvable")
