from __future__ import annotations

import asyncio
import re

import pytest

from ciel.evolution.illm_client import ILLMClient, MockLLMClient, LLMCompletionOptions, process


class TestLLMCompletionOptions:
    def test_create(self):
        opts = LLMCompletionOptions(max_tokens=1024, temperature=0.7)
        assert opts.max_tokens == 1024
        assert opts.temperature == 0.7

    def test_defaults(self):
        opts = LLMCompletionOptions()
        assert opts.max_tokens == 4096
        assert opts.temperature == 0.3


class TestMockLLMClient:
    def test_instantiate(self):
        client = MockLLMClient()
        assert client.name == "mock"

    def test_on_prompt_string(self):
        client = MockLLMClient()
        client.on_prompt("hello", "world")
        assert len(client.responses) == 1

    def test_on_prompt_regex(self):
        client = MockLLMClient()
        client.on_prompt(re.compile(r"test"), "response")
        assert len(client.responses) == 1

    def test_complete(self):
        async def _test():
            client = MockLLMClient()
            client.on_prompt("hello", "world")
            result = await client.complete("hello")
            assert result == "world"
        asyncio.run(_test())

    def test_complete_no_match(self):
        async def _test():
            client = MockLLMClient()
            result = await client.complete("anything")
            assert result == "// no mock response configured"
        asyncio.run(_test())

    def test_is_available(self):
        async def _test():
            client = MockLLMClient()
            assert await client.is_available() is True
        asyncio.run(_test())

    def test_fail_once(self):
        async def _test():
            client = MockLLMClient()
            client.fail_once("error msg")
            with pytest.raises(RuntimeError, match="error msg"):
                await client.complete("x")
        asyncio.run(_test())

    def test_get_calls(self):
        async def _test():
            client = MockLLMClient()
            client.on_prompt("hi", "there")
            await client.complete("hi")
            calls = client.get_calls()
            assert len(calls) == 1
            assert calls[0]["prompt"] == "hi"
        asyncio.run(_test())

    def test_process_state(self):
        r = process({"action": "state"})
        assert r["client"] == "ILLMClient"
        assert r["available"] is True

    def test_process_bad_input(self):
        r = process("bad")
        assert r["client"] == "ILLMClient"

    def test_process_unknown_action(self):
        r = process({"action": "nonexistent"})
        assert r["client"] == "ILLMClient"
