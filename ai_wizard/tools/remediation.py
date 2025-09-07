"""Remediation planning tool."""
from __future__ import annotations

from typing import List, Dict, Any

from cyberzard.core.models import RemediationAction, RemediationPlan
from cyberzard.config import RecommendedAction
from .registry import register_tool

_SUPPORTED = {a.value for a in RecommendedAction}


@register_tool(description="Build remediation plan from proposed actions")
def plan_remediation(actions: List[Dict[str, str]], summary: str | None = None) -> Dict[str, Any]:
    built: List[RemediationAction] = []
    errors: List[Dict[str, Any]] = []
    for idx, a in enumerate(actions):
        act = a.get("action")
        if act not in _SUPPORTED:
            errors.append({"index": idx, "error": "unsupported_action", "action": act})
            continue
        target = a.get("target") or ""
        if not target:
            errors.append({"index": idx, "error": "missing_target"})
            continue
        built.append(
            RemediationAction(
                finding_id=a.get("finding_id", ""),
                action=RecommendedAction(act),
                target=target,
                dry_run=True,
                summary=a.get("summary"),
            )
        )
    plan_summary = summary or f"Planned {len(built)} actions (errors={len(errors)})"
    plan = RemediationPlan(actions=built, summary=plan_summary)
    return {
        "summary": plan.summary,
        "actions": [
            {
                "id": ra.id,
                "finding_id": ra.finding_id,
                "action": ra.action.value,
                "target": ra.target,
                "dry_run": ra.dry_run,
            }
            for ra in plan.actions
        ],
        "errors": errors,
    }


__all__ = ["plan_remediation"]
