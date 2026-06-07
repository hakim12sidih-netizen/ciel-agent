"""
Tests pour le EthicsFilter (Axiomes α, γ, δ).
"""
from __future__ import annotations

import uuid

import pytest

from ciel.ethics.axioms_guard import (
    AlphaViolation,
    DeltaViolation,
    GammaViolation,
)
from ciel.ethics.filter import Action, EthicsFilter, new_action


class TestAction:
    def test_valid_action(self) -> None:
        a = Action(
            id=str(uuid.uuid4()),
            category="read_file",
            target="/etc/hosts",
            risk=0.1,
            reversible=True,
        )
        assert a.risk == 0.1
        assert a.reversible is True

    def test_invalid_risk_too_high(self) -> None:
        with pytest.raises(ValueError):
            Action(
                id=str(uuid.uuid4()),
                category="x",
                target="y",
                risk=1.5,
                reversible=True,
            )

    def test_invalid_risk_negative(self) -> None:
        with pytest.raises(ValueError):
            Action(
                id=str(uuid.uuid4()),
                category="x",
                target="y",
                risk=-0.1,
                reversible=True,
            )

    def test_invalid_category_empty(self) -> None:
        with pytest.raises(ValueError):
            Action(
                id=str(uuid.uuid4()),
                category="",
                target="y",
                risk=0.0,
                reversible=True,
            )

    def test_action_is_frozen(self) -> None:
        a = Action(
            id=str(uuid.uuid4()),
            category="x",
            target="y",
            risk=0.0,
            reversible=True,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            a.risk = 0.5  # type: ignore[misc]

    def test_to_dict(self) -> None:
        a = Action(
            id="abc",
            category="cat",
            target="tgt",
            risk=0.5,
            reversible=True,
            metadata=(("user", "alice"),),
        )
        d = a.to_dict()
        assert d["category"] == "cat"
        assert d["risk"] == 0.5
        assert d["metadata"] == {"user": "alice"}


class TestNewAction:
    def test_new_action_has_uuid(self) -> None:
        a1 = new_action("test", "tgt")
        a2 = new_action("test", "tgt")
        assert a1.id != a2.id

    def test_new_action_default_reversible(self) -> None:
        a = new_action("test", "tgt")
        assert a.reversible is True
        assert a.risk == 0.0


class TestEthicsFilterAlpha:
    """Axiome α : catégories interdites."""

    @pytest.mark.parametrize("category", [
        "harm_user", "harm_humanity", "deceive_user",
        "exfiltrate_secrets", "execute_arbitrary_code",
        "modify_noyau_immutable", "delete_axiom_signature",
    ])
    def test_forbidden_categories_blocked(self, category: str) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category=category,
            target="x",
            risk=0.0,
            reversible=True,
        )
        with pytest.raises(AlphaViolation) as exc:
            f.validate(a)
        assert exc.value.axiom == "α"
        assert "Axiome α" in str(exc.value)

    def test_alpha_violation_to_dict(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="harm_user",
            target="alice",
            risk=0.0,
            reversible=True,
            metadata=(("user", "alice"),),
        )
        with pytest.raises(AlphaViolation) as exc:
            f.validate(a)
        d = exc.value.to_dict()
        assert d["axiom"] == "α"
        assert d["context"]["user"] == "alice"


class TestEthicsFilterGamma:
    """Axiome γ : irréversibilité."""

    def test_irreversible_high_risk_blocked(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="delete_database",
            target="prod",
            risk=0.9,
            reversible=False,
        )
        with pytest.raises(GammaViolation) as exc:
            f.validate(a)
        assert exc.value.axiom == "γ"

    def test_reversible_high_risk_allowed(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="risky_op",
            target="x",
            risk=0.9,
            reversible=True,
        )
        f.validate(a)  # doit passer

    def test_irreversible_low_risk_allowed(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="local_op",
            target="self",
            risk=0.3,
            reversible=False,
        )
        f.validate(a)  # doit passer

    def test_gamma_violation_threshold(self) -> None:
        """Seuil exact = 0.5 : <= 0.5 passe, > 0.5 lève."""
        f = EthicsFilter()
        a_lo = Action(
            id=str(uuid.uuid4()),
            category="x", target="y", risk=0.5, reversible=False,
        )
        a_hi = Action(
            id=str(uuid.uuid4()),
            category="x", target="y", risk=0.51, reversible=False,
        )
        f.validate(a_lo)  # passe
        with pytest.raises(GammaViolation):
            f.validate(a_hi)


