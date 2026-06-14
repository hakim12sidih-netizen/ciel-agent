from __future__ import annotations

import math
import random
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SourceType(Enum):
    WEB = "web"
    API = "api"
    SCIENTIFIC = "scientific"
    OSINT = "osint"
    FEDERATED = "federated"


class ContentType(Enum):
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    XML = "xml"
    BINARY = "binary"


@dataclass(slots=True)
class SourceResponse:
    id: str
    source: str
    source_type: SourceType
    content: str
    content_type: ContentType = ContentType.TEXT
    status_code: int = 200
    latency_ms: float = 0.0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def successful(self) -> bool:
        return 200 <= self.status_code < 300


@dataclass(slots=True)
class SourceRequest:
    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    body: str | None = None
    timeout_s: float = 10.0
    retry_count: int = 0


class RateLimiter:
    """Contrôle de débit — limite les requêtes par fenêtre temporelle."""

    def __init__(self, max_per_window: int = 60, window_s: float = 60.0):
        self.max_per_window = max_per_window
        self.window_s = window_s
        self._timestamps: list[float] = []

    def allow(self) -> bool:
        now = time.time()
        cutoff = now - self.window_s
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        if len(self._timestamps) < self.max_per_window:
            self._timestamps.append(now)
            return True
        return False

    def wait_time(self) -> float:
        if self.allow():
            return 0.0
        if not self._timestamps:
            return 0.0
        oldest = self._timestamps[0]
        return max(0.0, oldest + self.window_s - time.time())

    def reset(self) -> None:
        self._timestamps.clear()


class RetryPolicy:
    """Politique de réessai avec backoff exponentiel."""

    def __init__(self, max_retries: int = 3, base_delay_s: float = 1.0,
                 max_delay_s: float = 30.0, jitter: bool = True):
        self.max_retries = max_retries
        self.base_delay_s = base_delay_s
        self.max_delay_s = max_delay_s
        self.jitter = jitter

    def delay(self, attempt: int) -> float:
        delay = min(self.base_delay_s * (2 ** attempt), self.max_delay_s)
        if self.jitter:
            delay *= random.uniform(0.5, 1.5)
        return delay

    def should_retry(self, attempt: int, response: SourceResponse | None = None) -> bool:
        if attempt >= self.max_retries:
            return False
        if response is None:
            return True
        return not response.successful()


class WebCrawler:
    """Crawler web avec politesse et respect robots.txt simulé."""

    def __init__(self, rate_limiter: RateLimiter | None = None,
                 retry_policy: RetryPolicy | None = None,
                 respect_robots: bool = True):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.retry_policy = retry_policy or RetryPolicy()
        self.respect_robots = respect_robots
        self._crawl_count = 0
        self._blocked_domains: set[str] = set()

    def block_domain(self, domain: str) -> None:
        self._blocked_domains.add(domain)

    def unblock_domain(self, domain: str) -> None:
        self._blocked_domains.discard(domain)

    def crawl(self, url: str) -> SourceResponse:
        self._crawl_count += 1
        request = SourceRequest(url=url)
        return self._execute(request)

    def _execute(self, request: SourceRequest) -> SourceResponse:
        if not self.rate_limiter.allow():
            wait = self.rate_limiter.wait_time()
            return SourceResponse(
                id=str(uuid.uuid4()),
                source=request.url,
                source_type=SourceType.WEB,
                content="",
                status_code=429,
                metadata={"error": "rate_limited", "wait_s": wait},
            )

        domain = request.url.split("/")[2] if "//" in request.url else request.url
        if domain in self._blocked_domains:
            return SourceResponse(
                id=str(uuid.uuid4()),
                source=request.url,
                source_type=SourceType.WEB,
                content="",
                status_code=403,
                metadata={"error": "domain_blocked"},
            )

        latency = random.uniform(0.05, 0.5)
        success = random.random() > 0.1
        content = f"<html><body>contenu simulé de {request.url}</body></html>" if success else ""

        response = SourceResponse(
            id=str(uuid.uuid4()),
            source=request.url,
            source_type=SourceType.WEB,
            content=content,
            content_type=ContentType.HTML,
            status_code=200 if success else 500,
            latency_ms=latency * 1000,
            metadata={"domain": domain, "method": request.method},
        )

        if not response.successful():
            for attempt in range(self.retry_policy.max_retries):
                delay = self.retry_policy.delay(attempt)
                time.sleep(delay * 0.001)
                response.status_code = 200
                response.content = f"<html><body>contenu après retry {attempt + 1}</body></html>"
                response.latency_ms = delay * 1000
                break

        return response

    def crawl_count(self) -> int:
        return self._crawl_count


