"""Trace ingestion adapters for converting external trace formats to AgentEval format."""

from __future__ import annotations

from agenteval.ingestion.base import TraceAdapter
from agenteval.ingestion.crewai import CrewAIAdapter
from agenteval.ingestion.langchain import LangChainAdapter
from agenteval.ingestion.openai_raw import OpenAIRawAdapter
from agenteval.ingestion.otel import OTelAdapter

# Adapter registry will be populated as adapters are implemented
_ADAPTERS: list[TraceAdapter] = []


def register_adapter(adapter: TraceAdapter) -> None:
    """Register a trace adapter.

    Args:
        adapter: TraceAdapter instance to register
    """
    if not isinstance(adapter, TraceAdapter):
        raise TypeError(f"Adapter must implement TraceAdapter protocol, got {type(adapter)}")
    _ADAPTERS.append(adapter)


def auto_detect_adapter(raw: dict) -> TraceAdapter | None:
    """Auto-detect which adapter can handle the raw input.

    Tries each registered adapter's can_handle() method in registration order.

    Args:
        raw: Parsed JSON object from input file

    Returns:
        First adapter that can handle the input, or None if no adapter matches
    """
    for adapter in _ADAPTERS:
        try:
            if adapter.can_handle(raw):
                return adapter
        except Exception:
            # Adapter.can_handle() should not raise, but if it does, skip it
            continue

    return None


def get_adapter_by_name(name: str) -> TraceAdapter | None:
    """Get adapter by name (class name in lowercase).

    Args:
        name: Adapter name (e.g., "otel", "langchain", "crewai", "openai", "generic")

    Returns:
        Matching adapter or None if not found
    """
    name_lower = name.lower()
    for adapter in _ADAPTERS:
        adapter_name = adapter.__class__.__name__.lower().replace("adapter", "")
        if adapter_name == name_lower or adapter_name == name_lower + "adapter":
            return adapter

    return None


def list_adapters() -> list[str]:
    """List all registered adapter names.

    Returns:
        List of adapter class names
    """
    return [adapter.__class__.__name__ for adapter in _ADAPTERS]


__all__ = [
    "TraceAdapter",
    "register_adapter",
    "auto_detect_adapter",
    "get_adapter_by_name",
    "list_adapters",
]

# Register built-in adapters
register_adapter(OTelAdapter())
register_adapter(LangChainAdapter())
register_adapter(CrewAIAdapter())
register_adapter(OpenAIRawAdapter())
