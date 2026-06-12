"""Tests for CIEL API — nouvelles capacités (toolforge, vision, control, sandbox, clones, websearch)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ciel.api.server import create_app
from ciel.api.models import ServerConfig


@pytest.fixture
def client():
    cfg = ServerConfig(host="test", port=0, api_keys=[])
    app = create_app(config=cfg)
    with TestClient(app) as c:
        yield c


def test_capabilities_router_registered(client):
    routes = [r.path for r in client.app.routes if hasattr(r, "path")]
    capability_endpoints = [e for e in routes if "/toolforge/" in e or "/vision/" in e
                            or "/control/" in e or "/sandbox/" in e
                            or "/clones/" in e or "/web/" in e]
    assert capability_endpoints


# ── ToolForge ──

def test_tool_forge(client):
    resp = client.post("/v1/toolforge/forge?name=hello&description=Says hello&body=return+%22hello%22")
    data = resp.json()
    assert data["success"] is True
    assert data["result"]["tool"]["name"] == "hello"


def test_tool_forge_existing(client):
    client.post("/v1/toolforge/forge?name=hello2&description=Says hello&body=return+%22hello%22")
    resp2 = client.post("/v1/toolforge/forge?name=hello2&description=Again")
    data2 = resp2.json()
    # Le moteur met a jour l'outil existant sans erreur
    assert data2["success"] is True


def test_tool_find_by_name(client):
    client.post("/v1/toolforge/forge?name=summer&description=Summer+tool&body=return+1")
    resp = client.get("/v1/toolforge/find?query=summer")
    data = resp.json()
    assert data["success"] is True
    assert len(data["result"]) >= 1


def test_tool_run(client):
    client.post("/v1/toolforge/forge?name=hi&body=return+%22hi%22")
    resp = client.post("/v1/toolforge/run/hi")
    data = resp.json()
    assert data["success"] is True


def test_tool_run_nonexistent(client):
    resp = client.post("/v1/toolforge/run/nonexistent_tool_xyz")
    data = resp.json()
    assert data["success"] is True
    assert "error" in data["result"]["result"]


def test_tool_suggest(client):
    resp = client.post("/v1/toolforge/suggest?problem=sort+numbers")
    data = resp.json()
    assert data["success"] is True


# ── Vision ──

def test_vision_screenshot(client):
    resp = client.post("/v1/vision/screenshot")
    data = resp.json()
    assert data["success"] is True


def test_vision_last(client):
    client.post("/v1/vision/screenshot")
    resp = client.get("/v1/vision/last")
    data = resp.json()
    assert data["success"] is True


# ── Control ──

def test_control_move(client):
    resp = client.post("/v1/control/move?x=100&y=200")
    data = resp.json()
    assert data["success"] is True
    assert data["result"]["action"]["action"] == "mouse_move"


def test_control_click(client):
    resp = client.post("/v1/control/click?button=left&x=50&y=60")
    data = resp.json()
    assert data["success"] is True


def test_control_type(client):
    resp = client.post("/v1/control/type?text=hello+world")
    data = resp.json()
    assert data["success"] is True


def test_control_key(client):
    resp = client.post("/v1/control/key?key=enter")
    data = resp.json()
    assert data["success"] is True


def test_control_clipboard_set(client):
    resp = client.post("/v1/control/clipboard?text=test+data")
    data = resp.json()
    assert data["success"] is True


def test_control_clipboard_get(client):
    client.post("/v1/control/clipboard?text=read+this")
    resp = client.get("/v1/control/clipboard")
    data = resp.json()
    assert data["success"] is True
    assert data["result"]["text"] == "read this"


def test_control_live_mode(client):
    resp = client.post("/v1/control/live?enabled=true")
    data = resp.json()
    assert data["success"] is True
    assert data["result"]["live_mode"] is True

    resp2 = client.post("/v1/control/live?enabled=false")
    data2 = resp2.json()
    assert data2["success"] is True
    assert data2["result"]["live_mode"] is False


# ── Sandbox ──

def test_sandbox_run_python(client):
    resp = client.post("/v1/sandbox/run?code=print(42)&language=python&timeout=10")
    data = resp.json()
    assert data["success"] is True
    assert "stdout" in data["result"]["result"]
    assert "42" in data["result"]["result"]["stdout"]


def test_sandbox_run_js(client):
    resp = client.post("/v1/sandbox/run?code=console.log(7*6)&language=js&timeout=10")
    data = resp.json()
    assert data["success"] is True


# ── Clones ──

def test_clone_spawn(client):
    resp = client.post("/v1/clones/spawn?name=test-clone&clone_type=worker&task=explore")
    data = resp.json()
    assert data["success"] is True
    assert data["success"] is True
    cid = data["result"]["clone"]["id"]
    assert cid.startswith("CLN-")


def test_clone_list(client):
    resp = client.get("/v1/clones/list")
    data = resp.json()
    assert data["success"] is True


def test_clone_task(client):
    resp = client.post("/v1/clones/spawn?name=task-clone&clone_type=scout&task=scan")
    data = resp.json()
    cid = data["result"]["clone"]["id"]
    resp2 = client.post(f"/v1/clones/task?clone_id={cid}&task=new+mission")
    data2 = resp2.json()
    assert data2["success"] is True


def test_clone_terminate(client):
    resp = client.post("/v1/clones/spawn?name=kill-clone&clone_type=phantom&task=covert")
    data = resp.json()
    cid = data["result"]["clone"]["id"]
    resp2 = client.post(f"/v1/clones/terminate?clone_id={cid}")
    data2 = resp2.json()
    assert data2["success"] is True


def test_clone_recall_all(client):
    resp = client.post("/v1/clones/recall_all")
    data = resp.json()
    assert data["success"] is True


# ── WebSearch ──

def test_web_search(client):
    resp = client.get("/v1/web/search?query=ciel+ai&max_results=3")
    data = resp.json()
    assert data["success"] is True


def test_web_fetch(client):
    resp = client.post("/v1/web/fetch?url=https://example.com")
    data = resp.json()
    assert data["success"] is True


# ── Erreurs et cas limites ──

def test_control_move_negative(client):
    resp = client.post("/v1/control/move?x=-10&y=-20")
    data = resp.json()
    assert data["success"] is True


def test_sandbox_run_empty_code(client):
    resp = client.post("/v1/sandbox/run?code=&language=python")
    data = resp.json()
    assert data["success"] is True


def test_clone_spawn_invalid_type(client):
    resp = client.post("/v1/clones/spawn?name=x&clone_type=invalid_type&task=")
    data = resp.json()
    # Le moteur accepte tout type sans validation
    assert data["success"] is True


# ── Database API ──

def test_db_initialize(client):
    resp = client.post("/v1/db/init")
    data = resp.json()
    assert data["success"] is True


def test_db_register_table(client):
    client.post("/v1/db/init")
    resp = client.post("/v1/db/register_table?name=api_test"
                       "&columns=id:TEXT,name:TEXT,value:REAL,created_at:REAL,updated_at:REAL")
    data = resp.json()
    assert data["success"] is True


def test_db_insert_and_query(client):
    client.post("/v1/db/init")
    client.post("/v1/db/register_table?name=api_test"
                "&columns=id:TEXT,name:TEXT,value:REAL,created_at:REAL,updated_at:REAL")
    resp = client.post("/v1/db/insert?table=api_test"
                       "&data={\"name\":\"api row\",\"value\":42.0}")
    data = resp.json()
    assert data["success"] is True
    assert data["result"]["status"] == "ok"
    resp2 = client.get("/v1/db/query?table=api_test&filters={\"name\":\"api row\"}")
    data2 = resp2.json()
    assert data2["success"] is True


def test_db_update(client):
    client.post("/v1/db/init")
    client.post("/v1/db/register_table?name=api_test"
                "&columns=id:TEXT,name:TEXT,value:REAL,created_at:REAL,updated_at:REAL")
    r = client.post("/v1/db/insert?table=api_test"
                    "&data={\"name\":\"old\",\"value\":0.0}")
    rid = r.json()["result"]["id"]
    resp = client.post(f"/v1/db/update?table=api_test&id={rid}"
                       "&data={\"value\":999.0}")
    data = resp.json()
    assert data["success"] is True


def test_db_delete(client):
    client.post("/v1/db/init")
    client.post("/v1/db/register_table?name=api_test"
                "&columns=id:TEXT,name:TEXT,value:REAL,created_at:REAL,updated_at:REAL")
    r = client.post("/v1/db/insert?table=api_test"
                    "&data={\"name\":\"delete me\",\"value\":1.0}")
    rid = r.json()["result"]["id"]
    resp = client.post(f"/v1/db/delete?table=api_test&id={rid}")
    data = resp.json()
    assert data["success"] is True


def test_db_export(client):
    client.post("/v1/db/init")
    client.post("/v1/db/register_table?name=api_test"
                "&columns=id:TEXT,name:TEXT,value:REAL,created_at:REAL,updated_at:REAL")
    client.post("/v1/db/insert?table=api_test"
                "&data={\"name\":\"exp\",\"value\":1.0}")
    resp = client.get("/v1/db/export/api_test")
    data = resp.json()
    assert data["success"] is True


def test_db_stats(client):
    client.post("/v1/db/init")
    resp = client.get("/v1/db/stats")
    data = resp.json()
    assert data["success"] is True


# ── Config API ──

def test_config_get(client):
    resp = client.get("/v1/config?key=api.port")
    data = resp.json()
    assert data["success"] is True


def test_config_set(client):
    resp = client.post("/v1/config?key=api.port&value=9000")
    data = resp.json()
    assert data["success"] is True
    # Verify
    resp2 = client.get("/v1/config?key=api.port")
    data2 = resp2.json()
    assert data2["result"]["value"] == 9000


def test_config_build(client):
    resp = client.post("/v1/config/build")
    data = resp.json()
    assert data["success"] is True
    assert "api" in data["result"]["config"]


def test_config_stats(client):
    resp = client.get("/v1/config/stats")
    data = resp.json()
    assert data["success"] is True


# ── Cache API ──

def test_cache_set_and_get(client):
    resp = client.post("/v1/cache/mykey?value=hello+world&ttl=300")
    data = resp.json()
    assert data["success"] is True
    resp2 = client.get("/v1/cache/mykey")
    data2 = resp2.json()
    assert data2["success"] is True
    assert data2["result"]["value"] == "hello world"


def test_cache_get_missing(client):
    resp = client.get("/v1/cache/nonexistent_key_xyz")
    data = resp.json()
    assert data["success"] is True
    assert data["result"]["value"] is None


def test_cache_delete(client):
    client.post("/v1/cache/delkey?value=delete+me")
    resp = client.delete("/v1/cache/delkey")
    data = resp.json()
    assert data["success"] is True
    resp2 = client.get("/v1/cache/delkey")
    data2 = resp2.json()
    assert data2["result"]["value"] is None


def test_cache_clear(client):
    client.post("/v1/cache/c1?value=1")
    client.post("/v1/cache/c2?value=2")
    resp = client.post("/v1/cache/clear")
    data = resp.json()
    assert data["success"] is True


def test_cache_stats(client):
    resp = client.get("/v1/cache/stats")
    data = resp.json()
    assert data["success"] is True
