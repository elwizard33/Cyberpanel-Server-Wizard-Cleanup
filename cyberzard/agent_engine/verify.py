from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class ProbeContext:
    """Track probe budget, consent, and cached data for verification.

    This object is intentionally simple and has no side effects at import time.
    """

    def __init__(
        self,
        *,
        allow_probes: bool,
        max_probes: int,
        consent_callback: Optional[Callable[[str], bool]] = None,
    ) -> None:
        self.allow_probes = bool(allow_probes)
        self.remaining = int(max(0, max_probes))
        self.consent_callback = consent_callback
        self._consent_cache: Dict[str, bool] = {}
        self.consent_log: List[Dict[str, Any]] = []
        self.probes_skipped = 0
        self.ps_cache: Optional[str] = None

    def allow(self, category: str) -> bool:
        """Check consent for a probe category and budget availability."""
        if not self.allow_probes:
            self.probes_skipped += 1
            return False
        if self.remaining <= 0:
            return False
        if category in self._consent_cache:
            return self._consent_cache[category]
        approved = True
        if self.consent_callback is not None:
            try:
                approved = bool(self.consent_callback(category))
            except Exception:
                approved = False
        self._consent_cache[category] = approved
        self.consent_log.append({"category": category, "approved": approved})
        return approved

    def consume(self, n: int = 1) -> bool:
        if self.remaining >= n:
            self.remaining -= n
            return True
        return False


def _probe_systemd_status(ctx: ProbeContext, unit: str) -> Optional[str]:
    """Safely query systemctl is-active for a unit with a short timeout.

    Returns the status string (e.g., 'active', 'inactive') or None on failure.
    """
    if not ctx.allow("systemd") or not ctx.consume():
        return None
    try:
        import shutil
        import subprocess
        if shutil.which("systemctl") is None:
            return None
        cp = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=2,
        )
        out = (cp.stdout or cp.stderr or "").strip()
        return out or None
    except Exception:
        return None


def _read_file_excerpt(ctx: ProbeContext, path: str, lines: int = 40) -> Optional[str]:
    """Read up to N lines from a file safely (read-only)."""
    if not ctx.allow("file") or not ctx.consume():
        return None
    try:
        data: List[str] = []
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for _ in range(max(0, lines)):
                line = fh.readline()
                if not line:
                    break
                data.append(line)
        return "".join(data)
    except Exception:
        return None


def _capture_ps(ctx: ProbeContext) -> Optional[str]:
    """Capture ps aux output once and cache it in the context."""
    if ctx.ps_cache is not None:
        return ctx.ps_cache
    if not ctx.allow("ps") or not ctx.consume():
        return None
    try:
        import subprocess
        cp = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=2)
        ctx.ps_cache = (cp.stdout or cp.stderr or "").strip()
        return ctx.ps_cache
    except Exception:
        return None

