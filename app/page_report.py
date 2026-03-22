"""Report page for AgentEval Workbench UI."""
from __future__ import annotations

import streamlit as st

from agenteval.core.service import generate_summary_report


def render() -> None:
    """Render the Report page."""
    st.header("Aggregated Evaluation Report")

    st.markdown(
        "Generate a summary report from all evaluation templates in `reports/`. "
        "Results will be written to `reports/summary.evaluation.json` and "
        "`reports/summary.evaluation.md`."
    )

    if st.button("Generate Report"):
        try:
            with st.spinner("Generating summary report..."):
                report = generate_summary_report()

            # --- Overview ---
            summary = report.get("summary", {})
            st.subheader("Overview")
            cols = st.columns(2)
            cols[0].metric("Total Cases", summary.get("num_cases", 0))
            cols[1].metric("Scored Cases", summary.get("num_scored_cases", 0))

            # --- Dimension Statistics ---
            dimensions = report.get("dimensions", {})
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
            failure_summary = report.get("failure_summary", {})
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
            recommendations = report.get("recommendations", [])
            if recommendations:
                st.subheader("Recommendations")
                for rec in recommendations:
                    st.markdown(f"- {rec}")

            # --- Output confirmation ---
            st.success(
                "Summary files written to `reports/summary.evaluation.json` "
                "and `reports/summary.evaluation.md`."
            )

        except RuntimeError as exc:
            msg = str(exc)
            if "No *.evaluation.json" in msg or "evaluation" in msg.lower():
                st.info(
                    "No evaluation templates found in `reports/`. "
                    "Run the evaluation pipeline first from the **Evaluate** page."
                )
            elif "rubric" in msg.lower():
                st.error(f"Rubric error: {msg}")
            else:
                st.error(f"Report generation failed: {msg}")
