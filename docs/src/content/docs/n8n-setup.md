---
title: n8n Setup
description: Use Cyberzard to generate and apply an n8n deployment on CyberPanel using Docker
---

This guide shows how to deploy n8n on a CyberPanel server using the `cyberzard n8n-setup` command. The assistant collects your preferences, generates safe, reproducible scripts, and can optionally apply them automatically.

## What it does

- Collects deployment preferences (domain, subdomain, mode, port, resource limits)
- Generates scripts for two modes:
  - Native: n8n + Postgres with OpenLiteSpeed reverse proxy on the server
  - Tunnel: Docker Compose stack (n8n + Postgres) behind a Cloudflare Tunnel
- Writes scripts to disk for review, or applies them directly
- Redacts secrets from JSON summaries and avoids destructive actions

## Requirements

- Docker installed on the server (both modes)
- For Tunnel mode: Cloudflare account; `cloudflared` is installed automatically by the script if missing
- Root privileges are optional; if not root, user-creation steps are skipped

## Quick start

Interactive prompts (recommended on first run):

```bash
cyberzard n8n-setup --interactive --domain example.com
```

Non-interactive, write-only preview (no changes applied):

```bash
cyberzard n8n-setup --domain example.com --subdomain n8n --mode native \
  --write-only --out-dir ./out --overwrite --json-out
```

Apply immediately (native mode):

```bash
cyberzard n8n-setup --domain example.com --subdomain n8n --mode native
```

Apply with Cloudflare Tunnel (compose mode):

```bash
cyberzard n8n-setup --domain example.com --subdomain n8n --mode tunnel
```

The command prints a summary and, when `--out-dir` is provided, writes scripts like:

- `n8n_setup_native.sh` and `n8n_update_native.sh` (native)
- `n8n_setup_tunnel.sh` and `n8n_update_tunnel.sh` (tunnel)

You can inspect and version these scripts before running them.

### Agent-mediated execution, permission gating, and logs

- When applying, Cyberzard asks for confirmation in interactive mode (or proceed automatically with `--auto-approve`).
- Scripts are executed through the AI agent's shell tool when available (with a safe fallback to direct execution).
- An execution log is written next to the script (e.g., `n8n_setup_native.sh.log`) capturing combined output and exit codes.
- A memory entry is recorded in the chat history DB under the session `n8n` summarizing the run (applied/aborted, mode, paths).

## Options reference

- `--domain TEXT` (required): Root domain, e.g. `example.com`
- `--subdomain TEXT` (default: `n8n`)
- `--mode [native|tunnel]` (default: `native`)
- `--port INTEGER` (default: `5678`, binds to localhost)
- `--basic-auth / --no-basic-auth` and `--basic-auth-user TEXT` (password is generated if omitted)
- `--timezone TEXT` (default: `UTC`)
- `--n8n-image TEXT` (default: `n8nio/n8n:latest`)
- `--postgres-image TEXT` (default: `postgres:16`)
- `--resource-cpus TEXT`, `--resource-memory TEXT` (Docker limits)
- `--write-only` and `--out-dir PATH` to generate scripts without applying
- `--overwrite` to allow overwriting existing files in `--out-dir`
- `--interactive/--no-interactive` to require an approval prompt before applying (interactive mode)
- `--auto-approve` to apply without prompting in non-interactive environments
- `--json-out` to print a machine-readable summary

## Notes and safety

- Secrets (DB password and optional Basic Auth password) are generated automatically and redacted from JSON outputs.
- Native mode binds n8n to `127.0.0.1:PORT` and expects OpenLiteSpeed/CyberPanel to terminate TLS and reverse proxy the subdomain.
- Tunnel mode creates a Cloudflare Tunnel and a Docker Compose project in `~/n8n-stack`.
- The scripts are idempotent where possible; repeated runs won’t destroy volumes. Always review scripts in compliance-heavy environments.

## Troubleshooting

- Docker not found: install Docker before applying. You can still generate scripts with `--write-only`.
- Cloudflared auth: run `cloudflared tunnel login` once on the server before first tunnel use.
- SSL issuance: in native mode, ensure the subdomain exists in DNS and that CyberPanel can issue a certificate.

See also: the general [Commands](./commands/) page and the [Roadmap](./roadmap/) for upcoming assistants beyond security.
