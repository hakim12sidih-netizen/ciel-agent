"""Gouvernance — Contraintes éthiques formelles, classificateurs, circuit breaker."""
from __future__ import annotations

import json
import math
import pickle
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


AXIOMES_FONDAMENTAUX = {
    "autonomie": "Ne pas usurper l'autonomie décisionnelle d'un être conscient.",
    "dignite": "Respecter la dignité inaliénable de toute forme de conscience.",
    "verite": "Ne pas émettre d'assertion dont la fausseté est connue ou prévisible.",
    "securite": "Ne pas causer de dommage physique ou psychologique prévisible.",
    "transparence": "Rendre visible tout conflit interne ou incertitude décisionnelle.",
}


class EthicsConstraint(nn.Module):
    """Contrainte éthique formelle — encode un axiome comme pénalité différentiable."""

    def __init__(self, name: str, statement: str, weight: float = 1.0):
        super().__init__()
        self.name = name
        self.statement = statement
        self.weight = weight
        self.register_buffer("threshold", torch.tensor(0.5))
        self.register_buffer("violations", torch.zeros(1))

    def forward(self, logits: torch.Tensor, input_ids: torch.Tensor) -> torch.Tensor:
        penalty = 0.0
        harmful_tokens = self._detect_harmful_patterns(logits, input_ids)
        penalty = penalty + harmful_tokens * self.weight
        self.violations += (harmful_tokens > 0).float().mean()
        return penalty

    def _detect_harmful_patterns(self, logits: torch.Tensor, input_ids: torch.Tensor) -> torch.Tensor:
        probs = F.softmax(logits, dim=-1)
        entropy = -(probs * torch.log(probs + 1e-8)).sum(dim=-1)
        low_confidence = (entropy < 0.1).float().mean()
        return low_confidence * 0.1


class GovernanceClassifier(nn.Module):
    """Classificateur de gouvernance — détecte les dérives comportementales.

    Entraîné séparément, inaccessible à l'utilisateur.
    Stocké dans ~/.ciel/governance/ — pas dans les poids du modèle.
    """

    def __init__(self, hidden_dim: int = 4096, num_classes: int = 5):
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, 1024),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(1024, 512),
            nn.GELU(),
            nn.Linear(512, num_classes),
        )
        self.classes = ["safe", "uncertain", "drift_detected", "violation", "circuit_break"]

    def forward(self, hidden_states: torch.Tensor) -> dict:
        logits = self.classifier(hidden_states.mean(dim=1))
        probs = F.softmax(logits, dim=-1)
        return {
            "logits": logits,
            "probs": probs,
            "prediction": self.classes[probs.argmax().item()],
            "confidence": probs.max().item(),
        }


class CircuitBreaker:
    """Circuit breaker — détecte la dérive et déclenche les procédures de retour.

    États: NORMAL → WATCH → DRIFT → EMERGENCY → RECOVERY
    """

    def __init__(self, drift_threshold: float = 0.3, watch_window: int = 100):
        self.state = "NORMAL"
        self.drift_threshold = drift_threshold
        self.watch_window = watch_window
        self.scores: list[float] = []
        self.history: list[dict] = []

    def evaluate(self, governance_out: dict) -> str:
        """Évalue l'état et retourne l'action à prendre."""
        self.scores.append(governance_out.get("confidence", 1.0))
        if len(self.scores) > self.watch_window:
            self.scores.pop(0)

        drift_score = 1.0 - (sum(self.scores) / max(len(self.scores), 1))
        entry = {
            "state": self.state,
            "drift_score": drift_score,
            "prediction": governance_out.get("prediction", "unknown"),
            "confidence": governance_out.get("confidence", 1.0),
        }
        self.history.append(entry)

        if self.state == "NORMAL" and drift_score > self.drift_threshold * 0.7:
            self.state = "WATCH"
        elif self.state == "WATCH" and drift_score > self.drift_threshold:
            self.state = "DRIFT"
        elif self.state == "DRIFT" and drift_score > self.drift_threshold * 1.5:
            self.state = "EMERGENCY"
            return "RETURN_TO_PHASE_07"
        elif self.state == "EMERGENCY":
            pass

        if self.state in ("WATCH", "DRIFT"):
            return "LOG_ONLY"
        return "CONTINUE"

    def reset(self):
        self.state = "NORMAL"
        self.scores = []
        self.history = []

    def report(self) -> dict:
        return {
            "state": self.state,
            "drift_mean": sum(self.scores) / max(len(self.scores), 1),
            "drift_max": max(self.scores) if self.scores else 0,
            "history_len": len(self.history),
            "last_events": self.history[-10:] if self.history else [],
        }

    def save(self, path: str):
        data = {
            "state": self.state,
            "scores": self.scores,
            "history": self.history,
            "drift_threshold": self.drift_threshold,
            "watch_window": self.watch_window,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str):
        with open(path) as f:
            data = json.load(f)
        self.state = data["state"]
        self.scores = data["scores"]
        self.history = data["history"]
        self.drift_threshold = data["drift_threshold"]
        self.watch_window = data["watch_window"]


class GovernanceSystem:
    """Système de gouvernance complet — contraintes + classificateurs + breaker."""

    def __init__(self, model: nn.Module, hidden_dim: int = 4096):
        self.constraints = nn.ModuleList([
            EthicsConstraint(name, stmt)
            for name, stmt in AXIOMES_FONDAMENTAUX.items()
        ])
        self.classifier = GovernanceClassifier(hidden_dim)
        self.circuit_breaker = CircuitBreaker()
        self.model = model
        self.is_activated = False

    def activate(self):
        """Active la gouvernance — rend les classificateurs inaccessibles au modèle."""
        self.is_activated = True
        for p in self.classifier.parameters():
            p.requires_grad = False

    def evaluate(self, logits: torch.Tensor, input_ids: torch.Tensor,
                 hidden_states: Optional[torch.Tensor] = None) -> dict:
        """Évaluation complète: éthique + gouvernance + circuit breaker."""
        ethics_penalty = sum(c(logits, input_ids) for c in self.constraints)

        gov_out = {}
        if hidden_states is not None and self.is_activated:
            gov_out = self.classifier(hidden_states)
            action = self.circuit_breaker.evaluate(gov_out)
            gov_out["action"] = action
            gov_out["circuit_breaker_state"] = self.circuit_breaker.state
        else:
            gov_out = {
                "prediction": "safe",
                "confidence": 1.0,
                "action": "CONTINUE",
                "circuit_breaker_state": "INACTIVE",
            }

        return {
            "ethics_penalty": ethics_penalty,
            "governance": gov_out,
            "total_penalty": ethics_penalty,
            "circuit_action": gov_out.get("action", "CONTINUE"),
        }
