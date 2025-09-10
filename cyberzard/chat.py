from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.theme import Theme

from .agent_engine.tools import read_file, scan_server, propose_remediation
from .agent_engine.verify import verify_plan
from .agent_engine.provider import summarize as summarize_advice


THEME = Theme({
    "user": "bold cyan",
    "assistant": "bold green",
    "tool": "magenta",
    "title": "bold blue",
    "info": "dim",
    "warn": "yellow",
    "err": "red",
})


def _console() -> Console:
    return Console(theme=THEME, soft_wrap=True)


@dataclass
class PermissionState:
    auto_approve: bool = False
    remembered: Dict[str, bool] = field(default_factory=dict)  # tool_name -> allowed

    def ask(self, tool: str, description: str) -> bool:
        if self.auto_approve:
            return True
        if not sys.stdout.isatty() or os.getenv("NO_COLOR") in {"1", "true", "TRUE"}:
            # Non-interactive or color-less terminals default to deny for safety
            return False
        if tool in self.remembered:
            return self.remembered[tool]
        cons = _console()
        cons.print(Panel(f"Tool request: [bold]{tool}[/] — {description}\nAllow once or remember?", title="Permission", border_style="yellow"))
        allow = Confirm.ask("Allow this tool now?", default=True)
        if allow:
            remember = Confirm.ask("Remember this approval for the session?", default=True)
            if remember:
                self.remembered[tool] = True
            return True
        else:
            remember_deny = Confirm.ask("Remember deny for the session?", default=False)
            if remember_deny:
                self.remembered[tool] = False
            return False


def _bubble(role: str, content: str) -> Panel:
    style = {
        "user": "user",
        "assistant": "assistant",
        "tool": "tool",
    }.get(role, "info")
    title = role.capitalize()
    return Panel(Text(content, style=style), title=title, border_style=style)


def _actions_preview_table(plan: Dict[str, Any]) -> Optional[Table]:
    if not isinstance(plan, dict):
        return None
    p = plan.get("plan", {}) if "plan" in plan else plan
    acts = p.get("actions", []) if isinstance(p, dict) else []
    if not acts:
        return None
    t = Table(show_header=True, header_style="bold magenta")
    t.add_column("Type", style="info")
    t.add_column("Target")
    t.add_column("Risk")
    for a in acts[:10]:
        t.add_row(str(a.get("type", "")), str(a.get("target", ""))[:60], str(a.get("risk", "")))
    return t


def _intent(query: str) -> str:
    q = query.strip().lower()
    if q in {"quit", "exit", ":q", "/q", "/quit", "/exit"}:
        return "quit"
    if q in {"help", "/help"}:
        return "help"
    if any(k in q for k in ["scan", "check", "investigate", "ioc", "miner", "malware", "backdoor"]):
        return "scan"
    if q.startswith("read ") or q.startswith("open "):
        return "read"
    if any(k in q for k in ["remediation", "plan", "fix", "actions"]):
        return "plan"
    return "chat"


