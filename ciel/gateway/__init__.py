"""
CIEL v1.0 — Gateway : serveur de passerelle multi-plateforme.

Composant CIEL natif — passerelle de communication.
Architecture de dispatch de méthodes :
  - GatewayServer : serveur HTTP/WebSocket
  - MethodRegistry : enregistrement et dispatch des méthodes
  - Protocol : OpenAI-compatible, WebSocket JSON-RPC
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from ciel.channels import ChannelManager, Message
from ciel.evolution.leader_network import LeaderNetwork
from ciel.memory import MemoryManager
from ciel.skills import SkillManager
from ciel.plugins import get_registry as get_plugin_registry


@dataclass(slots=True)
class GatewayMethod:
    name: str
    handler: Callable[..., Any]
    description: str = ""
    scope: str = "public"  # public | admin | internal


class GatewayServer:
    """Serveur de passerelle CIEL.

    Point d'entrée unique pour toutes les interactions :
      - Messages des canaux (Telegram, Discord, etc.)
      - Appels API REST
      - WebSocket JSON-RPC
      - CLI
    """

    def __init__(self):
        self.methods: dict[str, GatewayMethod] = {}
        self.channels = ChannelManager()
        self.memory = MemoryManager()
        self.skills = SkillManager()
        self.network = LeaderNetwork()
        self._running = False
        self._start_time: float = 0.0

        # Enregistre les méthodes de base
        self._register_core_methods()

    def _register_core_methods(self) -> None:
        self.register_method("system.health", self._handle_health, "Health check")
        self.register_method("system.info", self._handle_info, "System information")
        self.register_method("memory.store", self._handle_memory_store, "Store memory")
        self.register_method("memory.recall", self._handle_memory_recall, "Recall memory")
        self.register_method("skills.list", self._handle_skills_list, "List skills")
        self.register_method("skills.create", self._handle_skills_create, "Create skill")
        self.register_method("channels.list", self._handle_channels_list, "List channels")
        self.register_method("channels.send", self._handle_channels_send, "Send message")
        self.register_method("providers.list", self._handle_providers_list, "List providers")

    def register_method(self, name: str, handler: Callable,
                        description: str = "", scope: str = "public") -> None:
        self.methods[name] = GatewayMethod(
            name=name, handler=handler, description=description, scope=scope
        )

    def start(self) -> bool:
        self._running = True
        self._start_time = time.time()
        self.channels.connect_all()
        self.network.emit("gateway.started", {"method_count": len(self.methods)})
        return True

    def stop(self) -> bool:
        self.channels.disconnect_all()
        self.memory.shutdown_all()
        self._running = False
        self.network.emit("gateway.stopped", {"uptime_s": time.time() - self._start_time})
        return True

    def dispatch(self, method: str, params: dict | None = None) -> Any:
        gw_method = self.methods.get(method)
        if not gw_method:
            raise ValueError(f"Méthode inconnue: {method}")
        return gw_method.handler(**(params or {}))

    def handle_message(self, message: Message) -> str | None:
        """Traite un message entrant et retourne une réponse."""
        # Commandes système
        if message.content.startswith("/"):
            return self._handle_command(message)

        # Dispatch vers l'agent (placeholder)
        self.network.emit("gateway.message", {
            "channel": message.channel,
            "content": message.content[:80],
        })
        return None

    def _handle_command(self, message: Message) -> str | None:
        cmd = message.content[1:].split()[0].lower()
        if cmd == "health":
            return json.dumps(self._handle_health(), indent=2)
        elif cmd == "memory":
            return json.dumps(self.memory.statistics(), indent=2)
        elif cmd == "skills":
            return json.dumps(self.skills.statistics(), indent=2)
        elif cmd == "help":
            methods = "\n".join(f"  /{m}" for m in self.methods if m.startswith("system."))
            return f"Méthodes disponibles:\n{methods}"
        return None

    def _handle_health(self, **kwargs: Any) -> dict:
        return {
            "status": "healthy" if self._running else "stopped",
            "uptime_s": round(time.time() - self._start_time, 2) if self._start_time else 0,
            "methods": len(self.methods),
            "channels": len(self.channels.channels),
            "timestamp": time.time(),
            "version": "1.0.0",
        }

    def _handle_info(self, **kwargs: Any) -> dict:
        return {
            "name": "CIEL Gateway",
            "version": "1.0.0",
            "edition": "Polyglot v1.0",
            "running": self._running,
            "methods": list(self.methods.keys()),
        }

    def _handle_memory_store(self, content: str = "", type_: str = "fact",
                              source: str = "gateway", **kwargs: Any) -> dict:
        from ciel.memory import create_memory
        entry = create_memory(content, type_, source)
        self.memory.store(entry)
        return {"status": "stored", "id": entry.id}

    def _handle_memory_recall(self, query: str = "", limit: int = 10, **kwargs: Any) -> dict:
        results = self.memory.recall(query, limit)
        return {"results": [e.to_dict() for e in results]}

    def _handle_skills_list(self, category: str | None = None, **kwargs: Any) -> dict:
        skills = self.skills.list(category=category)
        return {"skills": [s.to_dict() for s in skills]}

    def _handle_skills_create(self, name: str = "", description: str = "",
                               body: str = "", **kwargs: Any) -> dict:
        skill = self.skills.create(name, description, body)
        return {"status": "created", "id": skill.id}

    def _handle_channels_list(self, **kwargs: Any) -> dict:
        return {"channels": self.channels.list_channels()}

    def _handle_channels_send(self, channel_id: str = "", content: str = "", **kwargs: Any) -> dict:
        success = self.channels.send(channel_id, content)
        return {"status": "sent" if success else "failed"}

    def _handle_providers_list(self, **kwargs: Any) -> dict:
        from ciel.providers import get_registry
        registry = get_registry()
        return {"providers": [p.to_dict() for p in registry.list()]}


# Instance globale
_gateway: GatewayServer | None = None


def get_gateway() -> GatewayServer:
    global _gateway
    if _gateway is None:
        _gateway = GatewayServer()
    return _gateway


def reset_gateway() -> None:
    global _gateway
    _gateway = None
