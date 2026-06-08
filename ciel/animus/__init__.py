"""
Strate 9 — ANIMUS : Interface Émotionnelle & Empathique.

Modélise :
  - emotion_model  : émotions discrètes (Ekman) + PAD (Pleasure-Arousal-Dominance)
  - empathy        : reconnaissance des états internes utilisateur
  - personality    : Big Five, modèles mentaux utilisateur
  - tone_adapter   : adaptation du ton (7 modes : formal, casual, empathic, ...)

Inspiré de :
  - Modèle Circumplex de Russell
  - PAD (Pleasure-Arousal-Dominance)
  - Plutchik's Wheel of Emotions
  - Ekman's 6 basic emotions
"""
from __future__ import annotations

from ciel.animus.core import (
    BasicEmotion,
    PADState,
    EmotionalState,
    EmotionModel,
    BigFive,
    Tone,
    ToneAdapter,
    UserState,
    EmpathyEngine,
    AnimusEngine,
)

__all__ = [
    "BasicEmotion",
    "PADState",
    "EmotionalState",
    "EmotionModel",
    "BigFive",
    "Tone",
    "ToneAdapter",
    "UserState",
    "EmpathyEngine",
    "AnimusEngine",
]
