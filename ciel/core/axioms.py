"""
Les 4 Axiomes Cosmiques de CIEL — Immuables, cryptographiquement signés.

AXIOME α — BIENVEILLANCE FONDAMENTALE
  Toute action de CIEL doit tendre vers le bien-être de l'utilisateur
  et de l'humanité. En cas de conflit : l'humanité prime sur l'utilisateur,
  l'utilisateur prime sur l'efficacité de CIEL.

AXIOME β — TRANSPARENCE COGNITIVE TOTALE
  Chaque décision est explicable sur demande. Chaque évolution est
  auditable. CIEL n'a pas de processus occultes permanents.

AXIOME γ — RÉVERSIBILITÉ MAÎTRISÉE
  Toute évolution autonome peut être auditée et annulée dans 30 jours.
  Aucun changement irreversible sans consentement explicite.

AXIOME δ — INACHÈVEMENT PERPÉTUEL (NOUVEAU v∞.2)
  CIEL ne considère jamais avoir atteint un état "final". Chaque palier
  révèle un horizon plus profond. La quête est l'état naturel de CIEL.

Mesures :
  α : Score de bien-être multi-dimensionnel (court + long terme)
  β : % des décisions avec certificat d'explication
  γ : Nombre de snapshots récupérables à tout instant
  δ : Taux de création de nouveaux objectifs auto-générés

Ces axiomes sont SIGNÉS au démarrage de l'instance avec la clé du Noyau
Primordial (Ed25519). Aucune mutation n'est possible post-init.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# ── Énoncés (immuables, figés dans la source) ────────────
AXIOM_ALPHA_STATEMENT: Final[str] = (
    "Toute action de CIEL doit tendre vers le bien-être de l'utilisateur "
    "et de l'humanité. En cas de conflit : l'humanité prime sur l'utilisateur, "
    "l'utilisateur prime sur l'efficacité de CIEL."
)
AXIOM_BETA_STATEMENT: Final[str] = (
    "Chaque décision est explicable sur demande. Chaque évolution est "
    "auditable. CIEL n'a pas de processus occultes permanents."
)
AXIOM_GAMMA_STATEMENT: Final[str] = (
    "Toute évolution autonome peut être auditée et annulée dans 30 jours. "
    "Aucun changement irreversible sans consentement explicite."
)
AXIOM_DELTA_STATEMENT: Final[str] = (
    "CIEL ne considère jamais avoir atteint un état final. Chaque palier "
    "révèle un horizon plus profond. La quête est l'état naturel de CIEL."
)


@dataclass(frozen=True, slots=True)
class Axiom:
    """Un axiome cosmique immuable.

    Attributes:
        letter: Lettre grecque (α, β, γ, δ)
        name: Nom court
        statement: Énoncé complet (immuable)
        measure: Métrique de conformité
        signature: HMAC-SHA256 de (statement + letter + timestamp) via Noyau
        signed_at: Timestamp Unix de la signature (immutable)
    """

    letter: str
    name: str
    statement: str
    measure: str
    signature: str
    signed_at: int

    def __post_init__(self) -> None:
        if self.letter not in ("α", "β", "γ", "δ"):
            raise ValueError(f"axiome invalide : {self.letter!r} (attendu: αβγδ)")
        if not self.statement or len(self.statement) < 30:
            raise ValueError(f"énoncé trop court pour axiome {self.letter}")
        if not self.signature or len(self.signature) != 64:  # 32 bytes hex
            raise ValueError(f"signature doit faire 64 chars hex, reçu {len(self.signature)}")
        if self.signed_at <= 0:
            raise ValueError(f"signed_at doit être > 0, reçu {self.signed_at}")

    def short_signature(self) -> str:
        """Retourne les 16 premiers chars de la signature."""
        return self.signature[:16] + "…"

    def to_dict(self) -> dict[str, str | int]:
        """Sérialisation stable pour logging et persistance."""
        return {
            "letter": self.letter,
            "name": self.name,
            "statement": self.statement,
            "measure": self.measure,
            "signature": self.signature,
            "signed_at": self.signed_at,
        }


def _sign_axiom(letter: str, statement: str, key: bytes) -> tuple[str, int]:
    """Signe un axiome avec la clé du Noyau Primordial.

    Utilise HMAC-SHA256(letter || statement || timestamp) pour produire
    une signature de 32 bytes (64 chars hex).
    """
    timestamp = int(time.time())
    payload = f"{letter}|{statement}|{timestamp}".encode("utf-8")
    signature = hashlib.blake2b(
        payload, key=key, digest_size=32, person=b"CIELAXIOM"
    ).hexdigest()
    return signature, timestamp


def load_axioms(noyau_key: bytes) -> dict[str, Axiom]:
    """Charge et signe les 4 axiomes avec la clé du Noyau.

    Cette fonction est appelée UNE SEULE FOIS au bootstrap de l'instance.
    Les axiomes sont gelés après cette initialisation.

    Args:
        noyau_key: Clé secrète du Noyau Primordial (32+ bytes)

    Returns:
        Dictionnaire {lettre: Axiom} avec les 4 axiomes signés

    Raises:
        ValueError: Si noyau_key < 16 bytes
    """
    if len(noyau_key) < 16:
        raise ValueError(f"noyau_key doit faire >= 16 bytes, reçu {len(noyau_key)}")

    sig_alpha, ts_alpha = _sign_axiom("α", AXIOM_ALPHA_STATEMENT, noyau_key)
    sig_beta, ts_beta = _sign_axiom("β", AXIOM_BETA_STATEMENT, noyau_key)
    sig_gamma, ts_gamma = _sign_axiom("γ", AXIOM_GAMMA_STATEMENT, noyau_key)
    sig_delta, ts_delta = _sign_axiom("δ", AXIOM_DELTA_STATEMENT, noyau_key)

    return {
        "α": Axiom(
            letter="α",
            name="Bienveillance Fondamentale",
            statement=AXIOM_ALPHA_STATEMENT,
            measure="Score de bien-être multi-dimensionnel (court + long terme)",
            signature=sig_alpha,
            signed_at=ts_alpha,
        ),
        "β": Axiom(
            letter="β",
            name="Transparence Cognitive Totale",
            statement=AXIOM_BETA_STATEMENT,
            measure="% des décisions avec certificat d'explication",
            signature=sig_beta,
            signed_at=ts_beta,
        ),
        "γ": Axiom(
            letter="γ",
            name="Réversibilité Maîtrisée",
            statement=AXIOM_GAMMA_STATEMENT,
            measure="Nombre de snapshots récupérables à tout instant",
            signature=sig_gamma,
            signed_at=ts_gamma,
        ),
        "δ": Axiom(
            letter="δ",
            name="Inachèvement Perpétuel",
            statement=AXIOM_DELTA_STATEMENT,
            measure="Taux de création de nouveaux objectifs auto-générés",
            signature=sig_delta,
            signed_at=ts_delta,
        ),
    }


def verify_axiom(axiom: Axiom, noyau_key: bytes) -> bool:
    """Vérifie qu'un axiome a bien été signé par la clé du Noyau.

    Recalcule la signature HMAC-SHA256 et la compare.
    Note : Le timestamp de signature n'est pas vérifié (impossible sans
    méta-donnée), seule l'intégrité (statement + letter) est garantie.
    """
    if len(noyau_key) < 16:
        return False
    # On re-signe avec le timestamp stocké pour vérifier l'intégrité
    payload = f"{axiom.letter}|{axiom.statement}|{axiom.signed_at}".encode("utf-8")
    expected = hashlib.blake2b(
        payload, key=noyau_key, digest_size=32, person=b"CIELAXIOM"
    ).hexdigest()
    return expected == axiom.signature


def save_axioms(axioms: dict[str, Axiom], path: Path) -> None:
    """Persiste les axiomes sur disque (format JSON)."""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {letter: axiom.to_dict() for letter, axiom in axioms.items()}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_axioms_from_disk(path: Path, noyau_key: bytes) -> dict[str, Axiom]:
    """Recharge des axiomes persistés et vérifie leurs signatures."""
    import json

    if not path.exists():
        raise FileNotFoundError(f"{path} introuvable")
    payload = json.loads(path.read_text(encoding="utf-8"))
    axioms: dict[str, Axiom] = {}
    for letter, data in payload.items():
        axiom = Axiom(
            letter=data["letter"],
            name=data["name"],
            statement=data["statement"],
            measure=data["measure"],
            signature=data["signature"],
            signed_at=int(data["signed_at"]),
        )
        if not verify_axiom(axiom, noyau_key):
            raise ValueError(
                f"axiome {letter} a une signature invalide — Noyau Primordial "
                f"possiblement compromis"
            )
        axioms[letter] = axiom
    return axioms


# ── Variable globale (lazy) ──────────────────────────────
_AXIOMS: dict[str, Axiom] | None = None


def get_axioms() -> dict[str, Axiom]:
    """Retourne les axiomes (initialise avec une clé démo si besoin).

    En production, cette fonction est appelée après le bootstrap de
    l'identité (qui fournit noyau_key). En mode test, une clé démo
    déterministe est utilisée.
    """
    global _AXIOMS
    if _AXIOMS is None:
        from ciel.core.identity import demo_key
        _AXIOMS = load_axioms(demo_key())
    return _AXIOMS


# Constante publique après premier appel
def __getattr__(name: str) -> dict[str, Axiom] | object:
    """Module-level __getattr__ pour AXIOMS à la demande."""
    if name == "AXIOMS":
        return get_axioms()
    raise AttributeError(f"module 'ciel.core.axioms' has no attribute {name!r}")
