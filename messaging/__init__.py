"""
CIEL v∞.3 — Messaging : Canaux Multi-Plateforme + Skills.

Engines : MessagingEngine (process compatible CIELBrain).
"""
from __future__ import annotations

from ciel.messaging.channels.base import ChannelAdapter, ChannelMessage, ChannelConfig
from ciel.messaging.channels.whatsapp import WhatsAppAdapter
from ciel.messaging.channels.signal import SignalAdapter
from ciel.messaging.channels.matrix import MatrixAdapter
from ciel.messaging.channels.irc import IRCAdapter
from ciel.messaging.skills import SkillRegistry, SkillMetadata
from ciel.messaging.gateway import GatewayServer, RouteConfig
from ciel.messaging.core import MessagingEngine

__all__ = [
    "ChannelAdapter", "ChannelMessage", "ChannelConfig",
    "WhatsAppAdapter", "SignalAdapter", "MatrixAdapter", "IRCAdapter",
    "SkillRegistry", "SkillMetadata",
    "GatewayServer", "RouteConfig",
    "MessagingEngine",
]
