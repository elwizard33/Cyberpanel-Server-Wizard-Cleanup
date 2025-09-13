from __future__ import annotations
"""Guided execution engine for email hardening/remediation actions.

Features:
- Command safety validation (binary whitelist + heuristics)
- Dry-run support (simulate success without running)
- Sequential execution with optional early stop (fail_fast)
- Optional AI justification/refinement hooks (provider layer already handles fallbacks)
- Risk filtering (skip actions above max_risk)
- Structured result objects + summary

NOTE: Actual AI integration (justify/refine) consumed from provider_email helpers
via agent_engine.provider_email when available. This module keeps pure execution logic.
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Tuple, Optional
import os, shlex, subprocess, time, json, pathlib, shutil

# Conservative whitelist of root-level binaries we permit.
ALLOWED_BINARIES = {
    "systemctl", "postqueue", "postsuper", "sed", "curl", "postconf", "tee",
    "apt-get", "bash", "ufw", "iptables", "chmod", "echo", "date",
}

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}

@dataclass
class EmailActionExecutionResult:
    type: str
    category: str
    risk: str
    reason: str
    command_preview: str
    skipped: bool = False
    skip_reason: Optional[str] = None
    unsafe: bool = False
    unsafe_reason: Optional[str] = None
    dry_run: bool = False
    success: Optional[bool] = None
    return_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_sec: float = 0.0
    refined_command: Optional[str] = None
    refinement_attempted: bool = False
    refinement_success: Optional[bool] = None
    justification: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ---------------- Safety -----------------

def _extract_first_binary(cmd: str) -> Optional[str]:
    try:
        parts = shlex.split(cmd, posix=True)
        if not parts:
            return None
        # handle constructs like: bash -lc 'actual ...'
        if parts[0] == "bash" and len(parts) > 1:
            return "bash"
        return parts[0]
    except Exception:
        return None

def is_command_safe(cmd: str) -> Tuple[bool, str]:
    if not cmd.strip():
        return False, "empty command"
    bin_ = _extract_first_binary(cmd)
    if not bin_:
        return False, "unable to parse command"
    base = os.path.basename(bin_)
    if base not in ALLOWED_BINARIES:
        return False, f"binary '{base}' not in whitelist"
    # Heuristic forbids redirection to overwrite critical files other than explicit whitelisted patterns
    forbidden = ["/etc/passwd", "/etc/shadow"]
    for f in forbidden:
        if f in cmd:
            return False, f"references forbidden path {f}"
    if "wget " in cmd or "curl |" in cmd:
        return False, "network download piping not allowed"
    # Multi-line here-doc allowed only for tee temporary config writes; limit length
    if "<<'EOF'" in cmd and cmd.count("EOF") > 4:
        return False, "excessive heredoc usage"
    return True, "ok"

# ---------------- Execution -----------------

def _run_shell(cmd: str, timeout: int) -> Tuple[int, str, str]:
    try:
        cp = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return cp.returncode, cp.stdout, cp.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:  # pragma: no cover - defensive
        return 125, "", str(e)

# ---------------- Main guided flow -----------------

def execute_action(action: Dict[str, Any], timeout: int = 30, dry_run: bool = False) -> EmailActionExecutionResult:
    result = EmailActionExecutionResult(
        type=action.get("type"),
        category=action.get("category"),
        risk=action.get("risk"),
        reason=action.get("reason"),
        command_preview=action.get("command_preview", ""),
        dry_run=dry_run,
    )
    # Safety first
    is_safe, why = is_command_safe(result.command_preview)
    if not is_safe:
        result.unsafe = True
        result.unsafe_reason = why
        result.success = False
        return result
    if dry_run:
        result.success = True
        return result
    start = time.time()
    rc, so, se = _run_shell(result.command_preview, timeout=timeout)
    result.duration_sec = time.time() - start
    result.return_code = rc
    result.stdout = (so or "")[:20000]
    result.stderr = (se or "")[:20000]
    result.success = rc == 0
    return result

# Guided runner

def run_guided(
    actions: List[Dict[str, Any]],
    interactive: bool = True,
    auto_approve: bool = False,
    max_risk: str = "high",
    dry_run: bool = False,
    ai_refine: bool = True,
    scan_results: Optional[Dict[str, Any]] = None,
    provider_enabled: bool = True,
    fail_fast: bool = True,
    timeout: int = 60,
    log_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a sequence of actions with optional refinement.

    Returns dict with executions (list) + summary.
    interactive & auto_approve are placeholders (UI/CLI layer can prompt). This
    engine respects auto_approve; if interactive is False and not auto_approve,
    all actions are skipped with reason.
    """
    executions: List[EmailActionExecutionResult] = []
    if max_risk not in RISK_ORDER:
        max_risk = "high"
    max_rank = RISK_ORDER[max_risk]

    # Try to import provider helpers lazily
    justify = None
    refine = None
    if provider_enabled:
        try:  # pragma: no cover - optional
            from .agent_engine.provider_email import justify_email_action, refine_email_action  # type: ignore
            justify = justify_email_action
            refine = refine_email_action
        except Exception:
            provider_enabled = False

    if log_dir:
        pathlib.Path(log_dir).mkdir(parents=True, exist_ok=True)

    for action in actions:
        risk = action.get("risk", "low")
        if RISK_ORDER.get(risk, 0) > max_rank:
            r = EmailActionExecutionResult(
                type=action.get("type"),
                category=action.get("category"),
                risk=risk,
                reason=action.get("reason"),
                command_preview=action.get("command_preview", ""),
                skipped=True,
                skip_reason=f"risk {risk} exceeds max_risk {max_risk}",
            )
            executions.append(r)
            continue
        if not auto_approve and interactive is False:
            r = EmailActionExecutionResult(
                type=action.get("type"),
                category=action.get("category"),
                risk=risk,
                reason=action.get("reason"),
                command_preview=action.get("command_preview", ""),
                skipped=True,
                skip_reason="not approved (interactive disabled)",
            )
            executions.append(r)
            continue

        res = execute_action(action, timeout=timeout, dry_run=dry_run)
        # Optional justification
        if provider_enabled and justify and not res.skipped and not res.unsafe:
            try:
                summary = (scan_results or {}).get("summary", {}) if isinstance(scan_results, dict) else {}
                res.justification = justify(action, summary)
            except Exception:  # pragma: no cover
                pass
        # Failure refinement attempt once
        if (
            provider_enabled
            and ai_refine
            and refine
            and not res.dry_run
            and not res.skipped
            and not res.unsafe
            and res.success is False
            and not res.refinement_attempted
        ):
            res.refinement_attempted = True
            try:
                summary = (scan_results or {}).get("summary", {}) if isinstance(scan_results, dict) else {}
                new_cmd = refine(action, res.stdout, res.stderr, res.stderr or "failure", summary)
                if new_cmd and new_cmd != res.command_preview:
                    # Validate safety of refined command
                    safe2, why2 = is_command_safe(new_cmd)
                    if safe2:
                        res.refined_command = new_cmd
                        # execute refined
                        r2 = execute_action({**action, "command_preview": new_cmd}, timeout=timeout, dry_run=dry_run)
                        res.refinement_success = bool(r2.success)
                        # store second attempt outputs appended
                        if r2.stdout:
                            res.stdout += "\n[REFINED STDOUT]\n" + r2.stdout[:10000]
                        if r2.stderr:
                            res.stderr += "\n[REFINED STDERR]\n" + r2.stderr[:10000]
                    else:
                        res.refined_command = None
                        res.refinement_success = False
                else:
                    res.refinement_success = False
            except Exception:  # pragma: no cover
                res.refinement_success = False

        executions.append(res)
        if fail_fast and res.success is False and not res.dry_run:
            break

    # Logging
    if log_dir:
        try:
            log_path = pathlib.Path(log_dir) / f"email_exec_{int(time.time())}.json"
            data = [r.to_dict() for r in executions]
            log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:  # pragma: no cover
            pass

    summary = {
        "total": len(executions),
        "executed": sum(1 for r in executions if not r.skipped and not r.unsafe),
        "skipped": sum(1 for r in executions if r.skipped),
        "unsafe": sum(1 for r in executions if r.unsafe),
        "success": sum(1 for r in executions if r.success),
        "failures": sum(1 for r in executions if r.success is False),
        "refined_success": sum(1 for r in executions if r.refinement_success),
    }

    return {"executions": [r.to_dict() for r in executions], "summary": summary}

__all__ = [
    "run_guided",
    "execute_action",
    "is_command_safe",
    "EmailActionExecutionResult",
]
