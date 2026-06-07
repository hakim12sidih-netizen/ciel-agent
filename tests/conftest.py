"""
Fixtures pytest pour CIEL v∞.2.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture
def tmp_ciel_root() -> Iterator[Path]:
    """Crée un répertoire temporaire CIEL avec data/ et identity/."""
    tmp = Path(tempfile.mkdtemp(prefix="ciel_test_"))
    (tmp / "data" / "identity").mkdir(parents=True)
    (tmp / "data" / "snapshots").mkdir(parents=True)
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def identity_dir(tmp_ciel_root: Path) -> Path:
    """Chemin vers le répertoire d'identité temporaire."""
    return tmp_ciel_root / "data" / "identity"


@pytest.fixture
def snapshots_dir(tmp_ciel_root: Path) -> Path:
    """Chemin vers le répertoire de snapshots temporaire."""
    return tmp_ciel_root / "data" / "snapshots"
