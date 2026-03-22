"""Inspect page for AgentEval Workbench UI."""
from __future__ import annotations

import json

import streamlit as st

from agenteval.core.service import (
    list_cases,
    load_case_metadata,
    load_evaluation_template,
    load_trace,
)
from agenteval.dataset.validator import _get_repo_root

# Color-coded badges for step types
_TYPE_COLORS = {
    "thought": "blue",
    "tool_call": "orange",
    "observation": "green",
    "final_answer": "violet",
}


def _render_step(step: dict) -> None:  # type: ignore[type-arg]
    """Render a single trace step."""
    step_id = step.get("step_id", "?")
    step_type = step.get("type", "unknown")
    actor = step.get("actor_id", "")
    content = step.get("content", "")
    color = _TYPE_COLORS.get(step_type, "gray")

    st.markdown(f"**`{step_id}`** :{color}[{step_type}] — *{actor}*")
    st.text(content)

    if step_type == "tool_call":
        tool_name = step.get("tool_name")
        tool_input = step.get("tool_input")
        if tool_name:
            st.markdown(f"Tool: `{tool_name}`")
        if tool_input:
            st.json(tool_input)

    if step_type == "observation":
        tool_output = step.get("tool_output")
        if tool_output:
            st.code(str(tool_output), language=None)

    st.divider()


def render() -> None:
    """Render the Inspect page."""
    st.header("Inspect Trace & Evaluation")

    cases = list_cases()
    if not cases:
        st.info(
            "No cases found in the dataset. "
            "Use the **Generate** page to create benchmark cases first."
        )
        return

    selected = st.selectbox("Select a case", cases)
    if not selected:
        return

    repo_root = _get_repo_root()
    case_dir = repo_root / "data" / "cases" / selected

    # --- Case Metadata ---
    st.subheader("Case Metadata")
    metadata = load_case_metadata(case_dir)
    if metadata:
        cols = st.columns(3)
        cols[0].metric("Case ID", metadata.get("case_id") or selected)
        cols[1].metric("Primary Failure", metadata.get("primary_failure") or "N/A")
        cols[2].metric("Severity", metadata.get("severity") or "N/A")

        secondary = metadata.get("secondary_failures")
        if secondary:
            st.markdown(f"**Secondary Failures**: {secondary}")
        version = metadata.get("case_version")
        if version:
            st.markdown(f"**Case Version**: {version}")
    else:
        st.warning("No metadata found (expected_outcome.md missing or has no header).")

    # --- Trace Viewer ---
    st.subheader("Trace Steps")
    try:
        trace = load_trace(case_dir)
        steps = trace.get("steps", [])
        if not steps:
            st.info("Trace has no steps.")
        else:
            for step in steps:
                if isinstance(step, dict):
                    _render_step(step)
    except (json.JSONDecodeError, Exception) as exc:
        st.error(f"Failed to parse trace: {exc}")

    # --- Evaluation Template ---
    st.subheader("Evaluation Template")
    template = load_evaluation_template(selected)
    if template is None:
        st.info("No evaluation template found. Run evaluation first from the **Evaluate** page.")
    else:
        dims = template.get("dimensions", {})
        if dims:
            for dim_name, dim_data in dims.items():
                if not isinstance(dim_data, dict):
                    continue
                score = dim_data.get("score")
                weight = dim_data.get("weight", 1.0)
                scale = dim_data.get("scale", "0-2")
                score_display = str(score) if score is not None else "Not yet scored"

                st.markdown(
                    f"**{dim_name}** — Scale: {scale}, Weight: {weight}, "
                    f"Score: **{score_display}**"
                )

        auto_tags = template.get("auto_tags", [])
        if auto_tags:
            st.markdown(f"**Auto Tags**: {', '.join(f'`{t}`' for t in auto_tags)}")
