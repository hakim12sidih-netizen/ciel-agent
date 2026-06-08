from __future__ import annotations

import random

import numpy as np
import pytest

from ciel.evolution.genetic import GeneticAlgorithm, GAParams, GeneticOperator
from ciel.evolution.differential import DifferentialEvolution, DEParams, DEStrategy
from ciel.evolution.cma_es import CMAES, SepCMAES, CMAESParams
from ciel.evolution.neat import NEAT, HyperNEAT, NEATParams
from ciel.evolution.es_hyperneat import ES_HyperNEAT
from ciel.evolution.programming import GeneticProgramming, CGP
from ciel.evolution.rl import DQN, PPO, SAC, TD3, DreamerV3, MuZero, HierarchicalRL, MultiAgentRL, InverseRL, RLParams
from ciel.evolution.meta import MAML, Reptile, ANIL, ProtoNets, MetaParams
from ciel.evolution.continual import EWC, SI, PackNet, ProgressiveNN, ContinualParams
from ciel.evolution.swarm import PSO, ACO, ABC, CS, GWO, WOA, GOA, MFO, SCA, SSA, FFA, BA, FSS, SSO, HBA, EHO, AHA, SwarmParams
from ciel.evolution.immune import CLONALG, NegativeSelection, AINET, DangerTheory, ImmuneParams
from ciel.evolution.endocrine import HormonalSystem, Cortisol, Dopamine, Oxytocin
from ciel.evolution.oee import POET, EnhancedPOET, OMNI, OEEParams
from ciel.evolution.coevolution import Coevolution, PredatorPrey, HallOfFame, CoevParams
from ciel.evolution.qd import MAPElites, CVT_MAPElites, AURORA, SAIL, QDParams
from ciel.evolution.multiobjective import NSGA2, NSGA3, MOEAD, IBEA, HypE, MOParams
from ciel.evolution.core import EvolutionEngine


def _sphere(x: np.ndarray) -> float:
    return float(np.sum(x ** 2))


def _sphere_mo(x: np.ndarray) -> np.ndarray:
    return np.array([x[0] ** 2, (x[1] - 1) ** 2])


# ─── Bloc A ────────────────────────────────────────────────────────

class TestGeneticAlgorithm:
    def test_create(self):
        ga = GeneticAlgorithm(
            create_genome=lambda: [random.random() for _ in range(5)],
            evaluate=lambda g: -sum(g),
            crossover=lambda a, b: (a[:], b[:]),
            mutate=lambda g, r: [x + random.gauss(0, r) for x in g],
        )
        assert ga.generation == 0

    def test_run(self):
        ga = GeneticAlgorithm(
            create_genome=lambda: [random.random() for _ in range(3)],
            evaluate=lambda g: -sum(g),
            crossover=lambda a, b: (a[:], b[:]),
            mutate=lambda g, r: [x + random.gauss(0, r) for x in g],
            params=GAParams(population_size=20, generations=5),
        )
        best = ga.run()
        assert best is not None

    def test_selection_modes(self):
        for sel in GeneticOperator:
            ga = GeneticAlgorithm(
                create_genome=lambda: [random.random()],
                evaluate=lambda g: -g[0],
                crossover=lambda a, b: (a[:], b[:]),
                mutate=lambda g, r: [g[0] + random.gauss(0, r)],
                params=GAParams(population_size=10, generations=2, selection=sel),
            )
            ga.run()

    def test_niching(self):
        ga = GeneticAlgorithm(
            create_genome=lambda: [random.random()],
            evaluate=lambda g: -g[0],
            crossover=lambda a, b: (a[:], b[:]),
            mutate=lambda g, r: [g[0] + random.gauss(0, r)],
            params=GAParams(population_size=10, generations=2, niching=True),
        )
        ga.run()


class TestDifferentialEvolution:
    def test_create(self):
        de = DifferentialEvolution(_sphere, params=DEParams(dimension=3))
        assert de.generation == 0

    def test_run(self):
        de = DifferentialEvolution(_sphere, params=DEParams(population_size=15, generations=5))
        best, fit = de.run()
        assert fit < float("inf")


class TestCMAES:
    def test_create(self):
        cma = CMAES(_sphere)
        assert cma.dim == 10

    def test_run(self):
        cma = CMAES(_sphere, params=CMAESParams(dimension=3, generations=20, population_size=10))
        cma.run()

    def test_sep_cmaes(self):
        sep = SepCMAES(_sphere, params=CMAESParams(dimension=2, generations=5, population_size=5))
        sep.run()


