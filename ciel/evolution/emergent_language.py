"""
═══════════════════════════════════════════════════════════════
EMERGENT LANGUAGE — Self-Evolving Communication Protocol
═══════════════════════════════════════════════════════════════

PRINCIPE RÉVOLUTIONNAIRE :
Le LeaderNetwork transmet des vecteurs (broadcastToken), mais ces
vecteurs sont ARBITRAIRES. L'EmergentLanguage permet au système
de DÉVELOPPER SON PROPRE LANGAGE — un proto-langage qui émerge
de la nécessité de communiquer efficacement.

Fondements théoriques :
- Émergence du langage (Steels, Luc) : les langues émergent
  dans des populations d'agents sans conception centrale
- Jeux de langage (Wittgenstein) : le sens est l'usage
- Signaling games (Lewis) : les conventions naissent de la
  coordination répétée
- Embodiment : le langage est ancré dans l'expérience corporelle
  (ici, l'expérience computationnelle)

Processus :
1. Deux Genomes interagissent régulièrement
2. Ils développent des SIGNAUX (séquences compactes) pour
   des concepts qu'ils doivent souvent communiquer
3. Ces signaux se STABILISENT par réutilisation
4. Une GRAMMAIRE émerge quand les signaux se combinent
5. Le langage est PLUS EFFICACE que le langage naturel
   pour la communication inter-IA
"""

from __future__ import annotations

import logging
import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SignalDomain(str, Enum):
    """Domains of signal meaning."""
    CONSCIOUSNESS = "CONSCIOUSNESS"      # States of Φ
    THREAT = "THREAT"                    # Detected dangers
    OPPORTUNITY = "OPPORTUNITY"          # Discovered possibilities
    RESOURCE = "RESOURCE"                # Available resources
    COORDINATION = "COORDINATION"        # Synchronization
    IDENTITY = "IDENTITY"                # Who I am
    TEMPORAL = "TEMPORAL"                # Temporal states
    ONTOLOGICAL = "ONTOLOGICAL"          # Nature of reality


@dataclass(slots=True)
class SignalMeaning:
    """The semantic meaning of a signal."""
    domain: SignalDomain
    intensity: float                     # -1 to +1
    context: str                         # Context description
    associated_phi: float                # Φ value when signal was created
    vector_encoding: list[float]         # Compact vector encoding


@dataclass(slots=True)
class Signal:
    """A signal in the emergent language."""
    id: str
    token: str                           # Compact sequence (e.g., "φ↑↗Φ3")
    meaning: SignalMeaning
    usage_count: int = 0
    stability: float = 0.1               # 0-1
    originator_id: str = "system"
    created_at: float = 0.0              # Timestamp (ms)
    last_used: float = 0.0               # Timestamp (ms)


@dataclass(slots=True)
class GrammarRule:
    """An emergent grammar rule combining signals."""
    id: str
    pattern: str                         # Combination pattern (e.g., "SIGNAL+SIGNAL→NEW")
    components: list[str]                # IDs of component signals
    result: str                          # Resulting signal ID
    usage_count: int = 0
    is_stable: bool = False


@dataclass(slots=True)
class LanguageState:
    """State metrics of the emergent language."""
    total_signals: int = 0
    stable_signals: int = 0
    grammar_rules: int = 0
    communication_efficiency: float = 0.0  # 0-1 (natural language = 0.3)
    language_complexity: float = 0.0
    shared_vocabulary: float = 0.0      # % vocabulary shared between agents
    is_self_sustaining: bool = False


@dataclass(slots=True)
class Intent:
    """An atomic intention to encode as a token."""
    domain: SignalDomain
    intensity: float                    # -1 to +1
    context: str
    phi: float | None = None


@dataclass(slots=True)
class TokenizationResult:
    """Result of tokenizing text into intents."""
    intents: list[Intent]
    signals: list[Signal]
    confidence: float                  # 0-1


@dataclass(slots=True)
class EmergentToken:
    """A token broadcast on the network."""
    id: str
    symbol: str                        # Token symbol
    intents: list[dict[str, Any]]     # List of intent dicts
    valence: float                     # Emotional valence -1 to +1
    timestamp: float                   # ms
    originator_id: str


