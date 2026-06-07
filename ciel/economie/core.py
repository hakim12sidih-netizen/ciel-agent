from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass(slots=True)
class Good:
    id: str
    name: str
    quantity: float = 0.0
    base_value: float = 1.0


@dataclass(slots=True)
class Resource:
    id: str
    name: str
    renewable: bool = True
    regeneration_rate: float = 0.01
    current_stock: float = 100.0
    max_stock: float = 100.0

    def tick(self) -> None:
        if self.renewable and self.current_stock < self.max_stock:
            self.current_stock = min(self.max_stock, self.current_stock + self.regeneration_rate)

    def consume(self, amount: float) -> float:
        taken = min(amount, self.current_stock)
        self.current_stock -= taken
        return taken


@dataclass(slots=True)
class Currency:
    id: str
    name: str
    symbol: str = "$"
    total_supply: float = 0.0


class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(slots=True)
class Order:
    agent_id: str
    order_type: OrderType
    good_id: str
    quantity: float
    price: float
    timestamp: float = 0.0


@dataclass(slots=True)
class Trade:
    buyer_id: str
    seller_id: str
    good_id: str
    quantity: float
    price: float
    timestamp: float = 0.0


class OrderBook:
    def __init__(self) -> None:
        self.bids: list[Order] = []  # buy orders, sorted price desc
        self.asks: list[Order] = []  # sell orders, sorted price asc

    def add_order(self, order: Order) -> list[Trade]:
        trades: list[Trade] = []
        if order.order_type == OrderType.BUY:
            self.asks.sort(key=lambda o: o.price)
            remaining = order.quantity
            matched: list[Order] = []
            for ask in self.asks:
                if remaining <= 0:
                    break
                if ask.price <= order.price:
                    qty = min(remaining, ask.quantity)
                    trades.append(Trade(
                        buyer_id=order.agent_id, seller_id=ask.agent_id,
                        good_id=order.good_id, quantity=qty, price=ask.price,
                    ))
                    ask.quantity -= qty
                    remaining -= qty
                    if ask.quantity <= 0:
                        matched.append(ask)
            self.asks = [o for o in self.asks if o not in matched]
            if remaining > 0:
                self.bids.append(Order(order.agent_id, OrderType.BUY, order.good_id, remaining, order.price))
            self.bids.sort(key=lambda o: o.price, reverse=True)
        else:
            self.bids.sort(key=lambda o: o.price, reverse=True)
            remaining = order.quantity
            matched = []
            for bid in self.bids:
                if remaining <= 0:
                    break
                if bid.price >= order.price:
                    qty = min(remaining, bid.quantity)
                    trades.append(Trade(
                        buyer_id=bid.agent_id, seller_id=order.agent_id,
                        good_id=order.good_id, quantity=qty, price=bid.price,
                    ))
                    bid.quantity -= qty
                    remaining -= qty
                    if bid.quantity <= 0:
                        matched.append(bid)
            self.bids = [o for o in self.bids if o not in matched]
            if remaining > 0:
                self.asks.append(Order(order.agent_id, OrderType.SELL, order.good_id, remaining, order.price))
            self.asks.sort(key=lambda o: o.price)
        return trades

    def spread(self) -> float:
        if not self.bids or not self.asks:
            return 0.0
        return self.asks[0].price - self.bids[0].price

    def mid_price(self) -> float:
        if not self.bids or not self.asks:
            return 0.0
        return (self.bids[0].price + self.asks[0].price) / 2.0


class UtilityFunction:
    def __init__(self, func: Callable[[dict[str, float]], float] | None = None):
        self.func = func or (lambda g: sum(g.values()) / max(len(g), 1))

    def evaluate(self, goods: dict[str, float]) -> float:
        return self.func(goods)

    @staticmethod
    def cobb_douglas(weights: dict[str, float]) -> UtilityFunction:
        def cd(goods: dict[str, float]) -> float:
            val = 1.0
            for gid, qty in goods.items():
                w = weights.get(gid, 1.0)
                if qty > 0:
                    val *= qty ** w
            return val
        return UtilityFunction(cd)

    @staticmethod
    def ces(weights: dict[str, float], rho: float = 0.5) -> UtilityFunction:
        def ces_func(goods: dict[str, float]) -> float:
            total = sum(weights.get(gid, 1.0) * (qty ** rho) for gid, qty in goods.items())
            return total ** (1.0 / rho) if total > 0 else 0.0
        return UtilityFunction(ces_func)


class ValueSystem:
    def __init__(self, values: dict[str, float] | None = None):
        self.values: dict[str, float] = values or {}
        self.priority: list[str] = []

    def set_priority(self, ordered_keys: list[str]) -> None:
        self.priority = ordered_keys
        self.values = {k: self.values.get(k, 1.0) for k in ordered_keys}

    def score(self, bundle: dict[str, float]) -> float:
        s = 0.0
        for k, v in bundle.items():
            weight = self.values.get(k, 1.0)
            s += v * weight * (1.0 + 0.1 * (len(self.priority) - self.priority.index(k)) if k in self.priority else 0.0)
        return s

    def add_value(self, key: str, weight: float) -> None:
        self.values[key] = weight
        if key not in self.priority:
            self.priority.append(key)


