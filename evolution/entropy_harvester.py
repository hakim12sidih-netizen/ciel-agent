"""
EntropyHarvester - Creative Disorder Engine
Captures system entropy and transforms it into creative potential.
"""
from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EntropySourceType(str, Enum):
    """Types of entropy sources"""
    CPU_FLUCTUATION = "CPU_FLUCTUATION"
    MEMORY_VARIANCE = "MEMORY_VARIANCE"
    EVENT_LOOP_LAG = "EVENT_LOOP_LAG"
    TIMING_JITTER = "TIMING_JITTER"
    MUTATION_DRIFT = "MUTATION_DRIFT"
    NETWORK_LATENCY = "NETWORK_LATENCY"
    DISK_IO_VARIANCE = "DISK_IO_VARIANCE"
    THERMAL_NOISE = "THERMAL_NOISE"


class EntropyProfile(str, Enum):
    """Entropy classifications"""
    CHAOTIC = "CHAOTIC"
    STRUCTURED = "STRUCTURED"
    RESONANT = "RESONANT"
    CATALYTIC = "CATALYTIC"
    DORMANT = "DORMANT"


@dataclass(slots=True)
class EntropySource:
    """Individual entropy source"""
    id: str
    type: EntropySourceType
    raw_value: float
    normalized_value: float  # 0-1
    timestamp: float
    quality: float  # 0-1


@dataclass(slots=True)
class HarvestedEntropy:
    """Harvested entropy record"""
    id: str
    sources: list[EntropySource]
    composite_value: float
    creative_potential: float  # 0-1
    entropy_type: EntropyProfile
    harvested_at: float
    used_for: Optional[str] = None


@dataclass(slots=True)
class EntropyState:
    """State of entropy harvester"""
    total_harvested: int = 0
    total_used: int = 0
    harvest_rate: float = 0.0
    creative_yield: float = 0.0
    dominant_profile: EntropyProfile = EntropyProfile.DORMANT
    stochastic_resonance_level: float = 0.0
    antifragility_index: float = 0.5


