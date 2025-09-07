"""Backward-compatible agent entry bridging to new agent.loop implementation.

Provides process_user_input() wrapper fulfilling original task spec.
"""
from __future__ import annotations

from typing import Dict, Any, Optional

from .agent.loop import run_agent


def process_user_input(query: str, provider: str = "openai", model: Optional[str] = None, steps: int = 6, verbose: bool = False) -> Dict[str, Any]:
    """Execute an agent reasoning loop over a user query.

    Returns dict with transcript + final.
    """
    return run_agent(provider=provider, user_query=query, model=model, max_steps=steps, verbose=verbose)

__all__ = ["process_user_input"]
