from __future__ import annotations

import json
import threading
import time
from typing import Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .node import MeshNode
from .identity import NodeIdentity

console = Console()


@click.group(name="mesh")
def mesh_group():
    """Commande maillage distribué (gRPC+QUIC).

    Démarre un nœud CIEL capable de se connecter à d'autres
    nœuds via gRPC, avec découverte de pairs, gossip, et
    consensus Raft distribué.
    """


@mesh_group.command()
@click.option("--port", default=0, help="Port d'écoute (défaut: port aléatoire)")
@click.option("--host", default="127.0.0.1", help="Interface d'écoute")
@click.option("--seeds", default="", help="Seeds (host:port, séparés par des virgules)")
@click.option("--data-dir", default=None, help="Répertoire des données du mesh")
@click.option("--name", default=None, help="Nom/ID du nœud")
def start(port: int, host: str, seeds: str, data_dir: str | None, name: str | None):
    """Démarre un nœud du mesh distribué."""
    identity = NodeIdentity.generate(peer_id=name) if name else NodeIdentity.generate()
    if data_dir:
        identity = NodeIdentity.load_or_generate(data_dir + "/identity.json")

    node = MeshNode(identity=identity, host=host, port=port, data_dir=data_dir)
    ok = node.start()
    if not ok:
        console.print("[red]✗[/] Échec du démarrage du nœud mesh")
        return

    seed_list = [s.strip() for s in seeds.split(",") if s.strip()]
    if seed_list:
        node.join(seed_list)

    console.print(Panel(
        f"[bold green]Nœud mesh démarré[/]\n"
        f"  Peer ID : [cyan]{identity.peer_id}[/]\n"
        f"  Adresse : [cyan]{host}:{node.port}[/]\n"
        f"  Seeds   : {', '.join(seed_list) if seed_list else 'aucune'}\n"
        f"  Fichier : [dim]{str(node.data_dir / 'identity.json')}[/]",
        box=box.ROUNDED,
    ))

    node.save_state()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Arrêt du nœud mesh...[/]")
        node.stop()
        console.print("[green]✓[/] Nœud arrêté")


@mesh_group.command()
@click.option("--port", default=0, help="Port d'écoute")
@click.option("--host", default="127.0.0.1", help="Interface d'écoute")
@click.option("--seeds", default="", help="Seeds")
@click.option("--name", default=None, help="Nom du nœud")
def once(port: int, host: str, seeds: str, name: str | None):
    """Démarre un nœud, exécute une action, puis s'arrête."""
    identity = NodeIdentity.generate(peer_id=name)
    node = MeshNode(identity=identity, host=host, port=port)
    node.start()

    seed_list = [s.strip() for s in seeds.split(",") if s.strip()]
    if seed_list:
        node.join(seed_list)
        time.sleep(1)

    stats = node.get_stats()
    peers = node.get_peers()
    console.print_json(json.dumps({
        "peer_id": stats["peer_id"],
        "port": stats["port"],
        "peers": stats["peers"],
        "active": stats["active_peers"],
        "raft_role": stats["raft_role"],
        "peers_list": peers,
    }, indent=2))
    node.stop()


@mesh_group.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=0)
@click.option("--name", default=None)
def status(host: str, port: int, name: str | None):
    """Affiche l'état du nœud mesh."""
    identity = NodeIdentity.generate(peer_id=name)
    node = MeshNode(identity=identity, host=host, port=port)
    node.start()
    stats = node.get_stats()
    peers = node.get_peers()

    table = Table(title=f"Mesh Node: {stats['peer_id']}", box=box.ROUNDED)
    table.add_column("Métrique", style="cyan")
    table.add_column("Valeur", style="green")
    table.add_row("Adresse", f"{stats['address']}:{stats['port']}")
    table.add_row("Namespace", stats["namespace"])
    table.add_row("Pairs découverts", str(stats["peers"]))
    table.add_row("Pairs actifs", str(stats["active_peers"]))
    table.add_row("Rôle Raft", stats["raft_role"])
    table.add_row("Terme Raft", str(stats["raft_term"]))
    table.add_row("Log Raft", str(stats["raft_log_size"]))
    table.add_row("Messages envoyés", str(stats["messages_sent"]))
    table.add_row("Messages reçus", str(stats["messages_received"]))
    table.add_row("Gossip envoyés", str(stats["gossip_sent"]))
    console.print(table)

    if peers:
        pt = Table(title="Pairs connectés", box=box.SIMPLE)
        pt.add_column("Peer ID", style="cyan")
        pt.add_column("Adresse", style="green")
        pt.add_column("Rôle", style="yellow")
        pt.add_column("État", style="magenta")
        pt.add_column("Latence", style="blue")
        for p in peers:
            pt.add_row(
                p["peer_id"][:20],
                f"{p['address']}:{p['port']}" if p["address"] else "-",
                p["role"], str(p["state"]),
                f"{p['latency_ms']:.1f}ms" if p["latency_ms"] else "-",
            )
        console.print(pt)
    node.stop()
