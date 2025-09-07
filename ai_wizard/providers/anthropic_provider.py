"""Anthropic provider adapter.

Lightweight wrapper around anthropic official SDK (if installed) that
normalizes tool use blocks into ProviderResponse format. Falls back
gracefully when SDK missing or key invalid.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import os

from cyberzard.core.provider_base import ProviderResponse, ToolCall, AbstractProvider

try:  # pragma: no cover - import side-eff
    import anthropic  # type: ignore
except Exception:  # pragma: no cover - absence path
    anthropic = None  # type: ignore


class AnthropicProvider(AbstractProvider):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        if anthropic and self.api_key:
            try:
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except Exception:  # invalid key
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
                content="Anthropic SDK not available or invalid key; running in degraded mode.",
                model=self.model,
            )
        # Anthropic expects alternating user/assistant; we collapse system into first user prompt
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_messages = [m for m in messages if m["role"] != "system"]
        if system_parts and user_messages:
            # Prepend system to first user
            user_messages[0]["content"] = "\n".join(system_parts) + "\n" + user_messages[0]["content"]

        tool_defs = []
        if tools_schema:
            for t in tools_schema:
                # Anthropic beta tool schema
                tool_defs.append(
                    {
                        "name": t.get("name"),
                        "description": t.get("description", ""),
                        "input_schema": t.get("parameters", {}),
                    }
                )

        try:
            response = self._client.messages.create(  # type: ignore[attr-defined]
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": m["role"], "content": m["content"]} for m in user_messages],
                tools=tool_defs or None,
            )
        except Exception as e:  # network/auth errors
            return ProviderResponse(
                content=f"Anthropic request failed: {e}",
                model=self.model,
            )

        tool_calls: List[ToolCall] = []
        text_fragments: List[str] = []
        # Claude content blocks structure
        for block in getattr(response, "content", []) or []:
            btype = getattr(block, "type", None) or block.get("type") if isinstance(block, dict) else None
            if btype == "tool_use":
                # Extract tool call
                name = getattr(block, "name", None) or block.get("name")
                input_obj = getattr(block, "input", None) or block.get("input") or {}
                tool_calls.append(ToolCall(name=name, arguments=input_obj, id=str(getattr(block, "id", ""))))
            elif btype == "text":
                text = getattr(block, "text", None) or block.get("text")
                if text:
                    text_fragments.append(text)
        combined = "\n".join(text_fragments).strip() or "(no content)"
        return ProviderResponse(content=combined, tool_calls=tool_calls, model=self.model, raw=response)


__all__ = ["AnthropicProvider"]
