"""
CIEL v1.0 — EmergentLanguage : langage auto-organisé pour agents CIEL.

Migré depuis Hydra, adapté pour CIEL.
Permet aux génomes/agents de communiquer via des
tokens symboliques auto-organisés.

Le langage émerge de l'usage : les tokens gagnent en
stabilité plus ils sont utilisés avec succès.
"""
from __future__ import annotations

import math
import secrets
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SymbolicToken:
    """Token symbolique émergent."""
    symbol: str
    meaning: str
    dimension: int  # Dimension sémantique (0-31)
    stability: float = 0.0  # 0.0 = éphémère, 1.0 = stable
    usage_count: int = 0
    created_at: float = field(default_factory=time.time)


class EmergentLanguage:
    """Système de langage auto-organisé pour CIEL.

    Les tokens sont créés, utilisés, et stabilisés par l'usage.
    Le système peut produire des séquences de tokens pour
    représenter des concepts complexes.
    """

    def __init__(self, max_tokens: int = 256):
        self.tokens: dict[str, SymbolicToken] = {}
        self.max_tokens = max_tokens
        self.usage_history: list[list[str]] = []  # Séquence de tokens utilisés
        self._dimension_usage: dict[int, int] = defaultdict(int)

        # Tokens primordiaux (innés)
        self._init_primordial_tokens()

    def _init_primordial_tokens(self) -> None:
        primordial = [
            ("α", "bienveillance", 0),
            ("β", "transparence", 1),
            ("γ", "réversibilité", 2),
            ("δ", "inachèvement", 3),
            ("↑", "exploration", 4),
            ("↓", "exploitation", 6),
            ("⊕", "coopération", 5),
            ("⊗", "compétition", 7),
            ("○", "cycle", 8),
            ("◇", "évolution", 9),
            ("△", "émergence", 10),
            ("□", "stabilité", 11),
            ("∞", "infini", 12),
            ("⚘", "conscience", 13),
            ("✧", "innovation", 14),
            ("⚔", "défi", 15),
        ]
        for symbol, meaning, dim in primordial:
            self.tokens[symbol] = SymbolicToken(
                symbol=symbol, meaning=meaning, dimension=dim,
                stability=1.0, usage_count=1000,  # Stables dès le départ
            )
            self._dimension_usage[dim] += 1000

    def propose(self, meaning: str) -> SymbolicToken:
        """Propose un nouveau token pour un sens donné."""
        if len(self.tokens) >= self.max_tokens:
            # Recycler le token le moins stable
            oldest = min(self.tokens.values(), key=lambda t: t.stability)
            del self.tokens[oldest.symbol]

        symbol = self._generate_symbol()
        dim = len(self._dimension_usage) % 32
        token = SymbolicToken(symbol=symbol, meaning=meaning, dimension=dim)
        self.tokens[symbol] = token
        return token

    def use(self, symbol: str) -> SymbolicToken | None:
        """Utilise un token, augmentant sa stabilité."""
        if symbol not in self.tokens:
            return None
        old = self.tokens[symbol]
        # Augmente stabilité et compteur
        new_stability = min(1.0, old.stability + 0.05)
        self.tokens[symbol] = SymbolicToken(
            symbol=old.symbol, meaning=old.meaning, dimension=old.dimension,
            stability=new_stability, usage_count=old.usage_count + 1,
            created_at=old.created_at,
        )
        self._dimension_usage[old.dimension] += 1
        return self.tokens[symbol]

    def encode(self, concepts: list[str]) -> list[str]:
        """Encode des concepts en séquence de tokens."""
        sequence: list[str] = []
        for concept in concepts:
            found = False
            for token in self.tokens.values():
                if token.meaning == concept or concept in token.meaning:
                    sequence.append(token.symbol)
                    self.use(token.symbol)
                    found = True
                    break
            if not found:
                token = self.propose(concept)
                sequence.append(token.symbol)
        self.usage_history.append(sequence)
        return sequence

    def decode(self, sequence: list[str]) -> list[str]:
        """Décode une séquence de tokens en concepts."""
        return [
            self.tokens[s].meaning
            for s in sequence
            if s in self.tokens
        ]

    def express(self, concept: str) -> str:
        """Trouve le meilleur token pour exprimer un concept (ou en crée un)."""
        for token in self.tokens.values():
            if token.meaning == concept:
                self.use(token.symbol)
                return token.symbol
        token = self.propose(concept)
        return token.symbol

    def get_tokens_by_dimension(self, dimension: int) -> list[SymbolicToken]:
        return [t for t in self.tokens.values() if t.dimension == dimension]

    def statistics(self) -> dict:
        vocab_size = len(self.tokens)
        avg_stability = sum(t.stability for t in self.tokens.values()) / max(1, vocab_size)
        return {
            "vocabulary_size": vocab_size,
            "avg_stability": round(avg_stability, 3),
            "total_usage": sum(t.usage_count for t in self.tokens.values()),
            "dimensions_used": len(self._dimension_usage),
            "sequences_recorded": len(self.usage_history),
        }

    def _generate_symbol(self) -> str:
        """Génère un symbole unique."""
        symbols = "⌘⌥⏣⎔⚙⛭✤⚛⎊⏥⏚⌲⌺⎉⎊⎋⏍⍟⍺⍵⍶⍷⍨⍩⍬⍭⍮⍯⍰⍱⍲⍳⍴⍵⍶⍷⍸⍹⍺"
        for s in symbols:
            if s not in self.tokens:
                return s
        return f"¤{uuid.uuid4().hex[:4]}"
