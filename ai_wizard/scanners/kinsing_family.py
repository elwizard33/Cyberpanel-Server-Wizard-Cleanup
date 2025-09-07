"""Composite scanner for Kinsing family infection correlation.

Relies on prior findings (process + file) to emit a single critical composite
finding to reduce noise and highlight confirmed multi-indicator compromise.

Orchestrator is expected to place already collected findings in
ScanContext.cache['prior_findings'] before invoking this scanner.
"""
from __future__ import annotations

from typing import List

from cyberzard.core.models import Finding
from cyberzard.config import Severity, Category, RecommendedAction
from cyberzard.scanners.base import BaseScanner, register, ScanContext


@register
class KinsingCompositeScanner(BaseScanner):
    name = "kinsing_family"
    description = "Correlates kinsing process + IOC file presence into composite finding."

    def scan(self, context: ScanContext) -> List[Finding]:
        findings: List[Finding] = []
        prior: List[Finding] = context.cache.get("prior_findings", [])  # type: ignore
        if not prior:
            return findings
        kinsing_proc_ids = [f.id for f in prior if f.category == Category.process and f.indicator.lower() == "kinsing"]
        kinsing_file_ids = [f.id for f in prior if f.category == Category.file and "kinsing" in (f.indicator.lower())]
        if kinsing_proc_ids and kinsing_file_ids:
            related = kinsing_proc_ids + kinsing_file_ids
            findings.append(
                Finding(
                    category=Category.composite,
                    severity=Severity.critical,
                    indicator="kinsing_family",
                    message="Multiple Kinsing indicators (process + file) detected",
                    rationale="Correlation of process and file IOC confirms active Kinsing compromise",
                    recommended_action=RecommendedAction.eradicate,
                    removable=False,
                    extra={"related_ids": related},
                )
            )
        return findings


__all__ = ["KinsingCompositeScanner"]
