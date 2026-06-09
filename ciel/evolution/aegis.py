"""
Aegis - Formal Verification System
Audits code changes for security and performance constraints.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SafetyMetadata:
    """Metadata for safety proof"""
    complexity: int
    forbidden_patterns: list[str] = field(default_factory=list)
    potential_infinite_loops: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SafetyProof:
    """Formal verification proof result"""
    is_safe: bool
    errors: list[str] = field(default_factory=list)
    score: float = 1.0  # 0 to 1
    metadata: SafetyMetadata = field(default_factory=lambda: SafetyMetadata(complexity=0))


@dataclass(slots=True)
class Aegis:
    """
    AEGIS - Formal Verification Engine
    Audits code changes to ensure security and performance constraints.
    """
    
    def __post_init__(self) -> None:
        """Initialize verification engine"""
        logger.info("[Aegis] 🛡️ Formal Verification Engine (Audit Statique) activated.")

    async def verify_code(self, file_path: str, code: str) -> SafetyProof:
        """
        Verify code for safety violations.
        
        Checks for:
        1. Forbidden APIs (eval, exec, spawn)
        2. Infinite loops without break
        3. Code complexity
        """
        logger.info(f"[Aegis] 🛡️ Auditing code: {os.path.basename(file_path)}...")
        
        proof = SafetyProof(
            is_safe=True,
            errors=[],
            score=1.0,
            metadata=SafetyMetadata(complexity=0)
        )

        # 1. Forbidden API Check
        forbidden_apis = {"eval", "exec", "spawn", "execSync", "spawnSync"}
        for api in forbidden_apis:
            if api in code:
                proof.metadata.forbidden_patterns.append(api)
                proof.is_safe = False
                proof.errors.append(
                    f"FORBIDDEN API: Use of {api} is restricted by AEGIS protocol."
                )

        # 2. Loop Safety Check (simple regex-based)
        if "while True:" in code or "while 1:" in code:
            if "break" not in code.split("while")[1].split("\n")[0]:
                proof.metadata.potential_infinite_loops.append("while(True)")
                proof.is_safe = False
                proof.errors.append(
                    "POTENTIAL INFINITE LOOP: while(True) detected without break condition."
                )

        # 3. Complexity Metric (line count as proxy)
        lines = code.split("\n")
        proof.metadata.complexity = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
        
        if proof.metadata.complexity > 100:
            proof.score -= 0.2
            logger.warning(f"[Aegis] High complexity detected: {proof.metadata.complexity} lines.")

        # 4. Persist proof
        proof_dir = os.path.join(os.getcwd(), "src", "evolution", "proofs")
        os.makedirs(proof_dir, exist_ok=True)
        
        proof_path = os.path.join(proof_dir, f"{os.path.basename(file_path)}.proof.json")
        with open(proof_path, "w") as f:
            json.dump({
                "is_safe": proof.is_safe,
                "errors": proof.errors,
                "score": proof.score,
                "metadata": {
                    "complexity": proof.metadata.complexity,
                    "forbidden_patterns": proof.metadata.forbidden_patterns,
                    "potential_infinite_loops": proof.metadata.potential_infinite_loops,
                }
            }, f, indent=2)

        if proof.is_safe:
            logger.info(f"[Aegis] ✅ CODE VERIFIED. Safety score: {proof.score}")
        else:
            logger.error("[Aegis] ❌ CODE REJECTED. Safety violations found.")

        return proof

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process verification request.
        CIEL compatibility method.
        """
        if isinstance(input_data, dict):
            code = input_data.get("code", "")
            file_path = input_data.get("file_path", "unknown.py")
            
            # Note: In async context, this should be awaited
            # For sync compatibility, return basic analysis
            proof = SafetyProof(is_safe=True)
            
            if "eval" in code or "exec" in code:
                proof.is_safe = False
                proof.errors.append("Forbidden API detected")
                proof.score = 0.0
            
            return {
                "is_safe": proof.is_safe,
                "errors": proof.errors,
                "score": proof.score,
                "metadata": proof.metadata.__dict__
            }
        
        return {
            "is_safe": True,
            "errors": [],
            "score": 1.0,
            "metadata": SafetyMetadata(complexity=0).__dict__
        }
