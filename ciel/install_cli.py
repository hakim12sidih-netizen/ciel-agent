"""
CIEL v∞.8 — Installation Assistant CLI.
Assistant intelligent pour l'installation et la configuration.
"""
from __future__ import annotations

import sys
import json
import shutil
import subprocess
import platform
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box



console = Console()


@click.group(name="install")
def install_cli():
    """Assistant d'installation intelligent CIEL."""


@install_cli.command()
@click.option("--fix", is_flag=True, help="Tente de réparer automatiquement les problèmes")
def doctor(fix: bool):
    """Diagnostic complet du système."""
    from ciel.doctor.core import Doctor
    d = Doctor()
    if fix:
        fixed = d.fix_all()
        console.print(f"[green]✓ {len(fixed)} problème(s) corrigé(s)[/]")
        for f in fixed:
            console.print(f"  [green]→ {f}[/]")
    else:
        report = d.check_all()
        for f in report.findings:
            icon = {"ok": "✓", "warning": "⚠", "error": "✗", "info": "ℹ"}.get(f.severity, "?")
            style = {"ok": "green", "warning": "yellow", "error": "red", "info": "blue"}.get(f.severity)
            console.print(f"  [{style}]{icon}[/] {f.title}")
            if f.detail:
                console.print(f"    [dim]{f.detail}[/]")
        console.print(f"\n[bold]{len(report.ok)}/{len(report.findings)} checks OK[/]")
        if report.errors:
            console.print(f"\n[yellow]Conseil: `ciel install doctor --fix` pour réparer[/]")


@install_cli.command()
@click.option("--mode", type=click.Choice(["quickstart", "advanced"]), default="quickstart",
              help="Quickstart (valeurs par défaut) ou Advanced (configuration complète)")
@click.option("--auto", is_flag=True, help="Mode automatique (pas d'interaction)")
@click.option("--provider", default="openai", help="Fournisseur LLM par défaut")
@click.option("--model", default="gpt-4o", help="Modèle par défaut")
@click.option("--port", default="8765", help="Port du serveur API")
def run(mode: str, auto: bool, provider: str, model: str, port: str):
    """Lance l'installation guidée de CIEL."""
    import asyncio
    asyncio.run(_do_install(mode, auto, provider, model, port))


async def _do_install(mode: str, auto: bool, provider: str, model: str, port: str):
    from ciel.api.routes.install import (
        run_checks, get_install_steps, execute_step, get_config_suggestions,
    )
    console.print(Panel.fit("[bold green]⚡ Installation de CIEL[/]", border_style="green"))
    console.print()

    # Mode indicator
    if mode == "quickstart":
        console.print(f"[cyan]Mode: Démarrage rapide[/] [dim](provider={provider}, model={model}, port={port})[/]")
    else:
        console.print(f"[cyan]Mode: Installation avancée[/] [dim]configuration complète[/]")
        if not auto:
            provider = click.prompt("  Fournisseur LLM", default=provider)
            model = click.prompt("  Modèle par défaut", default=model)
            port = click.prompt("  Port du serveur", default=port)
    console.print()

    # 1. Doctor
    console.print("[bold]Phase 1: Diagnostic système[/]")
    checks = await run_checks()
    errors = [c for c in checks if c.status == "error"]
    warnings = [c for c in checks if c.status == "warning"]

    if errors:
        for e in errors:
            console.print(f"  [red]✗ {e.message}[/]")
            if e.detail:
                console.print(f"    [dim]{e.detail}[/]")
        if not auto:
            console.print("[yellow]Tentative de réparation automatique...[/]")
            from ciel.doctor.core import Doctor
            d = Doctor()
            fixed = d.fix_all()
            if fixed:
                console.print(f"  [green]✓ {len(fixed)} problème(s) corrigé(s)[/]")
            if not click.confirm("\nContinuer l'installation ?", default=False):
                console.print("[red]Installation annulée.[/]")
                return
    elif warnings:
        for w in warnings:
            console.print(f"  [yellow]⚠ {w.message}[/]")
    else:
        console.print("  [green]✓ Tous les checks passent[/]")
    console.print()

    # 2. Steps
    steps = await get_install_steps()
    console.print("[bold]Phase 2: Exécution des étapes[/]")

    for i, step in enumerate(steps, 1):
        if step.optional and not auto:
            if not click.confirm(f"  {i}. {step.label} (optionnel) ?", default=False):
                console.print(f"    [dim]⏭  Ignoré[/]")
                continue

        console.print(f"  {i}. {step.label}...")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Exécution de {step.id}...", total=None)
            result = await execute_step({"step_id": step.id, "params": {
                "provider": provider,
                "model": model,
                "port": port,
            }})

        if result.success:
            console.print(f"    [green]✓ {result.output or 'Terminé'}[/]")
        else:
            console.print(f"    [red]✗ {result.error or 'Échec'}[/]")
            if not auto:
                if not click.confirm("    Continuer malgré l'erreur ?", default=False):
                    console.print("[red]Installation interrompue.[/]")
                    return

    # 3. API keys (optional)
    console.print()
    console.print("[bold]Phase 3: Configuration des clés API (optionnelle)[/]")
    suggestions = await get_config_suggestions()
    key_suggestions = [s for s in suggestions if s.sensitive]

    if not auto and key_suggestions:
        keys_params = {}
        for s in key_suggestions:
            val = click.prompt(f"  {s.label} (laisser vide pour ignorer)", default="", hide_input=True)
            if val:
                keys_params[f"provider_{s.key.replace('provider_', '')}"] = val

        if keys_params:
            result = await execute_step({"step_id": "api_keys", "params": keys_params})
            if result.success:
                console.print(f"  [green]✓ {result.output}[/]")
            else:
                console.print(f"  [red]✗ {result.error}[/]")

    console.print()
    console.print(Panel.fit("[bold green]✓ Installation terminée ![/]", border_style="green"))
    console.print("\nCommandes utiles :")
    console.print("  [cyan]ciel[/]           — Lancer le chat")
    console.print("  [cyan]ciel-api[/]       — Démarrer le serveur web")
    console.print("  [cyan]ciel doctor[/]    — Vérifier l'installation")
    console.print("  [cyan]ciel serve[/]     — Lancer le serveur API")


@install_cli.command()
def suggest():
    """Affiche les suggestions de configuration."""
    import asyncio
    asyncio.run(_do_suggest())


async def _do_suggest():
    from ciel.api.routes.install import get_config_suggestions
    suggestions = await get_config_suggestions()
    t = Table(box=box.HEAVY_EDGE)
    t.add_column("Clé", style="cyan")
    t.add_column("Description", style="white")
    t.add_column("Défaut", style="yellow")
    t.add_column("Actuel", style="green")
    for s in suggestions:
        current = s.current if s.current else "[dim]non défini[/]"
        if s.sensitive and s.current:
            current = "[green]••••[/]"
        t.add_row(s.key, s.description, s.default, current)
    console.print(t)
