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
from .agent_engine.tools import scan_server, propose_remediation, scan_email_system, propose_email_hardening
from .agent_engine import (
    summarize_email_security,
    generate_email_fix_guide,
)
from .email_execute import run_guided
from .agent_engine.provider import summarize as summarize_advice
from .evidence import write_scan_snapshot  # will no-op if not implemented
from .ui import render_scan_output, render_advice_output
from .agent_engine.verify import verify_plan
from .chat import run_chat
from . import __version__
from . import updater as _updater
from .n8n_setup import run_n8n_setup

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
        # Prefer built-in updater for frozen binaries, else git self-update
        if _updater.is_frozen():
            try:
                res = _updater.upgrade(channel="stable", dry_run=False)
                status = res.get("status")
                if status == "ok":
                    typer.echo(f"✅ Upgraded binary to {res.get('version', 'latest')}")
                    raise typer.Exit(code=0)
                elif status == "unsupported":
                    pass  # fall through to git path
                else:
                    reason = res.get("reason", "unknown_error")
                    typer.echo(f"Update failed: {reason}")
                    raise typer.Exit(code=1)
            except Exception as e:  # pragma: no cover
                typer.echo(f"Update failed: {e}")
                raise typer.Exit(code=1)
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
    try:
        from . import __version__
        v = __version__
    except Exception:
        # Fallback to metadata if import failed for some reason
        try:
            from importlib.metadata import version as _pkg_version  # Python 3.8+
            v = _pkg_version("cyberzard")
        except Exception:
            v = "unknown"
    typer.echo(f"cyberzard version {v}")


@app.command()
def upgrade(
    channel: str = typer.Option("stable", "--channel", help="Upgrade channel for releases: stable (latest release) or edge (same as stable for now)", case_sensitive=False),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show planned actions without performing changes (frozen builds)"),
) -> None:
    """Upgrade Cyberzard to the latest version.

    - For frozen binaries (installer/PyInstaller), uses the built-in self-updater.
    - For git-based installs (development), attempts a git+pip self update.
    """
    ch = channel.lower().strip()
    if ch not in {"edge", "stable"}:
        typer.echo("Invalid --channel value. Use: edge | stable")
        raise typer.Exit(code=2)

    before = __version__ if '__version__' in globals() else 'unknown'
    if _updater.is_frozen():
        try:
            res = _updater.upgrade(channel=ch, dry_run=dry_run)
            status = res.get("status")
            if status == "dry_run":
                typer.echo("[dry-run] Would download: " + res.get("download", ""))
                typer.echo("[dry-run] Would verify using: " + res.get("checksums", ""))
                typer.echo("[dry-run] Would replace: " + res.get("target", ""))
                return
            if status == "ok":
                after = res.get("version", "unknown")
                typer.echo(f"✅ Upgraded binary {res.get('target')} to {after}")
                return
            if status == "unsupported":
                # Fall through to git path if not frozen
                pass
            else:
                reason = res.get("reason", "unknown_error")
                if reason == "checksum_mismatch":
                    typer.echo("Checksum mismatch while updating. Aborting.")
                else:
                    typer.echo(f"Update failed: {reason}")
                raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Update failed: {e}")
            raise typer.Exit(code=1)

    # Non-frozen or unsupported -> git path
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


