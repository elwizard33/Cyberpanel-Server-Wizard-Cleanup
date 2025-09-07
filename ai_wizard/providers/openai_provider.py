"""OpenAI provider adapter.

Supports tool/function calling mapping into ProviderResponse. Designed
to work with openai>=1.0 style client (responses API). Fallbacks gracefully
if SDK or key missing.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import os
import json

from cyberzard.core.provider_base import ProviderResponse, ToolCall, AbstractProvider

try:  # pragma: no cover - import side-eff
    import openai  # type: ignore
except Exception:  # pragma: no cover - absence path
    openai = None  # type: ignore


class OpenAIProvider(AbstractProvider):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if openai and self.api_key:
            try:
                openai.api_key = self.api_key  # legacy attr still honored in new SDK shim
                self._client = openai.Client() if hasattr(openai, "Client") else openai
            except Exception:
                self._client = None
        else:
            self._client = None

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 512,
    ) -> ProviderResponse:
        if not self._client:
            return ProviderResponse(
                content="OpenAI SDK not available or invalid key; running in degraded mode.",
                model=self.model,
            )

        # Prepare tool definitions (function calling schema)
        tool_defs = []
        if tools_schema:
            for t in tools_schema:
                tool_defs.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.get("name"),
                            "description": t.get("description", ""),
                            "parameters": t.get("parameters", {}),
                        },
                    }
                )
        try:
            if hasattr(self._client, "chat") and hasattr(self._client.chat, "completions"):
                # Legacy style (openai<1.0 or compatibility layer)
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tool_defs or None,
                    max_tokens=max_tokens,
                )
                choices = getattr(response, "choices", [])
                choice = choices[0] if choices else None
                message = getattr(choice, "message", None) if choice else None
                tool_calls_raw = getattr(message, "tool_calls", None) if message else None
                content_text = getattr(message, "content", "") if message else ""
            else:
                # New responses API path
                response = self._client.chat.completions.create(  # Fallback to chat
                    model=self.model,
                    messages=messages,
                    tools=tool_defs or None,
                    max_tokens=max_tokens,
                )
                choices = getattr(response, "choices", [])
                choice = choices[0] if choices else None
                message = getattr(choice, "message", None) if choice else None
                tool_calls_raw = getattr(message, "tool_calls", None) if message else None
                content_text = getattr(message, "content", "") if message else ""
        except Exception as e:
            return ProviderResponse(
                content=f"OpenAI request failed: {e}",
                model=self.model,
            )

        tool_calls: List[ToolCall] = []
        if tool_calls_raw:
            for tc in tool_calls_raw:
                try:
                    fname = tc.get("function", {}).get("name")
                    fargs_raw = tc.get("function", {}).get("arguments", "{}")
                    try:
                        parsed_args = json.loads(fargs_raw) if isinstance(fargs_raw, str) else fargs_raw
                    except Exception:
                        parsed_args = {"_raw": fargs_raw}
                    tool_calls.append(ToolCall(name=fname, arguments=parsed_args, id=str(tc.get("id", ""))))
                except Exception:
                    continue

        return ProviderResponse(content=content_text or "(no content)", tool_calls=tool_calls, model=self.model, raw=response)


__all__ = ["OpenAIProvider"]
