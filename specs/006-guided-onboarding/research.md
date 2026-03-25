# Research: Guided Onboarding

## 1. First-Run Detection Strategy

**Decision**: Use Streamlit session_state + optional file-based persistence

**Rationale**:
- Streamlit session_state provides per-session storage (in-memory)
- File-based marker (~/.agenteval/first_run_complete) for cross-session persistence
- Simple, no external dependencies

**Alternatives considered**:
- Cookies: Not accessible in Streamlit without custom components
- Database: Overkill for single boolean flag
- Config file in repo: Would require git-ignored file, potential conflicts

**Implementation**: Check for file marker on app startup, write marker after demo completion

---

## 2. Welcome Modal Implementation

**Decision**: Use Streamlit's built-in dialog/modal (st.dialog) or custom expander

**Rationale**:
- Streamlit 1.22+ has native dialog support via `@st.dialog` decorator
- Fallback to custom expander with prominent positioning for older versions
- No JavaScript required

**Alternatives considered**:
- Custom HTML/JS component: Too complex, breaks offline constraint
- Third-party modal library: Adds dependency

**Implementation**: Use `@st.dialog` decorator for modal function, check Streamlit version

---

## 3. Demo Flow Orchestration

**Decision**: Programmatic workflow using existing service layer

**Rationale**:
- service.py already has generate_case(), validate_dataset(), run_evaluation(), generate_summary_report()
- Can orchestrate full pipeline in Python without CLI subprocess calls
- Progress feedback via st.progress() and st.status()

**Alternatives considered**:
- CLI subprocess calls: Less control over progress, harder to show intermediate steps
- Duplicate logic: Violates Library-First principle

**Implementation**:
```python
def run_demo():
    with st.status("Running demo...") as status:
        # Generate demo case
        status.update(label="Generating case...", state="running")
        generate_case(case_id="demo_001", failure_type="tool_hallucination")

        # Validate
        status.update(label="Validating...", state="running")
        validate_dataset()

        # Evaluate
        status.update(label="Evaluating...", state="running")
        run_evaluation(dataset_dir="data/cases", output_dir="reports")

        # Report
        status.update(label="Generating report...", state="running")
        generate_summary_report(input_dir="reports")

        status.update(label="Demo complete!", state="complete")
```

---

## 4. Contextual Help System

**Decision**: Collapsible `st.expander` components with markdown content

**Rationale**:
- Native Streamlit component, familiar UX
- Markdown support for rich formatting
- Can be placed on every page without cluttering UI

**Alternatives considered**:
- Sidebar help: Limited space, not contextual
- Separate help page: Breaks workflow, users won't find it

**Implementation**: Reusable `render_help_section(page_name)` function that loads content from `content.py`

---

## 5. Tooltip Implementation

**Decision**: Use Streamlit's built-in `help` parameter on components

**Rationale**:
- Native support: `st.metric(..., help="tooltip text")`
- Consistent with Streamlit UX patterns
- No custom CSS or JavaScript needed

**Alternatives considered**:
- Custom CSS tooltips: Requires unsafe HTML injection
- Third-party library: Adds dependency

**Implementation**: Add `help` parameter to all key UI elements (step types, rubric dimensions, scores)

---

## 6. Interactive Walkthrough Mode

**Decision**: Step-by-step guide using st.progress + highlighted content

**Rationale**:
- Can't directly highlight arbitrary UI elements in Streamlit
- Use progress indicator + descriptive text to guide users
- Skip button stores preference in session state

**Alternatives considered**:
- Driver.js or similar JS library: Breaks offline constraint, complex integration
- Full tutorial page: Less engaging than in-context guidance

**Implementation**: Optional tutorial mode triggered by URL parameter `?tutorial=true` or sidebar button

---

## 7. User Preference Persistence

**Decision**: File-based storage in ~/.agenteval/preferences.json

**Rationale**:
- Simple JSON file, easy to read/write
- Standard location for user data (~/.agenteval/)
- No database needed for small preference dict

**Alternatives considered**:
- Streamlit secrets: Not for user data
- Browser localStorage: Not accessible without JS

**Implementation**:
```python
{
  "first_run_complete": true,
  "tutorial_skipped": true,
  "show_contextual_help": true
}
```

---

## 8. Quick Reference Sidebar

**Decision**: Markdown files in docs/ + st.sidebar.expander

**Rationale**:
- Quick reference content lives in docs/ (version controlled)
- Rendered in sidebar via st.sidebar.expander
- Always accessible without leaving current page

**Alternatives considered**:
- Separate reference page: Requires navigation away from workflow
- Hardcode in Python: Harder to maintain, no markdown formatting

**Implementation**: Load `docs/quick_reference_taxonomy.md` and `docs/quick_reference_rubric.md` on demand

---

## Summary

All research items resolved with zero new dependencies. Implementation uses native Streamlit components and existing service layer. File-based persistence (~/.agenteval/) for cross-session state.
