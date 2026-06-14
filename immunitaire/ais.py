from __future__ import annotations

import logging
import math
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ImmuneState(Enum):
    TOLERANCE = "tolerance"
    INNATE = "innate"
    ADAPTIVE = "adaptive"
    MEMORY = "memory"
    HYPERMUTATION = "hypermutation"


class ImmuneResponse(Enum):
    NONE = "none"
    INNATE = "innate"
    ADAPTIVE = "adaptive"
    MEMORY = "memory"
    TOLERANCE = "tolerance"


@dataclass(slots=True)
class Antibody:
    id: str
    vector: np.ndarray
    affinity: float = 0.0
    concentration: float = 1.0
    clone_count: int = 0
    generation: int = 0
    b_cell: bool = False
    t_cell: bool = False
    created_at: float = field(default_factory=time.time)
    last_affinity_update: float = 0.0

    def clone(self) -> Antibody:
        return Antibody(
            id=f"{self.id}_c{self.clone_count}",
            vector=self.vector.copy(),
            affinity=self.affinity,
            concentration=self.concentration * 0.5,
            clone_count=self.clone_count + 1,
            generation=self.generation + 1,
            b_cell=self.b_cell,
            t_cell=self.t_cell,
        )


@dataclass(slots=True)
class ImmuneMemory:
    pathogen_signature: np.ndarray
    antibody: Antibody
    response_time: float
    recall_count: int = 0
    last_recall: float = 0.0
    affinity_threshold: float = 0.8


