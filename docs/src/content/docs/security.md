---
title: Security
description: Security model and threat considerations
---

# Security

Principles:
| Principle | Detail |
|-----------|--------|
| Least Privilege | Read-only scanning; no mutation tools yet |
| Explicit Allowlist | Only curated tools callable |
| Bounded Resources | Step & context limits prevent runaway usage |
| Provider Optional | Offline / air‑gapped safe defaults |

## Data storage

- Chat transcripts are stored locally in a SQLite file (`cyberzard_agent.sqlite`) alongside the CLI. Data stays on your machine.
- Use sessions to separate contexts (e.g., `--session prod`, `--session staging`). You can clear a session in chat with `/clear`.

