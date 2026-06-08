from __future__ import annotations

import pytest
from ciel.analysis.core import (
    AnalysisMode, AnalysisDimension, Paradigm,
    AnalysisContext, AnalysisResult, AnalysisEngine,
    LabyrinthEngine, DescriptiveAnalyzer, DiagnosticAnalyzer,
    PredictiveAnalyzer, PrescriptiveAnalyzer, ExploratoryAnalyzer,
    CounterfactualAnalyzer, MetaAnalyzer, BaseAnalyzer,
)


class TestEnums:
    def test_analysis_mode_values(self):
        assert len(AnalysisMode) == 7
        assert AnalysisMode.DESCRIPTIF.value == "descriptif"
        assert AnalysisMode.DIAGNOSTIQUE.value == "diagnostique"
        assert AnalysisMode.PREDICTIF.value == "prédictif"
        assert AnalysisMode.PRESCRIPTIF.value == "prescriptif"
        assert AnalysisMode.EXPLORATOIRE.value == "exploratoire"
        assert AnalysisMode.CONTREFACTUEL.value == "contrefactuel"
        assert AnalysisMode.META.value == "méta"

    def test_analysis_dimension_values(self):
        assert len(AnalysisDimension) == 6
        assert AnalysisDimension.TEMPORELLE.value == "temporelle"
        assert AnalysisDimension.CAUSALE.value == "causale"

    def test_paradigm_values(self):
        assert len(Paradigm) == 6
        assert Paradigm.DEDUCTIF.value == "déductif"
        assert Paradigm.BAYESIEN.value == "bayésien"


class TestAnalysisContext:
    def test_create_empty(self):
        ctx = AnalysisContext()
        assert ctx.data == {}
        assert len(ctx.dimensions) == 6
        assert len(ctx.paradigms) == 2

    def test_create_with_data(self):
        ctx = AnalysisContext(data={"a": 1, "b": 2})
        assert ctx.get("a") == 1
        assert ctx.get("missing") is None

    def test_set_and_get(self):
        ctx = AnalysisContext()
        ctx.set("key", "value")
        assert ctx.get("key") == "value"

    def test_temporal_window(self):
        ctx = AnalysisContext(temporal_window=(0.0, 10.0))
        assert ctx.temporal_window == (0.0, 10.0)

    def test_with_dimensions(self):
        ctx = AnalysisContext(dimensions=[AnalysisDimension.CAUSALE])
        assert ctx.dimensions == [AnalysisDimension.CAUSALE]


class TestAnalysisResult:
    def test_create(self):
        r = AnalysisResult(
            mode=AnalysisMode.DESCRIPTIF,
            conclusion="test",
            confidence=0.8,
        )
        assert r.mode == AnalysisMode.DESCRIPTIF
        assert r.conclusion == "test"
        assert r.confidence == 0.8

    def test_is_reliable(self):
        r = AnalysisResult(mode=AnalysisMode.DESCRIPTIF, conclusion="x", confidence=0.8)
        assert r.is_reliable()
        r2 = AnalysisResult(mode=AnalysisMode.DESCRIPTIF, conclusion="x", confidence=0.5)
        assert not r2.is_reliable()

    def test_defaults(self):
        r = AnalysisResult(mode=AnalysisMode.META, conclusion="x", confidence=1.0)
        assert r.evidence == []
        assert r.alternatives == []
        assert r.recommendations == []
        assert r.metrics == {}


class TestDescriptiveAnalyzer:
    def test_analyze_empty(self):
        analyzer = DescriptiveAnalyzer()
        result = analyzer.analyze(AnalysisContext())
        assert result.mode == AnalysisMode.DESCRIPTIF
        assert "aucune donnée" in result.conclusion
        assert result.confidence == 0.0

    def test_analyze_with_data(self):
        analyzer = DescriptiveAnalyzer()
        ctx = AnalysisContext(data={"temp": 25.0, "pression": 1013})
        result = analyzer.analyze(ctx)
        assert result.mode == AnalysisMode.DESCRIPTIF
        assert "temp" in result.conclusion
        assert len(result.evidence) == 2
        assert result.confidence > 0

    def test_analyze_with_temporal_window(self):
        analyzer = DescriptiveAnalyzer()
        ctx = AnalysisContext(data={"x": 1}, temporal_window=(0.0, 5.0))
        result = analyzer.analyze(ctx)
        assert "période" in " ".join(result.evidence)


