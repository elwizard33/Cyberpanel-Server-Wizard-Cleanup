from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .agent import run_agent, SYSTEM_PROMPT
from .agent_engine.tools import scan_server, propose_remediation
from .agent_engine.provider import summarize as summarize_advice
from .evidence import write_scan_snapshot  # will no-op if not implemented

app = typer.Typer(help="Cyberzard – CyberPanel AI assistant & security scan CLI")


@app.command()
def scan(
    json_out: bool = typer.Option(False, "--json", help="Output full JSON result"),
    include_encrypted: bool = typer.Option(
        False,
        "--include-encrypted/--no-include-encrypted",
        help="Search for encrypted-looking files",
    ),
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
    if json_out:
        typer.echo(json.dumps({"scan": results, "remediation": plan}, indent=2))
        return
    summary = results.get("summary", {})
    typer.echo(json.dumps(summary, indent=2))
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
        typer.echo(advice)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
