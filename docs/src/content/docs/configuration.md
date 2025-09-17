---
title: Configuration
description: Configure Cyberzard settings
---

# Configuration

Set environment variables or a future `config.toml` (planned). Precedence: CLI flags > environment.

| Variable | Purpose | Default |
|----------|---------|---------|
| `CYBERZARD_MODEL_PROVIDER` | `openai`, `anthropic`, `none` | `none` |
| `CYBERZARD_MAX_CONTEXT_BYTES` | Upper bound for model context payload | 20000 |
| `CYBERZARD_NO_HISTORY` | Disable transcript retention | unset |

Example minimal AI setup:
```bash
export CYBERZARD_MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

Or per-invocation without changing your shell environment:
```bash
cyberzard --provider anthropic advise
```

## Data storage

- Chat history is persisted to `cyberzard_agent.sqlite` in the project directory.
- Use `cyberzard chat --session <id>` to segment conversations (each session has its own history).
- Clear the current session during chat with `/clear`.

