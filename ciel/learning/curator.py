from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CuratedItem:
    id: str
    type: str
    name: str
    usage_count: int = 0
    last_used_at: float = 0.0
    created_at: float = field(default_factory=time.time)
    score: float = 0.0
    archived: bool = False
    pinned: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class Curator:
    """Curateur background — archive les skills/sessions inutilisés,
    épingle les critiques, ne supprime jamais.

    Inspiré du Curator Hermès mais plus agressif :
    - skills inutilisés >30j → archivés (score -= 0.1/jour)
    - skills très utilisés → épinglés (pin = True)
    - sessions >7d sans activity → archivées
    """

    def __init__(self, data_dir: str | Path | None = None):
        self._data_dir = Path(data_dir or Path.home() / ".ciel" / "curator")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._items: dict[str, CuratedItem] = {}
        self._db_path = self._data_dir / "curator.db"
        self._load()
        self._stats = {
            "total_scans": 0,
            "items_archived": 0,
            "items_pinned": 0,
            "sessions_cleaned": 0,
        }

    def _load(self) -> None:
        if not self._db_path.exists():
            return
        try:
            data = json.loads(self._db_path.read_text())
            for item_data in data.get("items", []):
                item = CuratedItem(**item_data)
                self._items[item.id] = item
            self._stats.update(data.get("stats", {}))
        except Exception:
            pass

    def _save(self) -> None:
        data = {
            "items": [vars(i) for i in self._items.values()],
            "stats": self._stats,
        }
        self._db_path.write_text(json.dumps(data, indent=2, default=str))

    def track(self, item_id: str, type_: str, name: str,
              metadata: dict | None = None) -> None:
        if item_id in self._items:
            item = self._items[item_id]
            item.usage_count += 1
            item.last_used_at = time.time()
        else:
            self._items[item_id] = CuratedItem(
                id=item_id, type=type_, name=name,
                usage_count=1, last_used_at=time.time(),
                metadata=metadata or {},
            )
        self._save()

    def pin(self, item_id: str) -> None:
        item = self._items.get(item_id)
        if item:
            item.pinned = True
            item.archived = False
            self._save()

    def unpin(self, item_id: str) -> None:
        item = self._items.get(item_id)
        if item:
            item.pinned = False
            self._save()

    def scan(self, age_days_archive: int = 30,
             age_days_pin: int = 7,
             usage_threshold: int = 10) -> list[str]:
        self._stats["total_scans"] += 1
        now = time.time()
        changes: list[str] = []

        for item_id, item in list(self._items.items()):
            if item.pinned:
                continue

            age_seconds = now - item.last_used_at if item.last_used_at else now - item.created_at
            age_days = age_seconds / 86400

            if age_days > age_days_archive and not item.archived:
                item.archived = True
                item.score = max(0, item.score - age_days * 0.1)
                self._stats["items_archived"] += 1
                changes.append(f"archived:{item_id}")
                logger.info(f"Curator archived {item.type} '{item.name}' ({age_days:.0f}d)")

            if item.usage_count >= usage_threshold and not item.pinned:
                self.pin(item_id)
                self._stats["items_pinned"] += 1
                changes.append(f"pinned:{item_id}")
                logger.info(f"Curator pinned {item.type} '{item.name}' ({item.usage_count} uses)")

        self._save()
        return changes

    def cleanup_old_sessions(self, max_age_days: int = 7) -> int:
        now = time.time()
        threshold = now - (max_age_days * 86400)
        old = [i for i in self._items.values()
               if i.type == "session" and i.last_used_at < threshold
               and not i.pinned]
        for item in old:
            item.archived = True
        count = len(old)
        self._stats["sessions_cleaned"] += count
        self._save()
        if count:
            logger.info(f"Curator cleaned {count} old sessions")
        return count

    def get_stats(self) -> dict[str, Any]:
        return dict(self._stats)

    def get_items(self, type_: str = "", archived: bool | None = None,
                  pinned: bool | None = None) -> list[CuratedItem]:
        results = list(self._items.values())
        if type_:
            results = [i for i in results if i.type == type_]
        if archived is not None:
            results = [i for i in results if i.archived == archived]
        if pinned is not None:
            results = [i for i in results if i.pinned == pinned]
        return sorted(results, key=lambda i: i.score, reverse=True)

    def get_item(self, item_id: str) -> CuratedItem | None:
        return self._items.get(item_id)

    def forget(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            self._save()
            return True
        return False

    def summary(self) -> str:
        total = len(self._items)
        active = len([i for i in self._items.values() if not i.archived])
        pinned = len([i for i in self._items.values() if i.pinned])
        archived = len([i for i in self._items.values() if i.archived])
        return (
            f"Curator: {total} items ({active} actifs, {pinned} épinglés, {archived} archivés) | "
            f"{self._stats['total_scans']} scans, "
            f"{self._stats['items_archived']} archivés, "
            f"{self._stats['sessions_cleaned']} sessions nettoyées"
        )
