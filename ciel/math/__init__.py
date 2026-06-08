"""
Transverse — MATH : Mathématiques des Profondeurs.

Composants :
  - category_theory      : Catégories, foncteurs, transformations
  - hott                 : Homotopy Type Theory (types = espaces)
  - information_geometry : métrique de Fisher-Rao
  - topology             : homologie persistante, Betti, TDA
  - clifford             : algèbre géométrique Cl(3,0)
  - optimal_transport    : Wasserstein 1D/2D, Sinkhorn
"""
from __future__ import annotations

from ciel.math.core import (
    Category, Functor, NaturalTransformation,
    Simplex, SimplicialComplex, PersistentHomology,
    CliffordAlgebra, OptimalTransport, FisherMetric, HoTT,
    MathEngine,
)
__all__ = [
    "Category", "Functor", "NaturalTransformation",
    "Simplex", "SimplicialComplex", "PersistentHomology",
    "CliffordAlgebra", "OptimalTransport", "FisherMetric", "HoTT",
    "MathEngine",
]
