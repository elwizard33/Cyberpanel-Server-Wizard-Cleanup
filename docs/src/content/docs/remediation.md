---
title: Remediation
description: Remediation flows and automation
---

# Remediation

Cyberzard proposes a dry‑run remediation plan based on scan results. It never executes destructive changes automatically.

Plan entries include:
- `type`, `target`, optional `pattern`
- `reason` and `risk`
- `command_preview` (shell-quoted)

Action categories covered:
- Remove known IOC files (preview `rm -f`)
- Kill suspicious process groups (preview `pkill -f`)
- Stop/disable suspicious systemd units and remove unit files (previews)
- Remove unexpected `/etc/ld.so.preload` (preview)
- Review `authorized_keys` files (previews `ls` and `sed -n`)

Always review the plan before executing any commands manually.


Remediation workflow:
1. Gather findings (scan).
2. Rank by severity & exploitability.
3. Draft ordered plan (advise or agent output).
4. Manually approve & execute outside agent.

Planned: structured JSON plan export.

