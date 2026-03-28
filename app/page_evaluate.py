"""Evaluate page for AgentEval Workbench UI."""
from __future__ import annotations

from typing import Any

import streamlit as st

from agenteval.core.service import (
    get_dataset_tags,
    list_cases,
    list_runs,
    load_case_metadata,
    run_evaluation,
    run_selective_evaluation,
)
from agenteval.dataset.validator import _get_repo_root
from components.help_section import show_help_section
from onboarding.content import PAGE_HELP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_case_data() -> list[dict[str, Any]]:
    """Load all cases with metadata. Cached in session_state for the session."""
    if "eval_case_data" not in st.session_state:
        repo_root = _get_repo_root()
        dataset_dir = repo_root / "data" / "cases"
        cases: list[dict[str, Any]] = []
        for case_id in list_cases():
            case_dir = dataset_dir / case_id
            meta = load_case_metadata(case_dir)
            cases.append({
                "case_id": case_id,
                "primary_failure": meta.get("primary_failure") or "",
                "severity": meta.get("severity") or "",
            })
        st.session_state.eval_case_data = cases
    return st.session_state.eval_case_data  # type: ignore[return-value]


def _load_dataset_tags() -> list[str]:
    """Load dataset tags. Cached in session_state."""
    if "eval_dataset_tags" not in st.session_state:
        st.session_state.eval_dataset_tags = sorted(get_dataset_tags())
    return st.session_state.eval_dataset_tags  # type: ignore[return-value]


def _apply_filters(
    cases: list[dict[str, Any]],
    failure_type: str | None,
    severity: list[str],
    tags: list[str],
    pattern: str,
) -> list[dict[str, Any]]:
    """Filter case list using active filter criteria (AND logic)."""
    from agenteval.core.filtering import filter_cases

    repo_root = _get_repo_root()
    dataset_dir = repo_root / "data" / "cases"

    all_dirs = [dataset_dir / c["case_id"] for c in cases]
    filtered_dirs = filter_cases(
        case_dirs=all_dirs,
        failure_type=failure_type or None,
        severity=severity if severity else None,
        tags=tags if tags else None,
        pattern=pattern if pattern.strip() else None,
    )
    filtered_names = {d.name for d in filtered_dirs}
    return [c for c in cases if c["case_id"] in filtered_names]


def _on_evaluate_selected(filtered_cases: list[dict[str, Any]]) -> None:
    """Callback: evaluate checked cases."""
    selected = [
        c["case_id"]
        for c in filtered_cases
        if st.session_state.get(f"chk_{c['case_id']}", False)
    ]
    if not selected:
        return
    try:
        result = run_selective_evaluation(selected)
        st.session_state.eval_results = result
    except Exception as exc:
        st.session_state.eval_results = {"error": str(exc)}


def _on_evaluate_filtered(filtered_cases: list[dict[str, Any]]) -> None:
    """Callback: evaluate all filtered cases."""
    case_ids = [c["case_id"] for c in filtered_cases]
    if not case_ids:
        return
    try:
        result = run_selective_evaluation(case_ids)
        st.session_state.eval_results = result
    except Exception as exc:
        st.session_state.eval_results = {"error": str(exc)}


# ---------------------------------------------------------------------------
# Page render
# ---------------------------------------------------------------------------


