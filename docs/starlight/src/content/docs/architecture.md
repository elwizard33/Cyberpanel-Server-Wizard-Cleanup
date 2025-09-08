---
title: Architecture
---

# Architecture

Layers:
1. CLI (Typer)
2. Agent Engine (reasoner + tool registry)
3. Scanners (IOC detectors)
4. Remediation planner (dry-run)
5. Future: Provider adapters & guardrails layer

Data Flow: scan -> findings -> plan -> (optional) AI explanation -> approved actions.
