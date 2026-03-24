"""CrewAI task execution log adapter."""

from __future__ import annotations

from datetime import datetime

from agenteval.ingestion.base import parse_timestamp
from agenteval.schemas.trace import Trace

# Mapping from CrewAI action types to AgentEval step types
ACTION_TO_STEP_TYPE = {
    "thought": "thought",  # Agent reasoning
    "tool_use": "tool_call",  # Tool usage (will expand to tool_call + observation)
    "observation": "observation",  # Tool output
    "final_answer": "final_answer",  # Task completion
}


class CrewAIAdapter:
    """Adapter for CrewAI task execution logs."""

    def can_handle(self, raw: dict) -> bool:
        """Check if input is a CrewAI execution log.

        Args:
            raw: Parsed JSON object

        Returns:
            True if this looks like a CrewAI log
        """
        try:
            return "tasks" in raw and isinstance(raw["tasks"], list) and len(raw["tasks"]) > 0
        except (KeyError, TypeError):
            return False

    def convert(self, raw: dict) -> Trace:
        """Convert CrewAI log to AgentEval format.

        Args:
            raw: CrewAI execution log JSON

        Returns:
            AgentEval Trace dict

        Raises:
            ValueError: If conversion fails
        """
        if not self.can_handle(raw):
            raise ValueError("Input is not a valid CrewAI execution log")

        steps: list[dict] = []

        # Extract actions from all tasks
        for task in raw["tasks"]:
            self._process_task(task, steps)

        # Sort steps by timestamp (deterministic ordering)
        steps.sort(key=lambda s: s["timestamp"])

        # Extract execution ID for metadata
        execution_id = raw.get("execution_id", "unknown")

        # Get timestamp from first step or first task
        if steps:
            timestamp = steps[0]["timestamp"]
        elif raw["tasks"] and "started_at" in raw["tasks"][0]:
            timestamp = parse_timestamp(raw["tasks"][0]["started_at"])
        else:
            timestamp = datetime.now().isoformat() + "Z"

        # Extract crew name or first task description as prompt
        user_prompt = "Ingested from CrewAI execution"
        if "crew_name" in raw:
            user_prompt = f"CrewAI Crew: {raw['crew_name']}"
        elif raw["tasks"] and "description" in raw["tasks"][0]:
            user_prompt = raw["tasks"][0]["description"]

        # Build trace matching AgentEval schema
        trace: Trace = {
            "task_id": execution_id,
            "user_prompt": user_prompt,
            "model_version": "unknown",  # CrewAI doesn't track model version
            "steps": steps,
            "metadata": {
                "timestamp": timestamp,
                "environment": {
                    "source": "crewai",
                    "execution_id": execution_id,
                    "crew_name": raw.get("crew_name", "unknown"),
                },
            },
        }

        return trace

    def _process_task(self, task: dict, steps: list[dict]) -> None:
        """Process a single task and extract actions.

        Args:
            task: Task dict from CrewAI log
            steps: List to append steps to

        Raises:
            ValueError: If task is malformed
        """
        if "actions" not in task:
            return  # Task has no actions (skip)

        for action in task["actions"]:
            # Convert action based on type
            action_type = action.get("type", "thought")

            if action_type == "tool_use":
                # Expand tool_use into tool_call + observation
                self._expand_tool_action(action, steps)
            else:
                # Regular action: convert to single step
                step = self._convert_action(action)
                steps.append(step)

    def _convert_action(self, action: dict) -> dict:
        """Convert a single CrewAI action to an AgentEval step.

        Args:
            action: CrewAI action dict

        Returns:
            AgentEval step dict

        Raises:
            ValueError: If action is malformed
        """
        if "action_id" not in action:
            raise ValueError("Action missing required field 'action_id'")

        if "timestamp" not in action:
            raise ValueError("Action missing required field 'timestamp'")

        action_type = action.get("type", "thought")

        # Map action type (default to thought if unknown)
        if action_type in ACTION_TO_STEP_TYPE:
            step_type = ACTION_TO_STEP_TYPE[action_type]
        else:
            step_type = "thought"

        # Extract content
        content = action.get("content", "")

        # Build step
        step = {
            "step_id": action["action_id"],
            "type": step_type,
            "content": content,
            "timestamp": parse_timestamp(action["timestamp"]),
            "event_id": action["action_id"],
        }

        # Add agent as actor_id
        if "agent" in action:
            step["actor_id"] = action["agent"]

        return step

    def _expand_tool_action(self, action: dict, steps: list[dict]) -> None:
        """Expand tool_use action into tool_call + observation steps.

        Args:
            action: Tool action dict
            steps: List to append steps to

        Raises:
            ValueError: If action is malformed
        """
        if "action_id" not in action:
            raise ValueError("Action missing required field 'action_id'")

        if "timestamp" not in action:
            raise ValueError("Action missing required field 'timestamp'")

        action_id = action["action_id"]
        tool_name = action.get("tool_name", "unknown_tool")

        # Step 1: tool_call
        tool_input = action.get("tool_input", "")
        tool_call_step = {
            "step_id": f"{action_id}_call",
            "type": "tool_call",
            "content": tool_input,
            "timestamp": parse_timestamp(action["timestamp"]),
            "event_id": f"{action_id}_call",
            "tool_name": tool_name,
        }

        if "agent" in action:
            tool_call_step["actor_id"] = action["agent"]

        steps.append(tool_call_step)

        # Step 2: observation (if tool_output available)
        if "tool_output" in action:
            # Create observation timestamp slightly after tool_call
            obs_timestamp = parse_timestamp(action["timestamp"])
            obs_dt = datetime.fromisoformat(obs_timestamp.replace("Z", ""))
            obs_dt = obs_dt.replace(microsecond=obs_dt.microsecond + 100)
            obs_timestamp = obs_dt.isoformat() + "Z"

            observation_step = {
                "step_id": f"{action_id}_obs",
                "type": "observation",
                "content": action["tool_output"],
                "timestamp": obs_timestamp,
                "event_id": f"{action_id}_obs",
                "parent_event_id": f"{action_id}_call",
            }

            if "agent" in action:
                observation_step["actor_id"] = action["agent"]

            steps.append(observation_step)

    def validate_mapping(self, raw: dict) -> list[str]:
        """Validate CrewAI log and return warnings.

        Args:
            raw: CrewAI log dict

        Returns:
            List of warning messages
        """
        warnings = []

        if not self.can_handle(raw):
            warnings.append("Input does not appear to be a valid CrewAI execution log")
            return warnings

        # Check for agent field in actions
        has_agents = False
        for task in raw.get("tasks", []):
            for action in task.get("actions", []):
                if "agent" in action:
                    has_agents = True
                    break
            if has_agents:
                break

        if not has_agents:
            warnings.append("No 'agent' fields found in actions (actor_id will be empty)")

        # Check for task descriptions
        if raw.get("tasks") and not raw["tasks"][0].get("description"):
            warnings.append("No task descriptions found (context may be limited)")

        return warnings
