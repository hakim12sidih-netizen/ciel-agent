"""
LeaderNetwork - Inter-Agent Communication Channel
EventEmitter for faction coordination and emergent tokens.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmergentToken:
    """Self-organized semantic token"""
    symbol: str
    intents: list[dict[str, Any]]
    valence: float  # -1 = threat, 0 = neutral, +1 = opportunity
    timestamp: float
    originator_id: str
    id: str


@dataclass(slots=True)
class LeaderNetwork:
    """
    Leader Network - EventBus for Inter-Agent Communication
    Supports both vector and semantic token channels.
    """
    listeners: dict[str, list[Callable]] = field(default_factory=dict)
    max_listeners: int = 100

    def __post_init__(self) -> None:
        """Initialize network"""
        logger.info("[Leader Network] 📡 Leader Network initialized.")

    def broadcast_discovery(self, faction_id: str, title: str, discovery: str) -> None:
        """Broadcast discovery to all leaders"""
        logger.debug(
            f"[Leader Network] 📡 {title} broadcasts: \"{discovery[:50]}...\""
        )
        self._emit("discovery", {
            "faction_id": faction_id,
            "title": title,
            "discovery": discovery
        })

    def send_direct_message(
        self, from_faction_id: str, to_faction_id: str, message: str
    ) -> None:
        """Send direct message between factions"""
        channel = f"dm_{to_faction_id}"
        self._emit(channel, {
            "from_faction_id": from_faction_id,
            "message": message
        })

    def transmit_council_order(self, order: str) -> None:
        """Transmit directive from Council/Overseer"""
        logger.debug(
            f"[Council Command] ⚠️ OVERSEER TRANSMITS DIRECTIVE: {order}"
        )
        self._emit("council_order", order)

    def broadcast_vector(
        self, from_id: str, to_id: str, vector: list[float]
    ) -> None:
        """Broadcast raw vector (ultra-efficient coordination)"""
        self._emit("vector_exchange", {
            "from_id": from_id,
            "to_id": to_id,
            "vector": vector
        })
        logger.debug(
            f"[Emergent Comm] Vector Exchange: {from_id} ➔ {to_id} (len: {len(vector)})"
        )

    def broadcast_token(self, token: EmergentToken) -> None:
        """Broadcast emergent semantic token"""
        logger.debug(
            f"[Leader Network] 🗣️ Token: {token.symbol} from {token.originator_id} "
            f"(valence: {token.valence:.2f})"
        )
        self._emit("token", token)

    def send_token_to(self, to_id: str, token: EmergentToken) -> None:
        """Send token to specific agent"""
        logger.debug(
            f"[Leader Network] 📨 Token to {to_id}: {token.symbol}"
        )
        self._emit(f"token_{to_id}", token)

    def on(self, event: str, callback: Callable) -> None:
        """Register listener for event"""
        if event not in self.listeners:
            self.listeners[event] = []
        if len(self.listeners[event]) < self.max_listeners:
            self.listeners[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Unregister listener"""
        if event in self.listeners:
            self.listeners[event] = [
                c for c in self.listeners[event] if c != callback
            ]

    def _emit(self, event: str, data: Any) -> None:
        """Emit event to all listeners"""
        if event in self.listeners:
            for callback in self.listeners[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"[Leader Network] Error in callback: {e}")

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process network request.
        CIEL compatibility method.
        """
        return {
            "channels": len(self.listeners),
            "status": "active"
        }


# Global singleton instance
_leader_network: LeaderNetwork | None = None


def get_leader_network() -> LeaderNetwork:
    """Get or create global leader network"""
    global _leader_network
    if _leader_network is None:
        _leader_network = LeaderNetwork()
    return _leader_network
