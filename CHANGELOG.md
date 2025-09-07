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
- Extended composite heuristics
- Delta scan caching
- YARA integration (optional)
