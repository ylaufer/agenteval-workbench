"""Rubric Builder page for AgentEval Workbench.

Allows users to create and save custom evaluation rubrics from a UI without
editing raw YAML/JSON. Supports template-based creation, dimension management
(add/remove/reorder via expanders), JSON/YAML preview, schema validation, and
auto-versioned save.
"""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agenteval.core.rubric_builder import SCALE_KEYS
import agenteval.core.service as service


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------


def _init_state() -> None:
    """Initialize all session state keys used by this page."""
    st.session_state.setdefault("rubric_dims", [])
    st.session_state.setdefault("rubric_template_source", None)
    st.session_state.setdefault("rubric_name", "")
    st.session_state.setdefault("rubric_description", "")
    st.session_state.setdefault("rubric_valid", None)  # None=unchecked, True/False
    st.session_state.setdefault("rubric_validate_errors", [])
    st.session_state.setdefault("rubric_save_msg", None)


def _blank_dimension() -> dict[str, Any]:
    return {
        "name": "",
        "title": "",
        "scale": "0-2",
        "weight": 1.0,
        "description": "",
        "evidence_required": True,
        "scoring_guide": {"0": "", "1": "", "2": ""},
    }


def _init_dim_widgets(dims: list[dict[str, Any]]) -> None:
    """Pre-populate session state widget keys from dims list (use setdefault, not overwrite)."""
    for i, dim in enumerate(dims):
        st.session_state.setdefault(f"dim_{i}_name", dim.get("name", ""))
        st.session_state.setdefault(f"dim_{i}_title", dim.get("title", ""))
        st.session_state.setdefault(f"dim_{i}_description", dim.get("description", ""))
        st.session_state.setdefault(f"dim_{i}_scale", dim.get("scale", "0-2"))
        st.session_state.setdefault(f"dim_{i}_weight", float(dim.get("weight", 1.0)))
        st.session_state.setdefault(f"dim_{i}_evidence", bool(dim.get("evidence_required", True)))
        sg = dim.get("scoring_guide", {})
        scale = dim.get("scale", "0-2")
        for k in SCALE_KEYS.get(scale, []):
            st.session_state.setdefault(f"dim_{i}_sg_{k}", sg.get(k, ""))


def _flush_dims_from_widgets() -> None:
    """Sync all dimension widget values back into st.session_state['rubric_dims']."""
    dims = st.session_state["rubric_dims"]
    for i in range(len(dims)):
        scale = st.session_state.get(f"dim_{i}_scale", dims[i].get("scale", "0-2"))
        sg: dict[str, str] = {}
        for k in SCALE_KEYS.get(scale, []):
            sg[k] = st.session_state.get(f"dim_{i}_sg_{k}", "")
        dims[i] = {
            "name": st.session_state.get(f"dim_{i}_name", ""),
            "title": st.session_state.get(f"dim_{i}_title", ""),
            "scale": scale,
            "weight": float(st.session_state.get(f"dim_{i}_weight", 1.0)),
            "description": st.session_state.get(f"dim_{i}_description", ""),
            "evidence_required": bool(st.session_state.get(f"dim_{i}_evidence", True)),
            "scoring_guide": sg,
        }


def _clear_dim_widgets() -> None:
    """Remove all dim_* widget keys so they are rebuilt from dims list on next render."""
    for k in list(st.session_state.keys()):
        if k.startswith("dim_"):
            del st.session_state[k]


def _invalidate_validation() -> None:
    """Mark validation state as stale."""
    st.session_state["rubric_valid"] = None
    st.session_state["rubric_validate_errors"] = []
    st.session_state["rubric_save_msg"] = None


