from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Modality(Enum):
    VISUAL = "visual"
    ACOUSTIC = "acoustic"
    TACTILE = "tactile"
    KINESTHETIC = "kinesthetic"
    PROXIMITY = "proximity"
    THERMAL = "thermal"
    CHEMICAL = "chemical"
    MAGNETIC = "magnetic"
    ELECTRIC = "electric"
    VIBRATIONAL = "vibrational"
    PRESSURE = "pressure"


@dataclass(slots=True)
class SensoryInput:
    modality: Modality
    data: dict[str, Any]
    intensity: float
    timestamp: float
    source: str = ""


@dataclass(slots=True)
class IntegratedPercept:
    id: str
    modalities: list[Modality]
    content: dict[str, Any]
    confidence: float
    salience: float


class Sensorium:
    def __init__(self) -> None:
        self._inputs: list[SensoryInput] = []
        self._percepts: list[IntegratedPercept] = []
        self._thresholds: dict[Modality, float] = {m: 0.1 for m in Modality}

    def receive(self, modality: Modality, data: dict[str, Any], intensity: float = 0.5, source: str = "") -> SensoryInput:
        si = SensoryInput(modality=modality, data=data, intensity=intensity, timestamp=time.time(), source=source)
        self._inputs.append(si)
        return si

    def integrate(self) -> IntegratedPercept | None:
        recent = [i for i in self._inputs if time.time() - i.timestamp < 1.0]
        if not recent:
            return None
        active_mods = [i.modality for i in recent if i.intensity >= self._thresholds[i.modality]]
        if not active_mods:
            return None
        combined: dict[str, Any] = {}
        for inp in recent:
            combined.update(inp.data)
        ip = IntegratedPercept(
            id=f"percept_{len(self._percepts)}",
            modalities=list(set(active_mods)),
            content=combined,
            confidence=min(1.0, sum(i.intensity for i in recent) / len(recent)),
            salience=len(active_mods) / len(Modality),
        )
        self._percepts.append(ip)
        return ip

    def get_recent_inputs(self, n: int = 10) -> list[SensoryInput]:
        return self._inputs[-n:]

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            return {"success": True, "inputs": len(self._inputs), "percepts": len(self._percepts), "modalities": len(Modality)}
        elif action == "receive":
            mod_str = input_data.get("modality", "visual")
            try:
                mod = Modality(mod_str)
            except ValueError:
                return {"success": False, "error": f"unknown modality '{mod_str}'"}
            si = self.receive(mod, input_data.get("data", {}), float(input_data.get("intensity", 0.5)))
            return {"success": True, "input_id": len(self._inputs) - 1, "modality": si.modality.value}
        elif action == "integrate":
            ip = self.integrate()
            if ip:
                return {"success": True, "percept_id": ip.id, "modalities": len(ip.modalities), "confidence": ip.confidence}
            return {"success": False, "error": "no data to integrate"}
        return {"success": False, "error": f"unknown action '{action}'"}
