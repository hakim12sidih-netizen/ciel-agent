"""CIEL SAGA 1 — Architecture complète 10B MoE avec contexte 1M."""
from __future__ import annotations

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple

from ciel.saga.config import ModelConfig
from ciel.saga.attention import GroupedAttention, yarn_rope
from ciel.saga.moe import MoELayer, DenseFFN


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-5):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        rms = x.pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return x * rms * self.weight


class TransformerBlock(nn.Module):
    """Bloc transformer : attention GQA + FFN (dense ou MoE)."""

    def __init__(self, config: ModelConfig, layer_idx: int, use_moe: bool = False):
        super().__init__()
        self.use_moe = use_moe
        self.attention = GroupedAttention(config)
        self.attn_norm = RMSNorm(config.hidden_dim, config.norm_eps)

        if use_moe:
            self.ffn = MoELayer(config)
        else:
            self.ffn = DenseFFN(config)
        self.ffn_norm = RMSNorm(config.hidden_dim, config.norm_eps)

    def forward(
        self,
        x: torch.Tensor,
        position_ids: torch.LongTensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        expert_type: Optional[str] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        residual = x
        x = self.attn_norm(x)
        x = self.attention(x, position_ids, cos, sin, mask)
        x = residual + x

        residual = x
        x = self.ffn_norm(x)
        if self.use_moe:
            x, aux_loss = self.ffn(x, expert_type)
        else:
            x = self.ffn(x)
            aux_loss = torch.tensor(0.0, device=x.device)
        x = residual + x
        return x, aux_loss


class SagaModel(nn.Module):
    """CIEL SAGA 1 — 10B paramètres, 1M contexte, 5 types d'experts."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_dim, padding_idx=0)
        self.layers = nn.ModuleList([
            TransformerBlock(config, i, use_moe=(i in config.moe_layers))
            for i in range(config.num_layers)
        ])
        self.norm = RMSNorm(config.hidden_dim, config.norm_eps)
        self.lm_head = nn.Linear(config.hidden_dim, config.vocab_size, bias=False)

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, (nn.Linear, nn.Embedding)):
                module.weight.data.normal_(mean=0.0, std=self.config.weight_init_std)
                if isinstance(module, nn.Linear) and module.bias is not None:
                    module.bias.data.zero_()

    def _prepare_cos_sin(
        self,
        position_ids: torch.LongTensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        return yarn_rope(
            None, position_ids,
            theta=self.config.rope_theta,
            scaling_factor=self.config.rope_scaling.get("factor", 32.0),
            original_max_seq=self.config.rope_scaling.get("original_max_seq_len", 8192),
            head_dim=self.config.head_dim,
        )

    def _create_causal_mask(
        self,
        seq_len: int,
        kv_len: int,
        device: torch.device,
    ) -> torch.Tensor:
        if seq_len <= 131072:
            mask = torch.tril(torch.ones((seq_len, kv_len), device=device))
            mask = mask.view(1, 1, seq_len, kv_len)
            return mask
        return None

    def forward(
        self,
        input_ids: torch.LongTensor,
        attention_mask: Optional[torch.Tensor] = None,
        expert_types: Optional[list[Optional[str]]] = None,
        return_logits: bool = True,
    ) -> dict:
        batch, seq_len = input_ids.shape
        device = input_ids.device

        h = self.embed_tokens(input_ids)
        position_ids = torch.arange(seq_len, device=device).unsqueeze(0).expand(batch, -1)
        cos, sin = self._prepare_cos_sin(position_ids)
        mask = self._create_causal_mask(seq_len, seq_len, device)

        total_aux_loss = 0.0
        for i, layer in enumerate(self.layers):
            expert_type = None
            if expert_types and i < len(expert_types):
                expert_type = expert_types[i]
            h, aux_loss = layer(h, position_ids, cos, sin, mask, expert_type)
            total_aux_loss = total_aux_loss + aux_loss

        h = self.norm(h)

        logits = self.lm_head(h) if return_logits else None
        return {
            "logits": logits,
            "hidden_states": h,
            "aux_loss": total_aux_loss,
        }

    def generate(
        self,
        input_ids: torch.LongTensor,
        max_new_tokens: int = 180_000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        eos_token_id: int = 2,
        streaming: bool = False,
    ) -> torch.LongTensor:
        self.eval()
        batch = input_ids.shape[0]
        device = input_ids.device
        max_gen = min(max_new_tokens, self.config.max_output_len)

        past = []
        for pos in range(max_gen):
            if input_ids.shape[1] > self.config.max_seq_len:
                input_ids = input_ids[:, -self.config.max_seq_len:]

            with torch.no_grad():
                out = self(input_ids, expert_types=None, return_logits=True)

            logits = out["logits"][:, -1, :]
            logits = logits / temperature

            if repetition_penalty != 1.0:
                for b in range(batch):
                    for token in input_ids[b].unique():
                        logits[b, token] /= repetition_penalty

            if top_k > 0:
                vals, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < vals[:, -1:]] = float('-inf')

            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                cum_probs = sorted_logits.softmax(dim=-1).cumsum(dim=-1)
                sorted_indices_to_remove = cum_probs > top_p
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = 0
                indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                logits[indices_to_remove] = float('-inf')

            probs = F.softmax(logits, dim=-1)
            next_tokens = torch.multinomial(probs, num_samples=1)
            input_ids = torch.cat([input_ids, next_tokens], dim=-1)

            if (next_tokens == eos_token_id).any():
                break

        return input_ids

    def get_param_count(self) -> dict:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {
            "total": total,
            "trainable": trainable,
            "total_m": total / 1_000_000,
            "trainable_m": trainable / 1_000_000,
            "total_b": total / 1e9,
        }

    def get_memory_estimate(self) -> dict:
        params = sum(p.numel() for p in self.parameters())
        fp32_bytes = params * 4 / (1024**3)
        bf16_bytes = params * 2 / (1024**3)
        return {
            "fp32_gb": round(fp32_bytes, 2),
            "bf16_gb": round(bf16_bytes, 2),
            "optimizer_states_gb": round(fp32_bytes * 3, 2),
            "total_bf16_estimate_gb": round(bf16_bytes * 4, 2),
        }
