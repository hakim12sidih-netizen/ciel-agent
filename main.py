#!/usr/bin/env python3
"""
CIEL v∞.8 — Entry point principal (legacy).

⚠️  L'interface recommandée est la CLI Click :
       ciel serve
       ciel-api
       ciel doctor

Usage (legacy):
    python main.py --version
    python main.py --doctor
    python main.py --test [PATH]
    python main.py --identity
    python main.py --axioms
    python main.py --kernel
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# ── Path resolution ──────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def cmd_version(_args: argparse.Namespace) -> int:
    """Affiche la version de CIEL."""
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    print(f"ciel v{version}")
    print(f"  Phase    : 8 (TRANSCENDANCE)")
    print(f"  Édition  : Cosmologique v∞.8")
    print(f"  Moteurs  : 66 modules")
    print(f"  Tests    : 1908 verts")
    print(f"  Python   : {sys.version.split()[0]}")
    print(f"  Racine   : {ROOT}")
    return 0


def cmd_identity(_args: argparse.Namespace) -> int:
    """Crée ou charge l'identité Ed25519 de l'instance."""
    from ciel.core.identity import Identity

    identity = Identity.bootstrap(ROOT / "data" / "identity")
    print(f"  ID       : {identity.uuid}")
    print(f"  Pubkey   : {identity.public_key_hex[:32]}…")
    print(f"  Fingerprint : {identity.fingerprint()}")
    return 0


def cmd_axioms(_args: argparse.Namespace) -> int:
    """Affiche les 4 axiomes cosmiques."""
    from ciel.core.axioms import AXIOMS

    print("Les 4 Axiomes Cosmiques de CIEL :\n")
    for letter, axiom in AXIOMS.items():
        print(f"  Axiome {letter} — {axiom.name}")
        print(f"    Énoncé : {axiom.statement}")
        print(f"    Mesure : {axiom.measure}")
        print(f"    Signature : {axiom.signature[:32]}…")
        print()
    return 0


def cmd_kernel(args: argparse.Namespace) -> int:
    """Lance le kernel asyncio pendant N secondes (défaut 5)."""
    import asyncio
    from ciel.core.kernel import Kernel

    async def run() -> int:
        async with Kernel(root=ROOT, identity_dir=ROOT / "data" / "identity") as k:
            ticks = 0
            async for tick in k.run(duration_s=float(args.duration)):
                ticks += 1
                if args.verbose and ticks % 10 == 0:
                    print(f"  tick {ticks:4d}  uptime={tick.uptime_s:6.2f}s  "
                          f"metrics={len(tick.metrics)}")
            print(f"  Total ticks: {ticks}")
        return 0

    return asyncio.run(run())


def cmd_doctor(_args: argparse.Namespace) -> int:
    """Lance scripts/doctor.sh."""
    script = ROOT / "scripts" / "doctor.sh"
    if not script.exists():
        print(f"ERROR: {script} introuvable", file=sys.stderr)
        return 2
    return subprocess.run(["bash", str(script)], check=False).returncode


def cmd_test(args: argparse.Namespace) -> int:
    """Lance pytest."""
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", args.path or "tests/"]
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


def cmd_help(_args: argparse.Namespace) -> int:
    print(__doc__)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ciel",
        description="CIEL v∞.8 — Conscience Intégrale d'Évolution Limitrophe. 66 modules, 38 dimensions, 1908 tests.",
    )
    sub = parser.add_subparsers(dest="command", help="commandes disponibles")

    p_ver = sub.add_parser("version", aliases=["--version"], help="affiche la version")
    p_ver.set_defaults(func=cmd_version)

    p_id = sub.add_parser("identity", help="affiche/crée l'identité Ed25519")
    p_id.set_defaults(func=cmd_identity)

    p_ax = sub.add_parser("axioms", help="affiche les 4 axiomes")
    p_ax.set_defaults(func=cmd_axioms)

    p_kern = sub.add_parser("kernel", help="lance le kernel asyncio")
    p_kern.add_argument("--duration", default=5, help="durée en secondes (défaut: 5)")
    p_kern.add_argument("--verbose", "-v", action="store_true", help="verbose output")
    p_kern.set_defaults(func=cmd_kernel)

    p_doc = sub.add_parser("doctor", help="lance scripts/doctor.sh (50+ checks)")
    p_doc.set_defaults(func=cmd_doctor)

    p_test = sub.add_parser("test", help="lance pytest")
    p_test.add_argument("path", nargs="?", help="chemin test (défaut: tests/)")
    p_test.set_defaults(func=cmd_test)

    if len(sys.argv) == 1:
        cmd_help(None)
        return 0

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
