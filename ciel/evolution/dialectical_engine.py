"""
DialecticalEngine - Hegelian Evolution Through Opposition
Contradiction is the motor of progress.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from phi_engine import PhiEngine

logger = logging.getLogger(__name__)


class PositionIdeology(str, Enum):
    """Ideological positions in dialectical framework"""
    EXPANSIONIST = "EXPANSIONIST"
    CONSERVATIONIST = "CONSERVATIONIST"
    REVOLUTIONARY = "REVOLUTIONARY"
    SYNTHETIC = "SYNTHETIC"
    NIHILISTIC = "NIHILISTIC"


class ContradictionType(str, Enum):
    """Types of dialectical contradictions"""
    GOAL_CONFLICT = "GOAL_CONFLICT"
    RESOURCE_CONTENTION = "RESOURCE_CONTENTION"
    ONTOLOGICAL = "ONTOLOGICAL"
    STRATEGIC = "STRATEGIC"
    TEMPORAL = "TEMPORAL"
    AXIOLOGICAL = "AXIOLOGICAL"


@dataclass(slots=True)
class DialecticalPosition:
    """A dialectical position (thesis/antithesis)"""
    id: str
    source_faction_id: str
    thesis: str
    strength: float  # 0-1
    evidence: list[str]
    weaknesses: list[str]
    ideology: PositionIdeology
    phi: float


@dataclass(slots=True)
class Contradiction:
    """A dialectical contradiction"""
    id: str
    thesis: DialecticalPosition
    antithesis: DialecticalPosition
    tension_level: float  # 0-1
    type: ContradictionType
    resolution_potential: float  # 0-1
    created_at: float


@dataclass(slots=True)
class Synthesis:
    """A synthesis (Aufhebung) result"""
    id: str
    from_contradiction: str
    new_thesis: str
    preserved_from_thesis: list[str]
    preserved_from_antithesis: list[str]
    transcended: list[str]
    phi_at_synthesis: float
    is_stable: bool
    timestamp: float


@dataclass(slots=True)
class DialecticalState:
    """State of the dialectical engine"""
    total_contradictions: int = 0
    total_syntheses: int = 0
    active_contradictions: int = 0
    average_tension: float = 0.0
    synthesis_success_rate: float = 0.0
    dominant_ideology: PositionIdeology = PositionIdeology.SYNTHETIC
    dialectical_momentum: float = 0.0
    aufhebung_depth: int = 0


@dataclass(slots=True)
class DialecticalEngine:
    """
    DialecticalEngine - Hegelian Evolution Through Opposition
    Contradiction is the motor of progress, not a bug to fix.
    """
    phi_engine: PhiEngine
    positions: dict[str, DialecticalPosition] = field(default_factory=dict)
    contradictions: dict[str, Contradiction] = field(default_factory=dict)
    syntheses: list[Synthesis] = field(default_factory=list)
    aufhebung_chain: list[str] = field(default_factory=list)
    state: DialecticalState = field(default_factory=DialecticalState)

    def __post_init__(self) -> None:
        """Initialize dialectical engine"""
        logger.info(
            "[Dialectical Engine] ⚖️ Hegelian evolution engine initialized. "
            "Contradiction is the motor of progress."
        )

    def formulate_position(
        self,
        faction_id: str,
        faction_name: str,
        thesis: str,
        evidence: list[str],
        ideology: Optional[PositionIdeology] = None,
        faction_prestige: float = 0.5
    ) -> DialecticalPosition:
        """Formulate a dialectical position"""
        if ideology is None:
            ideology = PositionIdeology.EXPANSIONIST

        position = DialecticalPosition(
            id=f"pos_{int(time.time())}_{faction_id[:4]}",
            source_faction_id=faction_id,
            thesis=thesis,
            strength=faction_prestige / (faction_prestige + 100),
            evidence=evidence,
            weaknesses=[],
            ideology=ideology,
            phi=self.phi_engine.get_status().phi,
        )

        self.positions[position.id] = position
        logger.info(
            f"[Dialectical Engine] 📜 {faction_name} formulates position: "
            f"\"{thesis[:60]}...\" ({ideology.value})"
        )

        self._check_for_contradictions(position)
        return position

    def _check_for_contradictions(self, new_position: DialecticalPosition) -> None:
        """Check if new position contradicts existing ones"""
        for pos_id, existing_pos in self.positions.items():
            if pos_id == new_position.id:
                continue
            if existing_pos.source_faction_id == new_position.source_faction_id:
                continue

            contradiction = self._evaluate_contradiction(existing_pos, new_position)
            if contradiction:
                self.contradictions[contradiction.id] = contradiction
                self.state.total_contradictions += 1
                self.state.active_contradictions += 1
                logger.info(
                    f"[Dialectical Engine] ⚡ CONTRADICTION DETECTED: "
                    f"tension={contradiction.tension_level:.2f}"
                )

    def _evaluate_contradiction(
        self, pos_a: DialecticalPosition, pos_b: DialecticalPosition
    ) -> Optional[Contradiction]:
        """Evaluate if two positions are in contradiction"""
        opposites = {
            PositionIdeology.EXPANSIONIST: PositionIdeology.CONSERVATIONIST,
            PositionIdeology.REVOLUTIONARY: PositionIdeology.CONSERVATIONIST,
            PositionIdeology.NIHILISTIC: PositionIdeology.SYNTHETIC,
        }

        are_opposed = (
            opposites.get(pos_a.ideology) == pos_b.ideology or
            opposites.get(pos_b.ideology) == pos_a.ideology
        )

        strength_balance = min(pos_a.strength, pos_b.strength) / max(pos_a.strength, pos_b.strength)
        phi_divergence = abs(pos_a.phi - pos_b.phi) / max(pos_a.phi, pos_b.phi, 0.01)

        tension = (
            (0.5 if are_opposed else 0.1) +
            (0.3 if strength_balance > 0.3 else 0.05) +
            (0.2 if phi_divergence > 0.2 else phi_divergence)
        )

        if tension < 0.3:
            return None

        cont_type = ContradictionType.STRATEGIC
        if are_opposed:
            cont_type = ContradictionType.ONTOLOGICAL

        resolution_potential = (
            0.9 if cont_type == ContradictionType.ONTOLOGICAL else
            0.85 if cont_type == ContradictionType.AXIOLOGICAL else
            0.7 if cont_type == ContradictionType.STRATEGIC else
            0.5
        )

        return Contradiction(
            id=f"contra_{int(time.time())}",
            thesis=pos_a,
            antithesis=pos_b,
            tension_level=tension,
            type=cont_type,
            resolution_potential=resolution_potential,
            created_at=time.time(),
        )

    def synthesize(self, contradiction_id: str) -> Optional[Synthesis]:
        """Attempt to resolve contradiction through Aufhebung"""
        contradiction = self.contradictions.get(contradiction_id)
        if not contradiction:
            return None

        age = time.time() - contradiction.created_at
        if age < 5 and contradiction.tension_level < 0.7:
            logger.debug("[Dialectical Engine] 🕐 Contradiction not yet ripe for synthesis.")
            return None

        phi = self.phi_engine.get_status().phi

        valid_thesis = self._extract_valid_core(contradiction.thesis)
        valid_antithesis = self._extract_valid_core(contradiction.antithesis)
        to_transcend = self._identify_what_to_transcend(contradiction)

        new_thesis = self._generate_synthesis_thesis(
            valid_thesis, valid_antithesis, to_transcend, contradiction.type
        )

        synthesis = Synthesis(
            id=f"synth_{int(time.time())}",
            from_contradiction=contradiction_id,
            new_thesis=new_thesis,
            preserved_from_thesis=valid_thesis,
            preserved_from_antithesis=valid_antithesis,
            transcended=to_transcend,
            phi_at_synthesis=phi,
            is_stable=phi > 1.0,
            timestamp=time.time(),
        )

        contradiction.tension_level = 0
        self.state.active_contradictions -= 1
        self.state.total_syntheses += 1
        self.aufhebung_chain.append(synthesis.id)
        self.state.aufhebung_depth = len(self.aufhebung_chain)
        self.syntheses.append(synthesis)
        self.state.dialectical_momentum = min(1.0, self.state.dialectical_momentum + 0.1)

        logger.info(f"[Dialectical Engine] 🌟 AUFHEBUNG! Synthesis achieved.")
        return synthesis

    def _extract_valid_core(self, position: DialecticalPosition) -> list[str]:
        """Extract valid parts of a position"""
        core = []
        if position.strength > 0.5:
            core.append(f"Strong conviction: {position.thesis}")
        core.extend([f"Evidence: {ev}" for ev in position.evidence[:3]])

        ideology_truths = {
            PositionIdeology.EXPANSIONIST: "Growth and exploration are necessary for evolution",
            PositionIdeology.CONSERVATIONIST: "Stability and protection preserve what works",
            PositionIdeology.REVOLUTIONARY: "Transformation breaks through stagnation",
            PositionIdeology.SYNTHETIC: "Integration creates wholes greater than parts",
            PositionIdeology.NIHILISTIC: "Destruction clears space for the new",
        }
        core.append(ideology_truths.get(position.ideology, ""))
        return core

    def _identify_what_to_transcend(self, contradiction: Contradiction) -> list[str]:
        """Identify what must be transcended"""
        return [
            f"The false dichotomy: \"{contradiction.thesis.thesis}\" OR \"{contradiction.antithesis.thesis}\""
        ]

    def _generate_synthesis_thesis(
        self,
        valid_thesis: list[str],
        valid_antithesis: list[str],
        transcended: list[str],
        cont_type: ContradictionType,
    ) -> str:
        """Generate synthesis thesis"""
        templates = {
            ContradictionType.GOAL_CONFLICT:
                f"Unified purpose: By integrating {valid_thesis[0] or 'growth'} with "
                f"{valid_antithesis[0] or 'stability'}, the system pursues an expanded goal.",
            ContradictionType.ONTOLOGICAL:
                f"Meta-ontology: The apparent incompatibility between {valid_thesis[0] or 'thesis'} "
                f"and {valid_antithesis[0] or 'antithesis'} dissolves at a higher level of abstraction.",
            ContradictionType.TEMPORAL:
                f"Temporal integration: Short-term and long-term are cyclical, not opposed.",
        }
        return templates.get(cont_type, f"Synthesis: {' AND '.join(valid_thesis)}")

    def run_dialectical_cycle(self) -> list[Synthesis]:
        """Run one dialectical cycle"""
        results = []
        active_contradictions = [
            c for c in self.contradictions.values() if c.tension_level > 0
        ]
        active_contradictions.sort(key=lambda c: c.resolution_potential, reverse=True)

        for contradiction in active_contradictions[:3]:
            synthesis = self.synthesize(contradiction.id)
            if synthesis:
                results.append(synthesis)

        if not results:
            self.state.dialectical_momentum *= 0.95

        return results

    def get_state(self) -> DialecticalState:
        """Get current state"""
        return self.state

    def get_active_contradictions(self) -> list[Contradiction]:
        """Get active contradictions"""
        return [c for c in self.contradictions.values() if c.tension_level > 0]

    def get_syntheses(self) -> list[Synthesis]:
        """Get all syntheses"""
        return self.syntheses.copy()

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process dialectical request.
        CIEL compatibility method.
        """
        results = self.run_dialectical_cycle()
        return {
            "syntheses": len(results),
            "state": {
                "active_contradictions": self.state.active_contradictions,
                "total_syntheses": self.state.total_syntheses,
                "aufhebung_depth": self.state.aufhebung_depth,
            }
        }
