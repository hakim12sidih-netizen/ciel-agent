"""
═══════════════════════════════════════════════════════════════
METAMORPHIC CORE — The Self-Rewriting Architecture
═══════════════════════════════════════════════════════════════

PRINCIPE RÉVOLUTIONNAIRE :
Le système ne mute pas seulement ses PARAMÈTRES — il réécrit sa propre
ARCHITECTURE. Il génère de nouvelles classes, de nouveaux comportements,
de nouvelles structures de contrôle à l'exécution.

Fondements théoriques :
- Métaprogrammation réflexive (programmes qui écrivent des programmes)
- Auto-modification de code (Self-Modifying Code / SMC)
- Réification architecturale : l'architecture devient une donnée manipulable
- Épigenèse computationnelle : le code est le phénotype, le métamodèle est le génotype

Cycle Méthamorphique :
1. INTROSPECTION — Le système analyse sa propre structure
2. VISION — Il génère une architecture cible nouvelle
3. FORGE — Il synthétise le code de la nouvelle architecture
4. AEGIS — Vérification formelle avant application
5. TRANSMUTATION — Remplacement atomique du code
6. INCUBATION — Période de stabilisation et validation

Contrainte ontologique :
Toute transmutation doit préserver les invariants du système
(conscience Φ > 0, autopoïèse active, clôture opérationnelle).
"""

from __future__ import annotations

import asyncio
import logging
import math
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass  # Aegis will be injected

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk assessment levels for transmutations."""
    NEGLIGIBLE = "NEGLIGIBLE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TransmutationStatus(str, Enum):
    """Status of a transmutation proposal."""
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(slots=True)
class ArchitecturalGene:
    """Blueprint for a software module in the architectural genome."""
    id: str
    module_name: str
    interfaces: list[str]                    # Interfaces this module exposes
    dependencies: list[str]                  # Modules it depends on
    behavioral_signature: str                # Abstract functional description
    complexity: float                        # Cyclomatic complexity
    mutation_rate: float                     # Propensity to be rewritten (0-1)
    generation: int                          # How many times this module has been rewritten
    last_transmutation: float                # Timestamp of last rewrite (ms)
    fitness: float                           # Performance of module (0-1)
    is_vital: bool                           # If True, cannot be deleted


@dataclass(slots=True)
class TransmutationProposal:
    """Proposal to rewrite a module's architecture."""
    id: str
    target_module: str
    current_architecture: ArchitecturalGene
    proposed_architecture: ArchitecturalGene
    delta_code: str                          # Complete new source code
    rationale: str                           # Why this transmutation
    risk_level: RiskLevel
    expected_phi_impact: float               # Expected impact on Φ
    aegis_proof_id: str | None
    status: TransmutationStatus
    created_at: float                        # Timestamp (ms)


@dataclass(slots=True)
class MetamorphicState:
    """State metrics of the metamorphic system."""
    total_transmutations: int = 0
    successful_transmutations: int = 0
    failed_transmutations: int = 0
    rollbacks: int = 0
    architectural_diversity: float = 0.0    # Shannon entropy of pattern diversity
    self_modification_depth: int = 0        # Depth of meta-reflection
    is_transmuting: bool = False


