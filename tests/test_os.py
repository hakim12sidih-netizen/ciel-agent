from __future__ import annotations

import pytest

from ciel.os.core import OSEngine, SensorReading, SensorType


class TestSensorType:
    def test_count(self):
        assert len(SensorType) == 21

    def test_values(self):
        assert SensorType.CPU.value == "cpu"
        assert SensorType.MEM.value == "mem"
        assert SensorType.DISK.value == "disk"
        assert SensorType.NET.value == "net"

    def test_members_present(self):
        assert SensorType.CPU in SensorType
        assert SensorType.MEM in SensorType
        assert SensorType.GPU in SensorType
        assert SensorType.TEMP in SensorType
        assert SensorType.ENTROPY in SensorType

    def test_all_unique(self):
        names = [s.name for s in SensorType]
        assert len(names) == len(set(names))


class TestSensorReading:
    def test_create(self):
        sr = SensorReading(sensor=SensorType.CPU, value=42.5)
        assert sr.sensor == SensorType.CPU
        assert sr.value == 42.5
        assert sr.label == ""
        assert sr.metadata == {}

    def test_auto_timestamp(self):
        sr = SensorReading(sensor=SensorType.MEM, value=50.0)
        assert sr.timestamp > 0


class TestOSEngine:
    def test_create(self):
        os = OSEngine()
        assert os._ring_level == -1
        assert len(os._hooks) == 10

    def test_read_sensor(self):
        os = OSEngine()
        r = os.read_sensor(SensorType.CPU)
        assert isinstance(r, SensorReading)
        assert r.sensor == SensorType.CPU
        assert 0 <= r.value <= 100

    def test_read_sensor_restricted(self):
        os = OSEngine()
        r = os.read_sensor(SensorType.AUDIO)
        assert r.value == 0.0

    def test_read_all(self):
        os = OSEngine()
        values = os.read_all()
        assert len(values) == 21
        assert "cpu" in values

    def test_get_stats(self):
        os = OSEngine()
        stats = os.get_stats()
        assert stats["ring_level"] == -1
        assert stats["sensors"] == 21
        assert stats["hooks_active"] == 10
        assert stats["readings"] == 0

    def test_set_hook(self):
        os = OSEngine()
        os.set_hook("syscall_open", False)
        assert os._hooks["syscall_open"] is False

    def test_set_hook_invalid(self):
        os = OSEngine()
        os.set_hook("nonexistent", False)
        assert "nonexistent" not in os._hooks

    def test_process_read(self):
        os = OSEngine()
        r = os.process({"action": "read", "sensor": "cpu"})
        assert r["success"] is True
        assert r["sensor"] == "cpu"
        assert isinstance(r["value"], float)

    def test_process_read_bad_sensor(self):
        os = OSEngine()
        r = os.process({"action": "read", "sensor": "nonexistent"})
        assert r["success"] is False

    def test_process_read_all(self):
        os = OSEngine()
        r = os.process({"action": "read_all"})
        assert r["success"] is True
        assert len(r["sensors"]) == 21

    def test_process_stats(self):
        os = OSEngine()
        r = os.process({"action": "stats"})
        assert r["success"] is True
        assert r["action"] == "stats"
        assert r["sensors"] == 21

    def test_process_default_returns_stats(self):
        os = OSEngine()
        r = os.process({})
        assert r["success"] is True
        assert r["action"] == "stats"

    def test_process_bad_input(self):
        os = OSEngine()
        r = os.process("bad")
        assert r["success"] is False

    def test_process_unknown_action(self):
        os = OSEngine()
        r = os.process({"action": "nope"})
        assert r["success"] is False

    def test_sensor_value_range(self):
        os = OSEngine()
        r = os.read_sensor(SensorType.CPU)
        assert 0 <= r.value <= 100

    def test_readings_are_appended(self):
        os = OSEngine()
        os.read_sensor(SensorType.CPU)
        os.read_sensor(SensorType.MEM)
        assert len(os._readings) == 2
