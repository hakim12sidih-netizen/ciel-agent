"""
Strate 8 — NOOSPHÈRE : Conscience Mondiale, Web, Sciences.

Composants :
  - web_crawler    : navigation, scraping éthique
  - api_manager    : rate limiting, retry, fallback
  - federated      : FedAvg, SCAFFOLD, FedProx
  - osint          : sources ouvertes (légales)

Sources :
  - Web public (HTTP/HTTPS)
  - APIs REST/GraphQL
  - Bases scientifiques (arXiv, PubMed, ...)
  - OSINT légal (données publiques)
"""
from __future__ import annotations

from ciel.noosphere.core import (
    SourceType,
    ContentType,
    SourceResponse,
    SourceRequest,
    RateLimiter,
    RetryPolicy,
    WebCrawler,
    ApiManager,
    FederatedLearning,
    OSINTSource,
    NoosphereEngine,
)

__all__ = [
    "SourceType",
    "ContentType",
    "SourceResponse",
    "SourceRequest",
    "RateLimiter",
    "RetryPolicy",
    "WebCrawler",
    "ApiManager",
    "FederatedLearning",
    "OSINTSource",
    "NoosphereEngine",
]
