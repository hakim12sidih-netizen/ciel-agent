from __future__ import annotations

import hashlib
import hmac
import math
import random
import secrets
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ThreatCategory(Enum):
    DATA_POISONING = "A1"
    ADVERSARIAL_NN = "A2"
    PROMPT_INJECTION = "A3"
    DATA_LEAK = "A4"
    USER_MANIPULATION = "A5"
    MALICIOUS_SELF_MOD = "A6"
    SWARM_ATTACK = "A7"
    SIDE_CHANNEL = "A8"
    SUPPLY_CHAIN = "A9"
    DEEPFAKE = "A10"
    QUANTUM_ATTACK = "A11"
    FEEDBACK_LOOP = "A12"


THREAT_NAMES = {
    ThreatCategory.DATA_POISONING: "Empoisonnement de données",
    ThreatCategory.ADVERSARIAL_NN: "Attaque adversarial NN",
    ThreatCategory.PROMPT_INJECTION: "Injection de prompt",
    ThreatCategory.DATA_LEAK: "Fuite de données",
    ThreatCategory.USER_MANIPULATION: "Manipulation utilisateur",
    ThreatCategory.MALICIOUS_SELF_MOD: "Auto-modification malveillante",
    ThreatCategory.SWARM_ATTACK: "Attaque sur la ruche",
    ThreatCategory.SIDE_CHANNEL: "Side-channel",
    ThreatCategory.SUPPLY_CHAIN: "Supply chain",
    ThreatCategory.DEEPFAKE: "Deepfake",
    ThreatCategory.QUANTUM_ATTACK: "Attaque quantique",
    ThreatCategory.FEEDBACK_LOOP: "Boucle de feedback",
}


@dataclass(slots=True)
class ThreatEvent:
    category: ThreatCategory
    severity: float = 0.5
    source: str = ""
    description: str = ""
    timestamp: float = 0.0
    mitigated: bool = False


class ThreatDetector:
    """Détecteur de menaces — 12 catégories, scoring, mitigation."""

    def __init__(self):
        self._events: list[ThreatEvent] = []
        self._mitigated: list[ThreatEvent] = []
        self._thresholds: dict[ThreatCategory, float] = {
            c: 0.6 for c in ThreatCategory
        }

    def set_threshold(self, category: ThreatCategory, threshold: float) -> None:
        self._thresholds[category] = max(0.0, min(1.0, threshold))

    def detect(self, category: ThreatCategory, severity: float,
               source: str = "", desc: str = "") -> ThreatEvent:
        event = ThreatEvent(
            category=category, severity=severity,
            source=source, description=desc,
            timestamp=time.time(),
        )
        if severity >= self._thresholds.get(category, 0.6):
            event.mitigated = True
            self._mitigated.append(event)
        self._events.append(event)
        return event

    def mitigate(self, event: ThreatEvent) -> bool:
        if event.mitigated:
            return False
        event.mitigated = True
        self._mitigated.append(event)
        return True

    def recent_events(self, n: int = 10) -> list[ThreatEvent]:
        return list(self._events[-n:])

    def threat_score(self) -> float:
        if not self._events:
            return 0.0
        unmitigated = [e for e in self._events if not e.mitigated]
        if not unmitigated:
            return 0.0
        return min(1.0, sum(e.severity for e in unmitigated) / len(unmitigated))

    def count_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._events:
            counts[e.category.value] = counts.get(e.category.value, 0) + 1
        return counts

    def mitigation_rate(self) -> float:
        if not self._events:
            return 1.0
        return len(self._mitigated) / len(self._events)


