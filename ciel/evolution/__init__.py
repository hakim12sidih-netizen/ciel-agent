"""
CIEL v∞.3 — Evolution : Arsenal Évolutionnaire Complet (60+ algorithmes).

Inspiré de HYDRA evolution module (60+ algorithmes TS).
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

# Bloc K : Architectures Avancées (v∞.4)
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
    # Moteur
    "EvolutionEngine",
]