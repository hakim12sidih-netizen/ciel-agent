from __future__ import annotations

import pytest
from ciel.animus.core import (
    BasicEmotion, PADState, EmotionalState, EmotionModel,
    BigFive, Tone, ToneAdapter, UserState, EmpathyEngine, AnimusEngine,
)


class TestBasicEmotion:
    def test_values(self):
        assert len(BasicEmotion) == 7
        assert BasicEmotion.JOY.value == "joy"
        assert BasicEmotion.NEUTRAL.value == "neutral"


class TestPADState:
    def test_from_emotion(self):
        pad = PADState.from_emotion(BasicEmotion.JOY)
        assert pad.pleasure > 0
        assert pad.arousal > 0

    def test_from_neutral(self):
        pad = PADState.from_emotion(BasicEmotion.NEUTRAL)
        assert pad.pleasure == 0.0
        assert pad.arousal == 0.0

    def test_distance(self):
        a = PADState(1.0, 0.0, 0.0)
        b = PADState(0.0, 0.0, 0.0)
        assert a.distance_to(b) > 0
        assert a.distance_to(a) == 0.0

    def test_blend(self):
        a = PADState(1.0, 0.0, 0.0)
        b = PADState(0.0, 1.0, 0.0)
        blended = a.blend(b, 0.5)
        assert blended.pleasure == 0.5
        assert blended.arousal == 0.5


class TestEmotionModel:
    def test_initial_neutral(self):
        m = EmotionModel()
        assert m.current().primary == BasicEmotion.NEUTRAL

    def test_stimulate(self):
        m = EmotionModel()
        state = m.stimulate(BasicEmotion.JOY, 0.8)
        assert state.primary == BasicEmotion.JOY
        assert state.intensity == 0.8

    def test_tick_decay(self):
        m = EmotionModel()
        m.stimulate(BasicEmotion.JOY, 1.0)
        assert m.current().intensity == 1.0
        m.tick()
        assert m.current().intensity < 1.0

    def test_dominant_emotion(self):
        m = EmotionModel()
        assert m.dominant_emotion() == BasicEmotion.NEUTRAL
        m.stimulate(BasicEmotion.ANGER, 0.9)
        assert m.dominant_emotion() == BasicEmotion.ANGER

    def test_valence(self):
        m = EmotionModel()
        m.stimulate(BasicEmotion.JOY, 1.0)
        assert m.emotional_valence() > 0
        m.stimulate(BasicEmotion.SADNESS, 1.0)
        assert m.emotional_valence() < 0

    def test_is_positive(self):
        m = EmotionModel()
        m.stimulate(BasicEmotion.JOY)
        assert m.is_positive() is True
        assert m.is_negative() is False

    def test_is_aroused(self):
        m = EmotionModel()
        m.stimulate(BasicEmotion.SURPRISE, 1.0)
        assert m.is_aroused() is True

    def test_history(self):
        m = EmotionModel()
        m.stimulate(BasicEmotion.JOY)
        m.stimulate(BasicEmotion.SADNESS)
        assert len(m.history()) == 2


class TestBigFive:
    def test_defaults(self):
        bf = BigFive()
        assert bf.openness == 0.5
        assert bf.conscientiousness == 0.5

    def test_random(self):
        bf = BigFive.random()
        assert 0 <= bf.openness <= 1
        assert 0 <= bf.extraversion <= 1

    def test_profile(self):
        bf = BigFive(openness=0.8, conscientiousness=0.9)
        p = bf.profile()
        assert p["openness"] == 0.8
        assert p["conscientiousness"] == 0.9


