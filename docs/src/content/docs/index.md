---
title: Introduction
description: Cyberzard is an AI-assisted CLI for CyberPanel — focused on security today, aiming to help with all things CyberPanel tomorrow
---

Welcome to Cyberzard. Today, it helps you secure and triage a CyberPanel server using an AI‑assisted CLI. Our goal is broader: become your general-purpose CyberPanel assistant for setup, operations, and automation — while keeping safety and reviewability front and center.

## What Cyberzard Does
Cyberzard accelerates incident triage by combining deterministic scanners (processes, files, cron, users, SSH keys) with an optional constrained ReAct agent that can summarize and advise without arbitrary shell access. Beyond security, assistants are emerging for everyday operations, like deploying services (see the new n8n setup assistant).

## Feature Highlights
| Area | Capability | Notes |
|------|------------|-------|
| Scanning | Process / file IOC checks | Fast, read‑only collection |
| Remediation | Structured action plans | Human approval first |
| AI Assist | Summaries, prioritization | Provider optional (offline safe) |
| Safety | Tool allowlist, step cap | No raw shell exposed |
| Chat | Interactive, permission‑aware | See [Chat mode](./chat/) |

Next: Read the [Installation](./installation) page, then try the [Chat mode](./chat/). If you want to deploy n8n, check out [n8n Setup](./n8n-setup/).

## Chat quick start

```bash
cyberzard chat
```

Helpful flags:

- `--session <id>` keep separate histories (SQLite-backed)
- `--verify/--no-verify` enable verification of suggested actions
- `--auto-approve` allow safe read-only probes without prompting
- `--max-probes N` cap verification probes (default: 5)

See the full guide: [Chat mode](./chat/)

