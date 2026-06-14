"""
CIEL v∞.8 — Plugin CLI.
`ciel plugin` commands for management.
"""
from __future__ import annotations

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.table import Table
from rich.panel import Panel
from rich.box import HEAVY_EDGE
from rich.markdown import Markdown

from ciel.plugins.core import PluginManifest, PluginError, PluginDependencyError, get_registry


console = Console()


def _format_bool(v: bool) -> str:
    return "[green]✓[/]" if v else "[red]✗[/]"


def _format_plugins_table(plugins: list[tuple[str, PluginManifest, bool]]) -> Table:
    table = Table(box=HEAVY_EDGE)
    table.add_column("Plugin", style="cyan")
    table.add_column("Version", style="yellow")
    table.add_column("Auteur", style="blue")
    table.add_column("Chargé", justify="center")
    table.add_column("Activé", justify="center")
    for name, manifest, loaded in plugins:
        table.add_row(
            name,
            manifest.version,
            manifest.author or "-",
            _format_bool(loaded),
            _format_bool(loaded),
        )
    return table


@click.group(name="plugin")
def plugin_group():
    """Gère les plugins CIEL."""


@plugin_group.command(name="list")
@click.option("--all", "-a", "show_all", is_flag=True, help="Affiche aussi les plugins non chargés")
def list_plugins(show_all: bool):
    """Liste les plugins découverts."""
    registry = get_registry()
    discovered = registry.discover()
    loaded = {n for n in registry._plugins}
    items = registry.list()
    if not show_all:
        items = [(n, m, l) for n, m, l in items if l]

    if not items:
        if discovered:
            console.print("[yellow]Aucun plugin chargé. `ciel plugin load <name>`[/]")
        else:
            console.print("[yellow]Aucun plugin trouvé dans les répertoires :[/]")
            for d in registry._plugin_dirs:
                console.print(f"  [dim]{d}[/]")
        return

    console.print(_format_plugins_table(items))
    console.print(f"\n[dim]{len(items)} plugin(s) — "
                  f"{len(loaded)} chargé(s) sur {len(discovered)} découvert(s)[/]")

    if discovered and not show_all:
        unloaded = [n for n, _, _ in registry.list() if n not in loaded]
        if unloaded:
            console.print(f"\n[dim]Non chargés : {', '.join(unloaded)}[/]")


@plugin_group.command(name="discover")
def discover_plugins():
    """(Re)découvre les plugins dans les répertoires."""
    registry = get_registry()
    found = registry.discover()
    if found:
        console.print(f"[green]✓[/] {len(found)} plugin(s) découvert(s) :")
        for m in found:
            console.print(f"  [cyan]{m.name}[/] v{m.version} — {m.description}")
    else:
        console.print("[yellow]Aucun plugin trouvé.[/]")
        console.print("[dim]Répertoires scannés :[/]")
        for d in registry._plugin_dirs:
            console.print(f"  [dim]{d}[/]")
        console.print("[dim]Créez `~/mon_plugin/plugin.json`[/]")


@plugin_group.command(name="load")
@click.argument("name")
def load_plugin(name: str):
    """Charge un plugin par son nom."""
    import asyncio
    registry = get_registry()
    registry.discover()
    try:
        plugin = asyncio.run(registry.load_plugin(name))
        if plugin:
            console.print(f"[green]✓[/] Plugin [cyan]{name}[/] v{plugin.manifest.version} chargé")
        else:
            console.print(f"[red]✗[/] Plugin {name} introuvable")
    except PluginDependencyError as e:
        console.print(f"[red]✗ Dépendance: {e}[/]")
    except PluginError as e:
        console.print(f"[red]✗ {e}[/]")


@plugin_group.command(name="unload")
@click.argument("name")
def unload_plugin(name: str):
    """Décharge un plugin."""
    import asyncio
    registry = get_registry()
    if name in registry._plugins:
        asyncio.run(registry.unload_plugin(name))
        console.print(f"[yellow]⊘[/] Plugin [cyan]{name}[/] déchargé")
    else:
        console.print(f"[red]✗[/] Plugin {name} non chargé")


@plugin_group.command(name="enable")
@click.argument("name")
def enable_plugin(name: str):
    """Active un plugin."""
    import asyncio
    registry = get_registry()
    if name not in registry._plugins:
        console.print(f"[red]✗[/] Plugin {name} non chargé. Utilisez `ciel plugin load {name}` d'abord.")
        return
    success = asyncio.run(registry.enable_plugin(name))
    if success:
        console.print(f"[green]✓[/] Plugin [cyan]{name}[/] activé")
    else:
        console.print(f"[red]✗[/] Impossible d'activer {name}")


@plugin_group.command(name="disable")
@click.argument("name")
def disable_plugin(name: str):
    """Désactive un plugin."""
    import asyncio
    registry = get_registry()
    if name not in registry._plugins:
        console.print(f"[red]✗[/] Plugin {name} non chargé")
        return
    success = asyncio.run(registry.disable_plugin(name))
    if success:
        console.print(f"[yellow]⊘[/] Plugin [cyan]{name}[/] désactivé")
    else:
        console.print(f"[red]✗[/] Impossible de désactiver {name}")


