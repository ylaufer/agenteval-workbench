"""Compare Runs page for AgentEval Workbench UI."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

import streamlit as st

from agenteval.core.runs import get_run_results
from agenteval.core.service import compare_runs, list_runs
from components.help_section import show_help_section


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_run_options() -> list[dict[str, Any]]:
    """Return all completed runs, always fresh."""
    return [r for r in list_runs() if r.get("status") == "completed"]


def _run_label(run: dict[str, Any]) -> str:
    run_id = run.get("run_id", "")
    num_cases = run.get("num_cases") or "?"
    results = get_run_results(run_id)
    scored = sum(
        1
        for rec in results
        for dim in rec.get("dimensions", {}).values()
        if dim.get("score") is not None
    )
    tag = f"{scored} scored dims" if scored else "no scores"
    return f"{run_id}  [{num_cases} cases · {tag}]"


def _do_compare(run_a_id: str, run_b_id: str) -> None:
    """Run comparison and store result in session state."""
    try:
        result = compare_runs(run_a_id, run_b_id)
        st.session_state.compare_result = asdict(result)
        st.session_state.compare_error = None
    except FileNotFoundError as exc:
        st.session_state.compare_result = None
        st.session_state.compare_error = str(exc)
    except Exception as exc:  # noqa: BLE001
        st.session_state.compare_result = None
        st.session_state.compare_error = f"Unexpected error: {exc}"


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def _render_summary(summary: dict[str, Any]) -> None:
    st.subheader("Summary", anchor=False)

    net = summary.get("net_quality_change", "unknown")
    net_color = {
        "improved": "green",
        "regressed": "red",
        "unchanged": "gray",
        "insufficient_data": "orange",
    }.get(net, "gray")
    st.markdown(f"**Net quality change:** :{net_color}[{net}]")

    delta = summary.get("overall_score_delta")
    if delta is not None:
        sign = "+" if delta > 0 else ""
        st.metric("Overall score delta", f"{sign}{delta:.3f}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Compared", summary.get("total_cases_compared", 0))
    col2.metric("Improved", summary.get("cases_improved", 0))
    col3.metric("Regressed", summary.get("cases_regressed", 0))
    col4.metric("Unchanged", summary.get("cases_unchanged", 0))
    col5.metric("New / Removed", f"{summary.get('cases_new', 0)} / {summary.get('cases_removed', 0)}")

    new_failures = summary.get("new_failure_types", [])
    resolved_failures = summary.get("resolved_failure_types", [])
    if new_failures or resolved_failures:
        col_a, col_b = st.columns(2)
        with col_a:
            if new_failures:
                st.warning("**New failure types in run B:**\n" + "\n".join(f"- {f}" for f in new_failures))
        with col_b:
            if resolved_failures:
                st.success("**Resolved failure types:**\n" + "\n".join(f"- {f}" for f in resolved_failures))


def _render_dimension_deltas(dimension_deltas: list[dict[str, Any]]) -> None:
    if not dimension_deltas:
        return
    st.subheader("Dimension Deltas", anchor=False)

    rows = []
    for d in dimension_deltas:
        mean_a = d.get("mean_score_a")
        mean_b = d.get("mean_score_b")
        mean_delta = d.get("mean_delta")
        rows.append({
            "Dimension": d.get("dimension", ""),
            "Mean A": f"{mean_a:.3f}" if mean_a is not None else "—",
            "Mean B": f"{mean_b:.3f}" if mean_b is not None else "—",
            "Δ Mean": f"{mean_delta:+.3f}" if mean_delta is not None else "—",
            "Improved": d.get("cases_improved", 0),
            "Regressed": d.get("cases_regressed", 0),
            "Unchanged": d.get("cases_unchanged", 0),
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_case_deltas(case_deltas: list[dict[str, Any]]) -> None:
    if not case_deltas:
        return
    st.subheader("Case-Level Deltas", anchor=False)

    STATUS_ORDER = {"regressed": 0, "new": 1, "improved": 2, "unchanged": 3, "removed": 4}
    sorted_deltas = sorted(case_deltas, key=lambda d: STATUS_ORDER.get(d.get("status", ""), 99))

    rows = []
    for d in sorted_deltas:
        score_a = d.get("overall_score_a")
        score_b = d.get("overall_score_b")
        overall_delta = d.get("overall_delta")
        status = d.get("status", "")
        status_icon = {
            "improved": "✅",
            "regressed": "❌",
            "unchanged": "➖",
            "new": "🆕",
            "removed": "🗑️",
        }.get(status, status)
        rows.append({
            "Case": d.get("case_id", ""),
            "Status": f"{status_icon} {status}",
            "Score A": f"{score_a:.3f}" if score_a is not None else "—",
            "Score B": f"{score_b:.3f}" if score_b is not None else "—",
            "Δ": f"{overall_delta:+.3f}" if overall_delta is not None else "—",
            "Failure A": d.get("primary_failure_a") or "—",
            "Failure B": d.get("primary_failure_b") or "—",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------


def render() -> None:
    st.title("Compare Runs")

    show_help_section(
        "compare_runs",
        "**Compare Runs** lets you diff two evaluation runs side-by-side to see which "
        "cases improved or regressed, per-dimension trends, and net quality change.",
    )

    runs = _load_run_options()
    if len(runs) < 2:
        st.info("Need at least two completed runs to compare. Go to the **Evaluate** page and run auto-scoring.")
        return

    run_ids = [r["run_id"] for r in runs]
    run_labels = {r["run_id"]: _run_label(r) for r in runs}
    label_list = [run_labels[rid] for rid in run_ids]

    st.subheader("Select Runs", anchor=False)
    col_a, col_b = st.columns(2)
    with col_a:
        idx_a = st.selectbox(
            "Baseline (Run A)",
            options=range(len(run_ids)),
            format_func=lambda i: label_list[i],
            key="compare_run_a_idx",
        )
    with col_b:
        default_b = 1 if len(run_ids) > 1 else 0
        idx_b = st.selectbox(
            "Current (Run B)",
            options=range(len(run_ids)),
            format_func=lambda i: label_list[i],
            index=default_b,
            key="compare_run_b_idx",
        )

    run_a_id = run_ids[idx_a]  # type: ignore[index]
    run_b_id = run_ids[idx_b]  # type: ignore[index]

    same_run = run_a_id == run_b_id

    clicked = st.button(
        "Compare",
        type="primary",
        disabled=same_run,
        help="Select two different runs to compare" if same_run else None,
    )
    if clicked:
        with st.spinner("Comparing…"):
            _do_compare(run_a_id, run_b_id)

    if same_run:
        st.caption("Select two different runs to enable comparison.")

    # Show cached error
    if st.session_state.get("compare_error"):
        st.error(st.session_state.compare_error)

    # Show cached result
    result = st.session_state.get("compare_result")
    if result:
        st.divider()
        st.caption(
            f"Comparison `{result.get('comparison_id', '')}` · "
            f"Run A: `{result.get('run_a', '')}` vs Run B: `{result.get('run_b', '')}`"
        )
        _render_summary(result.get("summary", {}))
        st.divider()
        _render_dimension_deltas(result.get("dimension_deltas", []))
        st.divider()
        _render_case_deltas(result.get("case_deltas", []))