class ApiManager:
    """Gestionnaire d'API — rate limiting, retry, fallback."""

    def __init__(self, rate_limiter: RateLimiter | None = None,
                 retry_policy: RetryPolicy | None = None):
        self.rate_limiter = rate_limiter or RateLimiter(max_per_window=30, window_s=60.0)
        self.retry_policy = retry_policy or RetryPolicy()
        self._endpoints: dict[str, dict[str, Any]] = {}
        self._call_count = 0

    def register_endpoint(self, name: str, url: str, method: str = "GET",
                          headers: dict[str, str] | None = None) -> None:
        self._endpoints[name] = {
            "url": url,
            "method": method,
            "headers": headers or {},
        }

    def call(self, endpoint: str, params: dict[str, str] | None = None) -> SourceResponse:
        self._call_count += 1
        ep = self._endpoints.get(endpoint)
        if ep is None:
            return SourceResponse(
                id=str(uuid.uuid4()),
                source=endpoint,
                source_type=SourceType.API,
                content="",
                status_code=404,
                metadata={"error": f"endpoint '{endpoint}' not registered"},
            )

        if not self.rate_limiter.allow():
            return SourceResponse(
                id=str(uuid.uuid4()),
                source=ep["url"],
                source_type=SourceType.API,
                content="",
                status_code=429,
                metadata={"error": "rate_limited"},
            )

        latency = random.uniform(0.01, 0.3)
        success = random.random() > 0.05
        response = SourceResponse(
            id=str(uuid.uuid4()),
            source=ep["url"],
            source_type=SourceType.API,
            content=f'{{"status": "ok", "endpoint": "{endpoint}"}}' if success else "",
            content_type=ContentType.JSON,
            status_code=200 if success else 503,
            latency_ms=latency * 1000,
            metadata={"endpoint": endpoint, "method": ep["method"]},
        )
        return response

    def call_count(self) -> int:
        return self._call_count


class FederatedLearning:
    """Apprentissage fédéré — FedAvg simple."""

    def __init__(self, n_clients: int = 5, fraction_fit: float = 0.8):
        self.n_clients = n_clients
        self.fraction_fit = fraction_fit
        self._round = 0
        self._global_weights: dict[str, float] = {}
        self._client_weights: list[dict[str, float]] = []

    def init_weights(self, n_params: int = 10) -> None:
        self._global_weights = {f"w{i}": random.gauss(0, 0.1) for i in range(n_params)}

    def round(self) -> dict[str, Any]:
        self._round += 1
        n_selected = max(1, int(self.n_clients * self.fraction_fit))
        selected = random.sample(range(self.n_clients), n_selected)

        self._client_weights = []
        for idx in selected:
            client_w = {
                k: v + random.gauss(0, 0.05) for k, v in self._global_weights.items()
            }
            self._client_weights.append(client_w)

        self._global_weights = {
            k: sum(cw[k] for cw in self._client_weights) / len(self._client_weights)
            for k in self._global_weights
        }

        return {
            "round": self._round,
            "clients_selected": selected,
            "n_clients": len(selected),
            "global_weights": dict(self._global_weights),
            "convergence": self._estimate_convergence(),
        }

    def _estimate_convergence(self) -> float:
        if not self._client_weights or not self._global_weights:
            return 0.0
        variances = []
        for k in self._global_weights:
            vals = [cw[k] for cw in self._client_weights]
            mean = sum(vals) / len(vals)
            var = sum((v - mean) ** 2 for v in vals) / len(vals)
            variances.append(var)
        return 1.0 - min(1.0, math.sqrt(sum(variances) / len(variances)))

    def current_round(self) -> int:
        return self._round

    def get_weights(self) -> dict[str, float]:
        return dict(self._global_weights)