class TestDiagnosticAnalyzer:
    def test_analyze_empty(self):
        analyzer = DiagnosticAnalyzer()
        result = analyzer.analyze(AnalysisContext())
        assert result.mode == AnalysisMode.DIAGNOSTIQUE
        assert result.confidence == 0.1

    def test_analyze_with_causal_data(self):
        analyzer = DiagnosticAnalyzer()
        ctx = AnalysisContext(data={"a": 10.0, "b": 20.0})
        result = analyzer.analyze(ctx)
        assert "a → b" in result.conclusion or "causes" in result.conclusion

    def test_analyze_non_numeric(self):
        analyzer = DiagnosticAnalyzer()
        ctx = AnalysisContext(data={"a": "foo", "b": "bar"})
        result = analyzer.analyze(ctx)
        assert result.confidence == 0.1


class TestPredictiveAnalyzer:
    def test_analyze_empty(self):
        analyzer = PredictiveAnalyzer()
        result = analyzer.analyze(AnalysisContext())
        assert result.mode == AnalysisMode.PREDICTIF
        assert "aucune tendance" in result.conclusion

    def test_analyze_with_data(self):
        analyzer = PredictiveAnalyzer(horizon=2.0)
        ctx = AnalysisContext(data={"growth": 1.5, "rate": 0.5})
        result = analyzer.analyze(ctx)
        assert result.mode == AnalysisMode.PREDICTIF
        assert len(result.evidence) == 2
        assert result.metrics["horizon"] == 2.0

    def test_analyze_default_horizon(self):
        analyzer = PredictiveAnalyzer()
        assert analyzer.horizon == 1.0


class TestPrescriptiveAnalyzer:
    def test_analyze_empty(self):
        analyzer = PrescriptiveAnalyzer()
        ctx = AnalysisContext()
        result = analyzer.analyze(ctx)
        assert result.mode == AnalysisMode.PRESCRIPTIF

    def test_analyze_below_threshold(self):
        analyzer = PrescriptiveAnalyzer()
        ctx = AnalysisContext(data={"cpu": -5.0, "memory": 50.0})
        result = analyzer.analyze(ctx)
        assert any("augmenter" in r for r in result.recommendations)

    def test_analyze_above_threshold(self):
        analyzer = PrescriptiveAnalyzer()
        ctx = AnalysisContext(data={"cpu": 200.0})
        result = analyzer.analyze(ctx)
        assert any("réduire" in r for r in result.recommendations)

    def test_analyze_normal(self):
        analyzer = PrescriptiveAnalyzer()
        ctx = AnalysisContext(data={"cpu": 50.0})
        result = analyzer.analyze(ctx)
        assert any("maintenir" in r for r in result.recommendations)


class TestExploratoryAnalyzer:
    def test_analyze_empty(self):
        analyzer = ExploratoryAnalyzer()
        ctx = AnalysisContext()
        result = analyzer.analyze(ctx)
        assert result.mode == AnalysisMode.EXPLORATOIRE

    def test_analyze_with_data(self):
        analyzer = ExploratoryAnalyzer(n_scenarios=3)
        ctx = AnalysisContext(data={"x": 10.0, "y": 20.0})
        result = analyzer.analyze(ctx)
        assert result.metrics["n_scenarios"] == 3
        assert len(result.alternatives) == 3

    def test_custom_scenarios(self):
        analyzer = ExploratoryAnalyzer(n_scenarios=5)
        assert analyzer.n_scenarios == 5


class TestCounterfactualAnalyzer:
    def test_analyze_empty(self):
        analyzer = CounterfactualAnalyzer()
        ctx = AnalysisContext()
        result = analyzer.analyze(ctx)
        assert result.mode == AnalysisMode.CONTREFACTUEL
        assert "contrefactuel" in result.conclusion

    def test_analyze_numeric(self):
        analyzer = CounterfactualAnalyzer()
        ctx = AnalysisContext(data={"x": 10.0, "y": -5.0})
        result = analyzer.analyze(ctx)
        assert len(result.evidence) == 2

    def test_analyze_boolean(self):
        analyzer = CounterfactualAnalyzer()
        ctx = AnalysisContext(data={"active": True, "paused": False})
        result = analyzer.analyze(ctx)
        assert len(result.evidence) == 2


class TestMetaAnalyzer:
    def test_analyze(self):
        analyzer = MetaAnalyzer()
        ctx = AnalysisContext(
            data={"a": 1, "b": 2, "c": 3},
            dimensions=[AnalysisDimension.CAUSALE, AnalysisDimension.QUANTITATIVE],
            paradigms=[Paradigm.DEDUCTIF, Paradigm.ABDUCTIF],
        )
        result = analyzer.analyze(ctx)
        assert result.mode == AnalysisMode.META
        assert result.confidence == 0.95
        assert "3 variables" in " ".join(result.evidence)
        assert result.metrics["n_dimensions"] == 2
        assert result.metrics["n_paradigms"] == 2


