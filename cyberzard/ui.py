from __future__ import annotations

from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich.text import Text


_THEME = Theme(
    {
        "title": "bold cyan",
        "ok": "green",
        "warn": "yellow",
        "err": "red",
        "info": "dim",
    }
)


def _console() -> Console:
    return Console(theme=_THEME, soft_wrap=True)


def _summary_table(summary: Dict[str, Any]) -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Key", style="info")
    table.add_column("Value")
    for k, v in summary.items():
        table.add_row(str(k), str(v))
    return table


def _actions_table(actions: List[Dict[str, Any]], limit: int = 10) -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Type", style="info")
    table.add_column("Target")
    table.add_column("Risk")
    table.add_column("Preview")
    for idx, a in enumerate(actions):
        if idx >= limit:
            break
        table.add_row(
            str(a.get("type", "")),
            str(a.get("target", ""))[:60],
            str(a.get("risk", "")),
            str(a.get("command_preview", ""))[:60],
        )
    return table


def render_scan_output(results: Dict[str, Any], plan: Dict[str, Any]) -> None:
    """Pretty print scan summary and remediation plan preview using Rich."""
    cons = _console()
    summary = results.get("summary", {})
    plan_obj = plan.get("plan", {}) if isinstance(plan, dict) else {}
    actions: List[Dict[str, Any]] = plan_obj.get("actions", []) if isinstance(plan_obj, dict) else []
    total = plan_obj.get("total_actions", len(actions))

    cons.print(Panel(Text("Cyberzard scan", style="title"), border_style="cyan"))
    cons.print(_summary_table(summary))

    cons.print()
    cons.print(
        Panel(
            Text(f"Remediation preview • {total} actions", style="title"),
            border_style="cyan",
        )
    )
    if actions:
        cons.print(_actions_table(actions, limit=12))
    else:
        cons.print(Text("No actions suggested.", style="info"))


def render_advice_output(advice: str, results: Dict[str, Any]) -> None:
    """Pretty print advice with a quick summary."""
    cons = _console()
    summary = results.get("summary", {}) if isinstance(results, dict) else {}
    cons.print(Panel(Text("Cyberzard advice", style="title"), border_style="cyan"))
    if summary:
        cons.print(_summary_table(summary))
        cons.print()
    cons.print(Panel(advice, title="Advice", border_style="green"))

def render_verified_output(results: Dict[str, Any], verification: Dict[str, Any]) -> None:
    cons = _console()
    summary = results.get("summary", {})
    cons.print(Panel(Text("Cyberzard scan (verified)", style="title"), border_style="cyan"))
    cons.print(_summary_table(summary))
    cons.print()
    verified = verification.get("verified_plan", {}) if isinstance(verification, dict) else {}
    dropped = verification.get("dropped", []) if isinstance(verification, dict) else []
    downgraded = verification.get("downgraded", []) if isinstance(verification, dict) else []
    total_kept = verified.get("total_actions", 0)
    cons.print(
        Panel(
            Text(
                f"Verified remediation • kept {total_kept} | dropped {len(dropped)} | downgraded {len(downgraded)}",
                style="title",
            ),
            border_style="cyan",
        )
    )
    actions = verified.get("actions", []) if isinstance(verified, dict) else []
    if actions:
        cons.print(_actions_table(actions, limit=12))
    else:
        cons.print(Text("No verified actions.", style="info"))
    if dropped:
        t = Table(show_header=True, header_style="bold red")
        t.add_column("Type", style="err"); t.add_column("Target"); t.add_column("Reason")
        for d in dropped[:10]:
            a = d.get("action", {})
            t.add_row(str(a.get("type", "")), str(a.get("target", ""))[:60], str(d.get("reason", ""))[:60])
        cons.print(Panel(t, title="Dropped", border_style="red"))
    if downgraded:
        t2 = Table(show_header=True, header_style="bold yellow")
        t2.add_column("Type", style="warn"); t2.add_column("Target"); t2.add_column("Reason")
        for d in downgraded[:10]:
            a = d.get("action", {})
            t2.add_row(str(a.get("type", "")), str(a.get("target", ""))[:60], str(d.get("reason", ""))[:60])
        cons.print(Panel(t2, title="Downgraded (manual review)", border_style="yellow"))


def render_email_security(scan: Dict[str, Any], plan: Dict[str, Any], summary_text: str | None = None) -> None:
    """Render email security scan + plan preview.

    Fallback: if Rich import failed earlier (unlikely), do naive prints.
    """
    try:
        cons = _console()
    except Exception:  # pragma: no cover
        s = (scan or {}).get("summary", {})
        print("Email Security Scan")
        print(f"Queue size: {s.get('queue_size')} backlog={s.get('queue_backlog')}")
        print(f"SASL failures: {s.get('sasl_failures')}")
        return
    s = (scan or {}).get("summary", {})
    cons.print(Panel(Text("Email security scan", style="title"), border_style="cyan"))
    cons.print(_summary_table({
        "failed_services": s.get("failed_services_count"),
        "queue_size": s.get("queue_size"),
        "queue_backlog": s.get("queue_backlog"),
        "sasl_failures": s.get("sasl_failures"),
        "dns_mismatch": s.get("dns_mismatch"),
        "fail2ban_active": s.get("fail2ban_active"),
        "tls_hardened": s.get("tls_hardened"),
        "rate_limited": s.get("rate_limited"),
    }))
    if summary_text:
        cons.print(Panel(summary_text, title="AI Summary", border_style="green"))
    plan_obj = plan.get("plan", {}) if isinstance(plan, dict) else {}
    actions = plan_obj.get("actions", [])
    total = plan_obj.get("total_actions", len(actions))
    cons.print(Panel(Text(f"Hardening preview • {total} actions", style="title"), border_style="cyan"))
    if actions:
        cons.print(_actions_table(actions, limit=12))
    else:
        cons.print(Text("No suggested actions", style="info"))


def render_email_execution_progress(executions: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    """Render progress/results of guided execution."""
    try:
        cons = _console()
    except Exception:  # pragma: no cover
        print("Email Execution Summary:", summary)
        return
    cons.print(Panel(Text("Email remediation execution", style="title"), border_style="cyan"))
    cons.print(_summary_table(summary))
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Type")
    table.add_column("Risk")
    table.add_column("Status")
    table.add_column("Refined")
    table.add_column("Unsafe/Skip")
    for ex in executions[:30]:
        status = "dry-run" if ex.get("dry_run") else ("ok" if ex.get("success") else ("fail" if ex.get("success") is False else "?"))
        row = [
            str(ex.get("type")),
            str(ex.get("risk")),
            status,
            "yes" if ex.get("refinement_success") else ("attempt" if ex.get("refinement_attempted") else ""),
            "unsafe" if ex.get("unsafe") else ("skipped" if ex.get("skipped") else ""),
        ]
        table.add_row(*row)
    cons.print(table)


def render_email_fix(guide_markdown: str) -> None:
    """Render email fix guide (markdown simplified)."""
    try:
        from rich.markdown import Markdown  # local import to avoid heavy cost if unused
        cons = _console()
        cons.print(Markdown(guide_markdown[:8000]))
    except Exception:  # pragma: no cover
        print(guide_markdown[:8000])


__all__ = [
    "render_scan_output",
    "render_advice_output",
    "render_verified_output",
    "render_email_security",
    "render_email_execution_progress",
    "render_email_fix",
]
