# Cyberzard Roadmap

This roadmap formalizes phased evolution of the Cyberzard AI security CLI.

## Phase 1 (Current – Minimal Local Agent Core)
Scope: Ship a safe, offline-capable foundation mirroring core cleanup script intelligence without requiring an external LLM.

Delivered:
1. Heuristic mini reasoner (keyword -> tool plan) – deterministic, auditable.
2. System prompt (professional CyberPanel security engineer persona).
3. Initial tool registry (read_file, scan_server, propose_remediation).
4. IOC / miner indicator scan (files, processes, encrypted extensions subset).
5. Dry‑run remediation plan synthesis (non-destructive action previews).
6. CLI commands (assistant, scan, show-prompt) with JSON output option.
7. Packaging skeleton & structured module layout for future expansion.

Non-goals in Phase 1:
* Full multi-step reflective reasoning.
* External API model calls.
* Destructive remediation execution.
* Persistent memory or transcript storage beyond process.

## Phase 2 (LLM Integration & Guardrails)
Objective: Introduce external model reasoning while preserving strict safety, reliability, and operator trust.

Planned Features:
1. Provider Abstraction Layer
   - Adapters: OpenAI, Anthropic (extensible registry).
   - Retry/backoff, rate-limit smoothing, cost accounting.
2. ReAct Loop Implementation
   - Thought -> Tool -> Observation cycles with step budget & timeouts.
   - Adaptive tool selection using model function calling / JSON schema.
3. Conversation & Memory
   - Short-term: bounded step transcript (trimmable by token budget).
   - Long-term (optional): anonymized scan finding summaries for recurrence correlation.
4. Expanded Tool Set (read-only first)
   - list_directory (allowlisted traversal)
   - grep_text (bounded pattern search with result caps)
   - show_process_tree (structured ps subset)
   - list_cron, list_systemd_units (safe metadata only)
   - yara_scan (if python-yara & rules present; sandboxed & capped)
5. Remediation Execution (opt‑in)
   - Preflight risk scoring & human confirmation.
   - Evidence capture (hash + copy) before deletion / kill.
   - Rollback manifest generation (paths, original metadata).
6. Security Guardrails (see detailed section below).
7. Observability & Audit
   - Structured step log (JSON Lines) with: timestamp, thought, tool, inputs hash, outputs digest.
   - Redaction of secrets (basic heuristic + env allowlist).
8. Performance & Scale
   - Concurrent file scanning (async / thread hybrid with rate caps).
   - Incremental delta scans vs cached last_scan.json.
9. Extensibility
   - Plugin entrypoints for custom scanners & tools (namespace pkg).
10. Documentation & UX
   - Threat model doc.
   - Operator quickstart for incident triage.

## External LLM Integration Guardrails
Purpose: Contain risk of overreach, prompt injection, unintended destructive actions, data exfiltration, and cost overrun.

Categories & Controls:
1. Prompt Hardening
   - System prompt reasserted every turn.
   - User content isolation (no system overwrite; injection detection heuristics: directives like "ignore previous" flagged).
2. Tool Invocation Validation
   - JSON schema validation pre-execution (fail closed on mismatch).
   - Argument sanitation (path normalization, allowlist enforcement, byte/line caps).
   - Rate limiting: max tool calls per session & per minute.
3. Output & Data Controls
   - Token budget & truncation for large file/tool outputs.
   - Secret redaction (regex for API keys, private keys, tokens) prior to model send.
4. Destructive Action Gating
   - Two-phase commit: (a) propose plan (b) explicit user approve with hash of plan.
   - Risk tier thresholds (critical deletions require --force + interactive confirm unless offline batch mode with signed policy file).
5. Sandboxed Execution (future dynamic code tool)
   - AST allowlist (no import *, no exec/eval, no open, no subprocess, no network).
   - Resource limits (cpu time, memory, file descriptors), ephemeral temp dir.
6. Telemetry & Audit
   - Full step trace persisted (optional encryption at rest).
   - Integrity chain: hash(previous_step_hash + current_payload) -> step_hash for tamper evidence.
7. Cost & Quota
   - Per-session token ceiling; early stop with summary if exceeded.
   - Per-provider monthly soft budget warnings.
8. Failure Handling
   - Graceful degradation: fall back to local heuristic when provider unreachable.
   - Circuit breaker after N consecutive provider errors.
9. Privacy / Compliance
   - Configurable redaction policy file.
   - Explicit opt-in for sending file contents (default hashes + metadata only).

## Phase 3 (Beyond)
Exploratory / stretch after Phase 2 stabilization.

Potential Directions:
1. Behavioral anomaly baselines (historical process/user diffing).
2. Lightweight eBPF hooks for runtime suspicious activity snapshots.
3. Multi-host orchestration (agent mesh, central controller).
4. Threat intel feed ingestion (hash / domain / IP enrichment).
5. Automated patch recommendation checklist.
6. SBOM + dependency CVE correlation for panel components.

## Milestone Breakdown
| Milestone | Key Deliverables | Exit Criteria |
|-----------|------------------|---------------|
| M1 (Done) | Phase 1 minimal core | CLI runs local scan & remediation plan |
| M2        | ReAct loop + provider adapters | External model tool calls gated & audited |
| M3        | Expanded tools + remediation exec | Safe, logged destructive actions opt-in |
| M4        | Guardrails hardening + YARA | All guardrail checklist items implemented |
| M5        | Performance & plugin system | Scan latency < target & plugin demo |
| M6        | Phase 2 doc & release | Public tagged release >=0.2.0 |

## Acceptance Criteria Snapshots
Phase 2 considered complete when:
* External model integration passes injection simulation tests.
* All destructive actions require explicit hash-confirmed approval.
* Step logs reproducibly reconstruct session decisions.
* Secret redaction test corpus yields <1% false negatives (target) for included patterns.

## Contribution Guidance
When proposing features, reference which Phase & milestone they align to. Security-impacting changes must include updated threat model notes.

---
For high-level summary see the abridged section in `README.md` – this document remains the authoritative, detailed plan.
