"""
CIEL v1.0 — Agents : système multi-agents cognitifs.

Contient :
  - Overseer, Alchemist, OmegaSync (métacognition)
  - AgentProfile, AgentRunner, AgentManager (exécution)
  - SubAgent, SubAgentResult (délégation)
"""
from __future__ import annotations

from ciel.agents.overseer import Overseer
from ciel.agents.alchemist import Alchemist
from ciel.agents.omega_sync import OmegaSync
from ciel.agents.core import (
    AgentProfile, AgentRunner, AgentManager, AgentSession, AgentMessage,
    SubAgentSpec, SubAgentResult, get_manager, reset_manager,
)

__all__ = [
    "Overseer", "Alchemist", "OmegaSync",
    "AgentProfile", "AgentRunner", "AgentManager",
    "AgentSession", "AgentMessage",
    "SubAgentSpec", "SubAgentResult",
    "get_manager", "reset_manager",
]
