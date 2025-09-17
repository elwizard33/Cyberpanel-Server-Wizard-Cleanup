# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [0.1.0] - 2025-09-07
### Added
- Core scanner suite (files, processes, services, cron, users, SSH keys, encrypted files, composite correlation)
- Severity classification and rationale model
- Rich TTY + JSON reporting
- Hardening advice (static + AI enrichment when provider configured)
- AI providers abstraction (OpenAI / Anthropic) with graceful degradation
- ReAct agent loop with secure tool schema (file read/list/search, scan bridge, sandboxed exec)
- Sandboxed execution environment (AST validation + resource limits)
- Remediation planning & execution (remove / kill) with evidence preservation hook
- Configuration system via environment variables
- Minimal test suite (scanners orchestration, remediation dry run)
- Packaging metadata, dev extras, LICENSE

### Security
- Path allowlist enforcement for destructive operations
- Dry-run default safety

## [Unreleased]
### Planned
- Extended composite heuristics
- Delta scan caching
- YARA integration (optional)

## [0.1.5] - 2025-09-13
### Added
- Email stack scanner (`scan_email_system`) capturing services, queue backlog, SASL auth failures, DNS mismatch, RainLoop config, Fail2Ban, TLS posture, rate limits, Dovecot hardening, firewall, log tail
- Hardening planner (`propose_email_hardening`) with conditional actions (service restart, rate limiting, Fail2Ban, TLS, Dovecot, firewall, monitoring)
- AI email provider (`summarize_email_security`, `generate_email_fix_guide`, `justify_email_action`, `refine_email_action`) with OpenAI / Anthropic + deterministic fallback
- Guided execution engine (`run_guided`) with safety whitelist, dry-run, refinement, structured results
- CLI commands: `email-security` (scan + plan + optional guided exec) and `email-fix` (full remediation guide + optional exec)
### UI
- Rich render helpers: email security summary, execution progress, markdown guide
### Docs
- README feature row & usage examples for new email commands
- New docs pages: `email-security` reference and removal of stray duplicate `email_commands.md`
### Safety
- Command allowlist & heuristics (reject dangerous paths, pipeline downloads, excessive heredocs)
### Misc
- Top-level exports for email scan/plan

## [0.1.4] - 2025-09-12
### Added
- New `n8n-setup` command to guide n8n deployment on CyberPanel
	- Generates native (OpenLiteSpeed reverse-proxy) or tunnel (docker compose + cloudflared) scripts
	- Optional apply step with idempotent execution and Rich-styled feedback
	- Safe handling of secrets (redacted in JSON output)
### Docs
- New "n8n Setup" page with quick start, options, and troubleshooting
- Sidebar TOC updated to include n8n Setup
- Introduction updated to reflect long-term goal: beyond security toward a general-purpose CyberPanel assistant

## [1.0.1] - 2025-09-17
### Added
- LangChain tools agent powering `cyberzard chat` with safe tool calls (run, debug, and complete shell commands via constrained tools)
- SQLite-backed conversation history with per-session isolation (`--session <id>`)
- In-chat commands: `/history [n]`, `/clear`, `/sessions`, `/switch <id>`
- TUI scaffolding command (`tui`) wiring ready for future UI (experimental)
### Docs
- Chat guide updated with session support and in-chat commands
- Commands reference updated (`--session` flag, in-chat commands)
- Introduction now includes a Chat quick start
- Security and Configuration pages note local data storage in `cyberzard_agent.sqlite`
### Developer
- VS Code settings to align interpreter with Anaconda for consistent imports
