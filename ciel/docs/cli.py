from __future__ import annotations

import logging

import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
log = logging.getLogger("ciel.docs.cli")


@click.group(name="docs")
def docs_group():
    """Documentation auto-générée des modules CIEL.

    Génère des fichiers Markdown détaillés pour les
    modules mesh, ACP, et interfaces (backends, thèmes).
    """


@docs_group.command(name="generate")
@click.option("--output-dir", "-o", default="docs",
              help="Répertoire de sortie (défaut: docs/)")
@click.option("--modules", "-m", default="mesh,acp,interfaces",
              help="Modules à documenter (défaut: mesh,acp,interfaces)")
def generate(output_dir: str, modules: str):
    """Génère la documentation Markdown des modules CIEL.

    Parcourt les modules spécifiés, extrait les docstrings,
    signatures, et exporte en fichiers Markdown organisés.
    """
    from ciel.docs.generator import generate_all

    with console.status("[cyan]Génération de la documentation..."):
        try:
            generate_all(output_dir)
        except Exception as e:
            console.print(f"[red]Erreur :[/] {e}")
            raise click.Abort()

    console.print(f"\n[green]✓[/] Documentation générée dans [bold]{output_dir}/[/]")

    import os
    import glob
    files = sorted(glob.glob(os.path.join(output_dir, "**/*.md"), recursive=True))
    table = Table(box=box.SIMPLE)
    table.add_column("Fichier", style="cyan")
    table.add_column("Taille", style="green")
    for f in files:
        size = os.path.getsize(f)
        table.add_row(f, f"{size} o")
    if files:
        console.print(table)
    console.print(f"\n{len(files)} fichiers générés")


@docs_group.command(name="list")
def list_modules():
    """Liste les modules disponibles pour la documentation."""
    from ciel.docs.generator import MODULE_DOCS
    table = Table(title="Modules documentables", box=box.ROUNDED)
    table.add_column("Module", style="cyan")
    table.add_column("Description", style="white")
    for mod, desc in MODULE_DOCS.items():
        table.add_row(mod, desc)
    console.print(table)


@docs_group.command(name="module")
@click.argument("module_name")
@click.option("--title", "-t", default=None, help="Titre personnalisé")
def show_module(module_name: str, title: str | None):
    """Affiche la documentation d'un module spécifique dans la console."""
    from ciel.docs.generator import generate_module_doc
    try:
        full_name = f"ciel.{module_name}"
        content = generate_module_doc(full_name, title)
        console.print(content)
    except ImportError as e:
        console.print(f"[red]Erreur :[/] module [bold]{module_name}[/] introuvable : {e}")
        raise click.Abort()