def verify_plan(
    scan_results: Dict[str, Any],
    plan: Dict[str, Any],
    *,
    allow_probes: bool,
    max_probes: int = 5,
    consent_callback: Optional[Callable[[str], bool]] = None,
) -> Dict[str, Any]:
    """Verify proposed actions against evidence and optional safe probes.

    This is a skeleton implementation that returns the required structure.
    Later tasks will add deterministic heuristics and optional probes.
    """
    ctx = ProbeContext(allow_probes=allow_probes, max_probes=max_probes, consent_callback=consent_callback)

    import os

    verified_actions: List[Dict[str, Any]] = []
    downgraded: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []

    actions = []
    try:
        actions = plan.get("plan", {}).get("actions", []) if isinstance(plan, dict) else []
    except Exception:
        actions = []

    # Build quick indexes from scan_results for evidence lookups
    systemd = scan_results.get("systemd", {}) if isinstance(scan_results, dict) else {}
    units: List[Dict[str, Any]] = systemd.get("units_found", []) if isinstance(systemd, dict) else []
    units_by_unit = {u.get("unit"): u for u in units if isinstance(u, dict)}

    cron = scan_results.get("cron", {}) if isinstance(scan_results, dict) else {}
    cron_entries: List[Dict[str, Any]] = cron.get("suspicious_entries", []) if isinstance(cron, dict) else []

    suspicious_processes: List[Dict[str, Any]] = scan_results.get("suspicious_processes", []) if isinstance(scan_results, dict) else []
    proc_indicators = {p.get("indicator") for p in suspicious_processes if isinstance(p, dict)}

    ld_preload_exists = bool(scan_results.get("ld_preload", {}).get("exists")) if isinstance(scan_results, dict) else False

    # Heuristic classification of each action (with optional probes)
    for a in actions:
        if not isinstance(a, dict):
            dropped.append({"action": a, "reason": "invalid_action_shape"})
            continue
        a_type = a.get("type")
        target = a.get("target")

        # systemd unit handling
        if a_type == "systemd_unit":
            unit = str(target) if target else None
            info = units_by_unit.get(unit) if unit else None
            if info:
                status = (info.get("status") or "").strip().lower()
                unit_file = info.get("unit_file")
                if status == "active" or unit_file:
                    verified_actions.append(a)
                else:
                    # Try a quick probe to confirm status
                    probed = _probe_systemd_status(ctx, unit) if unit else None
                    if probed and probed.strip().lower() == "active":
                        verified_actions.append(a)
                    else:
                        # As a final deterministic check, see if a unit file exists in standard location
                        unit_path = f"/etc/systemd/system/{unit}" if unit else None
                        try:
                            import os as _os
                            if unit_path and _os.path.exists(unit_path):
                                verified_actions.append(a)
                            else:
                                dropped.append({"action": a, "reason": "systemd_inactive_and_no_unit_file"})
                        except Exception:
                            dropped.append({"action": a, "reason": "systemd_inactive_and_no_unit_file"})
            else:
                dropped.append({"action": a, "reason": "systemd_unit_not_observed"})
            continue

        if a_type == "remove_unit_file":
            path = str(target) if target else ""
            if path and os.path.exists(path):
                verified_actions.append(a)
            else:
                dropped.append({"action": a, "reason": "unit_file_missing"})
            continue

        if a_type == "kill_process_group":
            pattern = a.get("pattern")
            if pattern and pattern in proc_indicators:
                verified_actions.append(a)
            else:
                # Attempt a live ps capture to see if the indicator appears now
                ps_out = _capture_ps(ctx)
                if ps_out and pattern and pattern in ps_out:
                    verified_actions.append(a)
                else:
                    dropped.append({"action": a, "reason": "process_indicator_not_present"})
            continue

        if a_type == "remove_file":
            path = str(target) if target else ""
            # Special-case ld.so.preload: trust scan flag first
            if path == "/etc/ld.so.preload":
                if ld_preload_exists or os.path.exists(path):
                    verified_actions.append(a)
                else:
                    dropped.append({"action": a, "reason": "ld_preload_not_present"})
            else:
                if path and os.path.exists(path):
                    verified_actions.append(a)
                else:
                    dropped.append({"action": a, "reason": "file_missing"})
            continue

        if a_type == "cron_line":
            file_path = str(target) if target else ""
            pattern = a.get("pattern")
            # Verify the suspicious entry still matches our cached scan data
            matched = False
            for e in cron_entries:
                if e.get("file") == file_path and (not pattern or pattern == e.get("matched")):
                    matched = True
                    break
            if matched:
                verified_actions.append(a)
            else:
                # Optionally re-check file content for the pattern
                excerpt = _read_file_excerpt(ctx, file_path, lines=50) if file_path else None
                if excerpt and (not pattern or pattern in excerpt):
                    verified_actions.append(a)
                else:
                    dropped.append({"action": a, "reason": "cron_entry_not_found"})
            continue

        if a_type == "review_ssh_keys":
            # Low risk manual review is always acceptable to keep
            verified_actions.append(a)
            continue

        # Unknown action types are downgraded for manual review
        downgraded.append({"action": a, "reason": "unknown_action_type"})

    verified = {"total_actions": len(verified_actions), "actions": verified_actions}
    meta = {"probe_count": int(max_probes - ctx.remaining), "probes_skipped": ctx.probes_skipped, "consent_log": ctx.consent_log}
    return {"success": True, "verified_plan": verified, "downgraded": downgraded, "dropped": dropped, "meta": meta}


__all__ = ["verify_plan", "ProbeContext"]
