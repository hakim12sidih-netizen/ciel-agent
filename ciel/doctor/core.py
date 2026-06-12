"""
CIEL v∞.8 — Doctor : diagnostic & auto-réparation.
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class DoctorFinding:
    id: str
    severity: str  # error | warning | info
    title: str
    detail: str = ""
    fixable: bool = False
    fix_description: str = ""


@dataclass
class DoctorReport:
    findings: list[DoctorFinding] = field(default_factory=list)
    fixed: list[str] = field(default_factory=list)

    @property
    def errors(self): return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self): return [f for f in self.findings if f.severity == "warning"]

    @property
    def info(self): return [f for f in self.findings if f.severity == "info"]


class Doctor:
    """Moteur de diagnostic et réparation."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or Path.home() / ".ciel"
        self.report = DoctorReport()

    # ── Checks ──

    def check_all(self) -> DoctorReport:
        self.report = DoctorReport()
        self._check_python()
        self._check_venv()
        self._check_config_dir()
        self._check_config_file()
        self._check_database()
        self._check_providers()
        self._check_port()
        self._check_disk_space()
        self._check_docker()
        self._check_git()
        self._check_autostart()
        self._check_identity()
        self._check_modules()
        return self.report

    def _check_python(self):
        v = sys.version_info
        if v >= (3, 12):
            self.report.findings.append(DoctorFinding("python", "ok", f"Python {v.major}.{v.minor}.{v.micro}"))
        else:
            self.report.findings.append(DoctorFinding("python", "error", f"Python {v.major}.{v.minor}.{v.micro} (< 3.12)", fixable=False))

    def _check_venv(self):
        in_venv = sys.prefix != sys.base_prefix
        if in_venv:
            self.report.findings.append(DoctorFinding("venv", "ok", "Environnement virtuel actif", detail=sys.prefix))
        else:
            self.report.findings.append(DoctorFinding("venv", "warning", "Hors environnement virtuel", fixable=True, fix_description="Créer un venv: python3 -m venv .venv && source .venv/bin/activate"))

    def _check_config_dir(self):
        if self.config_dir.exists():
            self.report.findings.append(DoctorFinding("config_dir", "ok", f"Dossier config: {self.config_dir}"))
        else:
            self.report.findings.append(DoctorFinding("config_dir", "warning", "Dossier config manquant", fixable=True, fix_description="Créer ~/.ciel"))
            if self._auto_fix:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                self.report.fixed.append("config_dir")

    def _check_config_file(self):
        cfg = self.config_dir / "ciel.json"
        if cfg.exists():
            try:
                data = json.loads(cfg.read_text())
                self.report.findings.append(DoctorFinding("config", "ok", "ciel.json valide"))
                # Validate required keys
                if "api" not in data:
                    self.report.findings.append(DoctorFinding("config_api", "warning", "Section 'api' manquante dans ciel.json", fixable=True, fix_description="Ajouter la section api"))
                if "brain" not in data:
                    self.report.findings.append(DoctorFinding("config_brain", "warning", "Section 'brain' manquante", fixable=True, fix_description="Ajouter la section brain"))
            except json.JSONDecodeError:
                self.report.findings.append(DoctorFinding("config", "error", "ciel.json corrompu (JSON invalide)", fixable=True, fix_description="Régénérer la configuration"))
        else:
            self.report.findings.append(DoctorFinding("config", "warning", "ciel.json manquant", fixable=True, fix_description="Générer la config: ciel install run --auto"))

    def _check_database(self):
        db_paths = [
            self.config_dir / "ciel.db",
            self.config_dir / "state.db",
            self.config_dir / "hermes_state.db",
        ]
        found = [p for p in db_paths if p.exists()]
        if found:
            for p in found:
                size = p.stat().st_size
                self.report.findings.append(DoctorFinding("database", "ok", f"Base {p.name}: {size:,} o"))
        else:
            self.report.findings.append(DoctorFinding("database", "info", "Aucune base de données trouvée"))

    def _check_providers(self):
        cfg_file = self.config_dir / "ciel.json"
        if not cfg_file.exists():
            return
        try:
            data = json.loads(cfg_file.read_text())
            providers = data.get("providers", {})
            configured = [k for k, v in providers.items() if v.get("api_key") or v.get("base_url")]
            if configured:
                self.report.findings.append(DoctorFinding("providers", "ok", f"{len(configured)} fournisseur(s) configuré(s): {', '.join(configured)}"))
            else:
                self.report.findings.append(DoctorFinding("providers", "info", "Aucun fournisseur LLM configuré"))
        except Exception:
            pass

    def _check_port(self):
        import socket
        for port in [8765, 8080]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    if s.connect_ex(("127.0.0.1", port)) == 0:
                        self.report.findings.append(DoctorFinding("port", "warning", f"Port {port} déjà utilisé"))
                    else:
                        self.report.findings.append(DoctorFinding("port", "ok", f"Port {port} libre"))
            except Exception:
                pass
            break  # Only check first

    def _check_disk_space(self):
        try:
            st = os.statvfs(str(self.config_dir))
            free = st.f_frsize * st.f_bavail
            free_gb = free / (1024**3)
            if free_gb < 1:
                self.report.findings.append(DoctorFinding("disk", "error", f"Espace disque faible: {free_gb:.1f} Go libre", fixable=False))
            elif free_gb < 5:
                self.report.findings.append(DoctorFinding("disk", "warning", f"Espace disque: {free_gb:.1f} Go libre"))
            else:
                self.report.findings.append(DoctorFinding("disk", "ok", f"Espace disque: {free_gb:.1f} Go libre"))
        except Exception:
            pass

    def _check_docker(self):
        if shutil.which("docker"):
            try:
                r = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    self.report.findings.append(DoctorFinding("docker", "ok", f"Docker {r.stdout.strip()}"))
                else:
                    self.report.findings.append(DoctorFinding("docker", "warning", "Docker installé mais non fonctionnel"))
            except Exception:
                self.report.findings.append(DoctorFinding("docker", "warning", "Docker installé mais non joignable"))
        else:
            self.report.findings.append(DoctorFinding("docker", "info", "Docker non installé (optionnel)"))

    def _check_git(self):
        if shutil.which("git"):
            r = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                self.report.findings.append(DoctorFinding("git", "ok", r.stdout.strip()))
        else:
            self.report.findings.append(DoctorFinding("git", "warning", "Git non installé", fixable=True, fix_description="Installer git"))

    def _check_autostart(self):
        from ciel.persistence import is_autostart_enabled
        if is_autostart_enabled():
            self.report.findings.append(DoctorFinding("autostart", "ok", "Redémarrage auto actif"))
        else:
            self.report.findings.append(DoctorFinding("autostart", "info", "Redémarrage auto désactivé", fixable=True, fix_description="Activer: ciel install run --auto-start"))

    def _check_identity(self):
        key_file = self.config_dir / "identity.pub"
        if key_file.exists():
            self.report.findings.append(DoctorFinding("identity", "ok", "Identité CIEL présente"))
        else:
            self.report.findings.append(DoctorFinding("identity", "info", "Identité non générée", fixable=True, fix_description="Générer: ciel identity --create"))

    def _check_modules(self):
        try:
            from ciel.brain.core import CIELBrain
            b = CIELBrain()
            b.load_all_modules()
            count = len(b._modules)
            self.report.findings.append(DoctorFinding("modules", "ok", f"{count} modules chargés"))
        except Exception as e:
            self.report.findings.append(DoctorFinding("modules", "warning", f"Modules: {e}"))

    # ── Fix ──

    def fix_all(self, auto_confirm: bool = False) -> list[str]:
        """Tente de réparer automatiquement tous les problèmes corrigeables."""
        self._auto_fix = True
        self.check_all()
        self._auto_fix = False
        fixed = []

        for finding in self.report.findings:
            if not finding.fixable:
                continue

            if finding.id == "config_dir":
                self.config_dir.mkdir(parents=True, exist_ok=True)
                fixed.append(finding.id)

            elif finding.id == "config":
                self._fix_config()
                fixed.append(finding.id)

            elif finding.id == "config_api":
                self._fix_config_section("api")
                fixed.append(finding.id)

            elif finding.id == "config_brain":
                self._fix_config_section("brain")
                fixed.append(finding.id)

            elif finding.id == "identity":
                self._fix_identity()
                fixed.append(finding.id)

            elif finding.id == "autostart":
                self._fix_autostart()
                fixed.append(finding.id)

        return fixed

    def _fix_config(self):
        cfg_file = self.config_dir / "ciel.json"
        default = {
            "api": {"host": "0.0.0.0", "port": 8765, "log_level": "INFO"},
            "brain": {"modules_autoload": True, "default_provider": "openai", "default_model": "gpt-4o"},
            "database": {"path": str(self.config_dir / "ciel.db")},
            "providers": {},
        }
        cfg_file.write_text(json.dumps(default, indent=2, ensure_ascii=False))

    def _fix_config_section(self, section: str):
        cfg_file = self.config_dir / "ciel.json"
        try:
            data = json.loads(cfg_file.read_text())
        except Exception:
            data = {}
        if section == "api":
            data.setdefault("api", {"host": "0.0.0.0", "port": 8765, "log_level": "INFO"})
        elif section == "brain":
            data.setdefault("brain", {"modules_autoload": True, "default_provider": "openai", "default_model": "gpt-4o"})
        elif section == "database":
            data.setdefault("database", {"path": str(self.config_dir / "ciel.db")})
        cfg_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _fix_identity(self):
        try:
            from ciel.core.identity import generate_identity
            generate_identity(self.config_dir)
        except ImportError:
            subprocess.run([sys.executable, "-m", "ciel.core.identity", "--create"], cwd=str(self.config_dir), capture_output=True)

    def _fix_autostart(self):
        try:
            from ciel.persistence import install_autostart
            install_autostart()
        except Exception:
            pass


def run_doctor(fix: bool = False, quiet: bool = False) -> DoctorReport:
    """Point d'entrée principal pour le diagnostic."""
    d = Doctor()
    if fix:
        d.fix_all()
    else:
        d.check_all()
    return d.report