class PricingMechanism:
    def __init__(self, learning_rate: float = 0.1):
        self.lr = learning_rate
        self.prices: dict[str, float] = {}

    def update(self, good_id: str, demand: float, supply: float) -> float:
        current = self.prices.get(good_id, 1.0)
        if supply > 0:
            ratio = demand / supply
        else:
            ratio = 2.0
        new_price = current * (1.0 + self.lr * (ratio - 1.0))
        new_price = max(0.01, new_price)
        self.prices[good_id] = new_price
        return new_price

    def price(self, good_id: str) -> float:
        return self.prices.get(good_id, 1.0)


class ScarcityModel:
    def __init__(self, elasticity: float = 1.0):
        self.elasticity = elasticity

    def scarcity_score(self, available: float, total_capacity: float) -> float:
        if total_capacity <= 0:
            return 1.0
        ratio = available / total_capacity
        return (1.0 - ratio) ** self.elasticity

    def price_premium(self, available: float, total_capacity: float) -> float:
        return 1.0 + self.scarcity_score(available, total_capacity)


@dataclass(slots=True)
class EconomicAgent:
    id: str
    currency: float = 100.0
    inventory: dict[str, float] = field(default_factory=dict)
    utility_fn: UtilityFunction | None = None
    value_system: ValueSystem | None = None

    def utility(self) -> float:
        u = 0.0
        if self.utility_fn:
            u = self.utility_fn.evaluate(self.inventory)
        if self.value_system:
            u += self.value_system.score(self.inventory)
        return u

    def produce(self, good_id: str, amount: float, inputs: dict[str, float] | None = None) -> None:
        if inputs:
            for iid, qty in inputs.items():
                current = self.inventory.get(iid, 0.0)
                if current < qty:
                    return
                self.inventory[iid] = current - qty
        self.inventory[good_id] = self.inventory.get(good_id, 0.0) + amount

    def consume(self, good_id: str, amount: float) -> bool:
        current = self.inventory.get(good_id, 0.0)
        if current < amount:
            return False
        self.inventory[good_id] = current - amount
        return True


class ProductionFunction:
    def __init__(self, output_good: str, coefficients: dict[str, float], output_rate: float = 1.0):
        self.output_good = output_good
        self.coefficients = coefficients
        self.output_rate = output_rate

    def can_produce(self, inputs: dict[str, float]) -> bool:
        return all(inputs.get(k, 0.0) >= v for k, v in self.coefficients.items())

    def produce(self, inputs: dict[str, float]) -> tuple[str, float]:
        if not self.can_produce(inputs):
            return self.output_good, 0.0
        return self.output_good, self.output_rate


class Market:
    def __init__(self, name: str = "marché"):
        self.name = name
        self.order_book = OrderBook()
        self.agents: dict[str, EconomicAgent] = {}
        self.goods: dict[str, Good] = {}
        self.currencies: dict[str, Currency] = {}
        self.trades: list[Trade] = []
        self.pricing = PricingMechanism()
        self.scarcity = ScarcityModel()
        self.history: list[dict[str, float]] = []
        self._tick = 0

    def add_agent(self, agent: EconomicAgent) -> None:
        self.agents[agent.id] = agent

    def add_good(self, good: Good) -> None:
        self.goods[good.id] = good

    def add_currency(self, currency: Currency) -> None:
        self.currencies[currency.id] = currency

    def submit_order(self, order: Order) -> list[Trade]:
        trades = self.order_book.add_order(order)
        self.trades.extend(trades)
        for t in trades:
            buyer = self.agents.get(t.buyer_id)
            seller = self.agents.get(t.seller_id)
            if buyer and seller:
                buyer.currency -= t.quantity * t.price
                buyer.inventory[t.good_id] = buyer.inventory.get(t.good_id, 0.0) + t.quantity
                seller.currency += t.quantity * t.price
                seller.inventory[t.good_id] = seller.inventory.get(t.good_id, 0.0) - t.quantity
        return trades

    def tick(self) -> dict[str, Any]:
        self._tick += 1
        for good in self.goods.values():
            total_demand = sum(a.inventory.get(good.id, 0.0) for a in self.agents.values())
            total_supply = good.quantity
            self.pricing.update(good.id, total_demand, max(total_supply, 1))
        stats = {
            "tick": self._tick,
            "n_trades": len(self.trades),
            "volume": sum(t.quantity for t in self.trades),
            "spread": self.order_book.spread(),
            "mid_price": self.order_book.mid_price(),
        }
        self.history.append(stats)
        return stats


class EconomicLoop:
    """Boucle économique — simule cycles production/échange/consommation."""

    def __init__(self, market: Market | None = None):
        self.market = market or Market()
        self.resources: list[Resource] = []
        self._running = False

    def add_resource(self, resource: Resource) -> None:
        self.resources.append(resource)

    def step(self) -> dict[str, Any]:
        for r in self.resources:
            r.tick()
        stats = self.market.tick()
        for agent in self.market.agents.values():
            if agent.currency < 1.0:
                agent.currency += 10.0  # basic income
        stats["agents"] = len(self.market.agents)
        stats["goods"] = len(self.market.goods)
        return stats

    def run(self, n_steps: int = 10) -> list[dict[str, Any]]:
        self._running = True
        results = []
        for _ in range(n_steps):
            if not self._running:
                break
            results.append(self.step())
        return results

    def stop(self) -> None:
        self._running = False

    def gini_coefficient(self) -> float:
        wealths = sorted(a.currency for a in self.market.agents.values())
        n = len(wealths)
        if n <= 1:
            return 0.0
        cum = 0.0
        for i, w in enumerate(wealths):
            cum += (2 * (i + 1) - n - 1) * w
        mean = sum(wealths) / n
        if mean == 0:
            return 0.0
        return cum / (n * n * mean)
