"""Severity scoring & classification utilities.

Provides a lightweight heuristic classifier used when scanners
produce a raw indicator string but do not assign a contextual
severity yet, or when we want to normalize / escalate based on
indicator content.

The logic is intentionally simple & transparent (no ML) so that
security operators can audit / adjust. Adjust weight maps as the
project evolves.
"""
from __future__ import annotations

from typing import Dict

from .config import Severity

# Numeric weights (higher == more severe) primarily used for sorting
SEVERITY_WEIGHTS: Dict[Severity, int] = {
    Severity.critical: 100,
    Severity.high: 70,
    Severity.medium: 40,
    Severity.low: 10,
    Severity.info: 0,
}

# Keyword heuristics – order matters: first match wins for classify()
# These are intentionally concise; scanners already assign severities
# for most findings. This is a fallback / normalization helper.
_KEYWORD_MAP = [
    ("ransom", Severity.critical),
    ("encrypt", Severity.critical),
    ("exfil", Severity.critical),
    ("kinsing", Severity.high),
    ("xmrig", Severity.high),
    ("miner", Severity.high),
    ("crypto", Severity.high),
    ("suspicious", Severity.medium),
    ("anomal", Severity.medium),  # anomaly / anomalous
    ("unexpected", Severity.medium),
    ("deprecated", Severity.low),
    ("info", Severity.info),
]


def classify(indicator: str) -> Severity:
    """Classify a free-form indicator string into a Severity.

    Rules:
    1. Empty -> info
    2. Iterate keyword map (case-insensitive) first match returns mapped severity
    3. Fallback to medium if string length > 80 (long descriptive issue)
    4. Otherwise low
    """
    if not indicator:
        return Severity.info
    lowered = indicator.lower()
    for token, sev in _KEYWORD_MAP:
        if token in lowered:
            return sev
    if len(indicator) > 80:
        return Severity.medium
    return Severity.low


def weight(severity: Severity) -> int:
    """Return numeric weight for a severity enum (default 0)."""
    return SEVERITY_WEIGHTS.get(severity, 0)


__all__ = ["classify", "weight", "SEVERITY_WEIGHTS"]
