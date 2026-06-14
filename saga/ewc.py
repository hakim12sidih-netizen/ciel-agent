"""Elastic Weight Consolidation (EWC) — Anti-oubli catastrophique."""
from __future__ import annotations

import torch
import torch.nn as nn


class EWC:
    """Elastic Weight Consolidation.

    Protège les poids critiques contre les changements lors de nouvelles phases.
    Stocke l'importance de chaque paramètre (diag. Fisher) et pénalise les écarts.
    """

    def __init__(self, model: nn.Module, alpha: float = 0.5):
        self.model = model
        self.alpha = alpha
        self.params: dict[str, torch.Tensor] = {}
        self.fisher: dict[str, torch.Tensor] = {}
        self._frozen_params: dict[str, torch.Tensor] = {}

    def snapshot(self):
        """Capture l'état actuel des paramètres comme référence EWC."""
        self.params = {}
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.params[name] = param.data.clone().detach()

    def estimate_fisher(self, loader, num_samples: int = 200, device: str = "cuda"):
        """Estime la diagonale de Fisher sur un échantillon des données."""
        self.fisher = {}
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.fisher[name] = torch.zeros_like(param.data)

        self.model.train()
        count = 0
        for batch in loader:
            if count >= num_samples:
                break
            input_ids = batch["input_ids"].to(device)
            self.model.zero_grad()
            out = self.model(input_ids, return_logits=True)
            logits = out["logits"]
            loss = nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)),
                input_ids.view(-1),
                ignore_index=1,
            )
            loss.backward()
            for name, param in self.model.named_parameters():
                if param.requires_grad and param.grad is not None:
                    self.fisher[name] += param.grad.data.pow(2)
            count += input_ids.size(0)

        for name in self.fisher:
            self.fisher[name] /= max(count, 1)

    def consolidation_loss(self) -> torch.Tensor:
        """Calcule la perte EWC : pénalise les déviations des poids importants."""
        loss = 0.0
        for name, param in self.model.named_parameters():
            if name in self.params and name in self.fisher and param.requires_grad:
                diff = param.data - self.params[name]
                loss += (self.fisher[name] * diff.pow(2)).sum()
        return loss * self.alpha

    def freeze_critical(self, threshold: float = 0.9):
        """Gèle les poids les plus importants (top percentile Fisher)."""
        all_fisher = torch.cat([f.view(-1) for f in self.fisher.values()])
        cutoff = torch.quantile(all_fisher, threshold)
        for name, param in self.model.named_parameters():
            if name in self.fisher and param.requires_grad:
                if self.fisher[name].mean() > cutoff:
                    param.requires_grad = False
                    self._frozen_params[name] = param.data.clone()

    def unfreeze_all(self):
        """Dégèle tous les paramètres."""
        for name, param in self.model.named_parameters():
            param.requires_grad = True
        self._frozen_params = {}


class ProgressiveNetwork:
    """Progressive Neural Network — nouveau palier = nouvelle colonne.

    Permet l'ajout de nouvelles capacités sans écraser les anciennes.
    Chaque colonne est un sous-réseau lateral connecté aux précédentes.
    """

    def __init__(self, hidden_dim: int):
        self.columns: list[nn.Module] = []
        self.hidden_dim = hidden_dim

    def add_column(self, model: nn.Module, freeze_previous: bool = True):
        """Ajoute une colonne (phase)."""
        col_id = len(self.columns)
        self.columns.append(model)
        if freeze_previous:
            for i, col in enumerate(self.columns):
                if i < col_id:
                    for p in col.parameters():
                        p.requires_grad = False

    def lateral_connections(self, x: torch.Tensor, active_column: int) -> torch.Tensor:
        """Connexions latérales entre colonnes précédentes et active."""
        lateral = 0
        for i in range(active_column):
            lateral += self.columns[i](x) * (0.5 ** (active_column - i))
        return lateral
