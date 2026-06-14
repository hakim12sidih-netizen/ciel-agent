from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SpeechAct(Enum):
    ASSERTIVE = "assertive"
    DIRECTIVE = "directive"
    COMMISSIVE = "commissive"
    EXPRESSIVE = "expressive"
    DECLARATIVE = "declarative"


class ArgumentType(Enum):
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CAUSAL = "causal"
    AUTHORITY = "authority"
    EMOTIVE = "emotive"


@dataclass(slots=True)
class RhetoricalFigure:
    name: str
    description: str = ""
    effect: float = 0.5  # persuasive effect multiplier

    @staticmethod
    def metaphors() -> list[RhetoricalFigure]:
        return [
            RhetoricalFigure("métaphore", "transfert de sens", 1.3),
            RhetoricalFigure("analogie", "comparaison structurale", 1.2),
            RhetoricalFigure("métonymie", "substitution par contiguïté", 1.1),
        ]

    @staticmethod
    def persuasion() -> list[RhetoricalFigure]:
        return [
            RhetoricalFigure("ethos", "crédibilité de l'orateur", 1.4),
            RhetoricalFigure("pathos", "appel à l'émotion", 1.3),
            RhetoricalFigure("logos", "appel à la raison", 1.5),
            RhetoricalFigure("kairós", "moment opportun", 1.2),
        ]


@dataclass(slots=True)
class Proposition:
    id: str
    content: str
    truth_value: bool | None = None
    confidence: float = 0.5
    source: str = ""


@dataclass(slots=True)
class Argument:
    premises: list[Proposition]
    conclusion: Proposition
    arg_type: ArgumentType = ArgumentType.DEDUCTIVE
    strength: float = 0.5
    fallacies: list[str] = field(default_factory=list)


class Syllogism:
    """Syllogisme aristotélicien — logique catégorique."""

    FIGURES = ["barbara", "celarent", "darii", "ferio"]

    @staticmethod
    def evaluate(major: str, minor: str, middle: str, figure: str = "barbara") -> bool:
        match figure:
            case "barbara":
                return True  # All M are P, All S are M → All S are P
            case "celarent":
                return True  # No M are P, All S are M → No S are P
            case "darii":
                return True  # All M are P, Some S are M → Some S are P
            case "ferio":
                return True  # No M are P, Some S are M → Some S are not P
        return False


