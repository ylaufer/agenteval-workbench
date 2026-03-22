"""Evaluate page for AgentEval Workbench UI."""
from __future__ import annotations

import streamlit as st

from agenteval.core.service import run_evaluation


def render() -> None:
    """Render the Evaluate page."""
    st.header("Run Evaluation Pipeline")

    st.markdown(
        "Run the evaluation pipeline on all cases in `data/cases/`. "
        "Evaluation templates will be written to `reports/`."
    )

    if st.button("Run Evaluation"):
        try:
            with st.spinner("Running evaluation pipeline..."):
                results = run_evaluation()

            if not results:
                st.info(
                    "No cases found in the dataset. "
                    "Use the **Generate** page to create benchmark cases first."
                )
                return

            st.success(f"Processed **{len(results)}** case(s).")

            # Build summary table
            rows = []
            for ev in results:
                dims = ev.get("dimensions", {})
                scored = sum(
                    1 for d in dims.values()
                    if isinstance(d, dict) and d.get("score") is not None
                )
                total = len(dims)
                auto_tags = ev.get("auto_tags", [])
                tags_str = ", ".join(auto_tags) if auto_tags else ""

                rows.append({
                    "Case ID": ev.get("case_id", ""),
                    "Primary Failure": ev.get("primary_failure", ""),
                    "Severity": ev.get("severity", ""),
                    "Scored Dimensions": f"{scored}/{total}",
                    "Auto Tags": tags_str,
                })

            st.dataframe(rows, use_container_width=True)

        except RuntimeError as exc:
            msg = str(exc)
            if "rubric" in msg.lower() or "Rubric" in msg:
                st.error(f"Rubric error: {msg}")
            else:
                st.error(f"Evaluation failed: {msg}")
