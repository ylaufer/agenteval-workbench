"""Base adapter protocol and common utilities for trace ingestion."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from agenteval.schemas.trace import Trace


@runtime_checkable
class TraceAdapter(Protocol):
    """Protocol for trace format adapters.

    Each adapter must implement three methods:
    - can_handle: Determine if this adapter can process the raw input
    - convert: Transform raw input into AgentEval Trace format
    - validate_mapping: Check for unmappable fields and return warnings
    """

    def can_handle(self, raw: dict) -> bool:
        """Determine if this adapter can convert the raw input.

        Args:
            raw: Parsed JSON object from input file

        Returns:
            True if this adapter recognizes the format
        """
        ...

    def convert(self, raw: dict) -> Trace:
        """Convert raw input to AgentEval Trace.

        Args:
            raw: Parsed JSON object from input file

        Returns:
            Validated Trace dict

        Raises:
            ValueError: If conversion fails
        """
        ...

    def validate_mapping(self, raw: dict) -> list[str]:
        """Check for unmappable fields and return warnings.

        Args:
            raw: Parsed JSON object from input file

        Returns:
            List of warning messages (empty if all fields mappable)
        """
        ...


def check_file_size(
    file_path: Path, soft_limit_mb: int = 10, hard_limit_mb: int = 50
) -> tuple[bool, str | None]:
    """Check file size against soft and hard limits.

    Args:
        file_path: Path to file to check
        soft_limit_mb: Soft limit in MB (warns but continues)
        hard_limit_mb: Hard limit in MB (fails)

    Returns:
        Tuple of (should_continue, warning_or_error_message)
        - (True, None): File size OK
        - (True, "warning..."): File exceeds soft limit, but can continue
        - (False, "error..."): File exceeds hard limit, must abort

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)

    if size_mb >= hard_limit_mb:
        return (False, f"File size {size_mb:.1f} MB exceeds hard limit of {hard_limit_mb} MB")
    elif size_mb >= soft_limit_mb:
        return (
            True,
            f"Warning: File size {size_mb:.1f} MB exceeds soft limit of {soft_limit_mb} MB",
        )
    else:
        return (True, None)


def parse_timestamp(timestamp: str | int | float) -> str:
    """Parse various timestamp formats to ISO8601 string.

    Args:
        timestamp: Timestamp in various formats:
            - ISO8601 string: returned as-is
            - Unix epoch (seconds): converted to ISO8601
            - Unix epoch (milliseconds): converted to ISO8601
            - Nanoseconds: converted to ISO8601

    Returns:
        ISO8601 formatted timestamp string

    Raises:
        ValueError: If timestamp format is unrecognized
    """
    if isinstance(timestamp, str):
        # Assume already ISO8601
        return timestamp

    if isinstance(timestamp, (int, float)):
        # Determine if seconds, milliseconds, or nanoseconds
        if timestamp > 1e15:  # Nanoseconds (>~2033 in epoch seconds)
            dt = datetime.fromtimestamp(timestamp / 1e9)
        elif timestamp > 1e12:  # Milliseconds (>~2001 in epoch seconds)
            dt = datetime.fromtimestamp(timestamp / 1000)
        else:  # Seconds
            dt = datetime.fromtimestamp(timestamp)

        return dt.isoformat() + "Z"

    raise ValueError(f"Unrecognized timestamp format: {type(timestamp)}")


def map_step_type(source_type: str, mapping: dict[str, str]) -> str:
    """Map source step type to AgentEval step type.

    Args:
        source_type: Step type from source framework
        mapping: Dictionary mapping source types to AgentEval types

    Returns:
        Mapped step type (thought, tool_call, observation, final_answer)

    Raises:
        ValueError: If source_type not in mapping
    """
    if source_type not in mapping:
        raise ValueError(
            f"Unknown step type '{source_type}'. Expected one of: {', '.join(mapping.keys())}"
        )
    return mapping[source_type]


def validate_trace_output(trace: Trace) -> None:
    """Validate that converted trace meets AgentEval requirements.

    Args:
        trace: Converted trace dict

    Raises:
        ValueError: If trace is invalid
    """
    import jsonschema

    from agenteval.dataset.validator import _get_repo_root, _load_json

    # Load and validate against trace schema
    try:
        repo_root = _get_repo_root()
        schema_path = repo_root / "schemas" / "trace_schema.json"
        schema = _load_json(schema_path)

        jsonschema.validate(instance=trace, schema=schema)
    except jsonschema.ValidationError as e:
        raise ValueError(f"Trace validation failed: {e.message}") from e
    except Exception as e:
        raise ValueError(f"Converted trace failed schema validation: {e}") from e


class ValidationWarning:
    """Helper for collecting validation warnings."""

    def __init__(self) -> None:
        """Initialize empty warning collector."""
        self.warnings: list[str] = []

    def add(self, message: str) -> None:
        """Add a warning message.

        Args:
            message: Warning message to add
        """
        self.warnings.append(message)

    def get_all(self) -> list[str]:
        """Get all collected warnings.

        Returns:
            List of warning messages
        """
        return self.warnings


def fail_fast_validator(trace: Trace) -> None:
    """Validate trace with fail-fast strategy (abort on first error).

    Args:
        trace: Trace dict to validate

    Raises:
        ValueError: On first validation error encountered
    """
    validate_trace_output(trace)


def collect_warnings(raw: dict, adapter: TraceAdapter) -> list[str]:
    """Collect all validation warnings from adapter.

    Args:
        raw: Raw input dict
        adapter: Adapter instance

    Returns:
        List of warning messages
    """
    return adapter.validate_mapping(raw)
