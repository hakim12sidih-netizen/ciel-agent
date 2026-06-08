from __future__ import annotations

import pytest
from ciel.perception.core import (
    SensorType, SensorReading, Sensor,
    GravityFilter, IngestionPipeline, PerceptionEngine,
    SENSOR_NAMES,
)


class TestSensorType:
    def test_all_sensors(self):
        assert len(SensorType) == 12
        assert SensorType.FILESYSTEM.value == "filesystem"
        assert SensorType.CHANNEL.value == "channel"

    def test_names(self):
        assert SENSOR_NAMES[SensorType.VISION] == "Vision/CV"
        assert SENSOR_NAMES[SensorType.BCI] == "BCI/EEG"


class TestSensorReading:
    def test_create(self):
        r = SensorReading(SensorType.TEXT, data="hello", raw="hello world")
        assert r.sensor == SensorType.TEXT
        assert r.confidence == 1.0

    def test_fingerprint(self):
        r = SensorReading(SensorType.API, raw="api_call")
        fp = r.fingerprint()
        assert len(fp) == 16


class TestSensor:
    def test_create(self):
        s = Sensor(SensorType.IOT, "sensor1", sample_rate=2.0)
        assert s.sensor_type == SensorType.IOT
        assert s.source_id == "sensor1"
        assert s.sample_rate == 2.0

    def test_read(self):
        s = Sensor(SensorType.VISION, "cam1")
        r = s.read(data={"objects": 3}, raw="3 objects detected", confidence=0.9)
        assert r.data["objects"] == 3
        assert s.count() == 1

    def test_simulate(self):
        s = Sensor(SensorType.IOT, "iot1")
        r = s.simulate()
        assert r.sensor == SensorType.IOT
        assert "temp" in r.data

    def test_simulate_inactive(self):
        s = Sensor(SensorType.TEXT, "t1")
        s.deactivate()
        with pytest.raises(RuntimeError):
            s.simulate()

    def test_activate_deactivate(self):
        s = Sensor(SensorType.API, "api1")
        assert s._active is True
        s.deactivate()
        assert s._active is False
        s.activate()
        assert s._active is True

    def test_readings(self):
        s = Sensor(SensorType.TEXT, "t1")
        for i in range(20):
            s.read(data=i, raw=str(i))
        assert len(s.readings(5)) == 5


class TestGravityFilter:
    def test_create(self):
        f = GravityFilter(entropy_threshold=0.5)
        assert f.entropy_threshold == 0.5

    def test_high_entropy_passes(self):
        f = GravityFilter(entropy_threshold=0.1)
        r = SensorReading(SensorType.TEXT, raw="abcdefghijklmnopqrstuvwxyz0123456789")
        assert f.filter(r) is not None
        assert len(f._filtered) == 1

    def test_low_entropy_rejected(self):
        f = GravityFilter(entropy_threshold=0.9)
        r = SensorReading(SensorType.TEXT, raw="aaaaaa")
        assert f.filter(r) is None
        assert len(f._rejected) == 1

    def test_filter_many(self):
        f = GravityFilter(entropy_threshold=0.3)
        readings = [
            SensorReading(SensorType.TEXT, raw="a" * 64),
            SensorReading(SensorType.TEXT, raw="abcdefghijklmnopqrstuvwxyz0123456789" * 2),
            SensorReading(SensorType.TEXT, raw="bbbbbb"),
        ]
        passed = f.filter_many(readings)
        assert len(passed) <= 3

    def test_stats(self):
        f = GravityFilter()
        assert f.stats()["accept_rate"] == 1.0
        f.filter(SensorReading(SensorType.TEXT, raw="aaa"))
        f.filter(SensorReading(SensorType.TEXT, raw="xyz"))
        stats = f.stats()
        assert "passed" in stats
        assert "rejected" in stats

    def test_entropy_empty(self):
        f = GravityFilter()
        r = SensorReading(SensorType.TEXT, raw="")
        assert f.entropy(r) == 0.0


class TestIngestionPipeline:
    def test_create(self):
        p = IngestionPipeline()
        assert p.ingest_count() == 0

    def test_attach_sensor(self):
        p = IngestionPipeline()
        s = Sensor(SensorType.API, "api1")
        p.attach_sensor(s)
        assert p.sensor_count() == 1

    def test_ingest(self):
        p = IngestionPipeline()
        f = GravityFilter(entropy_threshold=0.0)
        p.add_filter(f)
        r = SensorReading(SensorType.TEXT, raw="data")
        result = p.ingest(r)
        assert result is not None
        assert p.ingest_count() == 1

    def test_ingest_rejected(self):
        p = IngestionPipeline()
        f = GravityFilter(entropy_threshold=1.0)
        p.add_filter(f)
        r = SensorReading(SensorType.TEXT, raw="aaa")
        assert p.ingest(r) is None
        assert p.ingest_count() == 0

    def test_ingest_from_sensor(self):
        p = IngestionPipeline()
        f = GravityFilter(entropy_threshold=0.0)
        p.add_filter(f)
        s = Sensor(SensorType.TEXT, "t1")
        p.attach_sensor(s)
        result = p.ingest_from_sensor("t1", raw="test data")
        assert result is not None
        assert s.count() == 1

    def test_ingest_from_sensor_unknown(self):
        p = IngestionPipeline()
        assert p.ingest_from_sensor("nonexistent", raw="x") is None

    def test_register_processor(self):
        p = IngestionPipeline()
        f = GravityFilter(entropy_threshold=0.0)
        p.add_filter(f)
        processed = []
        p.register_processor(lambda r: processed.append(r))
        r = SensorReading(SensorType.TEXT, raw="data")
        p.ingest(r)
        assert len(processed) == 1


