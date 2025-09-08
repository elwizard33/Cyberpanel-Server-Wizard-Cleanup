---
title: (Legacy) System Architecture
---
## Legacy Documentation Notice

Moved to Starlight at `/architecture`.

Original content removed.

## 1. High-Level Component Map (Textual)

```
┌──────────────────────────────────────────────────────────────┐
| CLI (Typer)                                                  |
|  scan | advise | explain | agent | remediate | shell         |
└──────────────┬──────────────────────────────────────────────┘
			   │ invokes
			   v
┌──────────────────────────────────────────────────────────────┐
| Scanners Layer                                               |
|  file | process | cron | encryption | composite | (yara stub) |
└──────────────┬──────────────────────────────────────────────┘
			   │ produces List[Finding]
			   v
┌──────────────────────────────────────────────────────────────┐
| Reporting / Serialization                                    |
|  tables (rich) | json export | advice generator              |
└──────────────┬──────────────────────────────────────────────┘
			   │ feeds context
			   v
┌──────────────────────────────────────────────────────────────┐
| AI Layer                                                     |
|  provider abstraction | agent loop | explain summary          |
|  tool registry & sandbox execution                           |
└──────────────┬──────────────────────────────────────────────┘
			   │ may request more data via tools
			   v
┌──────────────────────────────────────────────────────────────┐
| Remediation                                                  |
|  plan builder | executor | evidence preservation             |
└──────────────┬──────────────────────────────────────────────┘
			   │ writes
			   v
┌──────────────────────────────────────────────────────────────┐
| Evidence / State                                             |
|  last_scan.json | preserved/<finding_id>/ files              |
└──────────────────────────────────────────────────────────────┘
```

## 2. Core Modules & Responsibilities

| Module | Path (prefix) | Responsibility |
|--------|---------------|----------------|
| `config` | `cyberzard/config.py` | Settings, IOC constants, environment parsing |
| `core.models` | `cyberzard/core/models.py` | Data classes: Finding, ScanReport, RemediationAction, etc. |
| `scanners` | `cyberzard/scanners/` | Individual detection routines assembled by orchestrator |
| `reporting` | `cyberzard/reporting/` | Human (rich) & machine (JSON) formatting, advice generation |
| `agent` | `cyberzard/agent.py` & related | ReAct loop, model prompt construction |
| `tools` | `cyberzard/tools/` | Tool registry + safe callable wrappers for agent |
| `remediation` | `cyberzard/remediation/` | Plan construction & execution with safety checks |
| `evidence` | `cyberzard/evidence.py` | Persistence of last scan, file preservation |
| `logging` | `cyberzard/logging/` | Logging initialization (future structured logging) |
| `security` | various | Allowlist checks, context trimming, severity policy |

## 3. Data Flow Sequence (Scan → Report → Agent → Remediate)

1. User invokes `scan` command.
2. Scanners run sequentially (lightweight; can future parallelize) building a list of `Finding` objects.
3. Findings rendered (rich tables) or exported as JSON; prior snapshot loaded to compute delta (added/removed IDs).
4. Optional AI operations (`explain`, `advise`, `agent`) reuse scan stage (re-running to ensure freshness) and build compact context lines.
5. Agent may call tools to refine understanding (e.g., fetch a file snippet) before producing final answer.
6. User optionally runs `remediate` which rescans (ensuring minimal race with environment changes), builds `RemediationPlan` filtered by flags, and executes permitted actions.
7. Evidence (last scan, preserved files) updated.

## 4. Provider & Tool Interaction

The agent constructs a system prompt enumerating allowed tools with simple JSON-style argument schemas. The model must respond with either:

- A final answer block
- A tool invocation object `{ "tool": "name", "args": { ... } }`

Framework validates tool name & args, executes, captures output (size‑bounded), and appends it to conversational context. This loop repeats until a final answer or step limit.

## 5. Extensibility Points

| Extension | How to Add | Notes |
|-----------|-----------|-------|
| New scanner | Create module in `scanners/` implementing `run()` returning findings; register in orchestrator list | Keep fast & deterministic |
| New tool | Add function + schema entry in tool registry | Enforce argument validation & output size caps |
| New provider | Implement wrapper returning text + (optional) reasoning metadata | Ensure key auto-disable fallback |
| New remediation action | Extend enum + executor logic + safety checks | Must consider evidence preservation implications |

## 6. Concurrency & Performance Considerations

Current design is synchronous; file/process enumeration cost is modest. Future enhancements may introduce async or thread pooling for IO-heavy operations (e.g., large tree traversals or external reputation lookups). YARA scanning (stubbed) could be parallelized per rule group.

## 7. Error Handling Strategy

- Scanner errors should degrade to warning log + partial results (avoid total failure).
- Agent tool errors surfaced inline so reasoning can adapt.
- Remediation failures are per-action (no rollback), enabling partial success reporting.

## 8. Security Boundaries

Key boundary: Tool registry isolates model from arbitrary system access. Only curated functions with predictable side effects are exposed, blocking remote code execution vectors via prompt manipulation.

## 9. Future Architectural Evolutions

- Pluggable output (SARIF, HTML report)
- Background daemon mode with periodic scans & diff notifications
- State versioning & historical timeline queries
- Policy-as-code rules (YAML) for custom indicator injection
- Container image & scanning inside ephemeral sandbox

---

Next: See `roadmap.md` for planned milestones.