def _build_rubric_dict() -> dict[str, Any]:
    """Build a rubric dict from current session state widget values."""
    n = len(st.session_state.get("rubric_dims", []))
    dims: list[dict[str, Any]] = []
    for i in range(n):
        scale = st.session_state.get(f"dim_{i}_scale", "0-2")
        sg: dict[str, str] = {}
        for k in SCALE_KEYS.get(scale, []):
            sg[k] = st.session_state.get(f"dim_{i}_sg_{k}", "")
        dim: dict[str, Any] = {
            "name": st.session_state.get(f"dim_{i}_name", ""),
            "scale": scale,
            "description": st.session_state.get(f"dim_{i}_description", ""),
            "scoring_guide": sg,
        }
        title = st.session_state.get(f"dim_{i}_title", "")
        if title:
            dim["title"] = title
        dim["weight"] = float(st.session_state.get(f"dim_{i}_weight", 1.0))
        dim["evidence_required"] = bool(st.session_state.get(f"dim_{i}_evidence", True))
        dims.append(dim)

    rubric: dict[str, Any] = {
        "version": "draft",
        "dimensions": dims,
    }
    name = st.session_state.get("rubric_name", "")
    if name:
        rubric["name"] = name
    desc = st.session_state.get("rubric_description", "")
    if desc:
        rubric["description"] = desc
    return rubric


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


def _on_template_change() -> None:
    template_id = st.session_state.get("rubric_template_selector")
    if not template_id or template_id == "Blank":
        st.session_state["rubric_dims"] = [_blank_dimension()]
        st.session_state["rubric_template_source"] = None
    else:
        try:
            template = service.load_rubric_template(template_id)
            dims: list[dict[str, Any]] = []
            for d in template.get("dimensions", []):
                dims.append({
                    "name": d.get("name", ""),
                    "title": d.get("title", ""),
                    "scale": d.get("scale", "0-2"),
                    "weight": float(d.get("weight", 1.0)),
                    "description": d.get("description", ""),
                    "evidence_required": bool(d.get("evidence_required", True)),
                    "scoring_guide": dict(d.get("scoring_guide", {})),
                })
            st.session_state["rubric_dims"] = dims
            st.session_state["rubric_template_source"] = template_id
            # Pre-fill rubric name from template if currently blank
            if not st.session_state.get("rubric_name"):
                st.session_state["rubric_name"] = template_id
        except Exception:
            st.session_state["rubric_dims"] = [_blank_dimension()]
            st.session_state["rubric_template_source"] = None
    _clear_dim_widgets()
    _invalidate_validation()


def _on_move_up(i: int) -> None:
    _flush_dims_from_widgets()
    dims = st.session_state["rubric_dims"]
    dims[i - 1], dims[i] = dims[i], dims[i - 1]
    _clear_dim_widgets()
    _invalidate_validation()


def _on_move_down(i: int) -> None:
    _flush_dims_from_widgets()
    dims = st.session_state["rubric_dims"]
    dims[i], dims[i + 1] = dims[i + 1], dims[i]
    _clear_dim_widgets()
    _invalidate_validation()


def _on_remove(i: int) -> None:
    _flush_dims_from_widgets()
    st.session_state["rubric_dims"].pop(i)
    _clear_dim_widgets()
    _invalidate_validation()


def _on_add_dimension() -> None:
    _flush_dims_from_widgets()
    st.session_state["rubric_dims"].append(_blank_dimension())
    _invalidate_validation()


def _on_validate() -> None:
    rubric = _build_rubric_dict()
    is_valid, errors = service.validate_rubric(rubric)
    st.session_state["rubric_valid"] = is_valid
    st.session_state["rubric_validate_errors"] = errors
    st.session_state["rubric_save_msg"] = None


def _on_save() -> None:
    name = st.session_state.get("rubric_name", "").strip()
    rubric = _build_rubric_dict()
    try:
        path = service.save_rubric(name, rubric)
        st.session_state["rubric_save_msg"] = ("success", str(path))
        st.session_state["rubric_valid"] = None  # require re-validate after save
    except Exception as exc:
        st.session_state["rubric_save_msg"] = ("error", str(exc))


# ---------------------------------------------------------------------------
# YAML preview (stdlib only, no pyyaml)
# ---------------------------------------------------------------------------