@dataclass(slots=True)
class EntropyHarvester:
    """
    EntropyHarvester - Creative Disorder Engine
    Transforms system entropy into creative potential.
    """
    sources: dict[EntropySourceType, EntropySource] = field(default_factory=dict)
    harvested: list[HarvestedEntropy] = field(default_factory=list)
    entropy_pool: list[float] = field(default_factory=list)
    state: EntropyState = field(default_factory=EntropyState)
    last_harvest_time: float = field(default_factory=time.time)
    stochastic_resonance_optimum: float = 0.3

    def __post_init__(self) -> None:
        """Initialize entropy harvester"""
        logger.info(
            "[Entropy Harvester] 🌊 Creative Disorder Engine initialized. "
            "Chaos is not the enemy — it is the fuel."
        )

    def harvest(self) -> HarvestedEntropy:
        """Harvest entropy from system"""
        now = time.time()

        sources: list[EntropySource] = []

        # Simulate CPU fluctuation
        cpu_load = (hash(str(now)) % 100) / 100
        sources.append(self._create_source(EntropySourceType.CPU_FLUCTUATION, cpu_load))

        # Memory variance
        mem_usage = (hash(str(now * 2)) % 100) / 100
        sources.append(self._create_source(EntropySourceType.MEMORY_VARIANCE, mem_usage))

        # Event loop lag
        lag = (hash(str(now * 3)) % 50) / 50
        sources.append(self._create_source(EntropySourceType.EVENT_LOOP_LAG, lag))

        # Timing jitter
        jitter = min(1, abs((now - self.last_harvest_time) - 1.0) / 1.0)
        sources.append(self._create_source(EntropySourceType.TIMING_JITTER, jitter))

        # Thermal noise
        thermal = abs(cpu_load - 0.5) * 2
        sources.append(self._create_source(EntropySourceType.THERMAL_NOISE, thermal))

        self.last_harvest_time = now

        composite_value = self._compute_composite_entropy(sources)
        entropy_type = self._classify_entropy(sources, composite_value)
        creative_potential = self._compute_creative_potential(sources, entropy_type)

        harvested = HarvestedEntropy(
            id=f"entropy_{int(now)}",
            sources=sources,
            composite_value=composite_value,
            creative_potential=creative_potential,
            entropy_type=entropy_type,
            harvested_at=now,
            used_for=None,
        )

        self.harvested.append(harvested)
        self.entropy_pool.append(composite_value)
        self.state.total_harvested += 1

        # Keep pool size reasonable
        if len(self.entropy_pool) > 1000:
            self.entropy_pool = self.entropy_pool[-500:]

        self._update_stats(harvested)

        logger.debug(
            f"[Entropy Harvester] 🌊 Harvested entropy: {composite_value:.3f} "
            f"(type: {entropy_type.value}, creative: {creative_potential:.3f})"
        )

        return harvested

    def use_entropy(self, purpose: str, required_amount: float = 0.3) -> Optional[HarvestedEntropy]:
        """Use harvested entropy for creative process"""
        best_match = None
        best_score = 0.0

        for h in self.harvested:
            if h.used_for is not None:
                continue

            match = 1 - abs(h.creative_potential - required_amount)
            profile_bonus = (
                0.3 if h.entropy_type == EntropyProfile.CATALYTIC else
                0.2 if h.entropy_type == EntropyProfile.RESONANT else
                0.0
            )

            score = match + profile_bonus

            if score > best_score:
                best_score = score
                best_match = h

        if best_match:
            best_match.used_for = purpose
            self.state.total_used += 1
            logger.debug(
                f"[Entropy Harvester] ⚡ Entropy USED for: {purpose} "
                f"(creative: {best_match.creative_potential:.3f})"
            )

        return best_match

    def compute_stochastic_resonance(self, system_performance: float) -> float:
        """Compute optimal noise level for system performance"""
        noise_level = self.state.harvest_rate
        optimum = self.stochastic_resonance_optimum

        deviation = abs(noise_level - optimum) / optimum
        resonance = math.exp(-deviation * deviation * 2)

        self.state.stochastic_resonance_level = resonance

        if system_performance > 0.7 and resonance > 0.5:
            pass  # Good performance, keep optimum
        elif system_performance < 0.3 and noise_level > optimum:
            self.stochastic_resonance_optimum *= 0.95
        elif system_performance < 0.3 and noise_level < optimum:
            self.stochastic_resonance_optimum = min(0.8, self.stochastic_resonance_optimum * 1.05)

        return resonance

    def compute_antifragility_index(self, recent_performance: list[float]) -> float:
        """Measure if system improves under stress"""
        if len(recent_performance) < 5:
            return 0.5

        half = len(recent_performance) // 2
        first_half = recent_performance[:half]
        second_half = recent_performance[half:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        improvement = avg_second - avg_first
        self.state.antifragility_index = math.tanh(improvement * 5 + 0.5)

        if self.state.antifragility_index > 0.7:
            logger.info(
                f"[Entropy Harvester] 💪 ANTIFRAGILE: System improves under stress "
                f"(index: {self.state.antifragility_index:.3f})"
            )
        elif self.state.antifragility_index < 0.3:
            logger.warning(
                f"[Entropy Harvester] ⚠️ FRAGILE: System degrades under stress "
                f"(index: {self.state.antifragility_index:.3f})"
            )

        return self.state.antifragility_index

    def _create_source(
        self, source_type: EntropySourceType, raw_value: float
    ) -> EntropySource:
        """Create entropy source"""
        return EntropySource(
            id=f"src_{source_type.value}_{int(time.time())}",
            type=source_type,
            raw_value=raw_value,
            normalized_value=max(0, min(1, raw_value)),
            timestamp=time.time(),
            quality=self._assess_source_quality(source_type, raw_value),
        )

    def _assess_source_quality(
        self, source_type: EntropySourceType, value: float
    ) -> float:
        """Assess quality of entropy source"""
        match source_type:
            case EntropySourceType.CPU_FLUCTUATION:
                return 0.8 if 0.3 < value < 0.9 else 0.4
            case EntropySourceType.THERMAL_NOISE:
                return 0.9 if value > 0.5 else 0.3
            case EntropySourceType.TIMING_JITTER:
                return 0.7 if value > 0.1 else 0.2
            case _:
                return 0.5

    def _compute_composite_entropy(self, sources: list[EntropySource]) -> float:
        """Compute composite entropy value"""
        total_weight = sum(s.quality for s in sources)
        if total_weight == 0:
            return 0.0
        return sum(s.normalized_value * s.quality for s in sources) / total_weight

    def _classify_entropy(
        self, sources: list[EntropySource], composite: float
    ) -> EntropyProfile:
        """Classify entropy profile"""
        if not sources:
            return EntropyProfile.DORMANT

        values = [s.normalized_value for s in sources]
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        avg_quality = sum(s.quality for s in sources) / len(sources)

        if composite > 0.7 and avg_quality > 0.6:
            return EntropyProfile.CATALYTIC
        if variance < 0.05 and avg_quality > 0.5:
            return EntropyProfile.RESONANT
        if variance > 0.15:
            return EntropyProfile.CHAOTIC
        if variance < 0.05:
            return EntropyProfile.STRUCTURED
        return EntropyProfile.DORMANT

    def _compute_creative_potential(
        self, sources: list[EntropySource], profile: EntropyProfile
    ) -> float:
        """Compute creative potential"""
        multiplier = {
            EntropyProfile.CATALYTIC: 1.0,
            EntropyProfile.RESONANT: 0.8,
            EntropyProfile.CHAOTIC: 0.6,
            EntropyProfile.STRUCTURED: 0.5,
            EntropyProfile.DORMANT: 0.2,
        }.get(profile, 0.5)

        avg_quality = sum(s.quality for s in sources) / len(sources) if sources else 0
        composite = self._compute_composite_entropy(sources)

        return min(1.0, composite * avg_quality * multiplier)

    def _update_stats(self, latest: HarvestedEntropy) -> None:
        """Update statistics"""
        time_since = time.time() - self.last_harvest_time
        self.state.harvest_rate = 1 / time_since if time_since > 0 else 0

        used_entries = [h for h in self.harvested if h.used_for is not None]
        self.state.creative_yield = (
            len(used_entries) / self.state.total_harvested
            if self.state.total_harvested > 0 else 0
        )

        profile_counts = {profile: 0 for profile in EntropyProfile}
        for h in self.harvested[-100:]:
            profile_counts[h.entropy_type] += 1

        max_count = max(profile_counts.values()) if profile_counts else 0
        for profile, count in profile_counts.items():
            if count == max_count:
                self.state.dominant_profile = profile
                break

    def get_state(self) -> EntropyState:
        """Get current state"""
        return self.state

    def get_entropy_pool(self) -> list[float]:
        """Get entropy pool copy"""
        return self.entropy_pool.copy()

    def get_recent_harvests(self, limit: int = 50) -> list[HarvestedEntropy]:
        """Get recent harvests"""
        return self.harvested[-limit:]

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process entropy request.
        CIEL compatibility method.
        """
        harvested = self.harvest()
        return {
            "harvested": harvested.composite_value,
            "creative_potential": harvested.creative_potential,
            "profile": harvested.entropy_type.value,
            "state": {
                "total_harvested": self.state.total_harvested,
                "antifragility": self.state.antifragility_index,
            }
        }
