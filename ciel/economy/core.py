from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResourceType(Enum):
    ELECTRICITY = "electricity"
    DATA = "data"
    ATTENTION = "attention"
    MEMORY = "memory"
    COMPUTE = "compute"


@dataclass(slots=True)
class Resource:
    rtype: ResourceType
    amount: float = 0.0
    unit: str = ""

    def __add__(self, other: Resource) -> Resource:
        if self.rtype != other.rtype:
            raise ValueError(f"cannot add {self.rtype} and {other.rtype}")
        return Resource(self.rtype, self.amount + other.amount, self.unit)


@dataclass(slots=True)
class Bid:
    module_id: str
    expected_utility: float = 0.0
    urgency: float = 0.0
    cost: float = 0.0
    resource: Resource | None = None

    def priority(self) -> float:
        if self.cost <= 0:
            return 0.0
        return self.expected_utility * self.urgency / self.cost


class StorageTier(Enum):
    CACHE = "cache"
    RAM = "ram"
    NVME = "nvme"
    DNA = "dna"


@dataclass(slots=True)
class StoragePool:
    tier: StorageTier
    capacity: float = 0.0
    used: float = 0.0

    def available(self) -> float:
        return max(0.0, self.capacity - self.used)

    def allocate(self, amount: float) -> bool:
        if amount > self.available():
            return False
        self.used += amount
        return True

    def free(self, amount: float) -> None:
        self.used = max(0.0, self.used - amount)

    def utilization(self) -> float:
        return self.used / max(self.capacity, 0.01)


class Metabolism:
    """Métabolisme computationnel — entrées, stockage, dépenses."""

    def __init__(self):
        self.pools: dict[StorageTier, StoragePool] = {
            StorageTier.CACHE: StoragePool(StorageTier.CACHE, capacity=10.0),
            StorageTier.RAM: StoragePool(StorageTier.RAM, capacity=100.0),
            StorageTier.NVME: StoragePool(StorageTier.NVME, capacity=1000.0),
            StorageTier.DNA: StoragePool(StorageTier.DNA, capacity=10000.0),
        }
        self._intake: dict[ResourceType, float] = Counter()
        self._expenditure: dict[ResourceType, float] = Counter()
        self.bmr: float = 1.0

    def ingest(self, resource: Resource) -> None:
        self._intake[resource.rtype] += resource.amount

    def expend(self, resource: Resource) -> bool:
        if self._intake[resource.rtype] < resource.amount:
            return False
        self._intake[resource.rtype] -= resource.amount
        self._expenditure[resource.rtype] += resource.amount
        return True

    def store(self, tier: StorageTier, amount: float) -> bool:
        return self.pools[tier].allocate(amount)

    def retrieve(self, tier: StorageTier, amount: float) -> bool:
        if self.pools[tier].used < amount:
            return False
        self.pools[tier].free(amount)
        return True

    def tick(self) -> dict[str, float]:
        cost = self.bmr
        pool = self.pools[StorageTier.CACHE]
        if pool.used >= cost:
            pool.free(cost)
        return {"bmr_cost": cost, "cache_used": pool.used}

    def get_stats(self) -> dict[str, Any]:
        return {
            "intake": dict(self._intake),
            "expenditure": dict(self._expenditure),
            "bmr": self.bmr,
            "pools": {t.value: {"capacity": p.capacity, "used": p.used, "util": p.utilization()}
                      for t, p in self.pools.items()},
        }


class VickreyAuction:
    """Enchère de Vickrey — second-price sealed-bid."""

    def __init__(self):
        self._bids: list[Bid] = []
        self._history: list[dict[str, Any]] = []

    def submit(self, bid: Bid) -> None:
        self._bids.append(bid)

    def clear(self) -> list[dict[str, Any]]:
        if not self._bids:
            return []
        sorted_bids = sorted(self._bids, key=lambda b: b.priority(), reverse=True)
        winner = sorted_bids[0]
        price = sorted_bids[1].priority() if len(sorted_bids) > 1 else winner.cost
        result = {
            "winner": winner.module_id,
            "price": price,
            "utility": winner.expected_utility,
            "urgency": winner.urgency,
        }
        self._history.append(result)
        self._bids.clear()
        return [result]

    def history(self) -> list[dict[str, Any]]:
        return list(self._history)


class ShapleyValue:
    """Valeur de Shapley — contribution marginale moyenne."""

    @staticmethod
    def compute(contributions: dict[str, list[float]]) -> dict[str, float]:
        players = list(contributions.keys())
        n = len(players)
        if n == 0:
            return {}
        shapley: dict[str, float] = {p: 0.0 for p in players}

        from itertools import permutations
        for perm in permutations(players):
            cumulative = 0.0
            for player in perm:
                prev = cumulative
                if contributions[player]:
                    cumulative += contributions[player][-1]
                else:
                    cumulative += 0
                marginal = cumulative - prev
                shapley[player] += marginal

        total_permutations = math.factorial(n)
        for p in players:
            shapley[p] /= total_permutations
        return shapley


