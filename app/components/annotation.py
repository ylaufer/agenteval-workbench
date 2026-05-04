"""Streamlit annotation widgets for trace step reviewer notes."""
from __future__ import annotations

import os

import streamlit as st

_SEVERITY_BADGES = {
    "none": ":gray-badge[none]",
    "low": ":blue-badge[low]",
    "medium": ":orange-badge[medium]",
    "high": ":red-badge[high]",
}

_SEVERITY_OPTIONS = ["none", "low", "medium", "high"]


def _default_reviewer() -> str:
    """Return reviewer name from session state or system username."""
    stored = st.session_state.get("inspect_reviewer_id")
    if stored:
        return stored
    try:
        return os.getlogin()
    except OSError:
        return "reviewer"


def render_annotation_form(case_id: str, step_id: str) -> None:
    """Render an Add Note form for a specific trace step.

    On save, calls service.add_annotation() and clears the annotation cache
    for this case so the list refreshes on next rerun.
    """
    from agenteval.core import service

    form_key = f"ann_form_{case_id}_{step_id}"
    with st.form(key=form_key, clear_on_submit=True):
        reviewer = st.text_input(
            "Your name",
            value=_default_reviewer(),
            key=f"ann_reviewer_{case_id}_{step_id}",
        )
        content = st.text_area(
            "Note",
            placeholder="Describe the issue or observation…",
            key=f"ann_content_{case_id}_{step_id}",
        )
        severity = st.selectbox(
            "Severity",
            options=_SEVERITY_OPTIONS,
            key=f"ann_severity_{case_id}_{step_id}",
        )
        submitted = st.form_submit_button(":material/save: Save Note", type="primary")

    if submitted:
        reviewer_val = reviewer.strip()
        content_val = content.strip()
        if not reviewer_val:
            st.error("Reviewer name is required.")
            return
        if not content_val:
            st.error("Note content is required.")
            return
        try:
            service.add_annotation(
                case_id=case_id,
                step_id=step_id,
                reviewer_id=reviewer_val,
                content=content_val,
                severity=severity,
            )
            # Persist reviewer name across session
            st.session_state["inspect_reviewer_id"] = reviewer_val
            # Invalidate annotation cache for this case
            cache_key = f"annotations_{case_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.success("Note saved.")
            st.rerun()
        except ValueError as exc:
            st.error(f"Could not save note: {exc}")


def render_annotation_list(
    annotations: list[dict],  # type: ignore[type-arg]
    case_id: str,
) -> None:
    """Display existing annotations inline with Delete buttons.

    Args:
        annotations: List of annotation dicts (from service.get_annotations).
        case_id: Case ID used to invalidate the cache after delete.
    """
    from agenteval.core import service

    if not annotations:
        return

    for ann in annotations:
        ann_id = ann["annotation_id"]
        reviewer = ann.get("reviewer_id", "?")
        timestamp = ann.get("timestamp", "")[:19].replace("T", " ")
        content = ann.get("content", "")
        severity = ann.get("severity", "none")
        badge = _SEVERITY_BADGES.get(severity, ":gray-badge[?]")

        col_text, col_btn = st.columns([10, 1])
        with col_text:
            st.markdown(
                f"{badge} **{reviewer}** :small[{timestamp} UTC]  \n{content}"
            )
        with col_btn:
            if st.button(
                ":material/delete:",
                key=f"del_ann_{ann_id}",
                help="Delete this note",
            ):
                service.delete_annotation(case_id, ann_id)
                cache_key = f"annotations_{case_id}"
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                st.rerun()
