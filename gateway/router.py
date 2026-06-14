from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Route:
    id: str
    pattern: str
    target: str
    priority: int = 0
    description: str = ""
    filters: dict[str, Any] = field(default_factory=dict)


class Router:
    def __init__(self):
        self._routes: list[Route] = []
        self._handlers: dict[str, Callable[..., Any]] = {}

    def add_route(self, route: Route) -> None:
        self._routes.append(route)
        self._routes.sort(key=lambda r: r.priority, reverse=True)

    def add_routes(self, routes: list[Route]) -> None:
        for r in routes:
            self.add_route(r)

    def register_handler(self, name: str, handler: Callable[..., Any]) -> None:
        self._handlers[name] = handler

    def route(self, platform: str, text: str, **context: Any) -> str | None:
        for route in self._routes:
            match = self._match_route(route, platform, text, context)
            if match:
                handler = self._handlers.get(route.target)
                if handler:
                    try:
                        result = handler(text=text, platform=platform, **context)
                        if result is not None:
                            return str(result)
                    except Exception:
                        logger.exception(f"Router handler failed: {route.target}")
                return route.target
        return None

    def _match_route(self, route: Route, platform: str, text: str, context: dict) -> bool:
        if route.filters.get("platform"):
            if platform not in route.filters["platform"]:
                return False
        if route.filters.get("prefix"):
            if not text.startswith(route.filters["prefix"]):
                return False
        if route.filters.get("regex"):
            if not re.search(route.filters["regex"], text):
                return False
        if route.pattern == "*" or route.pattern == platform:
            return True
        if route.pattern.startswith("regex:"):
            return bool(re.search(route.pattern[6:], text))
        return False

    def list_routes(self) -> list[Route]:
        return list(self._routes)

    def clear(self) -> None:
        self._routes.clear()
        self._handlers.clear()


def create_default_routes() -> list[Route]:
    return [
        Route(id="help", pattern="regex:^(/help|aide|help)$",
              target="help", priority=100,
              description="Aide et commandes disponibles"),
        Route(id="status", pattern="regex:^/status$",
              target="status", priority=90,
              description="État du système"),
        Route(id="chat", pattern="*", target="chat", priority=0,
              description="Chat avec l'agent CIEL"),
    ]
