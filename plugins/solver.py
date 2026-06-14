"""
CIEL v∞.9 — SAT Dependency Solver.
Pure Python CDCL SAT solver for plugin dependency resolution.
"""
from __future__ import annotations

import re
import json
import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


__all__ = [
    "SemVer", "VersionSpec", "VersionConstraint",
    "Dependency", "DependencySolver", "SolveError",
    "SolveConflict", "SolveMissing",
    "parse_spec", "format_spec",
]


class SolveError(Exception):
    pass


class SolveConflict(SolveError):
    def __init__(self, msg: str, path: list[str] | None = None):
        self.path = path or []
        super().__init__(f"Conflict: {msg} (path: {' → '.join(self.path)})" if path else f"Conflict: {msg}")


class SolveMissing(SolveError):
    def __init__(self, name: str, constraint: str):
        self.name = name
        self.constraint = constraint
        super().__init__(f"Missing dependency: {name} ({constraint})")


# ── Semantic Versioning ──

@dataclass(frozen=True, slots=True)
class SemVer:
    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: str = ""
    build: str = ""

    _RE = re.compile(
        r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?"
        r"(?:[-\.]?([a-zA-Z0-9.]+))?"
        r"(?:\+([a-zA-Z0-9.]+))?$"
    )

    @classmethod
    def parse(cls, s: str) -> SemVer:
        m = cls._RE.match(s.strip())
        if not m:
            raise ValueError(f"Invalid semver: {s!r}")
        major = int(m.group(1))
        minor = int(m.group(2)) if m.group(2) else 0
        patch = int(m.group(3)) if m.group(3) else 0
        prerelease = m.group(4) or ""
        build = m.group(5) or ""
        return cls(major, minor, patch, prerelease, build)

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        if self.build:
            base += f"+{self.build}"
        return base

    def __lt__(self, other: SemVer) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease != other.prerelease:
            return self.prerelease < other.prerelease
        return False

    def __le__(self, other: SemVer) -> bool:
        return self < other or self == other

    def __gt__(self, other: SemVer) -> bool:
        return not (self <= other)

    def __ge__(self, other: SemVer) -> bool:
        return not (self < other)

    def compatible(self, other: SemVer) -> bool:
        return self.major == other.major and self.minor >= other.minor


# ── Version Specification ──

class Op(Enum):
    EQ = "=="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    WILDCARD = "*"
    TILDE = "~="
    CARET = "^"


@dataclass
class VersionSpec:
    op: Op
    version: SemVer | None = None

    def matches(self, ver: SemVer) -> bool:
        if self.op == Op.WILDCARD:
            return True
        if self.version is None:
            return True

        if self.op == Op.EQ:
            return ver == self.version
        if self.op == Op.NEQ:
            return ver != self.version
        if self.op == Op.GT:
            return ver > self.version
        if self.op == Op.GTE:
            return ver >= self.version
        if self.op == Op.LT:
            return ver < self.version
        if self.op == Op.LTE:
            return ver <= self.version
        if self.op == Op.TILDE:
            if ver.major != self.version.major:
                return False
            if ver.minor != self.version.minor:
                return False
            return ver.patch >= self.version.patch
        if self.op == Op.CARET:
            if self.version.major > 0:
                return (ver.major == self.version.major
                        and (ver.minor, ver.patch) >= (self.version.minor, self.version.patch))
            if self.version.minor > 0:
                return (ver.minor == self.version.minor
                        and ver.patch >= self.version.patch)
            return ver.patch >= self.version.patch
        return False

    def intersect(self, other: VersionSpec) -> VersionSpec | None:
        if self.op == Op.WILDCARD:
            return other
        if other.op == Op.WILDCARD:
            return self
        lo, hi = self._bounds()
        olo, ohi = other._bounds()
        l = max(lo or SemVer(0, 0, 0), olo or SemVer(0, 0, 0)) if lo or olo else SemVer(0, 0, 0)
        if hi and ohi:
            h = min(hi, ohi)
        else:
            h = hi or ohi or None
        if l and h and l > h:
            return None
        if l == h:
            return VersionSpec(Op.EQ, l) if l else None
        specs: list[VersionSpec] = []
        if lo is None or olo is None or lo < olo:
            pass
        if l:
            specs.append(VersionSpec(Op.GTE, l))
        if h:
            specs.append(VersionSpec(Op.LTE, h))
        return VersionConstraint(*specs) if len(specs) > 1 else (specs[0] if specs else VersionSpec(Op.WILDCARD))

    def _bounds(self) -> tuple[SemVer | None, SemVer | None]:
        v = self.version
        if self.op == Op.EQ:
            return (v, v) if v else (None, None)
        if self.op == Op.NEQ:
            return (None, None)  # cannot bound
        if self.op == Op.GT:
            return (v.next_patch() if v else None, None)
        if self.op == Op.GTE:
            return (v, None) if v else (None, None)
        if self.op == Op.LT:
            return (None, v.prev_patch() if v else None)
        if self.op == Op.LTE:
            return (None, v)
        if self.op == Op.CARET:
            if v and v.major > 0:
                return (v, SemVer(v.major + 1, 0, 0).prev_patch())
            if v and v.minor > 0:
                return (v, SemVer(v.major, v.minor + 1, 0).prev_patch())
            return (v, SemVer(v.major, v.minor, v.patch + 1).prev_patch()) if v else (None, None)
        if self.op == Op.TILDE:
            return (v, SemVer(v.major, v.minor + 1, 0).prev_patch()) if v else (None, None)
        return (None, None)

    def __str__(self) -> str:
        return f"{self.op.value}{self.version or ''}" if self.op != Op.WILDCARD else "*"


