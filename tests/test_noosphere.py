from __future__ import annotations

import pytest
from ciel.noosphere.core import (
    SourceType, ContentType, SourceResponse, SourceRequest,
    RateLimiter, RetryPolicy, WebCrawler, ApiManager,
    FederatedLearning, OSINTSource, NoosphereEngine,
)


class TestSourceType:
    def test_values(self):
        assert SourceType.WEB.value == "web"
        assert SourceType.API.value == "api"
        assert SourceType.SCIENTIFIC.value == "scientific"
        assert SourceType.OSINT.value == "osint"
        assert SourceType.FEDERATED.value == "federated"


class TestContentType:
    def test_values(self):
        assert ContentType.TEXT.value == "text"
        assert ContentType.JSON.value == "json"
        assert ContentType.HTML.value == "html"


class TestSourceResponse:
    def test_create(self):
        r = SourceResponse(
            id="r1", source="test", source_type=SourceType.WEB, content="data",
        )
        assert r.id == "r1"
        assert r.source == "test"
        assert r.status_code == 200

    def test_successful(self):
        r = SourceResponse(id="r1", source="x", source_type=SourceType.WEB, content="", status_code=200)
        assert r.successful() is True
        r.status_code = 404
        assert r.successful() is False

    def test_defaults(self):
        r = SourceResponse(id="r1", source="x", source_type=SourceType.WEB, content="")
        assert r.content_type == ContentType.TEXT
        assert r.latency_ms == 0.0


class TestSourceRequest:
    def test_create(self):
        req = SourceRequest(url="https://example.com")
        assert req.url == "https://example.com"
        assert req.method == "GET"
        assert req.timeout_s == 10.0

    def test_defaults(self):
        req = SourceRequest(url="x")
        assert req.retry_count == 0
        assert req.body is None


class TestRateLimiter:
    def test_allow(self):
        limiter = RateLimiter(max_per_window=5, window_s=60.0)
        for _ in range(5):
            assert limiter.allow() is True
        assert limiter.allow() is False

    def test_allow_after_reset(self):
        limiter = RateLimiter(max_per_window=2, window_s=60.0)
        limiter.allow()
        limiter.allow()
        assert limiter.allow() is False
        limiter.reset()
        assert limiter.allow() is True

    def test_wait_time_when_allowed(self):
        limiter = RateLimiter(max_per_window=10, window_s=60.0)
        assert limiter.wait_time() == 0.0

    def test_reset(self):
        limiter = RateLimiter(max_per_window=1, window_s=60.0)
        limiter.allow()
        limiter.reset()
        assert limiter.allow() is True


class TestRetryPolicy:
    def test_delay_exponential(self):
        policy = RetryPolicy(base_delay_s=1.0, jitter=False)
        d0 = policy.delay(0)
        d1 = policy.delay(1)
        d2 = policy.delay(2)
        assert d0 == 1.0
        assert d1 == 2.0
        assert d2 == 4.0

    def test_delay_max(self):
        policy = RetryPolicy(base_delay_s=10.0, max_delay_s=15.0, jitter=False)
        d = policy.delay(5)
        assert d == 15.0

    def test_delay_jitter(self):
        policy = RetryPolicy(base_delay_s=1.0, jitter=True)
        delays = [policy.delay(0) for _ in range(10)]
        assert any(d != 1.0 for d in delays)

    def test_should_retry(self):
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0) is True
        assert policy.should_retry(2) is True
        assert policy.should_retry(3) is False

    def test_should_retry_with_response(self):
        policy = RetryPolicy(max_retries=3)
        ok = SourceResponse(id="r", source="x", source_type=SourceType.WEB, content="", status_code=200)
        fail = SourceResponse(id="r", source="x", source_type=SourceType.WEB, content="", status_code=500)
        assert policy.should_retry(0, ok) is False
        assert policy.should_retry(0, fail) is True


class TestWebCrawler:
    def test_crawl(self):
        crawler = WebCrawler()
        resp = crawler.crawl("https://example.com")
        assert resp.source == "https://example.com"
        assert resp.source_type == SourceType.WEB

    def test_crawl_count(self):
        crawler = WebCrawler()
        assert crawler.crawl_count() == 0
        crawler.crawl("https://a.com")
        crawler.crawl("https://b.com")
        assert crawler.crawl_count() == 2

    def test_crawl_rate_limited(self):
        crawler = WebCrawler(rate_limiter=RateLimiter(max_per_window=1, window_s=60.0))
        crawler.crawl("https://x.com")
        resp = crawler.crawl("https://y.com")
        assert resp.status_code == 429

    def test_block_domain(self):
        crawler = WebCrawler()
        crawler.block_domain("evil.com")
        resp = crawler.crawl("https://evil.com/page")
        assert resp.status_code == 403

    def test_unblock_domain(self):
        crawler = WebCrawler()
        crawler.block_domain("evil.com")
        crawler.unblock_domain("evil.com")
        resp = crawler.crawl("https://evil.com/page")
        assert resp.status_code != 403


