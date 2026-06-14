"""
CIEL v∞.8 — Installation Assistant API.
Détection d'environnement, installation & configuration intelligente.
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
import platform
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1/install")


# ── Models ──

class SystemInfo(BaseModel):
    os: str
    os_version: str
    python_version: str
    python_path: str
    pip_available: bool
    node_available: bool
    node_version: str | None
    bun_available: bool
    bun_version: str | None
    go_available: bool
    go_version: str | None
    docker_available: bool
    git_available: bool
    git_version: str | None
    cpu_cores: int
    memory_gb: float
    is_venv: bool
    home_dir: str
    ciel_version: str


class CheckResult(BaseModel):
    name: str
    status: str  # ok | warning | error
    message: str
    detail: str | None = None


class InstallStep(BaseModel):
    id: str
    label: str
    description: str
    command: str
    optional: bool = False


class ConfigSuggestion(BaseModel):
    key: str
    label: str
    description: str
    default: str
    current: str | None = None
    sensitive: bool = False
    category: str = ""
    skipped: bool = False


# ── Helpers ──

def _run(cmd: list[str]) -> tuple[str, str, int]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError:
        return "", "not found", -1
    except subprocess.TimeoutExpired:
        return "", "timeout", -1


def _check_exe(name: str) -> str | None:
    p = shutil.which(name)
    return p


def _detect_ciel_version() -> str:
    try:
        vfile = Path(__file__).parents[4] / "VERSION"
        if vfile.exists():
            return vfile.read_text().strip()
    except Exception:
        pass
    try:
        from ciel import __version__
        return __version__
    except ImportError:
        return "1.0.0"


def _get_memory_gb() -> float:
    try:
        if sys.platform == "linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb / 1024 / 1024, 1)
        elif sys.platform == "darwin":
            o, _, _ = _run(["sysctl", "-n", "hw.memsize"])
            if o:
                return round(int(o) / 1024**3, 1)
    except Exception:
        pass
    return 0.0


# ── Endpoints ──

@router.get("/system", response_model=SystemInfo)
async def detect_system() -> SystemInfo:
    """Détection complète de l'environnement."""
    node_v, _, _ = _run(["node", "--version"])
    bun_v, _, _ = _run(["bun", "--version"])
    go_v, _, _ = _run(["go", "version"])
    git_v, _, _ = _run(["git", "--version"])

    pip_ok = _check_exe("pip") is not None or _check_exe("pip3") is not None
    docker_ok = _check_exe("docker") is not None

    return SystemInfo(
        os=sys.platform,
        os_version=platform.release(),
        python_version=sys.version.split()[0],
        python_path=sys.executable,
        pip_available=pip_ok,
        node_available=node_v != "" and node_v != "not found",
        node_version=node_v if node_v and node_v != "not found" else None,
        bun_available=bun_v != "" and bun_v != "not found",
        bun_version=bun_v if bun_v and bun_v != "not found" else None,
        go_available=go_v != "" and go_v != "not found",
        go_version=go_v.split()[-1].lstrip("go") if go_v and go_v != "not found" else None,
        docker_available=docker_ok,
        git_available=git_v != "" and git_v != "not found",
        git_version=git_v.split()[-1] if git_v and git_v != "not found" else None,
        cpu_cores=os.cpu_count() or 1,
        memory_gb=_get_memory_gb(),
        is_venv=sys.prefix != sys.base_prefix,
        home_dir=str(Path.home()),
        ciel_version=_detect_ciel_version(),
    )


