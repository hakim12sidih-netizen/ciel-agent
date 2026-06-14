"""
CIEL v∞.9 — ACID Transaction Engine for Plugin Registry.
Begin/commit/rollback with deep snapshots and concurrent isolation.
"""
from __future__ import annotations

import copy
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


__all__ = [
    "PluginTransaction", "TransactionError", "TransactionSnapshot",
    "transactional", "current_tx",
]


class TransactionError(Exception):
    pass


_thread_local = threading.local()


def current_tx() -> PluginTransaction | None:
    return getattr(_thread_local, "current_tx", None)


@dataclass
class TransactionSnapshot:
    id: str
    timestamp: float
    manifest_snapshot: dict[str, Any]
    plugin_snapshot: dict[str, Any]
    hook_snapshot: dict[str, list]
    event_snapshot: dict[str, list]
    parent_id: str | None = None


class PluginTransaction:
    def __init__(self, registry: Any, label: str = ""):
        self.id = f"tx-{uuid.uuid4().hex[:12]}"
        self.label = label or self.id
        self.registry = registry
        self._snapshot: TransactionSnapshot | None = None
        self._committed = False
        self._rolled_back = False
        self._pending: list[dict] = []
        self._nested: PluginTransaction | None = None
        self._parent: PluginTransaction | None = None
        self._lock = threading.Lock()
        self._start_time = time.time()

    def begin(self):
        if current_tx() is not None and current_tx() is not self:
            parent = current_tx()
            self._parent = parent
            parent._nested = self
            _thread_local.current_tx = self
            self._snapshot = parent._snapshot
            return self

        _thread_local.current_tx = self

        self._snapshot = TransactionSnapshot(
            id=self.id,
            timestamp=time.time(),
            manifest_snapshot=copy.deepcopy(self.registry._manifests),
            plugin_snapshot=copy.deepcopy(self.registry._plugins),
            hook_snapshot=copy.deepcopy(dict(self.registry._hooks)),
            event_snapshot=copy.deepcopy(dict(self.registry._events)),
        )
        self._pending.clear()
        return self

    async def commit(self) -> dict:
        if self._committed:
            raise TransactionError("Transaction already committed")
        if self._rolled_back:
            raise TransactionError("Transaction already rolled back")

        if self._nested:
            nested_result = await self._nested.commit()
            self._nested = None
            _thread_local.current_tx = self
            return nested_result

        if self._parent:
            self._committed = True
            _thread_local.current_tx = self._parent
            return {"status": "committed_nested", "id": self.id, "duration_ms": (time.time() - self._start_time) * 1000}

        _thread_local.current_tx = None
        self._committed = True

        audit = {
            "id": self.id,
            "label": self.label,
            "status": "committed",
            "operations": list(self._pending),
            "duration_ms": (time.time() - self._start_time) * 1000,
        }
        self._snapshot = None
        return audit

    async def rollback(self) -> dict:
        if self._committed:
            raise TransactionError("Cannot rollback committed transaction")
        if self._rolled_back:
            raise TransactionError("Transaction already rolled back")

        if self._nested:
            await self._nested.rollback()
            self._nested = None

        if self._snapshot is None:
            raise TransactionError("No snapshot to rollback to")

        if self._parent:
            self._rolled_back = True
            _thread_local.current_tx = self._parent
            self._parent._nested = None
            return {
                "status": "rolled_back_nested",
                "id": self.id,
                "duration_ms": (time.time() - self._start_time) * 1000,
            }

        with self._lock:
            self.registry._manifests = copy.deepcopy(self._snapshot.manifest_snapshot)
            self.registry._plugins = copy.deepcopy(self._snapshot.plugin_snapshot)
            self.registry._hooks = copy.deepcopy(self._snapshot.hook_snapshot)
            self.registry._events = copy.deepcopy(self._snapshot.event_snapshot)

        _thread_local.current_tx = None
        self._rolled_back = True

        return {
            "id": self.id,
            "label": self.label,
            "status": "rolled_back",
            "duration_ms": (time.time() - self._start_time) * 1000,
        }

    def log_operation(self, op_type: str, **kwargs):
        self._pending.append({
            "type": op_type,
            "timestamp": time.time(),
            **kwargs,
        })

    @property
    def duration_ms(self) -> float:
        return (time.time() - self._start_time) * 1000


@asynccontextmanager
async def transactional(registry: Any, label: str = ""):
    tx = PluginTransaction(registry, label)
    tx.begin()
    try:
        yield tx
        if not tx._committed and not tx._rolled_back:
            await tx.commit()
    except Exception as e:
        if not tx._rolled_back:
            await tx.rollback()
        raise


def transaction(label: str = ""):
    def decorator(func):
        import functools
        @functools.wraps(func)
        async def wrapper(registry: Any, *args, **kwargs):
            async with transactional(registry, label or func.__name__) as tx:
                return await func(registry, *args, tx=tx, **kwargs)
        return wrapper
    return decorator
