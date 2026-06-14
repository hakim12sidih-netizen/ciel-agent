from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Device:
    id: str
    name: str
    public_key: str = ""
    token_hash: str = ""
    verified: bool = False
    last_seen: float = 0.0
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthSession:
    token: str
    device_id: str
    scope: list[str]
    expires_at: float
    created_at: float = field(default_factory=time.time)


class GatewayAuth:
    def __init__(self, secrets_path: str | Path | None = None):
        self._path = Path(secrets_path or Path.home() / ".ciel" / "gateway_secrets.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._devices: dict[str, Device] = {}
        self._sessions: dict[str, AuthSession] = {}
        self._pairing_codes: dict[str, tuple[str, float]] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text())
            for d in data.get("devices", []):
                dev = Device(**d)
                self._devices[dev.id] = dev
        except Exception:
            pass

    def _save(self) -> None:
        data = {
            "devices": [vars(d) for d in self._devices.values()],
        }
        self._path.write_text(json.dumps(data, indent=2, default=str))

    def generate_pairing_code(self, device_name: str, ttl: int = 300) -> tuple[str, str]:
        code = secrets.token_hex(4).upper()
        device_id = f"dev-{uuid.uuid4().hex[:12]}"
        self._devices[device_id] = Device(id=device_id, name=device_name)
        self._pairing_codes[code] = (device_id, time.time() + ttl)
        self._save()
        return code, device_id

    def verify_pairing(self, code: str) -> str | None:
        entry = self._pairing_codes.get(code)
        if not entry:
            return None
        device_id, expires = entry
        if time.time() > expires:
            del self._pairing_codes[code]
            return None
        device = self._devices.get(device_id)
        if device:
            device.verified = True
            device.last_seen = time.time()
        del self._pairing_codes[code]
        self._save()
        return device_id

    def create_session(self, device_id: str, scope: list[str] | None = None,
                       ttl: int = 86400) -> str:
        token = f"ciel_{secrets.token_urlsafe(32)}"
        self._sessions[token] = AuthSession(
            token=token,
            device_id=device_id,
            scope=scope or ["public"],
            expires_at=time.time() + ttl,
        )
        return token

    def validate_session(self, token: str) -> AuthSession | None:
        session = self._sessions.get(token)
        if not session:
            return None
        if time.time() > session.expires_at:
            del self._sessions[token]
            return None
        return session

    def revoke_session(self, token: str) -> bool:
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False

    def list_devices(self, verified_only: bool = False) -> list[Device]:
        if verified_only:
            return [d for d in self._devices.values() if d.verified]
        return list(self._devices.values())

    def get_device(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)

    def remove_device(self, device_id: str) -> bool:
        if device_id in self._devices:
            del self._devices[device_id]
            for token, s in list(self._sessions.items()):
                if s.device_id == device_id:
                    del self._sessions[token]
            self._save()
            return True
        return False

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = [t for t, s in self._sessions.items() if now > s.expires_at]
        for t in expired:
            del self._sessions[t]
        expired_codes = [c for c, (_, e) in self._pairing_codes.items() if now > e]
        for c in expired_codes:
            del self._pairing_codes[c]
        return len(expired) + len(expired_codes)
