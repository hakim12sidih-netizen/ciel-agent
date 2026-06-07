from __future__ import annotations

import pytest
from ciel.lm.cot import ChainOfThought, MultiChainReasoning, ReasoningStep
from ciel.lm.tot import TreeOfThoughts, ThoughtNode, SearchStrategy
from ciel.lm.got import GraphOfThoughts, ThoughtGraph
from ciel.lm.ntp import NeuralTheoremProver
from ciel.lm.reasoning import ReasoningEngine, ReasoningMode, ReasoningResult
from ciel.logics.core import ClassicalLogic, Formula, FormulaType


class TestChainOfThought:
    def test_reason(self):
        cot = ChainOfThought(max_steps=3)
        steps = cot.reason("Résoudre 2+2")
        assert len(steps) > 0
        assert isinstance(steps[0], ReasoningStep)
        assert cot.final_answer

    def test_aggregate(self):
        cot = ChainOfThought(max_steps=2)
        cot.reason("Test")
        agg = cot.aggregate()
        assert "1." in agg

    def test_confidence(self):
        cot = ChainOfThought(max_steps=3)
        cot.reason("Problème")
        assert 0 < cot.confidence_score() <= 1.0


class TestMultiChainReasoning:
    def test_multi_reason(self):
        mcr = MultiChainReasoning(n_chains=3, max_steps=3)
        chains = mcr.reason("Problème")
        assert len(chains) == 3
        assert len(chains[0]) > 0

    def test_majority_vote(self):
        mcr = MultiChainReasoning(n_chains=2, max_steps=2)
        mcr.reason("Test")
        vote = mcr.majority_vote()
        assert isinstance(vote, str)


class TestTreeOfThoughts:
    def test_bfs(self):
        tot = TreeOfThoughts(max_depth=2, branching_factor=2, strategy=SearchStrategy.BFS)
        best = tot.search("Problème")
        assert isinstance(best, ThoughtNode)

    def test_dfs(self):
        tot = TreeOfThoughts(max_depth=2, branching_factor=2, strategy=SearchStrategy.DFS)
        best = tot.search("Test")
        assert best is not None

    def test_beam(self):
        tot = TreeOfThoughts(max_depth=2, branching_factor=2, strategy=SearchStrategy.BEAM, beam_width=2)
        best = tot.search("Test")
        assert best is not None

    def test_mcts(self):
        tot = TreeOfThoughts(max_depth=2, branching_factor=2, strategy=SearchStrategy.MCTS)
        best = tot.search("Test")
        assert best is not None

    def test_evaluator(self):
        tot = TreeOfThoughts()
        tot.set_evaluator(lambda t: 0.5)
        best = tot.search("Test")
        assert best.value == 0.5

    def test_ucb_score(self):
        node = ThoughtNode(id="test", content="test", visits=5, value=3.0)
        score = node.ucb_score()
        assert score > 0

    def test_inf_ucb(self):
        node = ThoughtNode(id="test", content="test", visits=0)
        assert node.ucb_score() == float("inf")


class TestGraphOfThoughts:
    def test_reason(self):
        got = GraphOfThoughts()
        graph = got.reason("Problème", max_steps=3)
        assert isinstance(graph, ThoughtGraph)
        assert len(graph.nodes) > 0

    def test_best_path(self):
        got = GraphOfThoughts()
        got.reason("Test", max_steps=2)
        path = got.best_path()
        assert len(path) > 0

    def test_merge(self):
        got = GraphOfThoughts()
        got.reason("Test", max_steps=2)
        n_before = len(got.graph.nodes)
        got.graph.merge_nodes(list(got.graph.nodes.keys())[:2])
        assert len(got.graph.nodes) < n_before


