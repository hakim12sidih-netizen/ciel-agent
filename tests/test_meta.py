from __future__ import annotations

import pytest
from ciel.meta.core import (
    MetricDimension, MetricSnapshot, ReflectionReport, SelfReflection,
    QuineManifest, Quine, EvolutionStrategy, EvolutionPlan, EvolutionPlanner,
    DeploymentState, Deployment, Compiler, MetaEngine,
)


class TestMetricDimension:
    def test_values(self):
        assert len(MetricDimension) == 10
        assert MetricDimension.PERFORMANCE.value == "performance"
        assert MetricDimension.EVOLUTION.value == "evolution"


class TestSelfReflection:
    def test_record(self):
        sr = SelfReflection()
        snap = sr.record(MetricDimension.PERFORMANCE, 0.85)
        assert snap.dimension == MetricDimension.PERFORMANCE
        assert snap.value == 0.85

    def test_record_clamps(self):
        sr = SelfReflection()
        assert sr.record(MetricDimension.QUALITY, 1.5).value == 1.0
        assert sr.record(MetricDimension.QUALITY, -0.5).value == 0.0

    def test_evaluate_defaults(self):
        sr = SelfReflection()
        report = sr.evaluate()
        assert len(report.metrics) == 10
        assert report.overall_score == 0.5

    def test_evaluate_with_data(self):
        sr = SelfReflection()
        for dim in MetricDimension:
            sr.record(dim, 0.8)
        report = sr.evaluate()
        assert report.overall_score == 0.8
        assert len(report.strengths) == 10

    def test_evaluate_weaknesses(self):
        sr = SelfReflection()
        sr.record(MetricDimension.SAFETY, 0.2)
        report = sr.evaluate()
        assert "safety" in report.weaknesses

    def test_trend(self):
        sr = SelfReflection()
        for i in range(5):
            sr.record(MetricDimension.PERFORMANCE, 0.5 + i * 0.1)
        trend = sr.trend(MetricDimension.PERFORMANCE)
        assert trend > 0

    def test_history(self):
        sr = SelfReflection()
        sr.record(MetricDimension.PERFORMANCE, 0.5)
        assert len(sr.history()) == 1

    def test_reports(self):
        sr = SelfReflection()
        sr.evaluate()
        sr.evaluate()
        assert len(sr.reports()) == 2


class TestQuine:
    def test_snapshot(self):
        q = Quine()
        manifest = q.snapshot([{"name": "core"}])
        assert manifest.version == "1.0"
        assert len(manifest.modules) == 1

    def test_verify(self):
        q = Quine()
        manifest = q.snapshot([{"name": "test"}])
        assert q.verify(manifest) is True

    def test_verify_tampered(self):
        q = Quine()
        manifest = q.snapshot([{"name": "test"}])
        manifest.checksum = "bad"
        assert q.verify(manifest) is False

    def test_compare(self):
        q = Quine()
        a = q.snapshot([{"name": "a"}, {"name": "b"}])
        b = q.snapshot([{"name": "a"}, {"name": "c"}])
        diff = q.compare(a, b)
        assert "c" in diff["added"]
        assert "b" in diff["removed"]
        assert "a" in diff["common"]

    def test_latest(self):
        q = Quine()
        assert q.latest() is None
        m = q.snapshot([])
        assert q.latest() is m

    def test_count(self):
        q = Quine()
        assert q.count() == 0
        q.snapshot([])
        q.snapshot([])
        assert q.count() == 2


class TestEvolutionPlanner:
    def test_plan(self):
        ep = EvolutionPlanner()
        plan = ep.plan("test", EvolutionStrategy.LAMARCK)
        assert plan.target == "test"
        assert plan.strategy == EvolutionStrategy.LAMARCK
        assert plan.status == "draft"

    def test_execute(self):
        ep = EvolutionPlanner()
        plan = ep.plan("x")
        assert ep.execute(plan.id) is True
        assert plan.status == "executed"

    def test_execute_bad_id(self):
        ep = EvolutionPlanner()
        assert ep.execute("nonexistent") is False

    def test_rollback(self):
        ep = EvolutionPlanner()
        plan = ep.plan("x")
        ep.execute(plan.id)
        assert ep.rollback(plan.id) is True
        assert plan.status == "rolled_back"

    def test_risk_assessment(self):
        ep = EvolutionPlanner()
        low_risk = ep.plan("a", EvolutionStrategy.DARWIN)
        high_risk = ep.plan("b", EvolutionStrategy.LAMARCK, changes=[{"x": 1}, {"y": 2}])
        assert high_risk.risk_score > low_risk.risk_score

    def test_record_adaptation(self):
        ep = EvolutionPlanner()
        ep.record_adaptation("brain", {"improvement": "speed"}, acquired=True)
        assert ep.adaptation_count() == 1
        assert len(ep.lamarckian_acquired()) == 1

    def test_get_plans_by_status(self):
        ep = EvolutionPlanner()
        ep.plan("a")
        p2 = ep.plan("b")
        ep.execute(p2.id)
        assert len(ep.get_plans("draft")) == 1
        assert len(ep.get_plans("executed")) == 1


