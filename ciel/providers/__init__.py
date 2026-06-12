"""
CIEL v1.0 — Providers : fournisseurs de modèles LLM.

Composant CIEL natif — registre de fournisseurs LLM.
Architecture ProviderProfile :
  - ProviderProfile : description déclarative d'un provider
  - ProviderRegistry : découverte et résolution
  - Providers supportés : OpenAI, Anthropic, Google, DeepSeek, etc.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class ProviderProfile:
    """Profil déclaratif d'un fournisseur LLM."""
    name: str
    display_name: str
    description: str
    api_mode: str  # "chat_completions" | "anthropic_messages" | "gemini"
    base_url: str = ""
    auth_type: str = "api_key"  # "api_key" | "oauth" | "none"
    env_var: str = ""
    models: list[str] = field(default_factory=list)
    default_model: str = ""
    is_available: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name, "display_name": self.display_name,
            "description": self.description, "api_mode": self.api_mode,
            "base_url": self.base_url, "auth_type": self.auth_type,
            "models": self.models, "default_model": self.default_model,
            "is_available": self.is_available,
        }


# ── Providers intégrés ─────────────────────────────────

BUILTIN_PROVIDERS = {
    "openai": ProviderProfile(
        name="openai", display_name="OpenAI",
        description="GPT-4, GPT-4o, o1, o3",
        api_mode="chat_completions", base_url="https://api.openai.com/v1",
        env_var="OPENAI_API_KEY",
        models=["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
        default_model="gpt-4o",
    ),
    "anthropic": ProviderProfile(
        name="anthropic", display_name="Anthropic",
        description="Claude 3.5 Sonnet, Claude 3 Opus",
        api_mode="anthropic_messages", base_url="https://api.anthropic.com/v1",
        env_var="ANTHROPIC_API_KEY",
        models=["claude-3-5-sonnet-latest", "claude-3-opus-latest"],
        default_model="claude-3-5-sonnet-latest",
    ),
    "google": ProviderProfile(
        name="google", display_name="Google AI",
        description="Gemini 2.0 Flash, Gemini 2.0 Pro",
        api_mode="gemini", base_url="https://generativelanguage.googleapis.com/v1beta",
        env_var="GOOGLE_API_KEY",
        models=["gemini-2.0-flash", "gemini-2.0-pro"],
        default_model="gemini-2.0-flash",
    ),
    "deepseek": ProviderProfile(
        name="deepseek", display_name="DeepSeek",
        description="DeepSeek V3, DeepSeek R1",
        api_mode="chat_completions", base_url="https://api.deepseek.com/v1",
        env_var="DEEPSEEK_API_KEY",
        models=["deepseek-chat", "deepseek-reasoner"],
        default_model="deepseek-chat",
    ),
    "openrouter": ProviderProfile(
        name="openrouter", display_name="OpenRouter",
        description="200+ modèles via une API unifiée",
        api_mode="chat_completions", base_url="https://openrouter.ai/api/v1",
        env_var="OPENROUTER_API_KEY",
        models=["openrouter/auto"],
        default_model="openrouter/auto",
    ),
    "ollama": ProviderProfile(
        name="ollama", display_name="Ollama",
        description="Modèles locaux (Llama, Mistral, DeepSeek, Qwen, Phi)",
        api_mode="chat_completions", base_url="http://localhost:11434/v1/chat/completions",
        auth_type="none",
        models=["llama3.2", "llama3.1", "mistral", "qwen2.5", "phi3", "phi4", "deepseek-r1", "deepseek-coder", "codellama", "gemma2", "mixtral"],
        default_model="llama3.2",
    ),
    "llmstudio": ProviderProfile(
        name="llmstudio", display_name="LM Studio",
        description="Serveur local LM Studio (OpenAI-compatible)",
        api_mode="chat_completions", base_url="http://localhost:1234/v1",
        auth_type="none",
        models=["local-model"],
        default_model="local-model",
    ),
    "github": ProviderProfile(
        name="github", display_name="GitHub Models (Codex)",
        description="GPT-4o, GPT-4o-mini via GitHub Marketplace",
        api_mode="chat_completions", base_url="https://models.inference.ai.azure.com",
        env_var="GITHUB_TOKEN",
        models=["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
        default_model="gpt-4o",
    ),
    "kimi": ProviderProfile(
        name="kimi", display_name="Kimi K2 (Moonshot AI)",
        description="Kimi K2, Moonshot AI models",
        api_mode="chat_completions", base_url="https://api.moonshot.cn/v1",
        env_var="KIMI_API_KEY",
        models=["kimi-k2", "moonshot-v1"],
        default_model="kimi-k2",
    ),
    "groq": ProviderProfile(
        name="groq", display_name="Groq",
        description="Inférence ultra-rapide (Llama, Mixtral)",
        api_mode="chat_completions", base_url="https://api.groq.com/openai/v1",
        env_var="GROQ_API_KEY",
        models=["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        default_model="llama-3.3-70b-versatile",
    ),
    "together": ProviderProfile(
        name="together", display_name="Together AI",
        description="200+ modèles open-source",
        api_mode="chat_completions", base_url="https://api.together.xyz/v1",
        env_var="TOGETHER_API_KEY",
        models=["meta-llama/Llama-3.3-70B-Instruct-Turbo"],
        default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    ),
    "mistral": ProviderProfile(
        name="mistral", display_name="Mistral AI",
        description="Mistral Large, Mistral Small",
        api_mode="chat_completions", base_url="https://api.mistral.ai/v1",
        env_var="MISTRAL_API_KEY",
        models=["mistral-large-latest", "mistral-small-latest"],
        default_model="mistral-large-latest",
    ),
    "perplexity": ProviderProfile(
        name="perplexity", display_name="Perplexity AI",
        description="Sonar, Sonar Pro (recherche + chat)",
        api_mode="chat_completions", base_url="https://api.perplexity.ai",
        env_var="PERPLEXITY_API_KEY",
        models=["sonar", "sonar-pro"],
        default_model="sonar",
    ),
    "xai": ProviderProfile(
        name="xai", display_name="xAI (Grok)",
        description="Grok 2, Grok 3",
        api_mode="chat_completions", base_url="https://api.x.ai/v1",
        env_var="XAI_API_KEY",
        models=["grok-2", "grok-3"],
        default_model="grok-2",
    ),

    # ── 30 providers supplémentaires ──

    "fireworks": ProviderProfile(
        name="fireworks", display_name="Fireworks AI",
        description="Fast inference, open models (Llama, Qwen, DeepSeek)",
        api_mode="chat_completions", base_url="https://api.fireworks.ai/inference/v1",
        env_var="FIREWORKS_API_KEY",
        models=["accounts/fireworks/models/llama-v3p3-70b-instruct", "accounts/fireworks/models/qwen2p5-72b-instruct"],
        default_model="accounts/fireworks/models/llama-v3p3-70b-instruct",
    ),
    "replicate": ProviderProfile(
        name="replicate", display_name="Replicate",
        description="Run open-source models in the cloud",
        api_mode="chat_completions", base_url="https://api.replicate.com/v1",
        env_var="REPLICATE_API_TOKEN",
        models=["meta/meta-llama-3-70b-instruct", "mistralai/mistral-7b-instruct"],
        default_model="meta/meta-llama-3-70b-instruct",
    ),
    "cohere": ProviderProfile(
        name="cohere", display_name="Cohere",
        description="Command R+, Command R, Command A",
        api_mode="chat_completions", base_url="https://api.cohere.com/v1",
        env_var="COHERE_API_KEY",
        models=["command-r-plus", "command-r", "command-a"],
        default_model="command-r-plus",
    ),
    "ai21": ProviderProfile(
        name="ai21", display_name="AI21 Labs",
        description="Jurassic-2, Jamba",
        api_mode="chat_completions", base_url="https://api.ai21.com/studio/v1",
        env_var="AI21_API_KEY",
        models=["jamba-1.5-mini", "jamba-1.5-large", "jurassic-2-ultra"],
        default_model="jamba-1.5-large",
    ),
    "bedrock": ProviderProfile(
        name="bedrock", display_name="AWS Bedrock",
        description="Claude, Llama, Mistral via AWS",
        api_mode="chat_completions", base_url="https://bedrock-runtime.us-east-1.amazonaws.com",
        env_var="AWS_ACCESS_KEY_ID",
        models=["anthropic.claude-3-5-sonnet", "meta.llama3-70b", "mistral.mixtral-8x7b"],
        default_model="anthropic.claude-3-5-sonnet",
    ),
    "azure": ProviderProfile(
        name="azure", display_name="Azure OpenAI",
        description="GPT-4, GPT-4o via Microsoft Azure",
        api_mode="chat_completions", base_url="https://YOUR_RESOURCE.openai.azure.com",
        env_var="AZURE_OPENAI_KEY",
        models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        default_model="gpt-4o",
    ),
    "vertex": ProviderProfile(
        name="vertex", display_name="Google Vertex AI",
        description="Gemini, Claude via GCP",
        api_mode="chat_completions", base_url="https://us-central1-aiplatform.googleapis.com/v1",
        env_var="VERTEX_API_KEY",
        models=["gemini-2.0-flash", "gemini-2.0-pro", "claude-3-5-sonnet"],
        default_model="gemini-2.0-flash",
    ),
    "ibm": ProviderProfile(
        name="ibm", display_name="IBM watsonx",
        description="Llama, Granite, Mistral via IBM Cloud",
        api_mode="chat_completions", base_url="https://us-south.ml.cloud.ibm.com/ml/v1",
        env_var="IBM_API_KEY",
        models=["meta-llama/llama-3-70b", "ibm/granite-13b", "mistralai/mixtral-8x7b"],
        default_model="meta-llama/llama-3-70b",
    ),
    "nvidia": ProviderProfile(
        name="nvidia", display_name="NVIDIA NIM",
        description="Llama, Nemotron, Mistral sur GPU NVIDIA",
        api_mode="chat_completions", base_url="https://integrate.api.nvidia.com/v1",
        env_var="NVIDIA_API_KEY",
        models=["meta/llama3-70b", "nvidia/nemotron-4-340b", "mistralai/mixtral-8x22b"],
        default_model="meta/llama3-70b",
    ),
    "sambanova": ProviderProfile(
        name="sambanova", display_name="SambaNova",
        description="Llama, Qwen, DeepSeek sur accélérateurs SN40L",
        api_mode="chat_completions", base_url="https://api.sambanova.ai/v1",
        env_var="SAMBANOVA_API_KEY",
        models=["Meta-Llama-3.3-70B-Instruct", "Qwen2.5-72B-Instruct", "DeepSeek-R1-Distill-Llama-70B"],
        default_model="Meta-Llama-3.3-70B-Instruct",
    ),
    "cerebras": ProviderProfile(
        name="cerebras", display_name="Cerebras",
        description="Inférence ultra-rapide sur wafer-scale",
        api_mode="chat_completions", base_url="https://api.cerebras.ai/v1",
        env_var="CEREBRAS_API_KEY",
        models=["llama3.1-8b", "llama3.1-70b"],
        default_model="llama3.1-70b",
    ),
    "deepinfra": ProviderProfile(
        name="deepinfra", display_name="DeepInfra",
        description="Inference serverless, nombreux modèles open",
        api_mode="chat_completions", base_url="https://api.deepinfra.com/v1/openai",
        env_var="DEEPINFRA_API_KEY",
        models=["meta-llama/Llama-3.3-70B-Instruct", "mistralai/Mixtral-8x22B-Instruct"],
        default_model="meta-llama/Llama-3.3-70B-Instruct",
    ),
    "lepton": ProviderProfile(
        name="lepton", display_name="Lepton AI",
        description="Modèles open-source serverless",
        api_mode="chat_completions", base_url="https://api.lepton.ai/v1",
        env_var="LEPTON_API_KEY",
        models=["llama3-70b", "mixtral-8x7b", "qwen2-72b"],
        default_model="llama3-70b",
    ),
    "anyscale": ProviderProfile(
        name="anyscale", display_name="Anyscale",
        description="Llama, Mistral, Qwen sur Ray",
        api_mode="chat_completions", base_url="https://api.endpoints.anyscale.com/v1",
        env_var="ANYSCALE_API_KEY",
        models=["meta-llama/Llama-3.3-70B-Instruct", "mistralai/Mixtral-8x22B-Instruct"],
        default_model="meta-llama/Llama-3.3-70B-Instruct",
    ),
    "fal": ProviderProfile(
        name="fal", display_name="Fal AI",
        description="Modèles open-source et propriétaires",
        api_mode="chat_completions", base_url="https://fal.run/v1",
        env_var="FAL_API_KEY",
        models=["fal-llama-3.3-70b", "fal-mixtral-8x22b", "fal-qwen-2.5-72b"],
        default_model="fal-llama-3.3-70b",
    ),
    "writer": ProviderProfile(
        name="writer", display_name="Writer",
        description="Palmyra, LLM enterprise",
        api_mode="chat_completions", base_url="https://api.writer.com/v1",
        env_var="WRITER_API_KEY",
        models=["palmyra-x-128k", "palmyra-x-004"],
        default_model="palmyra-x-128k",
    ),
    "databricks": ProviderProfile(
        name="databricks", display_name="Databricks",
        description="DBRX, Llama via Databricks Serving",
        api_mode="chat_completions", base_url="https://serving.databricks.com/v1",
        env_var="DATABRICKS_TOKEN",
        models=["dbrx-instruct", "meta-llama/Llama-3.3-70B-Instruct"],
        default_model="dbrx-instruct",
    ),
    "upstage": ProviderProfile(
        name="upstage", display_name="Upstage",
        description="Solar LLM, modèles coréens",
        api_mode="chat_completions", base_url="https://api.upstage.ai/v1",
        env_var="UPSTAGE_API_KEY",
        models=["solar-1-mini", "solar-pro"],
        default_model="solar-pro",
    ),
    "yi": ProviderProfile(
        name="yi", display_name="01.AI (Yi)",
        description="Yi Lightning, Yi Large",
        api_mode="chat_completions", base_url="https://api.lingyiwanwu.com/v1",
        env_var="YI_API_KEY",
        models=["yi-lightning", "yi-large", "yi-vision"],
        default_model="yi-lightning",
    ),
    "zhipu": ProviderProfile(
        name="zhipu", display_name="Zhipu AI (GLM)",
        description="GLM-4, GLM-4V, CogView",
        api_mode="chat_completions", base_url="https://open.bigmodel.cn/api/paas/v4",
        env_var="ZHIPU_API_KEY",
        models=["glm-4-plus", "glm-4v-plus", "glm-4-air"],
        default_model="glm-4-plus",
    ),
    "baidu": ProviderProfile(
        name="baidu", display_name="Baidu (ERNIE)",
        description="ERNIE 4.0, ERNIE Speed",
        api_mode="chat_completions", base_url="https://aip.baidubce.com/rpc/2.0/ai_custom",
        env_var="BAIDU_API_KEY",
        models=["ernie-4.0", "ernie-speed", "ernie-lite"],
        default_model="ernie-4.0",
    ),
    "alibaba": ProviderProfile(
        name="alibaba", display_name="Alibaba Cloud (Qwen)",
        description="Qwen Max, Qwen Turbo, Qwen Long",
        api_mode="chat_completions", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        env_var="ALIBABA_API_KEY",
        models=["qwen-max", "qwen-turbo", "qwen-plus", "qwen-long"],
        default_model="qwen-max",
    ),
    "tencent": ProviderProfile(
        name="tencent", display_name="Tencent (Hunyuan)",
        description="Hunyuan Large, Hunyuan Turbo",
        api_mode="chat_completions", base_url="https://api.hunyuan.cloud.tencent.com/v1",
        env_var="TENCENT_API_KEY",
        models=["hunyuan-large", "hunyuan-turbo", "hunyuan-standard"],
        default_model="hunyuan-large",
    ),
    "bytedance": ProviderProfile(
        name="bytedance", display_name="ByteDance (Doubao)",
        description="Doubao Pro, Doubao Lite",
        api_mode="chat_completions", base_url="https://ark.cn-beijing.volces.com/api/v1",
        env_var="BYTEDANCE_API_KEY",
        models=["doubao-pro-32k", "doubao-lite-32k", "doubao-pro-128k"],
        default_model="doubao-pro-32k",
    ),
    "minimax": ProviderProfile(
        name="minimax", display_name="MiniMax (Hailuo AI)",
        description="MiniMax-Text, MiniMax-VL",
        api_mode="chat_completions", base_url="https://api.minimax.chat/v1",
        env_var="MINIMAX_API_KEY",
        models=["MiniMax-Text-01", "MiniMax-VL-01"],
        default_model="MiniMax-Text-01",
    ),
    "huggingface": ProviderProfile(
        name="huggingface", display_name="HuggingFace Inference",
        description="Inference API, 200k+ modèles communautaires",
        api_mode="chat_completions", base_url="https://api-inference.huggingface.co/v1",
        env_var="HUGGINGFACE_API_KEY",
        models=["meta-llama/Llama-3.1-70B-Instruct", "mistralai/Mixtral-8x7B-Instruct"],
        default_model="meta-llama/Llama-3.1-70B-Instruct",
    ),
    "jina": ProviderProfile(
        name="jina", display_name="Jina AI",
        description="Embeddings, Classifieur, Reader LLM",
        api_mode="chat_completions", base_url="https://api.jina.ai/v1",
        env_var="JINA_API_KEY",
        models=["jina-embeddings-v3", "jina-reranker-v2", "reader-lm"],
        default_model="jina-embeddings-v3",
    ),
    "voyage": ProviderProfile(
        name="voyage", display_name="Voyage AI",
        description="Embeddings et reranking spécialisés",
        api_mode="chat_completions", base_url="https://api.voyageai.com/v1",
        env_var="VOYAGE_API_KEY",
        models=["voyage-3", "voyage-3-lite", "voyage-code-3"],
        default_model="voyage-3",
    ),
    "mixedbread": ProviderProfile(
        name="mixedbread", display_name="Mixedbread AI",
        description="Embeddings et reranking open-source",
        api_mode="chat_completions", base_url="https://api.mixedbread.ai/v1",
        env_var="MIXEDBREAD_API_KEY",
        models=["mxbai-embed-large-v1", "mxbai-rerank-large-v1"],
        default_model="mxbai-embed-large-v1",
    ),
    "featherless": ProviderProfile(
        name="featherless", display_name="Featherless",
        description="Hébergement serverless de modèles ouverts",
        api_mode="chat_completions", base_url="https://api.featherless.ai/v1",
        env_var="FEATHERLESS_API_KEY",
        models=["Llama-3.3-70B-Instruct", "Qwen2.5-72B-Instruct", "DeepSeek-R1-Distill-Qwen-32B"],
        default_model="Llama-3.3-70B-Instruct",
    ),
}


class ProviderRegistry:
    """Registre des fournisseurs LLM CIEL."""

    def __init__(self):
        self._providers: dict[str, ProviderProfile] = {}
        self._api_keys: dict[str, str] = {}
        self._check_availability()

    def configure(self, api_keys: dict[str, str] | None = None) -> None:
        """Configure le registre avec les clés API depuis la config.

        À appeler après que la config soit chargée (build()).
        """
        if api_keys:
            self._api_keys = api_keys
        self._check_availability()

    def _check_availability(self) -> None:
        import os as _os
        for name, profile in BUILTIN_PROVIDERS.items():
            key_in_config = self._api_keys.get(name)
            key_in_env = _os.environ.get(profile.env_var) if profile.env_var else None
            profile.is_available = (
                not profile.env_var
                or bool(key_in_config)
                or key_in_env is not None
            )
            self._providers[name] = profile

    def get(self, name: str) -> ProviderProfile | None:
        return self._providers.get(name)

    def list(self, available_only: bool = False) -> list[ProviderProfile]:
        profiles = list(self._providers.values())
        if available_only:
            profiles = [p for p in profiles if p.is_available]
        return profiles

    def register(self, profile: ProviderProfile) -> None:
        self._providers[profile.name] = profile

    def get_default(self) -> ProviderProfile | None:
        for p in self._providers.values():
            if p.is_available:
                return p
        return self._providers.get("ollama") or next(iter(self._providers.values()), None)

    def get_model_provider(self, model: str) -> ProviderProfile | None:
        for p in self._providers.values():
            if model in p.models or p.default_model == model:
                return p
        return None


# Instance globale
_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = None
