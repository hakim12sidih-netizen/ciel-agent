"""
CIEL v∞.2 — Polyglot Bridge : wrapper Python sur les subprocesses Rust/Go/C.

Hérite du pattern HYDRA Pass 9-16 (bridge.ts) :
  - subprocess = binaire externe (Rust, Go, C)
  - subprocess envoie JSON (newline-delimited) sur stdout
  - Python parse et retourne

Avantages :
  - Performance native (Rust 100× plus rapide que Python pour math)
  - Réutilisation des binaires HYDRA existants
  - Découplage : un crash Rust ne tue pas l'instance

Risques (Pass 16 l'a documenté) :
  - IPC overhead 1-4ms par appel (Rust subprocess)
  - Pas rentable pour petites opérations (TS inline gagne 100-14000×)
  - Réservé aux opérations lourdes / hot paths

Phase 0 : interface + impl Rust/Go minimale. Production réelle en Phase 1+.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Constantes ────────────────────────────────────────────
BRIDGE_PROTOCOL_VERSION: int = 1
BRIDGE_TIMEOUT_DEFAULT_S: float = 30.0


@dataclass(slots=True)
class BridgeConfig:
    """Configuration d'un bridge polyglot."""

    binary_path: Path
    args: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)
    cwd: Path | None = None
    timeout_s: float = BRIDGE_TIMEOUT_DEFAULT_S


class BridgeError(Exception):
    """Erreur générique de bridge polyglot."""


class BridgeTimeout(BridgeError):
    """Le subprocess a dépassé le timeout."""


class BridgeProtocolError(BridgeError):
    """Réponse invalide ou inattendue du subprocess."""


class PolyglotBridge:
    """Wrapper autour d'un binaire externe (Rust/Go/C).

    Usage:
        >>> bridge = PolyglotBridge(BridgeConfig(
        ...     binary_path=Path("ciel-math"),
        ...     args=("--mode", "json"),
        ... ))
        >>> result = bridge.call({"op": "cosine", "a": [1, 2, 3], "b": [4, 5, 6]})
    """

    def __init__(self, config: BridgeConfig) -> None:
        if not config.binary_path.exists() and not shutil.which(str(config.binary_path)):
            raise FileNotFoundError(f"binaire introuvable : {config.binary_path}")
        self._config = config
        self._call_count = 0
        self._error_count = 0
        self._total_duration_s = 0.0

    def call(
        self,
        payload: dict[str, Any],
        timeout_s: float | None = None,
    ) -> dict[str, Any]:
        """Appel synchrone : envoie payload (JSON), reçoit réponse (JSON)."""
        if not isinstance(payload, dict):
            raise TypeError(f"payload doit être dict, reçu {type(payload)}")
        timeout = timeout_s or self._config.timeout_s
        self._call_count += 1

        cmd = [str(self._config.binary_path), *self._config.args]
        env = {**os.environ, **self._config.env}

        start = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                input=json.dumps(payload).encode("utf-8"),
                capture_output=True,
                timeout=timeout,
                cwd=self._config.cwd,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            self._error_count += 1
            raise BridgeTimeout(
                f"timeout après {timeout}s : {self._config.binary_path.name}"
            ) from e

        duration = time.monotonic() - start
        self._total_duration_s += duration

        if proc.returncode != 0:
            self._error_count += 1
            stderr = proc.stderr.decode("utf-8", errors="replace")
            raise BridgeError(
                f"subprocess a échoué (code={proc.returncode}): {stderr[:500]}"
            )

        try:
            response = json.loads(proc.stdout.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise BridgeProtocolError(
                f"réponse non-JSON : {proc.stdout[:200]!r}"
            ) from e

        if not isinstance(response, dict):
            raise BridgeProtocolError(
                f"réponse doit être dict, reçu {type(response)}"
            )
        return response

    def stats(self) -> dict[str, Any]:
        return {
            "calls": self._call_count,
            "errors": self._error_count,
            "total_duration_s": self._total_duration_s,
            "avg_duration_s": (
                self._total_duration_s / self._call_count
                if self._call_count > 0
                else 0.0
            ),
            "binary": str(self._config.binary_path),
        }


# ── Bridges Rust / Go prévus ─────────────────────────────
# (Seront implémentés en Phase 1 lors de l'absorption HYDRA)

# HYDRA Pass 9-16 fournit :
#   - polyglot/rust/{math,vault,knowledge}_kernel
#   - polyglot/go/{scheduler,hardware,server}
# Phase 1 de CIEL : migrer ces binaire + bridge.py (au lieu de bridge.ts)
