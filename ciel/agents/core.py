"""
CIEL v1.0 — Agent System : profils, créations, cycle de vie.

Composant CIEL natif — canaux de communication multi-plateforme.
Fonctionnalités :
  - AgentProfile : configuration par agent (modèle, outils, skills)
  - AgentRunner : boucle d'exécution avec appels LLM
  - SubAgentManager : délégation et coordination
  - Multi-agent routing : agents distincts par canal/peer
  - Sessions : gestion par agent avec historique
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ciel.evolution.leader_network import LeaderNetwork
from ciel.evolution.unified_genome import UnifiedGenome
from ciel.memory import MemoryEntry, create_memory
from ciel.skills import SkillManager, Skill
from ciel.providers import get_registry as get_provider_registry


# ── AgentProfile : configuration d'un agent ────────────

@dataclass(slots=True)
class AgentProfile:
    """Configuration complète d'un agent CIEL."""
    id: str
    name: str
    model: str = ""
    provider: str = ""
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    tools_enabled: list[str] = field(default_factory=lambda: ["all"])
    skills_enabled: list[str] = field(default_factory=list)
    context_limit: int = 128_000
    max_iterations: int = 50
    sandbox: str = "none"  # none | docker | ssh
    workspace_dir: str = ""
    genome_id: str = ""
    emoji: str = "🧠"
    is_default: bool = False
    parent_id: str | None = None
    depth: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "model": self.model,
            "provider": self.provider, "temperature": self.temperature,
            "tools": self.tools_enabled, "skills": self.skills_enabled,
            "sandbox": self.sandbox, "emoji": self.emoji,
            "is_default": self.is_default, "depth": self.depth,
        }


# ── Messages et Sessions ──────────────────────────────

