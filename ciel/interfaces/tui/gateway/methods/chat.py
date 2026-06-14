"""
Chat method handler — bridges LLM streaming to the TUI.
Uses LLMBridgeEngine.chat_stream() — the actual CIEL streaming API.
"""

from typing import Any

from ciel.interfaces.tui.gateway.events.emitter import GatewayEventEmitter

_llm_bridge = None

def _get_bridge():
    global _llm_bridge
    if _llm_bridge is None:
        from ciel.llmbridge.core import LLMBridgeEngine
        _llm_bridge = LLMBridgeEngine()
    return _llm_bridge


class ChatMethods:

    def __init__(self, server):
        self.server = server
        self.emitter: GatewayEventEmitter = server.emitter

    def get_methods(self) -> dict[str, Any]:
        return {
            "chat.stream": self.handle_chat_stream,
        }

    async def handle_chat_stream(self, params: dict) -> dict | None:
        messages = params.get("messages", [])
        session_id = params.get("sessionId")
        stream = params.get("stream", True)

        if not messages:
            if stream:
                await self.emitter.chat_error("NO_MESSAGES", "No messages provided")
                return None
            return {"error": "No messages provided"}

        try:
            bridge = _get_bridge()
            full_content = ""

            if not session_id:
                session_id = bridge.create_session(
                    platform="tui",
                    title=f"TUI Chat {len(messages)} msgs",
                )

            if stream:
                await self.emitter.chat_delta("")

            async for chunk in bridge.chat_stream(
                messages=messages,
                temperature=params.get("temperature", 0.7),
                max_tokens=params.get("maxTokens", 4096),
            ):
                if not stream:
                    continue
                content = chunk.content
                if content:
                    full_content += content
                    await self.emitter.chat_delta(content)
                last_chunk = chunk

            if not stream:
                return {
                    "content": full_content,
                    "sessionId": session_id,
                }

            usage = last_chunk.usage if hasattr(last_chunk, "usage") else {"prompt_tokens": 0, "completion_tokens": 0}

            await self.emitter.chat_complete(
                message={
                    "role": "assistant",
                    "content": full_content,
                },
                session_id=session_id,
                usage={
                    "promptTokens": usage.get("prompt_tokens", 0),
                    "completionTokens": usage.get("completion_tokens", 0),
                    "totalTokens": usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0),
                },
            )
            return None

        except Exception as e:
            if stream:
                await self.emitter.chat_error("STREAM_ERROR", str(e))
                return None
            return {"error": str(e)}