class TestToneAdapter:
    def test_default_tone(self):
        ta = ToneAdapter()
        neutral = EmotionalState(id="1", primary=BasicEmotion.NEUTRAL, pad=PADState(), intensity=0.0)
        assert ta.adapt(neutral) == Tone.EMPATHETIC

    def test_cheerful(self):
        ta = ToneAdapter()
        joyful = EmotionalState(id="1", primary=BasicEmotion.JOY, pad=PADState(0.8, 0.7, 0.6), intensity=1.0)
        assert ta.adapt(joyful) == Tone.CHEERFUL

    def test_soothing(self):
        ta = ToneAdapter()
        fearful = EmotionalState(id="1", primary=BasicEmotion.FEAR, pad=PADState(-0.7, 0.6, -0.3), intensity=1.0)
        assert ta.adapt(fearful) == Tone.SOOTHING

    def test_markers(self):
        ta = ToneAdapter()
        markers = ta.markers(Tone.FORMAL)
        assert "veuillez" in markers
        assert ta.markers(Tone.CASUAL) != []


class TestEmpathyEngine:
    def test_register_user(self):
        e = EmpathyEngine()
        u = e.register_user("user_1")
        assert u.user_id == "user_1"

    def test_infer_sentiment(self):
        e = EmpathyEngine()
        e.register_user("u1")
        state = e.infer("u1", {"sentiment": 0.8})
        assert state is not None
        assert state.inferred_emotion == BasicEmotion.JOY
        assert state.confidence > 0

    def test_infer_negative(self):
        e = EmpathyEngine()
        e.register_user("u1")
        state = e.infer("u1", {"sentiment": -0.6})
        assert state.inferred_emotion == BasicEmotion.SADNESS

    def test_infer_unknown_user(self):
        e = EmpathyEngine()
        assert e.infer("nonexistent", {}) is None

    def test_get_user(self):
        e = EmpathyEngine()
        e.register_user("u1")
        assert e.get_user("u1") is not None
        assert e.get_user("nope") is None

    def test_all_users(self):
        e = EmpathyEngine()
        e.register_user("a")
        e.register_user("b")
        assert len(e.all_users()) == 2


class TestAnimusEngine:
    def test_create(self):
        a = AnimusEngine()
        assert a.emotion is not None
        assert a.personality is not None
        assert a.tone is not None
        assert a.empathy is not None

    def test_feel(self):
        a = AnimusEngine()
        state = a.feel(BasicEmotion.JOY, 0.9)
        assert state.primary == BasicEmotion.JOY

    def test_respond_to_user(self):
        a = AnimusEngine()
        result = a.respond_to_user("u1", {"sentiment": 0.7, "engagement": 0.8})
        assert result["user_id"] == "u1"
        assert "my_emotion" in result
        assert "user_emotion" in result
        assert "tone" in result

    def test_get_mood(self):
        a = AnimusEngine()
        assert isinstance(a.get_mood(), str)

    def test_get_stats(self):
        a = AnimusEngine()
        stats = a.get_stats()
        assert "current_emotion" in stats
        assert "personality" in stats
        assert "users_tracked" in stats

    def test_process_feel(self):
        a = AnimusEngine()
        result = a.process({"action": "feel", "emotion": "joy", "intensity": 0.8})
        assert result["success"] is True

    def test_process_feel_bad_emotion(self):
        a = AnimusEngine()
        result = a.process({"action": "feel", "emotion": "fake"})
        assert result["success"] is False

    def test_process_respond(self):
        a = AnimusEngine()
        result = a.process({"action": "respond", "user_id": "u1", "signals": {"sentiment": 0.5}})
        assert result["success"] is True

    def test_process_mood(self):
        a = AnimusEngine()
        result = a.process({"action": "mood"})
        assert result["success"] is True

    def test_process_stats(self):
        a = AnimusEngine()
        result = a.process({"action": "stats"})
        assert result["success"] is True

    def test_process_bad_action(self):
        a = AnimusEngine()
        result = a.process({"action": "nonexistent"})
        assert result["success"] is False

    def test_process_bad_input(self):
        a = AnimusEngine()
        result = a.process("invalid")
        assert result["success"] is False
