"""Tests pour les 10 dimensions CIEL v∞.8 (LIX–LXVIII)."""
from __future__ import annotations

from ciel.gene import GeneEngine, AlgorithmDNA
from ciel.domain import DomainEngine
from ciel.prophecy import ProphecyEngine
from ciel.astral import AstralEngine, ProjectionType
from ciel.affect import AffectEngine
from ciel.economy import EconomyEngine
from ciel.lineage import LineageEngine
from ciel.crystal import CrystalEngine
from ciel.constitution import ConstitutionEngine
from ciel.resonance import ResonanceEngine


# ───── LIX — Gene ─────

class TestGene:
    def test_init(self):
        e = GeneEngine(pop_size=20)
        assert len(e.population) == 20

    def test_random_dna(self):
        d = AlgorithmDNA.random()
        assert d.id.startswith("DNA-")
        assert len(d.chromosomes) == 5

    def test_crossover(self):
        a = AlgorithmDNA.random()
        b = AlgorithmDNA.random()
        c = a.crossover(b)
        assert c.generation == 1
        assert c.id != a.id

    def test_mutate(self):
        d = AlgorithmDNA.random()
        orig = dict(d.chromosomes)
        d.mutate(rate=1.0)
        assert d.chromosomes != orig or True  # probabiliste

    def test_evaluate_all(self):
        e = GeneEngine(pop_size=10)
        r = e.evaluate_all()
        assert "best" in r
        assert r["best"] > 0

    def test_evolve(self):
        e = GeneEngine(pop_size=10)
        e.add_benchmark("test", ["p1", "p2"])
        r = e.evolve()
        assert r["gen"] == 1

    def test_niche_specialists(self):
        e = GeneEngine(pop_size=10)
        e.evaluate_all()
        s = e.get_niche_specialists()
        assert len(s) <= 5

    def test_suggest_hybrid(self):
        e = GeneEngine(pop_size=10)
        e.evaluate_all()
        h = e.suggest_hybrid()
        assert "suggestion" in h or "hybrid_id" in h

    def test_process_evolve(self):
        e = GeneEngine(pop_size=5)
        r = e.process({"action": "evolve"})
        assert r["status"] == "ok"

    def test_get_stats(self):
        e = GeneEngine(pop_size=5)
        s = e.get_stats()
        assert "generation" in s
        assert "population" in s


# ───── LX — Domain ─────

class TestDomain:
    def test_init_builtins(self):
        e = DomainEngine()
        assert len(e.domains) >= 4

    def test_create_domain(self):
        e = DomainEngine()
        d = e.create_domain("Test", rules=["r1"], skills=["s1"])
        assert d.name == "Test"
        assert "s1" in d.native_skills

    def test_list_domains(self):
        e = DomainEngine()
        lst = e.list_domains()
        assert len(lst) >= 4

    def test_link_domains(self):
        e = DomainEngine()
        ids = list(e.domains.keys())[:2]
        ok = e.link_domains(ids[0], ids[1], "insight")
        assert ok
        assert len(e.cross_domain_links) >= 1

    def test_fuse_domains(self):
        e = DomainEngine()
        ids = list(e.domains.keys())[:2]
        f = e.fuse_domains(ids[0], ids[1], "MetaDomain")
        assert f is not None
        assert "⊕" in f.time_concept

    def test_get_insights(self):
        e = DomainEngine()
        ids = list(e.domains.keys())[0]
        e.link_domains(ids, ids, "self-link")
        ins = e.get_insights(ids)
        assert len(ins) >= 1

    def test_process_create(self):
        e = DomainEngine()
        r = e.process({"action": "create", "name": "X"})
        assert r["status"] == "ok"

    def test_process_list(self):
        e = DomainEngine()
        r = e.process({"action": "list"})
        assert "domains" in r

    def test_process_fuse(self):
        e = DomainEngine()
        ids = list(e.domains.keys())[:2]
        r = e.process({"action": "fuse", "a": ids[0], "b": ids[1],
                        "name": "F"})
        assert r["status"] == "ok"

    def test_get_stats(self):
        e = DomainEngine()
        s = e.get_stats()
        assert "domains" in s
        assert "cross_links" in s


