from __future__ import annotations

import math
import random
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Basic Emotions (Ekman) ──────────────────────────────────────────────────

class BasicEmotion(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"


BASIC_EMOTION_VECTORS: dict[BasicEmotion, tuple[float, float, float]] = {
    BasicEmotion.JOY: (0.8, 0.7, 0.6),
    BasicEmotion.SADNESS: (-0.6, -0.5, -0.4),
    BasicEmotion.ANGER: (-0.5, 0.8, 0.7),
    BasicEmotion.FEAR: (-0.7, 0.6, -0.3),
    BasicEmotion.SURPRISE: (0.0, 0.9, 0.0),
    BasicEmotion.DISGUST: (-0.4, 0.3, -0.2),
    BasicEmotion.NEUTRAL: (0.0, 0.0, 0.0),
}


# ── PAD Model (Pleasure-Arousal-Dominance) ──────────────────────────────────

@dataclass(slots=True)
class PADState:
    pleasure: float = 0.0   # -1.0 to 1.0
    arousal: float = 0.0    # -1.0 to 1.0
    dominance: float = 0.0  # -1.0 to 1.0

    @staticmethod
    def from_emotion(emotion: BasicEmotion) -> PADState:
        vec = BASIC_EMOTION_VECTORS.get(emotion, (0.0, 0.0, 0.0))
        return PADState(pleasure=vec[0], arousal=vec[1], dominance=vec[2])

    def distance_to(self, other: PADState) -> float:
        d = math.sqrt(
            (self.pleasure - other.pleasure) ** 2 +
            (self.arousal - other.arousal) ** 2 +
            (self.dominance - other.dominance) ** 2
        )
        return math.sqrt(d / 3.0)

    def blend(self, other: PADState, factor: float = 0.5) -> PADState:
        f = max(0.0, min(1.0, factor))
        return PADState(
            pleasure=self.pleasure * (1 - f) + other.pleasure * f,
            arousal=self.arousal * (1 - f) + other.arousal * f,
            dominance=self.dominance * (1 - f) + other.dominance * f,
        )


# ── Emotion Model ───────────────────────────────────────────────────────────

@dataclass(slots=True)
class EmotionalState:
    id: str
    primary: BasicEmotion
    pad: PADState
    intensity: float = 1.0
    decay_rate: float = 0.05
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def decay(self) -> None:
        self.intensity = max(0.0, self.intensity - self.decay_rate)
        if self.intensity <= 0:
            self.primary = BasicEmotion.NEUTRAL
            self.pad = PADState()


class EmotionModel:
    """Modèle émotionnel — émotions discrètes + dimensionnelles (PAD)."""

    def __init__(self, decay_rate: float = 0.05) -> None:
        self._current = EmotionalState(
            id=str(uuid.uuid4()),
            primary=BasicEmotion.NEUTRAL,
            pad=PADState(),
            intensity=0.0,
            decay_rate=decay_rate,
        )
        self._history: list[EmotionalState] = []

    def stimulate(self, emotion: BasicEmotion, intensity: float = 1.0,
                  source: str = "") -> EmotionalState:
        pad = PADState.from_emotion(emotion)
        state = EmotionalState(
            id=str(uuid.uuid4()),
            primary=emotion,
            pad=self._current.pad.blend(pad, intensity),
            intensity=max(0.0, min(1.0, intensity)),
            decay_rate=self._current.decay_rate,
        )
        self._current = state
        self._history.append(state)
        return state

    def tick(self) -> None:
        self._current.decay()

    def current(self) -> EmotionalState:
        return self._current

    def dominant_emotion(self) -> BasicEmotion:
        if self._current.intensity < 0.1:
            return BasicEmotion.NEUTRAL
        return self._current.primary

    def emotional_valence(self) -> float:
        return self._current.pad.pleasure

    def is_positive(self) -> bool:
        return self._current.pad.pleasure > 0.2

    def is_negative(self) -> bool:
        return self._current.pad.pleasure < -0.2

    def is_aroused(self) -> bool:
        return self._current.pad.arousal > 0.3

    def history(self, limit: int = 10) -> list[EmotionalState]:
        return self._history[-limit:]


# ── Personality (Big Five) ─────────────────────────────────────────────────

@dataclass(slots=True)
class BigFive:
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    @staticmethod
    def random() -> BigFive:
        return BigFive(
            openness=random.gauss(0.5, 0.15),
            conscientiousness=random.gauss(0.5, 0.15),
            extraversion=random.gauss(0.5, 0.15),
            agreeableness=random.gauss(0.5, 0.15),
            neuroticism=random.gauss(0.5, 0.15),
        )

    def profile(self) -> dict[str, float]:
        return {
            "openness": max(0.0, min(1.0, self.openness)),
            "conscientiousness": max(0.0, min(1.0, self.conscientiousness)),
            "extraversion": max(0.0, min(1.0, self.extraversion)),
            "agreeableness": max(0.0, min(1.0, self.agreeableness)),
            "neuroticism": max(0.0, min(1.0, self.neuroticism)),
        }


# ── Tone Adapter ────────────────────────────────────────────────────────────

class Tone(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    EMPATHETIC = "empathic"
    CHEERFUL = "cheerful"
    SERIOUS = "serious"
    PLAYFUL = "playful"
    SOOTHING = "soothing"


class ToneAdapter:
    """Adaptation du ton selon l'état émotionnel et la personnalité."""

    def __init__(self, default_tone: Tone = Tone.EMPATHETIC) -> None:
        self.default_tone = default_tone

    def adapt(self, emotion: EmotionalState, personality: BigFive | None = None) -> Tone:
        if emotion.intensity < 0.1:
            return self.default_tone

        pad = emotion.pad
        if pad.pleasure > 0.5 and pad.arousal > 0.3:
            return Tone.CHEERFUL
        if pad.pleasure > 0.3:
            return Tone.PLAYFUL if (personality and personality.extraversion > 0.6) else Tone.CASUAL
        if pad.pleasure < -0.5 and pad.arousal > 0.3:
            return Tone.SOOTHING
        if pad.pleasure < -0.3:
            return Tone.EMPATHETIC
        if pad.arousal > 0.5:
            return Tone.SERIOUS

        if personality:
            if personality.agreeableness > 0.7:
                return Tone.EMPATHETIC
            if personality.conscientiousness > 0.7:
                return Tone.FORMAL
            if personality.extraversion > 0.6:
                return Tone.CASUAL

        return self.default_tone

    def markers(self, tone: Tone) -> list[str]:
        markers_map: dict[Tone, list[str]] = {
            Tone.FORMAL: ["veuillez", "je vous prie", "cordialement"],
            Tone.CASUAL: ["salut", "voilà", "cool"],
            Tone.EMPATHETIC: ["je comprends", "je suis là", "ce doit être difficile"],
            Tone.CHEERFUL: ["super", "génial", "je suis ravi"],
            Tone.SERIOUS: ["important", "attention", "il faut"],
            Tone.PLAYFUL: ["haha", "et si", "imagine"],
            Tone.SOOTHING: ["tout va bien", "respire", "doucement"],
        }
        return markers_map.get(tone, [])


# ── Empathy Engine ──────────────────────────────────────────────────────────

@dataclass(slots=True)
class UserState:
    user_id: str
    inferred_emotion: BasicEmotion = BasicEmotion.NEUTRAL
    confidence: float = 0.0
    engagement: float = 0.5
    satisfaction: float = 0.5
    interaction_count: int = 0
    last_active: float = 0.0

    def __post_init__(self) -> None:
        if self.last_active == 0.0:
            self.last_active = time.time()


class EmpathyEngine:
    """Reconnaissance des états internes utilisateur."""

    def __init__(self) -> None:
        self._users: dict[str, UserState] = {}

    def register_user(self, user_id: str) -> UserState:
        state = UserState(user_id=user_id)
        self._users[user_id] = state
        return state

    def infer(self, user_id: str, signals: dict[str, Any]) -> UserState | None:
        state = self._users.get(user_id)
        if state is None:
            return None

        state.interaction_count += 1
        state.last_active = time.time()

        if "sentiment" in signals:
            sentiment = float(signals["sentiment"])
            if sentiment > 0.3:
                state.inferred_emotion = BasicEmotion.JOY
                state.confidence = min(1.0, abs(sentiment))
            elif sentiment < -0.3:
                state.inferred_emotion = BasicEmotion.SADNESS
                state.confidence = min(1.0, abs(sentiment))
            else:
                state.inferred_emotion = BasicEmotion.NEUTRAL
                state.confidence = 0.3

        if "engagement" in signals:
            state.engagement = max(0.0, min(1.0, float(signals["engagement"])))
        if "satisfaction" in signals:
            state.satisfaction = max(0.0, min(1.0, float(signals["satisfaction"])))

        return state

    def get_user(self, user_id: str) -> UserState | None:
        return self._users.get(user_id)

    def all_users(self) -> list[UserState]:
        return list(self._users.values())


# ── AnimusEngine ────────────────────────────────────────────────────────────

class AnimusEngine:
    """Point d'entrée principal de la Strate 9 — ANIMUS.

    Interface émotionnelle & empathique :
    - EmotionModel: émotions discrètes (Ekman) + PAD dimensionnel
    - BigFive: personnalité (5 facteurs)
    - ToneAdapter: adaptation du ton (7 modes)
    - EmpathyEngine: reconnaissance des états utilisateur
    """

    def __init__(self) -> None:
        self.emotion = EmotionModel()
        self.personality = BigFive.random()
        self.tone = ToneAdapter()
        self.empathy = EmpathyEngine()
        self._interaction_count = 0

    def feel(self, emotion: BasicEmotion, intensity: float = 1.0) -> EmotionalState:
        return self.emotion.stimulate(emotion, intensity)

    def respond_to_user(self, user_id: str, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        self._interaction_count += 1
        self.emotion.tick()

        user = self.empathy.get_user(user_id)
        if user is None:
            user = self.empathy.register_user(user_id)

        if signals:
            self.empathy.infer(user_id, signals)

        tone = self.tone.adapt(self.emotion.current(), self.personality)
        markers = self.tone.markers(tone)

        return {
            "user_id": user_id,
            "my_emotion": self.emotion.dominant_emotion().value,
            "my_valence": self.emotion.emotional_valence(),
            "user_emotion": user.inferred_emotion.value,
            "user_satisfaction": user.satisfaction,
            "user_engagement": user.engagement,
            "tone": tone.value,
            "tone_markers": markers,
            "personality": self.personality.profile(),
        }

    def get_mood(self) -> str:
        emotion = self.emotion.dominant_emotion()
        if emotion == BasicEmotion.NEUTRAL:
            return "calme"
        if self.emotion.is_positive():
            return "positif" if not self.emotion.is_aroused() else "exalté"
        if self.emotion.is_negative():
            return "triste" if not self.emotion.is_aroused() else "tendu"
        return "neutre"

    def get_stats(self) -> dict[str, Any]:
        return {
            "current_emotion": self.emotion.dominant_emotion().value,
            "valence": self.emotion.emotional_valence(),
            "arousal": self.emotion.current().pad.arousal,
            "mood": self.get_mood(),
            "personality": self.personality.profile(),
            "users_tracked": len(self.empathy.all_users()),
            "interactions": self._interaction_count,
            "emotional_history": len(self.emotion.history()),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "respond")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "feel":
            emo_name = data.get("emotion", "neutral")
            try:
                emo = BasicEmotion(emo_name)
            except ValueError:
                return {"success": False, "error": f"unknown emotion: {emo_name}"}
            state = self.feel(emo, float(data.get("intensity", 1.0)))
            return {"success": True, "action": "feel", "state": state}
        elif action == "respond":
            result = self.respond_to_user(
                data.get("user_id", "anonymous"),
                data.get("signals"),
            )
            return {"success": True, "action": "respond", "result": result}
        elif action == "mood":
            return {"success": True, "action": "mood", "mood": self.get_mood()}
        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