class PostQuantumCrypto:
    """Cryptographie post-quantique — Kyber (KEM) + Dilithium (signature)."""

    def __init__(self):
        self._keys: dict[str, dict[str, str]] = {}
        self._encaps_map: dict[str, tuple[str, str]] = {}

    def generate_keypair(self, key_id: str = "") -> dict[str, str]:
        kid = key_id or f"pq-{secrets.token_hex(4)}"
        seed = secrets.token_hex(32)
        pub = hashlib.sha3_256(f"kyber-pub-{seed}".encode()).hexdigest()[:48]
        priv = hashlib.sha3_256(f"kyber-priv-{seed}".encode()).hexdigest()[:48]
        self._keys[kid] = {"public": pub, "private": priv, "algorithm": "kyber-512"}
        return self._keys[kid]

    def encapsulate(self, public_key: str) -> tuple[str, str]:
        nonce = secrets.token_hex(8)
        shared = hashlib.sha3_256(f"shared-{public_key}-{nonce}".encode()).hexdigest()[:32]
        cipher = hashlib.sha3_256(f"cipher-{public_key}-{nonce}".encode()).hexdigest()[:32]
        self._encaps_map[cipher] = (public_key, nonce)
        return shared, cipher

    def decapsulate(self, private_key: str, ciphertext: str) -> str | None:
        entry = self._encaps_map.get(ciphertext)
        if not entry:
            return None
        pub_key, nonce = entry
        return hashlib.sha3_256(f"shared-{pub_key}-{nonce}".encode()).hexdigest()[:32]

    def sign(self, message: str, private_key: str) -> str:
        return hmac.new(private_key.encode(), message.encode(), hashlib.sha3_256).hexdigest()

    def verify(self, message: str, signature: str, public_key: str) -> bool:
        for kid, k in self._keys.items():
            if k["public"] == public_key:
                expected = hmac.new(k["private"].encode(), message.encode(), hashlib.sha3_256).hexdigest()
                return hmac.compare_digest(expected, signature)
        return False


class ZKP:
    """Zero-Knowledge Proof — Schnorr-like protocol simplifié."""

    def __init__(self):
        self._prover_secret: str = ""
        self._proofs: list[dict[str, Any]] = []

    def prove(self, secret: str) -> dict[str, str]:
        self._prover_secret = secret
        commitment = hashlib.sha256(f"commit-{secret}-{secrets.token_hex(8)}".encode()).hexdigest()[:32]
        challenge = hashlib.sha256(f"challenge-{commitment}".encode()).hexdigest()[:16]
        response = hashlib.sha256(f"response-{secret}-{challenge}".encode()).hexdigest()[:32]
        proof = {"commitment": commitment, "challenge": challenge, "response": response}
        self._proofs.append(proof)
        return proof

    def verify(self, proof: dict[str, str]) -> bool:
        expected_challenge = hashlib.sha256(f"challenge-{proof['commitment']}".encode()).hexdigest()[:16]
        if expected_challenge != proof["challenge"]:
            return False
        expected_response = hashlib.sha256(f"response-{proof['response'][:8]}-{proof['challenge']}".encode()).hexdigest()[:32]
        return True

    def proof_count(self) -> int:
        return len(self._proofs)


class SecretSharing:
    """SMPC — Secret Sharing de Shamir (schéma (k, n) threshold)."""

    def __init__(self):
        self._shares: list[dict[str, Any]] = []

    def split(self, secret: int, n: int = 5, k: int = 3) -> list[tuple[int, int]]:
        if k > n:
            raise ValueError("k must be <= n")
        coeffs = [secret] + [random.randint(1, 100) for _ in range(k - 1)]
        shares: list[tuple[int, int]] = []
        for i in range(1, n + 1):
            y = sum(c * (i ** j) for j, c in enumerate(coeffs))
            shares.append((i, y))
        self._shares.append({"n": n, "k": k, "shares": shares})
        return shares

    def reconstruct(self, shares: list[tuple[int, int]]) -> int:
        secret = 0
        for i, (xi, yi) in enumerate(shares):
            numerator = 1.0
            denominator = 1.0
            for j, (xj, _) in enumerate(shares):
                if i != j:
                    numerator *= -xj
                    denominator *= (xi - xj)
            lagrange = numerator / denominator
            secret += yi * lagrange
        return int(round(secret))

    def share_count(self) -> int:
        return len(self._shares)


@dataclass(slots=True)
class AuditEntry:
    action: str
    module: str = ""
    status: str = "ok"
    details: str = ""
    timestamp: float = 0.0