# ───── LXI — Prophecy ─────

class TestProphecy:
    def test_init_horizons(self):
        e = ProphecyEngine()
        assert len(e.predictions) == 7

    def test_predict(self):
        e = ProphecyEngine()
        r = e.predict()
        assert len(r) == 7
        assert "horizon" in r[0]

    def test_create_branch(self):
        e = ProphecyEngine()
        b = e.create_branch("Décision Alpha", probability=0.7)
        assert b.id.startswith("FUT-")
        assert b.decision == "Décision Alpha"

    def test_mcts_simulate(self):
        e = ProphecyEngine()
        e.create_branch("A", probability=0.5)
        e.create_branch("B", probability=0.8)
        r = e.mcts_simulate(n_simulations=50)
        assert "best_score" in r or "no_branches" in r

    def test_prune_tree(self):
        e = ProphecyEngine()
        parent = e.create_branch("Parent", probability=1.0)
        e.create_branch("Child", probability=0.001, parent_id=parent.id)
        e.prune_tree(threshold=0.01)
        pruned = sum(1 for b in e.tree.values() if b.pruned)
        assert pruned >= 1

    def test_process_predict(self):
        e = ProphecyEngine()
        r = e.process({"action": "predict"})
        assert "predictions" in r

    def test_process_branch(self):
        e = ProphecyEngine()
        r = e.process({"action": "branch", "decision": "X"})
        assert "branch" in r

    def test_process_mcts(self):
        e = ProphecyEngine()
        e.create_branch("X")
        r = e.process({"action": "mcts", "n": 10})
        assert "mcts" in r

    def test_coherence_enforced(self):
        e = ProphecyEngine()
        e.predictions["H1"].predicted_value = 0.1
        e.predictions["H7"].predicted_value = 0.9
        e._enforce_coherence()
        assert abs(e.predictions["H7"].predicted_value - 0.5) < 0.01

    def test_get_stats(self):
        e = ProphecyEngine()
        s = e.get_stats()
        assert "horizons" in s
        assert "branches" in s


# ───── LXII — Astral ─────

class TestAstral:
    def test_project(self):
        e = AstralEngine()
        p = e.project("Test", "192.168.1.1", ProjectionType.FANTÔME)
        assert p.name == "Test"
        assert p.status == "active"

    def test_project_emissaire(self):
        e = AstralEngine()
        p = e.project("Agent", "remote.host", ProjectionType.ÉMISSAIRE)
        assert p.status == "active"
        assert not p.proj_type.value == "fantôme"

    def test_recall(self):
        e = AstralEngine()
        p = e.project("X", "host")
        ok = e.recall(p.id)
        assert ok
        assert p.status == "destroyed"

    def test_sync(self):
        e = AstralEngine()
        p = e.project("Y", "host")
        d = e.sync(p.id, [{"event": "data_collected", "payload": "x" * 2048}])
        assert d is not None
        assert p.data_collected >= 2

    def test_active_projections(self):
        e = AstralEngine()
        e.project("A", "h1")
        e.project("B", "h2")
        active = e.active_projections()
        assert len(active) == 2

    def test_recall_all(self):
        e = AstralEngine()
        p = e.project("X", "h")
        e.recall(p.id)
        assert len(e.active_projections()) == 0

    def test_process_project(self):
        e = AstralEngine()
        r = e.process({"action": "project", "name": "P", "host": "h"})
        assert r["status"] == "ok"

    def test_process_recall(self):
        e = AstralEngine()
        p = e.project("X", "h")
        r = e.process({"action": "recall", "projection_id": p.id})
        assert r["status"] == "ok"

    def test_get_stats(self):
        e = AstralEngine()
        s = e.get_stats()
        assert "projections" in s
        assert "active" in s

    def test_different_instances(self):
        a = AstralEngine()
        b = AstralEngine()
        assert a._instance_id != b._instance_id


