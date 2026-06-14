"""
CIEL v∞.8 — DIMENSION LXIV : CIEL-ECONOMY.
Marché cognitif interne — agents commercent, négocient, prospèrent.

Concept : Économie interne basée sur les Cognitas (CG). Marchés :
Skills, Données, Compute, Agents. Règulation macro-économique par
CIEL (banque centrale). Spécialisation naturelle et innovation
via investissement en R&D.
"""
from __future__ import annotations

import math
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class CognitasAccount:
    agent_id: str
    balance: float = 1000.0
    credit_score: float = 1.0
    transactions: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"agent_id": self.agent_id,
                "balance": round(self.balance, 2),
                "credit": round(self.credit_score, 3),
                "tx_count": len(self.transactions)}


MARKET_TYPES = ("skills", "data", "compute", "agents")


@dataclass(slots=True)
class MarketOrder:
    id: str
    seller_id: str
    buyer_id: str
    market: str = "skills"
    item: str = ""
    price: float = 0.0
    timestamp: float = 0.0
    fulfilled: bool = False

    def to_dict(self) -> dict:
        return {"id": self.id, "seller": self.seller_id,
                "buyer": self.buyer_id, "market": self.market,
                "price": self.price, "fulfilled": self.fulfilled}


class EconomyEngine:
    """Moteur du marché économique cognitif interne.

    4 marchés : Skills, Données, Compute, Agents.
    Monnaie : Cognitas (CG). Règulation macro-économique.
    """

    def __init__(self):
        self.accounts: dict[str, CognitasAccount] = {}
        self.orders: list[MarketOrder] = []
        self.gdp: float = 0.0
        self.money_supply: float = 0.0
        self.inflation_rate: float = 0.0
        self.network = LeaderNetwork()
        self._init_accounts()

    def _init_accounts(self):
        for agent in ["RAPHAEL", "FORGE", "CHRONOS", "SOEI",
                       "SHION", "BENIMARU", "DIABLO"]:
            self.register_agent(agent)

    def register_agent(self, agent_id: str,
                       initial_balance: float = 1000.0) -> CognitasAccount:
        acct = CognitasAccount(agent_id=agent_id, balance=initial_balance)
        self.accounts[agent_id] = acct
        self.money_supply += initial_balance
        return acct

    def trade(self, seller_id: str, buyer_id: str,
              market: str = "skills", item: str = "",
              price: float = 10.0) -> MarketOrder | None:
        seller = self.accounts.get(seller_id)
        buyer = self.accounts.get(buyer_id)
        if not seller or not buyer:
            return None
        if buyer.balance < price:
            return None
        order = MarketOrder(
            id=f"ORD-{uuid.uuid4().hex[:12]}",
            seller_id=seller_id, buyer_id=buyer_id,
            market=market, item=item, price=price,
            timestamp=time.time(), fulfilled=True,
        )
        buyer.balance -= price
        seller.balance += price
        self.orders.append(order)
        self.gdp += price
        seller.transactions.append({"type": "sell", "price": price,
                                    "buyer": buyer_id, "market": market})
        buyer.transactions.append({"type": "buy", "price": price,
                                   "seller": seller_id, "market": market})
        return order

    def regulate(self) -> dict:
        if self.gdp > 10000 and self.money_supply > 50000:
            self.inflation_rate = min(0.1, self.inflation_rate + 0.01)
            tax = self.gdp * 0.05
            for acct in self.accounts.values():
                acct.balance *= 0.99  # QE inversé
            self.money_supply -= tax
            return {"action": "contraction", "tax": round(tax, 2)}
        elif self.gdp < 1000:
            self.inflation_rate = max(-0.02, self.inflation_rate - 0.01)
            stimulus = 500.0
            for acct in self.accounts.values():
                acct.balance += 50.0
            self.money_supply += stimulus
            return {"action": "stimulus", "amount": stimulus}
        return {"action": "stable", "inflation": round(self.inflation_rate, 4)}

    def market_prices(self) -> dict:
        prices = {}
        for m in MARKET_TYPES:
            m_orders = [o for o in self.orders if o.market == m]
            if m_orders:
                prices[m] = round(sum(o.price for o in m_orders) /
                                  len(m_orders), 2)
            else:
                prices[m] = 10.0
        return prices

    def wealth_distribution(self) -> dict:
        balances = [acct.balance for acct in self.accounts.values()]
        if not balances:
            return {}
        return {
            "total": round(sum(balances), 2),
            "mean": round(sum(balances) / len(balances), 2),
            "max": round(max(balances), 2),
            "min": round(min(balances), 2),
            "gdp": round(self.gdp, 2),
        }

    def token_balance(self, agent_id: str) -> float:
        """Retourne le solde Cognitas d'un agent."""
        acct = self.accounts.get(agent_id)
        return acct.balance if acct else 0.0

    def token_transfer(self, sender_id: str, receiver_id: str, amount: float) -> dict:
        """Transfère des Cognitas entre agents."""
        sender = self.accounts.get(sender_id)
        receiver = self.accounts.get(receiver_id)
        if not sender or not receiver:
            return {"status": "error", "reason": "Agent not found"}
        if sender.balance < amount:
            return {"status": "error", "reason": "Insufficient balance"}
        sender.balance -= amount
        receiver.balance += amount
        sender.transactions.append({"type": "transfer_out", "amount": amount, "to": receiver_id})
        receiver.transactions.append({"type": "transfer_in", "amount": amount, "from": sender_id})
        return {"status": "ok", "from": sender_id, "to": receiver_id, "amount": amount}

    def marketplace(self, action: str = "list", **kwargs) -> dict:
        """Interface du marketplace. Actions : list, buy, sell, prices."""
        if action == "list":
            return {
                "markets": list(MARKET_TYPES),
                "orders": len(self.orders),
                "recent": [o.to_dict() for o in self.orders[-10:]],
            }
        elif action == "prices":
            return {"prices": self.market_prices()}
        elif action == "buy":
            o = self.trade(
                kwargs.get("seller", ""),
                kwargs.get("buyer", ""),
                kwargs.get("market", "skills"),
                kwargs.get("item", ""),
                kwargs.get("price", 10.0),
            )
            return {"status": "ok" if o else "error", "order": o.to_dict() if o else None}
        elif action == "sell":
            return {"status": "ok", "action": "sell", "item": kwargs.get("item", "")}
        return {"status": "ok", "action": action}

    def stake(self, agent_id: str, amount: float) -> dict:
        """Stake des Cognitas (mise en garantie)."""
        acct = self.accounts.get(agent_id)
        if not acct:
            return {"status": "error", "reason": "Agent not found"}
        if acct.balance < amount:
            return {"status": "error", "reason": "Insufficient balance"}
        acct.balance -= amount
        # Dans une vraie implémentation, le staking rapporterait des intérêts
        acct.transactions.append({"type": "stake", "amount": amount})
        return {"status": "ok", "agent": agent_id, "staked": amount, "reward_rate": 0.05}

    def get_stats(self) -> dict:
        return {
            "agents": len(self.accounts),
            "transactions": len(self.orders),
            "gdp": round(self.gdp, 2),
            "money_supply": round(self.money_supply, 2),
            "inflation": round(self.inflation_rate, 4),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "register":
            a = self.register_agent(
                input_data.get("agent", "?"),
                input_data.get("balance", 1000.0),
            )
            return {"status": "ok", "account": a.to_dict()}
        elif action == "trade":
            o = self.trade(
                input_data.get("seller", ""),
                input_data.get("buyer", ""),
                input_data.get("market", "skills"),
                input_data.get("item", ""),
                input_data.get("price", 10.0),
            )
            return {"status": "ok" if o else "error",
                    "order": o.to_dict() if o else None}
        elif action == "regulate":
            return {"status": "ok",
                    "regulation": self.regulate()}
        elif action == "prices":
            return {"status": "ok",
                    "prices": self.market_prices()}
        elif action == "wealth":
            return {"status": "ok",
                    "wealth": self.wealth_distribution()}
        return {"status": "ok", "agents": len(self.accounts)}
