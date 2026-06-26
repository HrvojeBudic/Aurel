# PLAN TEMPLATE — {{P_ID}} {{TITLE}}

---

## 0. Current Canon Snapshot

Active roadmap:
Current roadmap section:
Last completed task:
Current expected task:
Relevant latest report:
Known repo state:
Known validation baseline:
Known blockers:

Canonical sources read:
- [ ] agent/ACTIVE_TASK.md
- [ ] agent/ROADMAP.md
- [ ] agent/STATE.md
- [ ] agent/TESTS.md
- [ ] agent/REPORTS.md
- [ ] latest agent/reports/
- [ ] agent/ARCHITECTURE.md (if needed)
- [ ] agent/DECISIONS.md (if needed)

---

## 1. Mission Summary

**Problem:** {{MISSION_PROBLEM}}

**Goal:** {{GOAL}}

**Operator value:** {{OPERATOR_VALUE}}

**Smallest correct scope:** {{SMALLEST_CORRECT_SCOPE}}

---

## 2. Roadmap Position

Roadmap version: AUREL Roadmap v5.1 — Integration-First Roadmap

Completed: {{COMPLETED_TASKS}}

Current: {{P_ID}} — {{TITLE}}

Next expected: {{NEXT_TASK}}

---

## 3. Section Context

Section: {{SECTION_ID}} — {{SECTION_TITLE}}

Section status: {{OPEN_IN_PROGRESS_SEALED}}

Dependencies: {{DEPENDENCIES}}

---

## 4. Core Law

- CodeOps is not a new tree; `agent/` remains governance source of truth.
- Prompt is an execution contract.
- Operator selects tool/model at dispatch time. CodeOps does not route models.
- No duplicate state, validation, evidence, or decision surfaces.
- Integration-first over isolated backend-only patches.
- Evidence over confidence.
- Clean git is part of done.

---

## 5. CodeOps Classification

| Field | Value |
|---|---|
| Task Pattern | {{PATTERN}} |
| Execution Mode | {{DOCS_ONLY_LEAN_ELEVATED_FULL_SEAL}} |
| Risk Tier | {{LOW_MEDIUM_HIGH_CRITICAL}} |
| Parallel Safety | {{SAFE_NOT_SAFE_SEQUENTIAL_ONLY}} |
| Validation Depth | {{DOCS_ONLY_LEAN_ELEVATED_FULL_SEAL}} |
| Review Needed | {{OMNI_REVIEW_ADVERSARIAL_INTEGRATION_SEAL_NONE}} |
| Dispatch Note | Operator selects tool/model at dispatch time. |

---

## 6. Integration-First Slice

| Layer | This task | Truth label |
|---|---|---|
| Backend capability | {{YES_NO_OR_UNAVAILABLE}} | {{LABEL}} |
| Versioned contract/schema | {{YES_NO_OR_UNAVAILABLE}} | {{LABEL}} |
| Projection/API/Event/read model | {{YES_NO_OR_UNAVAILABLE}} | {{LABEL}} |
| CLI/Shell/TUI binding | {{YES_NO_OR_UNAVAILABLE}} | {{LABEL}} |
| Trace/evidence/report binding | {{YES_NO_OR_UNAVAILABLE}} | {{LABEL}} |
| Operator-testable path | {{LIVE_SIMULATED_DEV_FIXTURE_OR_UNAVAILABLE}} | {{LABEL}} |

Truth labels (use honestly):

```
LIVE
TRACE_VERIFIED
SIMULATED
DEV_FIXTURE
UNAVAILABLE
ERROR
```

Risk of fake vertical slice: {{RISK_OF_FAKE_SLICE_OR_OVERCLAIM}}

---

## 7. What This Patch Must Prove

- {{PROOF_1}}
- {{PROOF_2}}
- {{PROOF_3}}

---

## 8. Suggested Files

### Create

- {{FILE_TO_CREATE_1}}
- {{FILE_TO_CREATE_2}}

### Modify

- {{FILE_TO_MODIFY_1}}
- {{FILE_TO_MODIFY_2}}

### Do not touch

