"""CLI entrypoint for CyberPanel AI Wizard.

Commands:
    scan       Run scanners and display findings (TTY or JSON)
    agent      Run ReAct agent loop with tool calling
    remediate  Apply limited remediation actions
    advise     Generate hardening advice (static + optional AI)
    explain    Summarize findings in natural language (AI if available)
    shell      Interactive loop allowing repeated scan/advice queries

Exit codes (scan):
    0 = no findings OR only low/info
    1 = medium findings present
    2 = high findings present
    3 = critical findings present
"""
from __future__ import annotations

import json
from typing import List, Optional

import typer

from cyberzard.scanners import run_all_scanners
from cyberzard.agent import run_agent
from cyberzard.config import get_settings, RecommendedAction
from cyberzard.evidence import preserve_file, save_last_scan, load_last_scan
from cyberzard.tools.registry import execute_tool
from cyberzard.remediation import execute_plan
from cyberzard.core.models import RemediationAction, RemediationPlan
from cyberzard.core.models import Finding, ScanReport
from cyberzard.logging.setup import init_logging
from cyberzard.reporting.formatter import render_findings
from cyberzard.reporting.json_export import findings_to_json
from cyberzard.reporting.advice import generate_advice
from cyberzard.core.react import build_system_prompt
from cyberzard.tools.registry import get_schema

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def scan(
    json_output: bool = typer.Option(False, "--json", help="Output JSON report"),
    verbose: int = typer.Option(0, "-v", count=True),
    exit_code: bool = typer.Option(True, "--exit-code/--no-exit-code", help="Set process exit code based on highest severity"),
):
    """Run all scanners and display findings.

    By default renders rich tables grouped by severity. Pass --json for
    machine readable stable-ordered JSON array of findings.
    """
    init_logging(verbose)
    settings = get_settings()
    prev = load_last_scan(settings.evidence_dir)
    findings: List[Finding] = run_all_scanners()
    # Basic ScanReport instantiation retained for future meta use
    _ = ScanReport(findings=findings)
    # Delta calculation (ids only)
    if prev:
        prev_ids = {p.get("id") for p in prev}
        curr_ids = {f.id for f in findings}
        added = sorted(curr_ids - prev_ids)
        removed = sorted(prev_ids - curr_ids)
    else:
        added, removed = [], []
    if json_output:
        payload = json.loads(findings_to_json(findings))
        if prev:
            typer.echo(json.dumps({"findings": payload, "delta": {"added": added, "removed": removed}}, indent=2))
        else:
            typer.echo(json.dumps({"findings": payload, "delta": {"added": added, "removed": removed}}, indent=2))
    else:
        render_findings(findings)
        if prev:
            typer.echo(f"Delta: +{len(added)} / -{len(removed)} findings since last scan")
    # Persist current scan (best effort)
    save_last_scan(findings, settings.evidence_dir)
    if exit_code:
        sev_ranks = {"info":0,"low":0,"medium":1,"high":2,"critical":3}
        highest = 0
        for f in findings:
            highest = max(highest, sev_ranks.get(f.severity.value,0))
        raise typer.Exit(code=highest)
