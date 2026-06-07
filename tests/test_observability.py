"""
Tests unitaires pour l'observability (Counter/Gauge/Histogram/Metrics).
"""
from __future__ import annotations

import math

import pytest

from ciel.core.observability import Counter, Gauge, Histogram, Metrics


class TestCounter:
    def test_basic_increment(self) -> None:
        c = Counter("test")
        assert c.value == 0
        c.inc()
        assert c.value == 1
        c.inc(5)
        assert c.value == 6

    def test_cannot_decrement(self) -> None:
        c = Counter("test")
        c.inc(10)
        with pytest.raises(ValueError):
            c.inc(-1)

    def test_reset(self) -> None:
        c = Counter("test")
        c.inc(100)
        c.reset()
        assert c.value == 0

    def test_invalid_name(self) -> None:
        with pytest.raises(ValueError):
            Counter("123_invalid")  # commence par chiffre
        with pytest.raises(ValueError):
            Counter("with-dash")

    def test_to_dict(self) -> None:
        c = Counter("requests_total", help_text="Total requests", labels={"env": "prod"})
        c.inc(42)
        d = c.to_dict()
        assert d["type"] == "counter"
        assert d["name"] == "requests_total"
        assert d["value"] == 42
        assert d["labels"] == {"env": "prod"}


class TestGauge:
    def test_basic_set(self) -> None:
        g = Gauge("temp")
        g.set(42.5)
        assert g.value == 42.5

    def test_inc_dec(self) -> None:
        g = Gauge("depth")
        g.inc(5)
        g.inc(3)
        assert g.value == 8
        g.dec(2)
        assert g.value == 6

    def test_nan_inf_rejected(self) -> None:
        g = Gauge("x")
        with pytest.raises(ValueError):
            g.set(float("nan"))
        with pytest.raises(ValueError):
            g.set(float("inf"))

    def test_can_decrement(self) -> None:
        # Contrairement au Counter, Gauge peut descendre
        g = Gauge("x")
        g.set(10)
        g.dec(15)
        assert g.value == -5

    def test_to_dict(self) -> None:
        g = Gauge("memory_mb", help_text="RSS in MB")
        g.set(256)
        d = g.to_dict()
        assert d["type"] == "gauge"
        assert d["value"] == 256


class TestHistogram:
    def test_basic_observe(self) -> None:
        h = Histogram("latency_ms", buckets=(1, 5, 10, 100))
        h.observe(0.5)
        h.observe(7)
        h.observe(50)
        assert h.count == 3
        assert h.sum == pytest.approx(57.5)

    def test_buckets_cumulative(self) -> None:
        h = Histogram("x", buckets=(1, 5, 10))
        h.observe(0.5)   # <=1, <=5, <=10
        h.observe(3)     # <=5, <=10
        h.observe(7)     # <=10
        d = h.to_dict()
        # Cumulatif : chaque bucket compte toutes les observations <= sa borne
        assert d["buckets"][1] == 1   # <=1 : 0.5
        assert d["buckets"][5] == 2   # <=5 : 0.5, 3
        assert d["buckets"][10] == 3  # <=10 : 0.5, 3, 7

    def test_quantile(self) -> None:
        h = Histogram("x", buckets=(10, 20, 30))
        for v in [1, 2, 3, 4, 5]:
            h.observe(v)
        p50 = h.quantile(0.5)
        # 5 observations, p50 = index 2.5
        assert p50 is not None

    def test_quantile_empty(self) -> None:
        h = Histogram("x")
        assert h.quantile(0.5) is None

    def test_invalid_quantile(self) -> None:
        h = Histogram("x")
        h.observe(1)
        with pytest.raises(ValueError):
            h.quantile(0)
        with pytest.raises(ValueError):
            h.quantile(1.0)
        with pytest.raises(ValueError):
            h.quantile(-0.1)

    def test_nan_observation_ignored(self) -> None:
        h = Histogram("x")
        h.observe(float("nan"))
        assert h.count == 0

    def test_invalid_buckets_rejected(self) -> None:
        with pytest.raises(ValueError):
            Histogram("x", buckets=())  # vide
        with pytest.raises(ValueError):
            Histogram("x", buckets=(0, 5))  # bucket à 0
        with pytest.raises(ValueError):
            Histogram("x", buckets=(-1, 5))  # bucket négatif

    def test_to_dict_includes_percentiles(self) -> None:
        h = Histogram("x", buckets=(1, 5, 10))
        for v in [0.1, 0.5, 1, 3, 7]:
            h.observe(v)
        d = h.to_dict()
        assert d["p50"] is not None
        assert d["p95"] is not None
        assert d["p99"] is not None


class TestMetrics:
    def test_counter_singleton(self) -> None:
        m = Metrics()
        c1 = m.get_counter("requests")
        c2 = m.get_counter("requests")
        assert c1 is c2  # même instance

    def test_gauge_singleton(self) -> None:
        m = Metrics()
        g1 = m.get_gauge("depth")
        g2 = m.get_gauge("depth")
        assert g1 is g2

    def test_histogram_singleton(self) -> None:
        m = Metrics()
        h1 = m.get_histogram("latency")
        h2 = m.get_histogram("latency")
        assert h1 is h2

    def test_snapshot(self) -> None:
        m = Metrics()
        m.get_counter("req_total").inc(5)
        m.get_gauge("temp").set(42)
        m.get_histogram("lat").observe(10)
        snap = m.snapshot()
        assert snap["req_total"] == 5
        assert snap["temp"] == 42
        assert snap["lat_count"] == 1

    def test_full_snapshot(self) -> None:
        m = Metrics()
        m.get_counter("c").inc(3)
        m.get_gauge("g").set(10)
        m.get_histogram("h").observe(1)
        full = m.full_snapshot()
        assert "c" in full["counters"]
        assert "g" in full["gauges"]
        assert "h" in full["histograms"]

    def test_reset(self) -> None:
        m = Metrics()
        m.get_counter("x").inc(10)
        m.get_gauge("y").set(20)
        m.reset()
        assert m.snapshot() == {}
