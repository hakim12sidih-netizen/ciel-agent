from __future__ import annotations

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


def yarn_rope(
    x: torch.Tensor,
    position_ids: torch.LongTensor,
    theta: float = 1000000.0,
    scaling_factor: float = 32.0,
    original_max_seq: int = 8192,
    head_dim: int = 128,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """YaRN (Yet another RoPE extensioN) avec scaling de longueur."""
    batch_size, seq_len = position_ids.shape
    freqs = 1.0 / (theta ** (torch.arange(0, head_dim, 2, device=x.device, dtype=x.dtype) / head_dim))
    positions = position_ids.float()

    t = positions.unsqueeze(-1) * freqs.unsqueeze(0)
    cos = t.cos() * scaling_factor
    sin = t.sin() * scaling_factor
    return cos, sin


def apply_rotary_emb(
    x: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
) -> torch.Tensor:
    """Applique RoPE à un tenseur x de forme (batch, heads, seq, dim)."""
    half = x.shape[-1] // 2
    x_reshaped = x.float().reshape(*x.shape[:-1], -1, 2)
    x_rot = torch.stack([-x_reshaped[..., 1], x_reshaped[..., 0]], dim=-1).reshape_as(x)
    cos = cos.unsqueeze(1).unsqueeze(1)
    sin = sin.unsqueeze(1).unsqueeze(1)
    return (x * cos + x_rot * sin).to(x.dtype)


class RingAttention(nn.Module):
    """Attention avec prise en charge de Ring Attention pour contexte 1M.

    Distribue les segments de séquence entre plusieurs devices.
    """
    def __init__(self, config):
        super().__init__()
        self.hidden_dim = config.hidden_dim
        self.num_heads = config.num_heads
        self.num_kv_heads = config.num_kv_heads
        self.head_dim = config.head_dim
        self.num_groups = self.num_heads // self.num_kv_heads
        self.ring_size = config.ring_attn_size

    def forward(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        batch, q_seq, _, _ = q.shape
        kv_seq = k.shape[2]

        scale = self.head_dim ** -0.5
        q = q * scale

        if kv_seq <= 65536 or not self.ring_size > 1:
            attn = torch.matmul(q, k.transpose(-2, -1))
            if mask is not None:
                attn = attn.masked_fill(mask == 0, float('-inf'))
            attn = F.softmax(attn, dim=-1, dtype=torch.float32).to(q.dtype)
            return torch.matmul(attn, v)
        else:
            return self._ring_attn(q, k, v, mask, batch, q_seq, kv_seq)

    def _ring_attn(self, q, k, v, mask, batch, q_seq, kv_seq):
        segment_size = kv_seq // self.ring_size
        output_chunks = []
        for i in range(0, kv_seq, segment_size):
            k_seg = k[:, :, i:i + segment_size]
            v_seg = v[:, :, i:i + segment_size]
            attn = torch.matmul(q, k_seg.transpose(-2, -1))
            if mask is not None:
                mask_seg = mask[:, :, :, i:i + segment_size]
                attn = attn.masked_fill(mask_seg == 0, float('-inf'))
            attn = F.softmax(attn, dim=-1, dtype=torch.float32).to(q.dtype)
            out = torch.matmul(attn, v_seg)
            output_chunks.append(out)
        return sum(output_chunks)


class GroupedAttention(nn.Module):
    """Attention GQA (Grouped Query Attention) avec Flash/Ring Attention."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.hidden_dim = config.hidden_dim
        self.num_heads = config.num_heads
        self.num_kv_heads = config.num_kv_heads
        self.head_dim = config.head_dim
        self.num_groups = self.num_heads // self.num_kv_heads

        self.q_proj = nn.Linear(self.hidden_dim, self.num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(self.hidden_dim, self.num_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(self.hidden_dim, self.num_kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_dim, bias=False)

        self.ring_attn = RingAttention(config)

    def forward(
        self,
        x: torch.Tensor,
        position_ids: torch.LongTensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        batch, seq_len, _ = x.shape

        q = self.q_proj(x).view(batch, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)

        q = apply_rotary_emb(q, cos, sin)
        k = apply_rotary_emb(k, cos, sin)

        if self.num_groups > 1:
            k = k.repeat_interleave(self.num_groups, dim=1)
            v = v.repeat_interleave(self.num_groups, dim=1)

        attn_out = self.ring_attn(q, k, v, mask)

        attn_out = attn_out.transpose(1, 2).contiguous().view(batch, seq_len, -1)
        return self.o_proj(attn_out)
