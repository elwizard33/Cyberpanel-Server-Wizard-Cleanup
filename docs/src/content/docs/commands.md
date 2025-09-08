---
title: Commands
description: CLI command reference
---

# Commands

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

