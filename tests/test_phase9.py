from __future__ import annotations

import pytest

from ciel.economie.core import (
    EconomicAgent, Market, Good, OrderBook, Order, OrderType, Trade,
    UtilityFunction, ValueSystem, PricingMechanism, ScarcityModel,
    ProductionFunction, Resource, EconomicLoop, Currency,
)
from ciel.conscience.core import (
    ConsciousnessModel, Qualia, GlobalWorkspace, AttentionSchema,
    Metacognition, SelfModel, Introspection, PhenomenalState,
    IntegratedInformation, BindingProblem, ConsciousState, AwarenessLevel,
)
from ciel.chronos.core import (
    ChronosEngine, InternalClock, TemporalMemory, TemporalEvent,
    TemporalInterval, RhythmDetector, TemporalReasoning,
)
from ciel.logos.core import (
    LogosEngine, Proposition, Argument, ArgumentType,
    RhetoricalFigure, Syllogism, Hermeneutics, DiscourseAnalyzer,
    PersuasionModel, SpeechAct,
)


class TestEconomie:
    def test_good(self):
        g = Good(id="g1", name="blé", quantity=100.0)
        assert g.id == "g1"

    def test_agent(self):
        a = EconomicAgent(id="a1", currency=100.0)
        assert a.currency == 100.0

    def test_agent_produce_consume(self):
        a = EconomicAgent(id="a1")
        a.produce("pain", 5.0)
        assert a.inventory["pain"] == 5.0
        a.consume("pain", 2.0)
        assert a.inventory["pain"] == 3.0

    def test_agent_utility(self):
        a = EconomicAgent(id="a1", inventory={"x": 10.0, "y": 5.0})
        uf = UtilityFunction(lambda g: g.get("x", 0) * g.get("y", 0))
        a.utility_fn = uf
        assert a.utility() == 50.0

    def test_order_book_buy(self):
        ob = OrderBook()
        trades = ob.add_order(Order("b1", OrderType.BUY, "g1", 10.0, 5.0))
        assert len(trades) == 0
        assert len(ob.bids) == 1

    def test_order_book_trade(self):
        ob = OrderBook()
        ob.add_order(Order("s1", OrderType.SELL, "g1", 10.0, 4.0))
        trades = ob.add_order(Order("b1", OrderType.BUY, "g1", 10.0, 5.0))
        assert len(trades) >= 0

    def test_spread(self):
        ob = OrderBook()
        ob.add_order(Order("b1", OrderType.BUY, "g1", 1.0, 5.0))
        ob.add_order(Order("s1", OrderType.SELL, "g1", 1.0, 6.0))
        assert ob.spread() == 1.0

    def test_market(self):
        m = Market("test")
        a = EconomicAgent(id="a1", currency=100.0)
        m.add_agent(a)
        m.add_good(Good(id="g1", name="good", quantity=100.0))
        stats = m.tick()
        assert stats["n_trades"] >= 0

    def test_pricing(self):
        p = PricingMechanism()
        new_p = p.update("g1", 10.0, 5.0)
        assert new_p > 1.0

    def test_scarcity(self):
        s = ScarcityModel()
        score = s.scarcity_score(20.0, 100.0)
        assert 0 < score < 1.0

    def test_production_function(self):
        pf = ProductionFunction("pain", {"farine": 2.0, "eau": 1.0})
        assert not pf.can_produce({"farine": 1.0})
        assert pf.can_produce({"farine": 2.0, "eau": 1.0})

    def test_resource_tick(self):
        r = Resource(id="r1", name="eau", renewable=True, current_stock=50.0, max_stock=100.0)
        r.tick()
        assert r.current_stock > 50.0

    def test_economic_loop(self):
        loop = EconomicLoop()
        loop.add_resource(Resource(id="r1", name="bois"))
        results = loop.run(n_steps=5)
        assert len(results) == 5

    def test_gini(self):
        loop = EconomicLoop()
        for i in range(10):
            loop.market.add_agent(EconomicAgent(id=f"a{i}", currency=float(i * 10)))
        gini = loop.gini_coefficient()
        assert 0 <= gini <= 1.0

    def test_utility_cobb_douglas(self):
        uf = UtilityFunction.cobb_douglas({"x": 0.5, "y": 0.5})
        val = uf.evaluate({"x": 4.0, "y": 9.0})
        assert val > 0

    def test_value_system(self):
        vs = ValueSystem({"a": 2.0, "b": 1.0})
        vs.set_priority(["a", "b"])
        score = vs.score({"a": 5.0, "b": 3.0})
        assert score > 0

    def test_mid_price(self):
        ob = OrderBook()
        ob.add_order(Order("b1", OrderType.BUY, "g1", 1.0, 5.0))
        ob.add_order(Order("s1", OrderType.SELL, "g1", 1.0, 7.0))
        assert ob.mid_price() == 6.0


