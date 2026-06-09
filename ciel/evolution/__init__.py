"""
CIEL v∞.4 — Evolution : Arsenal Évolutionnaire Complet (80+ algorithmes).

Inspiré de HYDRA evolution module (60+ algorithmes TS + portages v∞.4).
Porté en Python avec intégration native.

Architecture :
- Bloc A : Évolution Classique Étendue (GA, GP, DE, CMA-ES, NEAT, etc.)
- Bloc B : Apprentissage par Renforcement (DQN, PPO, SAC, Dreamer, MuZero, etc.)
- Bloc C : Meta-Learning (MAML, Reptile, RL², etc.)
- Bloc C : Continual Learning (EWC, SI, PNN, etc.)
- Bloc D : Intelligence en Nuée (ACO, PSO, ABC, etc.)
- Bloc E : Algorithmes Immunitaires (CLONALG, Danger Theory)
- Bloc F : Algorithmes Endocriniens (Hormones digitales)
- Bloc G : Open-Ended Evolution (POET, Enhanced POET, etc.)
- Bloc H : Co-Évolution & Symbiogenèse
- Bloc I : Quality-Diversity (MAP-Elites, CVT-MAP-Elites, etc.)
- Bloc J : Multi-Objectif (NSGA-II, MOEA/D, IBEA, etc.)
- Bloc K : Architectures Avancées v∞.4 (MetamorphicCore, EmergentLanguage, Titan)
- Modules v∞.4 : Aegis, CausalBrain, CRISPR_Titan, Curator, DialecticalEngine,
  DreamWeaver, EntropyHarvester, GladiatorArena, KarmicMemory, LeaderNetwork,
  ParadoxEngine, PhiEngine, QuantumResonance, ResonanceEngine, Sensorium,
  StrangeLoop, SymbioticProtocol, ArcheDeNoe
"""
from __future__ import annotations

# Bloc A : Évolution Classique
from ciel.evolution.genetic import GeneticAlgorithm, GeneticOperator
from ciel.evolution.differential import DifferentialEvolution, DEStrategy
from ciel.evolution.cma_es import CMAES, SepCMAES
from ciel.evolution.neat import NEAT, HyperNEAT
from ciel.evolution.programming import GeneticProgramming, CGP
from ciel.evolution.es_hyperneat import ES_HyperNEAT

# Bloc B : RL
from ciel.evolution.rl import (
    DQN, PPO, SAC, TD3, DreamerV3, MuZero, 
    HierarchicalRL, MultiAgentRL, InverseRL
)

# Bloc C : Meta-Learning & Continual
from ciel.evolution.meta import MAML, Reptile, ANIL, ProtoNets
from ciel.evolution.continual import EWC, SI, PackNet, ProgressiveNN

# Bloc D : Swarm
from ciel.evolution.swarm import (
    ACO, PSO, ABC, CS, GWO, WOA, GOA, MFO, SCA, SSA, FFA, BA, FSS, SSO, HBA, EHO, AHA
)

# Bloc E : Immunitaire
from ciel.evolution.immune import CLONALG, NegativeSelection, AINET, DangerTheory

# Bloc F : Endocrinien
from ciel.evolution.endocrine import HormonalSystem, Cortisol, Dopamine, Oxytocin

# Bloc G : OEE
from ciel.evolution.oee import POET, EnhancedPOET, OMNI

# Bloc H : Co-Évolution
from ciel.evolution.coevolution import Coevolution, PredatorPrey, HallOfFame

# Bloc I : Quality-Diversity
from ciel.evolution.qd import MAPElites, CVT_MAPElites, AURORA, SAIL

# Bloc J : Multi-Objectif
from ciel.evolution.multiobjective import NSGA2, NSGA3, MOEAD, IBEA, HypE