@router.get("/checks", response_model=list[CheckResult])
async def run_checks() -> list[CheckResult]:
    """Exécute tous les checks de pré-installation."""
    results: list[CheckResult] = []
    info = await detect_system()

    # Python version
    py_ver = tuple(int(x) for x in info.python_version.split(".")[:2])
    if py_ver >= (3, 12):
        results.append(CheckResult(name="python", status="ok", message=f"Python {info.python_version}"))
    else:
        results.append(CheckResult(name="python", status="error", message=f"Python {info.python_version} (≥3.12 requis)"))

    # Pip
    if info.pip_available:
        results.append(CheckResult(name="pip", status="ok", message="pip disponible"))
    else:
        results.append(CheckResult(name="pip", status="warning", message="pip non trouvé", detail="Certaines dépendances pourraient ne pas s'installer"))

    # Virtual env
    if info.is_venv:
        results.append(CheckResult(name="venv", status="ok", message="Environnement virtuel actif"))
    else:
        results.append(CheckResult(name="venv", status="warning", message="Hors environnement virtuel", detail="Recommandé : python -m venv .venv && source .venv/bin/activate"))

    # Node/Bun
    if info.bun_available:
        results.append(CheckResult(name="bun", status="ok", message=f"Bun {info.bun_version}"))
    elif info.node_available:
        results.append(CheckResult(name="node", status="ok", message=f"Node {info.node_version}"))
    else:
        results.append(CheckResult(name="runtime_js", status="warning", message="Node.js ou Bun recommandé pour les extensions TypeScript"))

    # Go
    if info.go_available:
        results.append(CheckResult(name="go", status="ok", message=f"Go {info.go_version}"))
    else:
        results.append(CheckResult(name="go", status="warning", message="Go optionnel (hardware monitor, scheduler)", detail="Installation : https://go.dev/dl/"))

    # Docker
    if info.docker_available:
        results.append(CheckResult(name="docker", status="ok", message="Docker disponible"))
    else:
        results.append(CheckResult(name="docker", status="warning", message="Docker optionnel (sandbox, isolation)", detail="Installation : https://docs.docker.com/engine/install/"))

    # Git
    if info.git_available:
        results.append(CheckResult(name="git", status="ok", message=f"Git {info.git_version}"))
    else:
        results.append(CheckResult(name="git", status="warning", message="Git non trouvé"))

    # Memory
    if info.memory_gb >= 4:
        results.append(CheckResult(name="memory", status="ok", message=f"{info.memory_gb} Go RAM"))
    elif info.memory_gb > 0:
        results.append(CheckResult(name="memory", status="warning", message=f"{info.memory_gb} Go RAM (≥4 Go recommandé)"))
    else:
        results.append(CheckResult(name="memory", status="warning", message="Détection mémoire impossible"))

    # CPU
    if info.cpu_cores >= 2:
        results.append(CheckResult(name="cpu", status="ok", message=f"{info.cpu_cores} cœurs"))
    else:
        results.append(CheckResult(name="cpu", status="warning", message=f"{info.cpu_cores} cœur (≥2 recommandé)"))

    # CIEL config dir
    config_dir = Path.home() / ".ciel"
    if config_dir.exists():
        results.append(CheckResult(name="config", status="ok", message=f"Config : {config_dir}"))
    else:
        results.append(CheckResult(name="config", status="info", message="Dossier ~/.ciel sera créé à l'installation"))

    return results


@router.get("/steps", response_model=list[InstallStep])
async def get_install_steps() -> list[InstallStep]:
    """Retourne les étapes d'installation avec leurs commandes."""
    return [
        InstallStep(
            id="venv",
            label="Environnement virtuel",
            description="Créer et activer un environnement virtuel Python",
            command="python3 -m venv .venv && source .venv/bin/activate",
            optional=False,
        ),
        InstallStep(
            id="deps",
            label="Dépendances Python",
            description="Installer les dépendances Python via pip",
            command="pip install -e .",
            optional=False,
        ),
        InstallStep(
            id="deps_all",
            label="Dépendances optionnelles",
            description="Installer toutes les dépendances optionnelles (vision, control, web)",
            command="pip install -e '.[all]'",
            optional=True,
        ),
        InstallStep(
            id="bun_deps",
            label="Dépendances TypeScript",
            description="Installer les dépendances Bun/Node pour les extensions TS",
            command="bun install",
            optional=True,
        ),
        InstallStep(
            id="config",
            label="Configuration",
            description="Générer la configuration par défaut dans ~/.ciel/ciel.json",
            command="",
            optional=False,
        ),
        InstallStep(
            id="identity",
            label="Identité CIEL",
            description="Générer l'identité Ed25519 (clé publique/privée)",
            command="ciel identity --create",
            optional=False,
        ),
        InstallStep(
            id="test",
            label="Vérification",
            description="Lancer les tests de base pour vérifier l'installation",
            command="ciel doctor",
            optional=False,
        ),
        InstallStep(
            id="api_keys",
            label="Clés API LLM",
            description="Configurer les fournisseurs LLM (OpenAI, Anthropic, Google, etc.)",
            command="",
            optional=True,
        ),
        InstallStep(
            id="messaging",
            label="Messagerie (Telegram, Discord, WhatsApp)",
            description="Configurer les plateformes de messagerie",
            command="",
            optional=True,
        ),
        InstallStep(
            id="autostart",
            label="Redémarrage automatique",
            description="Installer le service de redémarrage au boot (systemd/launchd)",
            command="",
            optional=True,
        ),
    ]


class InstallExecuteRequest(BaseModel):
    step_id: str
    params: dict[str, str] = {}


class InstallExecuteResponse(BaseModel):
    success: bool
    output: str
    error: str | None = None


@router.post("/execute", response_model=InstallExecuteResponse)
async def execute_step(req: InstallExecuteRequest) -> InstallExecuteResponse:
    """Exécute une étape d'installation."""
    step_map = {
        "venv": _step_venv,
        "deps": _step_deps,
        "deps_all": _step_deps_all,
        "bun_deps": _step_bun_deps,
        "config": _step_config,
        "identity": _step_identity,
        "test": _step_test,
        "api_keys": _step_api_keys,
        "messaging": _step_messaging,
        "autostart": _step_autostart,
    }
    handler = step_map.get(req.step_id)
    if not handler:
        return InstallExecuteResponse(success=False, output="", error=f"Étape inconnue : {req.step_id}")
    try:
        return await handler(req.params)
    except Exception as e:
        return InstallExecuteResponse(success=False, output="", error=str(e))


