---
title: (Deprecated) Roadmap
sidebar: false
---

This legacy file is deprecated. Current content lives at /roadmap.

---
title: (Legacy) Project Roadmap
---
## Legacy Documentation Notice

Moved to Starlight at `/roadmap`.

Original content removed.

## 1. Near Term (0.1.x → 0.2.0)

Focus: Stability, documentation completeness, foundational extensibility.

- Complete documentation site (Astro + GitHub Pages deployment).
- Add automated command reference generation script.
- Introduce basic unit tests coverage for each scanner.
- YARA integration (optional) with sample safe rules set.
- Add `disable` remediation action for benign service disabling (mask systemd units).
- Enhanced JSON schema version field for findings.

Success Criteria:

- >80% of users can install + run scan + remediate with docs alone.
- CI pipeline green across Python 3.10 / 3.11.

## 2. Mid Term (0.3.x)

Focus: Intelligence enrichment & policy.

- AI advice prioritization weighting (cost / severity / prevalence).
- Configurable policy file (YAML) allowing custom IOC injection.
- Historical scan archive rotation (timestamped snapshots).
- HTML / Markdown report export with severity summary.
- Optional offline mode enforcement flag.
- Tool registry introspection command (`cyberzard tools list`).

Success Criteria:

- Policy driven scanning adopted in >1 external environment.
- Reduced false positives through composite correlation refinements.

## 3. Longer Term / Stretch (0.4.x+)

Focus: Scale, depth, and forensic augmentation.

- Containerized distribution + ephemeral sandbox runner.
- Live monitoring mode with periodic diff emission.
- Threat intelligence enrichment (hash / domain reputation lookups with caching).
- Quarantine & archive remediation actions (zip evidence bundle, relocate file).
- Pluggable scoring model (weight adjustments via config file).
- Multi-host orchestrator (aggregate reports across fleet). 
- Optional web dashboard (read-only) for historical deltas.

## 4. Architectural Enhancements (Ongoing)

- Introduce plugin discovery via entry points for scanners & tools.
- Structured logging (JSON) with correlation IDs per command invocation.
- Async execution path for IO-bound scanners.

## 5. Security Hardening Milestones

- Evidence integrity hashing (SHA256 per preserved file) + manifest.
- Append-only remediation ledger with chain-of-hash verification.
- Secret redaction passes over AI-bound context.

## 6. Release Cadence

Target: minor updates every 4–6 weeks; patch releases as needed for fixes. Semantic-ish versioning with additive feature gating. CHANGELOG maintained per release.

## 7. Community & Contribution Goals

- Issue templates for scanner proposals & false-positive reports.
- Security disclosure guidelines document.
- Contribution guide (coding style, test expectations, commit conventions).

---

Return to: `architecture.md` or explore FAQ once populated.
