from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AnalysisMode(Enum):
    DESCRIPTIF = "descriptif"
    DIAGNOSTIQUE = "diagnostique"
    PREDICTIF = "prédictif"
    PRESCRIPTIF = "prescriptif"
    EXPLORATOIRE = "exploratoire"
    CONTREFACTUEL = "contrefactuel"
    META = "méta"


class AnalysisDimension(Enum):
    TEMPORELLE = "temporelle"
    SPATIALE = "spatiale"
    CAUSALE = "causale"
    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    SYSTEMIQUE = "systémique"


class Paradigm(Enum):
    DEDUCTIF = "déductif"
    INDUCTIF = "inductif"
    ABDUCTIF = "abductif"
    ANALOGIQUE = "analogique"
    STATISTIQUE = "statistique"
    BAYESIEN = "bayésien"


@dataclass(slots=True)
class AnalysisContext:
    data: dict[str, Any] = field(default_factory=dict)
    dimensions: list[AnalysisDimension] = field(default_factory=lambda: list(AnalysisDimension))
    paradigms: list[Paradigm] = field(default_factory=lambda: [Paradigm.DEDUCTIF, Paradigm.STATISTIQUE])
    temporal_window: tuple[float, float] | None = None
    spatial_boundary: dict[str, float] | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    hypothesis: str | None = None

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value


@dataclass(slots=True)
class AnalysisResult:
    mode: AnalysisMode
    conclusion: str
    confidence: float
    dimensions_used: list[AnalysisDimension] = field(default_factory=list)
    paradigms_used: list[Paradigm] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    def is_reliable(self, threshold: float = 0.7) -> bool:
        return self.confidence >= threshold


class BaseAnalyzer:
    def analyze(self, ctx: AnalysisContext) -> AnalysisResult: ...


class DescriptiveAnalyzer(BaseAnalyzer):
    """Analyse descriptive : 'Que s'est-il passé ?'"""

    def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
        evidence = []
        observations = []

        for key, val in ctx.data.items():
            evidence.append(f"{key}={val}")
            observations.append(f"observation: {key} → {val}")

        if ctx.temporal_window:
            evidence.append(f"période: [{ctx.temporal_window[0]}, {ctx.temporal_window[1]}]")

        summary = "; ".join(observations) if observations else "aucune donnée"
        confidence = min(1.0, len(evidence) * 0.15)

        return AnalysisResult(
            mode=AnalysisMode.DESCRIPTIF,
            conclusion=f"État observé : {summary}",
            confidence=confidence,
            dimensions_used=[d for d in ctx.dimensions if d in (AnalysisDimension.TEMPORELLE, AnalysisDimension.QUANTITATIVE, AnalysisDimension.QUALITATIVE)],
            paradigms_used=[p for p in ctx.paradigms if p in (Paradigm.DEDUCTIF, Paradigm.STATISTIQUE)],
            evidence=evidence,
            metrics={"n_observations": float(len(observations)), "data_volume": float(len(ctx.data))},
        )


