"""LangChain/LangSmith run tree adapter."""

from __future__ import annotations

import json
from datetime import datetime

from agenteval.ingestion.base import map_step_type, parse_timestamp
from agenteval.schemas.trace import Trace

# Mapping from LangChain run types to AgentEval step types
RUN_TYPE_TO_STEP_TYPE = {
    "llm": "thought",  # LLM reasoning
    "chain": "thought",  # Chain orchestration
    "tool": "tool_call",  # Tool execution (will expand to tool_call + observation)
    "retriever": "tool_call",  # Retrieval operation
    "prompt": "thought",  # Prompt processing
}


class LangChainAdapter:
    """Adapter for LangChain/LangSmith run tree JSON."""

    def can_handle(self, raw: dict) -> bool:
        """Check if input is a LangChain run tree.

        Args:
            raw: Parsed JSON object

        Returns:
            True if this looks like a LangChain run
        """
        try:
            return "run_type" in raw and "id" in raw and isinstance(raw.get("run_type"), str)
        except (KeyError, TypeError):
            return False

    def convert(self, raw: dict) -> Trace:
        """Convert LangChain run to AgentEval format.

        Args:
            raw: LangChain run tree JSON

        Returns:
            AgentEval Trace dict

        Raises:
            ValueError: If conversion fails
        """
        if not self.can_handle(raw):
            raise ValueError("Input is not a valid LangChain run")

        steps: list[dict] = []

        # Flatten nested run tree
        self._flatten_runs(raw, steps)

        # Sort steps by timestamp (deterministic ordering)
        steps.sort(key=lambda s: s["timestamp"])

        # Extract run ID for metadata
        run_id = raw.get("id", "unknown")

        # Get timestamp from first step or root run
        if steps:
            timestamp = steps[0]["timestamp"]
        elif "start_time" in raw:
            timestamp = parse_timestamp(raw["start_time"])
        else:
            timestamp = datetime.now().isoformat() + "Z"

        # Extract user prompt from root inputs
        user_prompt = "Ingested from LangChain run"
        if "inputs" in raw:
            if isinstance(raw["inputs"], dict):
                # Try common input keys
                for key in ["input", "question", "query", "prompt"]:
                    if key in raw["inputs"]:
                        user_prompt = str(raw["inputs"][key])
                        break

        # Build trace matching AgentEval schema
        trace: Trace = {
            "task_id": run_id,
            "user_prompt": user_prompt,
            "model_version": "unknown",  # LangChain doesn't always track model version
            "steps": steps,
            "metadata": {
                "timestamp": timestamp,
                "environment": {
                    "source": "langchain",
                    "run_id": run_id,
                    "run_type": raw.get("run_type", "unknown"),
                },
            },
        }

        return trace

    def _flatten_runs(self, run: dict, steps: list[dict], parent_id: str | None = None) -> None:
        """Recursively flatten run tree into steps.

        Args:
            run: Current run dict
            steps: List to append steps to
            parent_id: Parent run ID for hierarchy tracking
        """
        if "id" not in run:
            raise ValueError("Run missing required field 'id'")

        if "start_time" not in run:
            raise ValueError("Run missing required field 'start_time'")

        run_id = run["id"]
        run_type = run.get("run_type", "chain")

        # Special handling for tool runs: expand into tool_call + observation
        if run_type == "tool":
            self._expand_tool_run(run, steps, parent_id)
        else:
            # Regular run: convert to single step
            step = self._convert_run(run, parent_id)
            steps.append(step)

        # Recursively process child runs
        for child_run in run.get("child_runs", []):
            self._flatten_runs(child_run, steps, parent_id=run_id)

    def _convert_run(self, run: dict, parent_id: str | None) -> dict:
        """Convert a single LangChain run to an AgentEval step.

        Args:
            run: LangChain run dict
            parent_id: Parent run ID

        Returns:
            AgentEval step dict
        """
        run_type = run.get("run_type", "chain")
        step_type = map_step_type(run_type, RUN_TYPE_TO_STEP_TYPE)

        # Extract content from outputs or inputs
        content = self._extract_content(run, step_type)

        # Build step
        step = {
            "step_id": run["id"],
            "type": step_type,
            "content": content,
            "timestamp": parse_timestamp(run["start_time"]),
            "event_id": run["id"],
        }

        # Add parent relationship
        if parent_id:
            step["parent_event_id"] = parent_id

        # Add latency if available
        if "end_time" in run:
            start_time = parse_timestamp(run["start_time"])
            end_time = parse_timestamp(run["end_time"])
            # Calculate latency in milliseconds
            start_dt = datetime.fromisoformat(start_time.replace("Z", ""))
            end_dt = datetime.fromisoformat(end_time.replace("Z", ""))
            latency_ms = (end_dt - start_dt).total_seconds() * 1000
            step["latency_ms"] = round(latency_ms, 2)

        return step

    def _expand_tool_run(self, run: dict, steps: list[dict], parent_id: str | None) -> None:
        """Expand tool run into tool_call + observation steps.

        Args:
            run: Tool run dict
            steps: List to append steps to
            parent_id: Parent run ID
        """
        run_id = run["id"]
        tool_name = run.get("name", "unknown_tool")

        # Step 1: tool_call
        tool_call_content = json.dumps(run.get("inputs", {}))
        tool_call_step = {
            "step_id": f"{run_id}_call",
            "type": "tool_call",
            "content": tool_call_content,
            "timestamp": parse_timestamp(run["start_time"]),
            "event_id": f"{run_id}_call",
            "tool_name": tool_name,
        }

        if parent_id:
            tool_call_step["parent_event_id"] = parent_id

        steps.append(tool_call_step)

        # Step 2: observation (if outputs available)
        if "outputs" in run and "end_time" in run:
            observation_content = json.dumps(run["outputs"])
            observation_step = {
                "step_id": f"{run_id}_obs",
                "type": "observation",
                "content": observation_content,
                "timestamp": parse_timestamp(run["end_time"]),
                "event_id": f"{run_id}_obs",
                "parent_event_id": f"{run_id}_call",  # Observation follows tool_call
            }

            # Add latency
            start_dt = datetime.fromisoformat(parse_timestamp(run["start_time"]).replace("Z", ""))
            end_dt = datetime.fromisoformat(parse_timestamp(run["end_time"]).replace("Z", ""))
            latency_ms = (end_dt - start_dt).total_seconds() * 1000
            observation_step["latency_ms"] = round(latency_ms, 2)

            steps.append(observation_step)

    def _extract_content(self, run: dict, step_type: str) -> str:
        """Extract content from run based on step type.

        Args:
            run: LangChain run dict
            step_type: Determined step type

        Returns:
            Content string
        """
        # For LLM runs, try to extract assistant message
        if step_type == "thought" and "outputs" in run:
            outputs = run["outputs"]
            if isinstance(outputs, dict):
                # Try to extract from generations
                if "generations" in outputs:
                    generations = outputs["generations"]
                    if isinstance(generations, list) and len(generations) > 0:
                        first_gen = generations[0]
                        if isinstance(first_gen, dict) and "message" in first_gen:
                            message = first_gen["message"]
                            if isinstance(message, dict) and "content" in message:
                                return message["content"]

                # Fallback to output field
                if "output" in outputs:
                    return str(outputs["output"])

        # For tool calls, use inputs
        if step_type == "tool_call" and "inputs" in run:
            return json.dumps(run["inputs"])

        # Fallback to run name
        return run.get("name", "")

    def validate_mapping(self, raw: dict) -> list[str]:
        """Validate LangChain run and return warnings.

        Args:
            raw: LangChain run dict

        Returns:
            List of warning messages
        """
        warnings = []

        if not self.can_handle(raw):
            warnings.append("Input does not appear to be a valid LangChain run")
            return warnings

        # Check for common issues
        if "child_runs" not in raw:
            warnings.append("No child_runs found (trace may be incomplete)")

        # Check for streaming events (not yet supported)
        def check_streaming(run: dict) -> bool:
            if run.get("run_type") == "llm" and "events" in run:
                return True
            for child in run.get("child_runs", []):
                if check_streaming(child):
                    return True
            return False

        if check_streaming(raw):
            warnings.append(
                "Streaming token events detected (will be collapsed into final outputs)"
            )

        return warnings
