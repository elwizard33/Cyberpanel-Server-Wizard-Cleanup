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
- `--verify/--no-verify` run AI/heuristic verification to reduce false positives (default: verify)
- `--auto-approve` auto-consent to safe, read-only probes (no prompts in TTY when set)
- `--max-probes N` limit total verification probes (default: 5)

Examples:

```bash
cyberzard scan
cyberzard scan --json --include-encrypted
cyberzard scan --no-verify
cyberzard scan --auto-approve --max-probes 8
```

JSON output shape (abridged):

```jsonc
{
	"scan": { /* scan results */ },
	"remediation": { /* proposed plan (preview only) */ },
	"verification": { // present when --verify
		"success": true,
		"verified_plan": { "total_actions": 2, "actions": [/* kept actions */] },
		"dropped": [ { "action": { /* ... */ }, "reason": "..." } ],
		"downgraded": [ { "action": { /* ... */ }, "reason": "..." } ],
		"meta": { "probe_count": 3, "probes_skipped": 0, "consent_log": [/* categories + approvals */] }
	}
}
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
| `scan` | Run all scanners, list findings | `--json`, `--verify/--no-verify`, `--auto-approve`, `--max-probes` |
| `advise` | Generate concise advice from scan | `--json`, `--include-encrypted` |
| `agent` | Minimal ReAct loop over safe tools | `--steps N`, `--show-plan` |
| `show-prompt` | Print the agent system prompt | — |
| `version` | Show version | — |

