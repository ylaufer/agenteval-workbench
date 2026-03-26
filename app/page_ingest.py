"""Trace Ingestion page for AgentEval Workbench UI."""
from __future__ import annotations

import json
from typing import Any

import streamlit as st

from agenteval.core.service import get_next_case_id, ingest_trace


# File size limits (from ingestion.base module)
SOFT_LIMIT_MB = 10
HARD_LIMIT_MB = 50


def _check_file_size(file_size: int) -> tuple[bool, str | None]:
    """Check if file size is within limits.

    Returns:
        (is_valid, warning_message)
    """
    size_mb = file_size / (1024 * 1024)

    if size_mb > HARD_LIMIT_MB:
        return False, f"❌ File exceeds {HARD_LIMIT_MB} MB hard limit ({size_mb:.1f} MB). Please reduce file size."

    if size_mb > SOFT_LIMIT_MB:
        return True, f"⚠️ File exceeds {SOFT_LIMIT_MB} MB soft limit ({size_mb:.1f} MB). Conversion may be slow."

    return True, None


def _init_session_state() -> None:
    """Initialize session state variables for ingestion workflow."""
    if "ingest_uploaded_file" not in st.session_state:
        st.session_state.ingest_uploaded_file = None
    if "ingest_adapter" not in st.session_state:
        st.session_state.ingest_adapter = "auto"
    if "ingest_mapping_config" not in st.session_state:
        st.session_state.ingest_mapping_config = None
    if "ingest_preview" not in st.session_state:
        st.session_state.ingest_preview = None
    if "ingest_case_id" not in st.session_state:
        st.session_state.ingest_case_id = None


def _display_conversion_preview(preview: dict[str, Any]) -> None:
    """Display conversion preview with step count and breakdown."""
    st.subheader("Conversion Preview")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Steps", preview["step_count"])
    with col2:
        st.metric("Adapter", preview["adapter_name"])

    if preview["step_types"]:
        st.write("**Step Type Breakdown:**")
        for step_type, count in preview["step_types"].items():
            st.write(f"- `{step_type}`: {count}")

    if preview.get("warnings"):
        with st.expander("⚠️ Conversion Warnings", expanded=True):
            for warning in preview["warnings"]:
                st.warning(warning)

    if preview.get("validation_errors"):
        st.error("**Schema Validation Failed**")
        for error in preview["validation_errors"]:
            st.error(error)


