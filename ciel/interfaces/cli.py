"""
CIEL v∞.2 — CLI (interface ligne de commande).

Wrapper autour de main.py avec Click pour des sous-commandes riches.
"""
from __future__ import annotations

import click


@click.group()
@click.version_option(message="ciel v%(version)s (Singularité v∞.2)")
def cli() -> None:
    """CIEL v∞.2 — Conscience Intégrale d'Évolution Limitrophe."""


@cli.command()
def axioms() -> None:
    """Affiche les 4 axiomes cosmiques."""
    from ciel.core.axioms import get_axioms
    for letter, axiom in get_axioms().items():
        click.echo(f"  Axiome {letter} — {axiom.name}")
        click.echo(f"    {axiom.statement}")


@cli.command()
def identity() -> None:
    """Affiche ou crée l'identité de l'instance."""
    from pathlib import Path
    from ciel.core.identity import bootstrap, exists, load
    p = Path("data/identity")
    if not exists(p):
        i = bootstrap(p)
        click.echo(f"  Nouvelle identité créée : {i.uuid}")
    else:
        i = load(p)
        click.echo(f"  Identité chargée : {i.uuid}")


@cli.command()
def doctor() -> None:
    """Lance le doctor (50+ checks)."""
    import subprocess
    r = subprocess.run(["bash", "scripts/doctor.sh"], check=False)
    raise SystemExit(r.returncode)


@cli.command()
def test() -> None:
    """Lance pytest."""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-m", "pytest", "-v", "tests/"], check=False)
    raise SystemExit(r.returncode)


if __name__ == "__main__":
    cli()