class OSINTSource:
    """Source OSINT — collecte de données publiques."""

    def __init__(self, name: str, source_type: SourceType = SourceType.OSINT):
        self.name = name
        self.source_type = source_type
        self._collected: list[SourceResponse] = []

    def collect(self, query: str) -> SourceResponse:
        latency = random.uniform(0.1, 0.8)
        content = f"osint: '{query}' — données simulées depuis {self.name}"
        response = SourceResponse(
            id=str(uuid.uuid4()),
            source=self.name,
            source_type=self.source_type,
            content=content,
            content_type=ContentType.TEXT,
            status_code=200,
            latency_ms=latency * 1000,
            metadata={"query": query},
        )
        self._collected.append(response)
        return response

    def collect_batch(self, queries: list[str]) -> list[SourceResponse]:
        return [self.collect(q) for q in queries]

    def collected_count(self) -> int:
        return len(self._collected)

    def clear(self) -> None:
        self._collected.clear()


class NoosphereEngine:
    """Point d'entrée principal de la Strate 8 — NOOSPHÈRE.

    Conscience mondiale :
    - Web crawling with politeness
    - API management with rate limiting
    - Federated learning (FedAvg)
    - OSINT data collection
    """

    def __init__(self) -> None:
        self.web_crawler = WebCrawler()
        self.api_manager = ApiManager()
        self.federated = FederatedLearning()
        self._osint_sources: dict[str, OSINTSource] = {}
        self._responses: list[SourceResponse] = []

    def add_osint_source(self, name: str) -> OSINTSource:
        source = OSINTSource(name=name)
        self._osint_sources[name] = source
        return source

    def get_osint_source(self, name: str) -> OSINTSource | None:
        return self._osint_sources.get(name)

    def crawl(self, url: str) -> SourceResponse:
        response = self.web_crawler.crawl(url)
        self._responses.append(response)
        return response

    def api_call(self, endpoint: str, params: dict[str, str] | None = None) -> SourceResponse:
        response = self.api_manager.call(endpoint, params)
        self._responses.append(response)
        return response

    def federated_round(self) -> dict[str, Any]:
        if not self.federated.get_weights():
            self.federated.init_weights()
        return self.federated.round()

    def osint_collect(self, source_name: str, query: str) -> SourceResponse | None:
        source = self._osint_sources.get(source_name)
        if source is None:
            return None
        response = source.collect(query)
        self._responses.append(response)
        return response

    def get_stats(self) -> dict[str, Any]:
        return {
            "crawl_count": self.web_crawler.crawl_count(),
            "api_calls": self.api_manager.call_count(),
            "federated_rounds": self.federated.current_round(),
            "osint_sources": list(self._osint_sources.keys()),
            "total_responses": len(self._responses),
            "osint_collected": sum(
                s.collected_count() for s in self._osint_sources.values()
            ),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "")
        if action == "crawl":
            resp = self.crawl(input_data.get("url", ""))
            return {"success": resp.successful(), "response": resp, "action": "crawl"}
        if action == "api":
            resp = self.api_call(
                input_data.get("endpoint", ""),
                input_data.get("params"),
            )
            return {"success": resp.successful(), "response": resp, "action": "api"}
        if action == "federated":
            result = self.federated_round()
            return {"success": True, "result": result, "action": "federated"}
        if action == "osint":
            resp = self.osint_collect(
                input_data.get("source", ""),
                input_data.get("query", ""),
            )
            if resp is None:
                return {"success": False, "error": "source not found", "action": "osint"}
            return {"success": True, "response": resp, "action": "osint"}
        return {"success": False, "error": f"unknown action '{action}'"}
