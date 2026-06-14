"""
CIEL v∞.9 — AOP Middleware Pipeline for Plugin Hooks.
before/after/around/on_error interceptors with chaining.
"""
from __future__ import annotations

import time
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable


__all__ = [
    "MiddlewarePipeline", "Middleware", "MiddlewareResult",
    "MiddlewareError",
]


class MiddlewareError(Exception):
    pass


@dataclass
class MiddlewareResult:
    success: bool = True
    context: dict | None = None
    result: Any = None
    error: str = ""
    duration_ms: float = 0.0


@dataclass
class Middleware:
    name: str
    plugin: str
    hook_name: str
    priority: int = 0
    enabled: bool = True

    async def before(self, context: dict) -> dict:
        return context

    async def after(self, context: dict, result: Any) -> Any:
        return result

    async def around(self, context: dict, next_hook: Callable[..., Awaitable[Any]]) -> Any:
        return await next_hook(context)

    async def on_error(self, context: dict, error: Exception) -> Any:
        raise error


class _MiddlewareChain:
    def __init__(self, middlewares: list[MiddlewareRegistry.Entry],
                 hook_fn: Callable[..., Awaitable[Any]]):
        self._middlewares = middlewares
        self._hook_fn = hook_fn

    async def execute(self, context: dict | None = None) -> Any:
        ctx = context or {}
        middleware_iter = iter(self._middlewares)

        async def chain(idx: int, ctx: dict) -> Any:
            if idx < len(self._middlewares):
                mw = self._middlewares[idx]
                try:
                    mw_instance = mw.instance
                    ctx = await mw_instance.before(ctx) if hasattr(mw_instance, 'before') else ctx

                    async def next_hook(c: dict) -> Any:
                        return await chain(idx + 1, c)

                    if hasattr(mw_instance, 'around'):
                        result = await mw_instance.around(ctx, next_hook)
                    else:
                        result = await next_hook(ctx)

                    result = await mw_instance.after(ctx, result) if hasattr(mw_instance, 'after') else result
                    return result
                except Exception as e:
                    if hasattr(mw_instance, 'on_error'):
                        return await mw_instance.on_error(ctx, e)
                    raise
            else:
                return await self._hook_fn(ctx)

        return await chain(0, ctx)


class MiddlewareRegistry:
    @dataclass
    class Entry:
        middleware: Middleware
        instance: Any
        plugin: str
        hook_name: str
        priority: int

    def __init__(self):
        self._entries: list[MiddlewareRegistry.Entry] = []
        self._global_middlewares: list[MiddlewareRegistry.Entry] = []

    def register(self, middleware: Middleware, instance: Any):
        entry = MiddlewareRegistry.Entry(
            middleware=middleware,
            instance=instance,
            plugin=middleware.plugin,
            hook_name=middleware.hook_name,
            priority=middleware.priority,
        )
        if middleware.hook_name == "*":
            self._global_middlewares.append(entry)
            self._global_middlewares.sort(key=lambda e: e.priority)
        else:
            self._entries.append(entry)
            self._entries.sort(key=lambda e: e.priority)

    def unregister(self, plugin: str, hook_name: str | None = None):
        def _filter(e: MiddlewareRegistry.Entry) -> bool:
            if e.plugin != plugin:
                return True
            if hook_name and e.hook_name != hook_name:
                return True
            return False
        self._entries = [e for e in self._entries if _filter(e)]
        self._global_middlewares = [e for e in self._global_middlewares if _filter(e)]

    def get_chain(self, hook_name: str,
                  hook_fn: Callable[..., Awaitable[Any]]) -> _MiddlewareChain:
        matching = [e for e in self._entries if e.hook_name == hook_name or e.hook_name == "*"]
        global_mw = list(self._global_middlewares)
        combined = sorted(global_mw + matching, key=lambda e: e.priority)
        return _MiddlewareChain(combined, hook_fn)

    def list(self) -> list[dict]:
        result = []
        for e in self._entries:
            result.append({
                "name": e.middleware.name,
                "plugin": e.plugin,
                "hook": e.hook_name,
                "priority": e.priority,
            })
        return result


class MiddlewarePipeline:
    def __init__(self):
        self.registry = MiddlewareRegistry()
        self._stats: dict[str, list[float]] = {}

    def register(self, middleware: Middleware, instance: Any):
        self.registry.register(middleware, instance)

    def unregister(self, plugin: str, hook_name: str | None = None):
        self.registry.unregister(plugin, hook_name)

    def wrap_hook(self, hook_name: str,
                  hook_fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        chain = self.registry.get_chain(hook_name, hook_fn)

        async def wrapped(context: dict | None = None) -> Any:
            start = time.time()
            try:
                result = await chain.execute(context)
                return result
            finally:
                elapsed = (time.time() - start) * 1000
                if hook_name not in self._stats:
                    self._stats[hook_name] = []
                self._stats[hook_name].append(elapsed)
                if len(self._stats[hook_name]) > 1000:
                    self._stats[hook_name] = self._stats[hook_name][-1000:]

        return wrapped

    def get_stats(self, hook_name: str | None = None) -> dict:
        if hook_name:
            times = self._stats.get(hook_name, [])
            return {
                "hook": hook_name,
                "count": len(times),
                "avg_ms": sum(times) / len(times) if times else 0,
                "max_ms": max(times) if times else 0,
                "min_ms": min(times) if times else 0,
            }
        return {
            hook: self.get_stats(hook)
            for hook in self._stats
        }

    def list_middlewares(self) -> list[dict]:
        return self.registry.list()