async def _step_venv(_: dict) -> InstallExecuteResponse:
    out, err, code = _run(["python3", "-m", "venv", ".venv"])
    return InstallExecuteResponse(
        success=code == 0,
        output=out or "Environnement virtuel créé",
        error=err or None,
    )


async def _step_deps(_: dict) -> InstallExecuteResponse:
    pip = "pip3" if shutil.which("pip3") else "pip"
    out, err, code = _run([pip, "install", "-e", "."])
    return InstallExecuteResponse(
        success=code == 0,
        output=out[-2000:] if len(out) > 2000 else out,
        error=err[-1000:] if err else None,
    )


async def _step_deps_all(_: dict) -> InstallExecuteResponse:
    pip = "pip3" if shutil.which("pip3") else "pip"
    out, err, code = _run([pip, "install", "-e", ".[all]"])
    return InstallExecuteResponse(
        success=code == 0,
        output=out[-2000:] if len(out) > 2000 else out,
        error=err[-1000:] if err else None,
    )


async def _step_bun_deps(_: dict) -> InstallExecuteResponse:
    bun = "bun" if shutil.which("bun") else None
    if not bun:
        return InstallExecuteResponse(success=False, output="", error="Bun non installé")
    out, err, code = _run([bun, "install"])
    return InstallExecuteResponse(
        success=code == 0,
        output=out[-2000:] if len(out) > 2000 else out,
        error=err[-1000:] if err else None,
    )


