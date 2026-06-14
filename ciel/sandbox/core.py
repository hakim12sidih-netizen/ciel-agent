"""
CIEL v1.0 — SANDBOX ENGINE v2.
Exécution sécurisée de code — backends multiples.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LANGUAGES = {
    "python": {"ext": ".py", "cmd": "python3", "image": "python:3.12-slim"},
    "js": {"ext": ".js", "cmd": "node", "image": "node:20-slim"},
    "go": {"ext": ".go", "cmd": "go run", "image": "golang:1.22"},
    "rust": {"ext": ".rs", "cmd": "rustc -O -o /tmp/out && /tmp/out", "image": "rust:1.78"},
    "bash": {"ext": ".sh", "cmd": "bash", "image": "bash:5"},
    "typescript": {"ext": ".ts", "cmd": "npx tsx", "image": "node:20-slim"},
    "ruby": {"ext": ".rb", "cmd": "ruby", "image": "ruby:3.3"},
}

SANDBOX_TIMEOUT = 30
SANDBOX_MEMORY = "256m"


@dataclass
class SandboxResult:
    id: str
    language: str
    code: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_ms: float = 0.0
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id, "lang": self.language,
            "stdout": self.stdout[:500], "stderr": self.stderr[:200],
            "exit": self.exit_code, "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
        }


@dataclass
class SandboxPolicy:
    allow_network: bool = False
    allow_filesystem_write: bool = False
    allow_gpu: bool = False
    max_memory_mb: int = 256
    max_cpu_cores: float = 1.0
    timeout_seconds: int = 30
    allowed_tools: list[str] = field(default_factory=lambda: ["python", "bash"])
    allowed_domains: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)

    @classmethod
    def restricted(cls) -> SandboxPolicy:
        return cls()

    @classmethod
    def default(cls) -> SandboxPolicy:
        return cls(allow_network=True)

    @classmethod
    def permissive(cls) -> SandboxPolicy:
        return cls(
            allow_network=True, allow_filesystem_write=True,
            max_memory_mb=1024, timeout_seconds=120,
            allowed_tools=list(LANGUAGES.keys()),
        )


class SandboxBackend(ABC):
    def __init__(self, policy: SandboxPolicy | None = None):
        self.policy = policy or SandboxPolicy.restricted()

    @abstractmethod
    def execute(self, code: str, language: str, timeout: int) -> SandboxResult:
        ...

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool: ...


class DockerBackend(SandboxBackend):
    def execute(self, code: str, language: str, timeout: int) -> SandboxResult:
        lang_cfg = LANGUAGES.get(language, LANGUAGES["python"])
        with tempfile.NamedTemporaryFile(suffix=lang_cfg["ext"], delete=False, mode="w") as f:
            f.write(code)
            f.flush()
            tmp_path = f.name

        cmd = [
            "docker", "run", "--rm",
            "-m", f"{self.policy.max_memory_mb}m",
            "--network", "bridge" if self.policy.allow_network else "none",
            "--timeout", str(timeout),
            "-v", f"{tmp_path}:/code{lang_cfg['ext']}",
            lang_cfg["image"],
            lang_cfg["cmd"], f"/code{lang_cfg['ext']}",
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=timeout + 10)
            return SandboxResult(
                id=f"sbx-{uuid.uuid4().hex[:12]}",
                language=language, code=code,
                stdout=r.stdout.decode(), stderr=r.stderr.decode(),
                exit_code=r.returncode,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                id=f"sbx-{uuid.uuid4().hex[:12]}",
                language=language, code=code,
                error=f"Timeout ({timeout}s)",
            )
        finally:
            os.unlink(tmp_path)

    @classmethod
    def is_available(cls) -> bool:
        try:
            r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False


class LocalBackend(SandboxBackend):
    def execute(self, code: str, language: str, timeout: int) -> SandboxResult:
        start = time.time()
        result = SandboxResult(id=f"sbx-{uuid.uuid4().hex[:12]}", language=language, code=code)
        if language == "python":
            try:
                r = subprocess.run(
                    ["python3", "-c", code],
                    capture_output=True, timeout=timeout,
                )
                result.stdout = r.stdout.decode()
                result.stderr = r.stderr.decode()
                result.exit_code = r.returncode
            except subprocess.TimeoutExpired:
                result.error = f"Timeout ({timeout}s)"
            except Exception as e:
                result.error = str(e)
        elif language == "bash":
            try:
                r = subprocess.run(
                    ["bash", "-c", code],
                    capture_output=True, timeout=timeout,
                )
                result.stdout = r.stdout.decode()
                result.stderr = r.stderr.decode()
                result.exit_code = r.returncode
            except subprocess.TimeoutExpired:
                result.error = f"Timeout ({timeout}s)"
            except Exception as e:
                result.error = str(e)
        else:
            result.error = f"Unsupported language for local backend: {language}"
        result.duration_ms = (time.time() - start) * 1000
        return result

    @classmethod
    def is_available(cls) -> bool:
        return True


class SSHBackend(SandboxBackend):
    def __init__(self, host: str = "", username: str = "",
                 key_path: str = "", policy: SandboxPolicy | None = None):
        super().__init__(policy)
        self.host = host or os.environ.get("CIEL_SSH_HOST", "")
        self.username = username or os.environ.get("CIEL_SSH_USER", "root")
        self.key_path = Path(key_path or os.environ.get("CIEL_SSH_KEY", ""))

    def execute(self, code: str, language: str, timeout: int) -> SandboxResult:
        if not self.host:
            return SandboxResult(
                id=f"sbx-{uuid.uuid4().hex[:12]}",
                language=language, code=code,
                error="SSH host not configured. Set CIEL_SSH_HOST env var.",
            )
        start = time.time()
        result = SandboxResult(id=f"sbx-{uuid.uuid4().hex[:12]}", language=language, code=code)
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
        if self.key_path.exists():
            ssh_cmd += ["-i", str(self.key_path)]
        ssh_cmd += [f"{self.username}@{self.host}"]

        base64_code = code.encode().hex()
        remote_cmd = f"echo '{base64_code}' | xxd -r -p | {LANGUAGES.get(language, LANGUAGES['python'])['cmd']}"
        try:
            r = subprocess.run(
                ssh_cmd + [remote_cmd],
                capture_output=True, timeout=timeout + 15,
            )
            result.stdout = r.stdout.decode()
            result.stderr = r.stderr.decode()
            result.exit_code = r.returncode
        except subprocess.TimeoutExpired:
            result.error = f"SSH timeout ({timeout}s)"
        except Exception as e:
            result.error = str(e)
        result.duration_ms = (time.time() - start) * 1000
        return result

    @classmethod
    def is_available(cls) -> bool:
        return bool(shutil.which("ssh"))


BACKENDS: dict[str, type[SandboxBackend]] = {
    "docker": DockerBackend,
    "local": LocalBackend,
    "ssh": SSHBackend,
}


def get_backend(name: str, **kwargs: Any) -> SandboxBackend:
    cls = BACKENDS.get(name)
    if not cls:
        raise ValueError(f"Unknown backend: {name}. Available: {list(BACKENDS.keys())}")
    return cls(**kwargs)


def detect_best_backend() -> str:
    if DockerBackend.is_available():
        return "docker"
    return "local"


class SandboxEngine:
    def __init__(self, backend: str | None = None, policy: SandboxPolicy | None = None):
        backend_name = backend or detect_best_backend()
        self.backend = get_backend(backend_name, policy=policy or SandboxPolicy.default())
        self.results: list[SandboxResult] = []

    def execute(self, code: str, language: str = "python",
                timeout: int = SANDBOX_TIMEOUT) -> SandboxResult:
        if language not in self.backend.policy.allowed_tools:
            return SandboxResult(
                id=f"sbx-{uuid.uuid4().hex[:12]}",
                language=language, code=code,
                error=f"Language '{language}' not allowed by policy",
            )
        result = self.backend.execute(code, language, min(timeout, self.backend.policy.timeout_seconds))
        self.results.append(result)
        return result

    def get_stats(self) -> dict:
        return {
            "executions": len(self.results),
            "backend": type(self.backend).__name__,
            "backend_available": type(self.backend).is_available(),
            "policy": {
                "network": self.backend.policy.allow_network,
                "fs_write": self.backend.policy.allow_filesystem_write,
                "gpu": self.backend.policy.allow_gpu,
                "max_memory_mb": self.backend.policy.max_memory_mb,
                "timeout": self.backend.policy.timeout_seconds,
            },
        }
