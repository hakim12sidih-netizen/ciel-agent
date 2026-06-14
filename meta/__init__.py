"""
Strate 12+ — META : Méta-Architecture. CIEL se reconstruit elle-même.

Composants :
  - self_reflection : auto-évaluation sur 10 métriques
  - evolution       : planification évolutionnaire (Lamarck/Darwin/Baldwin)
  - quine           : auto-reproduction (sérialisation + vérification)
  - compiler        : déploiement bleu-vert

Lamarckien + Darwinien + Baldwinien :
  - Lamarck : les acquis pendant l'exécution SONT transmis
  - Darwin  : sélection naturelle entre versions
  - Baldwin : la plasticité individuelle influence la sélection
"""
from __future__ import annotations

from ciel.meta.core import (
    MetricDimension,
    MetricSnapshot,
    ReflectionReport,
    SelfReflection,
    QuineManifest,
    Quine,
    EvolutionStrategy,
    EvolutionPlan,
    EvolutionPlanner,
    DeploymentState,
    Deployment,
    Compiler,
    MetaEngine,
)

__all__ = [
    "MetricDimension",
    "MetricSnapshot",
    "ReflectionReport",
    "SelfReflection",
    "QuineManifest",
    "Quine",
    "EvolutionStrategy",
    "EvolutionPlan",
    "EvolutionPlanner",
    "DeploymentState",
    "Deployment",
    "Compiler",
    "MetaEngine",
]