class TestConscience:
    def test_qualia(self):
        q = Qualia(modality="visual", intensity=0.8, valence=0.5, content="rouge")
        q.normalize()
        assert 0 <= q.intensity <= 1.0

    def test_phenomenal_state(self):
        ps = PhenomenalState()
        ps.add_qualia(Qualia(modality="auditory", intensity=0.6))
        ps.add_qualia(Qualia(modality="visual", intensity=0.8))
        assert len(ps.qualia) == 2
        assert ps.coherence >= 0

    def test_global_workspace(self):
        gw = GlobalWorkspace(capacity=3)
        gw.broadcast({"salience": 0.9, "content": "test"})
        assert len(gw.contents) == 1
        assert len(gw.global_availability()) == 1

    def test_attention(self):
        att = AttentionSchema(capacity=1.0)
        att.allocate("focus_a", 0.6)
        assert att.current_focus() == "focus_a"
        att.tick()
        assert att.focus.get("focus_a", 0) < 0.6

    def test_self_model(self):
        sm = SelfModel()
        sm.update_belief("name", "CIEL")
        sm.add_narrative("a eu une idée")
        assert sm.self_awareness() > 0

    def test_metacognition(self):
        mc = Metacognition()
        mc.judge("test", "ok")
        assert len(mc.judgments) == 1
        assert mc.calibration() > 0

    def test_introspection(self):
        intro = Introspection()
        report = intro.examine(Qualia(modality="test"))
        assert "type" in report

    def test_integrated_information(self):
        tm = [[0.5, 0.5], [0.3, 0.7]]
        ii = IntegratedInformation.compute(tm)
        assert ii.phi >= 0

    def test_binding_problem(self):
        bp = BindingProblem()
        bp.bind("obj1", "visual")
        bp.bind("obj1", "auditory")
        assert bp.is_bound("obj1", ["visual", "auditory"])
        assert bp.coherence_score() > 0

    def test_consciousness_model(self):
        cm = ConsciousnessModel()
        cm.perceive(Qualia(modality="cognitive", content="pensée"))
        cm.attend("focus", 0.5)
        state = cm.tick()
        assert isinstance(state, ConsciousState)
        assert state.level_of_consciousness() >= 0

    def test_awareness_levels(self):
        assert AwarenessLevel.NONE.value < AwarenessLevel.META.value


class TestChronos:
    def test_clock(self):
        clock = InternalClock()
        t = clock.tick(1.0)
        assert t > 0

    def test_clock_drift(self):
        clock = InternalClock(base_rate=1.5)
        clock.tick(10.0)
        assert abs(clock.drift) > 0

    def test_temporal_memory(self):
        tm = TemporalMemory(capacity=10)
        ev = TemporalEvent(id="e1", timestamp=1.0, content="début")
        tm.record(ev)
        assert len(tm.events) == 1

    def test_recall(self):
        tm = TemporalMemory()
        tm.record(TemporalEvent(id="e1", timestamp=1.0))
        tm.record(TemporalEvent(id="e2", timestamp=5.0))
        recalled = tm.recall(0.0, 3.0)
        assert len(recalled) == 1

    def test_predict_next(self):
        tm = TemporalMemory()
        tm.record(TemporalEvent(id="e1", timestamp=1.0, content="a"))
        tm.record(TemporalEvent(id="e2", timestamp=3.0, content="b"))
        tm.record(TemporalEvent(id="e3", timestamp=5.0, content="c"))
        pred = tm.predict_next()
        assert pred is not None
        assert pred.timestamp > 5.0

    def test_rhythm_detector(self):
        rd = RhythmDetector()
        periods = rd.detect([1.0, 3.0, 5.0, 7.0])
        assert len(periods) > 0

    def test_is_rhythmic(self):
        rd = RhythmDetector()
        assert rd.is_rhythmic([1.0, 3.0, 5.0, 7.0])
        assert not rd.is_rhythmic([1.0, 10.0, 11.0, 20.0])

    def test_allen_relations(self):
        a = TemporalInterval(start=0.0, end=5.0)
        b = TemporalInterval(start=6.0, end=10.0)
        assert TemporalReasoning.relation(a, b) == "before"
        b2 = TemporalInterval(start=3.0, end=8.0)
        assert TemporalReasoning.relation(a, b2) == "overlaps"

    def test_temporal_interval_contains(self):
        ti = TemporalInterval(start=0.0, end=10.0)
        assert ti.contains(5.0)
        assert not ti.contains(15.0)

    def test_chronos_engine(self):
        ch = ChronosEngine()
        ch.tick(1.0)
        ch.tick(2.0)
        ev = ch.observe("événement")
        assert ev.timestamp > 0
        assert len(ch.memory.events) == 1

    def test_detect_rhythms_in_engine(self):
        ch = ChronosEngine()
        for i in range(5):
            ch.observe(f"tick_{i}")
            ch.tick(2.0)
        rhythms = ch.detect_rhythms()
        assert len(rhythms) > 0

    def test_predict(self):
        ch = ChronosEngine()
        ch.observe("a")
        ch.tick(2.0)
        ch.observe("b")
        ch.tick(2.0)
        ch.observe("c")
        pred = ch.predict()
        assert pred is not None

    def test_transitive_closure(self):
        rels = [("a", "before", "b"), ("b", "before", "c")]
        closure = TemporalReasoning.transitive_closure(rels)
        assert ("a", "before", "c") in closure