class TestAnalysisEngine:
    def test_create(self):
        engine = AnalysisEngine()
        assert len(engine.get_history()) == 0

    def test_analyze_all_modes(self):
        engine = AnalysisEngine()
        ctx = AnalysisContext(data={"x": 10.0, "y": 20.0})
        results = engine.analyze(ctx)
        assert len(results) == 7

    def test_analyze_single_mode(self):
        engine = AnalysisEngine()
        ctx = AnalysisContext(data={"x": 1.0})
        results = engine.analyze(ctx, modes=[AnalysisMode.DESCRIPTIF])
        assert len(results) == 1
        assert results[0].mode == AnalysisMode.DESCRIPTIF

    def test_analyze_all_dict(self):
        engine = AnalysisEngine()
        ctx = AnalysisContext(data={"x": 1.0})
        by_mode = engine.analyze_all(ctx)
        assert len(by_mode) == 7
        assert AnalysisMode.DESCRIPTIF in by_mode

    def test_synthesize(self):
        engine = AnalysisEngine()
        ctx = AnalysisContext(data={"x": 1.0})
        results = engine.analyze(ctx)
        synthesis = engine.synthesize(results)
        assert synthesis.mode == AnalysisMode.META
        assert synthesis.confidence > 0

    def test_synthesize_empty(self):
        engine = AnalysisEngine()
        synthesis = engine.synthesize([])
        assert synthesis.confidence == 0.0
        assert "aucune" in synthesis.conclusion

    def test_process_dict(self):
        engine = AnalysisEngine()
        result = engine.process({"temp": 25.0})
        assert "results" in result
        assert "synthesis" in result
        assert result["n_modes"] == 7

    def test_process_context(self):
        engine = AnalysisEngine()
        ctx = AnalysisContext(data={"x": 1.0})
        result = engine.process(ctx)
        assert result["n_modes"] == 7

    def test_process_other(self):
        engine = AnalysisEngine()
        result = engine.process(42)
        assert result["n_modes"] == 7

    def test_history(self):
        engine = AnalysisEngine()
        ctx = AnalysisContext(data={"x": 1.0})
        engine.analyze(ctx)
        engine.analyze(ctx, modes=[AnalysisMode.META])
        assert len(engine.get_history()) == 8

    def test_clear_history(self):
        engine = AnalysisEngine()
        engine.analyze(AnalysisContext(data={"x": 1.0}))
        assert len(engine.get_history()) > 0
        engine.clear_history()
        assert len(engine.get_history()) == 0

    def test_custom_analyzer(self):
        engine = AnalysisEngine()

        def custom(ctx: AnalysisContext) -> AnalysisResult:
            return AnalysisResult(mode=AnalysisMode.DESCRIPTIF, conclusion="custom", confidence=1.0)

        engine.register_custom("test", custom)


class TestLabyrinthEngine:
    def test_create(self):
        lab = LabyrinthEngine()
        assert lab.engine is not None

    def test_analyze(self):
        lab = LabyrinthEngine()
        result = lab.analyze({"temp": 25.0, "humidity": 60.0})
        assert result["n_modes"] == 7

    def test_quick(self):
        lab = LabyrinthEngine()
        result = lab.quick({"cpu": 80.0})
        assert result["n_modes"] == 7

    def test_deep(self):
        lab = LabyrinthEngine()
        result = lab.deep({"a": 1.0, "b": 2.0, "c": 3.0})
        assert result["n_modes"] == 7


class TestBaseAnalyzer:
    def test_is_subclassable(self):
        class CustomAnalyzer(BaseAnalyzer):
            def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
                return AnalysisResult(mode=AnalysisMode.DESCRIPTIF, conclusion="ok", confidence=1.0)

        ca = CustomAnalyzer()
        result = ca.analyze(AnalysisContext())
        assert result.conclusion == "ok"


class TestAnalysisResultReliability:
    def test_confidence_threshold(self):
        r1 = AnalysisResult(mode=AnalysisMode.DESCRIPTIF, conclusion="x", confidence=0.7)
        assert r1.is_reliable(0.7)
        assert r1.is_reliable(0.5)

        r2 = AnalysisResult(mode=AnalysisMode.DESCRIPTIF, conclusion="x", confidence=0.3)
        assert not r2.is_reliable(0.5)


class TestAnalysisContextDefaults:
    def test_all_dimensions_present(self):
        ctx = AnalysisContext()
        dims = {d.value for d in ctx.dimensions}
        expected = {"temporelle", "spatiale", "causale", "quantitative", "qualitative", "systémique"}
        assert dims == expected

    def test_default_paradigms(self):
        ctx = AnalysisContext()
        assert Paradigm.DEDUCTIF in ctx.paradigms
        assert Paradigm.STATISTIQUE in ctx.paradigms