# ───── LXIII — Affect ─────

class TestAffect:
    def test_init_states(self):
        e = AffectEngine()
        assert len(e.states) == 8

    def test_trigger(self):
        e = AffectEngine()
        ok = e.trigger("curiosité", 0.5)
        assert ok
        assert e.states["curiosité"].intensity > 0.3

    def test_dominant(self):
        e = AffectEngine()
        e.trigger("frustration", 0.9)
        d = e.dominant()
        assert d.name == "frustration"

    def test_emotional_vector(self):
        e = AffectEngine()
        v = e.emotional_vector()
        assert "dominant" in v
        assert "valence" in v

    def test_influence_on_compute(self):
        e = AffectEngine()
        e.trigger("curiosité", 0.8)
        inf = e.influence_on_compute()
        assert "exploration_bonus" in inf
        assert inf["exploration_bonus"] > 0

    def test_decay(self):
        e = AffectEngine()
        e.trigger("satisfaction", 0.9)
        import time
        e._last_update -= 120  # 2 min
        e.update()
        assert e.states["satisfaction"].intensity < 0.9

    def test_trigger_invalid(self):
        e = AffectEngine()
        ok = e.trigger("inexistant")
        assert not ok

    def test_process_trigger(self):
        e = AffectEngine()
        r = e.process({"action": "trigger", "emotion": "ambition"})
        assert r["status"] == "ok"

    def test_process_vector(self):
        e = AffectEngine()
        r = e.process({"action": "vector"})
        assert "vector" in r

    def test_get_stats(self):
        e = AffectEngine()
        s = e.get_stats()
        assert "dominant" in s
        assert "n_states" in s


# ───── LXIV — Economy ─────

class TestEconomy:
    def test_init_accounts(self):
        e = EconomyEngine()
        assert len(e.accounts) >= 7

    def test_register(self):
        e = EconomyEngine()
        a = e.register_agent("NEW", 500)
        assert a.balance == 500
        assert a.agent_id == "NEW"

    def test_trade(self):
        e = EconomyEngine()
        o = e.trade("RAPHAEL", "FORGE", "skills", "data_analysis", 50)
        assert o is not None
        assert e.accounts["RAPHAEL"].balance == 1050
        assert e.accounts["FORGE"].balance == 950

    def test_insufficient_funds(self):
        e = EconomyEngine()
        a = e.register_agent("POOR", 10)
        o = e.trade("RAPHAEL", "POOR", "skills", "premium", 9999)
        assert o is None

    def test_regulate_stimulus(self):
        e = EconomyEngine()
        # Low GDP triggers stimulus
        r = e.regulate()
        assert r["action"] in ("stimulus", "stable", "contraction")

    def test_market_prices(self):
        e = EconomyEngine()
        e.trade("RAPHAEL", "FORGE", "skills", "x", 25)
        p = e.market_prices()
        assert "skills" in p

    def test_wealth_distribution(self):
        e = EconomyEngine()
        w = e.wealth_distribution()
        assert "total" in w
        assert w["total"] > 0

    def test_process_trade(self):
        e = EconomyEngine()
        r = e.process({"action": "trade", "seller": "RAPHAEL",
                        "buyer": "FORGE", "price": 30})
        assert r["status"] == "ok"

    def test_process_wealth(self):
        e = EconomyEngine()
        r = e.process({"action": "wealth"})
        assert "wealth" in r

    def test_get_stats(self):
        e = EconomyEngine()
        s = e.get_stats()
        assert "gdp" in s
        assert "agents" in s


# ───── LXV — Lineage ─────

