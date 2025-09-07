from cyberzard.scanners import run_all_scanners
from cyberzard.core.models import Finding


def test_run_all_scanners_returns_findings_list():
    findings = run_all_scanners()
    assert isinstance(findings, list)
    # Each element should be a Finding
    for f in findings:
        assert isinstance(f, Finding)
    # Basic sanity: no duplicate ids
    ids = [f.id for f in findings]
    assert len(ids) == len(set(ids))
