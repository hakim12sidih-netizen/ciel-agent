from __future__ import annotations

import pytest
from ciel.security.core import (
    ThreatCategory, ThreatEvent, ThreatDetector,
    PostQuantumCrypto, ZKP, SecretSharing,
    AuditEntry, AuditLog, Aegis,
    SecurityEngine, THREAT_NAMES,
)


class TestThreatCategory:
    def test_all_categories(self):
        assert len(ThreatCategory) == 12
        assert ThreatCategory.DATA_POISONING.value == "A1"
        assert ThreatCategory.FEEDBACK_LOOP.value == "A12"

    def test_threat_names(self):
        assert THREAT_NAMES[ThreatCategory.PROMPT_INJECTION] == "Injection de prompt"
        assert THREAT_NAMES[ThreatCategory.QUANTUM_ATTACK] == "Attaque quantique"


class TestThreatEvent:
    def test_create(self):
        e = ThreatEvent(ThreatCategory.DATA_POISONING, severity=0.8, source="test", description="poison")
        assert e.category == ThreatCategory.DATA_POISONING
        assert e.severity == 0.8
        assert e.mitigated is False


class TestThreatDetector:
    def test_create(self):
        d = ThreatDetector()
        assert d.threat_score() == 0.0
        assert d.mitigation_rate() == 1.0

    def test_detect_below_threshold(self):
        d = ThreatDetector()
        event = d.detect(ThreatCategory.DATA_POISONING, 0.3)
        assert event.mitigated is False
        assert len(d._events) == 1

    def test_detect_above_threshold(self):
        d = ThreatDetector()
        event = d.detect(ThreatCategory.DATA_POISONING, 0.9)
        assert event.mitigated is True

    def test_set_threshold(self):
        d = ThreatDetector()
        d.set_threshold(ThreatCategory.DATA_POISONING, 0.2)
        event = d.detect(ThreatCategory.DATA_POISONING, 0.3)
        assert event.mitigated is True

    def test_mitigate(self):
        d = ThreatDetector()
        event = d.detect(ThreatCategory.ADVERSARIAL_NN, 0.4)
        assert event.mitigated is False
        assert d.mitigate(event) is True
        assert d.mitigate(event) is False

    def test_threat_score(self):
        d = ThreatDetector()
        d.detect(ThreatCategory.DATA_POISONING, 0.8)
        d.detect(ThreatCategory.ADVERSARIAL_NN, 0.2)
        assert d.threat_score() > 0

    def test_count_by_category(self):
        d = ThreatDetector()
        d.detect(ThreatCategory.DATA_POISONING, 0.5)
        d.detect(ThreatCategory.DATA_POISONING, 0.6)
        d.detect(ThreatCategory.PROMPT_INJECTION, 0.7)
        counts = d.count_by_category()
        assert counts["A1"] == 2
        assert counts["A3"] == 1

    def test_mitigation_rate(self):
        d = ThreatDetector()
        assert d.mitigation_rate() == 1.0
        d.detect(ThreatCategory.DATA_POISONING, 0.3)
        assert d.mitigation_rate() < 1.0

    def test_recent_events(self):
        d = ThreatDetector()
        for i in range(20):
            d.detect(ThreatCategory.DATA_POISONING, 0.5)
        assert len(d.recent_events(5)) == 5


class TestPostQuantumCrypto:
    def test_generate_keypair(self):
        c = PostQuantumCrypto()
        keys = c.generate_keypair("test1")
        assert "public" in keys
        assert "private" in keys
        assert keys["algorithm"] == "kyber-512"

    def test_encapsulate_decapsulate(self):
        c = PostQuantumCrypto()
        keys = c.generate_keypair()
        shared, cipher = c.encapsulate(keys["public"])
        assert len(shared) == 32
        recovered = c.decapsulate(keys["private"], cipher)
        assert recovered == shared

    def test_decapsulate_wrong_cipher(self):
        c = PostQuantumCrypto()
        keys = c.generate_keypair()
        assert c.decapsulate(keys["private"], "badcipher") is None

    def test_sign_verify(self):
        c = PostQuantumCrypto()
        keys = c.generate_keypair()
        sig = c.sign("message123", keys["private"])
        assert c.verify("message123", sig, keys["public"]) is True
        assert c.verify("wrong", sig, keys["public"]) is False


