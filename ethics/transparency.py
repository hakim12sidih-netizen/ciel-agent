"""
CIEL v∞.2 — Transparency : certificats d'explication (Axiome β).

Chaque décision importante de CIEL produit un Certificate qui :
  - Décrit l'action effectuée
  - Liste les axiomes consultés
  - Référence les skills impliqués
  - Peut être signé cryptographiquement
  - Est auditable à tout moment

Format :
  Certificate {
    id, action, axioms_consulted, skills_used,
    reasoning_chain, signed_at, signature
  }
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.core.crypto import blake2b
from ciel.core.identity import Identity, demo_identity


@dataclass(frozen=True, slots=True)
class Certificate:
    """Certificat d'explication pour une décision.

    Immutable : une fois créé et signé, il ne change plus.
    """

    id: str
    action_id: str
    action_category: str
    axioms_consulted: tuple[str, ...]
    skills_used: tuple[str, ...]
    reasoning_chain: tuple[tuple[str, str], ...]  # [(step_id, description), ...]
    inputs: tuple[tuple[str, Any], ...]
    outputs: tuple[tuple[str, Any], ...]
    confidence: float
    signed_at: int
    signature: str  # 32 bytes hex = 64 chars
    signatory_uuid: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence doit être entre 0 et 1, reçu {self.confidence}")
        for a in self.axioms_consulted:
            if a not in ("α", "β", "γ", "δ"):
                raise ValueError(f"axiome inconnu dans certificat : {a!r}")
        if len(self.signature) != 64:
            raise ValueError(f"signature doit faire 64 chars hex, reçu {len(self.signature)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action_id": self.action_id,
            "action_category": self.action_category,
            "axioms_consulted": list(self.axioms_consulted),
            "skills_used": list(self.skills_used),
            "reasoning_chain": list(self.reasoning_chain),
            "inputs": dict(self.inputs),
            "outputs": dict(self.outputs),
            "confidence": self.confidence,
            "signed_at": self.signed_at,
            "signature": self.signature,
            "signatory_uuid": self.signatory_uuid,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class TransparencyLog:
    """Journal de tous les certificats d'explication.

    Append-only : aucune mutation possible. L'audit (Axiome β) lit
    ce journal pour répondre à "POURQUOI as-tu fait ça ?"
    """

    def __init__(self, max_size: int = 100_000) -> None:
        self._certs: list[Certificate] = []
        self._max_size = max_size
        self._by_action: dict[str, str] = {}  # action_id → cert_id

    def certify(
        self,
        action_id: str,
        action_category: str,
        axioms_consulted: list[str] | tuple[str, ...],
        skills_used: list[str] | tuple[str, ...] = (),
        reasoning_chain: list[tuple[str, str]] | None = None,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        confidence: float = 1.0,
        identity: Identity | None = None,
    ) -> Certificate:
        """Crée et signe un certificat d'explication.

        Args:
            action_id: ID de l'action certifiée
            action_category: Catégorie de l'action
            axioms_consulted: Liste des axiomes mobilisés (α/β/γ/δ)
            skills_used: Liste des skills impliqués
            reasoning_chain: Liste (step_id, description) du raisonnement
            inputs: Entrées de la décision
            outputs: Sorties de la décision
            confidence: Niveau de confiance [0, 1]
            identity: Identité signataire (démo par défaut)
        """
        id_ = identity or demo_identity()
        signed_at = int(time.time())
        # Construit le payload à signer
        payload = json.dumps(
            {
                "action_id": action_id,
                "action_category": action_category,
                "axioms_consulted": sorted(axioms_consulted),
                "skills_used": sorted(skills_used),
                "reasoning_chain": reasoning_chain or [],
                "inputs": inputs or {},
                "outputs": outputs or {},
                "confidence": confidence,
                "signed_at": signed_at,
                "signatory_uuid": id_.uuid,
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        signature = blake2b(payload, digest_size=32, domain=b"CIELTRANSP").hex()

        cert = Certificate(
            id=str(uuid.uuid4()),
            action_id=action_id,
            action_category=action_category,
            axioms_consulted=tuple(axioms_consulted),
            skills_used=tuple(skills_used),
            reasoning_chain=tuple(reasoning_chain or []),
            inputs=tuple(sorted((inputs or {}).items())),
            outputs=tuple(sorted((outputs or {}).items())),
            confidence=confidence,
            signed_at=signed_at,
            signature=signature,
            signatory_uuid=id_.uuid,
        )
        self._certs.append(cert)
        self._by_action[action_id] = cert.id
        if len(self._certs) > self._max_size:
            self._certs = self._certs[-self._max_size :]
        return cert

    def get(self, cert_id: str) -> Certificate | None:
        """Récupère un certificat par son ID."""
        for c in self._certs:
            if c.id == cert_id:
                return c
        return None

    def find_by_action(self, action_id: str) -> Certificate | None:
        """Récupère le certificat d'une action."""
        cert_id = self._by_action.get(action_id)
        if cert_id is None:
            return None
        return self.get(cert_id)

    def all(self) -> list[Certificate]:
        """Liste complète (lecture seule)."""
        return list(self._certs)

    def __len__(self) -> int:
        return len(self._certs)

    def stats(self) -> dict[str, Any]:
        axioms_count: dict[str, int] = {"α": 0, "β": 0, "γ": 0, "δ": 0}
        for c in self._certs:
            for a in c.axioms_consulted:
                axioms_count[a] = axioms_count.get(a, 0) + 1
        return {
            "total_certificates": len(self._certs),
            "axioms_breakdown": axioms_count,
            "avg_confidence": (
                sum(c.confidence for c in self._certs) / len(self._certs)
                if self._certs
                else 0.0
            ),
        }


# Module-level singleton
_LOG = TransparencyLog()


def global_log() -> TransparencyLog:
    """Retourne le journal global de transparence."""
    return _LOG
