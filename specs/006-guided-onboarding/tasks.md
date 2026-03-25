---

description: "Task list for Guided Onboarding feature implementation"
---

# Tasks: Guided Onboarding

**Input**: Design documents from `/specs/006-guided-onboarding/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-contract.md

**Tests**: No test tasks included - feature spec does not request TDD approach. Manual QA and testing will be performed during implementation.

**Organization**: Tasks are grouped by capability (user story) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Single project layout: `app/`, `tests/`, `docs/` at repository root
- Paths shown below use absolute paths from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [X] T001 Create app/components/ directory with __init__.py
- [X] T002 Create app/onboarding/ directory with __init__.py
- [X] T003 Create app/utils/ directory with __init__.py
- [X] T004 Create tests/app/ directory for UI tests
- [X] T005 [P] Create docs/quick_reference_taxonomy.md placeholder
- [X] T006 [P] Create docs/quick_reference_rubric.md placeholder

**Checkpoint**: Directory structure ready for component implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and state management that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement UserPreferences data model in app/utils/preferences.py
- [X] T008 Implement preferences file I/O (load/save/validate) in app/utils/preferences.py
- [X] T009 Implement preference corruption recovery with warning banner in app/utils/preferences.py
- [X] T010 Implement first-run detection logic in app/onboarding/first_run.py
- [X] T011 Implement session state initialization in app/onboarding/first_run.py
- [X] T012 [P] Create help content definitions in app/onboarding/content.py (page help text, tooltips, tutorial steps)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - First-Run Experience (Priority: P1) 🎯 MVP

**Goal**: New users see welcome modal and can run one-click demo that completes in <60 seconds

**Independent Test**:
1. Delete ~/.agenteval/preferences.json
2. Launch `streamlit run app/app.py`
3. Verify welcome modal appears with "Run Demo" and "Skip Tutorial" buttons
4. Click "Run Demo"
5. Verify progress through Generate → Validate → Evaluate → Report (completes in ~45-60 seconds)
6. Verify success message and "Go to Report" button
7. Reload page - verify welcome modal does NOT appear again

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement welcome modal component in app/components/welcome_modal.py using st.dialog
- [X] T014 [P] [US1] Implement demo orchestration logic in app/onboarding/demo.py (generate → validate → evaluate → report workflow)
- [X] T015 [US1] Add demo progress tracking (DemoStatus state machine) in app/onboarding/demo.py
- [X] T016 [US1] Implement demo error handling with "Retry Demo" button in app/onboarding/demo.py
- [X] T017 [US1] Implement demo case overwrite logic (always use case_demo_001) in app/onboarding/demo.py
- [X] T018 [US1] Integrate welcome modal into app/app.py main entry point
- [X] T019 [US1] Add demo button and progress UI to app/app.py using st.status
- [X] T020 [US1] Wire preference persistence on demo completion/skip in app/app.py

**Checkpoint**: At this point, first-time users can see and complete demo successfully

---

## Phase 4: User Story 2 - Contextual Help System (Priority: P2)

**Goal**: Every UI page has expandable help sections and tooltips explaining key concepts

**Independent Test**:
1. Launch `streamlit run app/app.py`
2. Navigate to each page (Generate, Evaluate, Inspect, Report)
3. Verify "ℹ️ How this works" expander appears at top of each page
4. Expand help section - verify content is relevant to page
5. Hover over step type badges on Inspect page - verify tooltips appear
6. Hover over rubric dimension names on Evaluate/Report pages - verify tooltips appear
7. Toggle "Show contextual help" in Settings - verify help sections collapse by default when disabled

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement collapsible help section component in app/components/help_section.py using st.expander
- [X] T022 [P] [US2] Implement tooltip helper component in app/components/tooltip.py using help parameter
- [X] T023 [US2] Add help section to app/page_generate.py with content from app/onboarding/content.py
- [X] T024 [US2] Add help section to app/page_evaluate.py with content from app/onboarding/content.py
- [X] T025 [US2] Add help section to app/page_inspect.py with content from app/onboarding/content.py
- [X] T026 [US2] Add help section to app/page_report.py with content from app/onboarding/content.py
- [ ] T027 [US2] Add tooltips to step type badges in app/page_inspect.py (thought, tool_call, observation, final_answer)
- [ ] T028 [US2] Add tooltips to rubric dimensions in app/page_evaluate.py (6 dimensions)
- [ ] T029 [US2] Add tooltips to score indicators in app/page_report.py (score 0/1/2 meanings)
- [X] T030 [US2] Add "Show contextual help" toggle to Settings in app/app.py sidebar
- [X] T031 [US2] Wire help visibility preference to session state in app/app.py

**Checkpoint**: All UI pages have contextual help and tooltips

---

## Phase 5: User Story 3 - Interactive Walkthrough Mode (Priority: P3)

**Goal**: Users can activate step-by-step tutorial that guides through each page with read-only navigation

**Independent Test**:
1. Launch app and skip welcome modal
2. Enable "Tutorial mode" checkbox in Settings sidebar
3. Verify tutorial UI appears with "Step 1 of 5" progress indicator
4. Click "Next" button without executing actions - verify tutorial advances to Step 2
5. Navigate through all 5 steps (Welcome → Generate → Validate → Evaluate → Report)
6. Verify "Next" button always enabled (no action completion required)
7. Click "Skip Tutorial" - verify tutorial mode exits and preference saved
8. Reload app - verify tutorial does not auto-start

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement tutorial navigation UI in app/app.py (progress bar, step counter, Next/Back buttons)
- [X] T033 [US3] Implement tutorial step tracking in session state in app/onboarding/first_run.py
- [X] T034 [US3] Add tutorial step content for Welcome (Step 1) in app/app.py using content from app/onboarding/content.py
- [X] T035 [US3] Add tutorial step content for Generate page (Step 2) in app/page_generate.py
- [X] T036 [US3] Add tutorial step content for Validate (Step 3) in app/page_generate.py
- [X] T037 [US3] Add tutorial step content for Evaluate page (Step 4) in app/page_evaluate.py
- [X] T038 [US3] Add tutorial step content for Report page (Step 5) in app/page_report.py
- [X] T039 [US3] Implement "Skip Tutorial" functionality with preference persistence in app/app.py
- [X] T040 [US3] Add "Tutorial mode" toggle to Settings sidebar in app/app.py
- [X] T041 [US3] Wire tutorial navigation (Next/Back) to session state updates in app/app.py

**Checkpoint**: Tutorial mode fully functional with read-only navigation

---

## Phase 6: User Story 4 - Quick Reference (Priority: P4)

**Goal**: Sidebar provides always-accessible reference sheets for failure taxonomy and rubric dimensions

**Independent Test**:
1. Launch app from any page
2. Scroll to sidebar
3. Expand "📖 Quick Reference" section
4. Expand "Failure Taxonomy" - verify 12 categories with descriptions appear
5. Expand "Rubric Dimensions" - verify 6 dimensions with explanations appear
6. Navigate to different page - verify quick reference persists in sidebar
7. Click internal links (if any) - verify navigation works

### Implementation for User Story 4

- [X] T042 [P] [US4] Populate docs/quick_reference_taxonomy.md with 12 failure categories from docs/failure_taxonomy.md
- [X] T043 [P] [US4] Populate docs/quick_reference_rubric.md with 6 dimensions from rubrics/v1_agent_general.yaml
- [X] T044 [US4] Implement quick reference component in app/components/quick_reference.py (loads markdown, renders in expander)
- [X] T045 [US4] Add quick reference to app/app.py sidebar below navigation
- [X] T046 [US4] Wire quick reference to load taxonomy from docs/quick_reference_taxonomy.md
- [X] T047 [US4] Wire quick reference to load rubric from docs/quick_reference_rubric.md

**Checkpoint**: All user stories (US1-US4) should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements that affect multiple user stories

- [X] T048 [P] Add keyboard navigation for modal dismissal (Esc key) in app/components/welcome_modal.py
- [X] T049 [P] Add keyboard navigation for help section toggle (Enter/Space) in app/components/help_section.py
- [X] T050 [P] Add visible focus indicators for interactive elements in app/app.py (CSS via st.markdown)
- [X] T051 [P] Implement unit tests for preferences.py in tests/app/test_preferences.py
- [X] T052 [P] Implement unit tests for first_run.py in tests/app/test_first_run.py
- [X] T053 [P] Implement unit tests for demo.py in tests/app/test_demo.py
- [X] T054 Update README.md with guided onboarding section (how to use welcome modal, tutorial, help)
- [X] T055 Update CLAUDE.md with app/ structure and new components
- [X] T056 Run manual QA checklist from specs/006-guided-onboarding/quickstart.md (Scenarios 1-10)
- [X] T057 Verify all success criteria from specs/006-guided-onboarding/spec.md are met
- [X] T058 Run agenteval-validate-dataset to ensure demo flow works correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (First-Run Experience): Can start after Foundational - No dependencies on other stories
  - US2 (Contextual Help): Can start after Foundational - No dependencies on other stories
  - US3 (Tutorial): Can start after Foundational - No dependencies on other stories
  - US4 (Quick Reference): Can start after Foundational - No dependencies on other stories
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent - Can start after Foundational
- **User Story 2 (P2)**: Independent - Can start after Foundational (but benefits from US1 being testable)
- **User Story 3 (P3)**: Independent - Can start after Foundational (but benefits from US1, US2 being present)
- **User Story 4 (P4)**: Independent - Can start after Foundational

**NOTE**: While user stories are technically independent, implementing them in priority order (US1 → US2 → US3 → US4) provides the best user experience, as each builds on the previous capabilities.

### Within Each User Story

- Components before page integration
- Core logic before UI wiring
- Error handling after happy path
- Preference persistence after functional implementation

### Parallel Opportunities

- **Setup tasks**: T001-T006 can all run in parallel
- **Foundational tasks**: T007-T012 can run in parallel (T012 is independent)
- **User Story 1**: T013-T014 can run in parallel, then T015-T017 sequentially, then T018-T020
- **User Story 2**: T021-T022 can run in parallel, T023-T026 can run in parallel, T027-T029 can run in parallel
- **User Story 3**: T032-T033 together, then T034-T038 can run in parallel
- **User Story 4**: T042-T043 can run in parallel, then T044-T047
- **Polish tasks**: T048-T053 can all run in parallel
- **All user stories (US1-US4)**: Can be worked on in parallel by different developers after Foundational phase completes

---

## Parallel Example: User Story 1

```bash
# Launch component implementations together:
Task: "Implement welcome modal component in app/components/welcome_modal.py"
Task: "Implement demo orchestration logic in app/onboarding/demo.py"