class TestApiManager:
    def test_register_and_call(self):
        mgr = ApiManager()
        mgr.register_endpoint("status", "https://api.example.com/status")
        resp = mgr.call("status")
        assert resp.source_type == SourceType.API

    def test_call_unregistered(self):
        mgr = ApiManager()
        resp = mgr.call("nonexistent")
        assert resp.status_code == 404

    def test_call_count(self):
        mgr = ApiManager()
        mgr.register_endpoint("e1", "https://x.com/e1")
        mgr.register_endpoint("e2", "https://x.com/e2")
        mgr.call("e1")
        mgr.call("e2")
        assert mgr.call_count() == 2

    def test_call_rate_limited(self):
        mgr = ApiManager(rate_limiter=RateLimiter(max_per_window=1, window_s=60.0))
        mgr.register_endpoint("e", "https://x.com/e")
        mgr.call("e")
        resp = mgr.call("e")
        assert resp.status_code == 429


class TestFederatedLearning:
    def test_init_weights(self):
        fl = FederatedLearning()
        fl.init_weights(5)
        assert len(fl.get_weights()) == 5

    def test_round(self):
        fl = FederatedLearning(n_clients=10, fraction_fit=0.5)
        fl.init_weights(3)
        result = fl.round()
        assert result["round"] == 1
        assert len(result["clients_selected"]) >= 1

    def test_convergence(self):
        fl = FederatedLearning(n_clients=3, fraction_fit=1.0)
        fl.init_weights(2)
        fl.round()
        fl.round()
        fl.round()
        assert fl.current_round() == 3

    def test_no_convergence_before_round(self):
        fl = FederatedLearning()
        result = fl.round()
        assert result is not None


class TestOSINTSource:
    def test_collect(self):
        src = OSINTSource("twitter")
        resp = src.collect("#ciel")
        assert resp.source == "twitter"
        assert resp.source_type == SourceType.OSINT
        assert "#ciel" in resp.content

    def test_collect_batch(self):
        src = OSINTSource("reddit")
        responses = src.collect_batch(["q1", "q2", "q3"])
        assert len(responses) == 3

    def test_collected_count(self):
        src = OSINTSource("news")
        assert src.collected_count() == 0
        src.collect("query")
        assert src.collected_count() == 1

    def test_clear(self):
        src = OSINTSource("src")
        src.collect("x")
        src.clear()
        assert src.collected_count() == 0


class TestNoosphereEngine:
    def test_create(self):
        ns = NoosphereEngine()
        assert ns.web_crawler is not None
        assert ns.api_manager is not None

    def test_crawl(self):
        ns = NoosphereEngine()
        resp = ns.crawl("https://example.com")
        assert resp.source == "https://example.com"

    def test_api_call_unregistered(self):
        ns = NoosphereEngine()
        resp = ns.api_call("unknown")
        assert resp.status_code == 404

    def test_api_call_registered(self):
        ns = NoosphereEngine()
        ns.api_manager.register_endpoint("test", "https://api.test.com/v1")
        resp = ns.api_call("test")
        assert resp.status_code == 200

    def test_federated_round(self):
        ns = NoosphereEngine()
        result = ns.federated_round()
        assert result["round"] == 1

    def test_osint_source(self):
        ns = NoosphereEngine()
        src = ns.add_osint_source("github")
        assert src.name == "github"
        assert ns.get_osint_source("github") is src

    def test_osint_collect(self):
        ns = NoosphereEngine()
        ns.add_osint_source("twitter")
        resp = ns.osint_collect("twitter", "query")
        assert resp is not None
        assert resp.successful() is True

    def test_osint_collect_missing_source(self):
        ns = NoosphereEngine()
        resp = ns.osint_collect("nonexistent", "q")
        assert resp is None

    def test_get_stats(self):
        ns = NoosphereEngine()
        ns.crawl("https://x.com")
        ns.add_osint_source("src1")
        ns.osint_collect("src1", "q")
        stats = ns.get_stats()
        assert stats["crawl_count"] == 1
        assert stats["osint_sources"] == ["src1"]

    def test_process_crawl(self):
        ns = NoosphereEngine()
        result = ns.process({"action": "crawl", "url": "https://x.com"})
        assert result["success"] is True
        assert result["action"] == "crawl"

    def test_process_api(self):
        ns = NoosphereEngine()
        ns.api_manager.register_endpoint("e", "https://api.x.com")
        result = ns.process({"action": "api", "endpoint": "e"})
        assert result["action"] == "api"

    def test_process_federated(self):
        ns = NoosphereEngine()
        result = ns.process({"action": "federated"})
        assert result["success"] is True
        assert result["action"] == "federated"

    def test_process_osint(self):
        ns = NoosphereEngine()
        ns.add_osint_source("src")
        result = ns.process({"action": "osint", "source": "src", "query": "data"})
        assert result["success"] is True
        assert result["action"] == "osint"

    def test_process_osint_missing(self):
        ns = NoosphereEngine()
        result = ns.process({"action": "osint", "source": "nonexistent", "query": "x"})
        assert result["success"] is False

    def test_process_unknown_action(self):
        ns = NoosphereEngine()
        result = ns.process({"action": "unknown"})
        assert result["success"] is False

    def test_process_bad_input(self):
        ns = NoosphereEngine()
        result = ns.process("bad")
        assert result["success"] is False
