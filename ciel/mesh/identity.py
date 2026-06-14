from __future__ import annotations

import json
import uuid
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)


@dataclass(slots=True)
class NodeIdentity:
    peer_id: str
    private_key: Ed25519PrivateKey
    public_key: Ed25519PublicKey
    address: str = ""
    port: int = 0
    protocol_version: int = 1
    capabilities: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    @classmethod
    def generate(cls, peer_id: str | None = None) -> NodeIdentity:
        pk = Ed25519PrivateKey.generate()
        node_id = peer_id or f"ciel-{uuid.uuid4().hex[:12]}"
        return cls(peer_id=node_id, private_key=pk, public_key=pk.public_key())

    @classmethod
    def load_or_generate(cls, path: str | Path) -> NodeIdentity:
        p = Path(path)
        if p.exists():
            data = json.loads(p.read_text())
            pk = Ed25519PrivateKey.from_private_bytes(
                bytes.fromhex(data["private_key"])
            )
            return cls(
                peer_id=data["peer_id"],
                private_key=pk,
                public_key=pk.public_key(),
                address=data.get("address", ""),
                port=data.get("port", 0),
                protocol_version=data.get("protocol_version", 1),
                capabilities=data.get("capabilities", []),
                created_at=data.get("created_at", time.time()),
            )
        identity = cls.generate()
        identity.save(path)
        return identity

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            "peer_id": self.peer_id,
            "private_key": self.private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            ).hex(),
            "public_key": self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            ).hex(),
            "address": self.address,
            "port": self.port,
            "protocol_version": self.protocol_version,
            "capabilities": self.capabilities,
            "created_at": self.created_at,
        }, indent=2))

    def sign(self, data: bytes) -> bytes:
        return self.private_key.sign(data)

    def verify(self, data: bytes, signature: bytes, peer_key: bytes) -> bool:
        try:
            pk = Ed25519PublicKey.from_public_bytes(peer_key)
            pk.verify(signature, data)
            return True
        except Exception:
            return False

    def to_peer_proto(self) -> Any:
        from .proto import Peer
        return Peer(
            peer_id=self.peer_id,
            address=self.address,
            port=self.port,
            public_key=self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            ).hex(),
            protocol_version=self.protocol_version,
            capabilities=self.capabilities,
            last_seen=time.time(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "address": self.address,
            "port": self.port,
            "protocol_version": self.protocol_version,
            "capabilities": self.capabilities,
            "created_at": self.created_at,
        }
