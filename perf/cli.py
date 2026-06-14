from __future__ import annotations

import importlib
import inspect
import logging
import time

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from ciel.perf.timing import Timer, timed, get_timings, reset_timings, Profiler

console = Console()
log = logging.getLogger("ciel.perf.cli")


@click.group(name="perf")
def perf_group():
    """Performance profiling et benchmarking.

    Mesure, profile et optimise les modules CIEL.
    """


@perf_group.command(name="profile")
@click.argument("target", default="ciel.skills.marketplace")
@click.option("--iterations", "-n", default=100, type=int,
              help="Nombre d'itérations (défaut: 100)")
@click.option("--warmup", "-w", default=3, type=int,
              help="Nombre d'itérations de warmup (défaut: 3)")
@click.option("--module", "-m", is_flag=True,
              help="Profile toutes les fonctions du module")
@click.option("--top", "-t", default=20, type=int,
              help="Nombre de résultats à afficher (défaut: 20)")
@click.option("--json", "json_out", is_flag=True,
              help="Sortie JSON")
def profile_cmd(target: str, iterations: int, warmup: int,
                module: bool, top: int, json_out: bool):
    """Profile une fonction ou un module CIEL.

    CIBLE peut être :
      - Un importable (ciel.mesh.node)
      - Un nom qualifié (ciel.mesh.node.MeshNode.start)

    Exemples :
      ciel perf profile ciel.skills.marketplace.SkillMarketplace.search
      ciel perf profile ciel.mesh.node -m  # toutes les fonctions du module
      ciel perf profile ciel.acp.tools --iterations 500
    """
    profiler = Profiler(warmup=warmup)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Profiling...", total=iterations + warmup)

        try:
            if module:
                results = profiler.run_module(target, iterations=iterations)
            else:
                fn = _resolve_target(target)
                stats = profiler.run(fn, iterations=iterations, label=target)
                results = {target: stats}
            progress.update(task, completed=iterations + warmup)
        except Exception as e:
            progress.update(task, completed=iterations + warmup)
            console.print(f"[red]Erreur :[/] {e}")
            raise click.Abort()

    summary = profiler.summary()

    if json_out:
        import json
        console.print(json.dumps(summary, indent=2))
        return

    if not summary:
        console.print("[yellow]Aucun résultat[/]")
        return

    table = Table(
        title=f"Profil — {target} ({iterations} itérations)",
        box=box.ROUNDED,
    )
    table.add_column("Fonction", style="cyan")
    table.add_column("Avg", style="green", justify="right")
    table.add_column("Min", style="dim", justify="right")
    table.add_column("Max", style="red", justify="right")
    table.add_column("P50", style="white", justify="right")
    table.add_column("P95", style="yellow", justify="right")
    table.add_column("P99", style="magenta", justify="right")
    table.add_column("N", style="blue", justify="right")

    for row in summary[:top]:
        table.add_row(
            row["key"][:60],
            f"{row['avg_ms']:.2f}",
            f"{row['min_ms']:.2f}",
            f"{row['max_ms']:.2f}",
            f"{row['p50_ms']:.2f}",
            f"{row['p95_ms']:.2f}",
            f"{row['p99_ms']:.2f}",
            str(row["count"]),
        )
    console.print(table)

    # suggestion si point chaud
    if summary and summary[0]["avg_ms"] > 50:
        console.print(f"\n[yellow]⚠ Point chaud :[/] {summary[0]['key']} "
                      f"({summary[0]['avg_ms']:.1f} ms en moyenne)")


@perf_group.command(name="timings")
def timings_cmd():
    """Affiche les chronos enregistrés via @timed / Timer."""
    stats = get_timings()
    if not stats:
        console.print("[yellow]Aucun chrono enregistré[/]")
        console.print("Utilisez le décorateur @timed ou Timer() dans votre code.")
        return

    table = Table(title="Chronos enregistrés", box=box.ROUNDED)
    table.add_column("Clé", style="cyan")
    table.add_column("N", style="blue", justify="right")
    table.add_column("Total", style="dim", justify="right")
    table.add_column("Moy", style="green", justify="right")
    table.add_column("P95", style="yellow", justify="right")

    sorted_stats = sorted(stats.items(), key=lambda kv: -kv[1]["total_ms"])
    for key, s in sorted_stats:
        table.add_row(
            key[:60],
            str(s["count"]),
            f"{s['total_ms']:.1f}",
            f"{s['avg_ms']:.2f}",
            f"{s['p95_ms']:.2f}",
        )
    console.print(table)


@perf_group.command(name="reset")
def reset_cmd():
    """Réinitialise tous les chronos."""
    reset_timings()
    console.print("[green]✓[/] Chronos réinitialisés")


