"""
CIEL v1.0 — Evolution : moteur d'évolution complet.

Modules d'architecture (portés depuis Hydra, améliorés pour CIEL) :
  - UnifiedGenome      : génome unifié (V1, V2, Titan)
  - ImperialCycle      : cycle d'évolution darwinien (8 phases)
  - FitnessEvaluator   : évaluation multi-dimensionnelle
  - GeneticOptimizer   : 5 stratégies de mutation
  - SymbioticProtocol  : super-organismes
  - LeaderNetwork      : bus d'événements
  - EmergentLanguage   : langage auto-organisé
  - FactionManager     : clustering par spécialité
  - LLMTransmuter      : auto-réécriture de code
  - Aegis              : audit statique
  - TransmutationBudget: limiteur de transmutation
  - MetamorphicCore    : cycle auto-métamorphose
  - TitanRL            : apprentissage 12 dimensions
"""
from __future__ import annotations

# Core evolution
from ciel.evolution.unified_genome import UnifiedGenome, GenomeMode, Gene, GeneCategory
from ciel.evolution.fitness_evaluator import FitnessEvaluator, FitnessResult
from ciel.evolution.imperial_cycle import ImperialCycle, ImperialCycleConfig, GenerationResult
from ciel.evolution.genetic_optimizer import GeneticOptimizer

# Symbiotic & communication
from ciel.evolution.symbiotic_protocol import SymbioticProtocol, Pact, SuperOrganism
from ciel.evolution.leader_network import LeaderNetwork, Event
from ciel.evolution.emergent_language import EmergentLanguage, SymbolicToken
from ciel.evolution.faction import FactionManager

# Self-rewriting
from ciel.evolution.llm_transmuter import LLMTransmuter, TransmutationProposal
from ciel.evolution.aegis import Aegis, AuditResult, AuditFinding
from ciel.evolution.transmutation_budget import TransmutationBudget
from ciel.evolution.metamorphic_core import MetamorphicCore, MetamorphicState

# Reinforcement Learning
from ciel.evolution.titan_rl import TitanRL, TaskResult, RLState, REWARD_DIMENSIONS

# Legacy modules (stubs for backward compatibility)
from ciel.evolution.genetic import GeneticAlgorithm, GeneticOperator
from ciel.evolution.swarm import ACO, PSO

__all__ = [
    # Core
    "UnifiedGenome", "GenomeMode", "Gene", "GeneCategory",
    "FitnessEvaluator", "FitnessResult",
    "ImperialCycle", "ImperialCycleConfig", "GenerationResult",
    "GeneticOptimizer",
    # Symbiotic
    "SymbioticProtocol", "Pact", "SuperOrganism",
    "LeaderNetwork", "Event",
    "EmergentLanguage", "SymbolicToken",
    "FactionManager",
    # Self-rewriting
    "LLMTransmuter", "TransmutationProposal",
    "Aegis", "AuditResult", "AuditFinding",
    "TransmutationBudget",
    "MetamorphicCore", "MetamorphicState",
    # RL
    "TitanRL", "TaskResult", "RLState", "REWARD_DIMENSIONS",
    # Legacy
    "GeneticAlgorithm", "GeneticOperator",
    "ACO", "PSO",
]
