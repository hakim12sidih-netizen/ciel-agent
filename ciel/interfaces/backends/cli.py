from __future__ import annotations

import json
import logging

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ciel.interfaces.capabilities import get_detector, TERMINAL_DB
from ciel.interfaces.themes import list_themes, set_theme, get_theme
from ciel.interfaces.backends.registry import get_all, get_available, get_terminal_adapters

console = Console()
log = logging.getLogger("ciel.interfaces.cli_backend")


@click.group(name="terminal")
def terminal_group():
    """Détection et configuration du terminal.

    Affiche les capacités du terminal détecté et
    les adaptateurs disponibles.
    """


@terminal_group.command(name="detect")
def detect_terminal():
    """Détecte le terminal et ses capacités."""
    detector = get_detector()
    info = detector.to_dict()
    caps = detector._cached

    table = Table(title="Terminal détecté", box=box.ROUNDED)
    table.add_column("Propriété", style="cyan")
    table.add_column("Valeur", style="green")

    table.add_row("Émulateur", f"[bold]{caps.get('emulator', '?')}[/]")
    table.add_row("TERM", caps.get("term_env", "?"))
    table.add_row("COLORTERM", caps.get("colorterm_env", "?"))
    table.add_row("Profondeur couleur", info["color_depth"])
    table.add_row("True Color", "[green]✓[/]" if info["supports_true_color"] else "[red]✗[/]")
    table.add_row("Images", "[green]✓[/]" if info["supports_images"] else "[red]✗[/]")
    table.add_row("Unicode", "[green]✓[/]" if info["supports_unicode"] else "[red]✗[/]")
    table.add_row("Protocole", info["protocol"])
    table.add_row("Colonnes", str(info["size"]["columns"]))
    table.add_row("Lignes", str(info["size"]["lines"]))
    console.print(table)

    if caps.get("is_tmux"):
        console.print("[yellow]ℹ Dans une session tmux[/]")
    if caps.get("is_ssh"):
        console.print("[yellow]ℹ Connexion SSH distante[/]")

    features = info.get("features", {})
    if features:
        ft = Table(title="Fonctionnalités", box=box.SIMPLE)
        ft.add_column("Fonctionnalité", style="cyan")
        ft.add_column("Disponible", style="green")
        for feat, avail in sorted(features.items()):
            ft.add_row(feat.replace("_", " ").title(),
                       "[green]✓[/]" if avail else "[red]✗[/]")
        console.print(ft)


@terminal_group.command(name="adapters")
def list_adapters():
    """Liste les adaptateurs terminaux disponibles."""
    adapters = get_terminal_adapters()
    table = Table(title="Adaptateurs terminaux", box=box.ROUNDED)
    table.add_column("Terminal", style="cyan")
    table.add_column("Adaptateur", style="green")
    table.add_column("Fonctionnalités", style="yellow")
    table.add_column("Conseils", style="dim")

    for term, info in adapters.items():
        table.add_row(
            term,
            info["adapter"],
            ", ".join(info["features"][:5]),
            info["hints"][:60],
        )
    console.print(table)


@terminal_group.command(name="backends")
def list_backends():
    """Liste les backends d'interface enregistrés."""
    backends = get_all()
    available = get_available()

    table = Table(title=f"Backends ({len(backends)} total, {len(available)} disponibles)",
                  box=box.ROUNDED)
    table.add_column("Mode", style="cyan")
    table.add_column("Nom", style="green")
    table.add_column("Description", style="white")
    table.add_column("Dispo", style="yellow")

    for b in backends:
        avail = "[green]✓[/]" if b.is_available() else "[red]✗[/]"
        table.add_row(b.mode, b.name, b.description[:50], avail)
    console.print(table)


@click.group(name="theme")
def theme_group():
    """Gestion des thèmes d'interface.

    Change l'apparence des interfaces CIEL (TUI, Web, etc.).
    Thèmes disponibles: ciel-dark, ciel-light, nord, dracula, tokyo-night.
    """


@theme_group.command(name="list")
def list_themes_cmd():
    """Liste les thèmes disponibles."""
    themes = list_themes()
    current_name = get_theme().name

    table = Table(title="Thèmes disponibles", box=box.ROUNDED)
    table.add_column("", style="green", width=3)
    table.add_column("Nom", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Type", style="yellow")

    for t in themes:
        marker = "✓" if t["name"] == current_name else " "
        mode = "sombre" if t["is_dark"] else "clair"
        table.add_row(marker, t["name"], t["description"], mode)
    console.print(table)
    console.print(f"\nThème actif: [bold]{current_name}[/]")


@theme_group.command(name="set")
@click.argument("name")
def set_theme_cmd(name: str):
    """Change le thème actif."""
    if set_theme(name):
        theme = get_theme()
        mode = "sombre" if theme.is_dark else "clair"
        console.print(f"[green]✓[/] Thème changé: [bold]{name}[/] ({mode})")
        # Preview colors
        table = Table(box=box.SIMPLE, title="Aperçu des couleurs")
        table.add_column("Token", style="cyan")
        table.add_column("Couleur", style="white")
        for token, color in list(theme.colors.items())[:10]:
            table.add_row(token, f"[{color}]{color}[/]")
        console.print(table)
    else:
        console.print(f"[red]✗[/] Thème inconnu: {name}")
        console.print("Thèmes disponibles: " + ", ".join(t["name"] for t in list_themes()))


@theme_group.command(name="preview")
def preview_theme():
    """Affiche un aperçu du thème actif."""
    theme = get_theme()
    mode = "Dark" if theme.is_dark else "Light"
    console.print(Panel(
        f"[{theme.colors['primary']}]███[/] [bold]{theme.name}[/] ({mode})\n"
        f"[{theme.colors['primary']}]███[/] primary   [{theme.colors['secondary']}]███[/] secondary\n"
        f"[{theme.colors['accent']}]███[/] accent    [{theme.colors['success']}]███[/] success\n"
        f"[{theme.colors['warning']}]███[/] warning   [{theme.colors['error']}]███[/] error\n"
        f"[{theme.colors['text']}]███[/] text      [{theme.colors['dim']}]███[/] dim\n"
        f"[{theme.colors['surface']}]   [/] surface   [{theme.colors['background']}]   [/] background\n"
        f"\n{theme.description}",
        title="Theme Preview",
        box=box.ROUNDED,
    ))
