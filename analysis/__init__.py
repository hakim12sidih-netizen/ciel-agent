"""
Strate 6 — LABYRINTHE : Moteur d'Analyse Multi-Paradigme.

7 modes d'analyse :
  - descriptif : "Que s'est-il passé ?"
  - diagnostique: "Pourquoi ?"
  - prédictif  : "Que va-t-il se passer ?"
  - prescriptif: "Que devrais-je faire ?"
  - exploratoire: "Que se passerait-il SI ?"
  - contrefactuel: "Qu'aurai-je dû faire ?"
  - méta       : "Comment ai-je décidé ?"

6 dimensions d'analyse :
  - temporelle, spatiale, causale, quantitative, qualitative, systémique

Paradigmes :
  - déductif, inductif, abductif, analogique, statistique, bayésien
"""
from __future__ import annotations

from ciel.analysis.core import (
    AnalysisMode,
    AnalysisDimension,
    Paradigm,
    AnalysisContext,
    AnalysisResult,
    AnalysisEngine,
    LabyrinthEngine,
    BaseAnalyzer,
    DescriptiveAnalyzer,
    DiagnosticAnalyzer,
    PredictiveAnalyzer,
    PrescriptiveAnalyzer,
    ExploratoryAnalyzer,
    CounterfactualAnalyzer,
    MetaAnalyzer,
)

__all__ = [
    "AnalysisMode",
    "AnalysisDimension",
    "Paradigm",
    "AnalysisContext",
    "AnalysisResult",
    "AnalysisEngine",
    "LabyrinthEngine",
    "BaseAnalyzer",
    "DescriptiveAnalyzer",
    "DiagnosticAnalyzer",
    "PredictiveAnalyzer",
    "PrescriptiveAnalyzer",
    "ExploratoryAnalyzer",
    "CounterfactualAnalyzer",
    "MetaAnalyzer",
]