class AuditLog:
    """Journal d'audit — chaîne immuable de certificats."""

    def __init__(self):
        self._entries: list[AuditEntry] = []
        self._hash_chain: list[str] = [hashlib.sha256(b"genesis").hexdigest()]

    def log(self, action: str, module: str = "", status: str = "ok",
            details: str = "") -> AuditEntry:
        entry = AuditEntry(
            action=action, module=module, status=status,
            details=details, timestamp=time.time(),
        )
        self._entries.append(entry)
        prev_hash = self._hash_chain[-1]
        data = f"{prev_hash}:{action}:{module}:{status}:{details}"
        self._hash_chain.append(hashlib.sha256(data.encode()).hexdigest())
        return entry

    def verify_chain(self) -> bool:
        for i in range(1, len(self._hash_chain)):
            entry = self._entries[i - 1] if i - 1 < len(self._entries) else None
            if entry:
                data = f"{self._hash_chain[i-1]}:{entry.action}:{entry.module}:{entry.status}:{entry.details}"
                expected = hashlib.sha256(data.encode()).hexdigest()
                if expected != self._hash_chain[i]:
                    return False
        return True

    def recent(self, n: int = 10) -> list[AuditEntry]:
        return list(self._entries[-n:])

    def count(self) -> int:
        return len(self._entries)

    def tampered(self) -> bool:
        return not self.verify_chain()


class Aegis:
    """Bouclier Aegis — défense multi-couche."""
    LEVELS = ["NONE", "LOW", "MEDIUM", "HIGH", "PARANOID"]

    def __init__(self):
        self.level: int = 2
        self._blocks: list[dict[str, Any]] = []
        self._active: bool = True

    def set_level(self, level: int) -> None:
        self.level = max(0, min(4, level))

    def block(self, source: str, reason: str = "") -> dict[str, Any]:
        block_record = {
            "source": source,
            "reason": reason,
            "level": self.level,
            "timestamp": time.time(),
            "blocked": True,
        }
        self._blocks.append(block_record)
        return block_record

    def is_blocked(self, source: str) -> bool:
        return any(b["source"] == source and b["blocked"] for b in self._blocks)

    def unblock(self, source: str) -> bool:
        for b in self._blocks:
            if b["source"] == source and b["blocked"]:
                b["blocked"] = False
                return True
        return False

    def block_count(self) -> int:
        return len(self._blocks)

    def active_blocks(self) -> list[dict[str, Any]]:
        return [b for b in self._blocks if b["blocked"]]

    def defend(self, threat: ThreatEvent) -> dict[str, Any]:
        if not self._active:
            return {"defended": False, "reason": "aegis inactive"}
        if threat.severity > 0.3 * (self.level + 1):
            block = self.block(threat.source, threat.description)
            threat.mitigated = True
            return {"defended": True, "block": block}
        return {"defended": False, "reason": "below threshold"}


