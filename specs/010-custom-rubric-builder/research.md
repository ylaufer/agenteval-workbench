# Research: Custom Rubric Builder (Feature 010)

## Decision: Rubric file format and naming convention

**Decision**: Save custom rubrics as `{name}.json` in `rubrics/`. The `version` field inside the JSON follows the existing pattern (`v1_agent_general`) and is set by the user or auto-derived from the filename. Version field format: `{version_prefix}_{name}` where `version_prefix` defaults to `v1` and increments if a file with that version already exists.
**Rationale**: Consistent with existing `v1_agent_general.json` in `rubrics/`. The `load_rubric()` in `loader.py` already expects files in that directory. Auto-increment prevents silent overwrites.
**Alternatives considered**:
- Separate `rubrics/custom/` subdirectory — rejected: adds path complexity with no benefit; `load_rubric()` would need updating.
- Timestamp-based versioning — rejected: version IDs in existing data are human-readable identifiers, not timestamps; `v1_rag_pipeline` is preferable to `rubric_20260504T123456`.

---

## Decision: Scale options

**Decision**: Restrict to the three scales already in `rubric_schema.json`: `"0-2"`, `"1-5"`, `"0-4"`. Derive scoring guide slot count automatically from scale (`"0-2"` → keys 0,1,2; `"1-5"` → keys 1,2,3,4,5; `"0-4"` → keys 0,1,2,3,4).
**Rationale**: The schema already enumerates exactly these three. Allowing arbitrary scales would require a schema change (constitution §II violation). The UI can render the right number of scoring guide text areas based on the selected scale.
**Alternatives considered**:
- Allow arbitrary min/max — rejected: breaks the existing schema enum; requires backward-incompatible schema change.
- Only support `"0-2"` — rejected: existing schema already supports three scales; being more restrictive than the schema is arbitrary.

---

## Decision: Template storage format

**Decision**: Store rubric templates as JSON in `rubrics/templates/` (not YAML). Load them with the same `json.loads()` path used elsewhere; no new dependency.
**Rationale**: The rest of the codebase loads rubrics as JSON. YAML templates would require either a new dependency (`pyyaml`) or a separate loader — both unnecessary. The `.yaml` source of truth (`v1_agent_general.yaml`) is a human-authoring convenience; the canonical format is JSON.
**Alternatives considered**:
- YAML templates — rejected: would need `pyyaml` or `ruamel.yaml`; violates constitution §V (minimal dependencies).
- Hardcoded template dicts in Python — rejected: harder to maintain and update without code changes.

---

## Decision: Rubric version auto-increment strategy

**Decision**: `save_rubric(name, rubric, repo_root)` picks the next unused version prefix. It scans `rubrics/` for files matching `v*_{name}.json`, finds the highest numeric prefix, and uses `v{n+1}`. If no match, starts at `v1`.
**Rationale**: Simple, deterministic, no clock dependency. Matches existing naming (`v1_agent_general`). Keeps version IDs human-readable.
**Alternatives considered**:
- Always `v1` with overwrite — rejected: spec requires versioning to prevent orphaned eval data.
- UUID suffix — rejected: opaque; hard to reference in reports and CLI.

---

## Decision: Reorder dimensions — move up/down buttons vs drag-and-drop

**Decision**: Up/Down buttons in the UI (no drag-and-drop). Each dimension row has `↑` and `↓` buttons that swap adjacent items in the session state list.
**Rationale**: Streamlit does not support native drag-and-drop without a custom component (CCv2). Button-based reordering is idiomatic Streamlit, testable, and zero-dependency.
**Alternatives considered**:
- Drag-and-drop via CCv2 — rejected: adds significant complexity for a minor UX improvement; out of scope for this feature.
- Numbered text input for position — rejected: error-prone and awkward for small lists.

---

## Decision: Dimension editor — inline expansion vs dialog

**Decision**: Use `st.expander` per dimension for inline editing, not a modal dialog. Expand to show the full edit form; collapse to show a summary row.
**Rationale**: `st.dialog` is available in recent Streamlit but requires a trigger button and rerun coordination that is fragile when multiple dialogs could be open. Expanders are simpler, stateless, and naturally collapse when another is opened by the user.
**Alternatives considered**:
- `st.dialog` — rejected: each dialog is a separate re-render scope; managing dirty state across reruns requires significant session state bookkeeping.
- Separate "edit" page navigation — rejected: heavy for editing a single dimension field.

---

## Decision: YAML preview generation

**Decision**: Generate YAML preview in Python using `json.dumps()` converted to a simple hand-rolled YAML-like formatter, or use stdlib only. Since `pyyaml` is not a runtime dependency, write a minimal dict-to-YAML serializer for the preview — it only needs to handle the known rubric structure (flat dicts with string/number/bool/list values). Alternatively, show JSON-only preview and mark YAML preview as "coming soon".
**Decision (revised)**: Show JSON preview only. YAML preview is a nice-to-have; the spec says "preview in YAML and JSON formats" but the constitution bans new runtime dependencies. Since `pyyaml` is not installed, generate a clean YAML-like text representation using Python's stdlib — a simple recursive formatter for the known rubric structure is sufficient and can be done in ~20 lines.
**Rationale**: The rubric structure is shallow and well-known. A small stdlib formatter avoids the dependency. Output will be functionally correct even if not 100% YAML-spec-compliant edge cases.
**Alternatives considered**:
- Add `pyyaml` as optional `[ui]` extra — rejected: spec says "no new runtime dependencies"; even optional extras add maintenance burden.
- JSON-only preview — kept as fallback if the formatter produces ugly output; both tabs shown.

---

## Decision: Comparison rubric mismatch warning

**Decision**: Add a warning in `page_compare.py` (and `comparison.py`) when the two compared runs used different rubric versions. Read rubric version from `run.json` (already stored in the run record via `rubric_path`). Extract the filename stem as the version identifier.
**Rationale**: Spec requirement §7. The run record already stores `rubric_path`; extracting the stem gives `v1_agent_general`. A simple `!=` check at comparison time is sufficient.
**Alternatives considered**:
- Block comparison when rubrics differ — rejected: too restrictive; teams may want to compare even across rubric versions for research purposes. A warning is the right level of friction.
- Store rubric version hash — rejected: over-engineering; filename stem is sufficient at this stage.