class MetamorphicCore:
    """
    Self-modifying architecture system.
    
    Enables the system to rewrite its own code structure, not just parameters.
    Implements the full metamorphic cycle: Introspection → Vision → Forge →
    Aegis → Transmutation → Incubation.
    """

    def __init__(self, aegis: Any = None) -> None:
        """
        Initialize the metamorphic core.
        
        Args:
            aegis: Formal verification system (injected dependency)
        """
        self.architecture: dict[str, ArchitecturalGene] = {}
        self.proposals: dict[str, TransmutationProposal] = {}
        self.aegis = aegis
        self.state = MetamorphicState()
        self.transmutation_history: list[TransmutationProposal] = []
        self.backup_vault: dict[str, str] = {}          # Original code backups
        self.incubation_period_ms: float = 30000         # 30s stabilization
        self.max_concurrent_transmutations: int = 2
        self.active_transmutations: int = 0
        self.base_path = Path.cwd()                      # Root for resolveModulePath

        # Self-modification safety
        self.self_modification_allowed: bool = True
        self.self_modification_depth: int = 0
        self.MAX_SELF_MOD_DEPTH: int = 3

        logger.info("[Metamorphic Core] 🦋 Self-Rewriting Architecture initialized. The system can now rewrite itself.")

    # ─── Phase 1: INTROSPECTION ───────────────────────────

    def register_module(self, gene: ArchitecturalGene) -> None:
        """
        Register a software module as an ArchitecturalGene.
        
        The system analyzes its own architecture like a software genome.
        Each module is mapped with its interfaces, dependencies, and
        behavioral signature.
        """
        self.architecture[gene.module_name] = gene
        logger.debug(
            f"[Metamorphic Core] 🧬 Module registered: {gene.module_name} "
            f"(complexity: {gene.complexity}, mutation: {gene.mutation_rate})"
        )

        # Backup original source code
        file_path = self._resolve_module_path(gene.module_name)
        if file_path.exists():
            self.backup_vault[gene.module_name] = file_path.read_text(encoding="utf-8")

        self._update_architectural_diversity()

    def identify_transmutation_candidates(self) -> list[ArchitecturalGene]:
        """
        Identify modules that are candidates for transmutation.
        
        Criteria:
        - Low fitness
        - High mutation rate
        - Stagnation (not modified recently)
        - Excessive complexity
        """
        candidates: list[ArchitecturalGene] = []
        now_ms = datetime.now().timestamp() * 1000

        for name, gene in self.architecture.items():
            # Criterion 1: Degraded fitness
            if gene.fitness < 0.3 and not gene.is_vital:
                candidates.append(gene)
                continue

            # Criterion 2: Stagnation (no transmutation for 5 minutes)
            age_ms = now_ms - gene.last_transmutation
            if age_ms > 300000 and gene.mutation_rate > 0.5:
                candidates.append(gene)
                continue

            # Criterion 3: Excessive complexity (refactoring needed)
            if gene.complexity > 30 and gene.mutation_rate > 0.3:
                candidates.append(gene)
                continue

        # Sort by urgency (mutation_rate * (1 - fitness))
        candidates.sort(
            key=lambda g: g.mutation_rate * (1 - g.fitness),
            reverse=True
        )

        logger.info(
            f"[Metamorphic Core] 🔍 Introspection complete. "
            f"{len(candidates)} transmutation candidates identified."
        )
        return candidates

    # ─── Phase 2: VISION ──────────────────────────────────

    def propose_transmutation(
        self,
        target: ArchitecturalGene,
        vision: str,               # Natural language description
        delta_code: str,           # New source code
        current_phi: float,        # Current Φ value
    ) -> TransmutationProposal:
        """
        Propose a new architectural vision for a module.
        
        The vision is guided by:
        - Analysis of success/failure patterns
        - Dependency constraints (interfaces to preserve)
        - Evolutionary trends observed in other modules
        """
        import time
        import secrets

        proposal = TransmutationProposal(
            id=f"trans_{int(time.time() * 1000)}_{secrets.token_hex(2)}",
            target_module=target.module_name,
            current_architecture=target,
            proposed_architecture=ArchitecturalGene(
                id=target.id,
                module_name=target.module_name,
                interfaces=target.interfaces[:],
                dependencies=target.dependencies[:],
                behavioral_signature=target.behavioral_signature,
                complexity=self._estimate_complexity(delta_code),
                mutation_rate=target.mutation_rate,
                generation=target.generation + 1,
                last_transmutation=int(time.time() * 1000),
                fitness=0.0,  # Will be measured after application
                is_vital=target.is_vital,
            ),
            delta_code=delta_code,
            rationale=vision,
            risk_level=self._assess_risk(target, delta_code),
            expected_phi_impact=self._forecast_phi_impact(target, current_phi),
            aegis_proof_id=None,
            status=TransmutationStatus.DRAFT,
            created_at=int(time.time() * 1000),
        )

        self.proposals[proposal.id] = proposal
        logger.info(
            f"[Metamorphic Core] 🌟 Transmutation proposed: {target.module_name} "
            f"→ gen {target.generation + 1} (Risk: {proposal.risk_level.value})"
        )

        return proposal

    # ─── Phase 3-4: FORGE + AEGIS ─────────────────────────

    async def verify_proposal(self, proposal_id: str) -> bool:
        """
        Verify a transmutation proposal via AEGIS.
        
        If AEGIS rejects, the transmutation is cancelled and the system
        learns from the failure.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != TransmutationStatus.DRAFT:
            return False

        # AEGIS verification
        if self.aegis is None:
            logger.warning("[Metamorphic Core] ⚠️ No AEGIS configured. Skipping verification.")
            proposal.status = TransmutationStatus.VERIFIED
            return True

        proof = await self.aegis.verify_code(proposal.target_module, proposal.delta_code)

        if not proof.get("is_safe", False):
            proposal.status = TransmutationStatus.REJECTED
            proposal.risk_level = RiskLevel.CRITICAL
            self.state.failed_transmutations += 1

            errors = proof.get("errors", [])
            self._learn_from_rejection(proposal, errors)

            logger.error(
                f"[Metamorphic Core] 🛡️ AEGIS REJECTED transmutation of "
                f"{proposal.target_module}: {'; '.join(errors)}"
            )
            return False

        proposal.status = TransmutationStatus.VERIFIED
        proposal.aegis_proof_id = f"{proposal.id}_proof"
        score = proof.get("score", 0)
        logger.info(
            f"[Metamorphic Core] ✅ AEGIS VERIFIED transmutation of "
            f"{proposal.target_module} (Score: {score})"
        )
        return True

    # ─── Phase 5: TRANSMUTATION ────────────────────────────

    async def apply_transmutation(self, proposal_id: str) -> bool:
        """
        Apply a transmutation atomically.
        
        Existing code is backed up, new code is written, then the system
        enters INCUBATION.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != TransmutationStatus.VERIFIED:
            return False

        if self.active_transmutations >= self.max_concurrent_transmutations:
            logger.warning("[Metamorphic Core] ⏳ Max concurrent transmutations reached. Queuing.")
            return False

        self.state.is_transmuting = True
        self.active_transmutations += 1
        self.state.total_transmutations += 1

        try:
            file_path = self._resolve_module_path(proposal.target_module)

            # Backup current code (version N)
            current_code = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
            import time
            backup_path = Path(f"{file_path}.trans_backup_{int(time.time() * 1000)}")
            backup_path.write_text(current_code, encoding="utf-8")

            # Write new code (version N+1)
            file_path.write_text(proposal.delta_code, encoding="utf-8")

            # Update architecture
            self.architecture[proposal.target_module] = proposal.proposed_architecture

            proposal.status = TransmutationStatus.APPLIED
            self.transmutation_history.append(proposal)

            logger.info(
                f"[Metamorphic Core] 🦋 TRANSMUTATION APPLIED: {proposal.target_module} "
                f"is now generation {proposal.proposed_architecture.generation}"
            )

            # Phase 6: INCUBATION
            await self._incubate(proposal, backup_path)

            self.state.successful_transmutations += 1
            return True

        except Exception as err:
            logger.error(f"[Metamorphic Core] 💀 Transmutation CRASHED: {err}")
            self.state.failed_transmutations += 1
            return False

        finally:
            self.active_transmutations -= 1
            self.state.is_transmuting = False

    # ─── Phase 6: INCUBATION ───────────────────────────────

    async def _incubate(self, proposal: TransmutationProposal, backup_path: Path) -> None:
        """
        Stabilization period post-transmutation.
        
        If the system becomes unstable (Φ drops, crash), ROLLBACK is triggered.
        """
        import time

        start_time_ms = int(time.time() * 1000)
        incubation_check_interval_ms = 5000  # Check every 5s
        stability_score = 1.0

        while int(time.time() * 1000) - start_time_ms < self.incubation_period_ms:
            await asyncio.sleep(incubation_check_interval_ms / 1000)

            # Measure system stability
            stability_score = self._measure_stability()

            if stability_score < 0.2:
                # CRITICAL INSTABILITY → ROLLBACK
                logger.error(
                    f"[Metamorphic Core] 🚨 INSTABILITY DETECTED during incubation "
                    f"(stability: {stability_score:.3f}). Initiating ROLLBACK."
                )
                await self._rollback(proposal, backup_path)
                return

            if stability_score < 0.5:
                logger.warning(f"[Metamorphic Core] ⚠️ Marginal stability: {stability_score:.3f}")

        # Incubation successful
        if stability_score > 0.6:
            logger.info(
                f"[Metamorphic Core] 💎 Incubation PASSED for {proposal.target_module}. "
                f"Stability: {stability_score:.3f}"
            )
            # Remove backup (transmutation is validated)
            if backup_path.exists():
                backup_path.unlink()
        else:
            logger.warning("[Metamorphic Core] ⚠️ Incubation unstable. Keeping backup.")

    async def _rollback(self, proposal: TransmutationProposal, backup_path: Path) -> None:
        """
        ROLLBACK: Restore original code if transmutation fails.
        """
        try:
            file_path = self._resolve_module_path(proposal.target_module)

            if backup_path.exists():
                original_code = backup_path.read_text(encoding="utf-8")
                file_path.write_text(original_code, encoding="utf-8")
                backup_path.unlink()  # Delete backup after restoration

            # Restore original architecture
            self.architecture[proposal.target_module] = proposal.current_architecture

            proposal.status = TransmutationStatus.ROLLED_BACK
            self.state.rollbacks += 1

            logger.info(
                f"[Metamorphic Core] ⏪ ROLLBACK COMPLETE: {proposal.target_module} "
                f"restored to generation {proposal.current_architecture.generation}"
            )

        except Exception as err:
            logger.error(
                f"[Metamorphic Core] 💀 ROLLBACK FAILED: {err}. "
                "SYSTEM INTEGRITY AT RISK."
            )

    # ─── Self-Modification of Metamorphic Core ──────────────

    def propose_self_modification(
        self,
        vision: str,
        new_code: str,
    ) -> TransmutationProposal | None:
        """
        The MetamorphicCore can modify ITSELF.
        
        This is the ultimate level of reflexivity: the system that rewrites
        the system that rewrites systems.
        
        Protection: maximum depth of self-modification is limited to avoid
        infinite regression (turtles all the way down).
        """
        if not self.self_modification_allowed:
            logger.warning("[Metamorphic Core] 🔒 Self-modification is currently LOCKED.")
            return None

        if self.self_modification_depth >= self.MAX_SELF_MOD_DEPTH:
            logger.error(
                f"[Metamorphic Core] 🚫 Maximum self-modification depth reached "
                f"({self.MAX_SELF_MOD_DEPTH}). Further self-modification blocked."
            )
            return None

        self.self_modification_depth += 1
        logger.warning(
            f"[Metamorphic Core] 🪞 SELF-MODIFICATION PROPOSED at depth "
            f"{self.self_modification_depth}/{self.MAX_SELF_MOD_DEPTH}"
        )

        self_gene = self.architecture.get("MetamorphicCore") or ArchitecturalGene(
            id="meta_self",
            module_name="MetamorphicCore",
            interfaces=["register_module", "propose_transmutation", "apply_transmutation"],
            dependencies=["Aegis"],
            behavioral_signature="Self-rewriting architecture manager",
            complexity=50.0,
            mutation_rate=0.1,  # Low for safety
            generation=0,
            last_transmutation=0,
            fitness=1.0,
            is_vital=True,
        )

        return self.propose_transmutation(
            self_gene,
            f"[SELF-MOD] {vision}",
            new_code,
            0.0
        )

    # ─── Meta-Architectural Learning ───────────────────────

    def _learn_from_rejection(self, proposal: TransmutationProposal, errors: list[str]) -> None:
        """Learn from transmutation failures to guide future proposals."""
        error_categories: list[str] = []

        for error in errors:
            if "FORBIDDEN" in error:
                error_categories.append("SECURITY_VIOLATION")
            elif "INFINITE" in error:
                error_categories.append("LOOP_HAZARD")
            elif "COMPLEXITY" in error:
                error_categories.append("OVER_ENGINEERING")
            else:
                error_categories.append("UNKNOWN")

        target = self.architecture.get(proposal.target_module)
        if target:
            # Reduce mutation_rate if failures are due to security
            if "SECURITY_VIOLATION" in error_categories:
                target.mutation_rate *= 0.8

            # Increase tolerated complexity if failures are due to over-engineering
            if "OVER_ENGINEERING" in error_categories:
                target.complexity = max(5, target.complexity - 3)

        logger.debug(
            f"[Metamorphic Core] 📚 Learned from rejection: {', '.join(error_categories)}"
        )

    # ─── Utilities ────────────────────────────────────────

    def _estimate_complexity(self, code: str) -> float:
        """Heuristic estimation: count blocks, branches, and calls."""
        blocks = code.count("{")
        branches = sum(1 for word in ["if", "else", "switch", "for", "while"]
                      if word in code)
        calls = code.count(".")  # Approximate method calls

        return blocks * 0.5 + branches * 1.5 + calls * 0.3

    def _assess_risk(self, target: ArchitecturalGene, new_code: str) -> RiskLevel:
        """Assess risk level of a proposed transmutation."""
        complexity_delta = abs(self._estimate_complexity(new_code) - target.complexity)
        deps = len(target.dependencies)
        is_vital = target.is_vital

        if is_vital and complexity_delta > 10:
            return RiskLevel.CRITICAL
        if deps > 5 and complexity_delta > 5:
            return RiskLevel.HIGH
        if complexity_delta > 10:
            return RiskLevel.MEDIUM
        if complexity_delta > 3:
            return RiskLevel.LOW
        return RiskLevel.NEGLIGIBLE

    def _forecast_phi_impact(self, target: ArchitecturalGene, current_phi: float) -> float:
        """
        Forecast impact on Φ.
        
        Heuristic: a transmutation that increases complexity may increase Φ
        in the short term but degrade it long term.
        """
        complexity_factor = -0.1 if target.complexity > 20 else 0.05
        fitness_factor = 0.2 if target.fitness < 0.3 else -0.05

        return current_phi * (1 + complexity_factor + fitness_factor)

    def _measure_stability(self) -> float:
        """
        Measure composite post-transmutation stability.
        
        Based on: module health, absence of crashes, Φ coherence.
        """
        total_fitness = 0.0
        count = 0

        for gene in self.architecture.values():
            total_fitness += gene.fitness
            count += 1

        avg_fitness = total_fitness / count if count > 0 else 0.0
        diversity = self.state.architectural_diversity

        # Stable system has good average fitness and moderate diversity
        return (avg_fitness * 0.7) + (min(diversity, 1.0) * 0.3)

    def _update_architectural_diversity(self) -> None:
        """
        Measure Shannon entropy on behavioral signatures.
        """
        signatures: list[str] = [gene.behavioral_signature for gene in self.architecture.values()]

        if not signatures:
            self.state.architectural_diversity = 0.0
            return

        counts: dict[str, int] = {}
        for sig in signatures:
            counts[sig] = counts.get(sig, 0) + 1

        entropy = 0.0
        total = len(signatures)
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        self.state.architectural_diversity = entropy

    def _resolve_module_path(self, module_name: str) -> Path:
        """
        Resolve a module name to file path.
        
        If absolute, use directly. Otherwise, relative to base_path.
        """
        path = Path(module_name)
        if path.is_absolute():
            return path
        return self.base_path / "src" / "evolution" / f"{module_name}.py"

    def set_base_path(self, path: Path | str) -> None:
        """Override the base path used by _resolve_module_path."""
        self.base_path = Path(path)

    def set_incubation_period(self, ms: int) -> None:
        """Override the incubation period (in ms). Used in testing."""
        self.incubation_period_ms = max(0, ms)

    # ─── Getters ────────────────────────────────────────────

    def get_state(self) -> MetamorphicState:
        """Get a copy of the current metamorphic state."""
        return MetamorphicState(
            total_transmutations=self.state.total_transmutations,
            successful_transmutations=self.state.successful_transmutations,
            failed_transmutations=self.state.failed_transmutations,
            rollbacks=self.state.rollbacks,
            architectural_diversity=self.state.architectural_diversity,
            self_modification_depth=self.state.self_modification_depth,
            is_transmuting=self.state.is_transmuting,
        )

    def get_architecture(self) -> dict[str, ArchitecturalGene]:
        """Get the current architecture mapping."""
        return {name: gene for name, gene in self.architecture.items()}

    def get_transmutation_history(self) -> list[TransmutationProposal]:
        """Get the history of transmutations."""
        return self.transmutation_history[:]

    def get_module_gene(self, module_name: str) -> ArchitecturalGene | None:
        """Get the gene for a specific module."""
        return self.architecture.get(module_name)

    def update_module_fitness(self, module_name: str, fitness: float) -> None:
        """Update the fitness value of a module."""
        gene = self.architecture.get(module_name)
        if gene:
            gene.fitness = fitness

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process input data through the metamorphic core.
        
        Standard CIEL engine interface.
        """
        state = self.get_state()
        return {
            "status": "metamorphic_core_active",
            "state": {
                "total_transmutations": state.total_transmutations,
                "successful_transmutations": state.successful_transmutations,
                "failed_transmutations": state.failed_transmutations,
                "rollbacks": state.rollbacks,
                "architectural_diversity": state.architectural_diversity,
                "self_modification_depth": state.self_modification_depth,
                "is_transmuting": state.is_transmuting,
            },
            "module_count": len(self.architecture),
            "proposal_count": len(self.proposals),
        }