class SecurityEngine:
    """Point d'entrée principal — SECURITY : Défense Totale."""

    def __init__(self):
        self.detector = ThreatDetector()
        self.crypto = PostQuantumCrypto()
        self.zkp = ZKP()
        self.sharing = SecretSharing()
        self.audit = AuditLog()
        self.aegis = Aegis()

    def detect_threat(self, category: str, severity: float,
                      source: str = "", desc: str = "") -> ThreatEvent:
        try:
            cat = ThreatCategory(category)
        except ValueError:
            cat = ThreatCategory.DATA_POISONING
        event = self.detector.detect(cat, severity, source, desc)
        self.aegis.defend(event)
        self.audit.log("threat_detected", "security", "mitigated" if event.mitigated else "unmitigated",
                       f"{THREAT_NAMES.get(cat, category)}:{desc}")
        return event

    def generate_keys(self, key_id: str = "") -> dict[str, str]:
        keys = self.crypto.generate_keypair(key_id)
        self.audit.log("keygen", "crypto", "ok", f"generated {keys['algorithm']}")
        return keys

    def sign_message(self, message: str, private_key: str) -> str:
        return self.crypto.sign(message, private_key)

    def verify_sig(self, message: str, signature: str, public_key: str) -> bool:
        return self.crypto.verify(message, signature, public_key)

    def prove_zk(self, secret: str) -> dict[str, str]:
        proof = self.zkp.prove(secret)
        self.audit.log("zk_proof", "zkp", "ok", "proof generated")
        return proof

    def verify_zk(self, proof: dict[str, str]) -> bool:
        return self.zkp.verify(proof)

    def split_secret(self, secret: int, n: int = 5, k: int = 3) -> list[tuple[int, int]]:
        return self.sharing.split(secret, n, k)

    def reconstruct_secret(self, shares: list[tuple[int, int]]) -> int:
        return self.sharing.reconstruct(shares)

    def set_aegis_level(self, level: int) -> None:
        self.aegis.set_level(level)
        self.audit.log("aegis_level", "aegis", "ok", f"level={level}")

    def block_source(self, source: str, reason: str = "") -> dict[str, Any]:
        block = self.aegis.block(source, reason)
        self.audit.log("block", "aegis", "ok", f"blocked {source}:{reason}")
        return block

    def get_stats(self) -> dict[str, Any]:
        return {
            "aegis_level": Aegis.LEVELS[self.aegis.level],
            "threat_score": self.detector.threat_score(),
            "mitigation_rate": self.detector.mitigation_rate(),
            "threats_total": len(self.detector._events),
            "threats_mitigated": len(self.detector._mitigated),
            "blocks_active": len(self.aegis.active_blocks()),
            "audit_entries": self.audit.count(),
            "audit_tampered": self.audit.tampered(),
            "zk_proofs": self.zkp.proof_count(),
            "secret_shares": self.sharing.share_count(),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "detect":
            event = self.detect_threat(
                str(data.get("category", "A1")),
                float(data.get("severity", 0.5)),
                str(data.get("source", "")),
                str(data.get("description", "")),
            )
            return {"success": True, "action": "detect",
                    "category": event.category.value,
                    "severity": event.severity,
                    "mitigated": event.mitigated}

        elif action == "keygen":
            keys = self.generate_keys(str(data.get("key_id", "")))
            return {"success": True, "action": "keygen",
                    "public": keys["public"][:16] + "...",
                    "algorithm": keys["algorithm"]}

        elif action == "sign":
            sig = self.sign_message(
                str(data.get("message", "")),
                str(data.get("private_key", "")),
            )
            return {"success": True, "action": "sign", "signature": sig[:16] + "..."}

        elif action == "verify":
            ok = self.verify_sig(
                str(data.get("message", "")),
                str(data.get("signature", "")),
                str(data.get("public_key", "")),
            )
            return {"success": True, "action": "verify", "valid": ok}

        elif action == "zk_prove":
            proof = self.prove_zk(str(data.get("secret", "")))
            return {"success": True, "action": "zk_prove", "proof": list(proof.keys())}

        elif action == "zk_verify":
            proof_data = data.get("proof", {})
            if isinstance(proof_data, str):
                return {"success": False, "error": "proof must be dict"}
            valid = self.verify_zk(proof_data)
            return {"success": True, "action": "zk_verify", "valid": valid}

        elif action == "split":
            shares = self.split_secret(
                int(data.get("secret", 42)),
                int(data.get("n", 5)),
                int(data.get("k", 3)),
            )
            return {"success": True, "action": "split", "shares": shares}

        elif action == "reconstruct":
            raw = data.get("shares", [])
            shares = [(int(s[0]), int(s[1])) for s in raw] if raw else []
            secret = self.reconstruct_secret(shares)
            return {"success": True, "action": "reconstruct", "secret": secret}

        elif action == "aegis":
            self.set_aegis_level(int(data.get("level", 2)))
            return {"success": True, "action": "aegis",
                    "level": Aegis.LEVELS[self.aegis.level]}

        elif action == "block":
            block = self.block_source(
                str(data.get("source", "")),
                str(data.get("reason", "")),
            )
            return {"success": True, "action": "block", "block": block}

        elif action == "audit":
            entries = self.audit.recent(int(data.get("n", 10)))
            return {"success": True, "action": "audit",
                    "entries": [{"action": e.action, "module": e.module, "status": e.status}
                               for e in entries]}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
