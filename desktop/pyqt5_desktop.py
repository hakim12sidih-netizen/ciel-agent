#!/usr/bin/env python3
"""CIEL Desktop — Contrôle du serveur CIEL depuis le bureau.

Usage:
  python ciel_desktop.py          # Lance l'app tray
  python ciel_desktop.py --debug  # Mode debug avec logs
"""

import os
import sys
import json
import time
import signal
import logging
import subprocess
import threading
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

from PyQt5.QtCore import (
    Qt, QTimer, QObject, pyqtSignal, QThread,
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox,
)

logger = logging.getLogger("ciel-desktop")

CIEL_PORT = int(os.environ.get("CIEL_PORT", "8765"))
CIEL_URL = f"http://127.0.0.1:{CIEL_PORT}"
ICON_SIZE = 32

# ── Statuts ──
STATE_STOPPED = 0
STATE_STARTING = 1
STATE_RUNNING = 2
STATE_ERROR = 3

# ── Icône générée par code ──

def make_icon(status, size=ICON_SIZE):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    if status == STATE_RUNNING:
        color = QColor(34, 197, 94)  # vert
    elif status == STATE_STARTING:
        color = QColor(251, 191, 36)  # jaune
    elif status == STATE_ERROR:
        color = QColor(239, 68, 68)   # rouge
    else:
        color = QColor(113, 113, 122)  # gris

    # Cercle
    p.setBrush(color)
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, size - 4, size - 4)

    # Lettre C
    p.setPen(QColor(255, 255, 255))
    font = QFont("sans-serif", size // 2, QFont.Bold)
    p.setFont(font)
    p.drawText(p.boundingRect(0, 0, size, size, Qt.AlignCenter, "C"), Qt.AlignCenter, "C")
    p.end()
    return QIcon(pix)

# ── Thread de vérification du serveur ──

class ServerPoller(QObject):
    status_changed = pyqtSignal(int, str)

    def __init__(self, interval=15):
        super().__init__()
        self.interval = interval
        self._running = True

    def stop(self):
        self._running = False

    def poll(self):
        while self._running:
            try:
                req = Request(f"{CIEL_URL}/v1/health", method="GET", headers={"Accept": "application/json"})
                resp = urlopen(req, timeout=5)
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    uptime = data.get("uptime", 0)
                    modules = data.get("modules_active", data.get("modules", 0))
                    self.status_changed.emit(STATE_RUNNING, f"En ligne • {modules} modules • {uptime:.0f}s")
                else:
                    self.status_changed.emit(STATE_ERROR, f"Erreur HTTP {resp.status}")
            except URLError:
                self.status_changed.emit(STATE_STOPPED, "Hors ligne")
            except Exception as e:
                self.status_changed.emit(STATE_ERROR, str(e)[:60])

            for _ in range(self.interval * 10):
                if not self._running:
                    return
                time.sleep(0.1)

# ── Application principale ──

class CielDesktopApp(QObject):
    def __init__(self):
        super().__init__()
        self.state = STATE_STOPPED
        self.status_text = "Hors ligne"
        self.server_process = None

        # Icônes par état
        self.icons = {
            STATE_STOPPED: make_icon(STATE_STOPPED),
            STATE_STARTING: make_icon(STATE_STARTING),
            STATE_RUNNING: make_icon(STATE_RUNNING),
            STATE_ERROR: make_icon(STATE_ERROR),
        }

        # Tray
        self.tray = QSystemTrayIcon(self.icons[STATE_STOPPED], self)
        self.tray.setToolTip("CIEL Desktop — Hors ligne")
        self._build_menu()
        self.tray.show()

        # Poller
        self.poller_thread = QThread()
        self.poller = ServerPoller(interval=15)
        self.poller.moveToThread(self.poller_thread)
        self.poller.status_changed.connect(self._on_status)
        self.poller_thread.started.connect(self.poller.poll)
        self.poller_thread.finished.connect(self.poller.deleteLater)
        self.poller_thread.start()

        # Timer pour le statut de démarrage
        self.startup_timer = QTimer(self)
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self._startup_timeout)

        # Vérification rapide initiale
        QTimer.singleShot(500, self._initial_check)

    def _build_menu(self):
        menu = QMenu()

        self.open_action = QAction("🌐 Ouvrir CIEL", menu)
        self.open_action.triggered.connect(self._open_browser)
        menu.addAction(self.open_action)

        menu.addSeparator()

        self.status_action = QAction(f"● {self.status_text}", menu)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)

        menu.addSeparator()

        self.start_action = QAction("▶ Démarrer le serveur", menu)
        self.start_action.triggered.connect(self._start_server)
        menu.addAction(self.start_action)

        self.stop_action = QAction("⏹ Arrêter le serveur", menu)
        self.stop_action.triggered.connect(self._stop_server)
        self.stop_action.setEnabled(False)
        menu.addAction(self.stop_action)

        menu.addSeparator()

        quit_action = QAction("✕ Quitter", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.menu = menu

    def _update_menu(self):
        self.status_action.setText(f"● {self.status_text}")
        running = self.state == STATE_RUNNING
        self.start_action.setEnabled(not running and self.state != STATE_STARTING)
        self.stop_action.setEnabled(running)
        self.open_action.setEnabled(running)

        icon = self.icons.get(self.state, self.icons[STATE_STOPPED])
        self.tray.setIcon(icon)

        tip = f"CIEL Desktop — {self.status_text}"
        self.tray.setToolTip(tip)

    def _on_status(self, state, text):
        if self.state != state or self.status_text != text:
            old_state = self.state
            self.state = state
            self.status_text = text
            self._update_menu()

            # Notification aux changements d'état
            if old_state != state:
                if state == STATE_RUNNING:
                    self._notify("CIEL", "✓ Serveur en ligne")
                elif state == STATE_STOPPED and old_state == STATE_RUNNING:
                    self._notify("CIEL", "✗ Serveur déconnecté")

    def _notify(self, title, message):
        try:
            self.tray.showMessage(title, message, QSystemTrayIcon.Information, 3000)
        except Exception:
            pass

    def _initial_check(self):
        try:
            req = Request(f"{CIEL_URL}/v1/health", method="GET", headers={"Accept": "application/json"})
            resp = urlopen(req, timeout=3)
            if resp.status == 200:
                self._on_status(STATE_RUNNING, "En ligne")
                return
        except Exception:
            pass
        self._on_status(STATE_STOPPED, "Hors ligne")

    def _open_browser(self):
        import webbrowser
        webbrowser.open(CIEL_URL)

    def _start_server(self):
        self._on_status(STATE_STARTING, "Démarrage…")

        # Try systemd user service first
        try:
            subprocess.run(
                ["systemctl", "--user", "start", "ciel.service"],
                capture_output=True, timeout=5, check=False,
            )
        except FileNotFoundError:
            pass

        # Fallback: ciell --daemon
        try:
            self.server_process = subprocess.Popen(
                ["ciell", "--daemon"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Server process started (PID %d)", self.server_process.pid)
        except FileNotFoundError:
            self._on_status(STATE_ERROR, "ciell introuvable")
            self._notify("CIEL", "Commande 'ciell' introuvable")
            return

        # Poll intensif pendant 10s
        self.startup_timer.start(10000)

    def _startup_timeout(self):
        if self.state == STATE_STARTING:
            self._on_status(STATE_STOPPED, "Échec du démarrage")
            self._notify("CIEL", "Le serveur n'a pas démarré dans les temps")
            if self.server_process:
                try:
                    self.server_process.terminate()
                except Exception:
                    pass

    def _stop_server(self):
        for cmd in [
            ["systemctl", "--user", "stop", "ciel.service"],
            ["pkill", "-f", "ciel-api"],
            ["pkill", "-f", "ciell"],
        ]:
            try:
                subprocess.run(cmd, capture_output=True, timeout=5, check=False)
            except Exception:
                pass

        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(3)
            except Exception:
                pass

        if self.state == STATE_RUNNING or self.state == STATE_STARTING:
            self._on_status(STATE_STOPPED, "Arrêté")
            self._notify("CIEL", "Serveur arrêté")

    def _quit(self):
        self.poller.stop()
        self.poller_thread.quit()
        self.poller_thread.wait(2)
        QApplication.quit()


def main():
    logging.basicConfig(
        level=logging.DEBUG if "--debug" in sys.argv else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("CIEL Desktop")
    app.setOrganizationName("CIEL")

    # Gérer Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    desktop = CielDesktopApp()

    logger.info("CIEL Desktop démarré — icône dans la barre système")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
