"""
CIEL — Portable Installer.

Bootstrap CIEL into ~/.ciel/ without pip or prior setup.
Can run as: python3 installer.py [--help]

Does NOT import any CIEL modules — zero dependencies required.
Uses only Python stdlib + subprocess for pip.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path


# ── Constants ─────────────────────────────────────────────

CIEL_HOME = Path.home() / ".ciel"
CIEL_VERSION = "1.0.0"
PYTHON_MIN = (3, 12)
REQUIRED_PIPS = [
    "cryptography>=42.0.0",
    "pydantic>=2.5.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "PyYAML>=6.0",
    "httpx>=0.27.0",
    "aiosqlite>=0.20.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "websockets>=12.0",
    "tomli-w>=1.0.0",
    "textual>=8.0.0",
]
OPTIONAL_PIPS = {
    "vision": ["mss>=9.0"],
    "control": ["pyautogui>=0.9.54", "pyperclip>=1.9.0", "notify-py>=0.3.0"],
    "web": ["duckduckgo_search>=7.0.0"],
    "test": ["pytest>=8.0.0"],
    "dev": ["ruff>=0.4.0", "mypy>=1.10.0"],
}


# ── Output helpers ────────────────────────────────────────

def _ok(msg: str, detail: str = "") -> None:
    line = f"  \033[92m\u2713\033[0m {msg}"
    if detail:
        line += f"  \033[90m{detail}\033[0m"
    print(line)


def _warn(msg: str, detail: str = "") -> None:
    line = f"  \033[93m\u26a0\033[0m {msg}"
    if detail:
        line += f"  \033[90m{detail}\033[0m"
    print(line)


def _err(msg: str, detail: str = "") -> None:
    line = f"  \033[91m\u2717\033[0m {msg}"
    if detail:
        line += f"  \033[90m{detail}\033[0m"
    print(line)


def _banner() -> None:
    print(textwrap.dedent("""\
        \033[96m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
        \u2551           \033[93mCIEL\033[96m \u2014 Portable Installer v""" + CIEL_VERSION + """  \u2551
        \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m
    """))


# ── Checks ────────────────────────────────────────────────

def _check_python() -> Path | None:
    """Find a suitable python3 binary."""
    for candidate in ["python3", "python"]:
        which = shutil.which(candidate)
        if which is None:
            continue
        try:
            ver = subprocess.run(
                [candidate, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            parts = tuple(int(x) for x in ver.split("."))
            if parts >= PYTHON_MIN:
                return Path(which)
        except (subprocess.CalledProcessError, ValueError):
            continue
    return None


def _check_pip(python: Path) -> bool:
    """Check if pip is available."""
    try:
        r = subprocess.run(
            [str(python), "-m", "pip", "--version"],
            capture_output=True, text=True,
        )
        return r.returncode == 0
    except FileNotFoundError:
        return False


def _ensure_pip(python: Path) -> bool:
    """Bootstrap pip if missing."""
    if _check_pip(python):
        return True
    _warn("pip not found — bootstrapping...")
    url = "https://bootstrap.pypa.io/get-pip.py"
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=15) as resp:
            script = resp.read()
        proc = subprocess.run([str(python)], input=script, capture_output=True)
        if proc.returncode != 0:
            _err("pip bootstrap failed", proc.stderr.decode()[:200])
            return False
        return _check_pip(python)
    except Exception as e:
        _err(f"pip bootstrap error: {e}")
        return False


# ── Directory structure ──────────────────────────────────

CIEL_DIRS = [
    "bin",
    "config",
    "data",
    "data/identity",
    "data/sessions",
    "cache",
    "cache/plugins",
    "logs",
    "plugins",
    "credentials",
]


def _create_dirs() -> None:
    """Create ~/.ciel/ directory structure."""
    for d in CIEL_DIRS:
        (CIEL_HOME / d).mkdir(parents=True, exist_ok=True)
    _ok("directory structure", str(CIEL_HOME))


# ── .pth file ─────────────────────────────────────────────

def _install_pth(source_root: Path) -> Path | None:
    """Install CIEL.pth into site-packages so `import ciel` works."""
    python = sys.executable
    try:
        r = subprocess.run(
            [python, "-c", "import site; print(site.getsitepackages()[0])"],
            capture_output=True, text=True, check=True,
        )
        site_pkg = Path(r.stdout.strip())
    except (subprocess.CalledProcessError, IndexError, OSError):
        try:
            r = subprocess.run(
                [python, "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                capture_output=True, text=True, check=True,
            )
            site_pkg = Path(r.stdout.strip())
        except Exception:
            _warn("could not determine site-packages path")
            return None

    pth = site_pkg / "CIEL.pth"
    pth.write_text(str(source_root.resolve()) + "\n")
    _ok("CIEL.pth installed", str(pth))
    return pth


# ── Shell PATH ────────────────────────────────────────────

def _install_path(bin_dir: Path) -> None:
    """Add ~/.ciel/bin to PATH via shell rc."""
    marker = "# --- CIEL PATH ---"
    line = f'export PATH="$PATH:{bin_dir}"'

    rc_files = []
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rc_files.append(Path.home() / ".zshrc")
    elif "bash" in shell:
        rc_files.append(Path.home() / ".bashrc")
        if platform.system() == "Darwin":
            rc_files.append(Path.home() / ".bash_profile")
    elif "fish" in shell:
        rc_files.append(Path.home() / ".config/fish/config.fish")

    for rc in rc_files:
        if not rc.exists():
            continue
        content = rc.read_text()
        if marker in content:
            continue
        rc.write_text(f"{content}\n{marker}\n{line}\n")
        _ok(f"PATH added to {rc.name}")

    if not rc_files:
        _warn("could not detect shell rc — add manually:", f'export PATH="$PATH:{bin_dir}"')


# ── Pip install ───────────────────────────────────────────

def _install_deps(python: Path, mode: str = "standard") -> bool:
    """Install required Python packages via pip."""
    extras = []
    if mode in ("dev", "all"):
        extras.extend(OPTIONAL_PIPS.get("dev", []))
        extras.extend(OPTIONAL_PIPS.get("test", []))
    if mode in ("all",):
        extras.extend(OPTIONAL_PIPS.get("web", []))
    all_deps = list(REQUIRED_PIPS) + extras

    _ok(f"installing {len(all_deps)} packages ({mode} mode)...")
    cmd = [str(python), "-m", "pip", "install", "--quiet"] + all_deps
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        _err("pip install failed", r.stderr[:300])
        return False
    _ok("dependencies installed")
    return True


# ── Config ────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "version": CIEL_VERSION,
    "api": {
        "host": "127.0.0.1",
        "port": 8765,
        "log_level": "INFO",
    },
    "brain": {
        "modules_autoload": True,
        "default_provider": "openai",
        "default_model": "gpt-4o",
    },
    "database": {
        "path": str(CIEL_HOME / "data" / "ciel.db"),
    },
    "providers": {},
    "plugins": {
        "dir": str(CIEL_HOME / "plugins"),
        "auto_load": True,
        "sandbox_enabled": True,
    },
    "security": {
        "api_keys": [],
    },
}


def _write_config() -> None:
    """Write default config if not present."""
    config_path = CIEL_HOME / "config" / "ciel.json"
    if config_path.exists():
        _ok("config already exists", str(config_path))
        return
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
    _ok("config written", str(config_path))


# ── Bin wrappers ──────────────────────────────────────────

BIN_WRAPPERS: dict[str, str] = {}


def _write_bin_wrappers(python: Path, source_root: Path) -> None:
    """Write shell wrappers in ~/.ciel/bin/."""
    bin_dir = CIEL_HOME / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    wrappers = {
        "ciel": f"""#!/usr/bin/env bash
exec "{python}" -m ciel.interfaces.cli "$@"
""",
        "ciel-api": f"""#!/usr/bin/env bash
exec "{python}" -m ciel.api.server "$@"
""",
        "ciel-install": f"""#!/usr/bin/env bash
exec "{python}" "{source_root / 'ciel' / 'install' / 'portable' / 'installer.py'}" "$@"
""",
    }

    for name, script in wrappers.items():
        path = bin_dir / name
        path.write_text(script)
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        _ok(f"wrapper: {name}", str(path))


# ── Main install logic ───────────────────────────────────

def install(mode: str = "standard", ci: bool = False) -> int:
    """Run the full portable installation."""
    _banner()

    # 1. Python check
    python = _check_python()
    if python is None:
        _err(f"Python {'.'.join(str(x) for x in PYTHON_MIN)}+ not found")
        return 1
    _ok(f"Python {sys.version.split()[0]}", str(python))

    # 2. Pip
    if not _ensure_pip(python):
        return 1
    _ok("pip available")

    # 3. Self-locate source root
    source_root = Path(__file__).resolve().parent.parent.parent.parent
    _ok("source root", str(source_root))

    # 4. Create dirs
    _create_dirs()

    # 5. Write config
    _write_config()

    # 6. Write bin wrappers
    _write_bin_wrappers(python, source_root)

    # 7. Install.pth
    _install_pth(source_root)

    # 8. Shell PATH
    _install_path(CIEL_HOME / "bin")

    # 9. Pip deps
    if not _install_deps(python, mode):
        return 1

    # 10. Done
    print()
    print(textwrap.dedent(f"""\
        \033[92m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
        \u2551     \u2713 CIEL v""" + CIEL_VERSION + """ installed !                \u2551
        \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m
        \033[90m  {CIEL_HOME}\033[0m
    """))

    print("  Commands:")
    print(f"    \033[96m{CIEL_HOME}/bin/ciel\033[0m         \u2014 Launch chat")
    print(f"    \033[96m{CIEL_HOME}/bin/ciel-api\033[0m     \u2014 Start API server")
    print("")
    print(f"  Add to your shell rc if not done automatically:")
    print(f"    \033[90mexport PATH=\"$PATH:{CIEL_HOME}/bin\"\033[0m")
    if not ci:
        print()
        print("  \033[90mTip: run `ciel doctor` to verify the installation.\033[0m")

    return 0


# ── CLI entry point ──────────────────────────────────────

def cli() -> int:
    """CLI entry point for the portable installer."""
    import argparse
    parser = argparse.ArgumentParser(
        prog="ciel-install",
        description="CIEL Portable Installer — bootstrap CIEL into ~/.ciel/",
    )
    parser.add_argument(
        "--mode", choices=["standard", "dev", "all"], default="standard",
        help="Installation mode (default: standard)",
    )
    parser.add_argument("--ci", action="store_true", help="CI mode (quiet output)")
    args = parser.parse_args()
    return install(mode=args.mode, ci=args.ci)


if __name__ == "__main__":
    sys.exit(cli())