def _rubric_to_yaml_preview(rubric: dict[str, Any]) -> str:
    """Convert rubric dict to YAML-like text using stdlib only.

    Handles the known rubric structure: shallow dicts with str/int/float/bool/list values.
    Not a general-purpose YAML serializer — output is functionally correct for rubrics.
    """

    def _scalar(v: Any) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, float):
            return f"{v:g}"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str):
            if not v:
                return "''"
            if any(c in v for c in (":", "#", "[", "]", "{", "}", ",", "&", "*", "?", "|", "<", ">", "=", "!", "%", "@", "`")):
                return json.dumps(v)
            return v
        return repr(v)

    def _dict_to_lines(d: dict[str, Any], indent: int) -> list[str]:
        pad = "  " * indent
        lines: list[str] = []
        for key, val in d.items():
            if isinstance(val, dict):
                lines.append(f"{pad}{key}:")
                lines.extend(_dict_to_lines(val, indent + 1))
            elif isinstance(val, list):
                if not val:
                    lines.append(f"{pad}{key}: []")
                else:
                    lines.append(f"{pad}{key}:")
                    for item in val:
                        if isinstance(item, dict):
                            item_lines = _dict_to_lines(item, indent + 2)
                            if item_lines:
                                first_line = item_lines[0]
                                lines.append(f"{'  ' * (indent + 1)}- {first_line.lstrip()}")
                                lines.extend(item_lines[1:])
                        else:
                            lines.append(f"{'  ' * (indent + 1)}- {_scalar(item)}")
            else:
                lines.append(f"{pad}{key}: {_scalar(val)}")
        return lines

    return "\n".join(_dict_to_lines(rubric, 0))


# ---------------------------------------------------------------------------
# Dimension editor
# ---------------------------------------------------------------------------


def _render_dimension_editor(i: int, total: int) -> None:
    """Render a single dimension expander with field editor and control buttons."""
    dim_name = st.session_state.get(f"dim_{i}_name") or f"dimension_{i + 1}"
    dim_scale = st.session_state.get(f"dim_{i}_scale", "0-2")
    dim_weight = st.session_state.get(f"dim_{i}_weight", 1.0)
    label = f"{i + 1}. {dim_name}   ·   scale: {dim_scale}   ·   weight: {dim_weight}"

    with st.expander(label, expanded=False):
        # Control buttons
        col_up, col_down, col_remove, _ = st.columns([1, 1, 2, 6])
        with col_up:
            st.button("↑", key=f"dim_{i}_up", on_click=_on_move_up, args=(i,),
                      disabled=(i == 0), help="Move up")
        with col_down:
            st.button("↓", key=f"dim_{i}_down", on_click=_on_move_down, args=(i,),
                      disabled=(i == total - 1), help="Move down")
        with col_remove:
            st.button(
                "✕ Remove",
                key=f"dim_{i}_remove_btn",
                on_click=_on_remove,
                args=(i,),
                disabled=(total <= 1),
                help="Cannot remove the only dimension" if total <= 1 else "Remove this dimension",
            )

        # Name + Title
        col_name, col_title = st.columns(2)
        with col_name:
            st.text_input("Name (snake_case)", key=f"dim_{i}_name",
                          on_change=_invalidate_validation,
                          placeholder="e.g. accuracy")
        with col_title:
            st.text_input("Title (human-readable)", key=f"dim_{i}_title",
                          on_change=_invalidate_validation,
                          placeholder="e.g. Accuracy")

        st.text_area("Description", key=f"dim_{i}_description",
                     on_change=_invalidate_validation,
                     placeholder="What does this dimension measure?",
                     height=80)

        # Scale / Weight / Evidence
        col_scale, col_weight, col_evidence = st.columns(3)
        with col_scale:
            st.selectbox("Scale", options=["0-2", "1-5", "0-4"],
                         key=f"dim_{i}_scale", on_change=_invalidate_validation)
        with col_weight:
            st.number_input("Weight", min_value=0.0, step=0.1,
                            key=f"dim_{i}_weight", on_change=_invalidate_validation)
        with col_evidence:
            st.checkbox("Evidence required", key=f"dim_{i}_evidence",
                        on_change=_invalidate_validation)

        # Scoring guide — keys derived from current scale selection
        current_scale = st.session_state.get(f"dim_{i}_scale", "0-2")
        st.caption("**Scoring Guide** — one entry per score value in the selected scale")
        for k in SCALE_KEYS.get(current_scale, []):
            st.text_area(
                f"Score {k}",
                key=f"dim_{i}_sg_{k}",
                on_change=_invalidate_validation,
                height=60,
                placeholder=f"Criteria for score {k}",
            )


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------


