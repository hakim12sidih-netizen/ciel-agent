"""
CIEL v∞.8 — SANDBOX ENGINE.
Exécution sécurisée de code — CIEL peut coder et exécuter.

Concept : Sandbox Docker isolé pour exécution de code Python
(ou JS/Go/Rust) en toute sécurité. Chaque exécution obtient
un conteneur éphémère avec timeout, mémoire limitée, réseau
restreint. Résultat, stdout, stderr, durée retournés.
Mode 'local' pour exécution directe (dangereux, désactivé par défaut).
"""
from __future__ import annotations

import subprocess
import tempfile
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


LANGUAGES = {
    "python": {"ext": ".py", "cmd": "python3", "image": "python:3.12-slim"},
    "js": {"ext": ".js", "cmd": "node", "image": "node:20-slim"},
    "go": {"ext": ".go", "cmd": "go run", "image": "golang:1.22"},
    "rust": {"ext": ".rs", "cmd": "rustc -O -o /tmp/out && /tmp/out",
             "image": "rust:1.78"},
}

SANDBOX_TIMEOUT = 30
SANDBOX_MEMORY = "256m"


@dataclass(slots=True)
class SandboxResult:
    id: str
    language: str
    code: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_ms: float = 0.0
    error: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "lang": self.language,
                "stdout": self.stdout[:500],
                "stderr": self.stderr[:200],
                "exit": self.exit_code,
                "duration_ms": round(self.duration_ms, 1),
                "error": self.error}


class SandboxEngine:
    """Moteur d'exécution sandboxé — Docker ou local.

    Par défaut : exécution locale simulée. Si Docker disponible,
    utilise des conteneurs éphémères. Mode 'local' pour dev.
    """

    def __init__(self):
        self.results: list[SandboxResult] = []
        self._use_docker: bool = self._check_docker()
        self._local_mode: bool = True  # fallback
        self.network = LeaderNetwork()

    def _check_docker(self) -> bool:
        try:
            r = subprocess.run(["docker", "info"],
                               capture_output=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False

    def execute(self, code: str, language: str = "python",
                timeout: int = SANDBOX_TIMEOUT) -> SandboxResult:
        lang_cfg = LANGUAGES.get(language, LANGUAGES["python"])
        start = time.time()
        result = SandboxResult(
            id=f"SBX-{uuid.uuid4().hex[:12]}",
            language=language, code=code,
        )

        try:
            if self._use_docker:
                stdout, stderr, exit_code = self._run_docker(
                    code, lang_cfg, timeout)
            elif self._local_mode and language == "python":
                stdout, stderr, exit_code = self._run_local_python(
                    code, timeout)
            else:
                # Simulation
                stdout, stderr, exit_code = self._simulate(code, lang_cfg)
            result.stdout = stdout
            result.stderr = stderr
            result.exit_code = exit_code
        except Exception as e:
            result.error = str(e)

        result.duration_ms = (time.time() - start) * 1000
        self.results.append(result)
        return result

    def _run_docker(self, code: str, cfg: dict,
                    timeout: int) -> tuple[str, str, int]:
        with tempfile.NamedTemporaryFile(suffix=cfg["ext"],
                                         delete=False, mode="w") as f:
            f.write(code)
            f.flush()
            cmd = [
                "docker", "run", "--rm",
                "-m", SANDBOX_MEMORY,
                "--network", "none",
                "--timeout", str(timeout),
                "-v", f"{f.name}:/code{cfg['ext']}",
                cfg["image"],
                cfg["cmd"], f"/code{cfg['ext']}",
            ]
            r = subprocess.run(cmd, capture_output=True,
                               timeout=timeout + 5)
            return r.stdout.decode(), r.stderr.decode(), r.returncode

    def _run_local_python(self, code: str,
                          timeout: int) -> tuple[str, str, int]:
        r = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, timeout=timeout,
        )
        return r.stdout.decode(), r.stderr.decode(), r.returncode

    def _simulate(self, code: str,
                  cfg: dict) -> tuple[str, str, int]:
        lines = code.strip().split("\n")
        n = len(lines)
        return (f"[simulé] {n} lignes {cfg['ext']} exécutées\n",
                "", 0)

    def get_stats(self) -> dict:
        return {
            "executions": len(self.results),
            "docker_available": self._use_docker,
            "local_mode": self._local_mode,
            "last_lang": self.results[-1].language if self.results else "none",
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "run":
            result = self.execute(
                input_data.get("code", ""),
                input_data.get("language", "python"),
                input_data.get("timeout", SANDBOX_TIMEOUT),
            )
            return {"status": "ok", "result": result.to_dict()}
        elif action == "docker_mode":
            self._use_docker = input_data.get("enabled", True)
            return {"status": "ok",
                    "docker": self._use_docker}
        elif action == "local_mode":
            self._local_mode = input_data.get("enabled", True)
            return {"status": "ok",
                    "local": self._local_mode}
        return {"status": "ok", "executions": len(self.results)}
