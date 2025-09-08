from __future__ import annotations

import json
import typer

from .agent import run_agent, SYSTEM_PROMPT

app = typer.Typer(help="Cyberzard – CyberPanel AI assistant & security scan CLI")


@app.command()
def assistant(
    query: str = typer.Argument(..., help="Instruction or question for the assistant"),
    max_steps: int = typer.Option(5, help="Max internal reasoning/tool steps"),
    show_plan: bool = typer.Option(False, help="Show full reasoning JSON output"),
):
    result = run_agent(user_query=query, max_steps=max_steps)
    if show_plan:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(result.get("final"))


@app.command()
def scan(include_encrypted: bool = typer.Option(True, help="Detect encrypted extension candidates")):
    result = run_agent(user_query="scan", max_steps=3)
    if result.get("remediation_plan"):
        typer.echo(json.dumps(result["remediation_plan"], indent=2))
    else:
        typer.echo("No remediation plan produced.")


@app.command("show-prompt")
def show_prompt():
    typer.echo(SYSTEM_PROMPT)


def main():  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
"""Command-line interface for cyberzard."""

import typer
from typing import Optional
from pathlib import Path

app = typer.Typer()


@app.command()
def scan(
    target: Optional[Path] = typer.Argument(None, help="Target directory to scan"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output file for results"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
) -> None:
    """Run security scans on the target system."""
    typer.echo(f"🔍 Starting cyberzard scan...")
    
    if target:
        typer.echo(f"Target: {target}")
    else:
        typer.echo("Scanning current system")
        
    # Placeholder implementation
    typer.echo("✅ Scan completed - no implementation yet")


@app.command()
def remediate(
    plan_file: Path = typer.Argument(..., help="Remediation plan file"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Run in dry-run mode"),
) -> None:
    """Execute a remediation plan."""
    typer.echo(f"🛠️  Processing remediation plan: {plan_file}")
    
    if dry_run:
        typer.echo("Running in dry-run mode...")
    else:
        typer.echo("⚠️  Executing remediation actions...")
        
    # Placeholder implementation
    typer.echo("✅ Remediation completed - no implementation yet")


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("cyberzard version 0.1.0")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
