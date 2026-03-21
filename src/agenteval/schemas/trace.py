from __future__ import annotations

from typing import Any, Literal
from typing_extensions import NotRequired, TypedDict


class ContextRef(TypedDict):
    type: str
    id: str
    label: NotRequired[str]


class Step(TypedDict):
    step_id: str
    event_id: NotRequired[str]
    parent_event_id: NotRequired[str]
    type: Literal["plan", "thought", "tool_call", "observation", "final_answer"]
    actor_id: str
    content: str
    tool_name: NotRequired[str]
    tool_input: NotRequired[Any]
    tool_output: NotRequired[Any]
    screenshot_path: NotRequired[str]
    timestamp: NotRequired[str]
    latency_ms: NotRequired[int]
    span_id: NotRequired[str]
    context_refs: NotRequired[list[ContextRef]]


class Tokens(TypedDict, total=False):
    input: int
    output: int
    total: int


class Metadata(TypedDict):
    timestamp: str
    latency_ms: NotRequired[int]
    tokens: NotRequired[Tokens]
    environment: NotRequired[dict[str, Any]]
    labels: NotRequired[list[str]]


class Trace(TypedDict):
    task_id: str
    user_prompt: str
    model_version: str
    run_id: NotRequired[str]
    conversation_id: NotRequired[str]
    agent_id: NotRequired[str]
    steps: list[Step]
    metadata: Metadata
