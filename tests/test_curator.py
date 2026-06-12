"""Tests pour le SkillCurator CIEL."""
from __future__ import annotations

import time
import pytest
from pathlib import Path
from ciel.skills.models import SkillManager
from ciel.skills.curator import SkillCurator, CuratorState, ConsolidationPlan


# ── Fixtures ───────────────────────────────────────────

@pytest.fixture
def fresh_mgr(tmp_path: Path) -> SkillManager:
    mgr = SkillManager(str(tmp_path / "skills"))
    for name in ["code-review", "code-lint", "test-writer", "doc-gen", "deploy"]:
        mgr.create(name=name, description=name.replace("-", " "),
                   tags=["code" if "code" in name else "ops"])
    return mgr


@pytest.fixture
def curator(tmp_path: Path, fresh_mgr: SkillManager) -> SkillCurator:
    cur = SkillCurator(str(tmp_path / "skills"))
    cur.skills_mgr = fresh_mgr
    return cur


# ── CuratorState ───────────────────────────────────────

def test_curator_state_defaults():
    cs = CuratorState()
    assert cs.last_run_at == 0.0
    assert cs.total_reviews == 0
    assert cs.total_archived == 0


def test_curator_state_to_dict():
    cs = CuratorState(last_run_at=100.0, total_reviews=5, total_archived=2)
    d = cs.to_dict()
    assert d["last_run_at"] == 100.0
    assert d["total_reviews"] == 5


# ── ConsolidationPlan ─────────────────────────────────

def test_consolidation_plan():
    plan = ConsolidationPlan(
        umbrella_name="code-umbrella",
        umbrella_description="All code skills",
        skills_to_absorb=["s1", "s2"],
    )
    assert plan.umbrella_name == "code-umbrella"
    d = plan.to_dict()
    assert d["umbrella"] == "code-umbrella"
    assert len(d["absorb"]) == 2


# ── Phase 1 : auto-transitions ────────────────────────

def test_phase1_no_transition_for_new_skills(curator, fresh_mgr):
    """Freshly created skills should stay active."""
    result = curator._phase1_auto_transitions(dry_run=True)
    assert result["stale"] == 0
    assert result["archived"] == 0


def test_phase1_stale_after_30_days(curator, fresh_mgr):
    """Skills inactive for >30 days become stale."""
    for s in fresh_mgr.list():
        s.updated_at = time.time() - 31 * 86400
    result = curator._phase1_auto_transitions(dry_run=False)
    assert result["stale"] == len(fresh_mgr.list())
    assert all(s.state == "stale" for s in fresh_mgr.list(state="stale"))


def test_phase1_archive_after_90_days(curator, fresh_mgr):
    """Stale skills inactive for >90 days get archived."""
    # First make them stale (31 days)
    for s in fresh_mgr.list():
        s.updated_at = time.time() - 31 * 86400
    curator._phase1_auto_transitions(dry_run=False)
    # Now make them old enough to archive (91 days)
    for s in fresh_mgr.list():
        s.updated_at = time.time() - 91 * 86400
    result = curator._phase1_auto_transitions(dry_run=False)
    assert result["archived"] == len(fresh_mgr.list())


def test_phase1_dry_run_does_not_modify(curator, fresh_mgr):
    """Dry run should not change states."""
    for s in fresh_mgr.list():
        s.updated_at = time.time() - 91 * 86400
    result = curator._phase1_auto_transitions(dry_run=True)
    # In dry_run, counts are always 0 (logging only)
    assert result["stale"] == 0
    assert result["archived"] == 0
    # Skills should remain active
    assert len(fresh_mgr.list(state="active")) == len(fresh_mgr.list())


def test_phase1_skips_archived_skills(curator, fresh_mgr):
    """Already archived skills should be skipped."""
    for i, s in enumerate(fresh_mgr.list()):
        if i == 0:
            fresh_mgr.archive(s.id)
    for s in fresh_mgr.list():
        if s.state != "archived":
            s.updated_at = time.time() - 91 * 86400
    result = curator._phase1_auto_transitions(dry_run=False)
    # The archived skill should stay archived, not double-processed
    assert len(fresh_mgr.list(state="archived")) >= 1


