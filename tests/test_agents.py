"""Tests pour le système multi-agents CIEL."""
from __future__ import annotations

import time
import pytest
from ciel.agents.core import (
    AgentProfile, AgentRunner, AgentManager, AgentSession, AgentMessage,
    SubAgentSpec, SubAgentResult, get_manager, reset_manager,
)


def test_agent_profile_defaults():
    p = AgentProfile(id="test-1", name="TestBot")
    assert p.id == "test-1"
    assert p.name == "TestBot"
    assert p.model == ""
    assert p.temperature == 0.7
    assert p.max_tokens == 4096
    assert p.sandbox == "none"
    assert not p.is_default


def test_agent_profile_to_dict():
    p = AgentProfile(id="t1", name="T1", model="gpt-4o", emoji="🤖")
    d = p.to_dict()
    assert d["id"] == "t1"
    assert d["model"] == "gpt-4o"
    assert d["emoji"] == "🤖"


def test_agent_message():
    m = AgentMessage(role="user", content="hello")
    assert m.role == "user"
    assert m.content == "hello"
    d = m.to_dict()
    assert d["role"] == "user"


def test_agent_message_tool_call():
    m = AgentMessage(role="assistant", content="", tool_calls=[{"name": "search"}])
    assert len(m.tool_calls) == 1


def test_agent_session_creation():
    s = AgentSession(id="SESS-1", agent_id="a1")
    assert s.id == "SESS-1"
    assert len(s.messages) == 0


def test_agent_session_add_message():
    s = AgentSession(id="SESS-2", agent_id="a1")
    s.add_message(AgentMessage(role="user", content="hi"))
    assert len(s.messages) == 1


def test_agent_session_context_window():
    s = AgentSession(id="SESS-3", agent_id="a1")
    for i in range(60):
        s.add_message(AgentMessage(role="user", content=f"msg_{i}"))
    ctx = s.context_window()
    assert len(ctx) == 50  # capped at 50
    assert ctx[0]["content"] == "msg_10"


def test_agent_runner_create_session():
    p = AgentProfile(id="r1", name="Runner1", model="gpt-4o")
    r = AgentRunner(p)
    sess = r.create_session()
    assert sess.agent_id == "r1"
    assert r.session is not None
    # Should have a system prompt
    assert len(sess.messages) == 1
    assert sess.messages[0].role == "system"


def test_agent_runner_process_message():
    p = AgentProfile(id="r2", name="Runner2")
    r = AgentRunner(p)
    resp = r.process_message("hello world")
    assert isinstance(resp, str)
    assert len(resp) > 0
    assert r.session is not None
    # Should have user msg + assistant response beyond system prompt
    assert len(r.session.messages) == 3


def test_agent_runner_skill_request():
    p = AgentProfile(id="r3", name="Runner3")
    r = AgentRunner(p)
    resp = r.process_message("crée un skill mon-test")
    assert "Skill" in resp


def test_agent_runner_find_matching_skill():
    p = AgentProfile(id="r4", name="Runner4")
    r = AgentRunner(p)
    skill = r.skills_mgr.create(name="testhelper", description="test helper",
                                body="Do the thing", tags=["test"])
    r.skills_mgr.use(skill.id)  # make it active
    instr = r._find_matching_skill("please testhelper help")
    assert len(instr) > 0
    assert "Do the thing" in instr


def test_agent_runner_status():
    p = AgentProfile(id="r5", name="Runner5")
    r = AgentRunner(p)
    r.create_session()
    st = r.status()
    assert st["agent_id"] == "r5"
    assert st["session_active"]
    assert st["messages"] == 1


def test_sub_agent_spec():
    spec = SubAgentSpec(task="analyze", agent_id="sub1")
    assert spec.task == "analyze"
    assert spec.context_mode == "isolated"
    d = spec.to_dict()
    assert d["agent_id"] == "sub1"


