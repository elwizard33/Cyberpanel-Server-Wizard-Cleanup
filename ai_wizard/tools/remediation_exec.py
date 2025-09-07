"""Remediation execution tool (limited).

Executes a single remediation action. Supported actions (when dry_run=False):
 - remove_file: unlink target file if exists and within allowed roots
 - kill_process: send SIGTERM to pid (numeric target)

Other actions return unsupported. Designed to be conservative; no recursive
deletions or modifications beyond simple unlink / signal.
"""
from __future__ import annotations

import os
import signal
from pathlib import Path
from typing import Dict, Any

from cyberzard.config import RecommendedAction
from .registry import register_tool

_ALLOWED_FILE_ROOTS = [Path("/tmp"), Path("/var"), Path.cwd()]


def _file_allowed(p: Path) -> bool:
    try:
        rp = p.resolve()
    except Exception:
        return False
    for root in _ALLOWED_FILE_ROOTS:
        try:
            if str(rp).startswith(str(root.resolve())):
                return True
        except Exception:
            continue
    return False


@register_tool(description="Execute a remediation action (remove / kill)")
def execute_remediation(action: str, target: str, dry_run: bool = True) -> Dict[str, Any]:
    """Execute a limited remediation action.

    Parameters:
        action: one of RecommendedAction values
        target: file path or pid (string)
        dry_run: if True, only report what would happen
    """
    if action not in {a.value for a in RecommendedAction}:
        return {"error": "unsupported_action"}
    # Map to internal behaviors
    if action == RecommendedAction.remove.value:
        p = Path(target)
        if not _file_allowed(p):
            return {"error": "forbidden_path"}
        if not p.exists():
            return {"status": "absent"}
        if dry_run:
            return {"status": "would_remove", "path": str(p)}
        try:
            p.unlink()
            return {"status": "removed", "path": str(p)}
        except Exception as e:
            return {"error": "remove_failed", "message": str(e)}
    elif action == RecommendedAction.kill.value:
        try:
            pid = int(target)
        except ValueError:
            return {"error": "invalid_pid"}
        if dry_run:
            return {"status": "would_kill", "pid": pid}
        try:
            os.kill(pid, signal.SIGTERM)
            return {"status": "signaled", "pid": pid}
        except ProcessLookupError:
            return {"status": "missing", "pid": pid}
        except PermissionError:
            return {"error": "permission_denied", "pid": pid}
        except Exception as e:
            return {"error": "kill_failed", "pid": pid, "message": str(e)}
    else:
        return {"error": "unsupported_exec_action"}


__all__ = ["execute_remediation"]
