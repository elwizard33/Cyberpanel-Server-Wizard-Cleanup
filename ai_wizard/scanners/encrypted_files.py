"""Encrypted/suspicious file extension scanner."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from cyberzard.config import (
    ENCRYPTED_SEARCH_ROOTS,
    ENCRYPTED_EXTS,
    MAX_ENCRYPTED_FINDINGS,
    Severity,
    Category,
    RecommendedAction,
)
from cyberzard.core.models import Finding
from cyberzard.scanners.base import BaseScanner, register, ScanContext


@register
class EncryptedFilesScanner(BaseScanner):
    name = "encrypted_files"
    description = "Finds files with suspicious encrypted extensions (ransomware artifacts)."

    def scan(self, context: ScanContext) -> List[Finding]:
        findings: List[Finding] = []
        count = 0
        for root in ENCRYPTED_SEARCH_ROOTS:
            if count >= MAX_ENCRYPTED_FINDINGS:
                break
            if not os.path.isdir(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                # Early exit if cap reached
                if count >= MAX_ENCRYPTED_FINDINGS:
                    break
                for fname in filenames:
                    if count >= MAX_ENCRYPTED_FINDINGS:
                        break
                    p = Path(dirpath) / fname
                    if p.suffix in ENCRYPTED_EXTS:
                        try:
                            size = p.stat().st_size
                        except Exception:
                            size = None
                        findings.append(
                            Finding(
                                category=Category.encryption,
                                severity=Severity.high,
                                indicator=p.suffix,
                                message=f"Suspicious encrypted-like file: {p}",
                                rationale="File extension matches ransomware/encryption indicator",
                                path=p,
                                recommended_action=RecommendedAction.investigate,
                                extra={"size": size},
                            )
                        )
                        count += 1
                # Prune deep hidden dirs quickly
                dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        return findings


__all__ = ["EncryptedFilesScanner"]
