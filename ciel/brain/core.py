from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.analysis.core import LabyrinthEngine
from ciel.animus.core import AnimusEngine
from ciel.conscience.core import ConsciousnessEngine
from ciel.economy.core import EconomyEngine
from ciel.evolution.core import EvolutionEngine
from ciel.hermes.core import HermesEngine
from ciel.math.core import MathEngine
from ciel.meta.core import MetaEngine
from ciel.noosphere.core import NoosphereEngine
from ciel.openclaw.core import OpenClawEngine
from ciel.perception.core import PerceptionEngine
from ciel.quantum.core import QuantumEngine
from ciel.security.core import SecurityEngine
from ciel.skills.core import ForgeronEngine
from ciel.swarm.core import SwarmEngine


class ProcessStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass(slots=True)
class CIELState:
    uptime: float = 0.0
    n_cycles: int = 0
    modules_loaded: list[str] = field(default_factory=list)
    last_error: str = ""
    status: ProcessStatus = ProcessStatus.IDLE
    active_processes: int = 0


class CIELBrain:
    """CIELBrain — cortex unifié intégrant les 10 phases de CIEL v∞.3.

    Point d'entrée unique pour toutes les strates :
    Phase 0-2 : Core, Axiomes, Crypto, Kernel, Polyglot
    Phase 3   : Évolution (60+ algorithmes)
    Phase 4   : Hermes (Gateway, State, Providers)
    Phase 5   : OpenClaw (Channels, Skills, Gateway)
    Phase 6   : Immunitaire + Narrateur
    Phase 7   : VSM, FEP, Gödel, Quine, Logics
    Phase 8   : CIEL-LM (CoT, ToT, GoT, NTP, ReAct, STaR, RAP)
    Phase 9   : Économie, Conscience, Chronos, Logos
    Phase 10  : Neuro-Symbolique, Abstraction, Hybrid Reasoning
    """

    def __init__(self, name: str = "CIEL v∞.3") -> None:
        self.name = name
        self.state = CIELState()
        self._modules: dict[str, Any] = {}
        self._hooks: dict[str, list[Callable]] = {}
        self._start_time: float = 0.0

    def load_module(self, name: str, instance: Any) -> None:
        self._modules[name] = instance
        self.state.modules_loaded.append(name)

    def get_module(self, name: str) -> Any:
        return self._modules.get(name)

    def has_module(self, name: str) -> bool:
        return name in self._modules

    def register_hook(self, event: str, hook: Callable) -> None:
        self._hooks.setdefault(event, []).append(hook)

    def emit(self, event: str, **data: Any) -> list[Any]:
        results = []
        for h in self._hooks.get(event, []):
            try:
                results.append(h(**data))
            except Exception as e:
                self.state.last_error = f"{event}: {e}"
        return results

    def start(self) -> None:
        self._start_time = time.time()
        self.state.status = ProcessStatus.RUNNING
        self.state.uptime = 0.0
        self.emit("brain.start")

    def cycle(self) -> dict[str, Any]:
        """Un cycle complet du cerveau CIEL."""
        self.state.n_cycles += 1
        self.state.uptime = time.time() - self._start_time
        results: dict[str, Any] = {
            "cycle": self.state.n_cycles,
            "uptime": self.state.uptime,
            "modules_active": len(self._modules),
        }
        self.emit("brain.cycle", **results)
        return results

    def pause(self) -> None:
        self.state.status = ProcessStatus.PAUSED
        self.emit("brain.pause")

    def resume(self) -> None:
        self.state.status = ProcessStatus.RUNNING
        self.emit("brain.resume")

    def stop(self) -> None:
        self.state.status = ProcessStatus.TERMINATED
        self.emit("brain.stop")

    def status_report(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.state.status.value,
            "uptime": self.state.uptime,
            "cycles": self.state.n_cycles,
            "modules": list(self.state.modules_loaded),
            "active_processes": self.state.active_processes,
            "last_error": self.state.last_error,
        }

    def load_all_modules(self, peer_id: str = "ciel-node") -> None:
        """Charge et initialise tous les moteurs CIEL dans le cerveau."""
        self.load_module("analysis", LabyrinthEngine())
        self.load_module("animus", AnimusEngine())
        self.load_module("conscience", ConsciousnessEngine())
        self.load_module("economy", EconomyEngine())
        self.load_module("evolution", EvolutionEngine())
        self.load_module("hermes", HermesEngine())
        self.load_module("math", MathEngine())
        self.load_module("meta", MetaEngine())
        self.load_module("noosphere", NoosphereEngine())
        self.load_module("openclaw", OpenClawEngine())
        self.load_module("perception", PerceptionEngine())
        self.load_module("quantum", QuantumEngine())
        self.load_module("security", SecurityEngine())
        self.load_module("skills", ForgeronEngine())
        self.load_module("swarm", SwarmEngine(peer_id=peer_id))
        self.emit("brain.modules_loaded", count=15)

    def process(self, input_data: Any) -> Any:
        """Pipeline de traitement unifié à travers tous les modules."""
        data = input_data
        for mod_name in self.state.modules_loaded:
            mod = self._modules.get(mod_name)
            if mod and hasattr(mod, "process"):
                try:
                    result = mod.process(data)
                    if isinstance(result, dict) and not result.get("success", True):
                        self.state.last_error = f"{mod_name}.process: {result.get('error', 'unknown')}"
                    data = result
                except Exception as e:
                    self.state.last_error = f"{mod_name}.process: {e}"
                    break
        return data
