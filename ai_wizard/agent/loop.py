"""Agent loop implementation.

Performs iterative provider calls with tool execution until either
no tool calls are returned or a step limit is reached. Tool schema is
derived from the registry on each run (dynamic extensibility).

The agent is intentionally minimal: no background threads, no hidden
state beyond the messages list. Each executed tool call is appended as
an assistant "tool" role style message with its JSON result to provide
full transparency to subsequent model iterations.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import json
import time

from cyberzard.tools.registry import get_schema, execute_tool
import cyberzard.tools  # noqa: F401  # ensure tool registration side-effects
from cyberzard.providers.openai_provider import OpenAIProvider
from cyberzard.providers.anthropic_provider import AnthropicProvider
from cyberzard.core.provider_base import Provider, ProviderResponse

SYSTEM_PROMPT = (
    "You are the CyberPanel AI Wizard assistant. You can inspect the server "
    "using the available tools. Always explain reasoning briefly before requesting a tool. "
    "Only request one tool per turn. When satisfied, provide a concise final answer."
)

_PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def _make_provider(name: str, model: Optional[str]) -> Provider:
    cls = _PROVIDERS.get(name.lower())
    if not cls:
        raise ValueError(f"Unsupported provider: {name}")
    return cls(model=model) if model else cls()


def run_agent(
    provider: str,
    user_query: str,
    model: Optional[str] = None,
    max_steps: int = 6,
    max_tokens: int = 600,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run an agent loop returning transcript and final response.

    Returns dict with keys: transcript (list[dict]), final (str).
    """
    prov = _make_provider(provider, model)
    schema = get_schema()
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    transcript: List[Dict[str, Any]] = []
    final_content = ""
    for step in range(max_steps):
        resp: ProviderResponse = prov.generate(messages, tools_schema=schema, max_tokens=max_tokens)
        transcript.append({
            "type": "model_response",
            "content": resp.content,
            "tool_calls": [tc.__dict__ for tc in resp.tool_calls],
        })
        if verbose:
            print(f"[step {step}] model: {resp.content[:120]}")
        if not resp.tool_calls:
            final_content = resp.content
            break
        # Execute first tool call only (policy: one per turn)
        tc = resp.tool_calls[0]
        tool_result = execute_tool(tc.name, tc.arguments)
        transcript.append({
            "type": "tool_result",
            "tool": tc.name,
            "arguments": tc.arguments,
            "result": tool_result,
        })
        # Append tool result as assistant tool message for context
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": f"Tool {tc.name} result:\n{json.dumps(tool_result)[:4000]}\nContinue reasoning or give final answer."})
        time.sleep(0.2)
    else:
        final_content = transcript[-1]["content"] if transcript else "(no content)"
    return {"transcript": transcript, "final": final_content}


__all__ = ["run_agent"]
