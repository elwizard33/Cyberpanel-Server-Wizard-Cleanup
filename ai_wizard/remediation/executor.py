"""Remediation plan executor with evidence preservation.

Translates RemediationPlan actions into side-effect operations while
respecting global and per-action dry_run flags. Supported actions:
 - remove (file unlink with optional evidence copy+hash)
 - kill (SIGTERM to process id)
 - disable (systemctl disable + stop for a service name)

All operations are conservative with input validation and broad
exception handling to prevent partial failure from aborting entire plan.
"""
from __future__ import annotations

from pathlib import Path
from typing import List
import os
import shutil
import signal
import subprocess

from cyberzard.core.models import RemediationPlan, RemediationResult, RemediationAction
from cyberzard.config import RecommendedAction, get_settings, is_path_allowed
from cyberzard.evidence import preserve_file


def _safe_service(name: str) -> bool:
    return bool(name) and all(c.isalnum() or c in ("-", "_", ".") for c in name) and len(name) < 80


def _remove_file(action: RemediationAction, global_dry: bool, preserve: bool, evidence_dir: Path) -> RemediationResult:
    p = Path(action.target)
    dry = global_dry or action.dry_run
    if not is_path_allowed(p):
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=False, message="path_not_allowed")
    if not p.exists():
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=True, message="already_absent")
    evidence_msg = ""
    if preserve and not dry:
        meta = preserve_file(p, evidence_dir)
        if meta.get("error"):
            evidence_msg = f"; evidence_error={meta.get('error')}"
        else:
            evidence_msg = f"; evidence_sha={meta.get('sha256')}"
    if dry:
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=True, message="dry_run", changed=False)
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=True, message="removed" + evidence_msg, changed=True)
    except Exception as e:  # pragma: no cover - defensive
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=False, message=f"remove_failed:{e}")


def _kill_process(action: RemediationAction, global_dry: bool) -> RemediationResult:
    dry = global_dry or action.dry_run
    try:
        pid = int(action.target)
    except ValueError:
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=False, message="invalid_pid")
    if dry:
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=True, message="dry_run", changed=False)
    try:
        os.kill(pid, signal.SIGTERM)
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=True, message="signaled", changed=True)
    except ProcessLookupError:
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=True, message="missing", changed=False)
    except PermissionError:
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=False, message="permission_denied")
    except Exception as e:  # pragma: no cover
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=False, message=f"kill_failed:{e}")


def _disable_service(action: RemediationAction, global_dry: bool) -> RemediationResult:
    dry = global_dry or action.dry_run
    name = action.target
    if not _safe_service(name):
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=False, message="invalid_service_name")
    if dry:
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=True, message="dry_run", changed=False)
    # Attempt systemctl disable then stop
    cmds = [["systemctl", "disable", name], ["systemctl", "stop", name]]
    executed = []
    for cmd in cmds:
        try:
            subprocess.run(cmd, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            executed.append(cmd[1])
        except Exception:
            continue
    if executed:
        return RemediationResult(finding_id=action.finding_id, action=action.action, success=True, message=";".join(executed), changed=True)
    return RemediationResult(finding_id=action.finding_id, action=action.action, success=False, message="no_action")


def execute_plan(plan: RemediationPlan, dry_run: bool | None = None, preserve_evidence: bool | None = None) -> List[RemediationResult]:
    settings = get_settings()
    global_dry = settings.dry_run if dry_run is None else dry_run
    preserve = settings.preserve_evidence if preserve_evidence is None else preserve_evidence
    results: List[RemediationResult] = []
    for action in plan.actions:
        if action.action == RecommendedAction.remove:
            results.append(_remove_file(action, global_dry, preserve, settings.evidence_dir))
        elif action.action == RecommendedAction.kill:
            results.append(_kill_process(action, global_dry))
        elif action.action == RecommendedAction.disable:
            results.append(_disable_service(action, global_dry))
        else:
            results.append(RemediationResult(finding_id=action.finding_id, action=action.action, success=False, message="unsupported_action"))
    return results


__all__ = ["execute_plan"]