class TestPerceptionEngine:
    def test_create(self):
        e = PerceptionEngine()
        assert e.pipeline is not None
        assert e._default_filter is not None

    def test_add_sensor(self):
        e = PerceptionEngine()
        s = e.add_sensor(SensorType.API, "api_main", sample_rate=5.0)
        assert s.source_id == "api_main"
        assert e.pipeline.sensor_count() == 1

    def test_read(self):
        e = PerceptionEngine(entropy_threshold=0.0)
        e.add_sensor(SensorType.TEXT, "t1")
        r = e.read("t1", raw="hello world")
        assert r is not None

    def test_read_unknown_sensor(self):
        e = PerceptionEngine()
        assert e.read("ghost", raw="x") is None

    def test_simulate(self):
        e = PerceptionEngine()
        e.add_sensor(SensorType.IOT, "iot1")
        r = e.simulate(SensorType.IOT)
        assert r is not None
        assert "temp" in r.data

    def test_simulate_no_sensor(self):
        e = PerceptionEngine()
        assert e.simulate(SensorType.BCI) is None

    def test_simulate_all(self):
        e = PerceptionEngine()
        for st in SensorType:
            e.add_sensor(st, f"sensor-{st.value}")
        results = e.simulate_all()
        assert len(results) == 12

    def test_set_threshold(self):
        e = PerceptionEngine()
        e.set_threshold(0.8)
        assert e._default_filter.entropy_threshold == 0.8
        e.set_threshold(2.0)
        assert e._default_filter.entropy_threshold == 1.0

    def test_get_stats(self):
        e = PerceptionEngine()
        e.add_sensor(SensorType.TEXT, "t1")
        e.add_sensor(SensorType.API, "a1")
        stats = e.get_stats()
        assert "sensors" in stats
        assert stats["sensors"] == 2
        assert "filter_stats" in stats

    def test_process_add_sensor(self):
        e = PerceptionEngine()
        r = e.process({"action": "add_sensor", "sensor_type": "iot", "source_id": "my-iot"})
        assert r["success"] is True
        assert r["source_id"] == "my-iot"

    def test_process_add_sensor_bad_type(self):
        e = PerceptionEngine()
        r = e.process({"action": "add_sensor", "sensor_type": "nonexistent"})
        assert r["success"] is False

    def test_process_read(self):
        e = PerceptionEngine()
        e.set_threshold(0.0)
        e.add_sensor(SensorType.TEXT, "t1")
        r = e.process({"action": "read", "source_id": "t1", "raw": "test"})
        assert r["success"] is True
        assert "fingerprint" in r

    def test_process_read_unknown(self):
        e = PerceptionEngine()
        r = e.process({"action": "read", "source_id": "ghost"})
        assert r["success"] is False

    def test_process_simulate(self):
        e = PerceptionEngine()
        e.add_sensor(SensorType.API, "a1")
        r = e.process({"action": "simulate", "sensor_type": "api"})
        assert r["success"] is True

    def test_process_simulate_no_sensor(self):
        e = PerceptionEngine()
        r = e.process({"action": "simulate", "sensor_type": "api"})
        assert r["success"] is False

    def test_process_simulate_all(self):
        e = PerceptionEngine()
        for st in SensorType:
            e.add_sensor(st, f"s-{st.value}")
        r = e.process({"action": "simulate_all"})
        assert r["success"] is True
        assert r["count"] == 12

    def test_process_set_threshold(self):
        e = PerceptionEngine()
        r = e.process({"action": "set_threshold", "threshold": 0.7})
        assert r["success"] is True
        assert e._default_filter.entropy_threshold == 0.7

    def test_process_stats(self):
        e = PerceptionEngine()
        r = e.process({"action": "stats"})
        assert r["success"] is True

    def test_process_bad_action(self):
        e = PerceptionEngine()
        r = e.process({"action": "nonexistent"})
        assert r["success"] is False

    def test_process_bad_input(self):
        e = PerceptionEngine()
        r = e.process("bad")
        assert r["success"] is False
