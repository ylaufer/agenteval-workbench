"""OpenAI Chat Completions API raw response adapter."""

from __future__ import annotations

from datetime import datetime

from agenteval.ingestion.base import parse_timestamp
from agenteval.schemas.trace import Trace


class OpenAIRawAdapter:
    """Adapter for OpenAI Chat Completions API raw responses."""

    def can_handle(self, raw: dict) -> bool:
        """Check if input is an OpenAI API response.

        Args:
            raw: Parsed JSON object

        Returns:
            True if this looks like an OpenAI response
        """
        try:
            return (
                "messages" in raw and isinstance(raw["messages"], list) and len(raw["messages"]) > 0
            )
        except (KeyError, TypeError):
            return False

    def convert(self, raw: dict) -> Trace:
        """Convert OpenAI response to AgentEval format.

        Args:
            raw: OpenAI API response JSON

        Returns:
            AgentEval Trace dict

        Raises:
            ValueError: If conversion fails
        """
        if not self.can_handle(raw):
            raise ValueError("Input is not a valid OpenAI API response")

        messages = raw["messages"]

        if len(messages) == 0:
            raise ValueError("No messages found in OpenAI response")

        steps: list[dict] = []

        # Process messages to extract steps
        # - Skip user messages (they're the input, not agent actions)
        # - Process assistant messages (can have tool_calls)
        # - Process tool messages (observations)
        for i, message in enumerate(messages):
            role = message.get("role")

            if role == "user":
                # Skip user messages
                continue

            elif role == "assistant":
                # Process assistant message
                # Check if this is the final message (heuristic: last assistant message with content)
                is_final = (
                    i == len(messages) - 1
                    and message.get("content")
                    and not message.get("tool_calls")
                )

                self._process_assistant_message(message, steps, is_final)

            elif role == "tool":
                # Process tool message (observation)
                self._process_tool_message(message, steps)

        # Sort steps by timestamp (deterministic ordering)
        steps.sort(key=lambda s: s["timestamp"])

        # Extract conversation ID
        conversation_id = raw.get("id", "unknown")

        # Get timestamp from first step or created timestamp
        if steps:
            timestamp = steps[0]["timestamp"]
        elif "created" in raw:
            timestamp = parse_timestamp(raw["created"])
        else:
            timestamp = datetime.now().isoformat() + "Z"

        # Extract user prompt from first user message
        user_prompt = "Ingested from OpenAI API response"
        for message in messages:
            if message.get("role") == "user" and message.get("content"):
                user_prompt = message["content"]
                break

        # Extract model version
        model_version = raw.get("model", "unknown")

        # Build trace matching AgentEval schema
        trace: Trace = {
            "task_id": conversation_id,
            "user_prompt": user_prompt,
            "model_version": model_version,
            "steps": steps,
            "metadata": {
                "timestamp": timestamp,
                "environment": {
                    "source": "openai",
                    "conversation_id": conversation_id,
                },
            },
        }

        return trace

    def _process_assistant_message(self, message: dict, steps: list[dict], is_final: bool) -> None:
        """Process an assistant message and extract steps.

        Args:
            message: Assistant message dict
            steps: List to append steps to
            is_final: Whether this is the final answer
        """
        # Generate timestamp (use current time as messages don't have timestamps)
        timestamp = datetime.now().isoformat() + "Z"

        # If message has tool_calls, expand them
        if message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                self._process_tool_call(tool_call, steps, timestamp)

        # If message has content, create a step
        elif message.get("content"):
            step_type = "final_answer" if is_final else "thought"
            step_id = f"msg_{len(steps)}"

            step = {
                "step_id": step_id,
                "type": step_type,
                "content": message["content"],
                "timestamp": timestamp,
                "event_id": step_id,
            }

            steps.append(step)

    def _process_tool_call(self, tool_call: dict, steps: list[dict], timestamp: str) -> None:
        """Process a tool call and create tool_call step.

        Args:
            tool_call: Tool call dict
            steps: List to append steps to
            timestamp: Timestamp string
        """
        tool_call_id = tool_call.get("id", f"call_{len(steps)}")
        function = tool_call.get("function", {})
        tool_name = function.get("name", "unknown_function")
        arguments = function.get("arguments", "{}")

        step = {
            "step_id": tool_call_id,
            "type": "tool_call",
            "content": arguments,
            "timestamp": timestamp,
            "event_id": tool_call_id,
            "tool_name": tool_name,
        }

        steps.append(step)

    def _process_tool_message(self, message: dict, steps: list[dict]) -> None:
        """Process a tool message (observation).

        Args:
            message: Tool message dict
            steps: List to append steps to
        """
        tool_call_id = message.get("tool_call_id", "unknown")
        content = message.get("content", "")

        # Generate timestamp
        timestamp = datetime.now().isoformat() + "Z"

        step = {
            "step_id": f"{tool_call_id}_obs",
            "type": "observation",
            "content": content,
            "timestamp": timestamp,
            "event_id": f"{tool_call_id}_obs",
            "parent_event_id": tool_call_id,  # Link to tool_call
        }

        steps.append(step)

    def validate_mapping(self, raw: dict) -> list[str]:
        """Validate OpenAI response and return warnings.

        Args:
            raw: OpenAI response dict

        Returns:
            List of warning messages
        """
        warnings = []

        if not self.can_handle(raw):
            warnings.append("Input does not appear to be a valid OpenAI API response")
            return warnings

        # Check for user messages
        has_user = False
        for message in raw.get("messages", []):
            if message.get("role") == "user":
                has_user = True
                break

        if not has_user:
            warnings.append("No user messages found (context may be limited)")

        # Check for model field
        if "model" not in raw:
            warnings.append("No 'model' field found (model_version will be 'unknown')")

        # Check for timestamps (OpenAI messages don't have timestamps by default)
        warnings.append("OpenAI messages lack timestamps - using current time for all steps")

        return warnings
