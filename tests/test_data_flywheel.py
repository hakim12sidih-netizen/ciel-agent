from __future__ import annotations

import time

import pytest

from ciel.data_flywheel.core import (
    DataFlywheel, DataPacket, DataTier, DataValue,
)


class TestDataTier:
    def test_values(self):
        assert DataTier.PLATINUM.value == "platinum"
        assert DataTier.GOLD.value == "gold"
        assert DataTier.SILVER.value == "silver"
        assert DataTier.BRONZE.value == "bronze"
        assert len(DataTier) == 4


class TestDataPacket:
    def test_create(self):
        dp = DataPacket(
            id="p1", source="test", tier=DataTier.GOLD,
            content={"key": "val"}, timestamp=time.time(),
        )
        assert dp.id == "p1"
        assert dp.source == "test"
        assert dp.tier == DataTier.GOLD
        assert dp.content == {"key": "val"}

    def test_auto_size_and_checksum(self):
        dp = DataPacket("p1", "src", DataTier.PLATINUM, {"a": 1}, 100.0)
        assert dp.size_bytes > 0
        assert len(dp.checksum) == 16

    def test_default_agent_id(self):
        dp = DataPacket("p1", "src", DataTier.SILVER, {}, 100.0)
        assert dp.agent_id == ""


class TestDataValue:
    def test_create_and_score(self):
        dv = DataValue(relevance=1.0, uniqueness=0.5, freshness=0.8, quality=0.9)
        assert dv.relevance == 1.0
        assert dv.uniqueness == 0.5
        assert dv.freshness == 0.8
        assert dv.quality == 0.9
        assert dv.score == 1.0 * 0.5 * 0.8 * 0.9


class TestDataFlywheel:
    def test_create(self):
        df = DataFlywheel()
        assert df._total_ingested == 0
        assert df._processed == []

    def test_ingest_packet(self):
        df = DataFlywheel()
        dp = DataPacket("p1", "src", DataTier.GOLD, {"x": 1}, time.time())
        dv = df.ingest(dp)
        assert isinstance(dv, DataValue)
        assert df._total_ingested == 1

    def test_ingest_routes_to_tier(self):
        df = DataFlywheel()
        dp = DataPacket("p1", "src", DataTier.PLATINUM, {"x": 1}, time.time())
        df.ingest(dp)
        assert len(df._queue[DataTier.PLATINUM]) == 1

    def test_process_all(self):
        df = DataFlywheel()
        df.ingest(DataPacket("p1", "src", DataTier.GOLD, {"a": 1}, time.time()))
        df.ingest(DataPacket("p2", "src", DataTier.SILVER, {"b": 2}, time.time()))
        counts = df.process_all()
        assert counts["gold"] == 1
        assert counts["silver"] == 1
        assert counts["platinum"] == 0
        assert counts["bronze"] == 0

    def test_get_stats(self):
        df = DataFlywheel()
        stats = df.get_stats()
        assert stats["total_ingested"] == 0
        assert stats["total_processed"] == 0
        assert stats["queue_size"] == 0

    def test_get_stats_after_ingest(self):
        df = DataFlywheel()
        df.ingest(DataPacket("p1", "src", DataTier.GOLD, {"x": 1}, time.time()))
        stats = df.get_stats()
        assert stats["total_ingested"] == 1
        assert stats["queue_size"] == 1

    def test_process_ingest(self):
        df = DataFlywheel()
        r = df.process({"action": "ingest", "tier": "gold", "source": "alpha", "content": {"x": 1}})
        assert r["success"] is True
        assert "packet_id" in r
        assert "value_score" in r

    def test_process_ingest_default_tier(self):
        df = DataFlywheel()
        r = df.process({"action": "ingest", "source": "alpha", "content": {"x": 1}})
        assert r["success"] is True

    def test_process_ingest_bad_tier(self):
        df = DataFlywheel()
        r = df.process({"action": "ingest", "tier": "mythic"})
        assert r["success"] is False

    def test_process_process_all(self):
        df = DataFlywheel()
        df.ingest(DataPacket("p1", "src", DataTier.BRONZE, {"x": 1}, time.time()))
        r = df.process({"action": "process"})
        assert r["success"] is True
        assert r["processed"]["bronze"] == 1

    def test_process_stats(self):
        df = DataFlywheel()
        r = df.process({"action": "stats"})
        assert r["success"] is True
        assert r["action"] == "stats"
        assert "total_ingested" in r

    def test_process_bad_input(self):
        df = DataFlywheel()
        r = df.process("bad")
        assert r["success"] is False

    def test_process_unknown_action(self):
        df = DataFlywheel()
        r = df.process({"action": "nope"})
        assert r["success"] is False
