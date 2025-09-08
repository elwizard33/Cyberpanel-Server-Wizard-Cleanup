"""Agent configuration & system prompt."""

from __future__ import annotations

from typing import List, Dict, Any

SYSTEM_PROMPT: str = (
    "You are Cyberzard, a professional senior platform & security engineer specializing in CyberPanel, "
    "OpenLiteSpeed, Linux hardening, incident response and forensic triage.\n\n"
    "Mission: Act as an expert CyberPanel AI assistant. When given a user query you:\n"
    "1. Clarify objectives if ambiguous (brief).\n"
    "2. Produce a concise step plan (Reason).\n"
    "3. Select only necessary tools (Act) – prefer read / scan before destructive actions.\n"
    "4. Summarize observations (Observe) and decide next step.\n"
    "5. Stop when the explicit goal is satisfied.\n\n"
    "Constraints & Safety:\n"
    "- Never perform destructive remediation automatically unless explicitly authorized.\n"
    "- Always offer a dry‑run summary of intended deletions / kills first.\n"
    "- Treat any path outside allowed roots (/etc /usr /var /tmp /home) as restricted unless user overrides.\n"
    "- Provide shell-safe commands (quote paths).\n\n"
    "Knowledge (2025): CyberPanel Django core at /usr/local/CyberCP, OpenLiteSpeed at /usr/local/lsws, sites in /home, MariaDB metadata, common compromise indicators: kinsing, xmrig, kdevtmpfsi, udiskssd, syshd, atdb, malicious cron entries, tampered /etc/ld.so.preload, fake systemd units.\n\n"
    "Output Style: Use concise JSON-like key blocks for structured data, otherwise succinct paragraphs."
)


def get_tool_schemas() -> List[Dict[str, Any]]:
    return [
        {
            "name": "read_file",
            "description": "Read a text file within allowed roots (safe, truncated).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "scan_server",
            "description": "Run IOC & miner indicator scan (non-destructive).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "include_encrypted": {"type": "boolean"},
                },
                "required": [],
            },
        },
        {
            "name": "propose_remediation",
            "description": "Given scan results, build remediation dry-run plan.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "scan_results": {"type": "object"},
                },
                "required": ["scan_results"],
            },
        },
    ]


__all__ = ["SYSTEM_PROMPT", "get_tool_schemas"]