class TestNEAT:
    def test_create(self):
        neat = NEAT(lambda g: 1.0)
        assert neat.generation == 0

    def test_forward(self):
        neat = NEAT(lambda g: 1.0, params=NEATParams(n_inputs=2, n_outputs=1))
        genome = neat._create_minimal_genome()
        out = neat.forward(genome, [0.5, 0.3])
        assert len(out) == 1

    def test_speciate(self):
        neat = NEAT(lambda g: 1.0, params=NEATParams(population_size=10))
        neat.initialize()
        neat._speciate()
        assert len(neat.species) >= 1

    def test_step(self):
        neat = NEAT(lambda g: random.random(), params=NEATParams(population_size=10))
        neat.initialize()
        neat.step()
        assert neat.generation == 1

    def test_hyperneat(self):
        hneat = HyperNEAT(lambda g: 1.0, params=NEATParams(n_inputs=2, n_outputs=1, population_size=5))
        assert hneat.substrate_dims == (4, 4)

    def test_es_hyperneat(self):
        es = ES_HyperNEAT(_sphere, genome_dim=3, population_size=5, generations=2)
        es.run()


class TestGeneticProgramming:
    def test_create(self):
        gp = GeneticProgramming(fitness=lambda tree: 1.0, n_variables=2)
        assert gp.generation == 0

    def test_run(self):
        gp = GeneticProgramming(fitness=lambda tree: float(tree.depth()), n_variables=2, population_size=10, generations=5)
        gp.run()

    def test_cgp(self):
        cgp = CGP(fitness=lambda c: float(np.mean(c.genes)), n_inputs=2, n_outputs=1, n_cols=5, n_rows=2, population_size=10, generations=3)
        cgp.run()


# ─── Bloc B ────────────────────────────────────────────────────────

class TestRL:
    def test_dqn(self):
        dqn = DQN(RLParams(state_dim=4, action_dim=2))
        state = np.random.randn(4)
        action = dqn.act(state)
        assert 0 <= action < 2

    def test_ppo(self):
        ppo = PPO(RLParams(state_dim=4, action_dim=2))
        state = np.random.randn(4)
        action = ppo.act(state)
        assert 0 <= action < 2

    def test_sac(self):
        sac = SAC(RLParams(state_dim=4, action_dim=2))
        state = np.random.randn(4)
        action = sac.act(state)
        assert action.shape == (2,)

    def test_td3(self):
        td3 = TD3(RLParams(state_dim=4, action_dim=2))
        state = np.random.randn(4)
        action = td3.act(state)
        assert action.shape == (2,)

    def test_dreamer(self):
        d = DreamerV3()
        assert 0 <= d.act(np.random.randn(4)) < d.params.action_dim

    def test_muzero(self):
        m = MuZero()
        assert 0 <= m.act(np.random.randn(4)) < m.params.action_dim

    def test_hierarchical(self):
        hrl = HierarchicalRL()
        assert 0 <= hrl.act(np.random.randn(4)) < hrl.params.action_dim

    def test_multiagent(self):
        marl = MultiAgentRL(n_agents=3)
        assert 0 <= marl.act(np.random.randn(4), agent_id=1) < marl.params.action_dim

    def test_inverse_rl(self):
        irl = InverseRL()
        r = irl.infer_reward([np.random.randn(4)])
        assert r.shape == (4,)


# ─── Bloc C ────────────────────────────────────────────────────────

class TestMeta:
    @pytest.fixture
    def params(self):
        return MetaParams(input_dim=4, output_dim=1)

    def test_maml(self, params):
        maml = MAML(params)
        tasks = [(np.random.randn(3, 4), np.random.randn(3, 1),
                  np.random.randn(2, 4), np.random.randn(2, 1))]
        loss = maml.meta_step(tasks)
        assert loss > 0

    def test_reptile(self, params):
        rep = Reptile(params)
        tasks = [(np.random.randn(3, 4), np.random.randn(3, 1),
                  np.random.randn(2, 4), np.random.randn(2, 1))]
        losses = rep.meta_step(tasks)
        assert len(losses) == 1

    def test_anil(self, params):
        anil = ANIL(params)
        tasks = [(np.random.randn(3, 4), np.random.randn(3, 1),
                  np.random.randn(2, 4), np.random.randn(2, 1))]
        loss = anil.meta_step(tasks)
        assert loss > 0

    def test_protonets(self):
        pn = ProtoNets(MetaParams(input_dim=4, hidden_dim=8, output_dim=3))
        x = np.random.randn(6, 4)
        y = np.array([0, 0, 1, 1, 2, 2])
        protos = pn.compute_prototypes(x, y, 3)
        assert protos.shape == (3, 8)
        preds = pn.predict(np.random.randn(2, 4), protos)
        assert preds.shape == (2,)


