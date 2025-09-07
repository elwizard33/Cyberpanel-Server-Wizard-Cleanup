"""Rich TTY formatter for scan findings.

Groups findings by severity (critical->info) and displays compact tables.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from cyberzard.core.models import Finding
from cyberzard.config import Severity
from cyberzard.severity import weight

_SEV_ORDER = [Severity.critical, Severity.high, Severity.medium, Severity.low, Severity.info]
_SEV_COLOR = {
    Severity.critical: "bold white on red",
    Severity.high: "red",
    Severity.medium: "yellow",
    Severity.low: "cyan",
    Severity.info: "green",
}


def render_findings(findings: Iterable[Finding], console: Console | None = None) -> None:
    console = console or Console()
    grouped: dict[Severity, List[Finding]] = defaultdict(list)
    for f in findings:
        grouped[f.severity].append(f)

    total = sum(len(v) for v in grouped.values())
    console.print(Panel.fit(Text(f"Total Findings: {total}", style="bold magenta")))

    for sev in _SEV_ORDER:
        bucket = grouped.get(sev, [])
        if not bucket:
            continue
        # Sort by weight (all same) then by message
        bucket.sort(key=lambda x: (weight(x.severity), x.message or x.rationale or ""), reverse=True)
        table = Table(title=f"{sev.value.upper()} ({len(bucket)})", style=_SEV_COLOR[sev])
        table.add_column("Category", no_wrap=True)
        table.add_column("Indicator", overflow="fold")
        table.add_column("Message", overflow="fold")
        table.add_column("Action", no_wrap=True)
        for f in bucket:
            table.add_row(f.category.value, f.indicator, (f.message or f.rationale or "")[:120], f.recommended_action.value)
        console.print(table)

__all__ = ["render_findings"]
