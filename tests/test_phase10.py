from __future__ import annotations

import pytest
from ciel.neuro_symbolic.core import (
    NeuroSymbolicNetwork, NeuralSymbolicBridge, Symbol, Concept,
    SymbolGrounding, HybridReasoner, AbstractionEngine,
    RepresentationType,
)
from ciel.brain.core import CIELBrain, CIELState, ProcessStatus
from ciel.logics.core import ClassicalLogic, Formula, FormulaType


class TestSymbol:
    def test_create(self):
        s = Symbol(name="Socrate")
        assert s.name == "Socrate"

    def test_to_formula(self):
        s = Symbol(name="mortel", args=["x"])
        f = s.to_formula()
        assert f.type == FormulaType.ATOM

    def test_embedding(self):
        s = Symbol(name="test", embedding=[0.1, 0.2, 0.3])
        assert len(s.embedding) == 3


class TestConcept:
    def test_create(self):
        c = Concept(id="c1", name="animal")
        assert c.name == "animal"

    def test_distance(self):
        c = Concept(id="c1", name="test", prototype=[1.0, 0.0, 0.0])
        d = c.distance([1.0, 0.0, 0.0])
        assert d == 0.0

    def test_update_prototype(self):
        c = Concept(id="c1", name="test")
        c.add_exemplar([1.0, 2.0])
        c.add_exemplar([3.0, 4.0])
        assert c.prototype == [2.0, 3.0]

    def test_add_exemplar(self):
        c = Concept(id="c1", name="test")
        c.add_exemplar([0.5, 0.5])
        assert len(c.exemplars) == 1


class TestSymbolGrounding:
    def test_ground(self):
        sg = SymbolGrounding(dim=3)
        vec = sg.ground("chat")
        assert len(vec) == 3

    def test_ground_with_vector(self):
        sg = SymbolGrounding()
        sg.ground("chat", [1.0, 0.0])
        assert sg.grounding_map["chat"] == [1.0, 0.0]

    def test_similarity(self):
        sg = SymbolGrounding(dim=3)
        sg.ground("a", [1.0, 0.0, 0.0])
        sg.ground("b", [1.0, 0.0, 0.0])
        assert sg.similarity("a", "b") > 0.99

    def test_grounding_fn(self):
        sg = SymbolGrounding()
        sg.set_grounding_fn(lambda s: [1.0, 1.0])
        vec = sg.ground("x")
        assert vec == [1.0, 1.0]


class TestNeuralSymbolicBridge:
    def test_symbolize(self):
        bridge = NeuralSymbolicBridge()
        sym = bridge.symbolize([0.1, 0.2])
        assert sym.name.startswith("sym_")
        assert sym.embedding == [0.1, 0.2]

    def test_concept_from_exemplars(self):
        bridge = NeuralSymbolicBridge()
        c = bridge.concept_from_exemplars("forme", [[1.0, 0.0], [0.9, 0.1]])
        assert len(c.exemplars) == 2

    def test_classify(self):
        bridge = NeuralSymbolicBridge()
        bridge.concept_from_exemplars("A", [[1.0, 0.0], [0.9, 0.1]])
        bridge.concept_from_exemplars("B", [[0.0, 1.0], [0.1, 0.9]])
        cls = bridge.classify([0.95, 0.05])
        assert cls == "A"

    def test_evaluate_symbolic(self):
        bridge = NeuralSymbolicBridge()
        sym = Symbol(name="P", embedding=[1.0])
        result = bridge.evaluate_symbolic(sym)
        assert isinstance(result, bool)


class TestHybridReasoner:
    def test_reason_hybrid(self):
        bridge = NeuralSymbolicBridge()
        reasoner = HybridReasoner(bridge)
        p = Symbol(name="P", embedding=[1.0, 0.0])
        q = Symbol(name="Q", embedding=[0.5, 0.5])
        result, conf = reasoner.reason_hybrid([p], q)
        assert isinstance(result, bool)
        assert 0 <= conf <= 1.0