class TestContinual:
    @pytest.fixture
    def params(self):
        return ContinualParams(input_dim=4, output_dim=1)

    def test_ewc(self, params):
        ewc = EWC(params)
        x = np.random.randn(4)
        out = ewc.forward(x)
        assert out.shape == (1,)

    def test_si(self, params):
        si = SI(params)
        si.after_task()
        assert si.omega[0].shape == (4, 64)

    def test_packnet(self, params):
        pn = PackNet(params)
        pn.prune()
        assert pn is not None

    def test_progressivenn(self, params):
        pnn = ProgressiveNN(params)
        pnn.add_column()
        assert len(pnn.columns) == 1


# ─── Bloc D ────────────────────────────────────────────────────────

class TestSwarm:
    def test_pso(self):
        pso = PSO(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        pso.run()
        assert pso.generation == 5

    def test_aco(self):
        aco = ACO(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=3))
        aco.run()

    def test_abc(self):
        abc = ABC(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        abc.run()

    def test_cs(self):
        cs = CS(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        cs.run()

    def test_gwo(self):
        gwo = GWO(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        gwo.run()

    def test_woa(self):
        woa = WOA(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        woa.run()

    def test_goa(self):
        goa = GOA(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        goa.run()

    def test_mfo(self):
        mfo = MFO(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        mfo.run()

    def test_sca(self):
        sca = SCA(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        sca.run()

    def test_ssa(self):
        ssa = SSA(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        ssa.run()

    def test_ffa(self):
        ffa = FFA(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        ffa.run()

    def test_ba(self):
        ba = BA(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        ba.run()

    def test_fss(self):
        fss = FSS(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        fss.run()

    def test_sso(self):
        sso = SSO(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        sso.run()

    def test_hba(self):
        hba = HBA(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        hba.run()

    def test_eho(self):
        eho = EHO(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        eho.run()

    def test_aha(self):
        aha = AHA(_sphere, params=SwarmParams(dimensions=3, population_size=10, generations=5))
        aha.run()


# ─── Bloc E ────────────────────────────────────────────────────────

class TestImmune:
    def test_clonalg(self):
        c = CLONALG(_sphere, params=ImmuneParams(population_size=10, generations=3))
        best, fit = c.run()
        assert fit < float("inf")

    def test_negative_selection(self):
        ns = NegativeSelection(params=ImmuneParams(dimensions=3))
        self_samples = np.random.randn(5, 3)
        ns.generate_detectors(self_samples, n_detectors=10)
        assert len(ns.detectors) <= 10

    def test_ainet(self):
        a = AINET(params=ImmuneParams(dimensions=3))
        data = np.random.randn(10, 3)
        net = a.train(data, epochs=3)
        assert len(net) > 0

    def test_danger_theory(self):
        dt = DangerTheory()
        result = dt.receive_signal(0.8)
        assert result is True
        assert dt.immune_response() == "adaptive_response"


# ─── Bloc F ────────────────────────────────────────────────────────

class TestEndocrine:
    def test_hormonal_system(self):
        hs = HormonalSystem()
        hs.update(stress=0.5, reward=0.8, social=0.3)
        assert hs.get_drive("cortisol") > 0
        assert hs.get_drive("dopamine") > 0
        assert hs.get_drive("oxytocin") > 0

    def test_cortisol(self):
        fx = Cortisol.effect(5.0)
        assert "stress_response" in fx

    def test_dopamine(self):
        fx = Dopamine.effect(5.0)
        assert "motivation" in fx

    def test_oxytocin(self):
        fx = Oxytocin.effect(5.0)
        assert "trust" in fx


# ─── Bloc G ────────────────────────────────────────────────────────

class TestOEE:
    def test_poet(self):
        def env_gen(seed):
            return np.array([seed])
        poet = POET(evaluate=lambda x, e: float(np.sum(x ** 2)), env_generate=env_gen,
                    params=OEEParams(population_size=5, generations=3, dimensions=2))
        poet.run()

    def test_enhanced_poet(self):
        def env_gen(seed):
            return np.array([seed])
        epoet = EnhancedPOET(evaluate=lambda x, e: float(np.sum(x ** 2)),
                              env_generate=env_gen, env_mutate=lambda e: e + 0.1,
                              params=OEEParams(population_size=5, generations=3, dimensions=2))
        epoet.run()

    def test_omni(self):
        omni = OMNI()
        assert omni is not None


# ─── Bloc H ────────────────────────────────────────────────────────

class TestCoevolution:
    def test_coevolution(self):
        ce = Coevolution(evaluate_a=lambda a, b: -float(np.sum((a - b) ** 2)),
                         params=CoevParams(pop_a_size=5, pop_b_size=5, dimensions=3, generations=3))
        ce.run()

    def test_predator_prey(self):
        pp = PredatorPrey(evaluate_a=lambda a, b: -float(np.sum((a - b) ** 2)),
                          params=CoevParams(pop_a_size=5, pop_b_size=5, dimensions=3, generations=3))
        pp.run()

    def test_hall_of_fame(self):
        hof = HallOfFame(max_size=10)
        hof.add(np.array([1.0, 2.0]), 0.9)
        hof.add(np.array([3.0, 4.0]), 0.95)
        assert len(hof.get_diverse_set(2)) == 2


# ─── Bloc I ────────────────────────────────────────────────────────

class TestQD:
    def test_map_elites(self):
        me = MAPElites(evaluate=_sphere, describe=lambda x: np.array([x[0], x[1]]),
                       params=QDParams(dimensions=2, population_size=10, generations=5, behaviour_dim=2))
        me.run()

    def test_cvt_map_elites(self):
        cvt = CVT_MAPElites(evaluate=_sphere, describe=lambda x: np.array([x[0], x[1]]),
                            n_centroids=10, params=QDParams(dimensions=2, population_size=10, generations=5, behaviour_dim=2))
        cvt.run()

    def test_aurora(self):
        aur = AURORA(params=QDParams(dimensions=2, population_size=10, generations=3))
        assert aur is not None

    def test_sail(self):
        sail = SAIL(params=QDParams(dimensions=2, population_size=10, generations=3))
        assert sail is not None


# ─── Bloc J ────────────────────────────────────────────────────────

class TestMultiObjective:
    def test_nsga2(self):
        nsga2 = NSGA2(_sphere_mo, params=MOParams(dimensions=3, population_size=10, generations=5))
        nsga2.run()

    def test_nsga3(self):
        nsga3 = NSGA3(_sphere_mo, params=MOParams(dimensions=3, population_size=10, generations=5))
        nsga3.run()

    def test_moead(self):
        moead = MOEAD(_sphere_mo, params=MOParams(dimensions=3, population_size=10, generations=5))
        moead.run()

    def test_ibea(self):
        ibea = IBEA(_sphere_mo, params=MOParams(dimensions=3, population_size=10, generations=5))
        ibea.run()

    def test_hype(self):
        hype = HypE(_sphere_mo)
        assert hype.n_samples == 10000


# ─── Evolution Engine ──────────────────────────────────────────────

class TestEvolutionEngine:
    def test_create(self):
        eng = EvolutionEngine()
        assert eng is not None

    def test_list_algorithms(self):
        eng = EvolutionEngine()
        algos = eng.list_algorithms()
        assert "ga" in algos
        assert len(algos) >= 15

    def test_process_run_ga(self):
        eng = EvolutionEngine()
        r = eng.process({"action": "run", "algorithm": "ga", "params": {"population_size": 10, "generations": 2}})
        assert r["success"] is True

    def test_process_run_pso(self):
        eng = EvolutionEngine()
        r = eng.process({"action": "run", "algorithm": "pso", "params": {"dimensions": 3, "population_size": 10, "generations": 2}})
        assert r["success"] is True

    def test_process_list(self):
        eng = EvolutionEngine()
        r = eng.process({"action": "list"})
        assert r["success"] is True

    def test_process_stats(self):
        eng = EvolutionEngine()
        r = eng.process({"action": "stats"})
        assert r["success"] is True

    def test_process_unknown(self):
        eng = EvolutionEngine()
        r = eng.process({"action": "nonexistent"})
        assert r["success"] is False

    def test_process_bad_input(self):
        eng = EvolutionEngine()
        r = eng.process("bad")
        assert r["success"] is False

    def test_run_unknown_algo(self):
        eng = EvolutionEngine()
        r = eng.process({"action": "run", "algorithm": "nonexistent"})
        assert r["success"] is False
