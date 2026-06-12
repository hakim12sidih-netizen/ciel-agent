"""
CIEL v∞.8 — Persistence & Auto-Recovery (SQLite).
Sauvegarde d'état, redémarrage automatique, continue là où tu t'es arrêté.
"""
from __future__ import annotations

import os
import sys
import json
import time
import shutil
import signal
import platform
import subprocess
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone


STATE_DIR = Path.home() / ".ciel"
STATE_FILE = STATE_DIR / "state.json"
SERVICE_FILE = STATE_DIR / "ciel.service"
BOOT_SCRIPT = STATE_DIR / "boot.sh"
DB_PATH = STATE_DIR / "ciel.db"

_SCHEMA_VERSION = 2


def _ensure_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


# ── SQLite Engine ──

_migrated = False


@asynccontextmanager
async def _get_db():
    global _migrated
    _ensure_dir()
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if not _migrated:
            await _init_schema(db)
            await _migrate_from_json(db)
            _migrated = True
        yield db


async def _init_schema(db):
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', '2');

        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            extra TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id, timestamp);

        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            metadata TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS credentials (
            service TEXT NOT NULL,
            key_name TEXT NOT NULL,
            key_value TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (service, key_name)
        );

        CREATE TABLE IF NOT EXISTS plugins (
            name TEXT PRIMARY KEY,
            version TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            installed_at TEXT NOT NULL DEFAULT (datetime('now')),
            manifest TEXT DEFAULT '{}'
        );
    """)
    await db.commit()


async def _migrate_from_json(db):
    """Migrate legacy JSON state to SQLite."""
    if not STATE_FILE.exists():
        return
    try:
        data = json.loads(STATE_FILE.read_text())
    except Exception:
        return
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not isinstance(value, str):
            value = str(value)
        await db.execute(
            "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
            (key, value),
        )
    # Migrate chat history
    log_file = STATE_DIR / "chat_history.jsonl"
    if log_file.exists():
        async with db.execute("SELECT COUNT(*) FROM chat_history") as cur:
            count = (await cur.fetchone())[0]
        if count == 0:
            with open(log_file) as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        await db.execute(
                            "INSERT INTO chat_history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                            (msg.get("session_id", ""), msg.get("role", ""), msg.get("content", ""), msg.get("timestamp", datetime.now(timezone.utc).isoformat())),
                        )
                    except Exception:
                        pass
    await db.commit()
    # Archive legacy files
    STATE_FILE.rename(STATE_FILE.with_suffix(".json.bak"))
    if log_file.exists():
        log_file.rename(log_file.with_suffix(".jsonl.bak"))


# ── State persistence ──

async def save_state(**extra) -> dict:
    """Sauvegarde l'état actuel pour restauration future."""
    async with _get_db() as db:
        entries = {
            "version": "1.0.0",
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "pid": str(os.getpid()),
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "active_modules": json.dumps(extra.pop("active_modules", [])),
            "channels_active": json.dumps(extra.pop("channels_active", [])),
            "last_session_id": extra.pop("last_session_id", ""),
            "api_port": str(extra.pop("api_port", 8765)),
            "api_host": extra.pop("api_host", "0.0.0.0"),
        }
        for key, value in entries.items():
            await db.execute(
                "INSERT OR REPLACE INTO state (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                (key, value),
            )
        for key, value in extra.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await db.execute(
                "INSERT OR REPLACE INTO state (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                (key, str(value)),
            )
        await db.commit()
        return entries


