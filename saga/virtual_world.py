"""Monde virtuel pour Phase 00 — ancrage causal sans langage.

Génère des séquences (état, action, état_suivant) pour entraîner
la prédiction de conséquences d'actions — zéro texte.
"""
from __future__ import annotations

import math
import random
from typing import Optional

import torch
from torch.utils.data import Dataset, DataLoader


class VirtualWorldState:
    """État d'un monde virtuel simple."""
    DIMENSIONS = {
        "physics": {"gravity": (-1, 1), "momentum": (-1, 1), "collision": (0, 1)},
        "social": {"trust": (0, 1), "cooperation": (0, 1), "dominance": (0, 1)},
        "economic": {"resources": (0, 100), "trade": (0, 1), "value": (0, 1)},
        "spatial": {"x": (0, 100), "y": (0, 100), "z": (0, 100)},
    }

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.features = {}
        for domain, feats in self.DIMENSIONS.items():
            for name, (lo, hi) in feats.items():
                self.features[f"{domain}_{name}"] = random.uniform(lo, hi)

    def to_tensor(self) -> torch.Tensor:
        vals = [v for v in self.features.values()]
        return torch.tensor(vals, dtype=torch.float32)

    @staticmethod
    def num_features() -> int:
        return sum(len(v) for v in VirtualWorldState.DIMENSIONS.values())

    def __repr__(self) -> str:
        return f"WorldState({len(self.features)} features)"


class VirtualAction:
    """Action possible dans le monde virtuel."""
    TYPES = [
        "push", "pull", "give", "take", "move_toward", "move_away",
        "combine", "break", "observe", "wait", "communicate", "hide",
    ]

    def __init__(self, action_type: str, intensity: float = 0.5,
                 target: str = "self"):
        self.type = action_type
        self.intensity = max(0.0, min(1.0, intensity))
        self.target = target

    def to_tensor(self) -> torch.Tensor:
        type_one_hot = [1.0 if t == self.type else 0.0 for t in self.TYPES]
        return torch.tensor(
            type_one_hot + [self.intensity],
            dtype=torch.float32,
        )

    @staticmethod
    def num_features() -> int:
        return len(VirtualAction.TYPES) + 1

    @staticmethod
    def random() -> VirtualAction:
        return VirtualAction(
            action_type=random.choice(VirtualAction.TYPES),
            intensity=random.random(),
            target=random.choice(["self", "other", "environment"]),
        )


def apply_action(state: VirtualWorldState, action: VirtualAction) -> VirtualWorldState:
    """Applique une action à un état et retourne le nouvel état."""
    new_state = VirtualWorldState()
    new_state.features = dict(state.features)
    action_idx = VirtualAction.TYPES.index(action.type)

    for feat_name in new_state.features:
        current = new_state.features[feat_name]
        delta = 0
        domain, fname = feat_name.split("_", 1)

        if action_idx == 0:  # push
            if domain == "physics":
                delta = action.intensity * 0.2 * random.uniform(-1, 1)
            elif domain == "social":
                delta = -action.intensity * 0.05
        elif action_idx == 1:  # pull
            if domain == "physics":
                delta = -action.intensity * 0.2 * random.uniform(-1, 1)
            elif domain == "social":
                delta = action.intensity * 0.05
        elif action_idx == 2:  # give
            if domain == "economic":
                delta = -action.intensity * 5
        elif action_idx == 3:  # take
            if domain == "economic":
                delta = action.intensity * 5
        elif action_idx == 4:  # move_toward
            if domain == "spatial":
                delta = action.intensity * 5 * random.uniform(0.5, 1.5)
        elif action_idx == 5:  # move_away
            if domain == "spatial":
                delta = -action.intensity * 5 * random.uniform(0.5, 1.5)
        elif action_idx == 6:  # combine
            if domain == "economic":
                delta = action.intensity * random.uniform(-2, 5)
        elif action_idx == 7:  # break
            if domain == "physics":
                delta = -action.intensity * 0.3
            elif domain == "social":
                delta = -action.intensity * 0.2
        elif action_idx == 8:  # observe
            pass
        elif action_idx == 9:  # wait
            if domain == "physics":
                delta = random.uniform(-0.05, 0.05)
        elif action_idx == 10:  # communicate
            if domain == "social":
                delta = action.intensity * 0.1 * random.uniform(-0.5, 1.0)
        elif action_idx == 11:  # hide
            if domain == "social":
                delta = -action.intensity * 0.15
            if domain == "spatial":
                delta = random.uniform(-10, 10)

        lo, hi = VirtualWorldState.DIMENSIONS[domain][fname]
        new_state.features[feat_name] = max(lo, min(hi, current + delta))

    return new_state


class VirtualWorldDataset(Dataset):
    """Dataset d'expériences monde virtuel — pas de langage.

    Chaque échantillon: (état, action, état_suivant, conséquence).
    """

    def __init__(self, num_samples: int = 10000, seq_length: int = 32):
        self.num_samples = num_samples
        self.seq_length = seq_length
        self.state_dim = VirtualWorldState.num_features()
        self.action_dim = VirtualAction.num_features()
        self.samples = self._generate()

    def _generate(self) -> list[dict]:
        samples = []
        for _ in range(self.num_samples):
            state = VirtualWorldState(seed=random.randint(0, 2**31))
            trajectory = [state]
            for _ in range(self.seq_length):
                action = VirtualAction.random()
                next_state = apply_action(trajectory[-1], action)
                trajectory.append(next_state)

            state_seq = torch.stack([s.to_tensor() for s in trajectory[:-1]])
            next_state_seq = torch.stack([s.to_tensor() for s in trajectory[1:]])
            action_seq = torch.stack([
                VirtualAction.random().to_tensor() for _ in range(self.seq_length)
            ])
            consequence = next_state_seq - state_seq

            samples.append({
                "states": state_seq,
                "actions": action_seq,
                "next_states": next_state_seq,
                "consequences": consequence,
            })
        return samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        return self.samples[idx]


class CausalEncoding(nn.Module):
    """Encodeur causal — transforme (état, action) en prédiction de conséquence.

    Remplace l'embedding textuel lors de la Phase 00 (zéro langage).
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int):
        super().__init__()
        self.state_encoder = nn.Linear(state_dim, hidden_dim)
        self.action_encoder = nn.Linear(action_dim, hidden_dim)
        self.causal_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, state_dim),
        )

    def forward(self, states: torch.Tensor, actions: torch.Tensor) -> dict:
        s_enc = self.state_encoder(states)
        a_enc = self.action_encoder(actions)
        combined = torch.cat([s_enc, a_enc], dim=-1)
        predicted_delta = self.causal_predictor(combined)

        next_state_pred = states + predicted_delta
        return {
            "state_encoding": s_enc,
            "action_encoding": a_enc,
            "predicted_delta": predicted_delta,
            "predicted_next_state": next_state_pred,
        }
