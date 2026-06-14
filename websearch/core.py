"""
CIEL v∞.8 — WEBSEARCH ENGINE.
Recherche web — CIEL explore le web.

Concept : CIEL cherche sur le web via DuckDuckGo (gratuit,
pas de clé API), lit des pages, extrait du contenu. Cache
des résultats pour éviter les requêtes redondantes.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class WebSearchResult:
    id: str
    query: str
    title: str = ""
    url: str = ""
    snippet: str = ""
    source: str = "web"
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {"id": self.id, "query": self.query,
                "title": self.title, "url": self.url,
                "snippet": self.snippet[:150]}


@dataclass(slots=True)
class CachedPage:
    url: str
    content: str = ""
    fetched_at: float = 0.0


class WebSearchEngine:
    """Moteur de recherche web.

    Utilise DuckDuckGo (pas de clé API), avec fallback
    sur des mock results pour le développement. Cache
    les résultats et pages pour 5 minutes.
    """

    def __init__(self):
        self.history: list[WebSearchResult] = []
        self.cache: dict[str, CachedPage] = {}
        self.network = LeaderNetwork()

    def search(self, query: str, max_results: int = 8) -> list[dict]:
        results = []
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                for i, r in enumerate(ddgs.text(query, max_results=max_results)):
                    sr = WebSearchResult(
                        id=f"WEB-{uuid.uuid4().hex[:12]}",
                        query=query,
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        timestamp=time.time(),
                    )
                    self.history.append(sr)
                    results.append(sr.to_dict())
                    if i >= max_results:
                        break
        except ImportError:
            results = self._mock_search(query, max_results)
        except Exception:
            results = self._mock_search(query, max_results)
        return results

    def _mock_search(self, query: str, n: int) -> list[dict]:
        results = []
        for i in range(min(n, 5)):
            sr = WebSearchResult(
                id=f"WEB-{uuid.uuid4().hex[:12]}",
                query=query,
                title=f"Résultat {i+1} pour '{query}'",
                url=f"https://example.com/{i}",
                snippet=f"Contenu simulé #{i}: à propos de {query}...",
                timestamp=time.time(),
            )
            self.history.append(sr)
            results.append(sr.to_dict())
        return results

    def fetch_page(self, url: str) -> dict:
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cached = self.cache.get(cache_key)
        if cached and time.time() - cached.fetched_at < 300:
            return {"url": url, "content": cached.content[:1000],
                    "cached": True}

        try:
            import httpx
            r = httpx.get(url, timeout=10, follow_redirects=True)
            content = r.text
            self.cache[cache_key] = CachedPage(
                url=url, content=content, fetched_at=time.time())
            return {"url": url, "content": content[:1000],
                    "size": len(content)}
        except Exception as e:
            return {"url": url, "error": str(e)}

    def get_stats(self) -> dict:
        return {
            "searches": len(self.history),
            "cached_pages": len(self.cache),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "search":
            results = self.search(
                input_data.get("query", ""),
                input_data.get("max", 8),
            )
            return {"status": "ok", "results": results,
                    "count": len(results)}
        elif action == "fetch":
            return {"status": "ok",
                    "page": self.fetch_page(
                        input_data.get("url", ""))}
        return {"status": "ok", "searches": len(self.history)}