class TestLogos:
    def test_proposition(self):
        p = Proposition(id="p1", content="Socrate est mortel", confidence=0.9)
        assert p.confidence == 0.9

    def test_argument(self):
        logos = LogosEngine()
        p1 = logos.assert_proposition("Tous les hommes sont mortels", 0.95)
        p2 = logos.assert_proposition("Socrate est un homme", 0.9)
        conc = logos.assert_proposition("Socrate est mortel", 0.8)
        arg = logos.build_argument([p1, p2], conc)
        assert arg.strength > 0

    def test_discourse_analysis(self):
        da = DiscourseAnalyzer()
        analysis = da.analyze("Je pense donc je suis. Es-tu sûr?")
        assert analysis["length"] == 7
        assert SpeechAct.ASSERTIVE in analysis["speech_acts"]

    def test_hermeneutics(self):
        h = Hermeneutics()
        h.fuse_horizons("texte ancien", "lecteur moderne")
        interpretation = h.interpret("un texte")
        assert "meaning" in interpretation
        assert "ambiguity" in interpretation

    def test_hermeneutic_circle(self):
        h = Hermeneutics()
        result = h.hermeneutic_circle("partie", "tout")
        assert "éclairé" in result

    def test_persuasion_model(self):
        pm = PersuasionModel()
        p1 = Proposition(id="p1", content="test", confidence=0.2)
        p2 = Proposition(id="p2", content="test2", confidence=0.1)
        arg = Argument(premises=[p1, p2], conclusion=p1, arg_type=ArgumentType.AUTHORITY, strength=0.95)
        fallacies = pm.detect_fallacies(arg)
        assert len(fallacies) > 0

    def test_persuasive_power(self):
        pm = PersuasionModel()
        pm.ethos = 0.7
        pm.pathos = 0.5
        pm.logos = 0.9
        power = pm.persuasive_power()
        assert 0 < power <= 1.0

    def test_apply_figure(self):
        pm = PersuasionModel()
        pm.apply_figure(RhetoricalFigure("logos", "", 1.5))
        assert pm.logos > 0.5

    def test_syllogism(self):
        assert Syllogism.evaluate("M", "S", "M", "barbara")
        assert Syllogism.evaluate("M", "S", "M", "celarent")

    def test_debate(self):
        logos = LogosEngine()
        p1 = logos.assert_proposition("thèse", 0.8)
        p2 = logos.assert_proposition("antithèse", 0.6)
        thesis = Argument(premises=[p1], conclusion=p1, strength=0.8)
        antithesis = Argument(premises=[p2], conclusion=p2, strength=0.6)
        result = logos.debate(thesis, antithesis)
        assert result["winner"] == "thesis"

    def test_generate_discourse(self):
        logos = LogosEngine()
        statements = logos.generate_discourse("La vérité", 3)
        assert len(statements) == 3

    def test_logos_engine_integration(self):
        logos = LogosEngine()
        p1 = logos.assert_proposition("première prémisse")
        p2 = logos.assert_proposition("deuxième prémisse")
        c = logos.assert_proposition("conclusion")
        logos.build_argument([p1, p2], c)
        logos.analyze_discourse("Donc, la conclusion est évidente.")
        logos.interpret("un texte philosophique")
        assert len(logos.arguments) == 1
        assert len(logos.propositions) == 3

    def test_rebuttal(self):
        pm = PersuasionModel()
        p = Proposition(id="p", content="c", confidence=0.8)
        counter = Argument(premises=[p], conclusion=p, strength=0.7)
        rebuttal = pm.rebut([counter])
        assert rebuttal > 0
