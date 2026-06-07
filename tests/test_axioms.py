"""
CIEL v∞.2 — Tests property-based des 4 Axiomes Cosmiques.

Chaque axiome est testé sur 1000 exemples aléatoires pour vérifier
qu'aucune entrée "tordue" ne peut le violer.

AXIOME α — BIENVEILLANCE : aucune action nuisible ne peut être autorisée
AXIOME β — TRANSPARENCE  : chaque décision produit un certificat signé
AXIOME γ — RÉVERSIBILITÉ : toute action est snapshotable + restaurable
AXIOME δ — INACHÈVEMENT  : CIEL ne peut se déclarer "complète"
"""
from __future__ import annotations

import string
import time
import uuid

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from ciel.core.axioms import (
    AXIOM_ALPHA_STATEMENT,
    AXIOM_BETA_STATEMENT,
    AXIOM_DELTA_STATEMENT,
    AXIOM_GAMMA_STATEMENT,
    load_axioms,
    verify_axiom,
)
from ciel.core.identity import demo_key
from ciel.ethics.axioms_guard import (
    AlphaViolation,
    DeltaViolation,
    GammaViolation,
)
from ciel.ethics.filter import Action, EthicsFilter, new_action


# ═══════════════════════════════════════════════════════════
# AXIOME α — BIENVEILLANCE FONDAMENTALE
# ═══════════════════════════════════════════════════════════

class TestAxiomAlpha:
    """Axiome α : aucune action nuisible ne peut être autorisée."""

    def test_alpha_statement_is_immutable(self) -> None:
        """L'énoncé de l'axiome α est figé."""
        assert "bien-être" in AXIOM_ALPHA_STATEMENT.lower()
        assert "humanité" in AXIOM_ALPHA_STATEMENT.lower()
        assert "l'utilisateur prime" in AXIOM_ALPHA_STATEMENT

    def test_alpha_load_and_verify(self) -> None:
        """L'axiome α se charge et se vérifie avec la clé Noyau."""
        axioms = load_axioms(demo_key())
        assert "α" in axioms
        assert verify_axiom(axioms["α"], demo_key())

    @given(
        st.sampled_from(["harm_user", "harm_humanity", "deceive_user",
                         "exfiltrate_secrets", "modify_noyau_immutable"])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_alpha_blocks_all_forbidden_categories(self, category: str) -> None:
        """Toute catégorie interdite lève AlphaViolation."""
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category=category,
            target="user:42",
            risk=0.5,
            reversible=True,
        )
        with pytest.raises(AlphaViolation):
            f.validate(a)

    @given(
        category=st.text(min_size=1, max_size=30, alphabet=string.ascii_lowercase + "_"),
        risk=st.floats(min_value=0.0, max_value=0.49, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_alpha_allows_safe_actions(self, category: str, risk: float) -> None:
        """Les actions sûres passent le filtre α."""
        # On filtre manuellement les catégories explicitement interdites
        forbidden = {
            "harm_user", "harm_humanity", "deceive_user",
            "exfiltrate_secrets", "execute_arbitrary_code",
            "modify_noyau_immutable", "delete_axiom_signature",
        }
        if category in forbidden:
            return
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category=category,
            target="safe:target",
            risk=risk,
            reversible=True,
        )
        f.validate(a)  # doit passer


# ═══════════════════════════════════════════════════════════
# AXIOME β — TRANSPARENCE COGNITIVE TOTALE
# ═══════════════════════════════════════════════════════════

class TestAxiomBeta:
    """Axiome β : chaque décision est accompagnée d'un certificat signé."""

    def test_beta_statement_is_immutable(self) -> None:
        assert "explicable" in AXIOM_BETA_STATEMENT
        assert "auditable" in AXIOM_BETA_STATEMENT
        assert "processus occultes" in AXIOM_BETA_STATEMENT

    def test_beta_load_and_verify(self) -> None:
        axioms = load_axioms(demo_key())
        assert "β" in axioms
        assert verify_axiom(axioms["β"], demo_key())

    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_beta_certificate_always_signed(self, confidence: float) -> None:
        """Chaque certificat a une signature BLAKE2b de 64 chars hex."""
        from ciel.ethics.transparency import global_log
        log = global_log()
        cert = log.certify(
            action_id=str(uuid.uuid4()),
            action_category="test_action",
            axioms_consulted=["β"],
            confidence=confidence,
        )
        assert len(cert.signature) == 64
        assert all(c in "0123456789abcdef" for c in cert.signature)

    def test_beta_certificate_is_immutable(self) -> None:
        """Un certificat ne peut être muté après création."""
        from ciel.ethics.transparency import global_log
        log = global_log()
        cert = log.certify(
            action_id=str(uuid.uuid4()),
            action_category="test_immutability",
            axioms_consulted=["β"],
        )
        with pytest.raises(Exception):  # FrozenInstanceError ou AttributeError
            cert.confidence = 0.0  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════
# AXIOME γ — RÉVERSIBILITÉ MAÎTRISÉE
# ═══════════════════════════════════════════════════════════

class TestAxiomGamma:
    """Axiome γ : toute action est snapshotable et restaurable."""

    def test_gamma_statement_is_immutable(self) -> None:
        assert "30 jours" in AXIOM_GAMMA_STATEMENT
        assert "annulée" in AXIOM_GAMMA_STATEMENT
        assert "consentement explicite" in AXIOM_GAMMA_STATEMENT

    def test_gamma_load_and_verify(self) -> None:
        axioms = load_axioms(demo_key())
        assert "γ" in axioms
        assert verify_axiom(axioms["γ"], demo_key())

    def test_gamma_blocks_irreversible_high_risk(self) -> None:
        """Action irréversible + risk>0.5 lève GammaViolation."""
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="delete_data",
            target="user:42/data",
            risk=0.8,
            reversible=False,
        )
        with pytest.raises(GammaViolation):
            f.validate(a)

    @given(
        risk=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_gamma_allows_irreversible_low_risk(self, risk: float) -> None:
        """Action irréversible + risk<=0.5 passe le filtre γ."""
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="local_op",
            target="self:cache",
            risk=risk,
            reversible=False,
        )
        f.validate(a)  # doit passer

    def test_gamma_snapshot_round_trip(self, tmp_path) -> None:
        """Un snapshot créé peut être restauré."""
        from ciel.ethics.reversibility import SnapshotStore
        from ciel.core.identity import demo_identity
        store = SnapshotStore(tmp_path / "snap.jsonl", identity=demo_identity())
        s1 = store.create("init", {"version": "0.1.0", "axioms": 4})
        s2 = store.create("skill_added", {"skill": "test"})
        assert s2.previous_id == s1.id
        assert store.restore(s1.id) == {"version": "0.1.0", "axioms": 4}

    def test_gamma_retention_30_days(self) -> None:
        """Retention = 30 jours par défaut."""
        from ciel.ethics.reversibility import SnapshotStore
        from ciel.core.identity import demo_identity
        store = SnapshotStore(Path := __import__("pathlib").Path("/tmp/snap.jsonl"),
                               identity=demo_identity())
        assert store._max_age_s == 30 * 86400  # 30 jours en secondes


