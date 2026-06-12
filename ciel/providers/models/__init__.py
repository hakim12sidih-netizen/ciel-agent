"""Métadonnées par modèle : fenêtre de contexte, prix, capacités."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class ModelInfo:
    name: str
    provider: str
    context_window: int = 4096
    max_output: int = 4096
    pricing_input: float = 0.0   # $/1M tokens
    pricing_output: float = 0.0
    capabilities: list[str] = field(default_factory=lambda: ["chat"])
    is_local: bool = False

MODEL_CATALOG: dict[str, ModelInfo] = {
    # OpenAI
    "gpt-4o":           ModelInfo("gpt-4o", "openai", 128000, 16384, 2.5, 10.0, ["chat","vision","tools"]),
    "gpt-4o-mini":      ModelInfo("gpt-4o-mini", "openai", 128000, 16384, 0.15, 0.6, ["chat","vision","tools"]),
    "o1":               ModelInfo("o1", "openai", 200000, 100000, 15.0, 60.0, ["chat","reasoning"]),
    "o3-mini":          ModelInfo("o3-mini", "openai", 200000, 100000, 1.1, 4.4, ["chat","reasoning"]),
    # Anthropic
    "claude-3-5-sonnet-latest": ModelInfo("claude-3-5-sonnet-latest", "anthropic", 200000, 8192, 3.0, 15.0, ["chat","vision"]),
    "claude-3-opus-latest":     ModelInfo("claude-3-opus-latest", "anthropic", 200000, 8192, 15.0, 75.0, ["chat","vision"]),
    # Google
    "gemini-2.0-flash": ModelInfo("gemini-2.0-flash", "google", 1048576, 8192, 0.1, 0.4, ["chat","vision","audio"]),
    "gemini-2.0-pro":   ModelInfo("gemini-2.0-pro", "google", 1048576, 8192, 0.5, 1.5, ["chat","vision","audio"]),
    # DeepSeek
    "deepseek-chat":    ModelInfo("deepseek-chat", "deepseek", 65536, 8192, 0.14, 0.28, ["chat"]),
    "deepseek-reasoner": ModelInfo("deepseek-reasoner", "deepseek", 65536, 8192, 0.55, 2.19, ["chat","reasoning"]),
    # Ollama (local)
    "phi3":             ModelInfo("phi3", "ollama", 4096, 2048, 0.0, 0.0, ["chat"], is_local=True),
    "llama3.2":         ModelInfo("llama3.2", "ollama", 8192, 4096, 0.0, 0.0, ["chat"], is_local=True),
    "mistral":          ModelInfo("mistral", "ollama", 8192, 4096, 0.0, 0.0, ["chat"], is_local=True),
    "qwen2.5":          ModelInfo("qwen2.5", "ollama", 32768, 8192, 0.0, 0.0, ["chat"], is_local=True),
    # Groq
    "llama-3.3-70b-versatile": ModelInfo("llama-3.3-70b-versatile", "groq", 131072, 8192, 0.59, 0.79, ["chat"]),
    "mixtral-8x7b-32768":      ModelInfo("mixtral-8x7b-32768", "groq", 32768, 4096, 0.24, 0.24, ["chat"]),
}

def get_model_info(model: str) -> ModelInfo | None:
    return MODEL_CATALOG.get(model)

def list_models(provider: str = "", local_only: bool = False) -> list[ModelInfo]:
    models = list(MODEL_CATALOG.values())
    if provider:
        models = [m for m in models if m.provider == provider]
    if local_only:
        models = [m for m in models if m.is_local]
    return sorted(models, key=lambda m: m.name)
