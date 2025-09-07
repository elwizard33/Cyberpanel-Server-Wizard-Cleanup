"""Scanner for known malicious file paths and patterns."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List

from cyberzard.config import (
    MALICIOUS_FILE_PATHS,
    Severity,
    Category,
    RecommendedAction,
)
from cyberzard.core.models import Finding
from cyberzard.scanners.base import BaseScanner, register, ScanContext


def _hash_path(p: Path) -> str:
    return hashlib.sha256(str(p).encode()).hexdigest()[:12]


@register
class MaliciousFilePathScanner(BaseScanner):
    name = "malicious_file_paths"
    description = "Detects presence of known malicious file paths from IOC list."

    def scan(self, context: ScanContext) -> List[Finding]:
        findings: List[Finding] = []
        for raw in MALICIOUS_FILE_PATHS:
            # Handle wildcard simple suffix match (very limited pattern support)
            if "*" in raw:
                base, _ = raw.split("*", 1)
                base_path = Path(base).parent
                if base_path.exists():
                    try:
                        for child in base_path.iterdir():
                            if child.name.startswith(Path(base).name):
                                findings.append(
                                    Finding(
                                        id=f"file-{_hash_path(child)}",
                                        category=Category.file,
                                        severity=Severity.high,
                                        message=f"Suspicious file (pattern match): {child}",
                                        indicator=str(child),
                                        path=child,
                                        recommended_action=RecommendedAction.remove,
                                    )
                                )
                    except Exception:
                        continue
                continue

            p = Path(raw)
            if p.exists():
                findings.append(
                    Finding(
                        id=f"file-{_hash_path(p)}",
                        category=Category.file,
                        severity=Severity.high,
                        message=f"Malicious IOC file present: {p}",
                        indicator=str(p),
                        path=p,
                        recommended_action=RecommendedAction.remove,
                    )
                )
        return findings


__all__ = ["MaliciousFilePathScanner"]
