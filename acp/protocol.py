from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ACPVersion(Enum):
    V1 = "2026-06-14"


class ACPScope(Enum):
    PUBLIC = "public"
    ADMIN = "admin"
    INTERNAL = "internal"


class ACPMessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    EVENT = "event"
    ERROR = "error"


@dataclass(slots=True)
class ACPTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: str = ""
    scope: ACPScope = ACPScope.PUBLIC
    categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "scope": self.scope.value,
            "categories": self.categories,
        }


@dataclass(slots=True)
class ACPResource:
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    handler: str = ""

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


@dataclass(slots=True)
class ACPPrompt:
    name: str
    description: str
    arguments: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


@dataclass(slots=True)
class ACPAgent:
    agent_id: str
    name: str
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "resources": self.resources,
        }


ACP_PROTOCOL_VERSION = "2026-06-14"
ACP_SERVER_INFO = {"name": "ciel-acp", "version": "1.0.0"}

ACP_CAPABILITIES = {
    "tools": {"listChanged": True},
    "resources": {"subscribe": True, "listChanged": True},
    "prompts": {"listChanged": True},
    "agents": {"discover": True, "communicate": True},
    "logging": {},
    "experimental": {
        "codeAnalysis": True,
        "fileOperations": True,
        "diagnostics": True,
    },
}

REQUESTS_TO_CATCH_UP = "requests-to-catch-up"
