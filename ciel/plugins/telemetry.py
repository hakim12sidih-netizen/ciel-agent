"""
CIEL v∞.9 — Plugin Telemetry & Audit.
Structured audit log, performance telemetry, crash reporting, usage heatmap.
"""
from __future__ import annotations

import json
import os
import time
import uuid
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


__all__ = [
    "TelemetryEngine", "AuditEntry", "TelemetryStats",
    "get_telemetry",
]


AUDIT_LOG_PATH = Path.home() / ".ciel" / "logs" / "plugin_audit.jsonl"
TELEMETRY_LOG_PATH = Path.home() / ".ciel" / "logs" / "plugin_telemetry.jsonl"
MAX_AUDIT_ENTRIES = 100_000
MAX_TELEMETRY_ENTRIES = 10_000


@dataclass
class AuditEntry:
    id: str
    timestamp: float
    plugin: str
    action: str
    capability: str = ""
    resource: str = ""
    decision: str = ""  # allow / deny / prompt
    reason: str = ""
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ts": self.timestamp,
            "plugin": self.plugin,
            "action": self.action,
            "capability": self.capability,
            "resource": self.resource,
            "decision": self.decision,
            "reason": self.reason,
            "duration_ms": round(self.duration_ms, 1),
            "metadata": self.metadata,
        }


@dataclass
class HookTelemetry:
    hook_name: str
    plugin: str
    duration_ms: float = 0.0
    success: bool = True
    error: str = ""
    timestamp: float = 0.0


