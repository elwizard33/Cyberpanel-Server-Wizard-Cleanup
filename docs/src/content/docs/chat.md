---
title: Chat mode
description: Interactive, permission-aware chat for CyberPanel anomaly hunting
---

# Chat mode

Cyberzard’s chat mode gives you an interactive, on-mission assistant focused on CyberPanel anomaly detection. It uses a safe, permission-gated set of tools and a readable Rich UI.

## What it does

- Stays focused on CyberPanel security tasks
- Runs safe, read-only checks with your explicit approval
- Summarizes results and shows a remediation preview
- Optionally verifies suggested actions with bounded, consented probes

## Start chat

```bash
cyberzard chat
```

Helpful flags:

- `--verify/--no-verify`: enable AI/heuristic verification of actions (default: verify)
- `--auto-approve`: auto-consent to safe, read-only probes (no prompts)
- `--max-probes N`: cap total verification probes (default: 5)

Examples:

```bash
cyberzard chat --no-verify
cyberzard chat --auto-approve --max-probes 8
```

## In-chat commands

- `scan` — run a quick IOC scan (files, processes, cron, systemd, users, keys)
- `plan` — show a remediation plan preview (optionally verified)
- `read /path` — read a file preview (permission-gated, read-only)
- `help` — quick tips
- `quit` — exit chat

## Permissions & safety

When chat needs to use a tool (e.g., scan, read file, limited probes), it asks for permission. You can allow once or “remember” the choice for the session.

- Tools are read-only; there’s no raw shell access
- Verification probes are grouped by category (e.g., `file`, `systemd`, `ps`)
- Probes are bounded by `--max-probes` and require consent
- Non-interactive terminals or `NO_COLOR=1` skip the Rich UI and default to deny

## Providers (optional)

Chat works offline. If you set a provider, advice summaries may be AI‑enriched.

```bash
export CYBERZARD_MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-...
cyberzard chat
```

Supported: `none` (default), `openai`, `anthropic`.

## Troubleshooting

- “Chat mode is best used in an interactive terminal (TTY).” — Run in a real TTY; don’t pipe/redirect output.
- No prompts? You used `--auto-approve` or your terminal isn’t interactive.
- Minimal UI? `NO_COLOR=1` disables Rich styling.