class DiagnosticAnalyzer(BaseAnalyzer):
    """Analyse diagnostique : 'Pourquoi ?'"""

    def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
        evidence: list[str] = []
        causal_links: list[str] = []

        keys = list(ctx.data.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                v_i = ctx.data.get(keys[i])
                v_j = ctx.data.get(keys[j])
                if isinstance(v_i, (int, float)) and isinstance(v_j, (int, float)) and v_i != 0 and v_j != 0:
                    ratio = v_i / v_j if v_j != 0 else 0
                    if abs(ratio) > 0.1:
                        causal_links.append(f"{keys[i]} → {keys[j]} (ratio={ratio:.2f})")

        evidence.extend(causal_links)
        root_causes = causal_links[:3] if causal_links else ["cause non identifiée"]
        confidence = min(1.0, len(causal_links) * 0.2) if causal_links else 0.1

        return AnalysisResult(
            mode=AnalysisMode.DIAGNOSTIQUE,
            conclusion=f"Causes racines : {'; '.join(root_causes)}",
            confidence=confidence,
            dimensions_used=[d for d in ctx.dimensions if d in (AnalysisDimension.CAUSALE, AnalysisDimension.SYSTEMIQUE, AnalysisDimension.TEMPORELLE)],
            paradigms_used=[p for p in ctx.paradigms if p in (Paradigm.ABDUCTIF, Paradigm.INDUCTIF, Paradigm.STATISTIQUE)],
            evidence=evidence,
            metrics={"causal_links": float(len(causal_links)), "root_causes": float(len(root_causes))},
        )


class PredictiveAnalyzer(BaseAnalyzer):
    """Analyse prédictive : 'Que va-t-il se passer ?'"""

    def __init__(self, horizon: float = 1.0):
        self.horizon = horizon

    def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
        evidence: list[str] = []
        projections: list[str] = []

        numerical = {k: v for k, v in ctx.data.items() if isinstance(v, (int, float))}
        for key, val in numerical.items():
            trend = val * (1 + random.gauss(0, 0.1) * self.horizon)
            projections.append(f"{key}: {val:.2f} → {trend:.2f} (horizon={self.horizon})")
            evidence.append(f"projection {key}={trend:.2f}")

        n = len(projections)
        summary = "; ".join(projections) if projections else "aucune tendance détectée"
        confidence = min(1.0, n * 0.2)

        return AnalysisResult(
            mode=AnalysisMode.PREDICTIF,
            conclusion=f"Projections (t={self.horizon}) : {summary}",
            confidence=confidence,
            dimensions_used=[d for d in ctx.dimensions if d in (AnalysisDimension.TEMPORELLE, AnalysisDimension.QUANTITATIVE)],
            paradigms_used=[p for p in ctx.paradigms if p in (Paradigm.INDUCTIF, Paradigm.STATISTIQUE, Paradigm.BAYESIEN)],
            evidence=evidence,
            metrics={"n_projections": float(n), "horizon": self.horizon},
        )


class PrescriptiveAnalyzer(BaseAnalyzer):
    """Analyse prescriptive : 'Que devrais-je faire ?'"""

    def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
        evidence: list[str] = []
        recommendations: list[str] = []

        for key, val in ctx.data.items():
            if isinstance(val, (int, float)):
                if val < 0:
                    recommendations.append(f"augmenter {key} (actuel={val})")
                    evidence.append(f"{key} sous le seuil")
                elif val > 100:
                    recommendations.append(f"réduire {key} (actuel={val})")
                    evidence.append(f"{key} au-dessus du seuil")
                else:
                    recommendations.append(f"maintenir {key} (actuel={val})")
                    evidence.append(f"{key} dans la norme")
            else:
                recommendations.append(f"surveiller {key}={val}")

        alternatives = [f"alternative: {r}" for r in recommendations]
        confidence = min(1.0, len(recommendations) * 0.15)

        return AnalysisResult(
            mode=AnalysisMode.PRESCRIPTIF,
            conclusion=f"Recommandations : {'; '.join(recommendations[:3])}",
            confidence=confidence,
            dimensions_used=[d for d in ctx.dimensions if d in (AnalysisDimension.QUALITATIVE, AnalysisDimension.SYSTEMIQUE)],
            paradigms_used=[p for p in ctx.paradigms if p in (Paradigm.DEDUCTIF, Paradigm.ANALOGIQUE)],
            evidence=evidence,
            recommendations=recommendations,
            alternatives=alternatives,
            metrics={"n_recommendations": float(len(recommendations))},
        )


class ExploratoryAnalyzer(BaseAnalyzer):
    """Analyse exploratoire : 'Que se passerait-il SI ?'"""

    def __init__(self, n_scenarios: int = 3):
        self.n_scenarios = n_scenarios

    def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
        evidence: list[str] = []
        scenarios: list[str] = []

        numerical = {k: v for k, v in ctx.data.items() if isinstance(v, (int, float))}
        for i in range(self.n_scenarios):
            delta = random.uniform(-0.5, 0.5)
            perturbations = {k: v * (1 + delta) for k, v in numerical.items()}
            scenario_parts = [f"{k}: {v:.2f}→{perturbations[k]:.2f}" for k, v in numerical.items()]
            scenario_label = f"scénario S{i + 1} (δ={delta:+.2f}) : {'; '.join(scenario_parts)}"
            scenarios.append(scenario_label)
            evidence.append(f"S{i + 1}: perturbations={perturbations}")

        confidence = min(1.0, self.n_scenarios * 0.15)

        return AnalysisResult(
            mode=AnalysisMode.EXPLORATOIRE,
            conclusion=f"Scénarios explorés ({self.n_scenarios}) : {'; '.join(scenarios)}",
            confidence=confidence,
            dimensions_used=[d for d in ctx.dimensions if d in (AnalysisDimension.TEMPORELLE, AnalysisDimension.CAUSALE, AnalysisDimension.QUANTITATIVE)],
            paradigms_used=[p for p in ctx.paradigms if p in (Paradigm.ABDUCTIF, Paradigm.STATISTIQUE)],
            evidence=evidence,
            alternatives=scenarios,
            metrics={"n_scenarios": float(self.n_scenarios)},
        )


class CounterfactualAnalyzer(BaseAnalyzer):
    """Analyse contrefactuelle : 'Qu'aurai-je dû faire ?'"""

    def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
        evidence: list[str] = []
        counterfactuals: list[str] = []

        for key, val in ctx.data.items():
            if isinstance(val, (int, float)):
                inverted = -val
                counterfactuals.append(f"si {key} était {inverted:.2f} au lieu de {val:.2f}")
                evidence.append(f"contrefactuel {key}: {val} → {inverted}")
            elif isinstance(val, bool):
                flipped = not val
                counterfactuals.append(f"si {key} était {flipped} au lieu de {val}")
                evidence.append(f"contrefactuel {key}: {val} → {flipped}")

        if not counterfactuals:
            counterfactuals.append("aucune variable contrefactuelle")
            evidence.append("pas de variables modifiables")

        confidence = min(1.0, len(counterfactuals) * 0.15)

        return AnalysisResult(
            mode=AnalysisMode.CONTREFACTUEL,
            conclusion=f"Contrefactuels : {'; '.join(counterfactuals[:3])}",
            confidence=confidence,
            dimensions_used=[d for d in ctx.dimensions if d in (AnalysisDimension.CAUSALE, AnalysisDimension.TEMPORELLE)],
            paradigms_used=[p for p in ctx.paradigms if p in (Paradigm.ABDUCTIF, Paradigm.DEDUCTIF)],
            evidence=evidence,
            alternatives=counterfactuals,
            metrics={"n_counterfactuals": float(len(counterfactuals))},
        )


class MetaAnalyzer(BaseAnalyzer):
    """Méta-analyse : 'Comment ai-je décidé ?' — introspection du processus d'analyse."""

    def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
        evidence: list[str] = [
            f"dimensions: {[d.value for d in ctx.dimensions]}",
            f"paradigmes: {[p.value for p in ctx.paradigms]}",
            f"taille données: {len(ctx.data)} variables",
        ]
        if ctx.temporal_window:
            evidence.append(f"fenêtre temporelle: {ctx.temporal_window}")

        meta_conclusion = (
            f"Processus d'analyse multi-paradigme avec {len(ctx.dimensions)} dimensions "
            f"et {len(ctx.paradigms)} paradigmes sur {len(ctx.data)} variables"
        )
        confidence = 0.95

        return AnalysisResult(
            mode=AnalysisMode.META,
            conclusion=meta_conclusion,
            confidence=confidence,
            dimensions_used=list(ctx.dimensions),
            paradigms_used=list(ctx.paradigms),
            evidence=evidence,
            metrics={
                "n_dimensions": float(len(ctx.dimensions)),
                "n_paradigms": float(len(ctx.paradigms)),
                "n_variables": float(len(ctx.data)),
            },
        )


class AnalysisEngine:
    """Moteur d'analyse multi-mode, multi-dimension, multi-paradigme."""

    def __init__(self) -> None:
        self._analyzers: dict[AnalysisMode, BaseAnalyzer] = {
            AnalysisMode.DESCRIPTIF: DescriptiveAnalyzer(),
            AnalysisMode.DIAGNOSTIQUE: DiagnosticAnalyzer(),
            AnalysisMode.PREDICTIF: PredictiveAnalyzer(),
            AnalysisMode.PRESCRIPTIF: PrescriptiveAnalyzer(),
            AnalysisMode.EXPLORATOIRE: ExploratoryAnalyzer(),
            AnalysisMode.CONTREFACTUEL: CounterfactualAnalyzer(),
            AnalysisMode.META: MetaAnalyzer(),
        }
        self._history: list[AnalysisResult] = []
        self._custom_analyzers: dict[str, Callable[[AnalysisContext], AnalysisResult]] = {}

    def register_custom(self, name: str, analyzer: Callable[[AnalysisContext], AnalysisResult]) -> None:
        self._custom_analyzers[name] = analyzer

    def analyze(self, ctx: AnalysisContext, modes: list[AnalysisMode] | None = None) -> list[AnalysisResult]:
        modes = modes or list(AnalysisMode)
        results: list[AnalysisResult] = []

        for mode in modes:
            analyzer = self._analyzers.get(mode)
            if analyzer is not None:
                result = analyzer.analyze(ctx)
                results.append(result)

        self._history.extend(results)
        return results

    def analyze_all(self, ctx: AnalysisContext) -> dict[AnalysisMode, AnalysisResult]:
        results = self.analyze(ctx)
        return {r.mode: r for r in results}

    def synthesize(self, results: list[AnalysisResult]) -> AnalysisResult:
        if not results:
            return AnalysisResult(
                mode=AnalysisMode.DESCRIPTIF,
                conclusion="aucune analyse disponible",
                confidence=0.0,
            )

        best = max(results, key=lambda r: r.confidence)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        all_evidence: list[str] = []
        all_recommendations: list[str] = []
        for r in results:
            all_evidence.extend(r.evidence)
            all_recommendations.extend(r.recommendations)

        used_dimensions = list({d for r in results for d in r.dimensions_used})
        used_paradigms = list({p for r in results for p in r.paradigms_used})

        return AnalysisResult(
            mode=AnalysisMode.META,
            conclusion=f"Synthèse multi-mode ({len(results)} analyses). "
                       f"Meilleur score: {best.mode.value} ({best.confidence:.2f}). "
                       f"Confiance moyenne: {avg_confidence:.2f}",
            confidence=avg_confidence,
            dimensions_used=used_dimensions,
            paradigms_used=used_paradigms,
            evidence=all_evidence,
            recommendations=all_recommendations,
            metrics={f"{r.mode.value}_confidence": r.confidence for r in results},
        )

    def get_history(self) -> list[AnalysisResult]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            ctx = AnalysisContext(data=input_data)
        elif isinstance(input_data, AnalysisContext):
            ctx = input_data
        else:
            ctx = AnalysisContext(data={"value": input_data})

        results = self.analyze(ctx)
        synthesis = self.synthesize(results)
        return {
            "results": results,
            "synthesis": synthesis,
            "n_modes": len(results),
        }


class LabyrinthEngine:
    """Point d'entrée principal de la Strate 6 — LABYRINTHE.

    Orchestre l'analyse multi-paradigme complète avec :
    - 7 modes d'analyse
    - 6 dimensions
    - 6 paradigmes
    - Synthèse et historique
    """

    def __init__(self) -> None:
        self.engine = AnalysisEngine()

    def analyze(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        ctx = AnalysisContext(data=data, **kwargs)
        return self.engine.process(ctx)

    def quick(self, data: dict[str, Any]) -> dict[str, Any]:
        ctx = AnalysisContext(data=data, dimensions=[AnalysisDimension.QUANTITATIVE, AnalysisDimension.CAUSALE])
        return self.engine.process(ctx)

    def deep(self, data: dict[str, Any]) -> dict[str, Any]:
        ctx = AnalysisContext(data=data)
        return self.engine.process(ctx)