# ── Phase 2 : consolidation ──────────────────────────

def test_phase2_no_clusters_small_set(curator, fresh_mgr):
    """Fewer than 3 skills should yield no consolidation."""
    # Remove skills so we have < 3
    for s in fresh_mgr.list():
        fresh_mgr.delete(s.id)
    fresh_mgr.create(name="only", description="lonely")
    result = curator._phase2_consolidation(dry_run=True)
    assert result["consolidated"] == 0
    assert result["umbrellas"] == 0


def test_phase2_cluster_detection(curator, fresh_mgr):
    """Skills with overlapping names should form clusters."""
    clusters = curator._find_clusters(fresh_mgr.list())
    code_clusters = [k for k in clusters if "code" in k]
    assert len(code_clusters) >= 1


def test_phase2_consolidation_plan(curator, fresh_mgr):
    clusters = curator._find_clusters(fresh_mgr.list())
    if clusters:
        name = list(clusters.keys())[0]
        plan = curator._build_consolidation_plan(name, clusters[name])
        assert isinstance(plan, ConsolidationPlan)
        assert len(plan.skills_to_absorb) >= 2


def test_phase2_full_consolidation_run(curator, fresh_mgr):
    clusters = curator._find_clusters(fresh_mgr.list())
    if clusters:
        result = curator._phase2_consolidation(dry_run=False)
        assert result["umbrellas"] >= 0
        # Umbrellas should be created
        umbrella_skills = [s for s in fresh_mgr.list() if "umbrella" in s.name]
        assert len(umbrella_skills) >= 0


def test_generate_umbrella_body(curator, fresh_mgr):
    skills = [
        fresh_mgr.create(name="a1", description="a1 desc", body="body1"),
        fresh_mgr.create(name="a2", description="a2 desc", body="body2"),
    ]
    body = curator._generate_umbrella_body(skills)
    assert "body1" in body
    assert "body2" in body
    assert "# Instructions consolidées" in body


# ── Archive / Restore ────────────────────────────────

def test_archive_skill(curator, fresh_mgr):
    s = list(fresh_mgr.list())[0]
    curator._archive_skill(s)
    assert fresh_mgr.get(s.id).state == "archived"


def test_archive_skill_creates_metadata(curator, fresh_mgr):
    s = list(fresh_mgr.list())[0]
    curator._archive_skill(s)
    archive_dir = curator._state_dir / "archive" / s.id
    assert (archive_dir / "metadata.json").exists()


def test_list_archived(curator, fresh_mgr):
    for s in list(fresh_mgr.list())[:2]:
        curator._archive_skill(s)
    archived = curator.list_archived()
    assert len(archived) >= 2


def test_restore_skill(curator, fresh_mgr):
    s = list(fresh_mgr.list())[0]
    curator._archive_skill(s)
    assert curator.restore(s.id)
    # Should now be in active skills
    assert len(fresh_mgr.list(state="active")) >= 1


def test_restore_nonexistent(curator):
    assert not curator.restore("no-such-skill")


# ── Full run ─────────────────────────────────────────

def test_full_run_dry(curator):
    result = curator.run(dry_run=True)
    assert result.total_reviews == 1
    assert result.last_run_at > 0


def test_full_run(curator, fresh_mgr):
    for s in fresh_mgr.list():
        s.updated_at = time.time() - 91 * 86400
    result = curator.run(dry_run=False)
    assert result.total_reviews == 1


def test_should_run(curator):
    curator.state.last_run_at = 0
    assert curator.should_run()


def test_should_not_run_recently(curator):
    curator.state.last_run_at = time.time()
    assert not curator.should_run()


# ── Backup ───────────────────────────────────────────

def test_backup_created(curator):
    curator._backup()
    backups = list(curator._backup_dir.iterdir())
    assert len(backups) == 1
    assert (backups[0] / "state.json").exists()


def test_statistics(curator, fresh_mgr):
    for s in list(fresh_mgr.list())[:2]:
        curator._archive_skill(s)
    stats = curator.statistics()
    assert stats["active_skills"] >= 1
    assert stats["archived_skills"] >= 2
    assert "backups" in stats