class TestAbstractionEngine:
    def test_abstract(self):
        engine = AbstractionEngine()
        c1 = Concept(id="c1", name="chat", prototype=[1.0, 0.0])
        c2 = Concept(id="c2", name="chien", prototype=[0.0, 1.0])
        abstract = engine.abstract([c1, c2], "animal")
        assert abstract.abstraction_level == 1
        assert abstract.name == "animal"

    def test_get_layer(self):
        engine = AbstractionEngine()
        c = Concept(id="c1", name="test", prototype=[0.5])
        engine.abstract([c], "niveau1")
        layer = engine.get_layer(1)
        assert len(layer) == 1


class TestNeuroSymbolicNetwork:
    def test_create(self):
        nsn = NeuroSymbolicNetwork(input_dim=4)
        assert nsn.input_dim == 4

    def test_create_symbol(self):
        nsn = NeuroSymbolicNetwork()
        sym = nsn.create_symbol("liberté", [0.5, 0.5])
        assert sym.name == "liberté"

    def test_create_concept(self):
        nsn = NeuroSymbolicNetwork()
        c = nsn.create_concept("vert", [[0.0, 1.0, 0.0], [0.1, 0.9, 0.1]])
        assert c.name == "vert"

    def test_forward(self):
        nsn = NeuroSymbolicNetwork(input_dim=3)
        output = nsn.forward([0.5, 0.5, 0.0])
        assert "vector" in output
        assert "symbol" in output
        assert "concept" in output

    def test_grounding_similarity(self):
        nsn = NeuroSymbolicNetwork()
        nsn.create_symbol("a", [1.0, 0.0])
        nsn.create_symbol("b", [1.0, 0.0])
        sim = nsn.grounding_similarity("a", "b")
        assert sim > 0.99

    def test_register_processor(self):
        nsn = NeuroSymbolicNetwork()
        results = []
        nsn.register_processor(lambda x: results.append(x))
        nsn.forward([0.1, 0.1])
        assert len(results) == 1

    def test_reason(self):
        nsn = NeuroSymbolicNetwork()
        p = nsn.create_symbol("P", [1.0, 0.0])
        q = nsn.create_symbol("Q", [1.0, 0.0])
        result, conf = nsn.reason([p], q)
        assert 0 <= conf <= 1.0


class TestCIELBrain:
    def test_create(self):
        brain = CIELBrain()
        assert brain.name == "CIEL v∞.3"
        assert brain.state.status == ProcessStatus.IDLE

    def test_load_module(self):
        brain = CIELBrain()
        brain.load_module("test", {"a": 1})
        assert brain.has_module("test")

    def test_get_module(self):
        brain = CIELBrain()
        brain.load_module("eco", {"value": 42})
        assert brain.get_module("eco")["value"] == 42

    def test_start_stop(self):
        brain = CIELBrain()
        brain.start()
        assert brain.state.status == ProcessStatus.RUNNING
        brain.stop()
        assert brain.state.status == ProcessStatus.TERMINATED

    def test_cycle(self):
        brain = CIELBrain()
        brain.start()
        result = brain.cycle()
        assert result["cycle"] == 1

    def test_pause_resume(self):
        brain = CIELBrain()
        brain.start()
        brain.pause()
        assert brain.state.status == ProcessStatus.PAUSED
        brain.resume()
        assert brain.state.status == ProcessStatus.RUNNING

    def test_register_hook(self):
        brain = CIELBrain()
        results = []
        brain.register_hook("test", lambda **kw: results.append(kw.get("msg")))
        brain.emit("test", msg="hello")
        assert "hello" in results

    def test_status_report(self):
        brain = CIELBrain()
        brain.load_module("m1", {})
        report = brain.status_report()
        assert "modules" in report
        assert "m1" in report["modules"]

    def test_process_pipeline(self):
        brain = CIELBrain()
        class Doubler:
            @staticmethod
            def process(x):
                return x * 2
        brain.load_module("d", Doubler())
        result = brain.process(5)
        assert result == 10

    def test_process_error_handling(self):
        brain = CIELBrain()
        class Broken:
            @staticmethod
            def process(x):
                raise ValueError("fail")
        brain.load_module("b", Broken())
        result = brain.process("x")
        assert result == "x"  # returns initial input on error

    def test_state_defaults(self):
        s = CIELState()
        assert s.status == ProcessStatus.IDLE
        assert s.n_cycles == 0
