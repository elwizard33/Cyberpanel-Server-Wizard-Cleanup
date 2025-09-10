---
title: Commands
description: CLI command reference
---

# Commands

## Scan

Run a deterministic system scan.

Flags:
- `--json` output full JSON including remediation preview
- `--include-encrypted/--no-include-encrypted` include heuristic search for encrypted-looking files

Examples:

```bash
cyberzard scan
cyberzard scan --json --include-encrypted
```

## Advise

Run a scan and print concise advice. Uses `CYBERZARD_MODEL_PROVIDER` (none|openai|anthropic); defaults to static advice.

```bash
CYBERZARD_MODEL_PROVIDER=none cyberzard advise
CYBERZARD_MODEL_PROVIDER=openai OPENAI_API_KEY=... cyberzard advise --include-encrypted
```

## Agent

Ask the minimal local agent to perform actions with tools.

```bash
cyberzard agent "scan the server"
cyberzard agent --steps 5 "read /etc/passwd"
```


Run `cyberzard --help` for full list.

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `scan` | Run all scanners, list findings | `--json` for machine output |
| `advise` | Generate remediation advice | `--severity high` (filter) |
| `explain` | Plain summary of findings | `--max` limit items |
| `agent` | ReAct reasoning loop | `--steps N` step cap |

## scan
Collects process/file/cron/user indicators quickly.

## agent
Uses provider (if configured) to iteratively call tools until answer formed.