async def load_state() -> dict | None:
    """Restaure l'état précédent."""
    async with _get_db() as db:
        async with db.execute("SELECT key, value FROM state") as cur:
            rows = await cur.fetchall()
        if not rows:
            return None
        state = {}
        for row in rows:
            key, value = row["key"], row["value"]
            try:
                state[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                state[key] = value
        return state


async def clear_state():
    """Efface l'état sauvegardé."""
    async with _get_db() as db:
        await db.execute("DELETE FROM state")
        await db.commit()


async def save_chat_message(session_id: str, role: str, content: str, extra: dict | None = None):
    """Sauvegarde un message de chat dans l'historique persistant."""
    async with _get_db() as db:
        await db.execute(
            "INSERT INTO chat_history (session_id, role, content, extra) VALUES (?, ?, ?, ?)",
            (session_id, role, content, json.dumps(extra or {}, ensure_ascii=False)),
        )
        await db.commit()


async def load_chat_history(session_id: str, limit: int = 100) -> list[dict]:
    """Charge l'historique de chat pour une session."""
    async with _get_db() as db:
        async with db.execute(
            "SELECT * FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        result = []
        for row in rows:
            msg = dict(row)
            try:
                msg["extra"] = json.loads(msg.get("extra", "{}"))
            except (json.JSONDecodeError, TypeError):
                msg["extra"] = {}
            result.append(msg)
        return list(reversed(result))


async def create_session(session_id: str, title: str = "") -> dict:
    """Crée une nouvelle session de chat."""
    async with _get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO sessions (session_id, title) VALUES (?, ?)",
            (session_id, title),
        )
        await db.commit()
        return {"session_id": session_id, "title": title}


async def get_session(session_id: str) -> dict | None:
    """Récupère une session."""
    async with _get_db() as db:
        async with db.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ) as cur:
            row = await cur.fetchone()
        if row:
            result = dict(row)
            try:
                result["metadata"] = json.loads(result.get("metadata", "{}"))
            except (json.JSONDecodeError, TypeError):
                result["metadata"] = {}
            return result
        return None


async def list_sessions(limit: int = 50) -> list[dict]:
    """Liste les sessions récentes."""
    async with _get_db() as db:
        async with db.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ── Credentials Management ──

async def save_credential(service: str, key_name: str, key_value: str):
    """Sauvegarde une clé API dans le vault SQLite."""
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO credentials (service, key_name, key_value) VALUES (?, ?, ?)",
            (service, key_name, key_value),
        )
        await db.commit()


async def get_credential(service: str, key_name: str) -> str | None:
    """Récupère une clé API."""
    async with _get_db() as db:
        async with db.execute(
            "SELECT key_value FROM credentials WHERE service = ? AND key_name = ?",
            (service, key_name),
        ) as cur:
            row = await cur.fetchone()
        return row["key_value"] if row else None


async def list_credentials(service: str | None = None) -> list[dict]:
    """Liste les credentials."""
    async with _get_db() as db:
        if service:
            async with db.execute(
                "SELECT * FROM credentials WHERE service = ?", (service,)
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute("SELECT * FROM credentials") as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def delete_credential(service: str, key_name: str):
    """Supprime une clé API."""
    async with _get_db() as db:
        await db.execute(
            "DELETE FROM credentials WHERE service = ? AND key_name = ?",
            (service, key_name),
        )
        await db.commit()


# ── Plugin Registry ──

async def register_plugin(name: str, version: str, manifest: dict | None = None):
    """Enregistre un plugin dans la base."""
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO plugins (name, version, manifest, enabled) VALUES (?, ?, ?, 1)",
            (name, version, json.dumps(manifest or {}, ensure_ascii=False)),
        )
        await db.commit()


async def get_plugin(name: str) -> dict | None:
    """Récupère un plugin."""
    async with _get_db() as db:
        async with db.execute(
            "SELECT * FROM plugins WHERE name = ?", (name,)
        ) as cur:
            row = await cur.fetchone()
        if row:
            result = dict(row)
            try:
                result["manifest"] = json.loads(result.get("manifest", "{}"))
            except (json.JSONDecodeError, TypeError):
                result["manifest"] = {}
            return result
        return None


async def list_plugins(enabled_only: bool = False) -> list[dict]:
    """Liste les plugins."""
    async with _get_db() as db:
        if enabled_only:
            async with db.execute("SELECT * FROM plugins WHERE enabled = 1") as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute("SELECT * FROM plugins") as cur:
                rows = await cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["manifest"] = json.loads(d.get("manifest", "{}"))
            except (json.JSONDecodeError, TypeError):
                d["manifest"] = {}
            result.append(d)
        return result


async def is_plugin_enabled(name: str) -> bool:
    """Vérifie si un plugin est activé."""
    p = await get_plugin(name)
    return bool(p and p.get("enabled"))


# ── Async autostart (wraps sync) ──

def install_autostart(api_port: int = 8765, api_host: str = "0.0.0.0") -> bool:
    """Installe le redémarrage automatique au boot."""
    system = platform.system()
    if system == "Linux":
        return _install_systemd(api_port, api_host)
    elif system == "Darwin":
        return _install_launchd(api_port, api_host)
    elif system == "Windows":
        return _install_windows(api_port, api_host)
    return False