def test_sub_agent_result():
    r = SubAgentResult(sub_session_id="SUB-1", status="completed", output="ok")
    assert r.status == "completed"
    d = r.to_dict()
    assert d["output"] == "ok"


def test_spawn_subagent():
    p = AgentProfile(id="parent1", name="Parent")
    r = AgentRunner(p)
    r.create_session()
    spec = SubAgentSpec(task="do something", agent_id="child1")
    res = r.spawn_subagent(spec)
    assert res.status in ("completed", "failed")
    assert len(res.sub_session_id) > 0


def test_spawn_subagent_completes_with_results():
    """Subagent returns results with correct fields."""
    p = AgentProfile(id="parent3", name="Parent")
    r = AgentRunner(p)
    r.create_session()
    spec = SubAgentSpec(task="do work", agent_id="worker")
    res = r.spawn_subagent(spec)
    assert isinstance(res.duration_ms, float)
    assert isinstance(res.tool_calls, int)
    assert res.output != "" or res.status == "completed"


def test_agent_manager_default():
    reset_manager()
    am = get_manager()
    assert "ciel-main" in am.profiles
    assert am.profiles["ciel-main"].is_default


def test_agent_manager_register():
    reset_manager()
    am = get_manager()
    p = AgentProfile(id="custom1", name="Custom1", model="claude-3")
    r = am.register(p)
    assert r.profile.id == "custom1"
    assert am.profiles["custom1"] is p


def test_agent_manager_create_agent():
    reset_manager()
    am = get_manager()
    r = am.create_agent(name="NewAgent", model="gpt-4o",
                        system_prompt="Be helpful")
    assert r.profile.name == "NewAgent"
    assert r.profile.parent_id is None


def test_agent_manager_create_agent_with_parent():
    reset_manager()
    am = get_manager()
    r = am.create_agent(name="ChildAgent", parent_id="parent-xyz")
    assert r.profile.parent_id == "parent-xyz"


def test_agent_manager_get_runner():
    reset_manager()
    am = get_manager()
    default = am.get_runner()
    assert default.profile.id == "ciel-main"
    same = am.get_runner("ciel-main")
    assert same is default


def test_agent_manager_get_runner_nonexistent():
    reset_manager()
    am = get_manager()
    r = am.get_runner("no-such-agent")
    assert r.profile.id == "ciel-main"  # falls back to default


def test_agent_manager_route_to_agent():
    reset_manager()
    am = get_manager()
    r = am.route_to_agent("terminal", "default")
    assert r.profile.id == "ciel-main"


def test_agent_manager_list_agents():
    reset_manager()
    am = get_manager()
    am.create_agent(name="Extra")
    agents = am.list_agents()
    assert len(agents) >= 2
    names = [a["name"] for a in agents]
    assert "CIEL" in names
    assert "Extra" in names


def test_agent_manager_statistics():
    reset_manager()
    am = get_manager()
    stats = am.statistics()
    assert stats["total_agents"] >= 1
    assert stats["active_sessions"] == 0


def test_agent_manager_register_returns_runner():
    reset_manager()
    am = get_manager()
    p = AgentProfile(id="unique1", name="Unique1")
    r = am.register(p)
    assert isinstance(r, AgentRunner)
    assert r.profile.name == "Unique1"


def test_empty_usage_counter():
    p = AgentProfile(id="ec1", name="EmptyCounter")
    r = AgentRunner(p)
    r.create_session()
    assert r.status()["messages"] == 1


def test_session_to_dict():
    s = AgentSession(id="SESS-DICT", agent_id="a1")
    s.add_message(AgentMessage(role="user", content="test"))
    d = s.to_dict()
    assert d["message_count"] == 1
    assert d["channel"] == "terminal"


def test_different_channel_session():
    s = AgentSession(id="SESS-CH", agent_id="a1", channel="web")
    assert s.channel == "web"
    s.add_message(AgentMessage(role="user", content="hello"))
    assert s.messages[0].role == "user"
