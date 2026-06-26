# AGENT REPORT — {{P_ID}} {{TITLE}}

---

## 0. Result Header

| Field | Value |
|---|---|
| Task ID | {{P_ID}} |
| Title | {{TITLE}} |
| Date | {{DATE}} |
| Executor | {{AGENT_OR_TOOL}} |
| Final status | {{DONE_NOT_DONE_PARTIAL}} |

---

## 1. Summary

{{ONE_PARAGRAPH_SUMMARY}}

---

## 2. Existing Canon Read

Sources read before work:

- [ ] agent/AGENT.md
- [ ] agent/CODEOPS.md
- [ ] agent/ACTIVE_TASK.md
- [ ] agent/ROADMAP.md
- [ ] agent/STATE.md
- [ ] agent/TESTS.md
- [ ] agent/REPORTS.md
- [ ] {{ADDITIONAL_SOURCES}}

Conflicts found: {{NONE_OR_DESCRIPTION}}

---

## 3. Git / Worktree Preflight

Branch: {{BRANCH}}

Pre-work status: {{STATUS}}

Unrelated files: {{NONE_OR_LIST}}

---

## 4. Files Created / Modified

### Created

{{FILES_CREATED}}

### Modified

{{FILES_MODIFIED}}

### Deliberately not touched

{{FILES_NOT_TOUCHED}}

---

## 5. Implementation Proof

{{IMPLEMENTATION_PROOF}}

Key evidence:

- {{EVIDENCE_1}}
- {{EVIDENCE_2}}

---

## 6. Integration-First Proof

| Layer | Status | Truth label | Notes |
|---|---|---|---|
| Backend capability | {{STATUS}} | {{LABEL}} | {{NOTES}} |
| Versioned contract/schema | {{STATUS}} | {{LABEL}} | {{NOTES}} |
| Projection/API/Event | {{STATUS}} | {{LABEL}} | {{NOTES}} |
| CLI/Shell/TUI binding | {{STATUS}} | {{LABEL}} | {{NOTES}} |
| Trace/evidence/report | {{STATUS}} | {{LABEL}} | {{NOTES}} |
| Operator-testable path | {{STATUS}} | {{LABEL}} | {{NOTES}} |

---

## 7. Truth Label / Source Label Check

Labels used in this patch:

- LIVE: {{YES_NO_WITH_DETAILS}}
- TRACE_VERIFIED: {{YES_NO_WITH_DETAILS}}
- SIMULATED: {{YES_NO_WITH_DETAILS}}
- DEV_FIXTURE: {{YES_NO_WITH_DETAILS}}
- UNAVAILABLE: {{YES_NO_WITH_DETAILS}}
- ERROR: {{YES_NO_WITH_DETAILS}}

Fake LIVE avoided: {{YES}}
Fake TRACE_VERIFIED avoided: {{YES}}

---

## 8. Boundary / Side-Effect Proof

Forbidden paths not touched:

- {{FORBIDDEN_1}} — confirmed untouched
- {{FORBIDDEN_2}} — confirmed untouched

Side effects:

- {{SIDE_EFFECT_OR_NONE}}

Duplicate canon surfaces created: {{NO_OR_LIST}}

---

## 9. Tests Added / Updated

{{TEST_SUMMARY}}

New test files: {{LIST_OR_NONE}}

Tests skipped and why: {{NONE_OR_REASON}}

---

## 10. Validation Run

Commands run (from `agent/TESTS.md` authority):

```bash
{{VALIDATION_COMMANDS_WITH_OUTPUT_SUMMARY}}
```

Validation not run (and why): {{NONE_OR_REASON}}

---

## 11. Existing Canon Updated

| File | Update |
|---|---|
| agent/ACTIVE_TASK.md | {{UPDATE_OR_UNCHANGED}} |
| agent/ROADMAP.md | {{UPDATE_OR_UNCHANGED}} |
| agent/STATE.md | {{UPDATE_OR_UNCHANGED}} |
| agent/DECISIONS.md | {{UPDATE_OR_UNCHANGED}} |
| agent/REPORTS.md | {{UPDATE_OR_UNCHANGED}} |
| agent/reports/ | {{REPORT_FILE}} |

---

## 12. What Was Deliberately Not Implemented

- {{NOT_IMPLEMENTED_1}}
- {{NOT_IMPLEMENTED_2}}

---

## 13. Scope Deviations

{{NONE_OR_DESCRIPTION}}

Prompt integrity: {{OBEDIENT_PARTIAL_DEVIATION}}

---

## 14. Prompt Integrity Check

| Requirement | Met |
|---|---|
| Git discipline obeyed | {{YES_NO}} |
| Scope boundaries obeyed | {{YES_NO}} |
| Validation authority from TESTS.md | {{YES_NO}} |
| No model routing performed | {{YES_NO}} |
| No forbidden paths touched | {{YES_NO}} |
| Report created if required | {{YES_NO}} |
| Commit created if required | {{YES_NO}} |

---

## 15. Acceptance Criteria Check

- [ ] {{AC_1}} — {{MET_NOT_MET}}
- [ ] {{AC_2}} — {{MET_NOT_MET}}
- [ ] {{AC_3}} — {{MET_NOT_MET}}
- [ ] Validation recorded — {{MET_NOT_MET}}
- [ ] Canon updated — {{MET_NOT_MET}}
- [ ] Git clean — {{MET_NOT_MET}}

---

## 16. Git Diff / Commit

Commit hash: {{HASH}}

Commit message: {{MESSAGE}}

Post-commit status: {{STATUS}}

---

## 17. Remaining Risks / Limitations

- {{RISK_1}}
- {{RISK_2}}

---

## 18. Next Recommended Task

{{NEXT_TASK}}

---

## 19. Final Status

**Status:** {{DONE_NOT_DONE}}

Do not claim DONE unless implementation, validation, canon updates, report, commit, and git state support that claim.