class TestZKP:
    def test_prove(self):
        z = ZKP()
        proof = z.prove("mysecret")
        assert "commitment" in proof
        assert "challenge" in proof
        assert "response" in proof

    def test_verify(self):
        z = ZKP()
        proof = z.prove("secret")
        assert z.verify(proof) is True

    def test_proof_count(self):
        z = ZKP()
        assert z.proof_count() == 0
        z.prove("a")
        z.prove("b")
        assert z.proof_count() == 2


class TestSecretSharing:
    def test_split(self):
        s = SecretSharing()
        shares = s.split(42, n=5, k=3)
        assert len(shares) == 5
        assert s.share_count() == 1

    def test_reconstruct(self):
        s = SecretSharing()
        shares = s.split(123, n=5, k=3)
        secret = s.reconstruct(shares[:3])
        assert secret == 123

    def test_reconstruct_wrong_shares(self):
        s = SecretSharing()
        shares = s.split(42, n=5, k=3)
        secret = s.reconstruct(shares[:2])
        assert secret != 42

    def test_split_invalid(self):
        s = SecretSharing()
        with pytest.raises(ValueError):
            s.split(42, n=3, k=5)


class TestAuditLog:
    def test_create(self):
        a = AuditLog()
        assert a.count() == 0
        assert a.verify_chain() is True

    def test_log(self):
        a = AuditLog()
        entry = a.log("test_action", "core", "ok", "details here")
        assert entry.action == "test_action"
        assert a.count() == 1

    def test_verify_chain(self):
        a = AuditLog()
        a.log("action1")
        a.log("action2")
        assert a.verify_chain() is True

    def test_tampered(self):
        a = AuditLog()
        a.log("action1")
        a.log("action2")
        assert a.tampered() is False
        a._hash_chain[-1] = "tampered"
        assert a.tampered() is True

    def test_recent(self):
        a = AuditLog()
        for i in range(5):
            a.log(f"action{i}")
        assert len(a.recent(3)) == 3


class TestAegis:
    def test_default_level(self):
        a = Aegis()
        assert a.level == 2
        assert a._active is True

    def test_set_level(self):
        a = Aegis()
        a.set_level(4)
        assert a.level == 4
        a.set_level(99)
        assert a.level == 4
        a.set_level(-1)
        assert a.level == 0

    def test_block(self):
        a = Aegis()
        block = a.block("bad_actor", "suspicious activity")
        assert block["blocked"] is True
        assert a.block_count() == 1

    def test_is_blocked(self):
        a = Aegis()
        a.block("src1")
        a.block("src2")
        assert a.is_blocked("src1") is True
        assert a.is_blocked("src3") is False

    def test_unblock(self):
        a = Aegis()
        a.block("src")
        assert a.unblock("src") is True
        assert a.is_blocked("src") is False
        assert a.unblock("src") is False

    def test_active_blocks(self):
        a = Aegis()
        a.block("a")
        a.block("b")
        a.unblock("a")
        assert len(a.active_blocks()) == 1

    def test_defend_low_threat(self):
        a = Aegis()
        a.set_level(4)
        threat = ThreatEvent(ThreatCategory.DATA_POISONING, severity=0.1)
        result = a.defend(threat)
        assert result["defended"] is False