@app.command("email-security")
def email_security(
    domain: Optional[str] = typer.Option(None, "--domain", help="Root domain (for DNS mismatch heuristics)"),
    json_out: bool = typer.Option(False, "--json", help="Output full JSON"),
    max_risk: str = typer.Option("high", "--max-risk", help="Maximum risk level to include: low|medium|high"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip confirmation prompts (non-interactive)"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Simulate actions without executing commands"),
    run: bool = typer.Option(False, "--run", help="Execute actions after scan (guided)"),
    ai_refine: bool = typer.Option(True, "--ai-refine/--no-ai-refine", help="Attempt AI refinement on failures"),
    log_dir: Optional[str] = typer.Option(None, "--log-dir", help="Directory to write persistent JSON logs for this run"),
) -> None:
    """Scan CyberPanel email stack and optionally run guided hardening."""
    typer.echo("📧 Scanning email stack...")
    scan = scan_email_system(domain=domain)
    plan = propose_email_hardening(scan)
    provider_enabled = (os.getenv("CYBERZARD_MODEL_PROVIDER") or "none").lower().strip() in {"openai", "anthropic"}
    summary_txt = summarize_email_security(scan, plan) if provider_enabled else None
    if run:
        actions = plan.get("plan", {}).get("actions", [])
        # Permission gating for email actions (interactive preview)
        if not auto_approve and sys.stdout.isatty():
            preview = [
                f"Total actions: {len(actions)}",
                f"Max risk allowed: {max_risk}",
            ]
            typer.echo("About to execute guided email actions:\n" + "\n".join(preview))
            approved = typer.confirm("Proceed with execution?", default=False)
            if not approved:
                actions = []
        exec_result = run_guided(
            actions,
            interactive=sys.stdout.isatty(),
            auto_approve=auto_approve,
            max_risk=max_risk,
            dry_run=dry_run,
            ai_refine=ai_refine,
            scan_results=scan,
            provider_enabled=provider_enabled,
            fail_fast=False,
            timeout=90,
            log_dir=log_dir,
        )
    else:
        exec_result = None
    if json_out:
        payload = {"scan": scan, "plan": plan, "summary": summary_txt}
        if exec_result:
            payload["execution"] = exec_result
        typer.echo(json.dumps(payload, indent=2))
        return
    use_rich = sys.stdout.isatty() and os.getenv("NO_COLOR") not in {"1", "true", "TRUE"}
    if use_rich:
        try:
            from .ui import render_email_security, render_email_execution_progress
            render_email_security(scan, plan, summary_txt)
            if exec_result:
                render_email_execution_progress(exec_result.get("executions", []), exec_result.get("summary", {}))
            return
        except Exception:
            pass
    # Plain fallback
    s = scan.get("summary", {})
    typer.echo(json.dumps(s, indent=2))
    if summary_txt:
        typer.echo("\nAI Summary:\n" + summary_txt)
    if exec_result:
        typer.echo("\nExecution Summary:")
        typer.echo(json.dumps(exec_result.get("summary", {}), indent=2))
        if exec_result.get("log_path"):
            typer.echo(f"Log: {exec_result['log_path']}")


    @app.command()
    def tui() -> None:
        """Launch the Textual TUI (optional dependency)."""
        try:
            # Lazy import to avoid hard dependency when not installed
            from .tui import run_tui  # type: ignore
        except Exception as e:
            typer.echo("Textual TUI not installed. Install optional dependency first:")
            typer.echo("  pip install 'textual>=0.60'")
            typer.echo(f"Detail: {e}")
            raise typer.Exit(code=1)
        run_tui()