def render() -> None:
    """Render the Evaluate page."""
    st.header("Run Evaluation Pipeline")

    # Help section
    show_help_section("How this works", PAGE_HELP["evaluate"])

    # Initialize session state
    st.session_state.setdefault("eval_results", None)

    # -----------------------------------------------------------------------
    # Full-dataset evaluation (existing behaviour, preserved)
    # -----------------------------------------------------------------------
    with st.expander("Run evaluation on all cases", expanded=False):
        st.markdown(
            "Run the full evaluation pipeline on all cases in `data/cases/`. "
            "Results are persisted under a tracked run in `runs/`."
        )
        if st.button("Run Full Evaluation"):
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
                    rows = []
                    for ev in results:
                        dims = ev.get("dimensions", {})
                        scored = sum(
                            1 for d in dims.values()
                            if isinstance(d, dict) and d.get("score") is not None
                        )
                        total = len(dims)
                        auto_tags = ev.get("auto_tags", [])
                        rows.append({
                            "Case ID": ev.get("case_id", ""),
                            "Scored Dimensions": f"{scored}/{total}",
                            "Auto Tags": ", ".join(auto_tags) if auto_tags else "",
                        })
                    st.dataframe(rows, use_container_width=True, hide_index=True)
            except RuntimeError as exc:
                msg = str(exc)
                st.error(f"Evaluation failed: {msg}")

    st.divider()

    # -----------------------------------------------------------------------
    # Selective auto-scoring
    # -----------------------------------------------------------------------
    st.subheader("Selective Auto-Scoring")
    st.caption(
        "Filter and select cases, then run auto-scoring on the chosen subset. "
        "This runs **auto-scoring only** (rule-based + optional LLM evaluators)."
    )

    all_cases = _load_case_data()
    all_tags = _load_dataset_tags()

    if not all_cases:
        st.info(
            "No cases found in the dataset. "
            "Use the **Generate** page to create benchmark cases first."
        )
        _render_run_history()
        return

    # --- Filter controls ---
    failure_options = sorted({c["primary_failure"] for c in all_cases if c["primary_failure"]})
    severity_options = ["Critical", "High", "Medium", "Low"]

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    with filter_col1:
        failure_filter = st.selectbox(
            "Failure Type",
            options=["(all)"] + failure_options,
            key="filter_failure_type",
        )
    with filter_col2:
        severity_filter: list[str] = st.multiselect(
            "Severity",
            options=severity_options,
            key="filter_severity",
        )
    with filter_col3:
        tag_filter: list[str] = st.multiselect(
            "Tags",
            options=all_tags,
            key="filter_tags",
        )
    with filter_col4:
        pattern_filter: str = st.text_input(
            "Case ID Pattern",
            placeholder="e.g. case_0*",
            key="filter_pattern",
        )

    active_failure = failure_filter if failure_filter != "(all)" else None
    filtered_cases = _apply_filters(
        all_cases,
        failure_type=active_failure,
        severity=severity_filter,
        tags=tag_filter,
        pattern=pattern_filter,
    )

    # --- Case list with checkboxes ---
    n_filtered = len(filtered_cases)
    n_selected = sum(
        1 for c in filtered_cases
        if st.session_state.get(f"chk_{c['case_id']}", False)
    )

    if not filtered_cases:
        st.info("No cases match the current filter.")
    else:
        st.markdown(f"**{n_filtered}** case(s) match the filter:")
        with st.container(border=True, gap=None):
            hdr1, hdr2, hdr3, hdr4 = st.columns([0.5, 2, 2, 1])
            hdr1.markdown("**✓**")
            hdr2.markdown("**Case ID**")
            hdr3.markdown("**Failure Type**")
            hdr4.markdown("**Severity**")
            st.divider()
            for case in filtered_cases:
                c1, c2, c3, c4 = st.columns([0.5, 2, 2, 1])
                c1.checkbox(
                    "",
                    key=f"chk_{case['case_id']}",
                    label_visibility="collapsed",
                )
                c2.write(case["case_id"])
                c3.write(case["primary_failure"] or "—")
                c4.write(case["severity"] or "—")

    # --- Evaluate buttons ---
    with st.container(horizontal=True):
        st.button(
            f"Run Auto-Scoring on Selected ({n_selected})",
            disabled=(n_selected == 0),
            on_click=_on_evaluate_selected,
            args=(filtered_cases,),
            type="primary",
        )
        st.button(
            f"Evaluate All Filtered ({n_filtered})",
            disabled=(n_filtered == 0),
            on_click=_on_evaluate_filtered,
            args=(filtered_cases,),
        )

    # --- Results ---
    result = st.session_state.get("eval_results")
    if result is not None:
        st.divider()
        if "error" in result:
            st.error(f"Scoring failed: {result['error']}")
        else:
            eval_results: list[dict[str, Any]] = result.get("results", [])
            errors: dict[str, str] = result.get("errors", {})
            skipped: list[str] = result.get("skipped", [])
            n_ok = len(eval_results)
            n_fail = len(errors)
            n_skip = len(skipped)

            if n_fail == 0 and n_skip == 0:
                st.success(f"Auto-scored **{n_ok}** case(s).")
            else:
                st.warning(
                    f"{n_ok} evaluated"
                    + (f", {n_fail} failed" if n_fail else "")
                    + (f", {n_skip} skipped (not found)" if n_skip else "")
                    + "."
                )

            if eval_results:
                rows = []
                for ev in eval_results:
                    dims = ev.get("dimensions", {})
                    scored = sum(
                        1 for d in dims.values()
                        if isinstance(d, dict) and d.get("score") is not None
                    )
                    total = len(dims)
                    auto_tags = ev.get("auto_tags", [])
                    rows.append({
                        "Case ID": ev.get("case_id", ""),
                        "Dimensions Scored": f"{scored}/{total}",
                        "Auto Tags": ", ".join(auto_tags) if auto_tags else "",
                    })
                st.dataframe(rows, hide_index=True, use_container_width=True)

            if errors:
                with st.expander(f"Errors ({n_fail})"):
                    for cid, msg in errors.items():
                        st.error(f"`{cid}`: {msg}")

            if skipped:
                with st.expander(f"Skipped ({n_skip})"):
                    st.write(", ".join(f"`{s}`" for s in skipped))

    _render_run_history()


def _render_run_history() -> None:
    """Render the run history section."""
    st.divider()
    st.subheader("Run History")

    runs = list_runs()
    if not runs:
        st.info("No evaluation runs yet. Run auto-scoring above to create one.")
    else:
        run_rows = []
        for run in runs:
            started = run.get("started_at", "")[:19].replace("T", " ")
            filter_crit = run.get("filter_criteria")
            filter_summary = "all cases"
            if filter_crit:
                parts = []
                if filter_crit.get("case_ids"):
                    parts.append(f"ids: {', '.join(filter_crit['case_ids'])}")
                if filter_crit.get("failure_type"):
                    parts.append(f"failure: {filter_crit['failure_type']}")
                if filter_crit.get("severity"):
                    parts.append(f"severity: {', '.join(filter_crit['severity'])}")
                if filter_crit.get("tags"):
                    parts.append(f"tags: {', '.join(filter_crit['tags'])}")
                if filter_crit.get("pattern"):
                    parts.append(f"pattern: {filter_crit['pattern']}")
                if parts:
                    filter_summary = "; ".join(parts)
            run_rows.append({
                "Run ID": run.get("run_id", ""),
                "Status": run.get("status", ""),
                "Cases": run.get("num_cases", 0),
                "Filter": filter_summary,
                "Started": started,
            })
        st.dataframe(run_rows, use_container_width=True, hide_index=True)
