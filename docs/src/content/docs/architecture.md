---
title: Architecture
description: High-level architecture overview
---

# Architecture

Layers:
1. CLI (Typer)
2. Scanners (process, files, cron, users)
3. Agent core (planning loop)
4. Provider adapter (OpenAI/Anthropic/none)

Data flow: CLI -> scanners -> findings -> (agent/advice) -> output.