# ——— Modules d'Architecture (Portage evolution_hydra) ———
from ciel.evolution.aegis import Aegis
from ciel.evolution.arche_de_noe import ArcheDeNoe, ExistentialThreat, ArkEntry
from ciel.evolution.causal_brain import CausalBrain, CausalEvent, CausalGraph
from ciel.evolution.crispr_titan import CRISPR_Titan
from ciel.evolution.curator import Curator, DataArtifact, DataQuality
from ciel.evolution.dialectical_engine import DialecticalEngine
from ciel.evolution.dream_weaver import DreamWeaver, Dream, DreamPhase
from ciel.evolution.entropy_harvester import EntropyHarvester
from ciel.evolution.gladiator_arena import GladiatorArena
from ciel.evolution.karmic_memory import KarmicMemory
from ciel.evolution.leader_network import LeaderNetwork
from ciel.evolution.paradox_engine import ParadoxEngine, Paradox, ParadoxType, ParadoxicalInsight
from ciel.evolution.phi_engine import PhiEngine
from ciel.evolution.quantum_resonance import QuantumResonance, Qubit, ResonanceField
from ciel.evolution.resonance_engine import ResonanceEngine, ResonancePattern
from ciel.evolution.sensorium import Sensorium, Modality, SensoryInput, IntegratedPercept
from ciel.evolution.strange_loop import StrangeLoop, StrangeLoopNode, LoopState
from ciel.evolution.symbiotic_protocol import SymbioticProtocol, SymbioticPair, SymbiosisType

# ——— Bloc K : Architectures Avancées (v∞.4) ———
from ciel.evolution.metamorphic_core import MetamorphicCore, ArchitecturalGene, TransmutationProposal
from ciel.evolution.emergent_language import EmergentLanguage, Signal, EmergentToken
from ciel.evolution.titan import TitanEcosystem, TitanRL, HierarchicalEpisodicMemory

# Moteur CIELBrain
from ciel.evolution.core import EvolutionEngine

__all__ = [
    # Bloc A
    "GeneticAlgorithm", "GeneticOperator",
    "DifferentialEvolution", "DEStrategy",
    "CMAES", "SepCMAES",
    "NEAT", "HyperNEAT",
    "GeneticProgramming", "CGP",
    "ES_HyperNEAT",
    # Bloc B
    "DQN", "PPO", "SAC", "TD3", "DreamerV3", "MuZero",
    "HierarchicalRL", "MultiAgentRL", "InverseRL",
    # Bloc C
    "MAML", "Reptile", "ANIL", "ProtoNets",
    "EWC", "SI", "PackNet", "ProgressiveNN",
    # Bloc D
    "ACO", "PSO", "ABC", "CS", "GWO", "WOA", "GOA", "MFO", "SCA", "SSA", "FFA", "BA", "FSS", "SSO", "HBA", "EHO", "AHA",
    # Bloc E
    "CLONALG", "NegativeSelection", "AINET", "DangerTheory",
    # Bloc F
    "HormonalSystem", "Cortisol", "Dopamine", "Oxytocin",
    # Bloc G
    "POET", "EnhancedPOET", "OMNI",
    # Bloc H
    "Coevolution", "PredatorPrey", "HallOfFame",
    # Bloc I
    "MAPElites", "CVT_MAPElites", "AURORA", "SAIL",
    # Bloc J
    "NSGA2", "NSGA3", "MOEAD", "IBEA", "HypE",
    # Bloc K — Architectures Avancées
    "MetamorphicCore", "ArchitecturalGene", "TransmutationProposal",
    "EmergentLanguage", "Signal", "EmergentToken",
    "TitanEcosystem", "TitanRL", "HierarchicalEpisodicMemory",
    # Modules d'Architecture (Portage evolution_hydra)
    "Aegis", "ArcheDeNoe", "ExistentialThreat", "ArkEntry",
    "CausalBrain", "CausalEvent", "CausalGraph",
    "CRISPR_Titan", "Curator", "DataArtifact", "DataQuality",
    "DialecticalEngine", "DreamWeaver", "Dream", "DreamPhase",
    "EntropyHarvester", "GladiatorArena", "KarmicMemory",
    "LeaderNetwork", "ParadoxEngine", "Paradox", "ParadoxType", "ParadoxicalInsight",
    "PhiEngine", "QuantumResonance", "Qubit", "ResonanceField",
    "ResonanceEngine", "ResonancePattern",
    "Sensorium", "Modality", "SensoryInput", "IntegratedPercept",
    "StrangeLoop", "StrangeLoopNode", "LoopState",
    "SymbioticProtocol", "SymbioticPair", "SymbiosisType",
    # Moteur
    "EvolutionEngine",
]