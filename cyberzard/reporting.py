"""Reporting functionality for cyberzard."""

from typing import Dict, Any, List
from .core.models import Finding, ScanResult

def generate_report(scan_result: ScanResult, format: str = "json") -> Dict[str, Any]:
    """Generate a report from scan results."""
    report = {
        "summary": {
            "total_findings": len(scan_result.findings),
            "format": format,
        },
        "findings": [
            {
                "id": finding.id,
                "severity": finding.severity.value,
                "description": finding.description,
                "scanner": finding.scanner,
                "timestamp": finding.timestamp
            }
            for finding in scan_result.findings
        ]
    }
    return report
