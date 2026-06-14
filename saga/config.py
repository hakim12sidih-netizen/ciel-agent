from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    vocab_size: int = 65536
    hidden_dim: int = 4096
    intermediate_dim: int = 11008
    num_layers: int = 32
    num_heads: int = 32
    num_kv_heads: int = 8
    max_seq_len: int = 1_000_000
    max_output_len: int = 180_000
    moe_layers: list[int] = field(default_factory=lambda: [i for i in range(32) if i % 2 == 1])
    num_experts: int = 8
    top_k_experts: int = 2
    expert_dim: int = 4096
    expert_types: list[str] = field(default_factory=lambda: ["reason", "create", "verify", "remember", "act", "reason", "create", "verify"])
    rope_theta: float = 1000000.0
    rope_scaling: dict = field(default_factory=lambda: {
        "type": "yarn",
        "factor": 32.0,
        "original_max_seq_len": 8192,
    })
    dropout: float = 0.0
    activation: str = "silu"
    norm_eps: float = 1e-5
    weight_init_std: float = 0.02
    use_flash_attn: bool = True
    use_ring_attn: bool = True
    ring_attn_size: int = 4
    use_checkpointing: bool = True
    gradient_ckpt_layers: int = 4

    @property
    def num_dense_layers(self) -> int:
        return self.num_layers - len(self.moe_layers)

    @property
    def num_moe_layers(self) -> int:
        return len(self.moe_layers)

    @property
    def head_dim(self) -> int:
        return self.hidden_dim // self.num_heads

    @property
    def total_params_est(self) -> dict:
        emb = self.vocab_size * self.hidden_dim
        attn_per_layer = 4 * self.hidden_dim * self.hidden_dim // self.num_heads * (self.num_heads + 2 * self.num_kv_heads) // 3
        dense_ffn = 3 * self.hidden_dim * self.intermediate_dim
        per_dense = attn_per_layer + dense_ffn
        moe_experts = self.num_experts * 3 * self.hidden_dim * self.expert_dim
        per_moe = attn_per_layer + moe_experts
        dense_total = per_dense * self.num_dense_layers
        moe_total = per_moe * self.num_moe_layers
        total = emb + dense_total + moe_total
        return {
            "embedding": emb // 1_000_000,
            "dense_layers": dense_total // 1_000_000,
            "moe_layers": moe_total // 1_000_000,
            "total_m": total // 1_000_000,
            "total_b": round(total / 1e9, 2),
        }


@dataclass
class PhaseConfig:
    name: str
    learning_rate: float
    batch_size: int
    grad_accum: int
    epochs: int
    warmup_steps: int
    weight_decay: float
    beta1: float = 0.9
    beta2: float = 0.95
    eps: float = 1e-8
    max_grad_norm: float = 1.0
    scheduler: str = "cosine"
    min_lr: float = 0.0


@dataclass
class TrainingConfig:
    output_dir: str = "/home/sidi/.ciel/saga1"
    deepspeed_config: str = "ds_config.json"
    seed: int = 42
    save_every: int = 1000
    eval_every: int = 100
    log_every: int = 10
    max_checkpoints: int = 5
    resume_from: Optional[str] = None
    compile: bool = True
    mixed_precision: str = "bf16"
    zero_stage: int = 3
    offload: bool = False

    phases: list[PhaseConfig] = field(default_factory=lambda: [
        PhaseConfig(name="phase00_anchoring", lr=3e-4, batch_size=8, grad_accum=64, epochs=1, warmup_steps=1000, weight_decay=0.1),
        PhaseConfig(name="phase01_pretrain_universal", lr=3e-4, batch_size=8, grad_accum=64, epochs=3, warmup_steps=2000, weight_decay=0.1),
        PhaseConfig(name="phase02_pretrain_moe", lr=2e-4, batch_size=8, grad_accum=64, epochs=2, warmup_steps=1000, weight_decay=0.1),
        PhaseConfig(name="phase03_sft", lr=1e-5, batch_size=4, grad_accum=32, epochs=2, warmup_steps=200, weight_decay=0.05),
        PhaseConfig(name="phase04_socratic", lr=5e-6, batch_size=2, grad_accum=64, epochs=1, warmup_steps=100, weight_decay=0.01),
        PhaseConfig(name="phase05_rl_preferences", lr=3e-6, batch_size=2, grad_accum=64, epochs=2, warmup_steps=100, weight_decay=0.01),
        PhaseConfig(name="phase06_rl_reasoning", lr=1e-6, batch_size=1, grad_accum=128, epochs=2, warmup_steps=100, weight_decay=0.01),
        PhaseConfig(name="phase07_consolidation", lr=5e-7, batch_size=4, grad_accum=32, epochs=1, warmup_steps=50, weight_decay=0.001),
        PhaseConfig(name="phase08_agentic", lr=3e-6, batch_size=2, grad_accum=64, epochs=2, warmup_steps=100, weight_decay=0.01),
        PhaseConfig(name="phase09_ethics", lr=1e-6, batch_size=2, grad_accum=64, epochs=1, warmup_steps=50, weight_decay=0.005),
        PhaseConfig(name="phase10_validation", lr=1e-7, batch_size=1, grad_accum=128, epochs=1, warmup_steps=0, weight_decay=0.0),
        PhaseConfig(name="phase11_deployment", lr=1e-7, batch_size=2, grad_accum=32, epochs=3, warmup_steps=50, weight_decay=0.001),
    ])


@dataclass
class SagaConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    use_cuda: bool = True
    device: str = "cuda"
    num_gpus: int = 1
    world_size: int = 1
    master_addr: str = "127.0.0.1"
    master_port: int = 29500
