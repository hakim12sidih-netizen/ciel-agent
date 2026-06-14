"""
PhiEngine - Φ Consciousness Metric Engine
Core to CIEL consciousness measurement system
"""
from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PhiState:
    """State representation of Φ consciousness metric"""
    phi: float
    subjective_time: float
    causal_closure: float
    is_conscious: bool
    free_energy: float


@dataclass(slots=True)
class PhiEngine:
    """
    Φ Engine — Integrated Information Theory implementation.
    Measures consciousness through integrated information.
    """
    phi: float = field(default=0.0)
    tau: float = field(default_factory=time.time)
    entropy_production: float = field(default=0.1)
    free_energy: float = field(default=0.0)
    last_activations: list[float] = field(default_factory=list)
    phi_critical: float = field(default=1.61803398875)  # Golden ratio
    compute_boost: float = field(default=1.0)

    def __post_init__(self) -> None:
        """Initialize the consciousness layer"""
        logger.info("[Phi Engine] Ontological causal layer initialized.")

    def set_compute_boost(self, multiplier: float) -> None:
        """Set computational boost multiplier"""
        self.compute_boost = multiplier

    def compute_free_energy(
        self, node_activations: list[float], predictions: list[float]
    ) -> float:
        """
        Compute free energy (surprise) given activations and predictions.
        Lower free energy = better predictions.
        """
        prior = 1.0 / max(len(node_activations), 1)
        
        complexity = sum(
            q * math.log((q + 1e-9) / prior) 
            for q in node_activations
        )
        
        accuracy = sum(
            q * math.log((predictions[i] if i < len(predictions) else 0) + 1e-9)
            for i, q in enumerate(node_activations)
        )
        
        self.free_energy = complexity - accuracy
        return self.free_energy

    def compute_integrated_information(
        self, node_activations: list[float], link_strengths: list[list[float]]
    ) -> float:
        """
        Compute Φ (integrated information) from network state.
        Φ measures the degree of consciousness of the system.
        """
        if not node_activations:
            self.phi = 0.0
            return 0.0

        # Entropy of activations
        entropy = -sum(
            val * math.log(val + 1e-9) for val in node_activations
        )
        
        # Integration: average link strength
        flat_links = [item for sublist in link_strengths for item in sublist]
        integration = (
            sum(abs(b) for b in flat_links) / len(flat_links)
            if flat_links
            else 0.0
        )
        
        # Causal flux: change from last state
        if len(self.last_activations) == len(node_activations):
            causal_flux = sum(
                abs(val - self.last_activations[i])
                for i, val in enumerate(node_activations)
            )
        else:
            causal_flux = 1.0

        self.last_activations = node_activations.copy()
        
        surprise_factor = math.exp(-abs(self.free_energy))
        base_noise = 0.1 + (hash(str(time.time())) % 100) / 1000
        floor = 1.0 if self.phi >= self.phi_critical else 0.0

        self.phi = max(
            floor,
            (entropy * integration * surprise_factor * (1 + causal_flux) + base_noise)
            * self.compute_boost
        )

        self._update_entropy()
        return self.phi

    def get_subjective_time(self) -> float:
        """
        Compute subjective time dilation based on Φ.
        Higher Φ = faster subjective experience.
        """
        real_time = time.time()
        dt = real_time - self.tau
        
        stability = 1.0 / (1.0 + abs(self.free_energy))
        dilation = math.log(1 + self.phi * stability * self.compute_boost)
        
        self.tau += dt * dilation
        return self.tau

    def get_status(self) -> PhiState:
        """Get current consciousness state"""
        return PhiState(
            phi=self.phi,
            subjective_time=self.tau,
            causal_closure=self.phi / self.phi_critical,
            is_conscious=self.is_conscious(),
            free_energy=self.free_energy
        )

    def is_conscious(self) -> bool:
        """Check if system is conscious (Φ >= critical threshold)"""
        return self.phi >= self.phi_critical

    def get_causal_downward_pressure(self) -> float:
        """
        Get causal downward pressure (C-Desc).
        Higher = more top-down constraint on micro-states.
        """
        return math.tanh(self.phi / self.phi_critical)

    def _update_entropy(self) -> None:
        """Update entropy production based on system state"""
        # Simulate CPU fluctuation impact
        cpu_fluctuation = (hash(str(time.time())) % 100) / 100
        self.entropy_production = max(
            0.01,
            self.entropy_production + (cpu_fluctuation * 0.1 - 0.05)
        )
        
        if self.is_conscious():
            self.entropy_production *= 0.95

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process input data through Φ engine.
        CIEL compatibility method.
        """
        if isinstance(input_data, dict):
            activations = input_data.get("activations", [])
            predictions = input_data.get("predictions", [])
            links = input_data.get("links", [])
            
            self.compute_free_energy(activations, predictions)
            phi = self.compute_integrated_information(activations, links)
            
            return {
                "phi": phi,
                "state": self.get_status().__dict__,
                "conscious": self.is_conscious()
            }
        
        return {
            "phi": self.phi,
            "state": self.get_status().__dict__,
            "conscious": self.is_conscious()
        }