class TestThoughtGraph:
    def test_add_node(self):
        g = ThoughtGraph()
        vid = g.add_node("test")
        assert vid in g.nodes

    def test_add_edge(self):
        g = ThoughtGraph()
        a = g.add_node("a")
        b = g.add_node("b")
        g.add_edge(a, b)
        assert len(g.edges) == 1

    def test_topo_sort(self):
        g = ThoughtGraph()
        a = g.add_node("a")
        b = g.add_node("b")
        c = g.add_node("c")
        g.add_edge(a, b)
        g.add_edge(b, c)
        topo = g.topo_sort()
        assert len(topo) == 3

    def test_merge_nodes(self):
        g = ThoughtGraph()
        a = g.add_node("a")
        b = g.add_node("b")
        g.add_edge(a, b)
        mid = g.merge_nodes([a, b])
        assert mid in g.nodes

    def test_get_children(self):
        g = ThoughtGraph()
        a = g.add_node("a")
        b = g.add_node("b")
        g.add_edge(a, b)
        children = g.get_children(a)
        assert len(children) == 1

    def test_get_parents(self):
        g = ThoughtGraph()
        a = g.add_node("a")
        b = g.add_node("b")
        g.add_edge(a, b)
        parents = g.get_parents(b)
        assert len(parents) == 1


class TestNeuralTheoremProver:
    @pytest.fixture
    def logic(self):
        return ClassicalLogic()

    @pytest.fixture
    def tautology(self):
        p = Formula(FormulaType.ATOM, ("P",), truth_value=True)
        return Formula(FormulaType.IMPLICATION, [
            p,
            Formula(FormulaType.IMPLICATION, [
                Formula(FormulaType.ATOM, ("Q",), truth_value=False),
                p,
            ]),
        ])

    def test_prove_tautology(self, logic, tautology):
        ntp = NeuralTheoremProver(logic=logic, max_depth=5)
        theorem = ntp.prove(tautology)
        assert theorem.is_proved

    def test_beam_search(self, logic, tautology):
        ntp = NeuralTheoremProver(logic=logic, max_depth=5, beam_width=3)
        theorem = ntp.prove(tautology)
        assert theorem.is_proved

    def test_batch_prove(self, logic, tautology):
        ntp = NeuralTheoremProver(logic=logic)
        p = Formula(FormulaType.ATOM, ("P",), truth_value=True)
        q = Formula(FormulaType.ATOM, ("Q",), truth_value=False)
        theorems = ntp.batch_prove([tautology, p, q])
        assert len(theorems) == 3

    def test_proved_count(self, logic, tautology):
        ntp = NeuralTheoremProver(logic=logic)
        ntp.batch_prove([tautology])
        assert ntp.proved_count() >= 1

    def test_average_confidence(self, logic, tautology):
        ntp = NeuralTheoremProver(logic=logic)
        ntp.batch_prove([tautology])
        assert ntp.average_confidence() > 0


class TestReasoningEngine:
    @pytest.fixture
    def engine(self):
        return ReasoningEngine()

    def test_cot(self, engine):
        result = engine.reason("Test CoT", mode=ReasoningMode.COT)
        assert isinstance(result, ReasoningResult)
        assert result.mode == ReasoningMode.COT

    def test_multi_chain(self, engine):
        result = engine.reason("Test", mode=ReasoningMode.MULTI_CHAIN)
        assert result.mode == ReasoningMode.MULTI_CHAIN

    def test_tot(self, engine):
        result = engine.reason("Test ToT", mode=ReasoningMode.TOT)
        assert result.mode == ReasoningMode.TOT

    def test_got(self, engine):
        result = engine.reason("Test GoT", mode=ReasoningMode.GOT)
        assert result.mode == ReasoningMode.GOT

    def test_react(self, engine):
        result = engine.reason("Test ReAct", mode=ReasoningMode.REACT)
        assert result.mode == ReasoningMode.REACT

    def test_star(self, engine):
        result = engine.reason("Test STaR", mode=ReasoningMode.STAR)
        assert result.mode == ReasoningMode.STAR

    def test_rap(self, engine):
        result = engine.reason("Test RAP", mode=ReasoningMode.RAP)
        assert result.mode == ReasoningMode.RAP

    def test_custom_mode(self, engine):
        def handler(problem, **kw):
            return ReasoningResult(
                answer="custom", mode=ReasoningMode.COT,
                steps=[], confidence=0.5,
            )
        engine.register_handler(ReasoningMode.COT, handler)
        result = engine.reason("test", mode=ReasoningMode.COT)
        assert result.answer == "custom"
