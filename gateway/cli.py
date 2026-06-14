from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ciel.gateway import (
    GatewayServer, GatewayState, GatewayAuth,
    install, uninstall, stop, is_running, get_pid,
)
from ciel.gateway.daemon import serve as daemon_serve

console = Console()


@click.group(name="gateway")
def gateway_group():
    """Gateway multi-plateforme — daemon, canaux, API.


    Point d'entrée central pour la messagerie CIEL.
    Connecte Telegram, Discord, Slack et plus.
    """


@gateway_group.command()
@click.option("--port", default=8787, help="Port de l'API REST (défaut: 8787)")
@click.option("--host", default="127.0.0.1", help="Interface d'écoute")
def start(port: int, host: str):
    """Démarre le serveur gateway en mode démon."""
    if is_running():
        console.print("[yellow]⚠ Gateway déjà en cours d'exécution[/]")
        pid = get_pid()
        console.print(f"  PID: {pid}")
        return

    console.print("[cyan]🚀 Démarrage du gateway CIEL...[/]")

    install_result = install()
    if install_result:
        console.print("[green]✓ Gateway installé comme service système[/]")
    else:
        console.print("[yellow]⚠ Mode foreground (pas de service manager trouvé)[/]")

    from ciel.gateway import GatewayServer
    server = GatewayServer()
    server.start()
    console.print(Panel(
        f"[bold green]Gateway CIEL démarré[/]\n"
        f"  API  : [cyan]http://{host}:{port}[/]\n"
        f"  PID  : {get_pid() or 'N/A'}\n"
        f"  État : {server.status()}",
        box=box.ROUNDED,
    ))


@gateway_group.command()
def stop_cmd():
    """Arrête le gateway."""
    if not is_running():
        console.print("[yellow]⚠ Gateway n'est pas en cours d'exécution[/]")
        return
    stop()
    console.print("[green]✓ Gateway arrêté[/]")


@gateway_group.command()
def status():
    """Affiche l'état du gateway."""
    state = GatewayState()
    running = is_running()

    if not running:
        console.print("[yellow]⚠ Gateway arrêté[/]")
    else:
        pid = get_pid()
        console.print(f"[green]✓ Gateway actif[/] (PID: {pid})")

    st = state.status()
    m = st["metrics"]

    table = Table(box=box.HEAVY_EDGE)
    table.add_column("Métrique", style="cyan")
    table.add_column("Valeur", style="green")
    table.add_row("Uptime", f"{m['uptime']:.0f}s")
    table.add_row("Messages", str(m["total_messages"]))
    table.add_row("Canaux", f"{m['active_channels']}/{st['channels']}")
    table.add_row("Sessions", str(st["sessions"]))
    table.add_row("Erreurs", str(m["errors_total"]))
    console.print(table)

    channels = state.list_channels()
    if channels:
        ch_table = Table(title="Canaux", box=box.ROUNDED)
        ch_table.add_column("ID", style="dim")
        ch_table.add_column("Plateforme", style="cyan")
        ch_table.add_column("État")
        ch_table.add_column("Messages ↑↓")
        for c in channels:
            status_str = "✓" if c.connected else "✗"
            style = "green" if c.connected else "red"
            ch_table.add_row(
                c.id[:16],
                c.platform,
                f"[{style}]{status_str}[/]",
                f"{c.messages_received}↓ {c.messages_sent}↑",
            )
        console.print(ch_table)


@gateway_group.command()
@click.option("--force", is_flag=True, help="Forcer la réinstallation")
def install_cmd(force: bool):
    """Installe le gateway comme service système."""
    if is_running() and not force:
        console.print("[yellow]⚠ Gateway déjà actif. Utilisez --force pour réinstaller.[/]")
        return
    if is_running():
        stop()
    result = install()
    if result:
        console.print("[green]✓ Gateway installé avec succès[/]")
    else:
        console.print("[red]✗ Échec de l'installation[/]")


@gateway_group.command()
def uninstall_cmd():
    """Désinstalle le service système."""
    if is_running():
        stop()
    from ciel.gateway.daemon import uninstall
    result = uninstall()
    if result:
        console.print("[green]✓ Gateway désinstallé[/]")
    else:
        console.print("[yellow]⚠ Aucun service à désinstaller[/]")


@gateway_group.command()
@click.option("--name", default="CIEL Device", help="Nom du périphérique")
def pair(name: str):
    """Génère un code d'appairage pour un nouveau périphérique."""
    auth = GatewayAuth()
    code, device_id = auth.generate_pairing_code(name)
    console.print(Panel(
        f"[bold cyan]Code d'appairage[/]\n\n"
        f"  [bold yellow]{code}[/]\n\n"
        f"  Périphérique : {name}\n"
        f"  ID : {device_id[:16]}...\n\n"
        f"[dim]Valable 5 minutes. Utilisez : ciel gateway verify {code}[/]",
        box=box.HEAVY,
    ))


@gateway_group.command()
@click.argument("code")
def verify(code: str):
    """Vérifie un code d'appairage."""
    auth = GatewayAuth()
    device_id = auth.verify_pairing(code.upper())
    if device_id:
        token = auth.create_session(device_id)
        console.print(f"[green]✓[/] Périphérique appairé avec succès !")
        console.print(f"  Token : [bold]{token[:24]}...[/]")
    else:
        console.print("[red]✗[/] Code invalide ou expiré")


@gateway_group.command()
def devices():
    """Liste les périphériques appairés."""
    auth = GatewayAuth()
    devs = auth.list_devices()
    if not devs:
        console.print("[yellow]Aucun périphérique appairé[/]")
        return
    table = Table(box=box.ROUNDED)
    table.add_column("Nom", style="cyan")
    table.add_column("ID")
    table.add_column("Vérifié")
    table.add_column("Dernière vue")
    for d in devs:
        verified = "✓" if d.verified else "✗"
        vstyle = "green" if d.verified else "red"
        last_seen = f"{time.time() - d.last_seen:.0f}s" if d.last_seen else "jamais"
        table.add_row(d.name, d.id[:16], f"[{vstyle}]{verified}[/]", last_seen)
    console.print(table)


@gateway_group.command()
@click.argument("device_id")
def remove_device(device_id: str):
    """Supprime un périphérique appairé."""
    auth = GatewayAuth()
    if auth.remove_device(device_id):
        console.print(f"[green]✓[/] Périphérique {device_id[:16]}... supprimé")
    else:
        console.print("[red]✗[/] Périphérique introuvable")


@gateway_group.command()
def log():
    """Affiche les logs du gateway."""
    log_file = Path.home() / ".ciel" / "gateway.log"
    if not log_file.exists():
        console.print("[yellow]Aucun fichier de log trouvé[/]")
        return
    content = log_file.read_text()
    lines = content.strip().split("\n")
    for line in lines[-50:]:
        console.print(line)


import time
