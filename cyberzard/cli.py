from __future__ import annotations

import json
from pathlib import Path
import subprocess
import shlex
import shutil
from typing import Optional
import sys
import os

import typer

from .agent import run_agent, SYSTEM_PROMPT
from .agent_engine.tools import scan_server, propose_remediation
from .agent_engine.provider import summarize as summarize_advice
from .evidence import write_scan_snapshot  # will no-op if not implemented
from .ui import render_scan_output, render_advice_output
from .agent_engine.verify import verify_plan

app = typer.Typer(help="Cyberzard – CyberPanel AI assistant & security scan CLI")


def _find_repo_root(start: Path) -> Optional[Path]:
    """Walk up from start to find a directory containing .git or pyproject.toml."""
    cur = start.resolve()
    for _ in range(6):
        if (cur / ".git").is_dir() or (cur / "pyproject.toml").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def _self_update(channel: str = "edge") -> tuple[bool, str]:
    """Attempt to update the installation in-place.

    Strategy:
    - If running from a git checkout, run: git pull && python -m pip install -U .
    - Else, print guidance to re-run the installer script.
    Returns (success, message).
    """
    try:
        repo_root = _find_repo_root(Path(__file__).parent)
        if repo_root and (repo_root / ".git").exists() and shutil.which("git"):
            if channel == "stable":
                # Checkout latest tag that matches v*.*.*
                subprocess.run(["git", "-C", str(repo_root), "fetch", "--tags", "--force"], capture_output=True, text=True)
                tag_proc = subprocess.run(
                    ["bash", "-lc", f"git -C {shlex.quote(str(repo_root))} tag --list 'v*' --sort=-v:refname | head -n1"],
                    capture_output=True, text=True
                )
                tag = (tag_proc.stdout or "").strip()
                if not tag:
                    # Fallback to edge if no tags
                    channel = "edge"
                else:
                    co = subprocess.run(["git", "-C", str(repo_root), "checkout", "--quiet", tag], capture_output=True, text=True)
                    if co.returncode != 0:
                        return False, f"git checkout {tag} failed: {co.stderr.strip() or co.stdout.strip()}"
            if channel == "edge":
                pull = subprocess.run(["git", "-C", str(repo_root), "pull", "--ff-only"], capture_output=True, text=True)
                if pull.returncode != 0:
                    return False, f"git pull failed: {pull.stderr.strip() or pull.stdout.strip()}"
            # Upgrade install in the current interpreter environment
            pip = subprocess.run([sys.executable, "-m", "pip", "install", "-U", str(repo_root)], capture_output=True, text=True)
            if pip.returncode != 0:
                return False, f"pip upgrade failed: {pip.stderr.strip() or pip.stdout.strip()}"
            return True, ("Updated to latest tag and reinstalled" if channel == "stable" else "Updated from git and reinstalled successfully.")
        # Fallback guidance
        one_liner = "bash -c \"$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)\""
        return False, (
            "Unable to auto-update: not a git checkout. "
            "Re-run the installer to upgrade:\n  " + one_liner
        )
    except Exception as e:  # pragma: no cover
        return False, f"self-update failed: {e}"


@app.callback()
def _root(
    upgrade: bool = typer.Option(
        False,
        "--upgrade",
        help="Upgrade Cyberzard to the latest from GitHub (git installs).",
        show_default=False,
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="Select AI provider for this run: none, openai, anthropic.",
        case_sensitive=False,
    ),
) -> None:
    """Global options handler."""
    # Apply provider override early so downstream imports read the env
    if provider:
        val = provider.lower().strip()
        if val not in {"none", "openai", "anthropic"}:
            typer.echo("Invalid --provider value. Use: none | openai | anthropic")
            raise typer.Exit(code=2)
        os.environ["CYBERZARD_MODEL_PROVIDER"] = val
    if upgrade:
        ok, msg = _self_update()
        if ok:
            typer.echo(f"✅ {msg}")
            raise typer.Exit(code=0)
        else:
            typer.echo(msg)
            raise typer.Exit(code=1)