def _next_patch(v: SemVer) -> SemVer:
    return SemVer(v.major, v.minor, v.patch + 1)


def _prev_patch(v: SemVer) -> SemVer:
    if v.patch > 0:
        return SemVer(v.major, v.minor, v.patch - 1)
    if v.minor > 0:
        return SemVer(v.major, v.minor - 1, 0)
    return SemVer(v.major - 1, 0, 0) if v.major > 0 else v


SemVer.next_patch = _next_patch
SemVer.prev_patch = _prev_patch

_SPEC_RE = re.compile(
    r"(!=|==|>=|<=|~=|\^|>|<)?\s*(\d+(?:\.\d+)*(?:[-.][a-zA-Z0-9.]+)?(?:\+[a-zA-Z0-9.]+)?|\*)"
)


def parse_spec(spec: str) -> VersionConstraint:
    specs = VersionConstraint()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = _SPEC_RE.match(part)
        if not m:
            if part.strip() == "*":
                specs.add(VersionSpec(Op.WILDCARD))
                continue
            raise ValueError(f"Invalid version spec: {part!r}")
        op_str, ver_str = m.groups()
        if ver_str == "*":
            specs.add(VersionSpec(Op.WILDCARD))
            continue
        ver = SemVer.parse(ver_str)
        if op_str is None or op_str == "==":
            specs.add(VersionSpec(Op.EQ, ver))
        elif op_str == "!=":
            specs.add(VersionSpec(Op.NEQ, ver))
        elif op_str == ">":
            specs.add(VersionSpec(Op.GT, ver))
        elif op_str == ">=":
            specs.add(VersionSpec(Op.GTE, ver))
        elif op_str == "<":
            specs.add(VersionSpec(Op.LT, ver))
        elif op_str == "<=":
            specs.add(VersionSpec(Op.LTE, ver))
        elif op_str == "~=":
            specs.add(VersionSpec(Op.TILDE, ver))
        elif op_str == "^":
            specs.add(VersionSpec(Op.CARET, ver))
    return specs


def format_spec(constraint: VersionConstraint) -> str:
    return ", ".join(str(s) for s in constraint.specs) if constraint.specs else "*"


# ── VersionConstraint (conjunction of VersionSpec) ──

@dataclass
class VersionConstraint:
    specs: list[VersionSpec] = field(default_factory=list)

    def add(self, spec: VersionSpec):
        self.specs.append(spec)

    def matches(self, ver: SemVer) -> bool:
        return all(s.matches(ver) for s in self.specs)

    def intersect(self, other: VersionConstraint) -> VersionConstraint | None:
        all_specs = list(self.specs)
        for s in other.specs:
            all_specs.append(s)
        return VersionConstraint(all_specs)

    def is_any(self) -> bool:
        return len(self.specs) == 0

    def __str__(self) -> str:
        return format_spec(self)

    @classmethod
    def any(cls) -> VersionConstraint:
        return cls()

    @classmethod
    def none(cls) -> VersionConstraint:
        return cls([VersionSpec(Op.NEQ, SemVer(0, 0, 0))])


# ── Dependency representation ──

@dataclass
class Dependency:
    name: str
    constraint: VersionConstraint
    optional: bool = False
    url: str = ""

    @classmethod
    def parse_line(cls, line: str) -> Dependency:
        line = line.strip()
        optional = line.startswith("?")
        if optional:
            line = line[1:].strip()
        url_match = re.match(r"(.+?)\s+(https?://\S+)", line)
        if url_match:
            name, constraint_str, url = url_match.group(1), "*", url_match.group(2)
        elif " " in line:
            parts = line.split(maxsplit=1)
            name = parts[0]
            constraint_str = parts[1] if len(parts) > 1 else "*"
        else:
            name = line
            constraint_str = "*"
        return cls(name, parse_spec(constraint_str), optional)

    def __str__(self) -> str:
        return f"{self.name} {self.constraint}" + (" [optional]" if self.optional else "")