- {{FORBIDDEN_PATH_1}}
- {{FORBIDDEN_PATH_2}}

---

## 9. Core Objects / Contracts

| Object / Contract | Purpose |
|---|---|
| {{OBJECT_1}} | {{PURPOSE_1}} |
| {{OBJECT_2}} | {{PURPOSE_2}} |

---

## 10. Main Helpers / Entry Points

| Helper / Entry | Purpose |
|---|---|
| {{HELPER_1}} | {{PURPOSE_1}} |
| {{HELPER_2}} | {{PURPOSE_2}} |

---

## 11. Required Demo / Operator-Testable Path

**Path:** {{DEMO_PATH}}

**Expected output:** {{EXPECTED_OUTPUT}}

**Truth label:** {{LIVE_SIMULATED_DEV_FIXTURE_OR_UNAVAILABLE}}

**If UNAVAILABLE:** {{REASON}}

---

## 12. Non-Goals / Hard Boundaries

- {{NON_GOAL_1}}
- {{NON_GOAL_2}}
- {{NON_GOAL_3}}

Hard laws for this patch:

- Do not fake LIVE or TRACE_VERIFIED.
- Do not weaken tests/governance to pass.
- Do not create branch unless explicitly instructed.
- Do not duplicate agent/ canon surfaces.
- Do not implement future roadmap tasks.

---

## 13. Implementation Plan

### Phase 1 — {{PHASE_1_TITLE}}

{{PHASE_1_STEPS}}

### Phase 2 — {{PHASE_2_TITLE}}

{{PHASE_2_STEPS}}

### Phase 3 — {{PHASE_3_TITLE}}

{{PHASE_3_STEPS}}

---

## 14. Tests

| Test area | Approach |
|---|---|
| Unit tests | {{UNIT_TEST_APPROACH}} |
| Integration tests | {{INTEGRATION_TEST_APPROACH}} |
| Regression | {{REGRESSION_APPROACH}} |

New test files: {{NEW_TEST_FILES}}

---

## 15. Docs / State / Report Updates

| File | Update |
|---|---|
| agent/ACTIVE_TASK.md | {{UPDATE_OR_NONE}} |
| agent/ROADMAP.md | {{UPDATE_OR_NONE}} |
| agent/STATE.md | {{UPDATE_OR_NONE}} |
| agent/DECISIONS.md | {{UPDATE_OR_NONE}} |
| agent/reports/ | {{REPORT_FILENAME}} |
| agent/REPORTS.md | Link new report |
| docs/ | {{UPDATE_OR_NONE}} |

---

## 16. Acceptance Criteria

- [ ] {{AC_1}}
- [ ] {{AC_2}}
- [ ] {{AC_3}}
- [ ] Validation commands run and recorded
- [ ] Report created and linked
- [ ] Remaining risks declared
- [ ] Final git status clean

---

## 17. Validation Commands

From `agent/TESTS.md` (authoritative):

```bash
{{VALIDATION_COMMAND_1}}
{{VALIDATION_COMMAND_2}}
```

Additional scope checks:

```bash
{{SCOPE_CHECK_1}}
```

---

## 18. Git Workflow

- Branch: none (work on master/main)
- Push: no
- Commit message: {{COMMIT_MESSAGE}}
- Stage only in-scope files
- Stop on unrelated dirty files

---

## 19. Stop Conditions

Stop and report if:

- Unrelated dirty or untracked files appear
- Scope requires touching forbidden paths
- Canon conflict cannot be resolved
- Validation fails and cannot be fixed in scope
- Implementation would require branch creation or push

---

## 20. Challenge / Main Risk

**Primary challenge:** {{MAIN_CHALLENGE}}

**Main risk:** {{MAIN_RISK}}

**Mitigation:** {{MITIGATION}}

---

## 21. Dispatch Note

This plan is ready for Prompt Contract authoring.

Operator selects tool/model at dispatch time. CodeOps does not route models.

Next step: convert this plan into a copy/paste Prompt Contract using `agent/templates/PROMPT_CONTRACT_TEMPLATE.md`.
