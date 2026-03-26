# Research Notes: Ingestion UI

**Feature**: Ingestion UI (012)
**Date**: 2026-03-25
**Phase**: 0 (Research)

## Research Questions

### RQ1: How to handle dataset completeness (prompt.txt, expected_outcome.md)?

**Context**: Constitution Principle VI requires every case to have `prompt.txt`, `trace.json`, and `expected_outcome.md`. The ingestion adapters only convert `trace.json`. How should the UI handle the other two required files?

**Options Evaluated**:

1. **Option A**: Create only `trace.json`, require manual addition of other files
   - **Pros**: Simple, delegates to existing workflow
   - **Cons**: Violates dataset completeness principle, case is invalid until user manually adds files

2. **Option B**: Add UI input fields for prompt and expected outcome
   - **Pros**: Creates complete case in one flow, satisfies completeness principle
   - **Cons**: Adds UI complexity, duplicates case generation workflow

3. **Option C**: Auto-generate placeholder files with prompts for user to fill
   - **Pros**: Satisfies validator, guides user to complete the case
   - **Cons**: Creates "fake" complete cases that aren't actually filled in

**Decision**: **Option C (Auto-generate placeholders)**

**Rationale**:
- Satisfies dataset validator (case has all 3 required files)
- Placeholder content clearly marks what needs to be filled: `[TODO: Add prompt text]`
- Follows existing pattern from case generator (`agenteval-generate-case`)
- User can complete via Inspect page or text editor afterward
- Maintains single responsibility: ingestion focuses on trace conversion, not prompt authoring

**Implementation**:
- Service layer `ingest_trace()` creates all 3 files:
  - `trace.json` — converted from uploaded file
  - `prompt.txt` — placeholder: `[TODO: Add the agent prompt that produced this trace]`
  - `expected_outcome.md` — placeholder with YAML front matter template

---

### RQ2: Should the UI support editing prompt/expected outcome during ingestion?

**Decision**: **No, defer to future feature**

**Rationale**:
- Feature scope is trace conversion + preview + save (spec FR-001 through FR-016)
- Editing prompt/outcome is orthogonal to ingestion
- Future feature (009: Trace Annotation Review UI) may add full case editing
- Placeholder approach (RQ1) provides clear path for users to complete cases

---

### RQ3: How to handle Generic adapter mapping config in the UI?

**Context**: Generic adapter requires a YAML/JSON mapping config file. Should this be a separate upload, inline editor, or preset selector?

**Options Evaluated**:

1. **Option A**: Separate file upload widget (appears when Generic selected)
2. **Option B**: Inline YAML editor with validation
3. **Option C**: Preset mapping configs (e.g., "AgentOps", "Custom Framework")

**Decision**: **Option A (Separate file upload)**

**Rationale**:
- Matches existing CLI workflow (`agenteval-ingest --adapter generic --mapping config.yaml`)
- Users likely have mapping configs saved from CLI usage
- Simpler than building inline editor
- Presets don't cover custom frameworks (would need fallback to upload anyway)

**Implementation**:
- When user selects "Generic" from adapter dropdown → show second file uploader
- Validate mapping config before allowing preview generation
- Block save button if mapping not provided (spec FR-005)

---

### RQ4: Bulk ZIP upload — should we extract to temp directory or process in-memory?

**Context**: User uploads ZIP with multiple JSON files. How should we process it?

**Options Evaluated**:

1. **Option A**: Extract ZIP to temp directory, process files, delete temp dir
2. **Option B**: Process ZIP entries in-memory using `zipfile.ZipFile`

**Decision**: **Option B (In-memory processing)**

**Rationale**:
- No temp file cleanup required
- Faster for small-to-medium ZIPs (<50MB hard limit applies to individual files)
- Avoids filesystem permission issues
- Python stdlib `zipfile` module supports in-memory extraction

**Implementation**:
```python
import zipfile
from io import BytesIO

with zipfile.ZipFile(BytesIO(uploaded_file.read())) as zf:
    for entry in zf.namelist():
        if entry.endswith('.json'):
            content = zf.read(entry)
            # Process JSON content
```

---

### RQ5: Should auto-detection try all adapters or stop at first match?

**Context**: Existing `auto_detect_adapter()` returns first match. Should UI behavior differ?

**Decision**: **Use existing behavior (first match)**

**Rationale**:
- Registry order already prioritizes more specific adapters (OTel, LangChain, CrewAI) before generic ones
- User can manually override if auto-detection picks wrong adapter (spec FR-004)
- Trying all adapters and showing ambiguity adds complexity without clear value

**Implementation**:
- Call `ingestion.auto_detect_adapter(raw)` as-is
- If no match → show error + manual adapter dropdown
- If match → show detected format + option to manually override

---

## Technology Decisions

### TD1: Streamlit UI Patterns

**Pattern**: Use existing component library from Feature 006 (Guided Onboarding)

**Components to Reuse**:
- `components/help_section.py` — Collapsible contextual help
- `components/tooltip.py` — Inline tooltips for form fields
- Session state management patterns from `onboarding/first_run.py`

**New Components Needed**:
- None (standard Streamlit widgets sufficient)

---

### TD2: Service Layer API Design

**Pattern**: Follow existing service.py conventions

**New Functions**:

```python
def get_next_case_id() -> str:
    """Return next available case ID (e.g., 'case_042')."""
    # Scan data/cases/, find max N, return case_{N+1}

def ingest_trace(
    raw_content: dict,
    adapter_name: str = "auto",
    mapping_config: dict | None = None,
    output_case_id: str | None = None
) -> dict:
    """Convert trace and create case directory with all 3 required files.

    Returns: {
        "case_id": "case_042",
        "trace_path": "data/cases/case_042/trace.json",
        "warnings": [...],
        "step_count": 12,
        "step_types": {"thought": 3, "tool_call": 5, ...}
    }
    """

def ingest_bulk(
    zip_bytes: bytes,
    adapter_name: str = "auto",
    mapping_config: dict | None = None,
    start_case_id: int | None = None
) -> list[dict]:
    """Process ZIP file and return per-file results.

    Returns: [
        {"filename": "trace1.json", "status": "converted", "case_id": "case_042", ...},
        {"filename": "trace2.json", "status": "failed", "error": "..."},
        {"filename": "readme.txt", "status": "skipped", "reason": "not JSON"}
    ]
    """
```

---

## Open Questions

**None.** All design decisions resolved.

---

## References

- Constitution Principle VI: Dataset Completeness
- Constitution Principle VIII: Library-First Architecture
- Feature 005: Trace Ingestion Adapters (existing module)
- Feature 006: Guided Onboarding (UI component patterns)
- Existing service layer: `src/agenteval/core/service.py`