class TestSecurityEngine:
    def test_create(self):
        e = SecurityEngine()
        assert e.detector is not None
        assert e.crypto is not None
        assert e.aegis is not None

    def test_detect_threat(self):
        e = SecurityEngine()
        event = e.detect_threat("A1", 0.9, "attacker", "data poison")
        assert event.mitigated is True
        assert event.category == ThreatCategory.DATA_POISONING

    def test_generate_keys(self):
        e = SecurityEngine()
        keys = e.generate_keys("node1")
        assert "public" in keys
        assert "private" in keys

    def test_sign_and_verify(self):
        e = SecurityEngine()
        keys = e.generate_keys()
        sig = e.sign_message("hello", keys["private"])
        assert e.verify_sig("hello", sig, keys["public"]) is True
        assert e.verify_sig("wrong", sig, keys["public"]) is False

    def test_zk_prove_verify(self):
        e = SecurityEngine()
        proof = e.prove_zk("mysecret")
        assert e.verify_zk(proof) is True

    def test_split_reconstruct(self):
        e = SecurityEngine()
        shares = e.split_secret(42, n=5, k=3)
        secret = e.reconstruct_secret(shares[:3])
        assert secret == 42

    def test_set_aegis_level(self):
        e = SecurityEngine()
        e.set_aegis_level(4)
        assert e.aegis.level == 4

    def test_block_source(self):
        e = SecurityEngine()
        block = e.block_source("hacker", "attack detected")
        assert block["blocked"] is True

    def test_get_stats(self):
        e = SecurityEngine()
        stats = e.get_stats()
        assert "aegis_level" in stats
        assert "threat_score" in stats
        assert "audit_entries" in stats
        assert "threats_total" in stats

    def test_process_detect(self):
        e = SecurityEngine()
        r = e.process({"action": "detect", "category": "A1", "severity": 0.8})
        assert r["success"] is True
        assert r["mitigated"] is True

    def test_process_keygen(self):
        e = SecurityEngine()
        r = e.process({"action": "keygen"})
        assert r["success"] is True
        assert "public" in r

    def test_process_sign(self):
        e = SecurityEngine()
        r = e.process({"action": "sign", "message": "test", "private_key": "abc"})
        assert r["success"] is True
        assert "signature" in r

    def test_process_verify(self):
        e = SecurityEngine()
        r = e.process({"action": "verify", "message": "test", "signature": "sig", "public_key": "pk"})
        assert r["success"] is True
        assert "valid" in r

    def test_process_zk_prove(self):
        e = SecurityEngine()
        r = e.process({"action": "zk_prove", "secret": "s3cr3t"})
        assert r["success"] is True
        assert "proof" in r

    def test_process_zk_verify(self):
        e = SecurityEngine()
        p = e.prove_zk("x")
        r = e.process({"action": "zk_verify", "proof": p})
        assert r["success"] is True
        assert r["valid"] is True

    def test_process_split(self):
        e = SecurityEngine()
        r = e.process({"action": "split", "secret": 42, "n": 5, "k": 3})
        assert r["success"] is True
        assert len(r["shares"]) == 5

    def test_process_reconstruct(self):
        e = SecurityEngine()
        r = e.process({"action": "split", "secret": 99, "n": 3, "k": 2})
        shares = r["shares"]
        r2 = e.process({"action": "reconstruct", "shares": shares[:2]})
        assert r2["success"] is True
        assert r2["secret"] == 99

    def test_process_aegis(self):
        e = SecurityEngine()
        r = e.process({"action": "aegis", "level": 4})
        assert r["success"] is True
        assert r["level"] == "PARANOID"

    def test_process_block(self):
        e = SecurityEngine()
        r = e.process({"action": "block", "source": "bad", "reason": "attack"})
        assert r["success"] is True
        assert r["block"]["blocked"] is True

    def test_process_audit(self):
        e = SecurityEngine()
        e.detect_threat("A1", 0.5, "t", "test")
        r = e.process({"action": "audit", "n": 5})
        assert r["success"] is True
        assert len(r["entries"]) >= 1

    def test_process_stats(self):
        e = SecurityEngine()
        r = e.process({"action": "stats"})
        assert r["success"] is True

    def test_process_bad_action(self):
        e = SecurityEngine()
        r = e.process({"action": "nonexistent"})
        assert r["success"] is False

    def test_process_bad_input(self):
        e = SecurityEngine()
        r = e.process("bad")
        assert r["success"] is False
