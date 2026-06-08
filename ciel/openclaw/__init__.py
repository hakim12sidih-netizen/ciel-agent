"""
CIEL v∞.3 — OpenClaw : Canaux Multi-Plateforme + Skills.

Engines : OpenClawEngine (process compatible CIELBrain).
"""
from __future__ import annotations

from ciel.openclaw.channels.base import ChannelAdapter, ChannelMessage, ChannelConfig
from ciel.openclaw.channels.whatsapp import WhatsAppAdapter
from ciel.openclaw.channels.signal import SignalAdapter
from ciel.openclaw.channels.matrix import MatrixAdapter
from ciel.openclaw.channels.irc import IRCAdapter
from ciel.openclaw.skills import SkillRegistry, SkillMetadata
from ciel.openclaw.gateway import GatewayServer, RouteConfig
from ciel.openclaw.core import OpenClawEngine

__all__ = [
    "ChannelAdapter", "ChannelMessage", "ChannelConfig",
    "WhatsAppAdapter", "SignalAdapter", "MatrixAdapter", "IRCAdapter",
    "SkillRegistry", "SkillMetadata",
    "GatewayServer", "RouteConfig",
    "OpenClawEngine",
]
