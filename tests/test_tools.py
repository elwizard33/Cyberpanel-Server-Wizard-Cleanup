from pathlib import Path

from cyberzard.tools.registry import execute_tool, get_schema
import cyberzard.tools  # noqa: F401


def test_schema_contains_core_tools():
    names = {t['name'] for t in get_schema()}
    for required in {"read_file","list_dir","run_scan","sandbox_run","execute_remediation"}:
        assert required in names


def test_sandbox_reject_import():
    res = execute_tool("sandbox_run", {"source": "import os"})
    assert "error" in res


def test_sandbox_exec_simple():
    res = execute_tool("sandbox_run", {"source": "print(1+1)"})
    assert res.get("returncode") == 0
    assert "2" in res.get("stdout", "")


def test_execute_remediation_remove(tmp_path: Path):
    f = tmp_path / "sample.txt"
    f.write_text("x")
    # Dry run is triggered by caller; tool expects explicit dry_run flag
    res = execute_tool("execute_remediation", {"action": "remove", "target": str(f), "dry_run": True})
    assert res["status"] in {"would_remove","absent"}
    res2 = execute_tool("execute_remediation", {"action": "remove", "target": str(f), "dry_run": False})
    assert res2["status"] in {"removed","absent"}


def test_execute_remediation_kill_dryrun():
    res = execute_tool("execute_remediation", {"action": "kill", "target": "999999", "dry_run": True})
    assert res["status"] == "would_kill"