def render() -> None:
    _init_state()
    st.title("Custom Rubric Builder")
    st.caption("Create and save custom evaluation rubrics. Start from a template or build from scratch.")

    # --- Template selector ---
    templates = service.list_rubric_templates()
    template_options = ["Blank"] + templates
    current_source = st.session_state.get("rubric_template_source")
    default_idx = (
        template_options.index(current_source)
        if current_source in template_options
        else 0
    )
    st.selectbox(
        "Start from template",
        options=template_options,
        index=default_idx,
        key="rubric_template_selector",
        on_change=_on_template_change,
        help="Load a starter template with pre-filled dimensions, or start blank.",
    )

    # Ensure at least one dimension exists
    if not st.session_state["rubric_dims"]:
        st.session_state["rubric_dims"] = [_blank_dimension()]

    # Pre-populate widget keys from dims list (only sets if not already in session state)
    _init_dim_widgets(st.session_state["rubric_dims"])

    # --- Rubric metadata ---
    col_name, col_desc = st.columns([2, 3])
    with col_name:
        st.text_input(
            "Rubric Name",
            key="rubric_name",
            placeholder="e.g. my_rag_rubric",
            help="snake_case identifier — used as the filename base (e.g. v1_my_rag_rubric.json)",
            on_change=_invalidate_validation,
        )
    with col_desc:
        st.text_input(
            "Description (optional)",
            key="rubric_description",
            placeholder="Brief description of this rubric",
            on_change=_invalidate_validation,
        )

    st.divider()

    # --- Dimension list ---
    dims = st.session_state["rubric_dims"]
    st.subheader(f"Dimensions ({len(dims)})", anchor=False)

    for i in range(len(dims)):
        _render_dimension_editor(i, len(dims))

    st.button("+ Add Dimension", on_click=_on_add_dimension,
              help="Append a new blank dimension")

    st.divider()

    # --- Preview (JSON + YAML) ---
    st.subheader("Preview", anchor=False)
    rubric_preview = _build_rubric_dict()
    tab_json, tab_yaml = st.tabs(["JSON", "YAML"])
    with tab_json:
        st.code(json.dumps(rubric_preview, indent=2), language="json")
    with tab_yaml:
        st.code(_rubric_to_yaml_preview(rubric_preview), language="yaml")

    st.divider()

    # --- Validate & Save ---
    st.subheader("Validate & Save", anchor=False)

    col_v, col_s = st.columns(2)
    with col_v:
        st.button("Validate", on_click=_on_validate, use_container_width=True)
    with col_s:
        rubric_is_valid = st.session_state.get("rubric_valid") is True
        st.button(
            "Save Rubric",
            on_click=_on_save,
            disabled=not rubric_is_valid,
            type="primary",
            use_container_width=True,
            help=(
                "Click Validate first, then Save"
                if not rubric_is_valid
                else "Save rubric to rubrics/ with auto-versioned filename"
            ),
        )

    # Validation feedback
    valid_state = st.session_state.get("rubric_valid")
    if valid_state is True:
        st.success("Rubric is valid ✓")
    elif valid_state is False:
        errors = st.session_state.get("rubric_validate_errors", [])
        error_lines = "\n".join(f"- {e}" for e in errors) if errors else "(unknown error)"
        st.error(f"Validation failed:\n{error_lines}")

    # Save feedback
    save_msg = st.session_state.get("rubric_save_msg")
    if save_msg:
        kind, msg = save_msg
        if kind == "success":
            st.success(f"Saved: `{msg}`")
            st.info("The new rubric is now available in the **Evaluate** page.")
        else:
            st.error(f"Save failed: {msg}")
