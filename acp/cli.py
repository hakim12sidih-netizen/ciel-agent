from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .server import ACPServer
from .tools import get_all_tools, get_tools_by_category
from .ide import generate_vscode_extension, generate_cursor_rules

console = Console()


@click.group(name="acp")
def acp_group():
    """Agent Communication Protocol — intégration IDE et agents.

    Serveur ACP pour connecter CIEL aux IDE (VS Code, Cursor, etc.)
    et aux autres agents via WebSocket ou stdio (JSON-RPC 2.0).
    """


@acp_group.command()
@click.option("--ws-port", default=9876, help="Port WebSocket (défaut: 9876)")
@click.option("--host", default="127.0.0.1", help="Interface d'écoute")
@click.option("--stdio", is_flag=True, help="Activer aussi le transport stdio")
def start(ws_port: int, host: str, stdio: bool):
    """Démarre le serveur ACP."""
    server = ACPServer(host=host, ws_port=ws_port)

    async def _run():
        await server.start()
        console.print(Panel(
            f"[bold green]Serveur ACP démarré[/]\n"
            f"  WebSocket : [cyan]ws://{host}:{ws_port}[/]\n"
            f"  Outils    : {len(get_all_tools())} enregistrés\n"
            f"  Stdio     : {'✓' if stdio else '✗'}",
            box=box.ROUNDED,
        ))
        if stdio:
            await server.serve_stdio()
        else:
            while True:
                await asyncio.sleep(3600)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Arrêt du serveur ACP...[/]")
        asyncio.run(server.stop())


@acp_group.command()
def tools():
    """Liste les outils ACP disponibles."""
    all_tools = get_all_tools()
    categories = sorted(set(c for t in all_tools for c in t.categories))

    table = Table(title=f"Outils ACP ({len(all_tools)})", box=box.ROUNDED)
    table.add_column("Outil", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Catégories", style="yellow")
    table.add_column("Scope", style="magenta")

    for t in all_tools:
        table.add_row(
            t.name,
            t.description[:60],
            ", ".join(t.categories),
            t.scope.value,
        )
    console.print(table)

    console.print(f"\n[bold]Catégories[/]: {', '.join(categories)}")
    for cat in categories:
        cat_tools = get_tools_by_category(cat)
        console.print(f"  [cyan]{cat}[/]: {len(cat_tools)} outils")


@acp_group.command()
@click.option("--output-dir", default="./vscode-ciel",
              help="Répertoire de sortie (défaut: ./vscode-ciel)")
def generate_vscode(output_dir: str):
    """Génère l'extension VS Code."""
    target = Path(output_dir).resolve()
    files = generate_vscode_extension(str(target))
    console.print(f"[green]✓[/] Extension VS Code générée dans {target}")
    for f in files:
        console.print(f"  [dim]•[/] {f}")
    console.print("\n[yellow]Pour installer:[/]")
    console.print(f"  cd {target} && npm install && npm run compile")
    console.print("  Copier le dossier dans ~/.vscode/extensions/")


@acp_group.command()
@click.option("--output-dir", default=".",
              help="Répertoire du projet (défaut: .)")
def generate_cursor(output_dir: str):
    """Génère les règles Cursor AI."""
    target = Path(output_dir).resolve()
    generate_cursor_rules(str(target))
    console.print(f"[green]✓[/] Règles Cursor générées dans {target}")
    console.print(f"  [dim]•[/] .cursorrules")
    console.print(f"  [dim]•[/] .cursor/rules/ciel-agent.mdc")


@acp_group.command()
@click.argument("message")
@click.option("--host", default="127.0.0.1", help="Hôte ACP")
@click.option("--port", default=9876, help="Port ACP")
@click.option("--tool", default=None, help="Outil ACP à appeler")
def call(message: str, host: str, port: int, tool: str | None):
    """Appelle un outil ACP ou envoie un message."""
    async def _call():
        import websockets
        uri = f"ws://{host}:{port}"
        async with websockets.connect(uri) as ws:
            # Initialize
            await ws.send(json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {},
            }))
            resp = json.loads(await ws.recv())

            if tool:
                method = "acp/tools/call"
                params = {"name": tool, "arguments": {"message": message}}
            else:
                method = "acp/tools/call"
                params = {"name": "ciel_chat", "arguments": {"message": message}}

            await ws.send(json.dumps({
                "jsonrpc": "2.0", "id": 2, "method": method, "params": params,
            }))
            resp = json.loads(await ws.recv())
            console.print_json(json.dumps(resp, indent=2))

    asyncio.run(_call())
