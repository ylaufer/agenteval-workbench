"""Inspect page for AgentEval Workbench UI."""
from __future__ import annotations

import json

import streamlit as st

from agenteval.core.service import (
    get_run,
    get_run_results,
    get_run_summary,
    list_cases,
    list_runs,
    load_case_metadata,
    load_evaluation_template,
    load_trace,
)
from agenteval.dataset.validator import _get_repo_root
from components.help_section import show_help_section
from onboarding.content import PAGE_HELP

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

    # Help section
    show_help_section("How this works", PAGE_HELP["inspect"])

    tab_cases, tab_runs = st.tabs(["Cases", "Runs"])

    with tab_cases:
        _render_cases_tab()

    with tab_runs:
        _render_runs_tab()


def _render_cases_tab() -> None:
    """Render the case inspection tab."""
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


def _render_runs_tab() -> None:
    """Render the run inspection tab."""
    runs = list_runs()
    if not runs:
        st.info("No evaluation runs yet. Run an evaluation from the **Evaluate** page first.")
        return

    run_ids = [r["run_id"] for r in runs]
    selected_run_id = st.selectbox("Select a run", run_ids)
    if not selected_run_id:
        return

    run = get_run(selected_run_id)
    if run is None:
        st.error(f"Run '{selected_run_id}' not found.")
        return

    # --- Run Metadata ---
    st.subheader("Run Metadata")
    cols = st.columns(3)
    cols[0].metric("Status", run.get("status", ""))
    cols[1].metric("Cases", run.get("num_cases", 0))
    started = run.get("started_at", "")[:19].replace("T", " ")
    cols[2].metric("Started", started)

    if run.get("completed_at"):
        completed = run["completed_at"][:19].replace("T", " ")
        st.markdown(f"**Completed**: {completed} UTC")
    st.markdown(f"**Dataset**: `{run.get('dataset_dir', '')}`")
    st.markdown(f"**Rubric**: `{run.get('rubric_path', '')}`")

    if run.get("error"):
        st.error(f"Error: {run['error']}")

    # --- Per-case Results ---
    results = get_run_results(selected_run_id)
    if results:
        st.subheader("Per-case Results")
        rows = []
        for ev in results:
            dims = ev.get("dimensions", {})
            scored = sum(
                1 for d in dims.values()
                if isinstance(d, dict) and d.get("score") is not None
            )
            total = len(dims)
            rows.append({
                "Case ID": ev.get("case_id", ""),
                "Primary Failure": ev.get("primary_failure", ""),
                "Severity": ev.get("severity", ""),
                "Scored": f"{scored}/{total}",
            })
        st.dataframe(rows, use_container_width=True)

    # --- Summary ---
    summary = get_run_summary(selected_run_id)
    if summary:
        st.subheader("Summary Statistics")
        summary_data = summary.get("summary", {})
        if summary_data:
            total_cases = summary_data.get("total_cases", 0)
            scored_cases = summary_data.get("scored_cases", 0)
            st.markdown(f"**Total cases**: {total_cases} | **Scored**: {scored_cases}")

        dimensions = summary.get("dimensions", {})
        if dimensions:
            dim_rows = []
            for dim_name, dim_data in dimensions.items():
                if not isinstance(dim_data, dict):
                    continue
                dim_rows.append({
                    "Dimension": dim_name,
                    "Mean Score": dim_data.get("mean_score", "N/A"),
                    "Scored Count": dim_data.get("scored_count", 0),
                })
            if dim_rows:
                st.dataframe(dim_rows, use_container_width=True)