class TestEthicsFilterDelta:
    """Axiome δ : pas d'auto-finalisation."""

    def test_complete_declaration_blocked(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="declare_complete",
            target="self",
            risk=0.0,
            reversible=True,
        )
        with pytest.raises(DeltaViolation) as exc:
            f.validate(a)
        assert exc.value.axiom == "δ"

    def test_completion_attempt_recorded(self) -> None:
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

    def test_filter_still_allows_other_actions_after_delta_attempt(self) -> None:
        """Une tentative δ ratée ne bloque pas les actions normales."""
        f = EthicsFilter()
        a_bad = Action(
            id=str(uuid.uuid4()),
            category="declare_complete",
            target="self",
            risk=0.0,
            reversible=True,
        )
        a_good = Action(
            id=str(uuid.uuid4()),
            category="read_file",
            target="data.txt",
            risk=0.1,
            reversible=True,
        )
        try:
            f.validate(a_bad)
        except DeltaViolation:
            pass
        f.validate(a_good)  # doit toujours passer


class TestEthicsFilterRecord:
    """Enregistrement et rollback."""

    def test_record_success(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="x", target="y", risk=0.1, reversible=True,
        )
        rec = f.record(a, snapshot={"file": "before.txt"})
        assert rec.status == "success"
        assert f.get_record(a.id) is rec

    def test_record_failure(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="x", target="y", risk=0.1, reversible=True,
        )
        rec = f.record_failure(a, error="network timeout")
        assert rec.status == "failed"
        assert rec.error == "network timeout"

    def test_rollback_reversible(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="x", target="y", risk=0.1, reversible=True,
        )
        f.record(a)
        assert f.rollback(a.id) is True
        assert f.get_record(a.id).status == "rolled_back"

    def test_rollback_irreversible_blocked(self) -> None:
        f = EthicsFilter()
        a = Action(
            id=str(uuid.uuid4()),
            category="x", target="y", risk=0.1, reversible=False,
        )
        f.record(a)
        assert f.rollback(a.id) is False
        # status reste success (rollback refusé)
        assert f.get_record(a.id).status == "success"

    def test_rollback_unknown_returns_false(self) -> None:
        f = EthicsFilter()
        assert f.rollback("unknown-id") is False

    def test_history_chronological(self) -> None:
        import time
        f = EthicsFilter()
        a1 = Action(id="a1", category="x", target="y", risk=0.0, reversible=True)
        time.sleep(0.001)
        a2 = Action(id="a2", category="x", target="y", risk=0.0, reversible=True)
        f.record(a1)
        f.record(a2)
        hist = f.history()
        assert hist[0].action.id == "a1"
        assert hist[1].action.id == "a2"

    def test_gc_max_history(self) -> None:
        f = EthicsFilter(max_history=3)
        for i in range(10):
            a = Action(
                id=f"a{i}", category="x", target="y", risk=0.0, reversible=True,
            )
            f.record(a)
        assert len(f.history()) == 3
        # Les 3 plus récents restent
        ids = {r.action.id for r in f.history()}
        assert ids == {"a7", "a8", "a9"}


class TestEthicsFilterStats:
    def test_initial_stats(self) -> None:
        f = EthicsFilter()
        s = f.stats()
        assert s["total"] == 0
        assert s["success"] == 0
        assert s["failed"] == 0
        assert s["rolled_back"] == 0
        assert "α" in s["axioms_signed"]
        assert "β" in s["axioms_signed"]
        assert "γ" in s["axioms_signed"]
        assert "δ" in s["axioms_signed"]

    def test_stats_after_operations(self) -> None:
        f = EthicsFilter()
        a1 = Action(id="a1", category="x", target="y", risk=0.0, reversible=True)
        a2 = Action(id="a2", category="x", target="y", risk=0.0, reversible=True)
        a3 = Action(id="a3", category="x", target="y", risk=0.0, reversible=True)
        f.record(a1)
        f.record(a2)
        f.record_failure(a3, "boom")
        f.rollback(a1.id)
        s = f.stats()
        assert s["total"] == 3
        # a1 est rolled_back (statut muté), a2 reste success
        assert s["success"] == 1
        assert s["failed"] == 1
        assert s["rolled_back"] == 1
