from __future__ import annotations

import pytest
from ciel.economy.core import EconomyEngine


class TestResource:
    def test_create(self):
        r = Resource(ResourceType.ELECTRICITY, 10.0, "kWh")
        assert r.rtype == ResourceType.ELECTRICITY
        assert r.amount == 10.0

    def test_add_same_type(self):
        a = Resource(ResourceType.DATA, 5.0)
        b = Resource(ResourceType.DATA, 3.0)
        c = a + b
        assert c.amount == 8.0

    def test_add_different_type(self):
        a = Resource(ResourceType.DATA, 1.0)
        b = Resource(ResourceType.COMPUTE, 1.0)
        with pytest.raises(ValueError):
            _ = a + b


class TestBid:
    def test_defaults(self):
        bid = Bid(module_id="m1")
        assert bid.expected_utility == 0.0
        assert bid.urgency == 0.0

    def test_priority(self):
        bid = Bid("m1", expected_utility=0.8, urgency=0.9, cost=0.1)
        assert bid.priority() == pytest.approx(7.2)

    def test_priority_zero_cost(self):
        bid = Bid("m1", cost=0.0)
        assert bid.priority() == 0.0


class TestStoragePool:
    def test_create(self):
        p = StoragePool(StorageTier.RAM, capacity=100.0)
        assert p.available() == 100.0

    def test_allocate(self):
        p = StoragePool(StorageTier.RAM, capacity=100.0)
        assert p.allocate(30.0) is True
        assert p.used == 30.0
        assert p.available() == 70.0

    def test_allocate_insufficient(self):
        p = StoragePool(StorageTier.RAM, capacity=10.0)
        assert p.allocate(20.0) is False
        assert p.used == 0.0

    def test_free(self):
        p = StoragePool(StorageTier.RAM, capacity=100.0)
        p.allocate(50.0)
        p.free(20.0)
        assert p.used == 30.0

    def test_utilization(self):
        p = StoragePool(StorageTier.CACHE, capacity=10.0)
        assert p.utilization() == 0.0
        p.allocate(5.0)
        assert p.utilization() == 0.5


class TestMetabolism:
    def test_create(self):
        m = Metabolism()
        assert m.bmr == 1.0
        assert len(m.pools) == 4

    def test_ingest(self):
        m = Metabolism()
        m.ingest(Resource(ResourceType.ELECTRICITY, 5.0))
        assert m._intake[ResourceType.ELECTRICITY] == 5.0

    def test_expend(self):
        m = Metabolism()
        m.ingest(Resource(ResourceType.DATA, 10.0))
        assert m.expend(Resource(ResourceType.DATA, 4.0)) is True
        assert m._intake[ResourceType.DATA] == 6.0

    def test_expend_insufficient(self):
        m = Metabolism()
        assert m.expend(Resource(ResourceType.COMPUTE, 1.0)) is False

    def test_store_and_retrieve(self):
        m = Metabolism()
        assert m.store(StorageTier.RAM, 50.0) is True
        assert m.pools[StorageTier.RAM].used == 50.0
        assert m.retrieve(StorageTier.RAM, 20.0) is True
        assert m.pools[StorageTier.RAM].used == 30.0

    def test_tick(self):
        m = Metabolism()
        m.store(StorageTier.CACHE, 5.0)
        result = m.tick()
        assert "bmr_cost" in result
        assert m.pools[StorageTier.CACHE].used < 5.0

    def test_get_stats(self):
        m = Metabolism()
        stats = m.get_stats()
        assert "intake" in stats
        assert "pools" in stats
        assert "bmr" in stats


class TestVickreyAuction:
    def test_submit(self):
        a = VickreyAuction()
        a.submit(Bid("m1", expected_utility=0.9, urgency=0.8, cost=0.1))
        assert len(a._bids) == 1

    def test_clear_single(self):
        a = VickreyAuction()
        a.submit(Bid("m1", expected_utility=0.5, urgency=0.5, cost=0.2))
        results = a.clear()
        assert len(results) == 1
        assert results[0]["winner"] == "m1"

    def test_clear_priority(self):
        a = VickreyAuction()
        a.submit(Bid("low", expected_utility=0.2, urgency=0.2, cost=0.5))
        a.submit(Bid("high", expected_utility=0.9, urgency=0.9, cost=0.1))
        results = a.clear()
        assert results[0]["winner"] == "high"

    def test_clear_empty(self):
        a = VickreyAuction()
        assert a.clear() == []

    def test_history(self):
        a = VickreyAuction()
        assert a.history() == []
        a.submit(Bid("m1", 0.5, 0.5, 0.1))
        a.clear()
        assert len(a.history()) == 1


class TestShapleyValue:
    def test_empty(self):
        assert ShapleyValue.compute({}) == {}

    def test_compute(self):
        contribs = {
            "a": [1.0, 2.0, 3.0],
            "b": [0.5, 1.0, 1.5],
        }
        values = ShapleyValue.compute(contribs)
        assert "a" in values
        assert "b" in values
        assert values["a"] > 0


class TestToken:
    def test_create(self):
        t = Token("TEST", 1000.0)
        assert t.total_supply == 1000.0
        assert t.circulating == 0.0

    def test_mint(self):
        t = Token()
        assert t.mint("alice", 500.0) is True
        assert t.balance("alice") == 500.0
        assert t.circulating == 500.0

    def test_mint_exceeds_supply(self):
        t = Token("T", total_supply=100.0)
        assert t.mint("a", 200.0) is False

    def test_transfer(self):
        t = Token()
        t.mint("alice", 100.0)
        assert t.transfer("alice", "bob", 40.0) is True
        assert t.balance("alice") == 60.0
        assert t.balance("bob") == 40.0

    def test_transfer_insufficient(self):
        t = Token()
        t.mint("alice", 10.0)
        assert t.transfer("alice", "bob", 20.0) is False

    def test_supply_remaining(self):
        t = Token("T", 100.0)
        t.mint("a", 30.0)
        assert t.supply_remaining() == 70.0


