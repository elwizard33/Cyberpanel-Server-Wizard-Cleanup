---
title: AI & Agent
description: Internal AI assistant architecture
---

# AI & Agent

Cyberzard combines deterministic scanners with an optional provider-based advice summarizer.

Deterministic tools (non-destructive):
- Processes and known malicious file paths
- Optional encrypted-looking file search (heuristic)
- Cron inspection for suspicious patterns
- Systemd unit inspection for suspicious names/status
- Users and authorized_keys overview (counts, modes)
- ld.so.preload presence and excerpt
- CyberPanel core file metadata (exists/size/mtime)

Safety:
- No remote downloads or executions
- Remediation is dry-run only with `command_preview`
- Paths are shell-quoted
 - Verification probes are read-only (e.g., `ps`, `systemctl is-active`, file excerpts)
 - Probes require explicit per-category user consent in TTY, unless `--auto-approve` is used

Advice Provider:
- `CYBERZARD_MODEL_PROVIDER` = `none` (default), `openai`, or `anthropic`
- When unset or SDK/API key missing, static advice is produced from summary counts
- When configured, a compact prompt is sent; timeouts and sizes are constrained
 - Optional: action-level justifications via `justify_actions`; degrades to `None` when not configured

Verification Layer:
- `verify_plan(results, plan, allow_probes, max_probes, consent_callback)` cross-checks actions against evidence and optional safe probes
- Classifies actions into: kept (verified), dropped (with reason), or downgraded (manual review)
- Probe categories tracked include: `systemd`, `file`, and `ps`; all are read-only
- CLI integration: `--verify/--no-verify`, `--auto-approve`, `--max-probes`


The agent implements a constrained ReAct loop:
1. System prompt enumerates safe tools.
2. Model proposes tool call OR final answer.
3. Framework validates name & args; executes.
4. Result appended; loop continues until final.

Safety levers: step cap, byte cap, no shell, tool schema validation.

