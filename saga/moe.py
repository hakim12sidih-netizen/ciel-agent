from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class Router(nn.Module):
    """Routeur MoE avec top-k et équilibrage de charge."""

    def __init__(self, hidden_dim: int, num_experts: int, top_k: int = 2):
        super().__init__()
        self.gate = nn.Linear(hidden_dim, num_experts, bias=False)
        self.num_experts = num_experts
        self.top_k = top_k

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        logits = self.gate(x)
        weights = F.softmax(logits, dim=-1, dtype=torch.float32)
        top_k_weights, top_k_indices = torch.topk(weights, self.top_k, dim=-1)
        top_k_weights = top_k_weights / (top_k_weights.sum(dim=-1, keepdim=True) + 1e-8)
        return top_k_weights.to(x.dtype), top_k_indices, weights


class MoEDenseFFN(nn.Module):
    """FFN gérée (SwiGLU) pour un expert MoE."""

    def __init__(self, hidden_dim: int, expert_dim: int):
        super().__init__()
        self.gate_proj = nn.Linear(hidden_dim, expert_dim, bias=False)
        self.up_proj = nn.Linear(hidden_dim, expert_dim, bias=False)
        self.down_proj = nn.Linear(expert_dim, hidden_dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


class MoELayer(nn.Module):
    """Couche MoE complète avec routage et dispatch aux experts."""

    def __init__(self, config):
        super().__init__()
        self.hidden_dim = config.hidden_dim
        self.num_experts = config.num_experts
        self.top_k = config.top_k_experts
        self.expert_dim = config.expert_dim
        self.expert_types = config.expert_types

        self.router = Router(config.hidden_dim, config.num_experts, config.top_k)
        self.experts = nn.ModuleList([
            MoEDenseFFN(config.hidden_dim, config.expert_dim)
            for _ in range(config.num_experts)
        ])

    def forward(
        self,
        x: torch.Tensor,
        expert_type: Optional[str] = None,
    ) -> torch.Tensor:
        batch, seq_len, hidden = x.shape
        x_flat = x.view(-1, hidden)

        weights, indices, gate_scores = self.router(x_flat)

        output = torch.zeros_like(x_flat)
        for i in range(self.num_experts):
            mask = (indices == i).any(dim=-1)
            if mask.any():
                expert_out = self.experts[i](x_flat[mask])
                w = weights[mask][(indices[mask] == i).float().argmax(dim=-1)].unsqueeze(-1)
                output[mask] += expert_out * w

        if expert_type is not None:
            expert_mask = torch.tensor(
                [t == expert_type for t in self.expert_types],
                device=x.device, dtype=torch.bool,
            )
            forced_expert_idx = torch.where(expert_mask)[0]
            if len(forced_expert_idx) > 0:
                idx = forced_expert_idx[0]
                mask = torch.ones(x_flat.shape[0], dtype=torch.bool, device=x.device)
                output[mask] = output[mask] + self.experts[idx](x_flat[mask]) * 0.3

        aux_loss = self._load_balancing_loss(gate_scores, indices)
        return output.view(batch, seq_len, hidden), aux_loss

    def _load_balancing_loss(self, gate_scores: torch.Tensor, indices: torch.Tensor) -> torch.Tensor:
        """Perte d'équilibrage de charge entre experts."""
        counts = torch.zeros(self.num_experts, device=gate_scores.device)
        for i in range(self.num_experts):
            counts[i] = (indices == i).any(dim=-1).float().sum()
        importance = gate_scores.mean(dim=0)
        load = counts / (counts.sum() + 1e-8)
        return self.num_experts * (importance * load).sum()


class DenseFFN(nn.Module):
    """FFN dense (SwiGLU) standard."""

    def __init__(self, config):
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_dim, config.intermediate_dim, bias=False)
        self.up_proj = nn.Linear(config.hidden_dim, config.intermediate_dim, bias=False)
        self.down_proj = nn.Linear(config.intermediate_dim, config.hidden_dim, bias=False)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x)))