async def _step_config(params: dict) -> InstallExecuteResponse:
    config_dir = Path.home() / ".ciel"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "ciel.json"

    config = {}
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
        except Exception:
            pass

    config.setdefault("api", {})
    config.setdefault("brain", {})
    config.setdefault("database", {})
    config.setdefault("cache", {})
    config.setdefault("security", {})
    config.setdefault("vision", {})
    config.setdefault("control", {})
    config.setdefault("sandbox", {})
    config.setdefault("websearch", {})
    config.setdefault("clones", {})
    config.setdefault("toolforge", {})
    config.setdefault("economy", {})
    config.setdefault("evolution", {})
    config.setdefault("naming", {})
    config.setdefault("logging", {})
    config.setdefault("channels", {})

    # ── API ──
    config["api"]["host"] = params.get("api_host", config["api"].get("host", "0.0.0.0"))
    config["api"]["port"] = int(params.get("api_port", config["api"].get("port", 8765)))
    config["api"]["log_level"] = params.get("api_log_level", config["api"].get("log_level", "INFO"))
    config["api"]["cors_origins"] = params.get("api_cors_origins", config["api"].get("cors_origins", "*"))
    config["api"]["workers"] = int(params.get("api_workers", config["api"].get("workers", 1)))
    config["api"]["rate_limit"] = int(params.get("api_rate_limit", config["api"].get("rate_limit", 0)))
    config["api"]["ssl_cert"] = params.get("api_ssl_cert", config["api"].get("ssl_cert", ""))
    config["api"]["ssl_key"] = params.get("api_ssl_key", config["api"].get("ssl_key", ""))
    config["api"]["expose_docs"] = params.get("api_expose_docs", config["api"].get("expose_docs", True))
    if isinstance(config["api"]["expose_docs"], str):
        config["api"]["expose_docs"] = config["api"]["expose_docs"].lower() in ("true", "1", "yes")

    # ── Brain ──
    config["brain"]["modules_autoload"] = params.get("brain_modules_autoload", config["brain"].get("modules_autoload", True))
    if isinstance(config["brain"]["modules_autoload"], str):
        config["brain"]["modules_autoload"] = config["brain"]["modules_autoload"].lower() in ("true", "1", "yes")
    config["brain"]["default_provider"] = params.get("brain_default_provider", config["brain"].get("default_provider", "openai"))
    config["brain"]["default_model"] = params.get("brain_default_model", config["brain"].get("default_model", "gpt-4o"))
    config["brain"]["max_tokens"] = int(params.get("brain_max_tokens", config["brain"].get("max_tokens", 4096)))
    config["brain"]["temperature"] = float(params.get("brain_temperature", config["brain"].get("temperature", 0.7)))
    config["brain"]["top_p"] = float(params.get("brain_top_p", config["brain"].get("top_p", 0.9)))
    config["brain"]["frequency_penalty"] = float(params.get("brain_frequency_penalty", config["brain"].get("frequency_penalty", 0.0)))
    config["brain"]["presence_penalty"] = float(params.get("brain_presence_penalty", config["brain"].get("presence_penalty", 0.0)))
    config["brain"]["context_window"] = int(params.get("brain_context_window", config["brain"].get("context_window", 0)))
    config["brain"]["timeout"] = int(params.get("brain_timeout", config["brain"].get("timeout", 60)))
    config["brain"]["max_retries"] = int(params.get("brain_max_retries", config["brain"].get("max_retries", 3)))
    config["brain"]["stream"] = params.get("brain_stream", config["brain"].get("stream", True))
    if isinstance(config["brain"]["stream"], str):
        config["brain"]["stream"] = config["brain"]["stream"].lower() in ("true", "1", "yes")

    # ── Database ──
    config["database"]["path"] = params.get("database_path", config["database"].get("path", str(config_dir / "ciel.db")))
    config["database"]["pool_size"] = int(params.get("database_pool_size", config["database"].get("pool_size", 5)))
    config["database"]["timeout"] = int(params.get("database_timeout", config["database"].get("timeout", 30)))
    config["database"]["wal_mode"] = params.get("database_wal_mode", config["database"].get("wal_mode", True))
    if isinstance(config["database"]["wal_mode"], str):
        config["database"]["wal_mode"] = config["database"]["wal_mode"].lower() in ("true", "1", "yes")

    # ── Cache ──
    config["cache"]["backend"] = params.get("cache_backend", config["cache"].get("backend", "memory"))
    config["cache"]["ttl"] = int(params.get("cache_ttl", config["cache"].get("ttl", 300)))
    config["cache"]["max_size"] = int(params.get("cache_max_size", config["cache"].get("max_size", 1000)))

    # ── Security ──
    config["security"]["encryption_key"] = params.get("security_encryption_key", config["security"].get("encryption_key", ""))
    config["security"]["sandbox_enabled"] = params.get("security_sandbox_enabled", config["security"].get("sandbox_enabled", True))
    if isinstance(config["security"]["sandbox_enabled"], str):
        config["security"]["sandbox_enabled"] = config["security"]["sandbox_enabled"].lower() in ("true", "1", "yes")
    config["security"]["api_keys"] = params.get("security_api_keys", config["security"].get("api_keys", "")).split(",") if params.get("security_api_keys") else config["security"].get("api_keys", [])
    config["security"]["jwt_secret"] = params.get("security_jwt_secret", config["security"].get("jwt_secret", ""))
    config["security"]["jwt_expiry"] = int(params.get("security_jwt_expiry", config["security"].get("jwt_expiry", 3600)))

    # ── Vision ──
    config["vision"]["enabled"] = params.get("vision_enabled", config["vision"].get("enabled", False))
    if isinstance(config["vision"]["enabled"], str):
        config["vision"]["enabled"] = config["vision"]["enabled"].lower() in ("true", "1", "yes")
    config["vision"]["screen_capture_fps"] = int(params.get("vision_screen_capture_fps", config["vision"].get("screen_capture_fps", 1)))
    config["vision"]["webcam_enabled"] = params.get("vision_webcam_enabled", config["vision"].get("webcam_enabled", False))
    if isinstance(config["vision"]["webcam_enabled"], str):
        config["vision"]["webcam_enabled"] = config["vision"]["webcam_enabled"].lower() in ("true", "1", "yes")

    # ── Control ──
    config["control"]["enabled"] = params.get("control_enabled", config["control"].get("enabled", False))
    if isinstance(config["control"]["enabled"], str):
        config["control"]["enabled"] = config["control"]["enabled"].lower() in ("true", "1", "yes")
    config["control"]["keyboard_shortcuts"] = params.get("control_keyboard_shortcuts", config["control"].get("keyboard_shortcuts", True))
    if isinstance(config["control"]["keyboard_shortcuts"], str):
        config["control"]["keyboard_shortcuts"] = config["control"]["keyboard_shortcuts"].lower() in ("true", "1", "yes")

    # ── Sandbox ──
    config["sandbox"]["enabled"] = params.get("sandbox_enabled", config["sandbox"].get("enabled", True))
    if isinstance(config["sandbox"]["enabled"], str):
        config["sandbox"]["enabled"] = config["sandbox"]["enabled"].lower() in ("true", "1", "yes")
    config["sandbox"]["docker_image"] = params.get("sandbox_docker_image", config["sandbox"].get("docker_image", "python:3.12-slim"))
    config["sandbox"]["timeout"] = int(params.get("sandbox_timeout", config["sandbox"].get("timeout", 30)))
    config["sandbox"]["memory_limit"] = params.get("sandbox_memory_limit", config["sandbox"].get("memory_limit", "256m"))

    # ── Websearch ──
    config["websearch"]["enabled"] = params.get("websearch_enabled", config["websearch"].get("enabled", True))
    if isinstance(config["websearch"]["enabled"], str):
        config["websearch"]["enabled"] = config["websearch"]["enabled"].lower() in ("true", "1", "yes")
    config["websearch"]["cache_ttl"] = int(params.get("websearch_cache_ttl", config["websearch"].get("cache_ttl", 3600)))

    # ── Clones ──
    config["clones"]["max_clones"] = int(params.get("clones_max_clones", config["clones"].get("max_clones", 10)))
    config["clones"]["default_strategy"] = params.get("clones_default_strategy", config["clones"].get("default_strategy", "scout"))

    # ── Evolution ──
    config["evolution"]["enabled"] = params.get("evolution_enabled", config["evolution"].get("enabled", True))
    if isinstance(config["evolution"]["enabled"], str):
        config["evolution"]["enabled"] = config["evolution"]["enabled"].lower() in ("true", "1", "yes")
    config["evolution"]["population_size"] = int(params.get("evolution_population_size", config["evolution"].get("population_size", 50)))
    config["evolution"]["generations"] = int(params.get("evolution_generations", config["evolution"].get("generations", 100)))
    config["evolution"]["mutation_rate"] = float(params.get("evolution_mutation_rate", config["evolution"].get("mutation_rate", 0.1)))

    # ── Economy ──
    config["economy"]["enabled"] = params.get("economy_enabled", config["economy"].get("enabled", True))
    if isinstance(config["economy"]["enabled"], str):
        config["economy"]["enabled"] = config["economy"]["enabled"].lower() in ("true", "1", "yes")
    config["economy"]["initial_balance"] = int(params.get("economy_initial_balance", config["economy"].get("initial_balance", 100)))

    # ── Logging ──
    config["logging"]["level"] = params.get("logging_level", config["logging"].get("level", "INFO"))
    config["logging"]["format"] = params.get("logging_format", config["logging"].get("format", "detailed"))
    config["logging"]["file"] = params.get("logging_file", config["logging"].get("file", ""))
    config["logging"]["max_bytes"] = int(params.get("logging_max_bytes", config["logging"].get("max_bytes", 10485760)))

    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    return InstallExecuteResponse(
        success=True,
        output=f"Configuration sauvegardée : {config_file}",
    )