@app.command()
def scan(
    json_out: bool = typer.Option(False, "--json", help="Output full JSON result"),
    include_encrypted: bool = typer.Option(
        False,
        "--include-encrypted/--no-include-encrypted",
        help="Search for encrypted-looking files",
    ),
    verify: bool = typer.Option(True, "--verify/--no-verify", help="Reduce false positives via AI/heuristic verification"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Run safe read-only probes without prompting"),
    max_probes: int = typer.Option(5, "--max-probes", help="Max number of probe operations during verification"),
) -> None:
    """Run a quick system scan and print findings or plan summary."""
    typer.echo("🔍 Starting cyberzard scan...")
    results = scan_server(include_encrypted=include_encrypted)
    # Attempt evidence snapshot (best-effort)
    try:
        write_scan_snapshot(results)
    except Exception:
        pass
    plan = propose_remediation(results)
    verification = None
    if verify:
        interactive = sys.stdout.isatty()
        consent_answers: dict[str, bool] = {}

        def consent_cb(category: str) -> bool:
            if auto_approve:
                return True
            if not interactive:
                return False
            if category in consent_answers:
                return consent_answers[category]
            answer = typer.confirm(
                f"Allow Cyberzard to run up to {max_probes} safe, read-only probes for '{category}'?",
                default=True,
            )
            consent_answers[category] = bool(answer)
            return consent_answers[category]

        try:
            verification = verify_plan(
                results,
                plan,
                allow_probes=(auto_approve or interactive),
                max_probes=max_probes,
                consent_callback=consent_cb,
            )
        except Exception:
            verification = {"success": False, "error": "verification_failed"}

    if json_out:
        payload = {"scan": results, "remediation": plan}
        if verification is not None:
            payload["verification"] = verification
        typer.echo(json.dumps(payload, indent=2))
        return
    # Decide whether to use rich or plain text based on TTY and NO_COLOR
    use_rich = sys.stdout.isatty() and os.getenv("NO_COLOR") not in {"1", "true", "TRUE"}
    if use_rich:
        try:
            # Prefer rendering verified results when available
            if verification and verification.get("success"):
                from .ui import render_verified_output  # local import to avoid hard dep if missing
                render_verified_output(results, verification)
            else:
                render_scan_output(results, plan)
            return
        except Exception:
            # Fallback to plain output if rich rendering fails for any reason
            pass
    summary = results.get("summary", {})
    typer.echo(json.dumps(summary, indent=2))
    if verification and verification.get("success"):
        typer.echo("\nVerified remediation plan (preview):")
        typer.echo(json.dumps(verification.get("verified_plan", {}), indent=2))
        if verification.get("dropped"):
            typer.echo("\nDropped (with reasons):")
            typer.echo(json.dumps(verification.get("dropped"), indent=2))
        if verification.get("downgraded"):
            typer.echo("\nDowngraded (manual review):")
            typer.echo(json.dumps(verification.get("downgraded"), indent=2))
    else:
        typer.echo("\nRemediation plan (preview):")
        typer.echo(json.dumps(plan, indent=2))


@app.command()
def agent(
    query: str = typer.Argument(..., help="Instruction or question for the assistant"),
    steps: int = typer.Option(5, "--steps", help="Max internal reasoning/tool steps"),
    show_plan: bool = typer.Option(False, "--show-plan", help="Show full reasoning JSON output"),
) -> None:
    """Ask the agent to reason with available tools."""
    result = run_agent(user_query=query, max_steps=steps)
    if show_plan:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(result.get("final"))


@app.command("show-prompt")
def show_prompt() -> None:
    """Show the system prompt used by the agent."""
    typer.echo(SYSTEM_PROMPT)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("cyberzard version 0.1.0")


@app.command()
def upgrade(
    channel: str = typer.Option("edge", "--channel", help="Upgrade channel: edge (main) or stable (latest tag)",
                                case_sensitive=False)
) -> None:
    """Upgrade Cyberzard to the latest version (git installs)."""
    ch = channel.lower().strip()
    if ch not in {"edge", "stable"}:
        typer.echo("Invalid --channel value. Use: edge | stable")
        raise typer.Exit(code=2)
    ok, msg = _self_update(channel=ch)
    if ok:
        typer.echo(f"✅ {msg}")
    else:
        typer.echo(msg)
        raise typer.Exit(code=1)


@app.command()
def advise(
    json_out: bool = typer.Option(False, "--json", help="Output combined JSON"),
    include_encrypted: bool = typer.Option(
        False,
        "--include-encrypted/--no-include-encrypted",
        help="Search for encrypted-looking files",
    ),
) -> None:
    """Run a scan and print concise provider-based advice."""
    typer.echo("🧠 Generating advice from scan...")
    results = scan_server(include_encrypted=include_encrypted)
    try:
        write_scan_snapshot(results)
    except Exception:
        pass
    advice = summarize_advice(results)
    if json_out:
        typer.echo(json.dumps({"scan": results, "advice": advice}, indent=2))
    else:
        use_rich = sys.stdout.isatty() and os.getenv("NO_COLOR") not in {"1", "true", "TRUE"}
        if use_rich:
            try:
                render_advice_output(advice, results)
                return
            except Exception:
                pass
        typer.echo(advice)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
