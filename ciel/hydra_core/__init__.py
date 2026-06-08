"""
CIEL v∞.3 — HYDRA Core : Moteur d'Évolution Darwinienne Multi-Agent.

Composants portés de HYDRA (TypeScript → Python) :
  - Pantheon       : 11 agents Olympiens + consensus BCQ
  - HydraBrain     : cycle OODA (Observe-Orient-Decide-Act)
  - ImperialCycle  : évolution darwinienne (pop 100, élite 10%)
  - UnifiedGenome  : génome unifié (4 chromosomes, 100+ gènes)
  - TitanRL        : RL 12 dimensions (policy gradient)
  - MetamorphicCore: auto-réécriture supervisée (Aegis)
  - SkillGraph     : graphe orienté de skills
  - ThoughtTree    : arbre de raisonnement hiérarchique
  - SystemBus      : bus d'événements inter-composants
  - TitanNVM       : mémoire persistante (Neural Virtual Machine)
"""
from __future__ import annotations

from ciel.hydra_core.core import (
    SystemBus, Event, EventPriority,
    TitanNVM, MemoryBlock,
    AgentRole, AgentProposal, ConsensusResult, Pantheon,
    SkillNode, SkillGraph,
    ThoughtType, Thought, ThoughtTree,
    Chromosome, Gene, UnifiedGenome,
    ImperialCycle,
    Aegis, MutationPatch, MetamorphicCore,
    RewardVector, TitanRL,
    HydraBrain, HydraEngine,
)

__all__ = [
    "SystemBus", "Event", "EventPriority",
    "TitanNVM", "MemoryBlock",
    "AgentRole", "AgentProposal", "ConsensusResult", "Pantheon",
    "SkillNode", "SkillGraph",
    "ThoughtType", "Thought", "ThoughtTree",
    "Chromosome", "Gene", "UnifiedGenome",
    "ImperialCycle",
    "Aegis", "MutationPatch", "MetamorphicCore",
    "RewardVector", "TitanRL",
    "HydraBrain", "HydraEngine",
]
