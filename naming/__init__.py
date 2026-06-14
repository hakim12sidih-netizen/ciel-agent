"""CIEL v∞.4 — Système de Nomination : agents subordonnés (Tensura-inspired)."""
from __future__ import annotations

from ciel.naming.core import Agent, AgentTier, Skill, Grimoire, SoulCore, NamingEngine
from ciel.naming.agents import (
    PREDEFINED_AGENTS, RAPHAEL, CHRONOS, FORGE,
    SOEI, BENIMARU, SHION, SHUNA, KUROBE, DIABLO,
    TIER_S_AGENTS, TIER_A_AGENTS, bootstrap_naming_engine,
)

__all__ = [
    "Agent", "AgentTier", "Skill", "Grimoire", "SoulCore", "NamingEngine",
    "PREDEFINED_AGENTS", "RAPHAEL", "CHRONOS", "FORGE",
    "SOEI", "BENIMARU", "SHION", "SHUNA", "KUROBE", "DIABLO",
    "TIER_S_AGENTS", "TIER_A_AGENTS", "bootstrap_naming_engine",
]
