"""
Strate 6 — ŒIL DU MONDE : Perception Universelle (12 sens).

Capteurs :
  1. filesystem   6. voice      10. bci
  2. database     7. vision     11. satellite
  3. api          8. text       12. channel
  4. websocket    9. biometric
  5. iot

Pipeline : ingestion → GravityFilter (entropie) → strates amont
"""
from __future__ import annotations

from ciel.perception.core import (
    SensorType, SensorReading, Sensor,
    GravityFilter, IngestionPipeline, PerceptionEngine,
    SENSOR_NAMES,
)
__all__ = [
    "SensorType", "SensorReading", "Sensor",
    "GravityFilter", "IngestionPipeline", "PerceptionEngine",
    "SENSOR_NAMES",
]
