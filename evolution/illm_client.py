from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class LLMCompletionOptions:
    max_tokens: int = 4096
    temperature: float = 0.3
    system_prompt: str = ""
    stop_sequences: list[str] = field(default_factory=list)


class ILLMClient(Protocol):
    name: str

    async def complete(self, prompt: str, options: LLMCompletionOptions | None = None) -> str: ...

    async def is_available(self) -> bool: ...


@dataclass(slots=True)
class MockLLMClient:
    name: str = "mock"
    responses: list[tuple[re.Pattern | str, str]] = field(default_factory=list)
    call_log: list[dict[str, Any]] = field(default_factory=list)
    fail_queue: list[str] = field(default_factory=list)

    def on_prompt(self, match: str | re.Pattern, text: str) -> MockLLMClient:
        if isinstance(match, str):
            self.responses.append((re.compile(re.escape(match)), text))
        else:
            self.responses.append((match, text))
        return self

    def fail_once(self, message: str = "mock LLM error") -> MockLLMClient:
        self.fail_queue.append(message)
        return self

    async def complete(self, prompt: str, options: LLMCompletionOptions | None = None) -> str:
        self.call_log.append({"prompt": prompt, "options": options})
        if self.fail_queue:
            msg = self.fail_queue.pop(0)
            raise RuntimeError(msg)
        for pattern, response in self.responses:
            if pattern.search(prompt):
                return response
        return "// no mock response configured"

    async def is_available(self) -> bool:
        return True

    def get_calls(self) -> list[dict[str, Any]]:
        return list(self.call_log)


def process(input_data: Any) -> dict[str, Any]:
    return {"client": "ILLMClient", "available": True}