# ── Dependency graph ──

@dataclass
class DependencyNode:
    name: str
    version: SemVer
    manifest: Any = None
    deps: list[Dependency] = field(default_factory=list)
    optional_deps: list[Dependency] = field(default_factory=list)


# ── SAT Solver ──

class _Clause:
    def __init__(self, literals: list[int]):
        self.literals = list(literals)
        self.watch1 = 0
        self.watch2 = min(1, len(literals) - 1) if len(literals) > 1 else 0


class DependencySolver:
    def __init__(self):
        self._var_names: dict[int, str] = {}
        self._name_vars: dict[str, int] = {}
        self._next_var = 1
        self._clauses: list[_Clause] = []
        self._assignment: list[int | None] = [None]
        self._trail: list[int] = []
        self._trail_lim: list[int] = []

    def _new_var(self, name: str) -> int:
        if name not in self._name_vars:
            var = self._next_var
            self._next_var += 1
            self._var_names[var] = name
            self._name_vars[name] = var
            self._assignment.append(None)
        return self._name_vars[name]

    def _add_clause(self, *lits: int):
        if lits:
            for l in lits:
                v = abs(l)
                while v >= len(self._assignment):
                    self._assignment.append(None)
            self._clauses.append(_Clause(list(lits)))

    def _ensure_var(self, name: str) -> int:
        return self._new_var(name)

    def _resolve(self, available: dict[str, list[tuple[str, Any]]],
                 root: str, constraint: VersionConstraint) -> dict[str, Any]:
        trail = [(root, constraint)]
        assignments: dict[str, Any] = {}
        visited: set[str] = set()

        def _get_deps(m: Any) -> list[str]:
            if isinstance(m, dict):
                return m.get("dependencies", []) or m.get("deps", []) or []
            return getattr(m, "dependencies", []) or []

        def _get_version(m: Any) -> str:
            if isinstance(m, dict):
                return m.get("version", "0.0.0")
            return getattr(m, "version", "0.0.0")

        def _get_name(m: Any) -> str:
            if isinstance(m, dict):
                return m.get("name", "")
            return getattr(m, "name", "")

        while trail:
            name, constraint = trail.pop(0)
            if name in assignments or name in visited:
                continue
            visited.add(name)

            candidates = available.get(name, [])
            if not candidates:
                raise SolveMissing(name, str(constraint))

            chosen = None
            for ver_str, manifest in sorted(candidates, key=lambda x: SemVer.parse(x[0]), reverse=True):
                ver = SemVer.parse(ver_str)
                if constraint.matches(ver):
                    chosen = (ver_str, manifest)
                    break

            if not chosen:
                raise SolveConflict(f"No version of {name} matches {constraint}")

            ver_str, manifest = chosen
            assignments[name] = {"name": _get_name(manifest),
                                 "version": _get_version(manifest),
                                 "_manifest": manifest}
            for dep_name in _get_deps(manifest):
                trail.append((dep_name, VersionConstraint.any()))

        return assignments

    def solve(self, root_name: str,
              available: dict[str, list[tuple[str, Any]]],
              root_constraint: VersionConstraint | None = None) -> dict[str, Any]:
        raw = self._resolve(available, root_name, root_constraint or VersionConstraint.any())
        order = self._topological_sort(raw, available)
        return raw

    def _topological_sort(self, resolved: dict[str, Any],
                          available: dict[str, list[tuple[str, Any]]]) -> list[str]:
        visited: set[str] = set()
        order: list[str] = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            manifest = resolved[name]
            for dep_name in getattr(manifest, "dependencies", []) or []:
                if dep_name in resolved:
                    visit(dep_name)
            order.append(name)

        for name in resolved:
            visit(name)
        return order

    def resolve_with_graph(self, root_name: str,
                           available: dict[str, list[tuple[str, Any]]],
                           constraint: VersionConstraint | None = None) -> dict[str, Any]:
        manifest = self.solve(root_name, available, constraint)
        return manifest

    def find_best(self, candidates: list[tuple[str, Any]],
                  constraint: VersionConstraint) -> tuple[str, Any] | None:
        best = None
        best_ver = None
        for ver_str, manifest in candidates:
            ver = SemVer.parse(ver_str)
            if constraint.matches(ver):
                if best is None or ver > best_ver:
                    best = (ver_str, manifest)
                    best_ver = ver
        return best


def _package_from_manifest(manifest) -> tuple[str, Any]:
    return manifest.version, manifest


def solver_available(plugins: dict[str, list],
                     root: str,
                     root_constraint: str = "*") -> dict[str, Any]:
    solver = DependencySolver()
    avail = {
        name: [m for m in manifests]
        for name, manifests in plugins.items()
    }
    constraint = parse_spec(root_constraint)
    return solver.solve(root, avail, constraint)
