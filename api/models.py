"""Pydantic models for CIEL API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Generic ──

class ProcessRequest(BaseModel):
    action: str = Field(default="status", description="Action à exécuter")
    data: dict[str, Any] = Field(default_factory=dict)

class ProcessResponse(BaseModel):
    success: bool = True
    result: Any = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    engine: str = "brain"

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "v∞.8"
    uptime: float = 0.0
    modules_active: int = 0
    cycles: int = 0


# ── Ethics ──

class EthicsCheckRequest(BaseModel):
    action: str
    context: dict[str, Any] = Field(default_factory=dict)

class EthicsCheckResponse(BaseModel):
    allowed: bool
    reason: str = ""
    layer: str = ""
    risk_score: float = 0.0


# ── Consciousness ──

class ConsciousnessStateResponse(BaseModel):
    level: str
    awareness: float
    qualia: dict[str, Any] = Field(default_factory=dict)


# ── Affect ──

class AffectTriggerRequest(BaseModel):
    emotion: str
    intensity: float | None = None

class AffectVectorResponse(BaseModel):
    dominant: str
    intensity: float
    valence: float
    arousal: float
    all_emotions: dict[str, float]


# ── Evolution ──

class EvolveRequest(BaseModel):
    generations: int = Field(default=1, ge=1, le=100)
    elite_pct: float = Field(default=0.1, ge=0.0, le=1.0)
    mut_rate: float = Field(default=0.1, ge=0.0, le=1.0)

class EvolveResponse(BaseModel):
    generation: int
    best_fitness: float
    population_size: int
    elapsed_ms: float


# ── Economy ──

class TradeRequest(BaseModel):
    seller: str
    buyer: str
    market: str = "skills"
    item: str = ""
    price: float = 10.0

class EconomyStatusResponse(BaseModel):
    agents: int
    gdp: float
    money_supply: float
    inflation: float
    transactions: int


# ── Memory ──

class MemoryStoreRequest(BaseModel):
    content: dict[str, Any]
    memory_type: str = "episodic"
    tags: list[str] = Field(default_factory=list)

class MemoryQueryRequest(BaseModel):
    query: str
    limit: int = 10


# ── Auth ──

class TokenRequest(BaseModel):
    api_key: str

class TokenResponse(BaseModel):
    token: str
    expires_at: datetime
    scope: str = "full"


# ── Config ──

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8765
    api_keys: list[str] = Field(default_factory=list)
    require_auth: bool = True
    rate_limit: int = 100
    log_level: str = "INFO"
