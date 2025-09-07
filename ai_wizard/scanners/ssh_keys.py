"""SSH authorized_keys scanner."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import List

from cyberzard.config import Severity, Category, RecommendedAction
from cyberzard.core.models import Finding
from cyberzard.scanners.base import BaseScanner, register, ScanContext

CANDIDATE_DIRS = [Path("/root"), Path("/home")]  # iterate user dirs under /home


def _fingerprint(key_line: str) -> str:
    return hashlib.md5(key_line.encode()).hexdigest()  # nosec: fingerprint only


@register
class SSHKeysScanner(BaseScanner):
    name = "ssh_keys"
    description = "Enumerates authorized_keys entries and fingerprints them."

    def scan(self, context: ScanContext) -> List[Finding]:
        findings: List[Finding] = []
        for base in CANDIDATE_DIRS:
            if not base.exists():
                continue
            # For /home, iterate subdirectories
            paths: List[Path] = []
            if base.name == "home":
                try:
                    for child in base.iterdir():
                        paths.append(child / ".ssh" / "authorized_keys")
                except Exception:
                    continue
            else:
                paths.append(base / ".ssh" / "authorized_keys")

            for ak in paths:
                if not ak.exists():
                    continue
                try:
                    for line in ak.read_text(encoding="utf-8", errors="ignore").splitlines():
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) < 2:
                            continue
                        key_type, key_body = parts[0], parts[1]
                        fp = _fingerprint(key_body)
                        findings.append(
                            Finding(
                                category=Category.ssh_key,
                                severity=Severity.medium,
                                indicator=fp,
                                message=f"SSH key fingerprint {fp} in {ak}",
                                rationale="Enumerated authorized key for review",
                                path=ak,
                                recommended_action=RecommendedAction.confirm,
                                extra={"key_type": key_type},
                            )
                        )
                except Exception:
                    continue
        return findings


__all__ = ["SSHKeysScanner"]