class AIS:
    """Artificial Immune System central — intègre tous les mécanismes immunitaires."""

    def __init__(
        self,
        dimension: int = 10,
        initial_population: int = 100,
        mutation_rate: float = 0.1,
        clone_factor: float = 0.3,
        suppression_threshold: float = 0.9,
        tolerance_threshold: float = 0.3,
    ) -> None:
        self.dimension = dimension
        self.mutation_rate = mutation_rate
        self.clone_factor = clone_factor
        self.suppression_threshold = suppression_threshold
        self.tolerance_threshold = tolerance_threshold
        self.b_cells: list[Antibody] = []
        self.t_cells: list[Antibody] = []
        self.memory: list[ImmuneMemory] = []
        self.self_set: list[np.ndarray] = []
        self.danger_signals: list[float] = []
        self.state = ImmuneState.TOLERANCE
        self.generation = 0
        self._init_population(initial_population)

    def _init_population(self, n: int) -> None:
        for i in range(n):
            vec = np.random.uniform(-1, 1, self.dimension)
            ab = Antibody(id=f"b{i}", vector=vec, b_cell=True, affinity=0.0)
            self.b_cells.append(ab)
        for i in range(n // 2):
            vec = np.random.uniform(-1, 1, self.dimension)
            ab = Antibody(id=f"t{i}", vector=vec, b_cell=False, t_cell=True, affinity=0.0)
            self.t_cells.append(ab)
        logger.info(f"AIS initialized: {len(self.b_cells)} B-cells, {len(self.t_cells)} T-cells")

    def add_self(self, sample: np.ndarray) -> None:
        self.self_set.append(sample.copy())

    def _affinity(self, antibody: np.ndarray, antigen: np.ndarray) -> float:
        return 1.0 / (1.0 + float(np.linalg.norm(antibody - antigen)))

    def negative_selection(self, candidates: list[np.ndarray]) -> list[np.ndarray]:
        """Negative selection: remove detectors that match self."""
        if not self.self_set:
            return candidates
        valid: list[np.ndarray] = []
        for c in candidates:
            matches_self = any(
                self._affinity(c, s) > self.tolerance_threshold for s in self.self_set
            )
            if not matches_self:
                valid.append(c)
        return valid

    def detect(self, antigen: np.ndarray) -> ImmuneResponse:
        response = ImmuneResponse.NONE
        # Check memory first
        for mem in self.memory:
            aff = self._affinity(mem.antibody.vector, antigen)
            if aff > mem.affinity_threshold:
                mem.recall_count += 1
                mem.last_recall = time.time()
                response = ImmuneResponse.MEMORY
                logger.debug(f"Memory recall: affinity={aff:.4f}")
                return response

        # B-cell activation
        best_aff = 0.0
        best_cell: Antibody | None = None
        for cell in self.b_cells:
            aff = self._affinity(cell.vector, antigen)
            if aff > best_aff:
                best_aff = aff
                best_cell = cell
        for cell in self.t_cells:
            aff = self._affinity(cell.vector, antigen)
            if aff > best_aff:
                best_aff = aff
                best_cell = cell
        if best_cell:
            best_cell.affinity = best_aff
            best_cell.last_affinity_update = time.time()
        danger = sum(self.danger_signals[-10:]) / max(1, len(self.danger_signals[-10:]))

        if danger > 0.5 and best_aff > self.tolerance_threshold:
            response = ImmuneResponse.ADAPTIVE
            self.state = ImmuneState.HYPERMUTATION
            self._clonal_expansion(best_cell, antigen)
        elif best_aff > self.tolerance_threshold:
            response = ImmuneResponse.INNATE
            self.state = ImmuneState.INNATE
        else:
            response = ImmuneResponse.TOLERANCE
            self.state = ImmuneState.TOLERANCE
        return response

    def _clonal_expansion(self, parent: Antibody | None, antigen: np.ndarray) -> None:
        if parent is None:
            return
        n_clones = max(1, int(self.clone_factor * len(self.b_cells) / (1 + parent.affinity * 10)))
        for _ in range(n_clones):
            clone = parent.clone()
            mutation_strength = self.mutation_rate * (1.0 / (1.0 + parent.affinity * 5))
            clone.vector += np.random.normal(0, mutation_strength, self.dimension)
            clone.vector = np.clip(clone.vector, -1, 1)
            clone.affinity = self._affinity(clone.vector, antigen)
            if clone.affinity > parent.affinity and len(self.b_cells) < 1000:
                self.b_cells.append(clone)
        # Affinity maturation: keep top antibodies
        self.b_cells.sort(key=lambda x: x.affinity, reverse=True)
        self.b_cells = self.b_cells[:len(self.b_cells) // 2]

    def add_danger_signal(self, signal: float) -> None:
        self.danger_signals.append(signal)
        if len(self.danger_signals) > 100:
            self.danger_signals.pop(0)

    def create_memory(self, antigen: np.ndarray, response_time: float) -> None:
        best = max(self.b_cells, key=lambda x: self._affinity(x.vector, antigen), default=None)
        if best and best.affinity > self.tolerance_threshold * 1.5:
            mem = ImmuneMemory(
                pathogen_signature=antigen.copy(),
                antibody=best.clone(),
                response_time=response_time,
                affinity_threshold=max(0.7, best.affinity * 0.9),
            )
            self.memory.append(mem)
            logger.debug(f"Immune memory created: affinity={best.affinity:.4f}")

    def suppress_autoimmunity(self) -> None:
        """Remove antibodies that match self (central tolerance)."""
        before = len(self.b_cells)
        self.b_cells = [
            c for c in self.b_cells
            if not any(self._affinity(c.vector, s) > self.tolerance_threshold for s in self.self_set)
        ]
        removed = before - len(self.b_cells)
        if removed:
            logger.debug(f"Suppressed {removed} self-reactive B-cells")

    def homeostasis_deviation(self) -> float:
        if not self.b_cells:
            return 0.0
        affinities = [c.affinity for c in self.b_cells if c.affinity > 0]
        if not affinities:
            return 0.0
        return float(np.std(affinities) / np.mean(affinities))

    def status(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "b_cells": len(self.b_cells),
            "t_cells": len(self.t_cells),
            "memory": len(self.memory),
            "self_set": len(self.self_set),
            "danger_signals": len(self.danger_signals),
            "generation": self.generation,
            "homeostasis_deviation": self.homeostasis_deviation(),
        }
