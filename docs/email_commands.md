# Email Commands

Two new commands provide CyberPanel email stack assessment and guided remediation.

## Overview

| Command | Purpose | Default Mode |
|---------|---------|--------------|
| `email-security` | Scan email services, produce hardening plan, optional AI summary, optional guided execution | Dry‑run preview |
| `email-fix` | Generate full markdown remediation guide (AI when enabled) + optional guided execution | Dry‑run + guide |

Both commands are safe by default:
- No changes executed unless `--run` is set (and even then, still dry‑run unless `--no-dry-run`)
- Command safety validation (allow‑listed binaries, heuristics) rejects unsafe commands
- AI is optional; falls back to deterministic static text

## Options

Common flags:
- `--domain <root>`: Enables DNS mismatch heuristic (checks `mail.<domain>` vs public IP)
- `--json`: Emit structured JSON instead of rich UI
- `--max-risk {low|medium|high}`: Filter actions by risk threshold
- `--auto-approve`: Skip interactive confirmation (non‑interactive environments)
- `--dry-run / --no-dry-run`: Simulate (default) vs actually execute commands
- `--run`: Trigger guided execution after planning
- `--ai-refine/--no-ai-refine`: Attempt single AI refinement on failed actions (default on)

`email-fix` adds:
- AI generated markdown remediation guide (sections: Overview, Detected Issues, Step‑by‑Step, Hardening, Verification)

## Guided Execution Model

Execution pipeline when `--run` provided:
1. Planner builds ordered actions (service restart, rate limiting, TLS, Fail2Ban, etc.)
2. Each action validated by `is_command_safe`
3. Dry‑run: mark success without running (fast preview)
4. Real run (`--no-dry-run`): shell execution with timeout
5. On failure and AI enabled: attempt a single safe refinement
6. Structured result appended; optional early stop disabled (fail_fast False)
7. Summary aggregates success/failed/skipped/unsafe/refined

## JSON Shape (email-security example)
```jsonc
{
  "scan": { "summary": { "queue_size": 0, "sasl_failures": 3, "tls_hardened": false, ... } },
  "plan": { "plan": { "total_actions": 7, "actions": [ {"type": "service_restart", ... } ] } },
  "summary": "Optional AI summary text...",          // email-security only
  "execution": {                                 // present when --run
    "executions": [
      {
        "type": "service_restart",
        "risk": "low",
        "command_preview": "systemctl restart postfix",
        "dry_run": true,
        "success": true
      }
    ],
    "summary": {"total": 7, "executed": 7, "failures": 0, ... }
  }
}
```

`email-fix` replaces `summary` with `guide` containing the markdown remediation guide.

## Rich UI

When stdout is a TTY and `NO_COLOR` is not set:
- `render_email_security` shows core posture metrics + hardening preview
- `render_email_fix` renders markdown guide
- `render_email_execution_progress` summarizes results

Fallback: plain JSON or key/value prints when Rich/import errors occur.

## Safety Guardrails

- Whitelisted binaries: `systemctl`, `postqueue`, `postsuper`, `postconf`, `ufw`, `iptables`, `apt-get`, `tee`, `sed`, `bash`, `chmod`, `echo`, `curl`
- Rejects: unknown binaries, dangerous paths (`/etc/shadow`), pipeline downloads (`curl |`), excessive heredocs
- AI refinement output must also pass safety validation before execution

## Example Workflows

Preview only:
```bash
cyberzard email-security --dry-run
```

Generate guide and preview execution:
```bash
cyberzard email-fix --run --dry-run --max-risk medium
```

Apply low risk items (after reviewing):
```bash
cyberzard email-security --run --no-dry-run --max-risk low --auto-approve
```

Full guide + real execution (medium or lower):
```bash
cyberzard email-fix --run --no-dry-run --max-risk medium --auto-approve
```

## AI Enablement

Set provider environment variable before running:
```bash
export CYBERZARD_MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-...
# or
export CYBERZARD_MODEL_PROVIDER=anthropic
export ANTHROPIC_API_KEY=... 
```

Without keys configured the commands gracefully fall back to static deterministic guidance.

## Verification

Re-run `email-security --json` to confirm improvements after applying actions (queue backlog reduced, TLS hardened, rate limiting active, Fail2Ban present, etc.).

---

For questions open an issue with `email` label.
