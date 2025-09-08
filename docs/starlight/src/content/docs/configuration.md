---
title: Configuration
---

# Configuration

Environment variables:

| Variable | Purpose |
|----------|---------|
| CYBERZARD_MODEL_PROVIDER | AI provider (openai|anthropic|none) |
| CYBERZARD_DRY_RUN | Force non-destructive operations |
| CYBERZARD_EVIDENCE_DIR | Evidence storage root |
| CYBERZARD_SEVERITY_FILTER | Minimum severity threshold |

Export before running commands:
```bash
export CYBERZARD_MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```