# Then sequential integration:
Task: "Add demo progress tracking in app/onboarding/demo.py"
Task: "Implement demo error handling in app/onboarding/demo.py"
Task: "Integrate welcome modal into app/app.py"
```

## Parallel Example: User Story 2

```bash
# Launch component implementations together:
Task: "Implement collapsible help section component in app/components/help_section.py"
Task: "Implement tooltip helper component in app/components/tooltip.py"

# Then launch all page integrations together:
Task: "Add help section to app/page_generate.py"
Task: "Add help section to app/page_evaluate.py"
Task: "Add help section to app/page_inspect.py"
Task: "Add help section to app/page_report.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (~5 minutes)
2. Complete Phase 2: Foundational (~30-45 minutes)
3. Complete Phase 3: User Story 1 (~60-90 minutes)
4. **STOP and VALIDATE**: Run independent test for US1
5. Test demo flow end-to-end
6. Deploy/demo if ready

**Total MVP Effort**: ~2-3 hours for minimal viable onboarding

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~45 minutes)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! ~90 minutes)
3. Add User Story 2 → Test independently → Deploy/Demo (~60 minutes)
4. Add User Story 3 → Test independently → Deploy/Demo (~60 minutes)
5. Add User Story 4 → Test independently → Deploy/Demo (~30 minutes)
6. Add Polish → Final QA → Production ready (~60 minutes)

**Total Full Feature Effort**: ~5-6 hours for complete guided onboarding

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~45 minutes)
2. Once Foundational is done:
   - Developer A: User Story 1 (First-Run Experience)
   - Developer B: User Story 2 (Contextual Help)
   - Developer C: User Story 3 (Tutorial)
   - Developer D: User Story 4 (Quick Reference)
3. Stories complete and integrate independently
4. Team collaborates on Polish phase

**Total Parallel Effort**: ~2-3 hours wall-clock time with 4 developers

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- All UI components use existing Streamlit primitives (no custom JavaScript)
- Zero new dependencies (Streamlit already in [ui] extras)
- All functionality must work offline
- Preference file corruption handled gracefully per clarification Q2
- Demo case overwrites case_demo_001 per clarification Q3
- Tutorial is read-only (no action completion required) per clarification Q4
- Keyboard navigation for critical flows per clarification Q5
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Run quickstart.md scenarios before marking story complete
