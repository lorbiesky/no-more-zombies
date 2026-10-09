---
description: "Godot implementation and QA task template"
---

# Tasks: [FEATURE NAME]

**Lifecycle Status**: DRAFT
**Package Revision**: 1
**Input**: specs/[feature]/spec.md and plan.md
**Prerequisites**: spec.md, plan.md, and analyze result
**QA**: Required. QA owns test creation, execution and qa-report.md.

## Task Format

```text
[ID] [P?] [US#] Description with exact project path
```

- P marks tasks that can safely run in parallel on separate files.
- Use the approved story identifier, such as US1.
- Do not add behavior or scope that is absent from the approved spec.
- Test-first is not mandatory. Order tests based on the plan and dependencies.

## Phase 1: Shared Setup

Only list Godot project or resource setup required by this feature.

- [ ] T001 [P] Prepare the required scene/resource paths from plan.md

## Phase 2: User Story 1 — [TITLE] (P1)

**Goal**: [Player-facing result]
**Independent Test**: [Runnable test against the approved acceptance criteria]

### QA Tests

- [ ] T002 [P] [US1] Create gdUnit4 tests for startup, input, node interactions, signals and cleanup in tests/integration/
- [ ] T003 [P] [US1] Create UI/HUD/menu tests in tests/integration/ when specified; otherwise record N/A in qa-report.md

### Implementation

- [ ] T004 [US1] Implement the approved scene and Node behavior in scenes/ and scripts/
- [ ] T005 [US1] Connect the approved inputs, signals and presentation states
- [ ] T006 [US1] Add required teardown, failure handling and resource cleanup

### QA Execution

- [ ] T007 [US1] Run scripts/test.sh, record the tested fingerprint and all results in qa-report.md
- [ ] T008 [US1] Fix in-scope failures with DEVELOPER and rerun QA until PASS

Repeat the story phase for each approved independent user story. QA tasks must
cover each story and its regression risk.

## Final Validation

Verify all acceptance scenarios and package revision. After QA PASS, present
controls and scenarios and record the user's explicit decision in
human-playtest.md. Run $speckit-converge and record convergence.md; reopen
implementation and QA for any new tasks.

## Dependencies and Execution Order

Package approval precedes every implementation task. Required QA cases and
implementation follow the plan's dependencies. QA execution follows the
implementation it verifies. User playtest follows technical QA PASS. Converge
follows the playtest and must be repeated after convergence adds tasks.
