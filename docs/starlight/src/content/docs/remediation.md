---
title: Remediation
---

# Remediation

Workflow:
1. Run a scan.
2. Review proposed remediation plan (dry-run JSON).
3. Approve actions (delete/kill) with evidence preservation flags.

Principles:
- Evidence first (hash + copy before delete).
- Idempotent: running again should not re-delete.
- Explicit scope via allowlisted paths.