class Token:
    """Token — unité de valeur économique interne."""

    def __init__(self, name: str = "CIEL", total_supply: float = 1_000_000):
        self.name = name
        self.total_supply = total_supply
        self.circulating: float = 0.0
        self._balances: dict[str, float] = {}

    def mint(self, recipient: str, amount: float) -> bool:
        if self.circulating + amount > self.total_supply:
            return False
        self._balances[recipient] = self._balances.get(recipient, 0.0) + amount
        self.circulating += amount
        return True

    def transfer(self, sender: str, recipient: str, amount: float) -> bool:
        if self._balances.get(sender, 0.0) < amount:
            return False
        self._balances[sender] -= amount
        self._balances[recipient] = self._balances.get(recipient, 0.0) + amount
        return True

    def balance(self, owner: str) -> float:
        return self._balances.get(owner, 0.0)

    def supply_remaining(self) -> float:
        return self.total_supply - self.circulating


class Market:
    """Marché interne — offre, demande, prix."""

    def __init__(self):
        self._asks: dict[str, float] = {}
        self._bids: dict[str, float] = {}
        self._trades: list[dict[str, Any]] = []

    def ask(self, item: str, price: float) -> None:
        self._asks[item] = price

    def bid(self, item: str, price: float) -> None:
        self._bids[item] = price

    def trade(self, item: str) -> dict[str, Any] | None:
        if item not in self._asks or item not in self._bids:
            return None
        ask_price = self._asks[item]
        bid_price = self._bids[item]
        if bid_price < ask_price:
            return None
        price = (ask_price + bid_price) / 2
        trade = {"item": item, "price": price, "volume": 1}
        self._trades.append(trade)
        del self._asks[item]
        del self._bids[item]
        return trade

    def market_price(self, item: str) -> float | None:
        relevant = [t["price"] for t in self._trades if t["item"] == item]
        if not relevant:
            return None
        if item in self._asks:
            return self._asks[item]
        if item in self._bids:
            return self._bids[item]
        return sum(relevant) / len(relevant)

    def trade_count(self) -> int:
        return len(self._trades)


class EconomyEngine:
    """Moteur économique — métabolisme, enchères, Shapley, tokens, marché."""

    def __init__(self):
        self.metabolism = Metabolism()
        self.auction = VickreyAuction()
        self.shapley = ShapleyValue()
        self.token = Token()
        self.market = Market()
        self._agents: dict[str, float] = {}

    def register_agent(self, agent_id: str, initial_balance: float = 100.0) -> None:
        self._agents[agent_id] = initial_balance
        self.token.mint(agent_id, initial_balance)

    def submit_bid(self, module_id: str, utility: float, urgency: float, cost: float) -> bool:
        bid = Bid(module_id=module_id, expected_utility=utility, urgency=urgency, cost=cost)
        self.auction.submit(bid)
        return True

    def clear_auction(self) -> list[dict[str, Any]]:
        return self.auction.clear()

    def compute_shapley(self, contributions: dict[str, list[float]]) -> dict[str, float]:
        return self.shapley.compute(contributions)

    def ingest(self, rtype: str, amount: float) -> None:
        try:
            rt = ResourceType(rtype)
            self.metabolism.ingest(Resource(rt, amount))
        except ValueError:
            pass

    def store(self, tier: str, amount: float) -> bool:
        try:
            t = StorageTier(tier)
            return self.metabolism.store(t, amount)
        except ValueError:
            return False

    def trade(self, item: str, price: float, side: str = "ask") -> dict[str, Any] | None:
        if side == "ask":
            self.market.ask(item, price)
        else:
            self.market.bid(item, price)
        return self.market.trade(item)

    def transfer_token(self, sender: str, recipient: str, amount: float) -> bool:
        return self.token.transfer(sender, recipient, amount)

    def get_stats(self) -> dict[str, Any]:
        return {
            "metabolism": self.metabolism.get_stats(),
            "auctions": len(self.auction.history()),
            "agents": len(self._agents),
            "token_circulating": self.token.circulating,
            "token_supply_remaining": self.token.supply_remaining(),
            "trades": self.market.trade_count(),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "register":
            agent = str(data.get("agent", "anon"))
            balance = float(data.get("balance", 100.0))
            self.register_agent(agent, balance)
            return {"success": True, "action": "register", "agent": agent, "balance": balance}

        elif action == "bid":
            self.submit_bid(
                str(data.get("module", "default")),
                float(data.get("utility", 0.5)),
                float(data.get("urgency", 0.5)),
                float(data.get("cost", 0.1)),
            )
            return {"success": True, "action": "bid"}

        elif action == "clear":
            results = self.clear_auction()
            return {"success": True, "action": "clear", "results": results}

        elif action == "shapley":
            contributions = data.get("contributions", {})
            values = self.compute_shapley(contributions)
            return {"success": True, "action": "shapley", "values": values}

        elif action == "ingest":
            self.ingest(str(data.get("type", "electricity")), float(data.get("amount", 1.0)))
            return {"success": True, "action": "ingest"}

        elif action == "store":
            ok = self.store(str(data.get("tier", "cache")), float(data.get("amount", 1.0)))
            return {"success": True, "action": "store", "stored": ok}

        elif action == "trade":
            result = self.trade(
                str(data.get("item", "compute")),
                float(data.get("price", 1.0)),
                str(data.get("side", "ask")),
            )
            return {"success": True, "action": "trade", "trade": result}

        elif action == "transfer":
            ok = self.transfer_token(
                str(data.get("sender", "")),
                str(data.get("recipient", "")),
                float(data.get("amount", 0.0)),
            )
            return {"success": True, "action": "transfer", "ok": ok}

        elif action == "tick":
            result = self.metabolism.tick()
            return {"success": True, "action": "tick", "result": result}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
