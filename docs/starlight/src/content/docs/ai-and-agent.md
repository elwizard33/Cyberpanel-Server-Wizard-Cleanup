---
title: AI & Agent
---

# AI & Agent

The agent uses a phased architecture:

- Phase 1: Deterministic heuristic tool selection (offline).
- Phase 2: External LLM ReAct loop with guardrails (see Roadmap).

Tools (current): read_file, scan_server, propose_remediation.

Planned expansions: directory listing, grep, process tree, YARA, cron & systemd introspection.

Safety: All destructive actions require explicit user confirmation outside the reasoning loop.