def run_chat(verify: bool = True, auto_approve: bool = False, max_probes: int = 5) -> None:
    """Interactive, Rich-powered chat focused on CyberPanel anomaly hunting.

    Tools are permission-gated and read-only by default. The assistant stays on-task.
    """
    cons = _console()
    cons.print(Panel("Cyberzard chat — focused on CyberPanel anomaly detection.\nType 'scan' to start, 'help' for tips, 'quit' to exit.", title="Welcome", border_style="cyan"))

    perms = PermissionState(auto_approve=auto_approve)
    last_scan: Optional[Dict[str, Any]] = None
    last_plan: Optional[Dict[str, Any]] = None

    while True:
        try:
            user = Prompt.ask("[bold cyan]You[/]")
        except (KeyboardInterrupt, EOFError):
            cons.print("\nGoodbye.")
            break
        if not user.strip():
            continue
        cons.print(_bubble("user", user))
        intent = _intent(user)

        if intent == "quit":
            cons.print("Exiting chat.")
            break
        if intent == "help":
            cons.print(_bubble("assistant", "Commands: scan • read <path> • plan • quit\nTips: Start with 'scan' to collect IOCs. Then ask for 'plan' or 'advice'."))
            continue

        if intent == "read":
            # read <path>
            path = user.split(" ", 1)[1].strip() if " " in user else ""
            if not path:
                cons.print(_bubble("assistant", "Please provide a path, e.g. 'read /etc/passwd'."))
                continue
            if not perms.ask("read_file", f"Read contents of {path} (read-only)"):
                cons.print(_bubble("assistant", "Denied. I won't read that file."))
                continue
            try:
                data = read_file(path=path)
                preview = (data.get("content", "") or "")[:2000]
                cons.print(_bubble("tool", f"read_file({path})\n---\n{preview}"))
            except Exception as e:  # pragma: no cover
                cons.print(_bubble("assistant", f"Error reading file: {e}"))
            continue

        if intent == "scan":
            if not perms.ask("scan_server", "Run quick IOC scan (read-only) with encrypted-file checks"):
                cons.print(_bubble("assistant", "Denied. No scan was run."))
                continue
            last_scan = scan_server(include_encrypted=True)
            cons.print(_bubble("tool", "scan_server(include_encrypted=True) → collected summary."))
            # Optional verification of remediation plan
            last_plan = propose_remediation(last_scan)
            if verify:
                try:
                    ver = verify_plan(
                        last_scan,
                        last_plan,
                        allow_probes=perms.auto_approve or sys.stdout.isatty(),
                        max_probes=max_probes,
                        consent_callback=lambda category: perms.ask(
                            f"probe:{category}", f"Run up to {max_probes} safe probes for {category}"
                        ),
                    )
                except Exception:
                    ver = None
                if ver and ver.get("success"):
                    # Replace plan preview with verified plan
                    last_plan = ver.get("verified_plan", last_plan)
                    dropped = ver.get("dropped") or []
                    downgraded = ver.get("downgraded") or []
                    cons.print(_bubble("assistant", f"Scan complete. Verified plan ready (kept {last_plan.get('total_actions', 0)}). Dropped {len(dropped)}, downgraded {len(downgraded)}."))
                else:
                    cons.print(_bubble("assistant", "Scan complete. Verification unavailable, showing raw plan."))
            else:
                cons.print(_bubble("assistant", "Scan complete. Showing plan preview."))

            # Show short plan preview and AI summary if possible
            if last_plan:
                table = _actions_preview_table(last_plan)
                if table:
                    cons.print(Panel(table, title="Remediation preview"))
            try:
                if last_scan:
                    advice = summarize_advice(last_scan)
                    cons.print(Panel(advice, title="AI advice", border_style="green"))
            except Exception:
                pass
            continue

        if intent == "plan":
            if not last_scan:
                cons.print(_bubble("assistant", "No scan yet. Say 'scan' first."))
                continue
            last_plan = propose_remediation(last_scan)
            if verify:
                try:
                    ver = verify_plan(
                        last_scan,
                        last_plan,
                        allow_probes=perms.auto_approve or sys.stdout.isatty(),
                        max_probes=max_probes,
                        consent_callback=lambda category: perms.ask(
                            f"probe:{category}", f"Run up to {max_probes} safe probes for {category}"
                        ),
                    )
                    if ver and ver.get("success"):
                        last_plan = ver.get("verified_plan", last_plan)
                except Exception:
                    pass
            table = _actions_preview_table(last_plan or {})
            if table:
                cons.print(Panel(table, title="Remediation plan", border_style="cyan"))
            else:
                cons.print(_bubble("assistant", "No actions suggested."))
            continue

        # Fallback chat guidance (stay on mission)
        cons.print(_bubble("assistant", "I'm focused on CyberPanel security. Say 'scan' to check the host, 'plan' for remediation, or 'read <path>' to inspect a file."))
