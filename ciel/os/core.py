from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SensorType(Enum):
    CPU = "cpu"
    MEM = "mem"
    DISK = "disk"
    NET = "net"
    PROC = "proc"
    FILE = "file"
    REG = "reg"
    AUDIO = "audio"
    CAMERA = "camera"
    KB = "keyboard"
    MOUSE = "mouse"
    WINDOW = "window"
    CLIP = "clipboard"
    GPU = "gpu"
    POWER = "power"
    TEMP = "temperature"
    USB = "usb"
    BT = "bluetooth"
    WIFI = "wifi"
    TIME = "time"
    ENTROPY = "entropy"


@dataclass(slots=True)
class SensorReading:
    sensor: SensorType
    value: float
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


class OSEngine:
    """CIEL-OS — 21 capteurs + hooks kernel (simulation)."""

    def __init__(self) -> None:
        self._sensors: dict[SensorType, dict[str, Any]] = {}
        self._readings: list[SensorReading] = []
        self._hooks: dict[str, bool] = {
            "syscall_open": True, "syscall_read": True, "syscall_write": True,
            "syscall_connect": True, "syscall_fork": True, "syscall_exec": True,
            "net_xdp": True, "net_tc": True, "fs_vfs": True, "lsm_file": True,
        }
        self._ring_level: int = -1  # -1 = hypervisor

    def read_sensor(self, sensor: SensorType) -> SensorReading:
        mock_ranges = {
            SensorType.CPU: (0, 100), SensorType.MEM: (0, 100),
            SensorType.DISK: (0, 100), SensorType.GPU: (0, 100),
            SensorType.POWER: (0, 100), SensorType.TEMP: (30, 95),
            SensorType.ENTROPY: (0, 1), SensorType.TIME: (0, 86400),
        }
        if sensor in (SensorType.AUDIO, SensorType.CAMERA, SensorType.CLIP):
            value = 0.0  # requires explicit permission
        else:
            lo, hi = mock_ranges.get(sensor, (0, 1))
            value = random.uniform(lo, hi)
        reading = SensorReading(sensor=sensor, value=value, label=f"{sensor.value}_sense")
        self._readings.append(reading)
        return reading

    def read_all(self) -> dict[str, float]:
        return {s.value: self.read_sensor(s).value for s in SensorType}

    def set_hook(self, hook: str, active: bool) -> None:
        if hook in self._hooks:
            self._hooks[hook] = active

    def get_stats(self) -> dict[str, Any]:
        return {
            "ring_level": self._ring_level,
            "sensors": len(SensorType),
            "hooks_active": sum(1 for v in self._hooks.values() if v),
            "readings": len(self._readings),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "read":
            sensor_str = str(data.get("sensor", "cpu")).upper()
            try:
                sensor = SensorType(sensor_str.lower())
            except ValueError:
                return {"success": False, "error": f"unknown sensor '{sensor_str}'"}
            reading = self.read_sensor(sensor)
            return {"success": True, "sensor": sensor.value, "value": reading.value}

        elif action == "read_all":
            values = self.read_all()
            return {"success": True, "sensors": values}

        elif action == "stats":
            return {"success": True, "action": "stats", **self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