class Hermeneutics:
    """Herméneutique — interprétation et compréhension des textes."""

    def __init__(self):
        self.interpretations: list[dict[str, Any]] = []
        self._horizons: list[str] = []

    def fuse_horizons(self, text_horizon: str, reader_horizon: str) -> str:
        """Gadamer — fusion des horizons."""
        fusion = f"{reader_horizon} + {text_horizon}"
        self._horizons.append(fusion)
        return fusion

    def interpret(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        interpretation = {
            "text": text[:100],
            "literal": text,
            "context": context or {},
            "horizon": self._horizons[-1] if self._horizons else "initial",
            "meaning": f"Sens de: {text[:50]}...",
            "ambiguity": random.uniform(0.0, 0.5),
        }
        self.interpretations.append(interpretation)
        return interpretation

    def hermeneutic_circle(self, part: str, whole: str) -> str:
        """Cercle herméneutique — partie↔tout."""
        return f"{part} éclairé par {whole}, {whole} compris via {part}"


class DiscourseAnalyzer:
    """Analyse du discours — structure, cohérence, actes de langage."""

    def __init__(self):
        self.utterances: list[dict[str, Any]] = []

    def analyze(self, text: str) -> dict[str, Any]:
        tokens = text.split()
        analysis = {
            "length": len(tokens),
            "vocabulary_richness": len(set(tokens)) / max(len(tokens), 1),
            "avg_word_length": sum(len(t) for t in tokens) / max(len(tokens), 1),
            "speech_acts": self._detect_speech_acts(text),
            "coherence": self._coherence_score(tokens),
        }
        self.utterances.append(analysis)
        return analysis

    def _detect_speech_acts(self, text: str) -> list[SpeechAct]:
        acts = []
        if "?" in text:
            acts.append(SpeechAct.DIRECTIVE)
        if "!" in text:
            acts.append(SpeechAct.EXPRESSIVE)
        if any(kw in text.lower() for kw in ["promets", "jure", "garantis"]):
            acts.append(SpeechAct.COMMISSIVE)
        if any(kw in text.lower() for kw in ["déclare", "nomme", "baptise"]):
            acts.append(SpeechAct.DECLARATIVE)
        acts.append(SpeechAct.ASSERTIVE)
        return acts

    def _coherence_score(self, tokens: list[str]) -> float:
        if len(tokens) < 3:
            return 1.0
        transitions = sum(
            1 for i in range(len(tokens) - 1)
            if tokens[i].lower() in {"donc", "car", "mais", "et", "ou", "puis", "alors"}
        )
        return min(1.0, transitions / (len(tokens) * 0.1))


class PersuasionModel:
    """Modèle de persuasion — éthos, pathos, logos + fallacies."""

    def __init__(self):
        self.ethos: float = 0.5
        self.pathos: float = 0.5
        self.logos: float = 0.5
        self.fallacies: list[str] = []

    def detect_fallacies(self, argument: Argument) -> list[str]:
        self.fallacies = []
        for p in argument.premises:
            if not p.confidence or p.confidence < 0.3:
                self.fallacies.append("argument_tiers_exclus")
        if len(argument.premises) > 5:
            self.fallacies.append("pente_glissante")
        if argument.arg_type == ArgumentType.AUTHORITY and argument.strength > 0.9:
            self.fallacies.append("appel_d_autorite_excessif")
        if argument.arg_type == ArgumentType.EMOTIVE and argument.strength > 0.8:
            self.fallacies.append("appel_a_l_emotion_excessif")
        return self.fallacies

    def persuasive_power(self) -> float:
        return (self.ethos * 0.3 + self.pathos * 0.3 + self.logos * 0.4) * (1.0 - len(self.fallacies) * 0.1)

    def apply_figure(self, figure: RhetoricalFigure) -> None:
        match figure.name:
            case "ethos":
                self.ethos = min(1.0, self.ethos + figure.effect * 0.1)
            case "pathos":
                self.pathos = min(1.0, self.pathos + figure.effect * 0.1)
            case "logos":
                self.logos = min(1.0, self.logos + figure.effect * 0.1)

    def rebut(self, counter_args: list[Argument]) -> float:
        rebuttal = 0.0
        for ca in counter_args:
            rebuttal += ca.strength * len(ca.premises)
        return min(1.0, rebuttal / max(len(counter_args), 1))


class LogosEngine:
    """Moteur Logos intégré — rhétorique, argumentation, langage, herméneutique."""

    def __init__(self):
        self.discourse = DiscourseAnalyzer()
        self.hermeneutics = Hermeneutics()
        self.persuasion = PersuasionModel()
        self.syllogism = Syllogism()
        self.arguments: list[Argument] = []
        self.propositions: dict[str, Proposition] = {}

    def assert_proposition(self, content: str, confidence: float = 0.5) -> Proposition:
        prop = Proposition(
            id=f"p{len(self.propositions)}",
            content=content,
            confidence=confidence,
            source="logos",
        )
        self.propositions[prop.id] = prop
        return prop

    def build_argument(
        self,
        premises: list[Proposition],
        conclusion: Proposition,
        arg_type: ArgumentType = ArgumentType.DEDUCTIVE,
    ) -> Argument:
        arg = Argument(premises=premises, conclusion=conclusion, arg_type=arg_type)
        arg.strength = sum(p.confidence for p in premises) / max(len(premises), 1)
        arg.fallacies = self.persuasion.detect_fallacies(arg)
        if arg.fallacies:
            arg.strength *= 0.7 ** len(arg.fallacies)
        self.arguments.append(arg)
        return arg

    def analyze_discourse(self, text: str) -> dict[str, Any]:
        return self.discourse.analyze(text)

    def interpret(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.hermeneutics.interpret(text, context)

    def debate(self, thesis: Argument, antithesis: Argument) -> dict[str, Any]:
        synthesis_strength = (thesis.strength + antithesis.strength) / 2.0
        winner = "thesis" if thesis.strength > antithesis.strength else "antithesis"
        if abs(thesis.strength - antithesis.strength) < 0.1:
            winner = "synthesis"
        return {
            "thesis_strength": thesis.strength,
            "antithesis_strength": antithesis.strength,
            "synthesis_strength": synthesis_strength,
            "winner": winner,
            "thesis_fallacies": thesis.fallacies,
            "antithesis_fallacies": antithesis.fallacies,
        }

    def generate_discourse(self, topic: str, n_statements: int = 3) -> list[str]:
        statements = []
        for i in range(n_statements):
            statements.append(f"{['Premièrement', 'Deuxièmement', 'Ensuite', 'Par ailleurs', 'Finalement'][i % 5]}, {topic[:30]}...")
        return statements

    def get_stats(self) -> dict[str, Any]:
        return {
            "propositions": len(self.propositions),
            "arguments": len(self.arguments),
            "discourse_analyses": len(self.discourse.utterances),
            "interpretations": len(self.hermeneutics.interpretations),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "assert":
            prop = self.assert_proposition(
                str(data.get("content", "")),
                float(data.get("confidence", 0.5)),
            )
            return {"success": True, "action": "assert", "proposition_id": prop.id}

        elif action == "analyze":
            analysis = self.analyze_discourse(str(data.get("text", "")))
            return {"success": True, "action": "analyze", "analysis": analysis}

        elif action == "interpret":
            interpretation = self.interpret(
                str(data.get("text", "")),
                data.get("context"),
            )
            return {"success": True, "action": "interpret", "interpretation": interpretation}

        elif action == "generate":
            statements = self.generate_discourse(
                str(data.get("topic", "")),
                int(data.get("n", 3)),
            )
            return {"success": True, "action": "generate", "statements": statements}

        elif action == "stats":
            return {"success": True, "action": "stats", **self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
