"""Evaluate page for AgentEval Workbench UI."""
from __future__ import annotations

import streamlit as st

from agenteval.core.service import list_runs, run_evaluation
from components.help_section import show_help_section
from onboarding.content import PAGE_HELP


def render() -> None:
    """Render the Evaluate page."""
    st.header("Run Evaluation Pipeline")

    # Help section
    show_help_section("How this works", PAGE_HELP["evaluate"])

    st.markdown(
        "Run the evaluation pipeline on all cases in `data/cases/`. "
        "Results are persisted under a tracked run in `runs/`."
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
            else:
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

    # --- Run History ---
    st.divider()
    st.subheader("Run History")

    runs = list_runs()
    if not runs:
        st.info("No evaluation runs yet. Click **Run Evaluation** above to create one.")
    else:
        run_rows = []
        for run in runs:
            started = run.get("started_at", "")[:19].replace("T", " ")
            run_rows.append({
                "Run ID": run.get("run_id", ""),
                "Status": run.get("status", ""),
                "Cases": run.get("num_cases", 0),
                "Started": started,
            })
        st.dataframe(run_rows, use_container_width=True)
