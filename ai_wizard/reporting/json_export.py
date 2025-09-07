"""JSON export helpers for ScanReport/Finding collections.

Ensures stable ordering and truncation of very large extra fields.
"""
from __future__ import annotations

import json
from typing import Iterable, Any, Dict

from cyberzard.core.models import Finding
from cyberzard.config import Severity
from cyberzard.severity import weight

_MAX_EXTRA_LEN = 400  # truncate large string fields in extra


def finding_to_dict(f: Finding) -> Dict[str, Any]:
    data = {
        "id": f.id,
        "category": f.category.value,
        "severity": f.severity.value,
        "indicator": f.indicator,
        "message": f.message or f.rationale,
        "recommended_action": f.recommended_action.value,
    }
    if f.location:
        data["location"] = f.location
    if f.path:
        data["path"] = str(f.path)
    if f.pid is not None:
        data["pid"] = f.pid
    if f.user:
        data["user"] = f.user
    if f.evidence_file:
        data["evidence_file"] = str(f.evidence_file)

    if f.extra:
        processed_extra = {}
        for k, v in f.extra.items():
            if isinstance(v, str) and len(v) > _MAX_EXTRA_LEN:
                processed_extra[k] = v[:_MAX_EXTRA_LEN] + "...<truncated>"
            else:
                processed_extra[k] = v
        data["extra"] = processed_extra
    return data


def findings_to_json(findings: Iterable[Finding]) -> str:
    # Sort by weight desc then category then indicator for stable ordering
    ordered = sorted(findings, key=lambda f: (weight(f.severity), f.category.value, f.indicator), reverse=True)
    payload = [finding_to_dict(f) for f in ordered]
    return json.dumps(payload, indent=2, sort_keys=True)

__all__ = ["finding_to_dict", "findings_to_json"]
