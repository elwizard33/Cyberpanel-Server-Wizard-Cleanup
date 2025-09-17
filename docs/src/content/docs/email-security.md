---
title: Email Security Commands
description: Scan, plan, and guided remediation for the CyberPanel email stack
---

# Email Security & Hardening

Cyberzard provides two focused commands for the CyberPanel email subsystem:

| Command | Purpose | Default Behavior |
|---------|---------|------------------|
| `email-security` | Scan services, queue, auth failures, DNS mismatch, TLS, rate limits, Fail2Ban, Dovecot hardening and produce an action plan (optionally guided execution) | Dry‑run (no commands executed) |
| `email-fix` | Generate comprehensive markdown remediation/hardening guide (AI when enabled) + optional guided execution pipeline | Dry‑run + guide |

AI is optional. Without AI keys configured output falls back to deterministic static summaries/guides.

Cyberzard now powers the execution path via the AI agent's shell tool (when enabled), with a safe fallback to direct execution. Interactive permission gating previews the plan before actions are run.

## What Is Collected

The scanner is read‑only:
- Service status: postfix, dovecot, mailscanner, cpecs
- Mail queue size + backlog flag (>500)
- SASL auth failures (count, top IP, top /24 aggregation)
- DNS mismatch for `mail.<domain>` vs public IP (when `--domain` supplied)
- RainLoop domain config host references
- Fail2Ban postfix-sasl jail status
- Postfix TLS & rate limiting parameters (`postconf -n`)
- Dovecot brute force mitigation hints (auth_failure_delay, negative cache)
- Firewall heuristic (ufw status)
- Tail of mail log (truncated)

No modifications are made during scanning.

## Common Flags

| Flag | Applies To | Description |
|------|------------|-------------|
| `--domain <root>` | both | Enable DNS mismatch + RainLoop host heuristics |
| `--json` | both | Emit structured JSON instead of rich UI |
| `--run` | both | Perform guided execution after planning |
| `--dry-run/--no-dry-run` | both | Simulate vs actually run commands (default: dry-run) |
| `--max-risk {low|medium|high}` | both | Skip actions above threshold (default: high) |
| `--auto-approve` | both | Skip interactive confirmations (non-TTY safe) |
| `--ai-refine/--no-ai-refine` | both | Attempt single AI correction for failed commands (default on) |
| `--log-dir <path>` | both | Write a persistent JSON log of the guided run to the given directory |

## email-security

Produces:
- Scan summary
- Optional AI short summary (bullet guidance)
- Hardening plan preview (actions with type/category/risk/reason/command_preview)
- Optional guided execution run (when `--run`)

Examples:
```bash
# Basic scan preview
cyberzard email-security --dry-run

# Run plan (still simulated) and print JSON
cyberzard email-security --run --dry-run --json

# Execute only low/medium risk actions for real
cyberzard email-security --run --no-dry-run --max-risk medium --auto-approve
```

JSON shape (abridged):
```jsonc
{
  "scan": { "summary": { "queue_size": 0, "sasl_failures": 12, ... } },
  "plan": { "plan": { "total_actions": 7, "actions": [ {"type": "service_restart", ...} ] } },
  "summary": "AI summary text...",           // present when provider enabled
  "execution": {                            // when --run provided
    "executions": [ { "type": "service_restart", "dry_run": true, "success": true } ],
    "summary": { "total": 7, "executed": 7, "failures": 0 }
  }
}
```

## email-fix

Adds a full remediation **guide** (markdown) with sections:
- Overview
- Detected Issues
- Step-by-Step Recovery
- Security Hardening
- Verification

Examples:
```bash
# Generate guide only (no execution)
cyberzard email-fix --dry-run --no-run

# Guide plus simulated execution
cyberzard email-fix --run --dry-run --max-risk low

# Real execution (review first!)
cyberzard email-fix --run --no-dry-run --max-risk medium --auto-approve --log-dir ./logs
```

Abridged JSON:
```jsonc
{
  "scan": { /* ... */ },
  "plan": { /* ... */ },
  "guide": "# Email Fix & Hardening Guide...",
  "execution": { /* same structure as email-security */ }
}
```

## Guided Execution Safety

Each action passes through safety validation:
- Whitelisted binaries (e.g. systemctl, postconf, ufw, iptables, apt-get, tee, sed, bash, chmod, echo, curl)
- Rejects dangerous paths (`/etc/shadow`, `/etc/passwd`), pipeline downloads (`curl |`), excessive heredocs
- Dry-run marks success without execution
- AI refinement (if enabled) proposes a single-line replacement executed only if also safe

Execution output and return codes are captured to a JSON log when `--log-dir` is provided. The CLI will display the log path, and the run will be recorded into the chat history DB (session `email-troubleshooting`).

## AI Integration

Set environment variables before running:
```bash
export CYBERZARD_MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-...
# or
export CYBERZARD_MODEL_PROVIDER=anthropic
export ANTHROPIC_API_KEY=... 
```
Without keys: static summary / guide provided.

## Verification Loop

After applying actions, re-run:
```bash
cyberzard email-security --json
```
Confirm improvements: reduced queue backlog, TLS hardened, rate limits present, Fail2Ban active, Dovecot mitigations, fewer auth failures.

## Troubleshooting

| Symptom | Cause | Resolution |
|---------|-------|------------|
| All services show `unknown` | systemctl absent / limited perms | Run with sufficient privileges or install systemd tools |
| Fail2Ban inactive after install action | Package install blocked | Manually install fail2ban then re-run command |
| No AI summary/guide | Provider not configured | Export provider + API key env vars |

---

See also: [Commands](./commands), [Configuration](./configuration), [Security](./security)
