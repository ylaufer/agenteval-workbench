"""Demo flow orchestration."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from agenteval.core.service import (
    generate_case,
    generate_summary_report,
    run_evaluation,
    validate_dataset,
)
from utils.preferences import save_preferences


def run_demo_workflow() -> None:
    """Execute the full demo workflow with progress tracking.

    Uses st.status for smooth progress updates.
    Handles errors with retry option.
    Always overwrites case_demo_001 if it exists.
    """
    demo_case_id = "demo_001"

    with st.status("Running demo workflow...", expanded=True) as status:
        try:
            # Stage 1: Generate (0-25%)
            status.update(label="Generating demo case...", state="running")
            st.session_state.demo_status = {
                "step": "generate",
                "progress": 0.0,
                "message": "Generating case with tool hallucination failure...",
                "error": None,
            }

            generate_case(
                case_id=demo_case_id,
                failure_type="tool_hallucination",
                overwrite=True,  # T017: Always overwrite case_demo_001
            )

            # Stage 2: Validate (25-50%)
            status.update(label="Validating dataset...", state="running")
            st.session_state.demo_status["step"] = "validate"
            st.session_state.demo_status["progress"] = 0.25
            st.session_state.demo_status[
                "message"
            ] = "Validating dataset structure and security..."

            result = validate_dataset()  # Uses default: repo_root/data/cases
            if not result.ok:
                raise RuntimeError(f"Validation failed: {result.issues[0].message}")

            # Stage 3: Evaluate (50-75%)
            status.update(label="Running evaluation...", state="running")
            st.session_state.demo_status["step"] = "evaluate"
            st.session_state.demo_status["progress"] = 0.50
            st.session_state.demo_status[
                "message"
            ] = "Evaluating trace against rubric dimensions..."

            run_evaluation()  # Uses defaults

            # Stage 4: Report (75-100%)
            status.update(label="Generating report...", state="running")
            st.session_state.demo_status["step"] = "report"
            st.session_state.demo_status["progress"] = 0.75
            st.session_state.demo_status[
                "message"
            ] = "Aggregating results into summary report..."

            generate_summary_report()  # Uses defaults

            # Complete
            status.update(label="✓ Demo Complete!", state="complete")
            st.session_state.demo_status["step"] = "complete"
            st.session_state.demo_status["progress"] = 1.0
            st.session_state.demo_status["message"] = "Demo completed successfully!"

            # Mark completion in preferences
            st.session_state.preferences["demo_completed_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            save_preferences(st.session_state.preferences)

        except Exception as e:
            # T016: Error handling with retry option
            status.update(label="Demo failed", state="error")
            st.session_state.demo_status["error"] = str(e)
            st.error(f"**Demo Error**: {e}")

            if st.button("Retry Demo"):
                # Clear error and restart (reuses same case ID per clarification Q3)
                st.session_state.demo_status["error"] = None
                st.rerun()

        finally:
            st.session_state.demo_in_progress = False


def show_demo_completion_message() -> None:
    """Show success message after demo completes."""
    st.success("**✓ Demo Complete!**")

    st.markdown(
        """
    View your results:
    • Navigate to the **Report** page to see aggregated metrics
    • Check the **Inspect** page to browse the demo trace
    • Visit the **Evaluate** page to run more evaluations
    """
    )

    if st.button("Go to Report", type="primary"):
        st.switch_page("app/page_report.py")
