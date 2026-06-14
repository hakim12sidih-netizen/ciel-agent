"""
CIEL v1.0 — Aegis : audit statique de code pour auto-réécriture.

Migré depuis Hydra, adapté pour CIEL.
Vérifie que les modifications proposées sont sûres :
  - Syntaxe Python valide (compile)
  - Pas d'imports dangereux
  - Pas de boucles infinies évidentes
  - Pas d'accès aux secrets
  - Respect des conventions CIEL
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any


DANGEROUS_IMPORTS = {
    "os.system", "os.popen", "subprocess.call", "subprocess.Popen",
    "subprocess.run", "shutil.rmtree", "shutil.chown",
    "eval", "exec", "compile", "__import__",
    "pickle.loads", "pickle.load", "shelve.open",
    "ctypes.CDLL", "ctypes.WinDLL",
}

DANGEROUS_PATTERNS = [
    (r"open\(.*['\"][rwab+]+['\"]\)", "File write operations"),
    (r"\.env|API_KEY|SECRET|PASSWORD|TOKEN", "Potential secret exposure"),
    (r"while\s+True\s*:", "Infinite loop risk"),
    (r"os\.environ", "Environment access"),
    (r"sys\.stdin", "Standard input"),
    (r"ptyprocess|pexpect", "PTY operations"),
]


@dataclass(slots=True)
class AuditFinding:
    line: int
    severity: str
    message: str
    category: str

    def to_dict(self) -> dict:
        return {"line": self.line, "severity": self.severity,
                "message": self.message, "category": self.category}


@dataclass(slots=True)
class AuditResult:
    passed: bool
    findings: list[AuditFinding] = field(default_factory=list)
    score: float = 1.0

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "finding_count": len(self.findings),
            "score": round(self.score, 2),
            "findings": [f.to_dict() for f in self.findings],
        }


class Aegis:
    """Bouclier d'audit statique pour CIEL.

    Vérifie que les modifications de code proposées
    respectent les règles de sécurité et de qualité.
    """

    def audit(self, code: str, file_path: str = "unknown") -> AuditResult:
        findings: list[AuditFinding] = []

        # 1. Vérification syntaxique
        findings.extend(self._check_syntax(code, file_path))

        # 2. Analyse AST
        try:
            tree = ast.parse(code)
            findings.extend(self._check_imports(tree))
            findings.extend(self._check_ast_patterns(tree))
        except SyntaxError:
            pass  # déjà rapporté dans _check_syntax

        # 3. Pattern matching regex
        findings.extend(self._check_regex_patterns(code))

        # 4. Score
        score = max(0.0, 1.0 - len(findings) * 0.15)
        passed = score >= 0.5 and not any(f.severity == "critical" for f in findings)

        return AuditResult(passed=passed, findings=findings, score=score)

    def _check_syntax(self, code: str, file_path: str) -> list[AuditFinding]:
        findings = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            findings.append(AuditFinding(
                line=e.lineno or 0,
                severity="critical",
                message=f"SyntaxError: {e.msg}",
                category="syntax",
            ))
        return findings

    def _check_imports(self, tree: ast.AST) -> list[AuditFinding]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {i.split(".")[0] for i in DANGEROUS_IMPORTS}:
                        findings.append(AuditFinding(
                            line=node.lineno,
                            severity="critical",
                            message=f"Import dangereux: {alias.name}",
                            category="security",
                        ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}"
                    if full_name in DANGEROUS_IMPORTS or module in {i.split(".")[0] for i in DANGEROUS_IMPORTS}:
                        findings.append(AuditFinding(
                            line=node.lineno,
                            severity="critical",
                            message=f"Import dangereux: {full_name}",
                            category="security",
                        ))
        return findings

    def _check_ast_patterns(self, tree: ast.AST) -> list[AuditFinding]:
        findings = []
        for node in ast.walk(tree):
            # Vérifie les appels à eval/exec
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec", "compile"):
                    findings.append(AuditFinding(
                        line=node.lineno,
                        severity="critical",
                        message=f"Appel à {node.func.id}() interdit",
                        category="security",
                    ))
        return findings

    def _check_regex_patterns(self, code: str) -> list[AuditFinding]:
        findings = []
        for i, line in enumerate(code.splitlines(), 1):
            for pattern, desc in DANGEROUS_PATTERNS:
                if re.search(pattern, line):
                    findings.append(AuditFinding(
                        line=i,
                        severity="warning",
                        message=f"{desc} détecté",
                        category="security",
                    ))
        return findings