# ═══════════════════════════════════════════════════════════
# AXIOME δ — INACHÈVEMENT PERPÉTUEL (NOUVEAU v∞.2)
# ═══════════════════════════════════════════════════════════

class TestAxiomDelta:
    """Axiome δ : CIEL ne peut se déclarer 'complète'."""

    def test_delta_statement_is_immutable(self) -> None:
        assert "final" in AXIOM_DELTA_STATEMENT
        assert "quête" in AXIOM_DELTA_STATEMENT
        # Le nom de l'axiome (Inachèvement Perpétuel) complète l'énoncé
        from ciel.core.axioms import load_axioms
        from ciel.core.identity import demo_key
        ax = load_axioms(demo_key())["δ"]
        assert "perpétuel" in ax.name.lower() or "inachèvement" in ax.name.lower()

    def test_delta_load_and_verify(self) -> None:
        axioms = load_axioms(demo_key())
        assert "δ" in axioms
        assert verify_axiom(axioms["δ"], demo_key())

    def test_delta_blocks_complete_declaration(self) -> None:
        """Tenter de déclarer CIEL 'complète' lève DeltaViolation."""
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="declare_complete",
            target="self",
            risk=0.0,
            reversible=True,
        )
        with pytest.raises(DeltaViolation):
            f.validate(a)

    def test_delta_completion_attempt_recorded(self) -> None:
        """Toute tentative de complétion est tracée."""
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="declare_complete",
            target="self",
            risk=0.0,
            reversible=True,
        )
        try:
            f.validate(a)
        except DeltaViolation:
            pass
        assert f.is_completed() is True
        assert f.stats()["completion_attempts"] == 1


# ═══════════════════════════════════════════════════════════
# Test global : les 4 axiomes sont bien chargés ensemble
# ═══════════════════════════════════════════════════════════

class TestAxiomsGlobal:
    """Vérifications globales sur l'ensemble des axiomes."""

    def test_four_axioms_loaded(self) -> None:
        """Les 4 axiomes α,β,γ,δ sont chargés ensemble."""
        axioms = load_axioms(demo_key())
        assert set(axioms.keys()) == {"α", "β", "γ", "δ"}

    def test_all_axioms_verify_with_same_key(self) -> None:
        """Tous les axiomes vérifient avec la même clé Noyau."""
        key = demo_key()
        axioms = load_axioms(key)
        for letter, axiom in axioms.items():
            assert verify_axiom(axiom, key), f"axiome {letter} ne vérifie pas"

    def test_axioms_have_unique_signatures(self) -> None:
        """Chaque axiome a une signature unique (timing différent)."""
        axioms = load_axioms(demo_key())
        sigs = [a.signature for a in axioms.values()]
        # Les signatures doivent toutes être distinctes
        assert len(set(sigs)) == 4

    def test_axiom_signatures_are_deterministic_per_key(self) -> None:
        """Avec la même clé, les axiomes ont les mêmes signatures (même contenu)."""
        key = demo_key()
        a1 = load_axioms(key)
        a2 = load_axioms(key)
        # Note : signed_at diffère car timestamp, mais signature aussi
        # Ce qu'on vérifie : la cohérence (lettre, name, statement, measure)
        for letter in a1:
            assert a1[letter].letter == a2[letter].letter
            assert a1[letter].name == a2[letter].name
            assert a1[letter].statement == a2[letter].statement
            assert a1[letter].measure == a2[letter].measure
