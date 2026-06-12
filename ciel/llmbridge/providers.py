from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0})
    finish_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class Message:
    role: str  # "system", "user", "assistant"
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class ProviderBase(ABC):
    def __init__(self, model: str, api_key: str = "", base_url: str = "") -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse:
        ...


class OpenAIProvider(ProviderBase):
    """OpenAI-compatible API provider (OpenAI, Groq, etc.)."""

    def __init__(self, model: str, api_key: str = "", base_url: str = "",
                 provider_name: str = "openai") -> None:
        super().__init__(model, api_key, base_url)
        self.provider_name = provider_name

    async def chat_completion(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse:
        import aiohttp
        url = self.base_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"API error {resp.status}: {text}")
                result = await resp.json()
                choice = result["choices"][0]
                return LLMResponse(
                    content=choice["message"]["content"],
                    model=result.get("model", self.model),
                    provider=self.provider_name,
                    usage=result.get("usage", {}),
                    finish_reason=choice.get("finish_reason", ""),
                )


class AnthropicProvider(ProviderBase):
    """Anthropic API provider (Claude models)."""

    def __init__(self, model: str, api_key: str = "", base_url: str = "",
                 provider_name: str = "anthropic") -> None:
        super().__init__(model, api_key, base_url)
        self.provider_name = provider_name

    async def chat_completion(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse:
        import aiohttp
        url = self.base_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        system = ""
        filtered: list[dict[str, str]] = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                filtered.append({"role": m.role, "content": m.content})

        data: dict[str, Any] = {
            "model": self.model,
            "messages": filtered,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            data["system"] = system

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Anthropic error {resp.status}: {text}")
                result = await resp.json()
                content = ""
                for block in result.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                usage = result.get("usage", {})
                return LLMResponse(
                    content=content,
                    model=result.get("model", self.model),
                    provider=self.provider_name,
                    usage={"prompt_tokens": usage.get("input_tokens", 0), "completion_tokens": usage.get("output_tokens", 0)},
                    finish_reason=result.get("stop_reason", ""),
                )


class GeminiProvider(ProviderBase):
    """Google Gemini API provider."""

    def __init__(self, model: str, api_key: str = "", base_url: str = "",
                 provider_name: str = "google") -> None:
        super().__init__(model, api_key, base_url)
        self.provider_name = provider_name

    async def chat_completion(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse:
        import aiohttp
        url = self.base_url or f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        gemini_contents: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "system":
                continue
            role = "model" if m.role == "assistant" else "user"
            gemini_contents.append({"role": role, "parts": [{"text": m.content}]})
        data = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Gemini error {resp.status}: {text}")
                result = await resp.json()
                candidate = result.get("candidates", [{}])[0]
                content_parts = candidate.get("content", {}).get("parts", [])
                content = "".join(p.get("text", "") for p in content_parts)
                return LLMResponse(
                    content=content,
                    model=self.model,
                    provider=self.provider_name,
                    usage={},
                    finish_reason=candidate.get("finishReason", ""),
                )