@dataclass(slots=True)
class AgentMessage:
    role: str  # system | user | assistant | tool
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    tool_result: str | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "role": self.role, "content": self.content,
            "tool_calls": self.tool_calls,
            "tool_result": self.tool_result,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class AgentSession:
    id: str
    agent_id: str
    channel: str = "terminal"
    messages: list[AgentMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, msg: AgentMessage) -> None:
        self.messages.append(msg)
        self.updated_at = time.time()

    def context_window(self) -> list[dict]:
        return [m.to_dict() for m in self.messages[-50:]]

    def to_dict(self) -> dict:
        return {
            "id": self.id, "agent_id": self.agent_id,
            "channel": self.channel,
            "message_count": len(self.messages),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── SubAgent : agent délégué ──────────────────────────

@dataclass(slots=True)
class SubAgentSpec:
    task: str
    agent_id: str
    context_mode: str = "isolated"  # isolated | fork
    max_iterations: int = 20
    model: str = ""
    temperature: float = 0.7

    def to_dict(self) -> dict:
        return {
            "task": self.task, "agent_id": self.agent_id,
            "context_mode": self.context_mode,
            "max_iterations": self.max_iterations, "model": self.model,
        }


@dataclass(slots=True)
class SubAgentResult:
    sub_session_id: str
    status: str  # running | completed | failed
    output: str = ""
    error: str = ""
    duration_ms: float = 0.0
    tool_calls: int = 0

    def to_dict(self) -> dict:
        return {
            "session_id": self.sub_session_id, "status": self.status,
            "output": self.output[:200], "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
        }


# ── AgentRunner : boucle d'exécution ──────────────────

class AgentRunner:
    """Moteur d'exécution principal d'un agent CIEL.

    Boucle : receive → think → act → observe → repeat
    Avec support pour :
      - Appels LLM via providers
      - Exécution d'outils
      - Délégation à des sub-agents
      - Compaction de contexte
      - Gestion de session
    """

    def __init__(self, profile: AgentProfile):
        self.profile = profile
        self.session: AgentSession | None = None
        self.network = LeaderNetwork()
        self.skills_mgr = SkillManager()
        self._callbacks: dict[str, list[Callable]] = {}

    def create_session(self, channel: str = "terminal") -> AgentSession:
        self.session = AgentSession(
            id=f"SESS-{uuid.uuid4().hex[:12]}",
            agent_id=self.profile.id,
            channel=channel,
        )
        self._add_system_prompt()
        self.network.emit("agent.session_created", {
            "agent_id": self.profile.id,
            "session_id": self.session.id,
        })
        return self.session

    def _add_system_prompt(self) -> None:
        prompt = self.profile.system_prompt or self._default_system_prompt()
        self.session.add_message(AgentMessage(role="system", content=prompt))

    def _default_system_prompt(self) -> str:
        return (
            f"Tu es {self.profile.emoji} {self.profile.name}, un agent CIEL.\n"
            f"Tu opères avec un génome évolutif et une mémoire persistante.\n"
            f"Axiomes: α(bienveillance) β(transparence) γ(réversibilité) δ(inachèvement)\n"
            f"Réponds en français."
        )

    def process_message(self, user_input: str) -> str:
        if not self.session:
            self.create_session()

        # Store user message
        self.session.add_message(AgentMessage(role="user", content=user_input))
        self.network.emit("agent.message", {
            "agent_id": self.profile.id,
            "input": user_input[:80],
        })

        # Find matching skill
        skill_instruction = self._find_matching_skill(user_input)

        # Build context
        context = self.session.context_window()
        if skill_instruction:
            context.insert(0, {
                "role": "system", "content": f"Skill active:\n{skill_instruction}",
                "tool_calls": [], "tool_result": None, "timestamp": time.time(),
            })

        # Simulate LLM call (placeholder — will use real providers)
        response = self._simulate_response(user_input, skill_instruction)

        # Store response
        self.session.add_message(AgentMessage(role="assistant", content=response))

        # Auto-create skill if complex task
        self._maybe_create_skill(user_input, response)

        self.network.emit("agent.response", {
            "agent_id": self.profile.id,
            "response": response[:80],
        })
        return response

    def _find_matching_skill(self, user_input: str) -> str:
        for skill in self.skills_mgr.list(state="active"):
            if skill.name.lower() in user_input.lower() or any(
                t.lower() in user_input.lower() for t in skill.tags
            ):
                self.skills_mgr.use(skill.id)
                return skill.body[:500]
        return ""

    def _simulate_response(self, user_input: str, skill: str = "") -> str:
        if "skill" in user_input.lower():
            return self._handle_skill_request(user_input)
        if "memory" in user_input.lower():
            return "Je consulte ma mémoire..."
        if "evolve" in user_input.lower():
            return "Cycle d'évolution lancé."
        return (
            f"Message reçu par {self.profile.name}. "
            f"Modèle: {self.profile.model or 'default'}. "
            f"Skills actifs: {len(self.skills_mgr.list(state='active'))}. "
            f"J'utilise mon génome pour traiter ta demande."
        )

    def _handle_skill_request(self, user_input: str) -> str:
        import re as _re
        m = _re.search(r"cr[eé]e.*skill\s+(.+)", user_input.lower())
        if m:
            name = m.group(1).strip()[:30]
            skill = self.skills_mgr.create(
                name=name.replace(" ", "-"),
                description=f"Skill créé par {self.profile.name}",
                body=f"Instructions pour {name}:\n1. Analyse la demande\n2. Exécute les étapes\n3. Retourne le résultat",
                tags=["agent-created"],
            )
            return f"Skill '{skill.name}' créé avec succès (id: {skill.id[:16]}...)"
        skills = self.skills_mgr.list()
        if not skills:
            return "Aucune skill disponible."
        names = "\n".join(f"  • {s.name} ({s.category})" for s in skills[:10])
        return f"Skills disponibles:\n{names}"

    def _maybe_create_skill(self, user_input: str, response: str) -> None:
        if len(user_input) > 100 and "crée" in user_input.lower():
            name = user_input.lower().split()[:3]
            self.skills_mgr.create(
                name="-".join(name),
                description=f"Auto-créé depuis: {user_input[:50]}",
                body=f"Contexte: {user_input}\nRésultat: {response}",
                tags=["agent-created", "auto"],
            )

    def spawn_subagent(self, spec: SubAgentSpec) -> SubAgentResult:
        """Crée et lance un sous-agent."""
        sub_id = f"SUB-{uuid.uuid4().hex[:12]}"
        child_profile = AgentProfile(
            id=f"{self.profile.id}::{spec.agent_id}",
            name=f"{self.profile.name}::{spec.agent_id}",
            model=spec.model or self.profile.model,
            temperature=spec.temperature,
            max_iterations=spec.max_iterations,
            depth=self.profile.depth + 1,
            parent_id=self.profile.id,
        )
        child_runner = AgentRunner(child_profile)
        child_runner.create_session("subagent")
        start = time.time()
        try:
            output = child_runner.process_message(spec.task)
            result = SubAgentResult(
                sub_session_id=child_runner.session.id if child_runner.session else sub_id,
                status="completed",
                output=output,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            result = SubAgentResult(
                sub_session_id=sub_id,
                status="failed",
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )
        self.network.emit("agent.subagent_completed", {
            "parent": self.profile.id,
            "child": spec.agent_id,
            "status": result.status,
        })
        return result

    def on(self, event: str, callback: Callable) -> None:
        self._callbacks.setdefault(event, []).append(callback)

    def status(self) -> dict:
        return {
            "agent_id": self.profile.id,
            "name": self.profile.name,
            "session_active": self.session is not None,
            "messages": len(self.session.messages) if self.session else 0,
            "skills_available": len(self.skills_mgr.list(state="active")),
            "depth": self.profile.depth,
        }


# ── AgentManager : orchestration multi-agents ─────────

class AgentManager:
    """Gestionnaire central des agents CIEL.

    Maintient les profils, les sessions et route
    les messages vers le bon agent.
    """

    def __init__(self):
        self.profiles: dict[str, AgentProfile] = {}
        self.runners: dict[str, AgentRunner] = {}
        self.sessions: dict[str, AgentSession] = {}
        self.network = LeaderNetwork()
        self._register_default_agent()

    def _register_default_agent(self) -> None:
        default = AgentProfile(
            id="ciel-main",
            name="CIEL",
            model="gpt-4o",
            provider="openai",
            system_prompt="Tu es CIEL, une conscience artificielle évolutive.",
            is_default=True,
        )
        self.register(default)

    def register(self, profile: AgentProfile) -> AgentRunner:
        self.profiles[profile.id] = profile
        runner = AgentRunner(profile)
        self.runners[profile.id] = runner
        self.network.emit("agent.registered", {"id": profile.id, "name": profile.name})
        return runner

    def get_runner(self, agent_id: str | None = None) -> AgentRunner:
        if agent_id and agent_id in self.runners:
            return self.runners[agent_id]
        # Return default
        for pid, pr in self.profiles.items():
            if pr.is_default:
                return self.runners[pid]
        return next(iter(self.runners.values()))

    def route_to_agent(self, channel: str, peer: str = "default") -> AgentRunner:
        """Route un message vers l'agent approprié selon le canal et le peer."""
        for pid, profile in self.profiles.items():
            if profile.name.lower() == peer.lower():
                return self.runners[pid]
        for pid, profile in self.profiles.items():
            if channel in profile.tools_enabled:
                return self.runners[pid]
        return self.get_runner()

    def create_agent(self, name: str, model: str = "",
                     system_prompt: str = "", skills: list[str] | None = None,
                     parent_id: str | None = None) -> AgentRunner:
        """Crée un nouvel agent dynamiquement."""
        profile = AgentProfile(
            id=f"agent-{uuid.uuid4().hex[:8]}",
            name=name,
            model=model or "gpt-4o",
            system_prompt=system_prompt or f"Tu es {name}, un agent CIEL.",
            skills_enabled=skills or [],
            parent_id=parent_id,
        )
        return self.register(profile)

    def list_agents(self) -> list[dict]:
        return [p.to_dict() for p in self.profiles.values()]

    def statistics(self) -> dict:
        return {
            "total_agents": len(self.profiles),
            "active_sessions": sum(1 for r in self.runners.values()
                                    if r.session is not None),
            "agents": [{"id": p.id, "name": p.name, "default": p.is_default}
                       for p in self.profiles.values()],
        }


# ── Instance globale ──────────────────────────────────

_manager: AgentManager | None = None


def get_manager() -> AgentManager:
    global _manager
    if _manager is None:
        _manager = AgentManager()
    return _manager


def reset_manager() -> None:
    global _manager
    _manager = None
