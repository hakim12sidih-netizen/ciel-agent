from __future__ import annotations

import hashlib
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SensorType(Enum):
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    API = "api"
    WEBSOCKET = "websocket"
    IOT = "iot"
    VOICE = "voice"
    VISION = "vision"
    TEXT = "text"
    BIOMETRIC = "biometric"
    BCI = "bci"
    SATELLITE = "satellite"
    CHANNEL = "channel"


SENSOR_NAMES = {
    SensorType.FILESYSTEM: "Système de fichiers",
    SensorType.DATABASE: "Base de données",
    SensorType.API: "API REST/GraphQL",
    SensorType.WEBSOCKET: "WebSocket/MQTT",
    SensorType.IOT: "Capteurs IoT",
    SensorType.VOICE: "Voix/ASR",
    SensorType.VISION: "Vision/CV",
    SensorType.TEXT: "Texte/OCR",
    SensorType.BIOMETRIC: "Biométrie",
    SensorType.BCI: "BCI/EEG",
    SensorType.SATELLITE: "Satellite",
    SensorType.CHANNEL: "Canal communication",
}


@dataclass(slots=True)
class SensorReading:
    sensor: SensorType
    data: Any = None
    raw: str = ""
    timestamp: float = 0.0
    confidence: float = 1.0
    source_id: str = ""

    def fingerprint(self) -> str:
        raw_str = str(self.raw)[:256]
        return hashlib.sha256(f"{self.sensor.value}:{raw_str}".encode()).hexdigest()[:16]


class Sensor:
    """Capteur individuel — collecte de données brutes."""

    def __init__(self, sensor_type: SensorType, source_id: str = "",
                 sample_rate: float = 1.0):
        self.sensor_type = sensor_type
        self.source_id = source_id or f"{sensor_type.value}-{random.randint(100,999)}"
        self.sample_rate = sample_rate
        self._readings: list[SensorReading] = []
        self._active = True
        self._error_count = 0

    def read(self, data: Any = None, raw: str = "", confidence: float = 1.0) -> SensorReading:
        reading = SensorReading(
            sensor=self.sensor_type,
            data=data,
            raw=raw,
            timestamp=time.time(),
            confidence=confidence,
            source_id=self.source_id,
        )
        self._readings.append(reading)
        return reading

    def simulate(self) -> SensorReading:
        if not self._active:
            raise RuntimeError(f"sensor {self.source_id} is inactive")
        mock_data = {
            SensorType.FILESYSTEM: {"path": "/tmp/data", "size": random.randint(100, 10000)},
            SensorType.DATABASE: {"query": "SELECT *", "rows": random.randint(0, 100)},
            SensorType.API: {"endpoint": "/v1/status", "status": random.choice(["ok", "degraded"])},
            SensorType.WEBSOCKET: {"event": random.choice(["connect", "disconnect", "message"])},
            SensorType.IOT: {"temp": round(random.uniform(15, 35), 1), "humidity": round(random.uniform(30, 80), 1)},
            SensorType.VOICE: {"transcript": "hello", "duration": round(random.uniform(0.5, 5.0), 2)},
            SensorType.VISION: {"objects": random.randint(0, 10), "resolution": "1920x1080"},
            SensorType.TEXT: {"content": "sample text", "length": random.randint(10, 500)},
            SensorType.BIOMETRIC: {"hr": random.randint(60, 100), "gsr": round(random.uniform(0.1, 5.0), 2)},
            SensorType.BCI: {"channels": 8, "alpha": round(random.uniform(0.1, 0.9), 2)},
            SensorType.SATELLITE: {"lat": round(random.uniform(-90, 90), 4), "lon": round(random.uniform(-180, 180), 4)},
            SensorType.CHANNEL: {"platform": random.choice(["telegram", "discord"]), "messages": random.randint(0, 50)},
        }
        return self.read(
            data=mock_data.get(self.sensor_type, {}),
            raw=str(mock_data.get(self.sensor_type, {})),
            confidence=random.uniform(0.7, 1.0),
        )

    def readings(self, n: int = 10) -> list[SensorReading]:
        return list(self._readings[-n:])

    def count(self) -> int:
        return len(self._readings)

    def deactivate(self) -> None:
        self._active = False

    def activate(self) -> None:
        self._active = True


class GravityFilter:
    """Filtre gravitationnel — filtrage entropique des signaux."""

    def __init__(self, entropy_threshold: float = 0.5):
        self.entropy_threshold = entropy_threshold
        self._filtered: list[SensorReading] = []
        self._rejected: list[SensorReading] = []

    def entropy(self, reading: SensorReading) -> float:
        raw = str(reading.raw)
        if not raw:
            return 0.0
        freq: dict[str, int] = {}
        for ch in raw[:64]:
            freq[ch] = freq.get(ch, 0) + 1
        h = 0.0
        total = sum(freq.values())
        for count in freq.values():
            p = count / total
            h -= p * (p and __import__("math").log2(p))
        return h / 6.0

    def filter(self, reading: SensorReading) -> SensorReading | None:
        h = self.entropy(reading)
        if h >= self.entropy_threshold:
            self._filtered.append(reading)
            return reading
        self._rejected.append(reading)
        return None

    def filter_many(self, readings: list[SensorReading]) -> list[SensorReading]:
        return [r for r in readings if self.filter(r) is not None]

    def stats(self) -> dict[str, Any]:
        return {
            "threshold": self.entropy_threshold,
            "passed": len(self._filtered),
            "rejected": len(self._rejected),
            "accept_rate": len(self._filtered) / max(len(self._filtered) + len(self._rejected), 1) if (self._filtered or self._rejected) else 1.0,
        }


