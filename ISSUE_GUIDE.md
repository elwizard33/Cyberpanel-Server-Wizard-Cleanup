# Cyberzard Issue Reporting Guide

High-quality issues help us fix and improve Cyberzard quickly. This guide defines the required structure and standards. Issues that do not meet the minimum fields may be closed or asked to revise.

## 🚦 Choose the Right Channel
| Type | Where to Report | Notes |
|------|-----------------|-------|
| Bug / False Positive | GitHub Issue | Follow template below |
| Feature Request | GitHub Issue | Focus on the problem, not implementation |
| Security Vulnerability | Email `security@elwizard.net` (PGP preferred) | Do **not** open a public issue first |
| Question / Clarification | GitHub Issue (Question label) | Link to relevant docs section |

## ✅ Minimum Required Fields (All Issues)
```
Title: < concise, problem-focused summary >
Type: bug | false-positive | feature | performance | security | question
Version: (git commit SHA or branch; run: git rev-parse HEAD)
Environment:
  OS: (e.g. Ubuntu 22.04)
  Python: (e.g. 3.11.6)
  Install Mode: editable | venv | container | other
  Shell: (e.g. bash, zsh)
  Resources: (CPU count, RAM if perf issue)
Command Executed:
  <exact command including flags>
Observed Behavior:
  <what happened>
Expected Behavior:
  <what you expected instead>
Artifacts / Evidence:
  - Logs (run with CYBERZARD_DEBUG=1 if reproducible)
  - Redacted snippets of output JSON (if applicable)
  - Hash prefixes (never share full sensitive file contents unless harmless)
Reproduction Steps:
  1. Step one
  2. Step two
  3. ...
Severity Assessment:
  low | medium | high | critical (justify briefly)
Additional Context:
  <optional assumptions, comparisons, links>
```

## 🐞 Bug Reports
Add these extras:
- Frequency: always / intermittent / one-off
- First Seen: (date or commit)
- Workaround: (if any)
- Related Modules: scanners / remediation / agent / reporting / evidence / config

## 🎯 False Positives / Missed Detections
Provide:
- File path pattern(s) or process names (redact sensitive segments)
- Why you believe it is benign/malicious
- Attach (if safe) a cryptographic hash:
  - `sha256sum <file>` output (first 12 chars ok)
- Classification suggestion (e.g. downgrade severity / add allowlist heuristic)

## 🚀 Performance Issues
Include:
- Dataset size (file count, total MB)
- Time spent (wall clock) + which phase(s)
- CPU / I/O saturation indicators (e.g. `top`, `iostat` snippets)
- Proposed optimization ideas (optional)

## 🔐 Security Reports
Never publicly disclose until coordinated. Email:
```
security@elwizard.net
```
If encryption needed, request a PGP key via that address first. Provide proof-of-concept, impact description, affected components, and mitigation ideas if possible.

## 💡 Feature Requests
Focus on the problem, not the implementation detail.
Template additions:
- Problem Statement: <what pain or gap>
- Current Workaround: <if any>
- Desired Outcome: <what success looks like>
- Suggested Acceptance Test: <observable result>
- Optional: Rough risk / complexity guess

## 🧪 Reproductions & Determinism
Strive for the smallest reproducible example. If reproduction depends on environmental artifacts (e.g. specific suspicious files), describe synthetic stand-ins you used.

## 🏷️ Labels (Applied by Maintainers)
- `bug`, `false-positive`, `feature`, `perf`, `security`, `question`
- `needs-repro`, `needs-info`, `accepted`, `duplicate`, `wontfix`

## 🗂️ Triage Process (What to Expect)
1. Initial validation (may request more info)
2. Severity & scope tagging
3. Reproduction attempt / automated test drafting
4. Fix scheduling (milestone assignment)
5. Patch review & merge
6. Regression test added (where practical)

## 🔄 After a Fix
Please:
- Pull latest main
- Re-run the original reproduction
- Confirm closure with: `Resolved in <commit SHA>`

## 🧭 Quality Checklist Before Submitting
- [ ] All required fields present
- [ ] Command pasted exactly
- [ ] Sensitive data redacted
- [ ] Reproduction deterministic or frequency specified
- [ ] Logs attached (if helpful) with `CYBERZARD_DEBUG=1`

## 🙏 Thanks
Thoughtful, complete reports dramatically shorten turnaround time and improve software quality for everyone. Thank you for investing the extra few minutes to make an excellent issue.
