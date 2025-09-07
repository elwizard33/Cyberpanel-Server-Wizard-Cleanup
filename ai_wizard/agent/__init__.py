"""Lightweight ReAct-style agent loop.

Exposes a helper to run a provider with the registered tool schema and
execute returned tool calls iteratively. Designed to keep state simple
and auditable (plain message list + executed tool results appended).
"""

from .loop import run_agent  # noqa: F401


def process_user_input(query: str, provider: str = "openai", model: str | None = None, steps: int = 6, verbose: bool = False):
	"""Backward-compatible wrapper returning run_agent result.

	Returns dict with transcript + final.
	"""
	return run_agent(provider=provider, user_query=query, model=model, max_steps=steps, verbose=verbose)


__all__ = ["run_agent", "process_user_input"]