@plugin_group.command(name="reload")
@click.argument("name")
def reload_plugin(name: str):
    """Recharge un plugin (hot-reload)."""
    import asyncio
    registry = get_registry()
    if name in registry._plugins:
        console.print(f"[yellow]↻[/] Rechargement de [cyan]{name}[/]...")
        try:
            plugin = asyncio.run(registry.reload_plugin(name))
            if plugin:
                console.print(f"[green]✓[/] Plugin [cyan]{name}[/] v{plugin.manifest.version} rechargé")
            else:
                console.print(f"[red]✗[/] Échec du rechargement")
        except Exception as e:
            console.print(f"[red]✗[/] {e}")
    else:
        console.print(f"[red]✗[/] Plugin {name} non chargé")


@plugin_group.command(name="info")
@click.argument("name")
def plugin_info(name: str):
    """Affiche les détails d'un plugin."""
    registry = get_registry()
    registry.discover()
    manifest = registry._manifests.get(name)
    if not manifest:
        console.print(f"[red]✗[/] Plugin {name} inconnu")
        return
    loaded = name in registry._plugins
    detail = (
        f"[bold]Nom[/]        : [cyan]{manifest.name}[/]\n"
        f"[bold]Version[/]    : {manifest.version}\n"
        f"[bold]Description[/]: {manifest.description or '-'}\n"
        f"[bold]Auteur[/]     : {manifest.author or '-'}\n"
        f"[bold]Licence[/]    : {manifest.license}\n"
        f"[bold]Entrypoint[/] : {manifest.entrypoint or '(auto)'}\n"
        f"[bold]Dépendances[/]: {', '.join(manifest.dependencies) or '(aucune)'}\n"
        f"[bold]Permissions[/]: {', '.join(manifest.permissions) or '(aucune)'}\n"
        f"[bold]Tags[/]       : {', '.join(manifest.tags) or '-'}\n"
        f"[bold]CIEL min[/]   : {manifest.min_ciel_version}\n"
        f"[bold]Chargé[/]     : {'✓' if loaded else '✗'}\n"
    )
    if manifest.homepage:
        detail += f"[bold]Site[/]       : {manifest.homepage}\n"
    if manifest.repository:
        detail += f"[bold]Repo[/]       : {manifest.repository}\n"
    if manifest.documentation:
        detail += f"[bold]Docs[/]       : {manifest.documentation}\n"

    console.print(Panel(detail, title=f"[bold]Plugin: {name}[/]"))


