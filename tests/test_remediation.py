from cyberzard.core.models import RemediationPlan, RemediationAction
from cyberzard.remediation import execute_plan
from cyberzard.config import RecommendedAction


def test_execute_empty_plan():
    plan = RemediationPlan(actions=[], summary="empty plan")
    results = execute_plan(plan, dry_run=True)
    assert results == []


def test_execute_dummy_remove_action(tmp_path):
    # Use a path inside /tmp to satisfy allowlist constraints
    allowed_dir = tmp_path  # pytest tmp usually inside /private/var/... may not match allowlist
    # Fallback: create explicit /tmp file
    import os, pathlib
    explicit_tmp = pathlib.Path('/tmp') / 'cp_cyberzard_test_dummy.txt'
    explicit_tmp.write_text('data')
    target = explicit_tmp
    action = RemediationAction(
        finding_id="test",
        action=RecommendedAction.remove,
        target=str(target),
        dry_run=True,  # keep safe
    )
    plan = RemediationPlan(actions=[action], summary="single remove dry run")
    results = execute_plan(plan, dry_run=True)
    assert len(results) == 1
    r = results[0]
    assert r.finding_id == "test"
    assert r.success is True or r.message in {"path_not_allowed"}
    # Dry run should not remove file if success
    if r.success:
        assert target.exists()