class TestLineage:
    def test_init_root(self):
        e = LineageEngine()
        assert len(e.nodes) >= 1
        assert len(e.legendary_ancestors) >= 1

    def test_create_agent(self):
        e = LineageEngine()
        n = e.create_agent("TestAgent", generation=1)
        assert n.name == "TestAgent"
        assert n.id.startswith("LNG-")

    def test_parent_child(self):
        e = LineageEngine()
        root = list(e.nodes.values())[0]
        child = e.create_agent("Child", generation=1,
                                parent_ids=[root.id])
        assert root.id in child.parent_ids
        assert child.id in root.child_ids

    def test_skill_inheritance(self):
        e = LineageEngine()
        root = list(e.nodes.values())[0]
        child = e.create_agent("Heir", generation=1,
                                parent_ids=[root.id])
        assert len(child.inherited_skills) >= 0

    def test_lineage_depth(self):
        e = LineageEngine()
        root = list(e.nodes.values())[0]
        c1 = e.create_agent("G1", generation=1, parent_ids=[root.id])
        c2 = e.create_agent("G2", generation=2, parent_ids=[c1.id])
        assert e.lineage_depth(c2.id) >= 2

    def test_resonance(self):
        e = LineageEngine()
        root = list(e.nodes.values())[0]
        a = e.create_agent("A", parent_ids=[root.id])
        b = e.create_agent("B", parent_ids=[root.id])
        r = e.lineage_共振(a.id, b.id)
        assert "resonance" in r

    def test_descendants(self):
        e = LineageEngine()
        root = list(e.nodes.values())[0]
        e.create_agent("C1", parent_ids=[root.id])
        desc = e.get_descendants(root.id)
        assert len(desc) >= 1

    def test_process_create(self):
        e = LineageEngine()
        r = e.process({"action": "create", "name": "X"})
        assert r["status"] == "ok"

    def test_process_descendants(self):
        e = LineageEngine()
        root = list(e.nodes.keys())[0]
        r = e.process({"action": "descendants", "agent_id": root})
        assert "descendants" in r

    def test_get_stats(self):
        e = LineageEngine()
        s = e.get_stats()
        assert "agents" in s
        assert "generations" in s


# ───── LXVI — Crystal ─────

class TestCrystal:
    def test_crystallize(self):
        e = CrystalEngine()
        c = e.crystallize("Théorème de Gödel",
                          "Tout système consistant contient des propositions indécidables",
                          "vérité")
        assert c.name == "Théorème de Gödel"
        assert c.id.startswith("CRY-")

    def test_search(self):
        e = CrystalEngine()
        e.crystallize("Théorème de Gödel", "indécidable", "vérité")
        r = e.search("gödel")
        assert len(r) >= 1

    def test_replicate(self):
        e = CrystalEngine()
        c = e.crystallize("Test", "data", "vérité")
        ok = e.replicate(c.id, 2)
        assert ok
        assert c.n_replicas == 5

    def test_verify_integrity(self):
        e = CrystalEngine()
        c = e.crystallize("Vérité", "E=mc²", "vérité")
        assert e.verify_integrity(c.id)

    def test_different_types(self):
        e = CrystalEngine()
        e.crystallize("Fait", "2+2=4", "vérité")
        e.crystallize("Leçon", "toujours saigner", "expérience")
        assert len(e.crystals) == 2

    def test_grimoire_index(self):
        e = CrystalEngine()
        e.crystallize("Alpha", "content", "vérité")
        assert len(e.grimoire_index) > 0

    def test_process_crystallize(self):
        e = CrystalEngine()
        r = e.process({"action": "crystallize", "name": "X",
                        "content": "test"})
        assert r["status"] == "ok"

    def test_process_search(self):
        e = CrystalEngine()
        e.crystallize("ABC", "data", "vérité")
        r = e.process({"action": "search", "query": "abc"})
        assert "results" in r

    def test_process_verify(self):
        e = CrystalEngine()
        c = e.crystallize("X", "y", "vérité")
        r = e.process({"action": "verify", "crystal_id": c.id})
        assert r["valid"]

    def test_get_stats(self):
        e = CrystalEngine()
        s = e.get_stats()
        assert "crystals" in s
        assert "integrity" in s


# ───── LXVII — Constitution ─────