@app.command()
def advise(
    json_output: bool = typer.Option(False, "--json", help="Output JSON array of advice strings"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Override provider for enrichment"),
):
    """Generate hardening / remediation advice.

    If provider available, future enrichment may expand recommendations.
    """
    init_logging(0)
    findings: List[Finding] = run_all_scanners()
    tips = generate_advice(findings)
    if json_output:
        typer.echo(json.dumps(tips, indent=2))
    else:
        for t in tips:
            typer.echo(f"- {t}")


@app.command()
def explain(
    provider: str = typer.Option("openai", "--provider", help="Model provider (openai|anthropic|none)", case_sensitive=False),
    model: str = typer.Option(None, "--model", help="Override model id"),
    max_tokens: int = typer.Option(400, "--max-tokens", help="Max tokens for explanation"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON with transcript"),
):
    """Summarize current findings in natural language (AI-assisted if provider available)."""
    init_logging(0)
    findings: List[Finding] = run_all_scanners()
    context_lines = [f"{f.id} {f.severity.value} {f.category.value} {f.message or f.rationale}" for f in findings[:50]]
    user_query = "Provide a concise plain-language summary of these findings and prioritized next steps."
    prompt_extra = "Findings list:\n" + "\n".join(context_lines)
    # Reuse agent infra for a single call
    result = run_agent(provider=provider, user_query=user_query + "\n" + prompt_extra, model=model, max_steps=2, verbose=False)
    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(result["final"])  # degrade prints provider notice if none


@app.command()
def shell():
    """Interactive shell for repeated scanning & advice queries."""
    init_logging(0)
    typer.echo("Entering AI Wizard shell. Type 'scan', 'advise', 'explain', or 'quit'.")
    while True:
        try:
            cmd = input("wizard> ").strip().lower()
        except EOFError:
            break
        if cmd in {"quit","exit"}:
            break
        if cmd == "scan":
            findings = run_all_scanners()
            render_findings(findings)
            continue
        if cmd == "advise":
            tips = generate_advice(run_all_scanners())
            for t in tips:
                typer.echo(f"- {t}")
            continue
        if cmd == "explain":
            findings = run_all_scanners()
            context_lines = [f"{f.id} {f.severity.value} {f.category.value} {f.message or f.rationale}" for f in findings[:50]]
            user_query = "Provide a concise plain-language summary of these findings and prioritized next steps."
            prompt_extra = "Findings list:\n" + "\n".join(context_lines)
            result = run_agent(provider="openai", user_query=user_query + "\n" + prompt_extra, model=None, max_steps=2, verbose=False)
            typer.echo(result["final"])
            continue
        typer.echo("Unknown command. Use scan|advise|explain|quit")


@app.command()
def agent(
    query: str = typer.Argument(..., help="User query / objective for the agent"),
    provider: str = typer.Option("openai", "--provider", case_sensitive=False),
    model: str = typer.Option(None, "--model", help="Override model id"),
    steps: int = typer.Option(6, "--steps", help="Max tool reasoning steps"),
    verbose: bool = typer.Option(False, "--verbose", help="Print step outputs"),
    json_output: bool = typer.Option(False, "--json", help="Emit full transcript JSON"),
):
    """Run interactive agent loop with tool calling.

    Requires provider API setup (environment variables) for full capability. In
    degraded mode (no key / SDK), returns a single response with no tool calls.
    """
    init_logging(0)
    result = run_agent(provider=provider, user_query=query, model=model, max_steps=steps, verbose=verbose)
    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(result["final"])  # final assistant answer


@app.command()
def remediate(
    finding_id: str = typer.Option("", "--finding", help="Specific finding id to target (optional)"),
    delete: bool = typer.Option(False, "--delete", help="Apply file removals (disable dry run for those)"),
    kill: bool = typer.Option(False, "--kill", help="Apply process kills (disable dry run for those)"),
    preserve: bool = typer.Option(False, "--preserve", help="Preserve evidence before destructive actions"),
):
    """Run scan and apply limited remediation actions.

    For now supports remove (file unlink) and kill (SIGTERM). Evidence
    preservation available for remove actions.
    """
    init_logging(0)
    settings = get_settings()
    findings = run_all_scanners()
    target_findings = findings
    if finding_id:
        target_findings = [f for f in findings if f.id == finding_id]
        if not target_findings:
            typer.echo("No matching finding id")
            raise typer.Exit(code=1)
    actions = []
    for f in target_findings:
        if f.recommended_action == RecommendedAction.remove and f.path and delete:
            actions.append(RemediationAction(finding_id=f.id, action=RecommendedAction.remove, target=str(f.path), dry_run=False))
        elif f.recommended_action == RecommendedAction.kill and f.pid and kill:
            actions.append(RemediationAction(finding_id=f.id, action=RecommendedAction.kill, target=str(f.pid), dry_run=False))
    plan = RemediationPlan(actions=actions, summary=f"Applying {len(actions)} actions")
    results = execute_plan(plan, dry_run=False, preserve_evidence=preserve)
    typer.echo(json.dumps({"summary": plan.summary, "results": [r.dict() for r in results]}, indent=2))


def main():  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
