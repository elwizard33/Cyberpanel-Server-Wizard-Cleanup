---
title: (Deprecated) FAQ
sidebar: false
---

This legacy file is deprecated. Current content lives at /faq.

---
title: (Legacy) FAQ
---
## Legacy Documentation Notice

Moved to Starlight at `/faq`.

Original content removed.

## 1. Why another CyberPanel cleanup / scanner tool?

Existing bash scripts were effective but monolithic and harder to extend. A modular Python architecture enables safer remediation, richer reporting, optional AI assistance, and structured outputs for automation.

## 2. How are severities determined?

Static heuristics map indicators (known malicious file paths, suspicious process names, encryption artifacts, composite correlation) to a severity enum: `info < low < medium < high < critical`. Exit codes reflect highest severity for CI gating.

## 3. What happens if AI provider keys are missing?

The provider auto-downgrades to `none`. Commands still run; `advise` returns static suggestions, `explain` uses a deterministic summary, `agent` produces a single non-tool answer. No errors should occur.

## 4. Is remediation safe to run on production?

Remediation is intentionally constrained: only explicit `--delete` / `--kill` actions operate, with allowlisted path prefixes and optional evidence preservation. Still, prefer staging or snapshot testing before broad production use.

## 5. How do I add a new scanner?

Create a module in `cyberzard/scanners/` returning a list of `Finding` objects, then register it in the orchestrator (scanner runner list). Keep execution fast and side-effect free.

## 6. How do I export findings as JSON?

Use `cp-ai-wizard scan --json > scan.json`. The file includes a `findings` array and `delta` section if a prior run exists.

## 7. What does a composite finding mean?

Composite findings aggregate related signals (e.g., suspicious process + cron token + file path). They highlight multi-indicator clusters that raise confidence and priority.

## 8. Where is evidence stored?

Default directory: `/var/lib/cp-ai-wizard/evidence`. It holds `last_scan.json` and optionally `preserved/<finding_id>/` subdirectories when `--preserve` is used with destructive actions.

## 9. How can I suppress or filter noisy findings?

Currently you can post-process JSON output or set `CYBERZARD_SEVERITY_FILTER` (future expansion may provide ignore patterns or policy YAML). Contributions welcome.

## 10. What does a high or critical severity imply?

`high` usually denotes strong evidence of malicious tooling or active miner components. `critical` would be reserved for catastrophic indicators (ransomware spread, widespread encryption) and may trigger exit code 3.

## 11. Why does the tool re-scan before remediation?

Ensures actions correspond to current state, reducing race conditions where files/processes changed between earlier scan and remediation invocation.

## 12. How is delta (added/removed) computed?

On each scan, the tool loads `last_scan.json` (if present) and compares finding IDs to the new list, reporting added / removed counts (and lists in JSON). IDs are stable for each finding instance.

## 13. How do I get an AI summary safely offline?

Set `CYBERZARD_MODEL_PROVIDER=none` explicitly. The `explain` command will produce non-network summary while guaranteeing no external API invocation.

## 14. Can I run this inside a container?

Yes, provided the container has access (bind mounts) to the host paths you wish to scan. A future roadmap item includes a hardened ephemeral container template.

## 15. What about YARA rules?

Currently a stub exists; if `python-yara` is installed and rules directory is configured (env var planned), rules will be loaded. Until then the module safely skips.

## 16. How are API costs controlled?

Context bytes limit (`CYBERZARD_MAX_CONTEXT_BYTES`) and step caps for agent keep token usage bounded. No secrets or large file contents are transmitted by default.

## 17. How can I contribute?

Open a GitHub issue with proposal details (problem, rationale, rough design). For code: fork, create feature branch, add tests if logic changes, and submit PR referencing roadmap item or issue.

---

Return to: [Commands](commands.md) | [Architecture](architecture.md) | [Security](security.md)