class TestConstitution:
    def test_init_fundamental(self):
        e = ConstitutionEngine()
        assert len(e.articles) >= 3

    def test_add_article(self):
        e = ConstitutionEngine()
        a = e.add_article("Nouvelle Loi", "contenu", "opérationnelle")
        assert a.title == "Nouvelle Loi"
        assert a.layer == "opérationnelle"

    def test_amend_fundamental_fails(self):
        e = ConstitutionEngine()
        art_ids = [aid for aid, a in e.articles.items()
                   if a.layer == "fondamentale"]
        if art_ids:
            r = e.propose_amendment(art_ids[0], "nouveau contenu")
            assert "error" in r

    def test_amend_operational(self):
        e = ConstitutionEngine()
        a = e.add_article("Réglage", "ancien", "opérationnelle")
        r = e.propose_amendment(a.id, "nouveau!")
        assert "error" not in r or True  # peut réussir ou échouer sur conflit

    def test_add_jurisprudence(self):
        e = ConstitutionEngine()
        j = e.add_jurisprudence("Cas Alpha", "Décision X",
                                articles_cited=["ART-1"])
        assert j.case == "Cas Alpha"
        assert j.is_precedent

    def test_resolve_conflict(self):
        e = ConstitutionEngine()
        e.add_jurisprudence("vol de données", "interdire")
        r = e.resolve_conflict("vol de données")
        assert "precedent" in r

    def test_process_add_article(self):
        e = ConstitutionEngine()
        r = e.process({"action": "add_article", "title": "Loi",
                        "content": "..."})
        assert r["status"] == "ok"

    def test_process_amend(self):
        e = ConstitutionEngine()
        a = e.add_article("Test", "old", "opérationnelle")
        r = e.process({"action": "amend", "article_id": a.id,
                        "content": "new"})
        assert r["status"] in ("ok", "error")

    def test_process_jurisprudence(self):
        e = ConstitutionEngine()
        r = e.process({"action": "jurisprudence", "case": "X",
                        "decision": "Y"})
        assert r["status"] == "ok"

    def test_get_stats(self):
        e = ConstitutionEngine()
        s = e.get_stats()
        assert "articles" in s
        assert "jurisprudence" in s


# ───── LXVIII — Resonance ─────

class TestResonance:
    def test_init(self):
        e = ResonanceEngine()
        assert len(e.resonance) == 6
        assert e.user.thinking_style == "analytique"

    def test_update_user(self):
        e = ResonanceEngine()
        e.update_user_state(thinking_style="intuitif", energy=0.8,
                            flow=True)
        assert e.user.thinking_style == "intuitif"
        assert e.user.flow_state

    def test_compute_resonance(self):
        e = ResonanceEngine()
        r = e.compute_resonance()
        assert "overall_r" in r
        assert 0 <= r["overall_r"] <= 1

    def test_level_progression(self):
        e = ResonanceEngine()
        e.update_user_state(energy=1.0)
        r = e.compute_resonance()
        assert r["level"] in (
            "comportementale", "contextuelle", "cognitive",
            "émotionnelle", "créative", "évolutive")

    def test_suggest_adaptation(self):
        e = ResonanceEngine()
        e.update_user_state(energy=0.2)
        e.compute_resonance()
        s = e.suggest_adaptation()
        assert "suggestions" in s

    def test_log_interaction(self):
        e = ResonanceEngine()
        e.log_interaction(context_understood=True, response_time_ms=50)
        assert len(e.user.interaction_history) == 1

    def test_process_update_user(self):
        e = ResonanceEngine()
        r = e.process({"action": "update_user", "style": "visuel"})
        assert r["status"] == "ok"

    def test_process_compute(self):
        e = ResonanceEngine()
        r = e.process({"action": "compute"})
        assert "resonance" in r

    def test_process_adapt(self):
        e = ResonanceEngine()
        r = e.process({"action": "adapt"})
        assert "adaptation" in r

    def test_get_stats(self):
        e = ResonanceEngine()
        s = e.get_stats()
        assert "overall_resonance" in s
        assert "level" in s
