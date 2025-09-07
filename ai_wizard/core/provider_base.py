"""Provider abstraction base classes.

Defines a minimal interface for LLM providers that support tool
(or function) calling. Concrete implementations will adapt
provider-specific SDK responses into canonical structures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Protocol, runtime_checkable
from abc import ABC, abstractmethod


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class ProviderResponse:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    model: Optional[str] = None
    raw: Optional[Any] = None  # original provider object for debugging


@runtime_checkable
class Provider(Protocol):  # Using Protocol to allow duck typing
    name: str

    def generate(self, messages: List[Dict[str, str]], tools_schema: Optional[List[Dict[str, Any]]] = None, max_tokens: int = 512) -> ProviderResponse:  # pragma: no cover - interface
        ...


class AbstractProvider(ABC):  # Optional stricter base
    name: str = "abstract"

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], tools_schema: Optional[List[Dict[str, Any]]] = None, max_tokens: int = 512) -> ProviderResponse:  # pragma: no cover - interface
        raise NotImplementedError


__all__ = ["ToolCall", "ProviderResponse", "Provider", "AbstractProvider"]