@plugin_group.command(name="install")
@click.argument("source")
@click.option("--dev", is_flag=True, help="Installer en mode développement (symlink)")
@click.option("--force", is_flag=True, help="Forcer la réinstallation")
def install_plugin(source: str, dev: bool, force: bool):
    """Installe un plugin depuis un chemin local, une archive ou un dépôt git.

    SOURCE peut être :
    \b
    * Un chemin local : /chemin/vers/plugin/
    * Une archive     : plugin.tar.gz, plugin.zip
    * Une URL git     : https://github.com/user/plugin.git
    """
    import asyncio
    registry = get_registry()

    target_dir = Path.home() / ".ciel" / "plugins"
    target_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(source).expanduser().resolve()
    plugin_name = None

    if source_path.is_dir():
        manifest_files = list(source_path.glob("plugin.json")) + list(source_path.glob("plugin.yaml")) + list(source_path.glob("plugin.yml"))
        if not manifest_files:
            console.print(f"[red]✗[/] Aucun plugin.json/trouvé dans {source}")
            return
        manifest = PluginManifest.from_dict(json.loads(manifest_files[0].read_text()))
        plugin_name = manifest.name
        dest = target_dir / plugin_name
        if dest.exists() and not force:
            console.print(f"[red]✗[/] Plugin [cyan]{plugin_name}[/] déjà installé. Utilisez --force pour réinstaller.")
            return
        if dest.exists():
            shutil.rmtree(dest)
        if dev:
            os.symlink(str(source_path), str(dest))
            console.print(f"[green]✓[/] Plugin [cyan]{plugin_name}[/] lié (dev) depuis {source}")
        else:
            shutil.copytree(source_path, dest)
            console.print(f"[green]✓[/] Plugin [cyan]{plugin_name}[/] installé depuis {source}")

    elif source.endswith((".tar.gz", ".tgz", ".zip")):
        import tarfile, zipfile
        tmp = tempfile.mkdtemp()
        try:
            if source.endswith(".zip"):
                with zipfile.ZipFile(source) as zf:
                    zf.extractall(tmp)
            else:
                with tarfile.open(source) as tf:
                    tf.extractall(tmp)
            tmp_path = Path(tmp)
            subdirs = [d for d in tmp_path.iterdir() if d.is_dir()]
            plugin_root = subdirs[0] if subdirs else tmp_path
            manifest_files = list(plugin_root.glob("plugin.json"))
            if not manifest_files:
                console.print(f"[red]✗[/] Aucun plugin.json dans l'archive")
                return
            manifest = PluginManifest.from_dict(json.loads(manifest_files[0].read_text()))
            plugin_name = manifest.name
            dest = target_dir / plugin_name
            if dest.exists() and not force:
                console.print(f"[red]✗[/] Plugin déjà installé. --force pour réinstaller.")
                return
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(plugin_root, dest)
            console.print(f"[green]✓[/] Plugin [cyan]{plugin_name}[/] installé depuis {source}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    elif source.startswith(("http://", "https://", "git@", "git://")):
        import tempfile
        clone_dir = tempfile.mkdtemp()
        try:
            console.print(f"[dim]Clonage de {source}...[/]")
            r = subprocess.run(
                ["git", "clone", source, clone_dir],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode != 0:
                console.print(f"[red]✗[/] Échec git clone: {r.stderr.strip()}")
                return
            manifest_files = list(Path(clone_dir).glob("plugin.json")) + list(Path(clone_dir).glob("plugin.yaml"))
            if not manifest_files:
                console.print(f"[red]✗[/] Aucun plugin.json dans le dépôt")
                return
            manifest = PluginManifest.from_dict(json.loads(manifest_files[0].read_text()))
            plugin_name = manifest.name
            dest = target_dir / plugin_name
            if dest.exists() and not force:
                console.print(f"[red]✗[/] Plugin déjà installé. --force pour réinstaller.")
                return
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(clone_dir, dest)
            console.print(f"[green]✓[/] Plugin [cyan]{plugin_name}[/] installé depuis {source}")
        finally:
            shutil.rmtree(clone_dir, ignore_errors=True)
    else:
        console.print(f"[red]✗[/] Source non reconnue: {source}")
        return

    if plugin_name:
        registry.add_plugin_dir(target_dir)
        registry.discover()
        try:
            plugin = asyncio.run(registry.load_plugin(plugin_name))
            if plugin:
                console.print(f"[green]✓[/] Plugin [cyan]{plugin_name}[/] chargé et activé")
        except Exception as e:
            console.print(f"[yellow]⚠[/] Plugin installé mais non chargé: {e}")


@plugin_group.command(name="remove")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Confirmer la suppression")
def remove_plugin(name: str, yes: bool):
    """Supprime un plugin installé."""
    import asyncio
    registry = get_registry()

    if name in registry._plugins:
        asyncio.run(registry.unload_plugin(name))

    plugin_dirs = [d / name for d in registry._plugin_dirs]
    existing = [d for d in plugin_dirs if d.exists()]
    if not existing:
        console.print(f"[red]✗[/] Plugin {name} non trouvé dans les répertoires")
        return

    if not yes:
        click.confirm(f"Supprimer définitivement le plugin {name} ?", abort=True)

    for d in existing:
        shutil.rmtree(d)
        console.print(f"[yellow]⊘[/] {d} supprimé")

    registry._manifests.pop(name, None)
    console.print(f"[green]✓[/] Plugin [cyan]{name}[/] supprimé")


@plugin_group.command(name="create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Description du plugin")
@click.option("--author", "-a", default="", help="Auteur")
@click.option("--version", "-v", default="0.1.0", help="Version initiale")
def create_plugin(name: str, description: str, author: str, version: str):
    """Crée un squelette de plugin."""
    target = Path.cwd() / name
    if target.exists():
        console.print(f"[red]✗[/] {target} existe déjà")
        return

    target.mkdir(parents=True)

    manifest = {
        "name": name,
        "version": version,
        "description": description or f"Plugin {name} for CIEL",
        "author": author or "",
        "entrypoint": f"ciel_plugins.{name}",
        "permissions": ["core"],
        "min_ciel_version": "1.0.0",
        "hooks": {
            "on_load": 0,
            "on_enable": 0,
        },
    }
    (target / "plugin.json").write_text(json.dumps(manifest, indent=2))
    (target / "__init__.py").write_text(f'''from ciel.plugins import PluginBase, PluginManifest


class {name.title().replace("-", "")}Plugin(PluginBase):
    manifest = PluginManifest(
        name="{name}",
        version="{version}",
        description="{description or f"Plugin {name} for CIEL"}",
    )

    async def on_load(self):
        print(f"  [green]✓ Plugin {{self.manifest.name}} chargé[/]")

    async def on_enable(self):
        print(f"  [green]✓ Plugin {{self.manifest.name}} activé[/]")

    async def on_disable(self):
        print(f"  [yellow]⊘ Plugin {{self.manifest.name}} désactivé[/]")
''')
    (target / "README.md").write_text(f"# {name}\n\n{description or f'Plugin {name} for CIEL'}\n")

    console.print(f"[green]✓[/] Plugin [cyan]{name}[/] créé dans {target}")
    console.print(f"  {target / 'plugin.json'}")
    console.print(f"  {target / '__init__.py'}")
    console.print(f"\n[dim]Pour installer: ciel plugin install {target}[/]")
