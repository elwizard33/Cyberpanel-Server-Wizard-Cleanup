from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .agent import run_agent, SYSTEM_PROMPT

app = typer.Typer(help="Cyberzard – CyberPanel AI assistant & security scan CLI")


@app.command()
def scan(
    json_out: bool = typer.Option(False, "--json", help="Output full JSON result"),
) -> None:
    """Run a quick system scan and print findings or plan summary."""
    typer.echo("🔍 Starting cyberzard scan...")
    result = run_agent(user_query="scan", max_steps=3)
    if json_out:
        typer.echo(json.dumps(result, indent=2))
        return
    plan = result.get("remediation_plan")
    if plan:
        typer.echo(json.dumps(plan, indent=2))
    else:
        typer.echo("No remediation plan produced.")


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


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