def render() -> None:
    """Render the Trace Ingestion page."""
    _init_session_state()

    st.header("Ingest External Traces")
    st.write("Upload trace files from LangChain, OpenTelemetry, CrewAI, OpenAI, or custom formats.")

    # Contextual help section
    with st.expander("ℹ️ How to Use This Page", expanded=False):
        st.markdown("""
**Single File Upload:**
1. Click "Upload Trace File (JSON)" and select your trace file
2. The system will auto-detect the format (OTel, LangChain, CrewAI, OpenAI)
3. Review the conversion preview (step count, step type breakdown)
4. Choose a case ID or use the auto-suggested ID
5. Click "Save Case" to create the case directory

**What Gets Created:**
- `trace.json` — Your converted trace
- `prompt.txt` — Placeholder (you'll need to add the actual prompt)
- `expected_outcome.md` — Placeholder (you'll need to describe the failure)

**Supported Formats:**
- **OpenTelemetry (OTel)**: OTLP JSON format with spans
- **LangChain**: LangSmith run tree format
- **CrewAI**: Task execution logs
- **OpenAI**: Chat Completions API responses
- **Generic**: Custom formats (requires mapping config - coming soon)

**File Size Limits:**
- Soft limit: 10 MB (warning shown, can proceed)
- Hard limit: 50 MB (upload rejected)

**After Ingestion:**
1. Navigate to **Inspect** page to view the trace
2. Edit `prompt.txt` and `expected_outcome.md` to complete the case
3. Run **Generate > Validate Dataset** to verify completeness
        """)

    st.divider()

    # Empty state when no file uploaded
    if st.session_state.ingest_uploaded_file is None:
        st.info("📤 Upload a JSON trace file to begin")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Trace File (JSON)",
        type=["json"],
        help="Upload a trace file from your agent framework",
        key="file_uploader_widget",
    )

    # Handle file upload
    if uploaded_file is not None:
        # File size validation
        is_valid, size_warning = _check_file_size(uploaded_file.size)

        if not is_valid:
            st.error(size_warning)
            return

        if size_warning:
            st.warning(size_warning)

        # Parse JSON
        try:
            raw_content = json.load(uploaded_file)
        except json.JSONDecodeError as exc:
            st.error(f"**Invalid JSON**: {exc.msg} at position {exc.pos}")
            return

        # Store in session state
        st.session_state.ingest_uploaded_file = {
            "name": uploaded_file.name,
            "content": raw_content,
        }

    # If file is uploaded, show conversion workflow
    if st.session_state.ingest_uploaded_file is not None:
        st.divider()
        file_data = st.session_state.ingest_uploaded_file

        # Auto-detect and generate preview
        if st.session_state.ingest_preview is None:
            with st.spinner("Detecting format and generating preview..."):
                try:
                    # Call ingest_trace in dry-run mode (don't actually create case yet)
                    # We'll create a temporary preview by calling the conversion
                    from agenteval.ingestion import auto_detect_adapter

                    raw_content = file_data["content"]
                    adapter = auto_detect_adapter(raw_content)

                    if adapter is None:
                        # Format not recognized
                        st.error(
                            "⚠️ **Format not recognized.** Please select an adapter manually."
                        )
                        # Show manual adapter dropdown
                        # (This will be implemented in US2)
                    else:
                        # Auto-detection succeeded
                        adapter_name = adapter.__class__.__name__
                        converted_trace = adapter.convert(raw_content)

                        # Calculate preview stats
                        steps = converted_trace.get("steps", [])
                        step_count = len(steps)
                        step_types: dict[str, int] = {}
                        for step in steps:
                            step_type = step.get("type", "unknown")
                            step_types[step_type] = step_types.get(step_type, 0) + 1

                        st.session_state.ingest_preview = {
                            "adapter_name": f"Auto-detected: {adapter_name}",
                            "step_count": step_count,
                            "step_types": step_types,
                            "warnings": [],
                            "validation_errors": [],
                            "converted_trace": converted_trace,
                        }

                except Exception as exc:
                    st.error(f"**Conversion failed**: {str(exc)}")

        # Display preview if available
        if st.session_state.ingest_preview is not None:
            _display_conversion_preview(st.session_state.ingest_preview)

            # Case ID input
            st.divider()
            st.subheader("Save to Case Directory")

            # Auto-suggest next case ID
            if st.session_state.ingest_case_id is None:
                suggested_id = get_next_case_id()
                st.session_state.ingest_case_id = suggested_id

            case_id = st.text_input(
                "Case ID",
                value=st.session_state.ingest_case_id,
                help="Target case directory (e.g., case_042)",
            )

            # Directory existence check
            from pathlib import Path

            from agenteval.dataset.validator import _get_repo_root

            repo_root = _get_repo_root()
            case_dir = repo_root / "data" / "cases" / case_id
            dir_exists = case_dir.exists()

            if dir_exists:
                st.warning(
                    f"⚠️ Case directory `{case_id}` already exists. Files will be overwritten."
                )
                confirm_overwrite = st.checkbox(
                    "I understand this will overwrite existing files",
                    value=False,
                )
            else:
                confirm_overwrite = True  # No need to confirm if directory doesn't exist

            # Save button
            save_disabled = (
                st.session_state.ingest_preview.get("validation_errors")
                or not confirm_overwrite
            )

            if st.button(
                "Save Case",
                disabled=save_disabled,
                type="primary",
            ):
                with st.spinner("Converting and saving trace..."):
                    try:
                        # Delete existing directory if overwriting
                        if dir_exists:
                            import shutil

                            shutil.rmtree(case_dir)

                        # Call ingest_trace to create the case
                        result = ingest_trace(
                            raw_content=file_data["content"],
                            adapter_name="auto",
                            output_case_id=case_id,
                            original_filename=file_data["name"],
                        )

                        # Success message
                        st.success(
                            f"✅ **Case created successfully!**\n\n"
                            f"- **Case ID**: `{result['case_id']}`\n"
                            f"- **Steps**: {result['step_count']}\n"
                            f"- **Adapter**: {result['adapter_name']}"
                        )

                        # Link to Inspect page
                        st.info(
                            "📝 **Next steps:**\n"
                            "1. Navigate to the **Inspect** page to view the trace\n"
                            "2. Edit `prompt.txt` and `expected_outcome.md` to complete the case\n"
                            "3. Run dataset validation to verify completeness"
                        )

                        # Clear session state
                        st.session_state.ingest_uploaded_file = None
                        st.session_state.ingest_preview = None
                        st.session_state.ingest_case_id = None

                        # Trigger rerun to show clean state
                        st.rerun()

                    except FileExistsError as exc:
                        st.error(f"**Error**: {exc}")
                    except ValueError as exc:
                        # Schema validation or format errors
                        if "Schema validation failed" in str(exc):
                            st.error(f"**Schema Validation Failed**: {exc}")
                        elif "Format not recognized" in str(exc):
                            st.error(
                                f"**Format Error**: {exc}\n\n"
                                "Try selecting an adapter manually (coming in next update)."
                            )
                        else:
                            st.error(f"**Error**: {exc}")
                    except Exception as exc:
                        st.error(f"**Unexpected Error**: {exc}")