async def _step_identity(_: dict) -> InstallExecuteResponse:
    ciel_bin = shutil.which("ciel")
    if not ciel_bin:
        return InstallExecuteResponse(success=False, output="", error="Commande 'ciel' non trouvée. Installer d'abord les dépendances.")
    out, err, code = _run([ciel_bin, "identity", "--create"])
    return InstallExecuteResponse(
        success=code == 0,
        output=out or "Identité CIEL créée",
        error=err or None,
    )


async def _step_test(_: dict) -> InstallExecuteResponse:
    ciel_bin = shutil.which("ciel")
    if not ciel_bin:
        return InstallExecuteResponse(success=False, output="", error="Commande 'ciel' non trouvée.")
    out, err, code = _run([ciel_bin, "doctor"])
    return InstallExecuteResponse(
        success=code == 0,
        output=out[-2000:] if len(out) > 2000 else out,
        error=err[-1000:] if err else None,
    )


async def _step_api_keys(params: dict) -> InstallExecuteResponse:
    config_dir = Path.home() / ".ciel"
    config_file = config_dir / "ciel.json"
    config_dir.mkdir(parents=True, exist_ok=True)

    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text())

    providers_config = config.setdefault("providers", {})
    configured = []
    for key, value in params.items():
        if not value:
            continue
        if key.startswith("provider_"):
            provider_name = key.replace("provider_", "")
            # Ollama uses base_url instead of api_key
            if provider_name == "ollama":
                providers_config[provider_name] = {"base_url": value}
            else:
                providers_config[provider_name] = {"api_key": value}
            configured.append(provider_name)

    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    return InstallExecuteResponse(
        success=True,
        output=f"Fournisseurs configurés : {', '.join(configured) if configured else 'aucun'}",
    )


async def _step_messaging(params: dict) -> InstallExecuteResponse:
    """Configure les plateformes de messagerie."""
    config_dir = Path.home() / ".ciel"
    config_file = config_dir / "ciel.json"
    config_dir.mkdir(parents=True, exist_ok=True)

    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text())

    providers_config = config.setdefault("providers", {})
    configured = []

    platform_fields = {
        "telegram": ["api_key"],
        "discord": ["api_key"],
        "whatsapp": ["api_key", "phone_number"],
        "signal": ["server_url", "api_key"],
        "matrix": ["server_url", "api_key"],
        "slack": ["api_key"],
    }

    for key, value in params.items():
        if not value or value == "__SKIPPED__":
            continue
        for platform, fields in platform_fields.items():
            for field in fields:
                if key == f"{platform}_{field}":
                    providers_config.setdefault(platform, {})[field] = value
                    if platform not in configured:
                        configured.append(platform)

    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    if not configured:
        return InstallExecuteResponse(success=True, output="Aucune plateforme configurée (ignoré)")

    return InstallExecuteResponse(
        success=True,
        output=f"Plateformes configurées : {', '.join(configured)}",
    )


async def _step_autostart(params: dict) -> InstallExecuteResponse:
    """Installe le redémarrage automatique au boot."""
    try:
        from ciel.persistence import install_autostart
        port = int(params.get("port", 8765))
        host = params.get("host", "0.0.0.0")
        ok = install_autostart(port, host)
        if ok:
            return InstallExecuteResponse(success=True, output="Redémarrage auto installé (systemd/launchd)")
        return InstallExecuteResponse(success=False, output="", error="Auto-start non supporté sur ce système")
    except Exception as e:
        return InstallExecuteResponse(success=False, output="", error=str(e))


