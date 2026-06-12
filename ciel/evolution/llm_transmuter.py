"""
CIEL v1.0 — LLMTransmuter : auto-réécriture de code assistée par LLM.

Migré depuis Hydra, adapté pour CIEL.
Propose des modifications de code, les vérifie via Aegis,
et les applique avec un budget de transmutation.
Respecte l'axiome γ (réversibilité) via snapshots.
"""
from __future__ import annotations

import difflib
import hashlib
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.evolution.aegis import Aegis, AuditResult
from ciel.evolution.transmutation_budget import TransmutationBudget


@dataclass(slots=True)
class TransmutationProposal:
    id: str
    file_path: str
    original_content: str
    proposed_content: str
    intent: str
    diff: str = ""
    verified: bool = False
    applied: bool = False
    rolled_back: bool = False
    created_at: float = field(default_factory=time.time)
    verified_at: float | None = None
    applied_at: float | None = None


class LLMTransmuter:
    """Système d'auto-amélioration de code CIEL.

    Cycle :
      1. PROPOSE : Un LLM (ou règle) propose une modification
      2. VERIFY  : Aegis vérifie statiquement le changement
      3. BUDGET  : Vérifie le budget de transmutation disponible
      4. APPLY   : Sauvegarde snapshot + applique le changement
      5. ROLLBACK: Possible si échec (axiome γ)
    """

    def __init__(self, root_path: str | Path = "."):
        self.root = Path(root_path).resolve()
        self.aegis = Aegis()
        self.budget = TransmutationBudget()
        self.history: list[TransmutationProposal] = []
        self._snapshot_dir = self.root / ".ciel" / "snapshots"
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)

    def transmutate(self, file_path: str, intent: str, proposed_content: str) -> TransmutationProposal:
        """Propose et applique une transmutation de code.

        Args:
            file_path: Chemin relatif du fichier à modifier
            intent: Description de l'intention de modification
            proposed_content: Nouveau contenu proposé

        Returns:
            TransmutationProposal avec le résultat
        """
        abs_path = (self.root / file_path).resolve()

        if not abs_path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {abs_path}")

        original = abs_path.read_text(encoding="utf-8")
        diff = self._generate_diff(original, proposed_content, file_path)

        proposal = TransmutationProposal(
            id=f"TRANS-{uuid.uuid4().hex[:12]}",
            file_path=file_path,
            original_content=original,
            proposed_content=proposed_content,
            intent=intent,
            diff=diff,
        )

        # Phase 1: Vérification Aegis
        audit = self.aegis.audit(proposed_content, file_path)
        proposal.verified = audit.passed
        proposal.verified_at = time.time()

        if not audit.passed:
            self.history.append(proposal)
            return proposal

        # Phase 2: Budget check
        if not self.budget.consume(proposal.id):
            proposal.verified = False
            self.history.append(proposal)
            return proposal

        # Phase 3: Snapshot (axiome γ)
        self._save_snapshot(file_path, original)

        # Phase 4: Apply
        abs_path.write_text(proposed_content, encoding="utf-8")
        proposal.applied = True
        proposal.applied_at = time.time()

        self.history.append(proposal)
        return proposal

    def rollback(self, proposal_id: str) -> bool:
        """Annule une transmutation (axiome γ - Réversibilité)."""
        for prop in self.history:
            if prop.id == proposal_id and prop.applied and not prop.rolled_back:
                # Restore from snapshot
                snapshot = self._load_snapshot(prop.file_path)
                if snapshot:
                    abs_path = (self.root / prop.file_path).resolve()
                    abs_path.write_text(snapshot, encoding="utf-8")
                    prop.rolled_back = True
                    self.budget.refund(prop.id)
                    return True
        return False

    def list_transmutations(self, limit: int = 50) -> list[dict]:
        return [
            {
                "id": p.id,
                "file": p.file_path,
                "intent": p.intent,
                "verified": p.verified,
                "applied": p.applied,
                "rolled_back": p.rolled_back,
            }
            for p in self.history[-limit:]
        ]

    def _generate_diff(self, original: str, proposed: str, file_path: str) -> str:
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
        return "".join(diff)

    def _save_snapshot(self, file_path: str, content: str) -> Path:
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        snap_path = self._snapshot_dir / f"{file_path.replace('/', '_')}.{hash_digest}.snap"
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        snap_path.write_text(content, encoding="utf-8")
        return snap_path

    def _load_snapshot(self, file_path: str) -> str | None:
        pattern = f"{file_path.replace('/', '_')}.*.snap"
        snapshots = sorted(self._snapshot_dir.glob(pattern))
        if not snapshots:
            return None
        return snapshots[-1].read_text(encoding="utf-8")
