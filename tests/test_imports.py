"""
Tests d'imports : tous les modules de CIEL s'importent sans erreur.
"""
from __future__ import annotations

import importlib
import sys

import pytest


# Tous les modules du package ciel/
CORE_MODULES = [
    "ciel",
    "ciel.core",
    "ciel.core.axioms",
    "ciel.core.identity",
    "ciel.core.crypto",
    "ciel.core.kernel",
    "ciel.core.observability",
    "ciel.core.observability.metrics",
    "ciel.ethics",
    "ciel.ethics.axioms_guard",
    "ciel.ethics.filter",
    "ciel.ethics.transparency",
    "ciel.ethics.reversibility",
    "ciel.memory",
    "ciel.perception",
    "ciel.analysis",
    "ciel.skills",
    "ciel.noosphere",
    "ciel.animus",
    "ciel.consciousness",
    "ciel.chronos",
    "ciel.logos",
    "ciel.meta",
    "ciel.brain",
    "ciel.swarm",
    "ciel.security",
    "ciel.economy",
    "ciel.quantum",
    "ciel.math",
    "ciel.interfaces",
    "ciel.interfaces.cli",
    "ciel.polyglot",
    "ciel.polyglot.bridge",
]


@pytest.mark.parametrize("module_name", CORE_MODULES)
def test_module_imports(module_name: str) -> None:
    """Chaque module de CIEL doit s'importer sans erreur."""
    importlib.import_module(module_name)


def test_ciel_root_constants() -> None:
    """Le package ciel expose ses constantes."""
    import ciel
    assert ciel.__version__ == "0.1.0"
    assert "Singularité" in ciel.__edition__
    assert "ÉVEIL" in ciel.__phase__
    assert set(ciel.AXIOMS) == {"α", "β", "γ", "δ"}
    assert len(ciel.STRATA) == 12
    assert len(ciel.TRANSVERSES) == 6


def test_strata_ordering_matches_vinfini2() -> None:
    """L'ordre des strates respecte la v∞.2 (1=NOYAU, 12=LOGOS)."""
    import ciel
    assert ciel.STRATA[0] == "noyau"
    assert ciel.STRATA[1] == "éthique"
    assert ciel.STRATA[2] == "immune"
    assert ciel.STRATA[3] == "mémoire"
    assert ciel.STRATA[4] == "œil"
    assert ciel.STRATA[5] == "labyrinthe"
    assert ciel.STRATA[6] == "forgeron"
    assert ciel.STRATA[7] == "noosphère"
    assert ciel.STRATA[8] == "animus"
    assert ciel.STRATA[9] == "conscience"
    assert ciel.STRATA[10] == "chronos"
    assert ciel.STRATA[11] == "logos"


def test_transverses_complete() -> None:
    """Les 6 transverses sont définies."""
    import ciel
    expected = {"brain", "swarm", "security", "economy", "quantum", "math"}
    assert set(ciel.TRANSVERSES) == expected