@app.command("email-fix")
def email_fix(
    domain: Optional[str] = typer.Option(None, "--domain", help="Root domain (for DNS mismatch heuristics)"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    max_risk: str = typer.Option("high", "--max-risk", help="Maximum risk level: low|medium|high"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip confirmation prompts"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Simulate actions without executing commands"),
    run: bool = typer.Option(True, "--run/--no-run", help="Execute actions (guided)"),
    ai_refine: bool = typer.Option(True, "--ai-refine/--no-ai-refine", help="Attempt AI refinement on failures"),
    log_dir: Optional[str] = typer.Option(None, "--log-dir", help="Directory to write persistent JSON logs for this run"),
) -> None:
    """Generate full email remediation guide and optionally run guided execution."""
    typer.echo("🛠 Generating email fix guide...")
    scan = scan_email_system(domain=domain)
    plan = propose_email_hardening(scan)
    provider_enabled = (os.getenv("CYBERZARD_MODEL_PROVIDER") or "none").lower().strip() in {"openai", "anthropic"}
    guide = generate_email_fix_guide(scan, plan) if provider_enabled else None
    exec_result = None
    if run:
        actions = plan.get("plan", {}).get("actions", [])
        exec_result = run_guided(
            actions,
            interactive=sys.stdout.isatty(),
            auto_approve=auto_approve,
            max_risk=max_risk,
            dry_run=dry_run,
            ai_refine=ai_refine,
            scan_results=scan,
            provider_enabled=provider_enabled,
            fail_fast=False,
            timeout=90,
            log_dir=log_dir,
        )
    if json_out:
        payload = {"scan": scan, "plan": plan, "guide": guide}
        if exec_result:
            payload["execution"] = exec_result
        typer.echo(json.dumps(payload, indent=2))
        return
    use_rich = sys.stdout.isatty() and os.getenv("NO_COLOR") not in {"1", "true", "TRUE"}
    if use_rich:
        try:
            from .ui import render_email_security, render_email_execution_progress, render_email_fix
            render_email_security(scan, plan, None)
            if guide:
                render_email_fix(guide)
            if exec_result:
                render_email_execution_progress(exec_result.get("executions", []), exec_result.get("summary", {}))
            return
        except Exception:
            pass
    # Plain fallback
    s = scan.get("summary", {})
    typer.echo(json.dumps(s, indent=2))
    if guide:
        typer.echo("\nGuide:\n" + guide[:4000])
    if exec_result:
        typer.echo("\nExecution Summary:")
        typer.echo(json.dumps(exec_result.get("summary", {}), indent=2))
        if exec_result.get("log_path"):
            typer.echo(f"Log: {exec_result['log_path']}")


@app.command()
def chat(
    verify: bool = typer.Option(True, "--verify/--no-verify", help="Verify remediation suggestions during chat"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Auto-approve safe, read-only probes without prompting"),
    max_probes: int = typer.Option(5, "--max-probes", help="Max number of probe operations during verification"),
    session: str = typer.Option("default", "--session", help="Conversation session id for persisted history"),
) -> None:
    """Interactive AI-powered chat (LangChain agent mode)."""
    typer.echo("Launching Cyberzard AI agent chat (LangChain mode)...")
    run_chat(verify=verify, auto_approve=auto_approve, max_probes=max_probes, session_id=session)


@app.command("n8n-setup")
def n8n_setup(
    domain: str = typer.Option(..., "--domain", help="Root domain, e.g., example.com"),
    subdomain: str = typer.Option("n8n", "--subdomain", help="Subdomain to use for n8n"),
    mode: str = typer.Option("native", "--mode", help="Deployment mode: native or tunnel", case_sensitive=False),
    port: int = typer.Option(5678, "--port", help="Local port to bind n8n"),
    basic_auth: bool = typer.Option(False, "--basic-auth/--no-basic-auth", help="Enable HTTP Basic Auth for n8n"),
    basic_auth_user: str = typer.Option("admin", "--basic-user", help="Basic auth username"),
    timezone: str = typer.Option("UTC", "--tz", help="Timezone for n8n"),
    n8n_image: str = typer.Option("n8nio/n8n:latest", "--n8n-image", help="n8n image"),
    postgres_image: str = typer.Option("postgres:16", "--postgres-image", help="Postgres image"),
    write_only: bool = typer.Option(False, "--write-only", help="Only write scripts; do not execute"),
    out_dir: Optional[str] = typer.Option(None, "--out-dir", help="Directory to write scripts to"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing files when writing"),
    interactive: bool = typer.Option(False, "--interactive/--no-interactive", help="Prompt before applying"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Apply without prompting (non-interactive)"),
    json_out: bool = typer.Option(False, "--json", help="Print JSON summary to stdout"),
) -> None:
    """Guide-and-generate scripts to deploy n8n on CyberPanel, optionally applying them.

    This command delegates to run_n8n_setup for orchestration, which handles prompting,
    agent-mediated execution, logging, and memory recording.
    """
    result = run_n8n_setup(
        domain=domain,
        subdomain=subdomain,
        mode=mode.lower().strip(),
        port=port,
        basic_auth=basic_auth,
        basic_auth_user=basic_auth_user,
        timezone=timezone,
        n8n_image=n8n_image,
        postgres_image=postgres_image,
        write_only=write_only,
        out_dir=out_dir,
        overwrite=overwrite,
        interactive=interactive,
        auto_approve=auto_approve,
        json_out=json_out,
    )
    # Human-friendly echo when TTY and not JSON
    if not json_out:
        if result.get("ok") and result.get("applied"):
            typer.echo(f"✅ Applied {result.get('mode')} setup (script at: {result.get('apply_script')})")
            if result.get("apply_log"):
                typer.echo(f"   Log: {result.get('apply_log')}")
        elif result.get("aborted"):
            typer.echo("ℹ️  Apply aborted (not approved)")
        else:
            typer.echo("❌ Apply failed")
            raise typer.Exit(code=1)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