class IngestionPipeline:
    """Pipeline d'ingestion — sens → filtre → strates amont."""

    def __init__(self):
        self._sensors: dict[str, Sensor] = {}
        self._filters: list[GravityFilter] = []
        self._processors: list[Callable[[SensorReading], None]] = []
        self._ingested: list[SensorReading] = []

    def attach_sensor(self, sensor: Sensor) -> None:
        self._sensors[sensor.source_id] = sensor

    def get_sensor(self, source_id: str) -> Sensor | None:
        return self._sensors.get(source_id)

    def add_filter(self, filter_obj: GravityFilter) -> None:
        self._filters.append(filter_obj)

    def register_processor(self, processor: Callable[[SensorReading], None]) -> None:
        self._processors.append(processor)

    def ingest(self, reading: SensorReading) -> SensorReading | None:
        for f in self._filters:
            reading = f.filter(reading)
            if reading is None:
                return None
        self._ingested.append(reading)
        for p in self._processors:
            p(reading)
        return reading

    def ingest_from_sensor(self, source_id: str, data: Any = None,
                           raw: str = "", confidence: float = 1.0) -> SensorReading | None:
        sensor = self._sensors.get(source_id)
        if not sensor:
            return None
        reading = sensor.read(data, raw, confidence)
        return self.ingest(reading)

    def ingest_count(self) -> int:
        return len(self._ingested)

    def sensor_count(self) -> int:
        return len(self._sensors)


class PerceptionEngine:
    """Point d'entrée — Perception : 12 sens, pipeline d'ingestion, filtre entropique."""

    def __init__(self, entropy_threshold: float = 0.5):
        self.pipeline = IngestionPipeline()
        self._default_filter = GravityFilter(entropy_threshold)
        self.pipeline.add_filter(self._default_filter)
        self._sensor_registry: dict[SensorType, list[str]] = {}

    def add_sensor(self, sensor_type: SensorType, source_id: str = "",
                   sample_rate: float = 1.0) -> Sensor:
        sensor = Sensor(sensor_type, source_id, sample_rate)
        self.pipeline.attach_sensor(sensor)
        st = sensor_type
        if st not in self._sensor_registry:
            self._sensor_registry[st] = []
        self._sensor_registry[st].append(sensor.source_id)
        return sensor

    def read(self, source_id: str, data: Any = None,
             raw: str = "", confidence: float = 1.0) -> SensorReading | None:
        return self.pipeline.ingest_from_sensor(source_id, data, raw, confidence)

    def simulate(self, sensor_type: SensorType) -> SensorReading | None:
        ids = self._sensor_registry.get(sensor_type, [])
        if not ids:
            return None
        sensor = self.pipeline.get_sensor(ids[0])
        if not sensor:
            return None
        reading = sensor.simulate()
        return self.pipeline.ingest(reading)

    def simulate_all(self) -> list[SensorReading]:
        results = []
        for st in SensorType:
            r = self.simulate(st)
            if r:
                results.append(r)
        return results

    def set_threshold(self, threshold: float) -> None:
        self._default_filter.entropy_threshold = max(0.0, min(1.0, threshold))

    def get_stats(self) -> dict[str, Any]:
        return {
            "sensors": self.pipeline.sensor_count(),
            "ingested": self.pipeline.ingest_count(),
            "filter_stats": self._default_filter.stats(),
            "sensor_types": {st.value: len(ids) for st, ids in self._sensor_registry.items()},
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "add_sensor":
            st_str = str(data.get("sensor_type", "text"))
            try:
                st = SensorType(st_str)
            except ValueError:
                return {"success": False, "error": f"unknown sensor type '{st_str}'"}
            s = self.add_sensor(st, str(data.get("source_id", "")),
                                float(data.get("sample_rate", 1.0)))
            return {"success": True, "action": "add_sensor",
                    "source_id": s.source_id, "sensor_type": st_str}

        elif action == "read":
            reading = self.read(
                str(data.get("source_id", "")),
                data.get("data"),
                str(data.get("raw", "")),
                float(data.get("confidence", 1.0)),
            )
            if reading:
                return {"success": True, "action": "read",
                        "fingerprint": reading.fingerprint(),
                        "sensor": reading.sensor.value}
            return {"success": False, "error": "sensor not found or rejected by filter"}

        elif action == "simulate":
            st_str = str(data.get("sensor_type", "text"))
            try:
                st = SensorType(st_str)
            except ValueError:
                return {"success": False, "error": f"unknown sensor type '{st_str}'"}
            reading = self.simulate(st)
            if reading:
                return {"success": True, "action": "simulate",
                        "fingerprint": reading.fingerprint()}
            return {"success": False, "error": f"no sensor of type '{st_str}'"}

        elif action == "simulate_all":
            results = self.simulate_all()
            return {"success": True, "action": "simulate_all",
                    "count": len(results),
                    "readings": [{"sensor": r.sensor.value, "fingerprint": r.fingerprint()}
                                for r in results]}

        elif action == "set_threshold":
            self.set_threshold(float(data.get("threshold", 0.5)))
            return {"success": True, "action": "set_threshold"}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
