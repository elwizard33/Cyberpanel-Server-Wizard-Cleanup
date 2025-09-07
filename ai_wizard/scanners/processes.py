"""Process scanner detecting suspicious processes via regex patterns."""
from __future__ import annotations

import psutil  # type: ignore
from typing import List

from cyberzard.config import PROCESS_REGEX, Severity, Category, RecommendedAction
from cyberzard.core.models import Finding
from cyberzard.scanners.base import BaseScanner, register, ScanContext


CRITICAL_KEYWORDS = {"kinsing", "xmrig"}


@register
class ProcessScanner(BaseScanner):
    name = "processes"
    description = "Matches running processes against IOC regex pattern."

    def scan(self, context: ScanContext) -> List[Finding]:
        findings: List[Finding] = []
        for proc in psutil.process_iter(attrs=["pid", "name", "cmdline", "username"]):
            try:
                cmdline_list = proc.info.get("cmdline") or []
                cmdline = " ".join(cmdline_list) if isinstance(cmdline_list, (list, tuple)) else str(cmdline_list)
                name = proc.info.get("name") or ""
                haystack = f"{name} {cmdline}".strip()
                if not haystack:
                    continue
                m = PROCESS_REGEX.search(haystack)
                if not m:
                    continue
                indicator = m.group(0)
                sev = Severity.critical if indicator.lower() in CRITICAL_KEYWORDS else Severity.high
                findings.append(
                    Finding(
                        category=Category.process,
                        severity=sev,
                        indicator=indicator,
                        message=f"Suspicious process matched pattern: {indicator}",
                        rationale="Process name/command matches known malicious pattern",
                        pid=proc.info.get("pid"),
                        user=proc.info.get("username"),
                        recommended_action=RecommendedAction.kill,
                        removable=True,
                        extra={"cmdline": cmdline, "name": name},
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception:
                context.logger.debug("Unexpected error inspecting process", exc_info=True)
        return findings


__all__ = ["ProcessScanner"]
