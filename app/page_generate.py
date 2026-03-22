"""Generate & Validate page for AgentEval Workbench UI."""
from __future__ import annotations

import streamlit as st

from agenteval.core.service import generate_case, validate_dataset
from agenteval.dataset.generator import VALID_FAILURE_TYPES


def _display_validation_issues(
    issues: tuple,  # type: ignore[type-arg]
    highlight_case_id: str | None = None,
) -> None:
    """Display validation issues, optionally highlighting a specific case."""
    if not issues:
        st.success("No validation issues found.")
        return

    if highlight_case_id:
        new_case_issues = [i for i in issues if i.case_id == highlight_case_id]
        other_issues = [i for i in issues if i.case_id != highlight_case_id]
    else:
        new_case_issues = []
        other_issues = list(issues)

    def _render_issues(issue_list: list) -> None:  # type: ignore[type-arg]
        errors = [i for i in issue_list if i.severity == "error"]
        warnings = [i for i in issue_list if i.severity == "warning"]
        for issue in errors:
            st.error(f"**{issue.case_id}** — `{issue.file_path}`: {issue.message}")
        for issue in warnings:
            st.warning(f"**{issue.case_id}** — `{issue.file_path}`: {issue.message}")

    if new_case_issues:
        st.subheader(f"Issues for `{highlight_case_id}`")
        _render_issues(new_case_issues)

    if other_issues:
        if highlight_case_id:
            with st.expander(f"Other issues ({len(other_issues)})", expanded=False):
                _render_issues(other_issues)
        else:
            _render_issues(other_issues)


def render() -> None:
    """Render the Generate & Validate page."""
    st.header("Generate & Validate Cases")

    # --- Generate Case section ---
    st.subheader("Generate a Benchmark Case")

    case_id = st.text_input(
        "Case ID (leave blank for auto-generated)",
        value="",
        help="Directory name for the case under data/cases/",
    )
    case_id_value = case_id.strip() if case_id.strip() else None

    failure_options = ["(None — generic case)"] + [ft for ft in VALID_FAILURE_TYPES]
    failure_selection = st.selectbox("Failure Type", failure_options)
    failure_type = None if failure_selection.startswith("(None") else failure_selection

    overwrite = st.checkbox("Overwrite if case exists", value=False)

    if st.button("Generate Case"):
        try:
            case_path = generate_case(
                case_id=case_id_value,
                failure_type=failure_type,
                overwrite=overwrite,
            )
            st.success(f"Case created at `{case_path}`")

            # Auto-validate after generation
            with st.spinner("Validating dataset..."):
                result = validate_dataset()

            generated_id = case_path.name
            if result.ok:
                st.success("Dataset validation passed.")
            else:
                _display_validation_issues(result.issues, highlight_case_id=generated_id)

        except ValueError as exc:
            msg = str(exc)
            if "already exists" in msg:
                st.warning(f"{msg}\n\nEnable the **Overwrite** checkbox to replace it.")
            elif "Invalid failure_type" in msg:
                st.error(f"{msg}")
            else:
                st.error(f"Generation failed: {msg}")

    # --- Validate Dataset section ---
    st.divider()
    st.subheader("Validate Dataset")

    if st.button("Validate Dataset"):
        with st.spinner("Validating dataset..."):
            result = validate_dataset()

        if result.ok:
            st.success("Dataset validation passed.")
        else:
            _display_validation_issues(result.issues)
