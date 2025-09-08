---
title: Configuration
description: Configure Cyberzard settings
---

# Configuration

Set environment variables or a future `config.toml` (planned). Environment variables take priority.

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

