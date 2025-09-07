---
title: Configuration
---
# Configuration

Runtime behavior is controlled primarily through environment variables. This page lists all supported variables, their defaults, and effects.

## 1. Environment Variables

| Variable | Default | Description | Notes |
|----------|---------|-------------|-------|
| `CYBERZARD_EVIDENCE_DIR` | `/var/lib/cyberzard/evidence` | Directory where JSON scan snapshots and preserved evidence files are stored. | Must be writable. Created automatically if possible. |
| `CYBERZARD_DRY_RUN` | `true` | If `true`, remediation actions are not executed (safety). | Commands like `remediate` explicitly set actions; currently CLI passes dry-run only if action flags not used. |
| `CYBERZARD_PRESERVE_EVIDENCE` | `false` | If `true`, attempt to copy targeted files before destructive actions. | Can also be provided via `--preserve` flag on `remediate`. |
| `CYBERZARD_FORCE` | `false` | Reserved for future use to bypass safety checks. | Not widely used yet. |
| `CYBERZARD_SEVERITY_FILTER` | _(unset)_ | Limit processing/reporting to minimum severity (info, low, medium, high, critical). | Currently influences model settings context building & can be extended to output filtering. |
| `CYBERZARD_MODEL_PROVIDER` | `none` | Which AI provider to use: `openai`, `anthropic`, or `none`. | Automatically downgraded to `none` if API key missing. |
| `OPENAI_API_KEY` | _(unset)_ | OpenAI key enabling AI summarization / agent. | Required when provider is `openai`. |
| `ANTHROPIC_API_KEY` | _(unset)_ | Anthropic key enabling AI summarization / agent. | Required when provider is `anthropic`. |
| `CYBERZARD_MAX_CONTEXT_BYTES` | `8000` | Approximate max bytes of findings text fed to AI. | Truncation occurs above this. |
| `CYBERZARD_NO_HISTORY` | `false` | If `true`, agent will avoid retaining reasoning transcript beyond immediate response. | Privacy / minimal retention mode. |

## 2. Loading Order & Caching

Settings are read lazily the first time `get_settings()` is invoked and are cached (LRU with size 1). To re-evaluate environment variables within the same Python process you would need to clear the cache (advanced / dev scenario):

```python
from cyberzard.config import CyberzardConfig

config = CyberzardConfig()
get_settings.cache_clear()  # then call get_settings() again
```

## 3. Provider Auto-Disable Logic

If `CYBERZARD_MODEL_PROVIDER` is set to `openai` but `OPENAI_API_KEY` is missing, provider is internally reset to `none`. Same for `anthropic`. This ensures commands like `scan` never hard fail due to optional AI.

## 4. Evidence Directory Layout

When scans run, the latest findings are stored as `last_scan.json` under the evidence directory (through helper functions). Future versions may store timestamped historical files. Ensure the directory is not world-readable if sensitive path metadata is a concern.

Example after a few runs:

```
/var/lib/cyberzard/evidence/
	last_scan.json
	preserved/               # (optional) evidence preservation copies
```

## 5. Severity Filtering (Pluggable)

`CYBERZARD_SEVERITY_FILTER=medium` could be used (future extension) to filter out low/info findings from certain outputs or AI context. Presently it influences advisory context size heuristics.

## 6. Adjusting AI Context Size

Large hosts may produce many findings. If you encounter truncation warnings, raise `CYBERZARD_MAX_CONTEXT_BYTES` cautiously (e.g. 16000). Be aware of provider token limits and cost.

## 7. Temporary Overrides via Shell

Instead of exporting variables permanently:

```bash
CYBERZARD_MODEL_PROVIDER=openai OPENAI_API_KEY=sk-... cyberzard explain --max-tokens 300
```

## 8. Non-Destructive Defaults

All destructive actions (file removal, process kill) require explicit CLI flags (`--delete`, `--kill`). Even if `CYBERZARD_DRY_RUN` is `false`, no destructive remediation occurs unless those flags are present and recommended actions match.

## 9. Future Configuration Sources

Planned: optional YAML config merging (environment > YAML > defaults). For now environment variables are the single authoritative override mechanism.

---

Next: See `commands.md` for detailed CLI usage.