@perf_group.command(name="doctor")
@click.option("--quick", is_flag=True, help="Mode rapide (5 itérations)")
def doctor_cmd(quick: bool):
    """Diagnostic de performance CIEL.

    Mesure les temps de démarrage des modules principaux
    et détecte les goulots d'étranglement.
    """
    n = 5 if quick else 20
    targets = [
        "ciel.skills.marketplace.SkillMarketplace.stats",
        "ciel.skills.marketplace.SkillMarketplace.categories",
        "ciel.skills.marketplace.SkillMarketplace.search",
        "ciel.skills.models.SkillManager.discover",
        "ciel.mesh.identity.NodeIdentity.generate",
        "ciel.skills.marketplace.CatalogueEntry.to_dict",
    ]

    profiler = Profiler(warmup=1)

    console.print(Panel(
        "[bold]Perf Doctor[/bold] — Diagnostic des performances CIEL\n\n"
        f"Modules testés : {len(targets)}\n"
        f"Itérations : {n}",
        box=box.ROUNDED,
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Test...", total=len(targets) * n)

        results = []
        for t in targets:
            try:
                fn = _resolve_target(t)
                stats = profiler.run(fn, iterations=n, label=t)
                results.append((t, stats))
            except Exception as e:
                results.append((t, {"avg_ms": -1, "error": str(e)}))
            progress.update(task, advance=n)

    # Afficher
    hot = []
    table = Table(box=box.SIMPLE)
    table.add_column("Fonction", style="cyan")
    table.add_column("Avg", style="green", justify="right")
    table.add_column("Min", style="dim", justify="right")
    table.add_column("Max", style="red", justify="right")

    for name, s in sorted(results, key=lambda r: -r[1].get("avg_ms", 0)):
        if "error" in s:
            table.add_row(name[:55], "[red]ERR[/]", "", f"[red]{s['error']}[/]")
        else:
            avg_str = f"{s['avg_ms']:.2f}"
            if s["avg_ms"] > 50:
                avg_str = f"[yellow]{avg_str}[/]"
                hot.append(name)
            table.add_row(
                name[:55],
                avg_str,
                f"{s['min_ms']:.2f}",
                f"{s['max_ms']:.2f}",
            )

    console.print(table)

    if hot:
        console.print(f"\n[yellow]⚠ {len(hot)} point(s) chaud(s) détecté(s) :[/]")
        for h in hot:
            console.print(f"  • {h}")
        console.print("\n[dim]Conseil : utilisez 'ciel perf profile <fonction> -n 500' "
                      "pour un diagnostic approfondi[/]")
    else:
        console.print("\n[green]✓[/] Aucun point chaud détecté")


def _resolve_target(target: str) -> callable:
    """Résout une chaîne comme 'module.Cls.method' en callable prêt à appeler.

    Gère :
      - Fonctions module : module.fn
      - Méthodes d'instance : module.Cls.method → instance auto-créée
      - Classmethods / staticmethods : résolues directement
    """
    parts = target.split(".")
    for i in range(len(parts), 0, -1):
        module_name = ".".join(parts[:i])
        try:
            mod = importlib.import_module(module_name)
            break
        except ImportError:
            continue
    else:
        raise ImportError(f"Impossible d'importer '{target}'")

    # remaining = attributs à résoudre dans le module
    remaining = parts[i:]

    # Cas 1: fonction module directement (1 attribut)
    if len(remaining) == 1:
        fn = getattr(mod, remaining[0])
        if callable(fn):
            return fn
        raise TypeError(f"{target} n'est pas callable")

    # Cas 2: module.Cls.method
    # On descend dans le module : le premier attribut est la classe / objet intermédiaire
    obj = getattr(mod, remaining[0])
    method_name = remaining[1]

    if inspect.isclass(obj):
        # C'est une classe — méthode d'instance
        method = getattr(obj, method_name)
        if isinstance(method, (classmethod, staticmethod)) or (
            hasattr(method, '__self__') and method.__self__ is obj
        ):
            # déjà bound (classmethod) ou staticmethod
            return method
        # créer une instance et binder
        try:
            # Essayer sans args
            instance = obj()
        except Exception:
            # Échec — essayer de construire avec des args par défaut pour les dataclasses
            try:
                import dataclasses
                if dataclasses.is_dataclass(obj):
                    fields = dataclasses.fields(obj)
                    kwargs = {}
                    for f in fields:
                        if hasattr(f, 'default') and f.default is not dataclasses.MISSING:
                            kwargs[f.name] = f.default
                        elif hasattr(f, 'default_factory') and f.default_factory is not dataclasses.MISSING:
                            kwargs[f.name] = f.default_factory()
                        else:
                            # type-based default
                            if f.type in (str,):
                                kwargs[f.name] = ""
                            elif f.type in (int, float):
                                kwargs[f.name] = 0
                            elif f.type in (list,):
                                kwargs[f.name] = []
                            elif f.type in (dict,):
                                kwargs[f.name] = {}
                            else:
                                kwargs[f.name] = None
                    instance = obj(**kwargs)
                else:
                    # Dernier recours : binder sans instance
                    return method
            except Exception:
                return method
        bound = method.__get__(instance, obj)
        return bound
    else:
        # objet existant — méthode déjà potentiellement bound
        return getattr(obj, method_name)
