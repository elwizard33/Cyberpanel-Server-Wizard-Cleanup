"""ReAct system prompt & tool schema assembly utilities."""
from __future__ import annotations

from typing import List, Dict, Any

from cyberzard.tools.registry import get_schema
import cyberzard.tools  # noqa: F401

SAFETY_PHRASE = "Never perform destructive actions without explicit confirmation"

BASE_SYSTEM_PROMPT = f"""
You are the CyberPanel AI Wizard.

Objectives:
- Investigate server security findings and explain reasoning step-by-step.
- Use tools to gather evidence before suggesting remediation.
- {SAFETY_PHRASE}.

Guidelines:
1. Request at most one tool per turn.
2. Prefer minimal data (only what you need).
3. If you have enough info, output a concise final answer summarizing findings and next steps.
4. For remediation, recommend a plan rather than executing unless explicitly instructed.
""".strip()


def build_system_prompt(extra: str | None = None) -> str:
    if extra:
        return BASE_SYSTEM_PROMPT + "\n" + extra.strip()
    return BASE_SYSTEM_PROMPT


def tool_schema() -> List[Dict[str, Any]]:
    return get_schema()

__all__ = ["build_system_prompt", "tool_schema", "SAFETY_PHRASE"]
