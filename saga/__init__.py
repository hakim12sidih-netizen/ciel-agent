"""CIEL SAGA 1 — LLM 10B avec contexte 1M tokens."""
from __future__ import annotations

from ciel.saga.config import SagaConfig, ModelConfig, TrainingConfig, PhaseConfig

__all__ = ["SagaConfig", "ModelConfig", "TrainingConfig", "PhaseConfig"]

try:
    import torch  # noqa: F401
    from ciel.saga.model import SagaModel
    from ciel.saga.tokenizer import SagaTokenizer
    __all__ += ["SagaModel", "SagaTokenizer"]
except ImportError:
    pass
