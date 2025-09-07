"""Core data models used by scanners and reporting.

Extended to satisfy task specification: Finding, ScanReport, RemediationAction,
RemediationPlan with validation and helper methods.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import uuid
from datetime import datetime, timezone

from cyberzard.config import Severity, Category, RecommendedAction


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: Category
    severity: Severity
    indicator: str
    # Original implementation used 'message'; spec uses 'rationale'. Keep both.
    message: str = Field(default="")
    rationale: Optional[str] = None
    location: Optional[str] = None  # generic location string
    path: Optional[Path] = None  # retained for convenience
    pid: Optional[int] = None
    user: Optional[str] = None
    details: Optional[str] = None
    recommended_action: RecommendedAction = RecommendedAction.investigate
    removable: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extra: Dict[str, Any] = Field(default_factory=dict)
    evidence_file: Optional[Path] = None

    @validator("rationale", always=True)
    def _sync_rationale(cls, v, values):  # pragma: no cover - simple
        if not v:
            return values.get("message")
        return v

    @validator("id")
    def _validate_uuid(cls, v: str) -> str:  # pragma: no cover - simple
        try:
            uuid.UUID(v)
            return v
        except Exception:
            return str(uuid.uuid4())

    def short(self) -> str:  # pragma: no cover
        return f"[{self.severity}] {self.category}: {self.message or self.rationale}".strip()

    def to_summary(self) -> Dict[str, Any]:  # minimal export for AI context
        return {
            "id": self.id,
            "cat": self.category.value,
            "sev": self.severity.value,
            "ind": self.indicator,
            "msg": self.message or self.rationale,
            "act": self.recommended_action.value,
        }


class RemediationAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    finding_id: str
    action: RecommendedAction
    target: str
    dry_run: bool = True
    summary: Optional[str] = None


class RemediationPlan(BaseModel):
    actions: List[RemediationAction]
    summary: str


class RemediationResult(BaseModel):
    finding_id: str
    action: RecommendedAction
    success: bool
    message: str
    changed: bool = False


class ScanReport(BaseModel):
    findings: List[Finding]
    remediation: List[RemediationResult] = []
    meta: Dict[str, Any] = Field(default_factory=dict)

    @property
    def counts_by_severity(self):  # pragma: no cover - trivial
        out = {s.value: 0 for s in Severity}
        for f in self.findings:
            out[f.severity.value] += 1
        return out


__all__ = [
    "Finding",
    "ScanReport",
    "RemediationAction",
    "RemediationPlan",
    "RemediationResult",
]
