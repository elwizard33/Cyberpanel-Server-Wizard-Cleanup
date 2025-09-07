"""Cron & systemd service artifact scanner."""
from __future__ import annotations

import glob
import os
import subprocess
from pathlib import Path
from typing import List

from cyberzard.config import (
    CRON_SUSPICIOUS_TOKENS,
    SUSPICIOUS_SERVICE_NAMES,
    Severity,
    Category,
    RecommendedAction,
)
from cyberzard.core.models import Finding
from cyberzard.scanners.base import BaseScanner, register, ScanContext

CRON_FILES = [
    "/etc/crontab",
    *glob.glob("/etc/cron.d/*"),
]

CRON_SPOOL_DIRS = ["/var/spool/cron", "/var/spool/cron/crontabs"]


def _read_file_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []


@register
class CronServiceScanner(BaseScanner):
    name = "cron_services"
    description = "Scans cron files and systemd services for suspicious indicators."

    def scan(self, context: ScanContext) -> List[Finding]:
        findings: List[Finding] = []
        # Cron scanning
        for fpath in CRON_FILES:
            p = Path(fpath)
            if not p.exists():
                continue
            for lineno, line in enumerate(_read_file_lines(p), start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                for token in CRON_SUSPICIOUS_TOKENS:
                    if token in stripped:
                        findings.append(
                            Finding(
                                category=Category.cron,
                                severity=Severity.medium,
                                indicator=token,
                                message=f"Suspicious cron token '{token}' in {p}:{lineno}",
                                rationale="Cron line contains suspicious token",
                                path=p,
                                recommended_action=RecommendedAction.review,
                                extra={"line": stripped, "lineno": lineno},
                            )
                        )
                        break

        # User cron spool
        for d in CRON_SPOOL_DIRS:
            if not os.path.isdir(d):
                continue
            for entry in Path(d).iterdir():
                if entry.is_file():
                    for lineno, line in enumerate(_read_file_lines(entry), start=1):
                        stripped = line.strip()
                        if not stripped or stripped.startswith("#"):
                            continue
                        for token in CRON_SUSPICIOUS_TOKENS:
                            if token in stripped:
                                findings.append(
                                    Finding(
                                        category=Category.cron,
                                        severity=Severity.medium,
                                        indicator=token,
                                        message=f"Suspicious cron token '{token}' in {entry}:{lineno}",
                                        rationale="User cron line contains suspicious token",
                                        path=entry,
                                        recommended_action=RecommendedAction.review,
                                        extra={"line": stripped, "lineno": lineno},
                                    )
                                )
                                break

        # Systemd service scanning
        try:
            result = subprocess.run(
                ["systemctl", "list-units", "--type=service", "--all", "--no-legend", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if not parts:
                        continue
                    unit = parts[0]
                    base_name = unit.split(".")[0]
                    for suspicious in SUSPICIOUS_SERVICE_NAMES:
                        if suspicious in base_name:
                            findings.append(
                                Finding(
                                    category=Category.service,
                                    severity=Severity.high,
                                    indicator=unit,
                                    message=f"Suspicious service unit: {unit}",
                                    rationale="Service name matches suspicious pattern",
                                    recommended_action=RecommendedAction.disable,
                                    extra={"raw": line},
                                )
                            )
                            break
        except Exception:
            context.logger.debug("Failed to list systemd services", exc_info=True)

        return findings


__all__ = ["CronServiceScanner"]
