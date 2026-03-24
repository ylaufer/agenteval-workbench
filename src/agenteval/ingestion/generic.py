"""Generic JSON adapter with user-defined field mappings."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from agenteval.ingestion.base import parse_timestamp
from agenteval.schemas.trace import Trace


class GenericAdapter:
    """Adapter for custom JSON formats with user-defined mappings.

    Supports dot-notation paths (e.g., "execution.run_id") and transforms.
    """

    def __init__(self, mapping: dict[str, Any]) -> None:
        """Initialize with mapping configuration.

        Args:
            mapping: Mapping config dict with field paths and transforms

        Raises:
            ValueError: If mapping is invalid
        """
        self.mapping = mapping
        self._validate_mapping_config()

    def _validate_mapping_config(self) -> None:
        """Validate that mapping config has required fields.

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["task_id", "user_prompt", "model_version", "steps_path", "step_mappings"]

        for field in required_fields:
            if field not in self.mapping:
                raise ValueError(f"Missing required mapping field: {field}")

        # Validate step_mappings has required fields
        step_mappings = self.mapping["step_mappings"]
        required_step_fields = ["step_id", "type", "content", "timestamp"]

        for field in required_step_fields:
            if field not in step_mappings:
                raise ValueError(f"Missing required step mapping field: {field}")

    def can_handle(self, raw: dict) -> bool:
        """Check if adapter can handle the input.

        Generic adapter always returns True as a fallback.

        Args:
            raw: Parsed JSON object

        Returns:
            Always True
        """
        return isinstance(raw, dict)

    def convert(self, raw: dict) -> Trace:
        """Convert custom JSON to AgentEval format using mapping.

        Args:
            raw: Custom JSON dict

        Returns:
            AgentEval Trace dict

        Raises:
            ValueError: If conversion fails
        """
        # Extract top-level fields
        task_id = self._extract_field(raw, self.mapping["task_id"])
        user_prompt = self._extract_field(raw, self.mapping["user_prompt"])
        model_version = self._extract_field(raw, self.mapping["model_version"])

        # Extract steps
        steps_path = self.mapping["steps_path"]
        steps_raw = self._extract_field(raw, steps_path)

        if not isinstance(steps_raw, list):
            raise ValueError(f"Steps path '{steps_path}' did not resolve to a list")

        # Convert each step
        steps = []
        for step_raw in steps_raw:
            step = self._convert_step(step_raw)
            steps.append(step)

        # Extract metadata timestamp if configured
        if "metadata_timestamp" in self.mapping:
            timestamp = self._extract_field(raw, self.mapping["metadata_timestamp"])
            if timestamp:
                timestamp = parse_timestamp(timestamp)
            else:
                timestamp = steps[0]["timestamp"] if steps else datetime.now().isoformat() + "Z"
        else:
            timestamp = steps[0]["timestamp"] if steps else datetime.now().isoformat() + "Z"

        # Build trace
        trace: Trace = {
            "task_id": str(task_id) if task_id else "unknown",
            "user_prompt": str(user_prompt) if user_prompt else "unknown",
            "model_version": str(model_version) if model_version else "unknown",
            "steps": steps,
            "metadata": {
                "timestamp": timestamp,
                "environment": {
                    "source": self.mapping.get("metadata_source", "generic"),
                },
            },
        }

        return trace

    def _convert_step(self, step_raw: dict) -> dict:
        """Convert a single step using step_mappings.

        Args:
            step_raw: Raw step dict

        Returns:
            AgentEval step dict
        """
        step_mappings = self.mapping["step_mappings"]
        step = {}

        # Extract each mapped field
        for field_name, field_config in step_mappings.items():
            value = self._extract_and_transform(step_raw, field_config)

            # Only include non-None values
            if value is not None:
                step[field_name] = value

        # Ensure required fields are present
        if "step_id" not in step:
            raise ValueError("Step missing required field 'step_id'")
        if "type" not in step:
            raise ValueError("Step missing required field 'type'")
        if "content" not in step:
            step["content"] = ""  # Default to empty string
        if "timestamp" not in step:
            raise ValueError("Step missing required field 'timestamp'")

        # Add event_id if not already set
        if "event_id" not in step:
            step["event_id"] = step["step_id"]

        return step

    def _extract_and_transform(self, data: dict, config: str | dict) -> Any:
        """Extract field and apply transforms.

        Args:
            data: Data dict to extract from
            config: Simple path string or dict with path + transform

        Returns:
            Extracted and transformed value
        """
        # Simple path (no transform)
        if isinstance(config, str):
            return self._extract_field(data, config)

        # Dict with path and optional transform
        if isinstance(config, dict):
            path = config.get("path")
            value = self._extract_field(data, path)

            # Apply transform if specified
            if "transform" in config and value is not None:
                value = self._apply_transform(value, config)

            return value

        return None

    def _extract_field(self, data: dict, path: str | None) -> Any:
        """Extract field using dot-notation path.

        Args:
            data: Data dict to extract from
            path: Dot-notation path (e.g., "execution.run_id")

        Returns:
            Extracted value or None if not found
        """
        if not path:
            return None

        parts = path.split(".")
        current = data

        for part in parts:
            if not isinstance(current, dict):
                return None

            if part not in current:
                return None

            current = current[part]

        return current

    def _apply_transform(self, value: Any, config: dict) -> Any:
        """Apply transform function to value.

        Args:
            value: Value to transform
            config: Transform config with 'transform' and optional parameters

        Returns:
            Transformed value
        """
        transform = config["transform"]

        if transform == "map":
            # Map value using provided mapping dict
            mapping_dict = config.get("mapping", {})
            return mapping_dict.get(value, value)

        elif transform == "iso8601":
            # Convert timestamp to ISO8601
            return parse_timestamp(value)

        elif transform == "concat":
            # Concatenate multiple fields (not yet implemented)
            return value

        else:
            # Unknown transform - return as-is
            return value

    def validate_mapping(self, raw: dict) -> list[str]:
        """Validate custom JSON and return warnings.

        Args:
            raw: Custom JSON dict

        Returns:
            List of warning messages
        """
        warnings = []

        # Check that top-level fields can be extracted
        for field_name in ["task_id", "user_prompt", "model_version"]:
            if field_name in self.mapping:
                path = self.mapping[field_name]
                value = self._extract_field(raw, path)
                if value is None:
                    warnings.append(f"Field '{field_name}' (path: '{path}') not found in input")

        # Check that steps_path resolves to a list
        steps_path = self.mapping["steps_path"]
        steps_raw = self._extract_field(raw, steps_path)
        if steps_raw is None:
            warnings.append(f"Steps path '{steps_path}' not found in input")
        elif not isinstance(steps_raw, list):
            warnings.append(f"Steps path '{steps_path}' did not resolve to a list")

        return warnings
