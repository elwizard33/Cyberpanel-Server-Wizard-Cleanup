"""Scan invocation bridge tools."""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from cyberzard.scanners import run_all_scanners
from cyberzard.core.models import Finding
from cyberzard.severity import weight
from .registry import register_tool

_MAX_FINDINGS_RETURN = 300

_last_findings: List[Finding] = []  # simple in-memory cache for detail lookup


def _serialize(f: Finding) -> Dict[str, Any]:
    return {
        "id": f.id,
        "severity": f.severity.value,
        "category": f.category.value,
        "indicator": f.indicator,
        "message": f.message or f.rationale,
        "recommended_action": f.recommended_action.value,
    }


@register_tool(description="Run scanners and return findings summary (capped)")
def run_scan(severity: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    global _last_findings
    findings = run_all_scanners()
    _last_findings = findings
    if severity:
        findings = [f for f in findings if f.severity.value == severity]
    # Sort by severity weight desc
    findings.sort(key=lambda f: weight(f.severity))
    findings.reverse()
    if limit > _MAX_FINDINGS_RETURN:
        limit = _MAX_FINDINGS_RETURN
    sliced = findings[:limit]
    return {"count": len(sliced), "total": len(findings), "findings": [_serialize(f) for f in sliced]}


@register_tool(description="Get detail for a finding id from last scan")
def get_finding_detail(finding_id: str) -> Dict[str, Any]:
    for f in _last_findings:
        if f.id == finding_id:
            data = _serialize(f)
            if f.extra:
                data["extra"] = f.extra
            if f.path:
                data["path"] = str(f.path)
            if f.pid:
                data["pid"] = f.pid
            return data
    return {"error": "not_found"}


__all__ = ["run_scan", "get_finding_detail"]
