"""
Tests pour le TransparencyLog (Axiome β).
"""
from __future__ import annotations

import json
import uuid

import pytest

from ciel.core.identity import demo_identity
from ciel.ethics.transparency import (
    Certificate,
    TransparencyLog,
    global_log,
)


class TestCertificate:
    def test_basic_certificate(self) -> None:
        c = Certificate(
            id=str(uuid.uuid4()),
            action_id="act-1",
            action_category="read_file",
            axioms_consulted=("β",),
            skills_used=("skill_read",),
            reasoning_chain=(("step1", "load file"),),
            inputs=(("path", "/etc/hosts"),),
            outputs=(("size", 256),),
            confidence=0.95,
            signed_at=1718000000,
            signature="a" * 64,
            signatory_uuid="uuid-x",
        )
        assert c.confidence == 0.95
        assert c.axioms_consulted == ("β",)

    def test_invalid_confidence(self) -> None:
        with pytest.raises(ValueError):
            Certificate(
                id="x", action_id="y", action_category="z",
                axioms_consulted=("β",), skills_used=(), reasoning_chain=(),
                inputs=(), outputs=(),
                confidence=1.5,  # invalide
                signed_at=1, signature="a" * 64, signatory_uuid="u",
            )

    def test_invalid_axiom(self) -> None:
        with pytest.raises(ValueError):
            Certificate(
                id="x", action_id="y", action_category="z",
                axioms_consulted=("Z",),  # pas αβγδ
                skills_used=(), reasoning_chain=(),
                inputs=(), outputs=(),
                confidence=0.5, signed_at=1,
                signature="a" * 64, signatory_uuid="u",
            )

    def test_invalid_signature_length(self) -> None:
        with pytest.raises(ValueError):
            Certificate(
                id="x", action_id="y", action_category="z",
                axioms_consulted=("β",), skills_used=(), reasoning_chain=(),
                inputs=(), outputs=(),
                confidence=0.5, signed_at=1,
                signature="abc",  # trop court
                signatory_uuid="u",
            )

    def test_to_json(self) -> None:
        c = Certificate(
            id="x", action_id="y", action_category="z",
            axioms_consulted=("β",), skills_used=(), reasoning_chain=(),
            inputs=(("a", 1),), outputs=(),
            confidence=0.5, signed_at=1,
            signature="a" * 64, signatory_uuid="u",
        )
        j = c.to_json()
        d = json.loads(j)
        assert d["confidence"] == 0.5
        assert d["inputs"] == {"a": 1}


class TestTransparencyLog:
    def test_log_creation(self) -> None:
        log = TransparencyLog()
        assert len(log) == 0

    def test_certify_creates_signed_cert(self) -> None:
        log = TransparencyLog()
        cert = log.certify(
            action_id="a1",
            action_category="read_file",
            axioms_consulted=["β"],
            confidence=0.9,
        )
        assert len(cert.signature) == 64
        assert cert.action_id == "a1"

    def test_find_by_action(self) -> None:
        log = TransparencyLog()
        cert = log.certify(
            action_id="a1", action_category="x", axioms_consulted=["β"],
        )
        found = log.find_by_action("a1")
        assert found is not None
        assert found.id == cert.id

    def test_find_by_action_unknown(self) -> None:
        log = TransparencyLog()
        assert log.find_by_action("unknown") is None

    def test_get_by_id(self) -> None:
        log = TransparencyLog()
        cert = log.certify(
            action_id="a1", action_category="x", axioms_consulted=["β"],
        )
        assert log.get(cert.id) is cert
        assert log.get("unknown") is None

    def test_all_returns_list(self) -> None:
        log = TransparencyLog()
        for i in range(5):
            log.certify(
                action_id=f"a{i}", action_category="x", axioms_consulted=["β"],
            )
        assert len(log.all()) == 5

    def test_stats(self) -> None:
        log = TransparencyLog()
        log.certify(
            action_id="a1", action_category="x",
            axioms_consulted=["α", "β"], confidence=0.9,
        )
        log.certify(
            action_id="a2", action_category="y",
            axioms_consulted=["γ"], confidence=0.7,
        )
        s = log.stats()
        assert s["total_certificates"] == 2
        assert s["axioms_breakdown"]["α"] == 1
        assert s["axioms_breakdown"]["β"] == 1
        assert s["axioms_breakdown"]["γ"] == 1
        assert s["avg_confidence"] == pytest.approx(0.8)

    def test_max_size_trimming(self) -> None:
        log = TransparencyLog(max_size=3)
        for i in range(10):
            log.certify(
                action_id=f"a{i}", action_category="x", axioms_consulted=["β"],
            )
        assert len(log) == 3

    def test_global_log_is_singleton(self) -> None:
        log1 = global_log()
        log2 = global_log()
        assert log1 is log2


class TestCertificateSignature:
    def test_signature_changes_with_payload(self) -> None:
        log = TransparencyLog()
        c1 = log.certify(
            action_id="a1", action_category="x", axioms_consulted=["β"],
            confidence=0.5,
        )
        c2 = log.certify(
            action_id="a1", action_category="x", axioms_consulted=["β"],
            confidence=0.9,  # différente
        )
        # Signatures différentes (payloads différents)
        assert c1.signature != c2.signature
