# Research: Trace Annotation & Review UI (Feature 009)

## Decision: Annotation storage location

**Decision**: `reports/{case_id}.annotations.json`
**Rationale**: Annotations are review artifacts tied to a specific case, not a specific run. Storing alongside other `reports/` artifacts (`*.evaluation.json`, `*.auto_evaluation.json`) keeps all case-level review data together and matches the existing pattern.
**Alternatives considered**:
- `data/cases/{case_id}/annotations.json` — rejected: dataset validator would scan and potentially flag annotation content; case directories are for benchmark inputs only.
- `runs/{run_id}/{case_id}.annotations.json` — rejected: annotations should persist across runs; tying them to a run would lose them when the run is not selected.

---

## Decision: Auto-evaluation source for overlay

**Decision**: Check `reports/{case_id}.auto_evaluation.json` first; fall back to the most recent run directory containing `{case_id}.auto_evaluation.json`.
**Rationale**: The `reports/` directory is the canonical output of `agenteval-auto-score` CLI. Run-directory auto_evaluations from the UI are equally valid but secondary. Checking `reports/` first is consistent with `load_evaluation_template()`.
**Alternatives considered**:
- Only `reports/` — too restrictive; UI-driven scoring (via `run_selective_evaluation`) writes to the run directory.
- Only latest run — ignores CLI-scored results; inconsistent with existing service layer patterns.

---

## Decision: reviewer_id source

**Decision**: Simple text input in the UI with a sensible default (system username via `os.getlogin()` with fallback to `"reviewer"`).
**Rationale**: No authentication exists in the framework; a lightweight string identifier is sufficient for lab/team use. Matches the spirit of the spec without adding an auth dependency.
**Alternatives considered**:
- Hardcoded "reviewer" — too opaque for multi-user scenarios.
- Full user profile system — out of scope; adds complexity with no corresponding value at this stage.

---

## Decision: evidence_step_ids overlay behaviour with empty arrays

**Decision**: When `evidence_step_ids` is empty for a dimension, show the dimension's score and notes at the *case level* (sidebar/expander) rather than on a specific step. When populated, show the dimension badge on the referenced step.
**Rationale**: Current rule-based evaluators (`ToolUseEvaluator`, `SecurityEvaluator`) leave `evidence_step_ids` empty. The overlay must be useful now while being future-ready for LLM evaluators that will populate step-level evidence.
**Alternatives considered**:
- Show nothing when evidence is empty — hides scoring context from reviewers entirely.
- Distribute score to all steps — misleading; implies all steps caused the score.

---

## Decision: Step-level diff view scope

**Decision**: Defer to a future iteration. Implement US1 (annotations), US2 (auto-score overlay), and US3 (evidence linking) in this feature. US4 (diff view) is P3 and requires trace versioning infrastructure that doesn't yet exist.
**Rationale**: The diff view requires two traces for the same case from different runs, which is only meaningful when agents actually produce different outputs. With fixed test fixtures, the diff would always be empty. The value is low until real agent iteration is supported.
**Alternatives considered**:
- Implement diff view now — adds significant complexity for near-zero practical value in the current dataset.

---

## Decision: "Jump to step" navigation in Streamlit

**Decision**: Use `st.session_state` to set a `highlighted_step` key; steps check this key and render with a visible highlight (colored container border) when selected. No anchor/scroll manipulation needed.
**Rationale**: Streamlit does not expose native anchor scrolling. Session-state-driven highlighting is idiomatic Streamlit, testable, and reliable across browser environments.
**Alternatives considered**:
- JavaScript `window.scrollTo` via `st.components.v1.html` — fragile, depends on DOM structure, unmaintainable.
- Anchor links with `st.markdown` HTML — not supported in Streamlit's sandbox mode.
