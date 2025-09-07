---
title: Security Model
---
# Security Model

Security posture is guided by a conservative principle set aimed at preventing the tool itself from becoming an additional risk while operating on potentially compromised systems.

## 1. Principles

| Principle | Description | Implementation Notes |
|-----------|-------------|----------------------|
| Least Surprise | Commands never perform destructive operations silently. | Separate `scan` vs `remediate` + explicit flags. |
| Fail Safe | Missing AI keys or optional deps degrade gracefully. | Provider auto-disable logic. |
| Minimize Exposure | Limit data sent to external APIs. | Truncated finding summaries, size caps. |
| Auditable Steps | Actions produce structured results. | JSON remediation output includes per-action record. |
| Containment | Restrict file operations to known safe scope. | Allowlist prefixes. |

## 2. Allowlist Path Enforcement

Deletion actions only proceed if the target path resides within allowlisted prefixes (see `ALLOWLIST_PATHS` in `config.py`). This reduces chance of an errant pattern matching sensitive system files outside targeted areas.

Considerations:

- Expand allowlist thoughtfully; overly broad lists reduce protection value.
- Future: per-action pre-flight interactive confirmation (optional mode).

## 3. Dry-Run Defaults

Global configuration defaults maintain a dry-run orientation. Even with `CYBERZARD_DRY_RUN=false`, destruction requires explicit intent through CLI flags. This layered opt-in design mitigates accidental misuse in scripted environments.

## 4. Sandboxed / Restricted Execution

Current agent tool set excludes arbitrary shell execution. Each tool wraps a narrow, deterministic operation (listing processes, reading head+tail of a file). This compartmentalization:

- Prevents LLM from issuing broad system modifications.
- Simplifies validation and logging.

Future: optional seccomp / subprocess isolation for higher-assurance deployments.

## 5. Severity Scoring & Prioritization

Severities are static enumerations mapped from heuristics (file/process patterns, encryption indicators, composite correlations). Exit codes mirror severity maxima to enable CI gating. Rationale:

- Provide quick triage threshold (e.g., treat high+critical as pipeline blockers).
- Encourage addressing higher-risk indicators first while still listing informational context.

Potential future dynamic scoring components:

- Time since modification / process start age.
- Density of related malicious artifacts (composite weighting).
- External threat intelligence lookups (hash reputation).

## 6. Data Handling & Privacy

No persistent transcripts are written by default. Environment variable `CYBERZARD_NO_HISTORY` further minimizes in-memory retention. Evidence preservation copies only explicitly removed files, not arbitrary system logs.

## 7. Supply Chain Considerations

Dependencies are limited and popular (Typer, Rich, Psutil, Pydantic, Requests). Periodic review recommended:

- Pin versions for reproducibility in production images.
- Integrate dependency scanning (e.g., GitHub Dependabot, pip-audit) in CI.

## 8. Threat Model (Abbreviated)

| Threat | Mitigation |
|--------|-----------|
| LLM prompt injection via file content | Minimal raw file ingestion; no arbitrary file dumps. |
| Over-removal due to false positive | Explicit flags + allowlist + incremental workflow recommendation. |
| API key leakage | Keys only read from environment; not echoed. |
| Malicious model output causing command execution | No direct shell tool exposed; action set constrained. |
| Log poisoning | Structured output with minimal interpolation; avoid executing returned strings. |

## 9. Future Hardening Ideas

Planned / potential enhancements:

- Hash & size logging for preserved evidence.
- Append-only remediation ledger with cryptographic hash chain.
- Optional offline mode enforcing `CYBERZARD_MODEL_PROVIDER=none` regardless of env.
- Configurable per-category remediation policy (e.g., auto-kill low-risk miners in sandbox context).
- ML-based anomaly scoring augmentation.

## 10. Operational Guidance

- Run initial scans in read-only contexts when feasible.
- Validate suspicious artifacts manually before large-scale deletion.
- Maintain backups / snapshots (especially for production servers) prior to remediation.
- Regularly rotate API keys used for AI providers.

---

Return to: `ai_and_agent.md` or proceed to architecture & roadmap once generated.