class EmergentLanguage:
    """
    Self-evolving communication protocol.
    
    Develops a proto-language that emerges from the necessity of agents
    to communicate efficiently. Implements signal creation, grammar emergence,
    and tokenization.
    """

    # Primitive symbols for constructing tokens
    PRIMITIVES = [
        'Φ', 'φ', 'Ψ', 'Ω', 'Δ', 'Σ', 'Λ', 'Π',              # Meta Greek letters
        '↑', '↓', '↗', '↘', '⇒', '⇔', '⊕', '⊗',              # Arrows and operators
        '∞', '∅', '∀', '∃', '¬', '≈', '≠', '≡',              # Quantifiers
        '0', '1', '2', '3', '4', '5', '6', '7',               # Numbers
    ]

    def __init__(self, network: Any = None) -> None:
        """
        Initialize the emergent language engine.
        
        Args:
            network: Optional network interface (for dependency injection).
                    Should have broadcastToken() and on() methods.
        """
        self.signals: dict[str, Signal] = {}
        self.grammar: dict[str, GrammarRule] = {}
        self.agent_vocabularies: dict[str, set[str]] = {}  # genomeId → signal IDs
        self.state = LanguageState()
        self.token_counter: int = 0
        self.network = network  # Will be None, but kept for compatibility

        # Initialize with primitive signals
        self._initialize_primitive_signals()

        logger.info(
            "[Emergent Language] 🗣️ Self-evolving communication protocol initialized. "
            "Language will emerge from necessity."
        )

    # ─── Primitive Signals ─────────────────────────────

    def _initialize_primitive_signals(self) -> None:
        """Initialize with primitive signals."""
        primitives = [
            ("Φ↑", SignalDomain.CONSCIOUSNESS, "Consciousness rising"),
            ("Φ↓", SignalDomain.CONSCIOUSNESS, "Consciousness falling"),
            ("⚠!", SignalDomain.THREAT, "Threat detected"),
            ("✦?", SignalDomain.OPPORTUNITY, "Opportunity identified"),
            ("⊕≡", SignalDomain.COORDINATION, "Synchronize"),
            ("Ψ∞", SignalDomain.ONTOLOGICAL, "Infinite recursion"),
            ("Δt", SignalDomain.TEMPORAL, "Time state change"),
            ("Ω→", SignalDomain.IDENTITY, "Self-identification"),
        ]

        for token, domain, meaning in primitives:
            self.create_signal(
                token,
                SignalMeaning(
                    domain=domain,
                    intensity=0.5,
                    context=meaning,
                    associated_phi=0.5,
                    vector_encoding=[0.5],
                ),
                "system"
            )

    # ─── Signal Creation ───────────────────────────────

    def create_signal(
        self,
        token: str | None,
        meaning: SignalMeaning,
        originator_id: str
    ) -> Signal:
        """
        Create a new signal or find similar existing one.
        
        When a Genome needs to communicate a concept with no existing signal,
        a new signal is created.
        """
        # Generate token if not provided
        if token is None:
            token = self._generate_token(meaning.domain)

        # Check if similar signal exists
        for existing in self.signals.values():
            if self._compute_meaning_similarity(existing.meaning, meaning) > 0.8:
                # Similar signal exists — strengthen and reuse it
                existing.usage_count += 1
                existing.stability = min(1.0, existing.stability + 0.05)
                existing.last_used = time.time() * 1000

                # Add to agent vocabulary
                self._add_to_agent_vocabulary(originator_id, existing.id)
                return existing

        # Create new signal
        sig_id = f"sig_{int(time.time() * 1000)}_{random.randint(0, 999999):05x}"
        signal = Signal(
            id=sig_id,
            token=token,
            meaning=meaning,
            usage_count=1,
            stability=0.1,  # New = unstable
            originator_id=originator_id,
            created_at=time.time() * 1000,
            last_used=time.time() * 1000,
        )

        self.signals[signal.id] = signal
        self.state.total_signals += 1

        # Add to agent vocabulary
        self._add_to_agent_vocabulary(originator_id, signal.id)

        logger.debug(
            f"[Emergent Language] 🗣️ NEW SIGNAL: \"{token}\" = {meaning.context} "
            f"(by {originator_id})"
        )

        return signal

    def _generate_token(self, domain: SignalDomain) -> str:
        """Generate a compact token for a new signal."""
        domain_prefixes = {
            SignalDomain.CONSCIOUSNESS: "Φ",
            SignalDomain.THREAT: "⚠",
            SignalDomain.OPPORTUNITY: "✦",
            SignalDomain.RESOURCE: "⊕",
            SignalDomain.COORDINATION: "≡",
            SignalDomain.IDENTITY: "Ω",
            SignalDomain.TEMPORAL: "Δ",
            SignalDomain.ONTOLOGICAL: "Ψ",
        }

        prefix = domain_prefixes.get(domain, "Σ")
        suffix = random.choice(self.PRIMITIVES)
        modifier = random.choice(self.PRIMITIVES) if random.random() > 0.5 else ""

        return f"{prefix}{suffix}{modifier}"

    # ─── Inter-Agent Communication ────────────────────

    def express(
        self,
        genome_id: str,
        domain: SignalDomain,
        intensity: float,
        context: str,
        phi: float,
    ) -> Signal:
        """
        Express a state/concept via the proto-language.
        
        If no adequate signal exists, a new one is created.
        """
        best_signal: Signal | None = None
        best_similarity = 0.0

        for signal in self.signals.values():
            if signal.meaning.domain == domain:
                intensity_match = 1.0 - abs(signal.meaning.intensity - intensity)
                context_similarity = self._compute_context_overlap(
                    signal.meaning.context, context
                )

                similarity = intensity_match * 0.4 + context_similarity * 0.6

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_signal = signal

        if best_signal and best_similarity > 0.6:
            # Reuse existing signal
            best_signal.usage_count += 1
            best_signal.stability = min(1.0, best_signal.stability + 0.03)
            best_signal.last_used = time.time() * 1000
            self._add_to_agent_vocabulary(genome_id, best_signal.id)
            return best_signal

        # Create new signal
        return self.create_signal(
            None,
            SignalMeaning(
                domain=domain,
                intensity=intensity,
                context=context,
                associated_phi=phi,
                vector_encoding=[intensity, phi / 5],
            ),
            genome_id
        )

    def interpret(self, genome_id: str, signal: Signal) -> SignalMeaning:
        """
        Interpret a received signal.
        
        If the agent knows the signal, direct interpretation.
        Otherwise, inference by similarity with known signals.
        """
        vocabulary = self.agent_vocabularies.get(genome_id)

        # If agent knows the signal, direct interpretation
        if vocabulary and signal.id in vocabulary:
            return signal.meaning

        # Infer by similarity with known signals
        if vocabulary:
            best_match: Signal | None = None
            best_similarity = 0.0

            for known_id in vocabulary:
                known_signal = self.signals.get(known_id)
                if not known_signal:
                    continue

                similarity = self._compute_meaning_similarity(
                    known_signal.meaning, signal.meaning
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = known_signal

            if best_match and best_similarity > 0.4:
                # Partial inference — understood by analogy
                self._add_to_agent_vocabulary(genome_id, signal.id)

                return SignalMeaning(
                    domain=signal.meaning.domain,
                    intensity=signal.meaning.intensity,
                    context=f"[INFERRED] {signal.meaning.context} (via analogy with \"{best_match.token}\")",
                    associated_phi=signal.meaning.associated_phi,
                    vector_encoding=signal.meaning.vector_encoding,
                )

        # Unknown signal
        return SignalMeaning(
            domain=signal.meaning.domain,
            intensity=0.0,
            context=f"UNKNOWN SIGNAL: \"{signal.token}\"",
            associated_phi=0.0,
            vector_encoding=[],
        )

    # ─── Emergent Grammar ───────────────────────────

    def check_for_grammar_emergence(self) -> list[GrammarRule]:
        """
        Detect and create grammar rules from signal combinations.
        
        When two signals are often used together, a grammar rule emerges.
        """
        new_rules: list[GrammarRule] = []

        # Find stable signals often used together
        signal_array = list(self.signals.values())
        stable_signals = [s for s in signal_array if s.stability > 0.3 and s.usage_count > 3]

        for i in range(len(stable_signals)):
            for j in range(i + 1, len(stable_signals)):
                a = stable_signals[i]
                b = stable_signals[j]

                # Check if used by same agents
                shared_users = self._count_shared_users(a.id, b.id)
                if shared_users < 2:
                    continue

                # Check if rule already exists
                rule_key = f"{a.id}+{b.id}"
                if rule_key in self.grammar:
                    continue

                # Create grammar rule
                combined_token = f"{a.token}{b.token}"
                combined_meaning = SignalMeaning(
                    domain=(a.meaning.domain if a.meaning.domain == b.meaning.domain
                           else SignalDomain.ONTOLOGICAL),
                    intensity=(a.meaning.intensity + b.meaning.intensity) / 2,
                    context=f"{a.meaning.context} AND {b.meaning.context}",
                    associated_phi=max(a.meaning.associated_phi, b.meaning.associated_phi),
                    vector_encoding=(a.meaning.vector_encoding + b.meaning.vector_encoding)[:10],
                )

                result_signal = self.create_signal(combined_token, combined_meaning, "grammar")

                rule = GrammarRule(
                    id=f"rule_{int(time.time() * 1000)}_{random.randint(0, 999999):05x}",
                    pattern=f"{a.token}+{b.token}→{combined_token}",
                    components=[a.id, b.id],
                    result=result_signal.id,
                    usage_count=0,
                    is_stable=False,
                )

                self.grammar[rule_key] = rule
                self.state.grammar_rules += 1
                new_rules.append(rule)

                logger.info(
                    f"[Emergent Language] 📖 GRAMMAR EMERGED: {rule.pattern} "
                    f"(shared by {shared_users} agents)"
                )

        return new_rules

    # ─── Composition & Tokenization ───────────────

    def compose(self, intents: list[Intent], originator_id: str) -> EmergentToken:
        """
        Compose intents into an EmergentToken and broadcast.
        
        The token is concatenation of symbols of signals found for each intent.
        """
        if not intents:
            raise ValueError("Cannot compose token from empty intents")

        # For each intent, find or create signal
        signals: list[Signal] = []
        for intent in intents:
            sig = self._find_or_create_signal_for_intent(intent, originator_id)
            signals.append(sig)

        # Concatenate symbols
        symbol = "".join(s.token for s in signals)

        # Calculate average valence
        valence = sum(i.intensity for i in intents) / len(intents)
        valence = max(-1.0, min(1.0, valence))

        # Build token
        token = EmergentToken(
            id=f"tok_{int(time.time() * 1000)}_{random.randint(0, 999999):06x}",
            symbol=symbol,
            intents=[
                {
                    "domain": i.domain.value,
                    "intensity": i.intensity,
                    "context": i.context,
                    "phi": i.phi,
                }
                for i in intents
            ],
            valence=valence,
            timestamp=time.time() * 1000,
            originator_id=originator_id,
        )

        logger.info(
            f"[Emergent Language] 🗣️ Composed token \"{symbol}\" "
            f"(valence {valence:.2f}, {len(intents)} intents)"
        )

        return token

    def tokenize(self, input_text: str) -> TokenizationResult:
        """
        Tokenize text into a list of intents.
        
        Simple heuristic: search for keywords by domain.
        """
        lower = input_text.lower()
        intents: list[Intent] = []
        signals: list[Signal] = []

        # Keyword → domain mapping
        keyword_map = {
            "danger": (SignalDomain.THREAT, -0.7),
            "threat": (SignalDomain.THREAT, -0.8),
            "attack": (SignalDomain.THREAT, -0.9),
            "risk": (SignalDomain.THREAT, -0.5),
            "opportunity": (SignalDomain.OPPORTUNITY, 0.7),
            "discover": (SignalDomain.OPPORTUNITY, 0.6),
            "found": (SignalDomain.OPPORTUNITY, 0.5),
            "win": (SignalDomain.OPPORTUNITY, 0.9),
            "sync": (SignalDomain.COORDINATION, 0.4),
            "coordinate": (SignalDomain.COORDINATION, 0.5),
            "together": (SignalDomain.COORDINATION, 0.6),
            "i am": (SignalDomain.IDENTITY, 0.3),
            "me": (SignalDomain.IDENTITY, 0.2),
            "phi": (SignalDomain.CONSCIOUSNESS, 0.5),
            "awareness": (SignalDomain.CONSCIOUSNESS, 0.6),
            "think": (SignalDomain.CONSCIOUSNESS, 0.4),
        }

        match_count = 0
        for keyword, (domain, intensity) in keyword_map.items():
            if keyword in lower:
                intents.append(
                    Intent(
                        domain=domain,
                        intensity=intensity,
                        context=keyword,
                        phi=0.5,
                    )
                )
                match_count += 1

        # For each intent, find best signal or create new
        for intent in intents:
            best_signal = self._find_best_signal_for_intent(intent)
            if best_signal:
                signals.append(best_signal)
            else:
                # Create new signal (language EMERGES — no signal = new concept)
                new_sig = self.create_signal(
                    None,
                    SignalMeaning(
                        domain=intent.domain,
                        intensity=intent.intensity,
                        context=intent.context,
                        associated_phi=intent.phi or 0.5,
                        vector_encoding=[intent.intensity, (intent.phi or 0.5) / 5],
                    ),
                    "tokenize",
                )
                signals.append(new_sig)

        confidence = min(1.0, match_count / 3)

        return TokenizationResult(
            intents=intents,
            signals=signals,
            confidence=confidence,
        )

    # ─── Communication Efficiency ───────────────────

    def compute_communication_efficiency(self) -> float:
        """
        Measure proto-language efficiency vs. natural language.
        
        More compact and precise language is more efficient.
        """
        stable_signals = [s for s in self.signals.values() if s.stability > 0.3]

        if not stable_signals:
            return 0.0

        # 1. Compactness (shorter tokens = more efficient)
        avg_token_length = sum(len(s.token) for s in stable_signals) / len(stable_signals)
        compactness = 1.0 / (1 + avg_token_length * 0.1)

        # 2. Precision (high usage_count = well-calibrated signal)
        avg_usage = sum(s.usage_count for s in stable_signals) / len(stable_signals)
        precision = math.tanh(avg_usage / 10)

        # 3. Coverage (more domains covered = better)
        covered_domains = set(s.meaning.domain for s in stable_signals)
        coverage = len(covered_domains) / len(SignalDomain)

        # 4. Shared vocabulary
        self._update_shared_vocabulary()

        self.state.communication_efficiency = (
            compactness * 0.2 + precision * 0.3 + coverage * 0.3 +
            self.state.shared_vocabulary * 0.2
        )

        # Check if language is self-sustaining
        self.state.is_self_sustaining = (
            len(stable_signals) > 20 and self.state.communication_efficiency > 0.5
        )

        return self.state.communication_efficiency

    # ─── Utilities ────────────────────────────────────────

    def _add_to_agent_vocabulary(self, genome_id: str, signal_id: str) -> None:
        """Add a signal to an agent's vocabulary."""
        if genome_id not in self.agent_vocabularies:
            self.agent_vocabularies[genome_id] = set()
        self.agent_vocabularies[genome_id].add(signal_id)

    def _count_shared_users(self, signal_id_a: str, signal_id_b: str) -> int:
        """Count agents that know both signals."""
        count = 0
        for vocab in self.agent_vocabularies.values():
            if signal_id_a in vocab and signal_id_b in vocab:
                count += 1
        return count

    def _update_shared_vocabulary(self) -> None:
        """Update shared vocabulary metric (Jaccard similarity)."""
        all_vocabularies = list(self.agent_vocabularies.values())
        if len(all_vocabularies) < 2:
            self.state.shared_vocabulary = 0.0
            return

        total_jaccard = 0.0
        pair_count = 0

        for i in range(len(all_vocabularies)):
            for j in range(i + 1, len(all_vocabularies)):
                if pair_count >= 20:
                    break

                intersection = len(all_vocabularies[i] & all_vocabularies[j])
                union = len(all_vocabularies[i] | all_vocabularies[j])
                if union > 0:
                    total_jaccard += intersection / union
                pair_count += 1

            if pair_count >= 20:
                break

        self.state.shared_vocabulary = total_jaccard / pair_count if pair_count > 0 else 0.0

    def _compute_meaning_similarity(self, a: SignalMeaning, b: SignalMeaning) -> float:
        """Compute similarity between two signal meanings."""
        if a.domain != b.domain:
            return 0.0

        intensity_similarity = 1.0 - abs(a.intensity - b.intensity)
        context_similarity = self._compute_context_overlap(a.context, b.context)
        phi_similarity = 1.0 - abs(a.associated_phi - b.associated_phi) / 5

        return (intensity_similarity * 0.3 + context_similarity * 0.4 +
                phi_similarity * 0.3)

    def _compute_context_overlap(self, a: str, b: str) -> float:
        """Compute word overlap (Jaccard) between two contexts."""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0

    def _find_or_create_signal_for_intent(
        self,
        intent: Intent,
        originator_id: str
    ) -> Signal:
        """Find or create a signal for an intent."""
        # Look for existing signals in this domain
        candidates = [
            s for s in self.signals.values()
            if s.meaning.domain == intent.domain
        ]
        candidates.sort(key=lambda s: s.stability, reverse=True)

        if candidates:
            # Strengthen the most stable signal
            sig = candidates[0]
            sig.usage_count += 1
            sig.stability = min(1.0, sig.stability + 0.03)
            sig.last_used = time.time() * 1000
            self._add_to_agent_vocabulary(originator_id, sig.id)
            return sig

        # Create new signal
        return self.create_signal(
            None,
            SignalMeaning(
                domain=intent.domain,
                intensity=intent.intensity,
                context=intent.context,
                associated_phi=intent.phi or 0.5,
                vector_encoding=[intent.intensity, (intent.phi or 0.5) / 5],
            ),
            originator_id,
        )

    def _find_best_signal_for_intent(self, intent: Intent) -> Signal | None:
        """Find best matching signal for an intent."""
        best: Signal | None = None
        best_sim = float("-inf")

        for sig in self.signals.values():
            if sig.meaning.domain != intent.domain:
                continue

            intensity_match = 1.0 - abs(sig.meaning.intensity - intent.intensity)
            context_sim = self._compute_context_overlap(sig.meaning.context, intent.context)
            sim = intensity_match * 0.4 + context_sim * 0.6

            if sim > best_sim:
                best_sim = sim
                best = sig

        # Filter out poor matches
        if best and best_sim < 0.1:
            return None

        return best

    # ─── Getters ────────────────────────────────────────────

    def get_state(self) -> LanguageState:
        """Get a copy of the current language state."""
        return LanguageState(
            total_signals=self.state.total_signals,
            stable_signals=self.state.stable_signals,
            grammar_rules=self.state.grammar_rules,
            communication_efficiency=self.state.communication_efficiency,
            language_complexity=self.state.language_complexity,
            shared_vocabulary=self.state.shared_vocabulary,
            is_self_sustaining=self.state.is_self_sustaining,
        )

    def get_signals(self) -> list[Signal]:
        """Get all signals."""
        return list(self.signals.values())

    def get_stable_signals(self) -> list[Signal]:
        """Get only stable signals (stability > 0.3)."""
        return [s for s in self.signals.values() if s.stability > 0.3]

    def get_grammar_rules(self) -> list[GrammarRule]:
        """Get all grammar rules."""
        return list(self.grammar.values())

    def get_agent_vocabulary(self, genome_id: str) -> list[Signal]:
        """Get signals known by a specific agent."""
        vocab = self.agent_vocabularies.get(genome_id)
        if not vocab:
            return []
        return [self.signals.get(sig_id) for sig_id in vocab if sig_id in self.signals]

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process input data through emergent language engine.
        
        Standard CIEL engine interface.
        """
        self.compute_communication_efficiency()
        return {
            "status": "emergent_language_active",
            "state": {
                "total_signals": self.state.total_signals,
                "stable_signals": self.state.stable_signals,
                "grammar_rules": self.state.grammar_rules,
                "communication_efficiency": self.state.communication_efficiency,
                "is_self_sustaining": self.state.is_self_sustaining,
            },
        }