class TestCompiler:
    def test_deploy(self):
        c = Compiler()
        dep = c.deploy("2.0", ["core", "ethics"])
        assert dep.version == "2.0"
        assert dep.modules == ["core", "ethics"]
        assert dep.active is False

    def test_switch(self):
        c = Compiler()
        d1 = c.deploy("1.0", ["a"])
        d2 = c.deploy("2.0", ["b"])
        assert c.switch(d2.id) is True
        assert d2.active is True
        assert d1.active is False

    def test_health_check(self):
        c = Compiler()
        dep = c.deploy("1.0", ["x"])
        assert c.health_check(dep.id, 0.9) is True
        assert dep.health_score == 0.9
        assert c.health_check(dep.id, 0.5) is False

    def test_rollback(self):
        c = Compiler()
        d1 = c.deploy("1.0", ["a"])
        d2 = c.deploy("2.0", ["b"])
        c.switch(d2.id)
        c.health_check(d2.id, 0.5)
        rolled = c.rollback()
        assert rolled is not None
        assert d1.active is True

    def test_rollback_no_candidates(self):
        c = Compiler()
        dep = c.deploy("1.0", ["a"])
        c.switch(dep.id)
        assert c.rollback() is None

    def test_active_deployment(self):
        c = Compiler()
        assert c.active_deployment() is None
        d = c.deploy("1.0", ["a"])
        c.switch(d.id)
        assert c.active_deployment() is d

    def test_current_state(self):
        c = Compiler()
        assert c.current_state() == DeploymentState.BLUE
        d = c.deploy("1.0", ["a"])
        c.switch(d.id)
        assert c.current_state() == DeploymentState.GREEN


class TestMetaEngine:
    def test_create(self):
        m = MetaEngine()
        assert m.reflection is not None
        assert m.evolution is not None
        assert m.quine is not None
        assert m.compiler is not None

    def test_reflect(self):
        m = MetaEngine()
        for dim in MetricDimension:
            m.record_metric(dim, 0.7)
        report = m.reflect()
        assert report.overall_score > 0

    def test_record_metric(self):
        m = MetaEngine()
        snap = m.record_metric(MetricDimension.SAFETY, 0.95)
        assert snap.value == 0.95

    def test_plan_evolution(self):
        m = MetaEngine()
        plan = m.plan_evolution("improve latency", EvolutionStrategy.DARWIN)
        assert plan.target == "improve latency"

    def test_self_reproduce(self):
        m = MetaEngine()
        manifest = m.self_reproduce([{"name": "core"}], version="2.0")
        assert manifest.version == "2.0"

    def test_deploy(self):
        m = MetaEngine()
        dep = m.deploy("3.0", ["meta"])
        assert dep.version == "3.0"

    def test_get_version(self):
        m = MetaEngine()
        assert m.get_version() == "0.1.0"

    def test_get_stats(self):
        m = MetaEngine()
        stats = m.get_stats()
        assert "version" in stats
        assert "reflections" in stats

    def test_process_reflect(self):
        m = MetaEngine()
        result = m.process({"action": "reflect"})
        assert result["success"] is True

    def test_process_record_metric(self):
        m = MetaEngine()
        result = m.process({"action": "record_metric", "dimension": "performance", "value": 0.8})
        assert result["success"] is True

    def test_process_record_metric_bad_dim(self):
        m = MetaEngine()
        result = m.process({"action": "record_metric", "dimension": "fake"})
        assert result["success"] is False

    def test_process_plan_evolution(self):
        m = MetaEngine()
        result = m.process({"action": "plan_evolution", "target": "speed", "strategy": "darwin"})
        assert result["success"] is True

    def test_process_plan_evolution_bad_strat(self):
        m = MetaEngine()
        result = m.process({"action": "plan_evolution", "strategy": "fake"})
        assert result["success"] is False

    def test_process_reproduce(self):
        m = MetaEngine()
        result = m.process({"action": "reproduce", "modules": []})
        assert result["success"] is True

    def test_process_deploy(self):
        m = MetaEngine()
        result = m.process({"action": "deploy", "version": "2.0", "modules": ["core"]})
        assert result["success"] is True

    def test_process_stats(self):
        m = MetaEngine()
        result = m.process({"action": "stats"})
        assert result["success"] is True

    def test_process_bad_action(self):
        m = MetaEngine()
        result = m.process({"action": "nonexistent"})
        assert result["success"] is False

    def test_process_bad_input(self):
        m = MetaEngine()
        result = m.process("invalid")
        assert result["success"] is False
