---
title: Remediation Workflow
---
# Remediation Workflow

The remediation subsystem applies a constrained, auditable subset of actions derived from scan findings. It is intentionally conservative to avoid collateral damage.

## 1. Scan to Action Mapping

Each finding may carry a `recommended_action` (enum) such as `remove`, `kill`, `investigate`, etc. Only `remove` (file unlink) and `kill` (process termination) are currently actionable by the CLI.

Mapping logic (simplified):

| Finding Category | Example Indicator | Recommended Action | Action Condition |
|------------------|-------------------|--------------------|------------------|
| file | Known malicious path present | remove | Path within allowlist & user passed `--delete` |
| process | Suspicious miner process | kill | PID available & user passed `--kill` |
| composite | Aggregated correlation | investigate | Not directly actionable yet |

## 2. Dry-Run Philosophy

The global settings default to non-destructive posture. Even if `CYBERZARD_DRY_RUN=false`, the CLI requires explicit flags (`--delete` or `--kill`) to execute those specific action types. No implicit remediation occurs during a plain `scan`.

## 3. Evidence Preservation

If `--preserve` is set, file removal actions first attempt to copy the target file into the evidence directory (`<evidence>/preserved/<finding_id>/`). Preservation failures are non-fatal; the action proceeds only if policy allows.

Benefits:

- Enables later forensic review.
- Mitigates risk of losing critical trace data.

## 4. Plan Generation Flow

1. Perform a new scan (ensures freshness).
2. Optionally filter by a specific `--finding` id.
3. Iterate findings, selecting those whose `recommended_action` matches provided capability flags.
4. Build `RemediationPlan(actions=[...])` summarizing intended operations.
5. Execute plan via executor which returns structured `RemediationResult` objects.

Output JSON example:

```json
{
	"summary": "Applying 2 actions",
	"results": [
		{"finding_id":"abc","action":"remove","success":true,"message":"removed","changed":true},
		{"finding_id":"def","action":"kill","success":false,"message":"process not found","changed":false}
	]
}
```

## 5. remove / kill Semantics

| Action | Operation | Success Criteria | Notes |
|--------|-----------|------------------|-------|
| remove | `Path.unlink()` | File no longer exists | Follows allowlist check & optional evidence copy |
| kill | Send SIGTERM (graceful) | Process gone / signal sent | Future enhancement: escalate to SIGKILL after timeout |

## 6. Safety Flags & Allowlist

Allowlist restricts deletion to specific top-level prefixes (see `configuration.md`). This reduces risk of arbitrary destructive suggestions if detection logic misfires.

Flags recap:

- `--delete`: authorizes file removals
- `--kill`: authorizes process termination
- `--preserve`: enable evidence copying
- `--finding <id>`: scope to one target (safer for incremental cleanup)

## 7. Failure Handling

Failures (permissions, missing file/PID) are captured per action and surfaced in `message`. Execution continues for other actions; there is no all-or-nothing rollback.

## 8. Idempotency

Repeated runs after successful removal return no matching findings (action list shrinks naturally). This encourages iterative, low-risk remediation cycles.

## 9. Auditing & Traceability

Storing remediation results JSON (future enhancement) would enable tamper‑evident logs. Currently users can redirect output:

```bash
cyberzard remediate --delete --kill --preserve > remediation_$(date +%s).json
```

## 10. Future Expansion

Planned action types:

- `disable` systemd service (mask / disable + preserve unit file)
- `quarantine` move file to isolated directory instead of delete
- `archive` compress evidence bundle (file + metadata)
- `network_block` (integration with host firewall rules)

## 11. Recommended Operational Pattern

1. Run `scan` and review findings.
2. Start with a single target: `remediate --finding <id> --delete --preserve`.
3. Validate system stability.
4. Broaden scope with combined flags.
5. Re-run `scan` to confirm delta.

---

Next: Review `security.md` for overarching safety design.
