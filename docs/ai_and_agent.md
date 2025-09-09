---
title: (Deprecated) AI & Agent
sidebar: false
---

This legacy placeholder file remains only to avoid broken inbound links.

All current content moved to /ai-and-agent.

Deprecated on flattening migration.

Current implementation: purely static rules map categories & severities to remediation suggestions. The design anticipates provider-based expansion where an LLM could refine ordering and add contextual mitigations (e.g., patch level checks). Future enhancement: pass top N findings plus environment constraints (severity filter, counts) to produce prioritized, cost-effective action steps.

## 4. Explain Command Flow

1. Run scanners to collect findings.
2. Build compact context lines: `id severity category message` (truncated list for safety/cost control).
3. Provide a fixed user query requesting plain-language summary + prioritized next steps.
4. Call provider (if available) with minimal system prompt reused from agent skeleton.
5. Output final text (or fallback summary in degraded mode).

Context minimization reduces risk of accidental sensitive data leakage and token cost.

## 5. ReAct Agent Loop Lifecycle

High-level steps executed by `agent` command when provider operational:

1. Initialize system prompt (security disclaimers + available tool schemas).
2. Accept user objective (query argument).
3. Iterate up to `--steps` times:
	- Model proposes an action (tool name + arguments) OR a final answer.
	- If tool invocation: framework validates tool name & schema, executes safely.
	- Tool result appended to transcript (trimmed if large) and fed back to model.
4. On final answer or step exhaustion, produce output JSON (if `--json`) or final text.

Failure Handling:

- Unknown tool -> model reminded of available tools.
- Tool execution error -> error message is included in next context turn, allowing graceful recovery or fallback answer.

## 6. Tool Schema Summary

Representative internal tools (subject to evolution):

| Tool | Purpose | Key Arguments | Notes |
|------|---------|---------------|-------|
| `scan_processes` | Enumerate processes matching patterns | none | Backed by psutil filters. |
| `scan_files` | Check IOC file paths existence | none | Light file existence probing. |
| `read_file_snippet` | Return head + tail of a file | `path`, `max_bytes` | Enforces size cap. |
| `list_cron_entries` | Show suspicious cron lines | none | Parsed from common cron locations. |

Schema exposure: the agent system prompt includes JSON-like mini spec per tool (name, description, argument fields). The model is instructed to output structured tool call instructions; the framework parses/validates them strictly.

## 7. Prompt Safety Considerations

Safeguards implemented / planned:

- Content minimization: Only hashed / truncated snippets for large files (future enhancement) to avoid exfiltration of secrets.
- Strict tool allowlist: No arbitrary shell execution exposed to model.
- Max steps cap: Prevents runaway loops and cost explosion.
- Context size limit (`CYBERZARD_MAX_CONTEXT_BYTES`): Hard ceiling on bytes passed to provider.
- Non-deterministic disclaimers: Summaries avoid giving definitive forensic conclusions; they propose next steps.

## 8. Privacy & Data Handling

No persistent conversation history is stored unless future feature toggles are added. Setting `CYBERZARD_NO_HISTORY=true` can further reduce retention (agent refrains from archiving transcripts beyond ephemeral in-memory loop).

## 9. Extending Providers (Planned)

To add a provider in the future:

1. Implement a `call_model(provider_id, messages, **opts)` function returning structured JSON.
2. Register in provider dispatch map.
3. Document required environment variable names & model defaults.

## 10. Limitations

- No fine-grained token usage metrics surfaced yet.
- Agent toolset intentionally narrow to reduce attack surface.
- Explain/advise contexts exclude file contents (design principle: metadata over raw content initially).

---

Next: See `remediation.md` for applying actions or `security.md` for protective design rationale.
