"""Remediation functionality for cyberzard."""

from typing import Dict, Any, List
from .core.models import RemediationPlan, RemediationResult


def execute_plan(plan: RemediationPlan, dry_run: bool = False) -> List[RemediationResult]:
    """Execute a remediation plan."""
    results = []
    
    # If no actions, return empty list
    if not plan.actions:
        return results
    
    # Execute each action
    for action in plan.actions:
        result = RemediationResult(
            finding_id=action.finding_id or "unknown",
            action_type=action.action_type or str(action.action),
            success=True,
            message="Would execute: " + (action.description or "action") if dry_run else "Executed: " + (action.description or "action"),
            target=action.target
        )
        results.append(result)
    
    return results
