"""Report page for AgentEval Workbench UI."""
from __future__ import annotations

import streamlit as st

from agenteval.core.service import generate_summary_report
from components.empty_state import render_empty_state
from components.help_section import show_help_section
from components.workflow_nav import render_next_step_hint
from onboarding.content import PAGE_HELP


def render() -> None:
    """Render the Report page."""
    st.header("Aggregated Evaluation Report")

    # Help section
    show_help_section("How this works", PAGE_HELP["report"])

    st.markdown(
        "Generate a summary report from all evaluation templates in `reports/`. "
        "Results will be written to `reports/summary.evaluation.json` and "
        "`reports/summary.evaluation.md`."
    )

    if st.button("Generate Report"):
        try:
            with st.spinner("Generating summary report..."):
                report = generate_summary_report()
            st.session_state["_report_data"] = report
            st.session_state["_report_error"] = None
        except RuntimeError as exc:
            msg = str(exc)
            st.session_state["_report_data"] = None
            st.session_state["_report_error"] = msg

    # Display results from session state so buttons remain in the widget tree
    _report_error = st.session_state.get("_report_error")
    _report = st.session_state.get("_report_data")

    if _report_error is not None:
        if "No *.evaluation.json" in _report_error or "evaluation" in _report_error.lower():
            render_empty_state(
                ":material/summarize:",
                "No evaluations found",
                "Run the evaluation pipeline on the Evaluate page first.",
                "Go to Evaluate",
                "Evaluate",
            )
        elif "rubric" in _report_error.lower():
            st.error(f"Rubric error: {_report_error}")
        else:
            st.error(f"Report generation failed: {_report_error}")

    if _report is not None:
        # --- Overview ---
        summary = _report.get("summary", {})
        st.subheader("Overview")
        cols = st.columns(2)
        cols[0].metric("Total Cases", summary.get("num_cases", 0))
        cols[1].metric("Scored Cases", summary.get("num_scored_cases", 0))

        # --- Dimension Statistics ---
        dimensions = _report.get("dimensions", {})
        if dimensions:
            st.subheader("Dimension Statistics")
            rows = []
            for name, data in sorted(dimensions.items()):
                if not isinstance(data, dict):
                    continue
                mean = data.get("mean_score")
                mean_str = f"{mean:.2f}" if isinstance(mean, (int, float)) else "-"
                dist = data.get("distribution", {})
                dist_str = ", ".join(
                    f"{k}: {v}" for k, v in sorted(dist.items())
                ) if isinstance(dist, dict) else ""
                rows.append({
                    "Dimension": name,
                    "Weight": data.get("weight", 1.0),
                    "Mean Score": mean_str,
                    "Scored Count": data.get("num_scored", 0),
                    "Distribution": dist_str,
                })
            st.dataframe(rows, use_container_width=True)

        # --- Failure Summary ---
        failure_summary = _report.get("failure_summary", {})
        if failure_summary:
            st.subheader("Failure Summary")
            primary = failure_summary.get("primary_failure_counts", {})
            if primary:
                st.markdown("**Primary Failure Counts**")
                for failure, count in sorted(
                    primary.items(), key=lambda kv: kv[1], reverse=True
                ):
                    st.markdown(f"- `{failure}`: {count}")
            severity = failure_summary.get("severity_counts", {})
            if severity:
                st.markdown("**Severity Distribution**")
                for sev, count in sorted(
                    severity.items(), key=lambda kv: kv[1], reverse=True
                ):
                    st.markdown(f"- `{sev}`: {count}")

        # --- Recommendations ---
        recommendations = _report.get("recommendations", [])
        if recommendations:
            st.subheader("Recommendations")
            for rec in recommendations:
                st.markdown(f"- {rec}")

        st.success(
            "Summary files written to `reports/summary.evaluation.json` "
            "and `reports/summary.evaluation.md`."
        )
        render_next_step_hint("Report")