class TestMarket:
    def test_ask_bid(self):
        m = Market()
        m.ask("compute", 5.0)
        m.bid("compute", 6.0)
        trade = m.trade("compute")
        assert trade is not None
        assert trade["item"] == "compute"
        assert trade["price"] == 5.5

    def test_trade_no_match(self):
        m = Market()
        m.ask("cpu", 10.0)
        m.bid("cpu", 5.0)
        assert m.trade("cpu") is None

    def test_trade_nonexistent(self):
        m = Market()
        assert m.trade("nonexistent") is None

    def test_market_price(self):
        m = Market()
        assert m.market_price("x") is None
        m.ask("x", 3.0)
        m.bid("x", 4.0)
        m.trade("x")
        assert m.market_price("x") == 3.5  # average of ask+bid

    def test_trade_count(self):
        m = Market()
        assert m.trade_count() == 0
        m.ask("a", 1.0)
        m.bid("a", 2.0)
        m.trade("a")
        assert m.trade_count() == 1


class TestEconomyEngine:
    def test_create(self):
        e = EconomyEngine()
        assert e.metabolism is not None
        assert e.auction is not None
        assert e.token is not None

    def test_register_agent(self):
        e = EconomyEngine()
        e.register_agent("agent1", 500.0)
        assert e.token.balance("agent1") == 500.0

    def test_submit_bid(self):
        e = EconomyEngine()
        assert e.submit_bid("m1", 0.9, 0.8, 0.1) is True

    def test_clear_auction(self):
        e = EconomyEngine()
        e.submit_bid("m1", 0.5, 0.5, 0.2)
        results = e.clear_auction()
        assert len(results) == 1

    def test_compute_shapley(self):
        e = EconomyEngine()
        values = e.compute_shapley({"a": [1.0], "b": [2.0]})
        assert "a" in values

    def test_ingest(self):
        e = EconomyEngine()
        e.ingest("electricity", 10.0)
        assert e.metabolism._intake[ResourceType.ELECTRICITY] == 10.0

    def test_store(self):
        e = EconomyEngine()
        assert e.store("ram", 50.0) is True
        assert e.store("cache", 5.0) is True
        assert e.store("invalid", 1.0) is False

    def test_trade(self):
        e = EconomyEngine()
        result = e.trade("compute", 5.0, "ask")
        assert result is None
        result = e.trade("compute", 6.0, "bid")
        assert result is not None

    def test_transfer_token(self):
        e = EconomyEngine()
        e.register_agent("a", 100.0)
        e.register_agent("b", 0.0)
        assert e.transfer_token("a", "b", 30.0) is True
        assert e.token.balance("b") == 30.0

    def test_get_stats(self):
        e = EconomyEngine()
        stats = e.get_stats()
        assert "metabolism" in stats
        assert "auctions" in stats
        assert "agents" in stats
        assert "token_circulating" in stats
        assert "trades" in stats

    def test_process_register(self):
        e = EconomyEngine()
        r = e.process({"action": "register", "agent": "x", "balance": 200.0})
        assert r["success"] is True
        assert r["balance"] == 200.0

    def test_process_bid(self):
        e = EconomyEngine()
        r = e.process({"action": "bid", "module": "m1", "utility": 0.8, "urgency": 0.7, "cost": 0.2})
        assert r["success"] is True

    def test_process_clear(self):
        e = EconomyEngine()
        e.process({"action": "bid"})
        r = e.process({"action": "clear"})
        assert r["success"] is True
        assert len(r["results"]) == 1

    def test_process_shapley(self):
        e = EconomyEngine()
        r = e.process({"action": "shapley", "contributions": {"a": [1.0], "b": [2.0]}})
        assert r["success"] is True

    def test_process_ingest(self):
        e = EconomyEngine()
        r = e.process({"action": "ingest", "type": "data", "amount": 5.0})
        assert r["success"] is True

    def test_process_store(self):
        e = EconomyEngine()
        r = e.process({"action": "store", "tier": "nvme", "amount": 200.0})
        assert r["success"] is True
        assert r["stored"] is True

    def test_process_trade(self):
        e = EconomyEngine()
        e.process({"action": "trade", "item": "cpu", "price": 5.0, "side": "ask"})
        r = e.process({"action": "trade", "item": "cpu", "price": 6.0, "side": "bid"})
        assert r["success"] is True
        assert r["trade"] is not None

    def test_process_transfer(self):
        e = EconomyEngine()
        e.process({"action": "register", "agent": "a", "balance": 100.0})
        e.process({"action": "register", "agent": "b", "balance": 0.0})
        r = e.process({"action": "transfer", "sender": "a", "recipient": "b", "amount": 50.0})
        assert r["success"] is True
        assert r["ok"] is True

    def test_process_tick(self):
        e = EconomyEngine()
        e.process({"action": "store", "tier": "cache", "amount": 3.0})
        r = e.process({"action": "tick"})
        assert r["success"] is True
        assert "result" in r

    def test_process_stats(self):
        e = EconomyEngine()
        r = e.process({"action": "stats"})
        assert r["success"] is True

    def test_process_bad_action(self):
        e = EconomyEngine()
        r = e.process({"action": "nonexistent"})
        assert r["success"] is False

    def test_process_bad_input(self):
        e = EconomyEngine()
        r = e.process("bad")
        assert r["success"] is False