def _find_ciel_api() -> str | None:
    which = shutil.which("ciel-api")
    if which:
        return which
    python = sys.executable
    if Path(__file__).parents[1].joinpath("api/server.py").exists():
        return f"{python} -m ciel.api.server"
    return None


def _install_systemd(api_port: int, api_host: str) -> bool:
    ciel_cmd = _find_ciel_api()
    if not ciel_cmd:
        return False
    service_content = f"""[Unit]
Description=CIEL v∞.8 — Cognitive Engine
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={ciel_cmd} --host {api_host} --port {api_port}
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""
    service_path = Path.home() / ".config" / "systemd" / "user" / "ciel.service"
    service_path.parent.mkdir(parents=True, exist_ok=True)
    service_path.write_text(service_content)
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    subprocess.run(["systemctl", "--user", "enable", "ciel"], capture_output=True)
    subprocess.run(["systemctl", "--user", "start", "ciel"], capture_output=True)
    return True


def _install_launchd(api_port: int, api_host: str) -> bool:
    ciel_cmd = _find_ciel_api()
    if not ciel_cmd:
        return False
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ciel.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>{ciel_cmd.split()[0]}</string>
        <string>--host</string>
        <string>{api_host}</string>
        <string>--port</string>
        <string>{api_port}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{STATE_DIR}/ciel.log</string>
    <key>StandardErrorPath</key>
    <string>{STATE_DIR}/ciel.err</string>
</dict>
</plist>
"""
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.ciel.server.plist"
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist_content)
    subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True)
    return True


def _install_windows(api_port: int, api_host: str) -> bool:
    ciel_cmd = _find_ciel_api()
    if not ciel_cmd:
        return False
    ps_script = f"""$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c {ciel_cmd} --host {api_host} --port {api_port}'
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "$(whoami)" -RunLevel Limited
Register-ScheduledTask -TaskName "CIEL Server" -Action $action -Trigger $trigger -Principal $principal -Force
"""
    ps_path = STATE_DIR / "install_autostart.ps1"
    ps_path.write_text(ps_script)
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_path)], capture_output=True)
    return True


def remove_autostart() -> bool:
    system = platform.system()
    if system == "Linux":
        subprocess.run(["systemctl", "--user", "stop", "ciel"], capture_output=True)
        subprocess.run(["systemctl", "--user", "disable", "ciel"], capture_output=True)
        svc = Path.home() / ".config" / "systemd" / "user" / "ciel.service"
        if svc.exists():
            svc.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        return True
    elif system == "Darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / "com.ciel.server.plist"
        if plist.exists():
            subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
            plist.unlink()
        return True
    elif system == "Windows":
        subprocess.run(["schtasks", "/Delete", "/TN", "CIEL Server", "/F"], capture_output=True)
        return True
    return False


def is_autostart_enabled() -> bool:
    system = platform.system()
    if system == "Linux":
        svc = Path.home() / ".config" / "systemd" / "user" / "ciel.service"
        return svc.exists()
    elif system == "Darwin":
        return Path.home() / "Library" / "LaunchAgents" / "com.ciel.server.plist"
    elif system == "Windows":
        return False
    return False


def create_boot_script(api_port: int = 8765, api_host: str = "0.0.0.0") -> Path:
    ciel_cmd = _find_ciel_api() or "ciel-api"
    script = f"""#!/bin/bash
# CIEL v∞.8 — Auto-start script
# Généré le {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{ciel_cmd} --host {api_host} --port {api_port}
"""
    BOOT_SCRIPT.write_text(script)
    BOOT_SCRIPT.chmod(0o755)
    return BOOT_SCRIPT


# ── Graceful shutdown handler ──

def _save_on_shutdown(*args):
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(clear_state())
        loop.close()
    except Exception:
        pass


def register_shutdown_handler():
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, _save_on_shutdown)
        except (ValueError, OSError):
            pass


# ── API endpoint helpers ──

async def get_status() -> dict:
    state = await load_state() or {}
    async with _get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM chat_history") as cur:
            chat_count = (await cur.fetchone())[0]
    return {
        "autostart": is_autostart_enabled(),
        "state_exists": True,  # DB exists
        "last_saved": state.get("saved_at", None),
        "last_shutdown": state.get("shutdown_at", None),
        "last_session": state.get("last_session_id", ""),
        "chat_history_size": chat_count,
        "database_path": str(DB_PATH),
    }
