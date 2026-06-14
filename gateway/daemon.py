from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_systemd_user_dir() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "systemd" / "user"


def get_launchd_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "com.ciel.gateway.plist"


SERVICE_NAME = "ciel-gateway"
SYSTEMD_SERVICE = f"""[Unit]
Description=CIEL Gateway — Multi-platform messaging daemon
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={sys.executable} -m ciel.gateway.daemon --serve
Restart=always
RestartSec=5
Environment=CIEL_GATEWAY_DAEMON=1
StandardOutput=append:{Path.home() / '.ciel' / 'gateway.log'}
StandardError=append:{Path.home() / '.ciel' / 'gateway.log'}

[Install]
WantedBy=default.target
"""

LAUNCHD_PLIST = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ciel.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>ciel.gateway.daemon</string>
        <string>--serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{Path.home() / '.ciel' / 'gateway.log'}</string>
    <key>StandardErrorPath</key>
    <string>{Path.home() / '.ciel' / 'gateway.log'}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CIEL_GATEWAY_DAEMON</key>
        <string>1</string>
    </dict>
</dict>
</plist>
"""


def is_systemd_available() -> bool:
    try:
        r = subprocess.run(["systemctl", "--user", "list-units"],
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def is_launchd_available() -> bool:
    return sys.platform == "darwin"


def install_systemd() -> bool:
    service_dir = get_systemd_user_dir()
    service_dir.mkdir(parents=True, exist_ok=True)
    service_path = service_dir / f"{SERVICE_NAME}.service"
    service_path.write_text(SYSTEMD_SERVICE)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", SERVICE_NAME], check=False)
    subprocess.run(["systemctl", "--user", "start", SERVICE_NAME], check=False)
    return True


def install_launchd() -> bool:
    plist_path = get_launchd_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(LAUNCHD_PLIST)
    subprocess.run(["launchctl", "load", str(plist_path)], check=False)
    return True


def uninstall_systemd() -> bool:
    subprocess.run(["systemctl", "--user", "stop", SERVICE_NAME], check=False)
    subprocess.run(["systemctl", "--user", "disable", SERVICE_NAME], check=False)
    service_path = get_systemd_user_dir() / f"{SERVICE_NAME}.service"
    if service_path.exists():
        service_path.unlink()
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    return True


def uninstall_launchd() -> bool:
    plist_path = get_launchd_plist_path()
    subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
    if plist_path.exists():
        plist_path.unlink()
    return True


def is_running() -> bool:
    pid = get_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def get_pid() -> int | None:
    pid_file = Path.home() / ".ciel" / "gateway.pid"
    if pid_file.exists():
        try:
            return int(pid_file.read_text().strip())
        except Exception:
            return None
    return None


def write_pid() -> None:
    pid_file = Path.home() / ".ciel" / "gateway.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))


def remove_pid() -> None:
    pid_file = Path.home() / ".ciel" / "gateway.pid"
    if pid_file.exists():
        pid_file.unlink()


def install() -> bool:
    if is_systemd_available():
        logger.info("Installing systemd service...")
        return install_systemd()
    elif is_launchd_available():
        logger.info("Installing launchd service...")
        return install_launchd()
    else:
        logger.warning("No supported service manager found. Starting in foreground mode.")
        return False


def uninstall() -> bool:
    if is_systemd_available():
        return uninstall_systemd()
    elif is_launchd_available():
        return uninstall_launchd()
    return False


def stop() -> bool:
    pid = get_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(10):
                time.sleep(0.5)
                try:
                    os.kill(pid, 0)
                except OSError:
                    remove_pid()
                    return True
            os.kill(pid, signal.SIGKILL)
            remove_pid()
            return True
        except ProcessLookupError:
            remove_pid()
            return True
    return False


async def serve() -> None:
    from ciel.gateway import GatewayServer

    data_dir = Path.home() / ".ciel"
    data_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(data_dir / "gateway.log"),
            logging.StreamHandler(),
        ],
    )

    write_pid()
    logger.info("CIEL Gateway daemon starting...")

    server = GatewayServer()
    server.start()

    def _shutdown(signum: signal.Signals, _frame: Any) -> None:
        logger.info(f"Received signal {signum.name}, shutting down...")
        server.stop()
        remove_pid()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        while server._running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        server.stop()
        remove_pid()


if __name__ == "__main__":
    import sys as _sys
    if "--serve" in _sys.argv:
        asyncio.run(serve())
    else:
        print("Usage: python -m ciel.gateway.daemon --serve")
