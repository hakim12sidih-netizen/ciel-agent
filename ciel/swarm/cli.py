from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ciel.swarm import SwarmEngine, Role, PeerState
from ciel.swarm.gateway_bridge import SwarmGatewayBridge

console = Console()


@click.group(name="swarm")
def swarm_group():
    """Essaim CIEL-NET — fédération P2P, consensus, FL.

    Connecte CIEL à d'autres instances pour former un essaim
    distribué avec découverte de pairs, consensus Raft/PBFT,
    et apprentissage fédéré (FedAvg).
    """


@swarm_group.command()
@click.option("--namespace", default="ciel-net", help="Namespace de l'essaim")
@click.option("--seed", default="", help="Adresse du seed (pair connu)")
@click.option("--role", default="ouvriere",
              type=click.Choice(["reine", "ouvriere", "eclaireuse", "gardienne", "mere"]))
@click.option("--id", "peer_id", default="", help="ID du pair")
def start(namespace: str, seed: str, role: str, peer_id: str):
    """Rejoint ou crée un essaim."""
    engine = SwarmEngine(peer_id=peer_id or "", namespace=namespace)
    try:
        engine.set_role(Role(role))
    except ValueError:
        console.print(f"[red]Rôle inconnu : {role}[/]")
        return

    peer = engine.join(seed_address=seed)
    console.print(Panel(
        f"[bold green]Essaim CIEL-NET[/]\n\n"
        f"  Peer ID  : {engine.peer_id}\n"
        f"  Rôle     : {engine.role.value}\n"
        f"  Namespace: {namespace}\n"
        f"  Seed     : {seed or '(aucun)'}\n"
        f"  État     : {peer.state.name if peer else 'inconnu'}",
        box=box.ROUNDED,
    ))

    console.print("\n[dim]Commandes disponibles :[/]")
    console.print("  [cyan]ciel swarm status[/]    État de l'essaim")
    console.print("  [cyan]ciel swarm peers[/]     Pairs découverts")
    console.print("  [cyan]ciel swarm broadcast[/] Diffuser un message")


@swarm_group.command()
def status():
    """État de l'essaim local."""
    engine = SwarmEngine()
    stats = engine.get_stats()
    table = Table(box=box.HEAVY_EDGE)
    table.add_column("Métrique", style="cyan")
    table.add_column("Valeur", style="green")
    table.add_row("Peer ID", stats["peer_id"])
    table.add_row("Rôle", stats["role"])
    table.add_row("Pairs découverts", str(stats["peers_discovered"]))
    table.add_row("Pairs actifs", str(stats["peers_active"]))
    table.add_row("Messages envoyés", str(stats["messages_sent"]))
    table.add_row("Messages reçus", str(stats["messages_received"]))
    table.add_row("Raft term", str(stats["raft_term"]))
    table.add_row("Raft rôle", stats["raft_role"])
    table.add_row("Raft log", str(stats["raft_log_size"]))
    table.add_row("PBFT vue", str(stats["pbft_view"]))
    table.add_row("FL round", str(stats["fed_round"]))
    console.print(table)


@swarm_group.command()
def peers():
    """Liste les pairs découverts."""
    engine = SwarmEngine()
    all_peers = engine.discovery.all_peers()
    if not all_peers:
        console.print("[yellow]Aucun pair découvert[/]")
        return
    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Rôle", style="yellow")
    table.add_column("État")
    table.add_column("Adresse", style="blue")
    table.add_column("Dernière vue")
    table.add_column("Confiance")
    for p in all_peers:
        state_style = {
            PeerState.OFFLINE: "red", PeerState.DISCOVERED: "yellow",
            PeerState.CONNECTED: "green", PeerState.SYNCED: "cyan",
            PeerState.FAULTY: "red",
        }.get(p.state, "")
        last_seen = f"{time.time() - p.last_seen:.0f}s" if p.last_seen else "-"
        table.add_row(
            p.peer_id[:16], p.role.value,
            f"[{state_style}]{p.state.name}[/]",
            p.address or "-", last_seen, f"{p.trust_score:.2f}",
        )
    console.print(table)


@swarm_group.command()
@click.argument("content")
@click.option("--target", default="", help="Pair cible (vide = broadcast)")
@click.option("--msg-type", default="data", help="Type de message")
def send(content: str, target: str, msg_type: str):
    """Envoie un message à un pair ou broadcast."""
    engine = SwarmEngine()
    if target:
        msg = engine.send_message(target, content, msg_type)
        if msg:
            console.print(f"[green]✓[/] Message envoyé à {target[:16]}...")
        else:
            console.print(f"[red]✗[/] Pair {target[:16]}... introuvable ou hors ligne")
    else:
        peers = engine.discovery.active_peers()
        sent = 0
        for p in peers:
            msg = engine.send_message(p.peer_id, content, msg_type)
            if msg:
                sent += 1
        console.print(f"[green]✓[/] Message diffusé à {sent}/{len(peers)} pairs")


@swarm_group.command()
@click.argument("command")
@click.option("--data", default="{}", help="Données JSON")
def raft(command: str, data: str):
    """Propose une commande Raft au consensus."""
    engine = SwarmEngine()
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError:
        data_dict = {}
    entry = engine.raft_append(command, data_dict)
    console.print(f"[green]✓[/] Commande Raft index {entry.index}, term {entry.term}")


@swarm_group.command()
@click.option("--request", "req", default="{}", help="Requête JSON")
def pbft(req: str):
    """Propose une requête PBFT."""
    engine = SwarmEngine()
    try:
        req_dict = json.loads(req)
    except json.JSONDecodeError:
        req_dict = {}
    msg = engine.pbft_propose(req_dict)
    console.print(f"[green]✓[/] PBFT sequence {msg.get('sequence')}")


@swarm_group.command()
@click.option("--rounds", default=1, type=int, help="Nombre de rounds FL")
def federate(rounds: int):
    """Lance un round d'apprentissage fédéré."""
    engine = SwarmEngine()
    for r in range(rounds):
        updates = [
            {"peer_id": engine.peer_id, "weights": [0.5, 0.3, 0.2],
             "n_samples": 100, "accuracy": 0.85 + r * 0.01},
        ]
        agg = engine.federated_round(updates)
        console.print(f"  Round {engine.federated.get_round()}: {len(agg)} weights")
    console.print(f"[green]✓[/] {rounds} round(s) FL terminé(s)")
    console.print(f"  Historique: {engine.federated.get_history()}")


import json, time
