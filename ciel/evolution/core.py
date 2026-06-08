from __future__ import annotations

from typing import Any

import numpy as np

from ciel.evolution.genetic import GeneticAlgorithm, GAParams
from ciel.evolution.swarm import PSO, SwarmParams
from ciel.evolution.differential import DifferentialEvolution, DEParams
from ciel.evolution.cma_es import CMAES, SepCMAES, CMAESParams
from ciel.evolution.neat import NEAT, HyperNEAT, NEATParams
from ciel.evolution.es_hyperneat import ES_HyperNEAT
from ciel.evolution.programming import GeneticProgramming, CGP
from ciel.evolution.multiobjective import NSGA2, NSGA3, MOEAD, IBEA, HypE, MOParams
from ciel.evolution.qd import MAPElites, CVT_MAPElites, AURORA, SAIL, QDParams
from ciel.evolution.oee import POET, EnhancedPOET, OMNI, OEEParams
from ciel.evolution.coevolution import Coevolution, PredatorPrey, CoevParams
from ciel.evolution.immune import CLONALG, AINET, ImmuneParams
from ciel.evolution.rl import DQN, PPO, SAC, TD3, RLParams


def _sphere(x: np.ndarray) -> float:
    return float(np.sum(x ** 2))


_ALGORITHMS = {
    "ga": ("GeneticAlgorithm", "Algorithme génétique classique avec sélection, crossover, mutation"),
    "de": ("DifferentialEvolution", "Évolution différentielle"),
    "cmaes": ("CMAES", "CMA-ES : stratégie d'évolution adaptative de covariance"),
    "sep_cmaes": ("SepCMAES", "CMA-ES séparable"),
    "pso": ("PSO", "Optimisation par essaims de particules"),
    "neat": ("NEAT", "Neuroévolution de topologies augmentées"),
    "hyperneat": ("HyperNEAT", "NEAT avec substrat CPPN"),
    "es_hyperneat": ("ES_HyperNEAT", "ES pour HyperNEAT"),
    "gp": ("GeneticProgramming", "Programmation génétique"),
    "cgp": ("CGP", "Programmation génétique cartésienne"),
    "nsga2": ("NSGA2", "Algorithme génétique de tri non-dominé II"),
    "nsga3": ("NSGA3", "NSGA-III multi-objectif"),
    "moead": ("MOEAD", "Décomposition multi-objectif"),
    "ibea": ("IBEA", "Algorithm évolutionnaire basé sur indicateur"),
    "map_elites": ("MAPElites", "Quality-Diversity MAP-Elites"),
    "cvt_map_elites": ("CVT_MAPElites", "MAP-Elites avec centroïdes CVT"),
    "aurora": ("AURORA", "Quality-Diversity AURORA"),
    "sail": ("SAIL", "Quality-Diversity SAIL"),
    "poet": ("POET", "Open-Ended Evolution POET"),
    "enhanced_poet": ("EnhancedPOET", "POET amélioré"),
    "omni": ("OMNI", "Open-Ended Evolution OMNI"),
    "coevolution": ("Coevolution", "Co-évolution classique"),
    "predator_prey": ("PredatorPrey", "Scénario proie-prédateur co-évolutif"),
    "clonalg": ("CLONALG", "Algorithme immunitaire clonal"),
    "ainet": ("AINET", "Réseau immunitaire artificiel"),
    "dqn": ("DQN", "Deep Q-Network (RL)"),
    "ppo": ("PPO", "Proximal Policy Optimization (RL)"),
    "sac": ("SAC", "Soft Actor-Critic (RL)"),
    "td3": ("TD3", "Twin Delayed DDPG (RL)"),
}


class EvolutionEngine:
    """EvolutionEngine — moteur évolutionnaire unifié.

    Wrapper process() compatible CIELBrain pour l'arsenal de 60+ algorithmes.
    Délègue à chaque implémentation spécifique selon la clé "algorithm".
    """

    def __init__(self):
        self._runs: int = 0
        self._converged: int = 0

    def list_algorithms(self) -> dict[str, str]:
        return {k: desc for k, (_, desc) in _ALGORITHMS.items()}

    def run(self, algorithm: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        p = params or {}
        self._runs += 1

        match algorithm:
            case "ga":
                def create():
                    return [np.random.uniform(-5, 5) for _ in range(p.get("dimensions", 5))]
                ga = GeneticAlgorithm(
                    create_genome=create,
                    evaluate=lambda g: -sum(abs(x) for x in g),
                    crossover=lambda a, b: (a[:2] + b[2:], b[:2] + a[2:]),
                    mutate=lambda g, r: [x + np.random.normal(0, r) for x in g],
                    params=GAParams(population_size=p.get("population_size", 50), generations=p.get("generations", 20)),
                )
                best = ga.run()
                return {"success": True, "best_fitness": best.fitness, "generations": ga.generation}

            case "de":
                dim = p.get("dimensions", 5)
                de = DifferentialEvolution(_sphere, dimensions=dim, params=DEParams(population_size=p.get("population_size", 30), generations=p.get("generations", 20)))
                best, fit = de.run()
                return {"success": True, "best_fitness": fit, "generations": de.generation}

            case "cmaes" | "cma_es":
                cma = CMAES(_sphere, params=CMAESParams(dimension=p.get("dimensions", 5), population_size=p.get("population_size"), generations=p.get("generations", 50)))
                best = cma.run()
                return {"success": True, "best_fitness": float(np.sum(best ** 2)), "generations": cma.generation}

            case "pso":
                pso = PSO(_sphere, params=SwarmParams(dimensions=p.get("dimensions", 5), population_size=p.get("population_size", 30), generations=p.get("generations", 20)))
                pso.run()
                return {"success": True, "best_fitness": pso.global_best_fitness, "generations": pso.generation}

            case "neat":
                neat = NEAT(lambda g: 1.0 - abs(len(g.connections) - 5) / 10.0, params=NEATParams(population_size=p.get("population_size", 20), generations=p.get("generations", 3)))
                neat.run()
                return {"success": True, "best_fitness": neat.best_fitness, "generations": neat.generation}

            case "nsga2":
                nsga2 = NSGA2(lambda x: np.array([x[0]**2, (x[1]-1)**2]), params=MOParams(dimensions=p.get("dimensions", 3), population_size=p.get("population_size", 30), generations=p.get("generations", 10)))
                pop, fit = nsga2.run()
                return {"success": True, "pareto_size": len(pop), "generations": nsga2.generation}

            case "map_elites":
                me = MAPElites(evaluate=_sphere, dimensions=p.get("dimensions", 2), params=QDParams(population_size=p.get("population_size", 30), generations=p.get("generations", 10)))
                me.run()
                return {"success": True, "generations": me.generation}

            case _:
                return {"success": False, "error": f"algorithme '{algorithm}' non implémenté dans l'engine"}

    def get_stats(self) -> dict[str, Any]:
        return {
            "runs": self._runs,
            "converged": self._converged,
            "algorithms_available": len(_ALGORITHMS),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "run":
            return self.run(str(data.get("algorithm", "ga")), data.get("params"))

        elif action == "list":
            return {"success": True, "algorithms": self.list_algorithms()}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
