"""
Transverse — ECONOMY : Métabolisme Computationnel.

Composants :
  - Metabolism     : entrées/stockage (cache→RAM→NVMe→ADN)/dépenses + BMR
  - VickreyAuction : enchère second-price, priorité = EU × Urgence / Coût
  - ShapleyValue   : contribution marginale moyenne
  - Token          : token interne (mint, transfer, supply)
  - Market         : carnet d'ordres ask/bid, price discovery
  - EconomyEngine  : process() compatible CIELBrain
"""
from __future__ import annotations

from ciel.economy.core import (
    ResourceType, Resource, Bid, StorageTier, StoragePool,
    Metabolism, VickreyAuction, ShapleyValue, Token, Market,
    EconomyEngine,
)
__all__ = [
    "ResourceType", "Resource", "Bid", "StorageTier", "StoragePool",
    "Metabolism", "VickreyAuction", "ShapleyValue", "Token", "Market",
    "EconomyEngine",
]
