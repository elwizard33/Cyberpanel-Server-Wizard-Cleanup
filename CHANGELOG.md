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