@router.get("/config-suggestions", response_model=list[ConfigSuggestion])
async def get_config_suggestions() -> list[ConfigSuggestion]:
    """Suggestions de configuration complètes pour l'installateur."""
    config_dir = Path.home() / ".ciel"
    config_file = config_dir / "ciel.json"
    current = {}
    if config_file.exists():
        try:
            current = json.loads(config_file.read_text())
        except Exception:
            pass

    def _g(keys: list[str], default: str = "") -> str | None:
        """Get nested value from current config."""
        obj = current
        for k in keys:
            if isinstance(obj, dict):
                obj = obj.get(k, {})
            else:
                return str(obj) if obj else None
        if obj is None or obj == {}:
            return None
        if isinstance(obj, bool):
            return str(obj).lower()
        return str(obj)

    P = "providers"

    suggestions = [
        # ── Serveur API ──
        ConfigSuggestion(key="api_host", label="Hôte serveur", description="Adresse d'écoute du serveur HTTP", default="0.0.0.0", category="server", current=_g(["api", "host"])),
        ConfigSuggestion(key="api_port", label="Port serveur", description="Port d'écoute du serveur HTTP", default="8765", category="server", current=_g(["api", "port"])),
        ConfigSuggestion(key="api_log_level", label="Niveau de log API", description="Niveau de log (DEBUG, INFO, WARNING, ERROR)", default="INFO", current=_g(["api", "log_level"])),
        ConfigSuggestion(key="api_workers", label="Workers", description="Nombre de workers uvicorn", default="1", category="server", current=_g(["api", "workers"])),
        ConfigSuggestion(key="api_cors_origins", label="Origines CORS", description="Origines autorisées (* pour toutes)", default="*", current=_g(["api", "cors_origins"])),
        ConfigSuggestion(key="api_rate_limit", label="Rate limit", description="Requêtes/min (0 = désactivé)", default="0", current=_g(["api", "rate_limit"])),
        ConfigSuggestion(key="api_ssl_cert", label="Certificat SSL", description="Chemin vers le certificat SSL (optionnel)", default="", current=_g(["api", "ssl_cert"])),
        ConfigSuggestion(key="api_ssl_key", label="Clé SSL", description="Chemin vers la clé privée SSL", default="", category="server", current=_g(["api", "ssl_key"])),
        ConfigSuggestion(key="api_expose_docs", label="Docs API", description="Exposer /v1/docs (Swagger)", default="true", current=_g(["api", "expose_docs"])),

        # ── Cerveau (Brain) ──
        ConfigSuggestion(key="brain_default_provider", label="Fournisseur LLM", description="Fournisseur par défaut", default="openai", category="brain", current=_g(["brain", "default_provider"])),
        ConfigSuggestion(key="brain_default_model", label="Modèle LLM", description="Modèle par défaut", default="gpt-4o", category="brain", current=_g(["brain", "default_model"])),
        ConfigSuggestion(key="brain_modules_autoload", label="Auto-chargement modules", description="Charger tous les modules au démarrage", default="true", category="brain", current=_g(["brain", "modules_autoload"])),
        ConfigSuggestion(key="brain_max_tokens", label="Max tokens", description="Nombre max de tokens par réponse", default="4096", category="brain", current=_g(["brain", "max_tokens"])),
        ConfigSuggestion(key="brain_temperature", label="Température", description="Créativité du modèle (0.0-2.0)", default="0.7", current=_g(["brain", "temperature"])),
        ConfigSuggestion(key="brain_top_p", label="Top P", description="Nucleus sampling (0.0-1.0)", default="0.9", current=_g(["brain", "top_p"])),
        ConfigSuggestion(key="brain_frequency_penalty", label="Pénalité fréquence", description="Éviter la répétition (-2.0-2.0)", default="0.0", current=_g(["brain", "frequency_penalty"])),
        ConfigSuggestion(key="brain_presence_penalty", label="Pénalité présence", description="Encourager les nouveaux sujets (-2.0-2.0)", default="0.0", current=_g(["brain", "presence_penalty"])),
        ConfigSuggestion(key="brain_context_window", label="Fenêtre contexte", description="Taille du contexte mémoire (0 = auto)", default="0", current=_g(["brain", "context_window"])),
        ConfigSuggestion(key="brain_timeout", label="Timeout", description="Timeout en secondes pour les requêtes LLM", default="60", category="brain", current=_g(["brain", "timeout"])),
        ConfigSuggestion(key="brain_max_retries", label="Max retries", description="Nombre de tentatives en cas d'échec", default="3", category="brain", current=_g(["brain", "max_retries"])),
        ConfigSuggestion(key="brain_stream", label="Streaming", description="Activer le streaming des réponses", default="true", category="brain", current=_g(["brain", "stream"])),

        # ── Base de données ──
        ConfigSuggestion(key="database_path", label="Chemin BDD", description="Chemin du fichier SQLite", default=str(config_dir / "ciel.db"), category="database", current=_g(["database", "path"])),
        ConfigSuggestion(key="database_pool_size", label="Taille pool", description="Nombre de connexions simultanées", default="5", category="database", current=_g(["database", "pool_size"])),
        ConfigSuggestion(key="database_timeout", label="Timeout BDD", description="Timeout en secondes", default="30", category="database", current=_g(["database", "timeout"])),
        ConfigSuggestion(key="database_wal_mode", label="Mode WAL", description="Write-Ahead Logging (performances)", default="true", category="database", current=_g(["database", "wal_mode"])),

        # ── Cache ──
        ConfigSuggestion(key="cache_backend", label="Backend cache", description="Type de cache (memory, sqlite, redis)", default="memory", category="cache", current=_g(["cache", "backend"])),
        ConfigSuggestion(key="cache_ttl", label="TTL cache", description="Durée de vie en secondes", default="300", category="cache", current=_g(["cache", "ttl"])),
        ConfigSuggestion(key="cache_max_size", label="Taille max cache", description="Nombre max d'entrées", default="1000", category="cache", current=_g(["cache", "max_size"])),

        # ── Sécurité ──
        ConfigSuggestion(key="security_sandbox_enabled", label="Sandbox", description="Isolation des exécutions de code", default="true", category="security", current=_g(["security", "sandbox_enabled"])),
        ConfigSuggestion(key="security_api_keys", label="Clés API serveur", description="Clés autorisées (séparées par des virgules)", default="", category="security", current=_g(["security", "api_keys"])),
        ConfigSuggestion(key="security_jwt_secret", label="Secret JWT", description="Clé secrète pour les tokens JWT", default="", category="security", current=_g(["security", "jwt_secret"]), sensitive=True),
        ConfigSuggestion(key="security_jwt_expiry", label="Expiration JWT", description="Durée de validité en secondes", default="3600", category="security", current=_g(["security", "jwt_expiry"])),

        # ── Vision ──
        ConfigSuggestion(key="vision_enabled", label="Vision", description="Activer la capture d'écran/webcam", default="false", category="vision", current=_g(["vision", "enabled"])),
        ConfigSuggestion(key="vision_screen_capture_fps", label="FPS capture", description="Images par seconde (screen)", default="1", category="vision", current=_g(["vision", "screen_capture_fps"])),
        ConfigSuggestion(key="vision_webcam_enabled", label="Webcam", description="Activer la webcam", default="false", category="vision", current=_g(["vision", "webcam_enabled"])),

        # ── Contrôle ──
        ConfigSuggestion(key="control_enabled", label="Contrôle système", description="Activer le contrôle clavier/souris", default="false", category="control", current=_g(["control", "enabled"])),
        ConfigSuggestion(key="control_keyboard_shortcuts", label="Raccourcis clavier", description="Activer les raccourcis clavier système", default="true", category="control", current=_g(["control", "keyboard_shortcuts"])),

        # ── Sandbox (exécution code) ──
        ConfigSuggestion(key="sandbox_enabled", label="Sandbox code", description="Exécution sécurisée de code", default="true", category="sandbox", current=_g(["sandbox", "enabled"])),
        ConfigSuggestion(key="sandbox_docker_image", label="Image Docker", description="Image pour le sandbox", default="python:3.12-slim", category="sandbox", current=_g(["sandbox", "docker_image"])),
        ConfigSuggestion(key="sandbox_timeout", label="Timeout sandbox", description="Timeout max d'exécution (s)", default="30", category="sandbox", current=_g(["sandbox", "timeout"])),
        ConfigSuggestion(key="sandbox_memory_limit", label="Limite mémoire", description="Limite mémoire par conteneur", default="256m", category="sandbox", current=_g(["sandbox", "memory_limit"])),

        # ── Web Search ──
        ConfigSuggestion(key="websearch_enabled", label="Recherche web", description="Activer la recherche DuckDuckGo", default="true", category="websearch", current=_g(["websearch", "enabled"])),
        ConfigSuggestion(key="websearch_cache_ttl", label="Cache recherche", description="TTL du cache de recherche (s)", default="3600", category="websearch", current=_g(["websearch", "cache_ttl"])),

        # ── Clones ──
        ConfigSuggestion(key="clones_max_clones", label="Max clones", description="Nombre maximum de clones simultanés", default="10", category="clones", current=_g(["clones", "max_clones"])),
        ConfigSuggestion(key="clones_default_strategy", label="Stratégie clones", description="Stratégie par défaut (scout, worker, phantom, aspect)", default="scout", category="clones", current=_g(["clones", "default_strategy"])),

        # ── Évolution ──
        ConfigSuggestion(key="evolution_enabled", label="Évolution", description="Activer le moteur d'évolution génétique", default="true", category="evolution", current=_g(["evolution", "enabled"])),
        ConfigSuggestion(key="evolution_population_size", label="Taille population", description="Taille de la population évolutive", default="50", category="evolution", current=_g(["evolution", "population_size"])),
        ConfigSuggestion(key="evolution_generations", label="Générations", description="Nombre de générations max", default="100", category="evolution", current=_g(["evolution", "generations"])),
        ConfigSuggestion(key="evolution_mutation_rate", label="Taux mutation", description="Taux de mutation génétique", default="0.1", category="evolution", current=_g(["evolution", "mutation_rate"])),

        # ── Économie ──
        ConfigSuggestion(key="economy_enabled", label="Économie", description="Activer le système économique", default="true", category="economy", current=_g(["economy", "enabled"])),
        ConfigSuggestion(key="economy_initial_balance", label="Solde initial", description="Crédits de départ pour chaque agent", default="100", category="economy", current=_g(["economy", "initial_balance"])),

        # ── Logging ──
        ConfigSuggestion(key="logging_level", label="Niveau log global", description="Niveau de log (DEBUG, INFO, WARNING, ERROR)", default="INFO", category="logging", current=_g(["logging", "level"])),
        ConfigSuggestion(key="logging_format", label="Format logs", description="Format (simple, detailed, json)", default="detailed", category="logging", current=_g(["logging", "format"])),
        ConfigSuggestion(key="logging_file", label="Fichier log", description="Chemin du fichier de log (vide = stdout)", default="", category="logging", current=_g(["logging", "file"])),
        ConfigSuggestion(key="logging_max_bytes", label="Taille max log", description="Taille max avant rotation (bytes)", default="10485760", category="logging", current=_g(["logging", "max_bytes"])),

        # ── Clés API LLM ──
        ConfigSuggestion(key="provider_openai", label="🔑 OpenAI", description="Clé API OpenAI (sk-...)", default="", category="api_keys", current="••••" if current.get(P, {}).get("openai", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_anthropic", label="🔑 Anthropic", description="Clé API Anthropic (sk-ant-...)", default="", category="api_keys", current="••••" if current.get(P, {}).get("anthropic", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_google", label="🔑 Google Gemini", description="Clé API Google", default="", category="api_keys", current="••••" if current.get(P, {}).get("google", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_deepseek", label="🔑 DeepSeek", description="Clé API DeepSeek", default="", category="api_keys", current="••••" if current.get(P, {}).get("deepseek", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_groq", label="🔑 Groq", description="Clé API Groq", default="", category="api_keys", current="••••" if current.get(P, {}).get("groq", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_mistral", label="🔑 Mistral", description="Clé API Mistral AI", default="", category="api_keys", current="••••" if current.get(P, {}).get("mistral", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_cohere", label="🔑 Cohere", description="Clé API Cohere", default="", category="api_keys", current="••••" if current.get(P, {}).get("cohere", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_together", label="🔑 Together AI", description="Clé API Together", default="", category="api_keys", current="••••" if current.get(P, {}).get("together", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_ollama", label="🔑 Ollama", description="URL du serveur Ollama (ex: http://localhost:11434)", default="http://localhost:11434", category="api_keys", current=_g([P, "ollama", "base_url"]), sensitive=True),
        ConfigSuggestion(key="provider_openrouter", label="🔑 OpenRouter", description="Clé API OpenRouter", default="", category="api_keys", current="••••" if current.get(P, {}).get("openrouter", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_perplexity", label="🔑 Perplexity", description="Clé API Perplexity", default="", category="api_keys", current="••••" if current.get(P, {}).get("perplexity", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="provider_replicate", label="🔑 Replicate", description="Clé API Replicate", default="", category="api_keys", current="••••" if current.get(P, {}).get("replicate", {}).get("api_key") else None, sensitive=True),

        # ── Messagerie (Telegram, Discord, WhatsApp, etc.) ──
        ConfigSuggestion(key="telegram_api_key", label="✈️ Telegram Bot Token", description="Token du bot Telegram (123456:ABC-DEF...)", default="", category="messaging", current="••••" if current.get(P, {}).get("telegram", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="discord_api_key", label="🎮 Discord Bot Token", description="Token du bot Discord", default="", category="messaging", current="••••" if current.get(P, {}).get("discord", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="whatsapp_api_key", label="💬 WhatsApp API Key", description="Clé API WhatsApp Business", default="", category="messaging", current="••••" if current.get(P, {}).get("whatsapp", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="whatsapp_phone_number", label="💬 WhatsApp Phone ID", description="Numéro de téléphone WhatsApp", default="", category="messaging", current=_g([P, "whatsapp", "phone_number"])),
        ConfigSuggestion(key="signal_server_url", label="🔒 Signal Server URL", description="URL du serveur Signal (http://localhost:8080)", default="", category="messaging", current=_g([P, "signal", "server_url"])),
        ConfigSuggestion(key="signal_api_key", label="🔒 Signal API Key", description="Clé API Signal", default="", category="messaging", current="••••" if current.get(P, {}).get("signal", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="matrix_server_url", label="◈ Matrix Server", description="URL du serveur Matrix (https://matrix.org)", default="", category="messaging", current=_g([P, "matrix", "server_url"])),
        ConfigSuggestion(key="matrix_api_key", label="◈ Matrix Token", description="Token d'accès Matrix", default="", category="messaging", current="••••" if current.get(P, {}).get("matrix", {}).get("api_key") else None, sensitive=True),
        ConfigSuggestion(key="slack_api_key", label="# Slack Bot Token", description="Token Slack (xoxb-...)", default="", category="messaging", current="••••" if current.get(P, {}).get("slack", {}).get("api_key") else None, sensitive=True),
    ]
    return suggestions