class TelemetryEngine:
    def __init__(self, audit_path: str | Path | None = None,
                 telemetry_path: str | Path | None = None):
        self._audit_path = Path(audit_path or AUDIT_LOG_PATH).expanduser().resolve()
        self._telemetry_path = Path(telemetry_path or TELEMETRY_LOG_PATH).expanduser().resolve()
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)
        self._telemetry_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

        self._audit_buffer: list[AuditEntry] = []
        self._telemetry_buffer: list[HookTelemetry] = []

        self._hook_times: dict[str, list[float]] = {}
        self._plugin_hook_times: dict[str, dict[str, list[float]]] = {}
        self._permission_counts: dict[str, dict[str, int]] = {}
        self._error_counts: dict[str, int] = {}
        self._crash_reports: list[dict] = []

        self._total_audit = 0
        self._total_telemetry = 0

    def log_audit(self, plugin: str, action: str, capability: str = "",
                  resource: str = "", decision: str = "allow",
                  reason: str = "", duration_ms: float = 0.0,
                  metadata: dict | None = None) -> AuditEntry:
        entry = AuditEntry(
            id=f"aud-{uuid.uuid4().hex[:12]}",
            timestamp=time.time(),
            plugin=plugin,
            action=action,
            capability=capability,
            resource=resource,
            decision=decision,
            reason=reason,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        with self._lock:
            self._audit_buffer.append(entry)
            self._total_audit += 1
            if capability not in self._permission_counts:
                self._permission_counts[capability] = {}
            if decision not in self._permission_counts[capability]:
                self._permission_counts[capability][decision] = 0
            self._permission_counts[capability][decision] += 1
            if len(self._audit_buffer) >= 100:
                self._flush_audit()
        return entry

    def log_hook(self, hook_name: str, plugin: str,
                 duration_ms: float, success: bool = True,
                 error: str = "") -> HookTelemetry:
        h = HookTelemetry(
            hook_name=hook_name, plugin=plugin,
            duration_ms=duration_ms, success=success,
            error=error, timestamp=time.time(),
        )
        with self._lock:
            self._telemetry_buffer.append(h)
            self._total_telemetry += 1
            if hook_name not in self._hook_times:
                self._hook_times[hook_name] = []
            self._hook_times[hook_name].append(duration_ms)
            if len(self._hook_times[hook_name]) > 1000:
                self._hook_times[hook_name] = self._hook_times[hook_name][-1000:]

            if plugin not in self._plugin_hook_times:
                self._plugin_hook_times[plugin] = {}
            if hook_name not in self._plugin_hook_times[plugin]:
                self._plugin_hook_times[plugin][hook_name] = []
            self._plugin_hook_times[plugin][hook_name].append(duration_ms)

            if not success:
                self._error_counts[plugin] = self._error_counts.get(plugin, 0) + 1

            if len(self._telemetry_buffer) >= 100:
                self._flush_telemetry()
        return h

    def report_crash(self, plugin: str, error: str,
                     trace: str = "", context: dict | None = None) -> dict:
        report = {
            "id": f"crash-{uuid.uuid4().hex[:12]}",
            "timestamp": time.time(),
            "plugin": plugin,
            "error": error,
            "traceback": trace,
            "context": context or {},
            "reported_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._crash_reports.append(report)
            self._error_counts[plugin] = self._error_counts.get(plugin, 0) + 1
            self._total_audit += 1
        return report

    def _flush_audit(self):
        if not self._audit_buffer:
            return
        try:
            lines = [json.dumps(e.to_dict()) for e in self._audit_buffer]
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            self._audit_buffer.clear()
        except Exception:
            pass

    def _flush_telemetry(self):
        if not self._telemetry_buffer:
            return
        try:
            lines = [
                json.dumps({
                    "hook": h.hook_name,
                    "plugin": h.plugin,
                    "duration_ms": round(h.duration_ms, 1),
                    "success": h.success,
                    "error": h.error,
                    "ts": h.timestamp,
                })
                for h in self._telemetry_buffer
            ]
            with open(self._telemetry_path, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            self._telemetry_buffer.clear()
        except Exception:
            pass

    def flush(self):
        with self._lock:
            self._flush_audit()
            self._flush_telemetry()

    def get_heatmap(self) -> dict:
        with self._lock:
            heatmap = {}
            for hook_name, times in self._hook_times.items():
                heatmap[hook_name] = {
                    "count": len(times),
                    "avg_ms": round(sum(times) / len(times), 1) if times else 0,
                    "max_ms": round(max(times), 1) if times else 0,
                    "p95_ms": sorted(times)[int(len(times) * 0.95)] if times else 0,
                }
            return heatmap

    def get_permission_audit(self) -> dict:
        with self._lock:
            return {
                cap: dict(counts)
                for cap, counts in self._permission_counts.items()
            }

    def get_error_report(self) -> dict:
        with self._lock:
            return {
                "total_errors": sum(self._error_counts.values()),
                "by_plugin": dict(self._error_counts),
                "recent_crashes": self._crash_reports[-10:],
            }

    def get_stats(self) -> dict:
        self.flush()
        with self._lock:
            audit_size = self._audit_path.stat().st_size if self._audit_path.exists() else 0
            telemetry_size = self._telemetry_path.stat().st_size if self._telemetry_path.exists() else 0
            return {
                "total_audit_entries": self._total_audit,
                "total_telemetry_entries": self._total_telemetry,
                "audit_log_size_bytes": audit_size,
                "telemetry_log_size_bytes": telemetry_size,
                "crash_reports": len(self._crash_reports),
                "hook_count": len(self._hook_times),
                "plugins_with_errors": len(self._error_counts),
                "audit_path": str(self._audit_path),
                "telemetry_path": str(self._telemetry_path),
            }

    def get_plugin_stats(self, plugin: str) -> dict:
        with self._lock:
            hook_data = self._plugin_hook_times.get(plugin, {})
            return {
                "plugin": plugin,
                "errors": self._error_counts.get(plugin, 0),
                "hooks": {
                    name: {
                        "count": len(times),
                        "avg_ms": round(sum(times) / len(times), 1) if times else 0,
                    }
                    for name, times in hook_data.items()
                },
                "total_hook_calls": sum(len(t) for t in hook_data.values()),
            }


_telemetry_singleton: TelemetryEngine | None = None
_telemetry_lock = threading.Lock()


def get_telemetry() -> TelemetryEngine:
    global _telemetry_singleton
    if _telemetry_singleton is None:
        with _telemetry_lock:
            if _telemetry_singleton is None:
                _telemetry_singleton = TelemetryEngine()
    return _telemetry_singleton
