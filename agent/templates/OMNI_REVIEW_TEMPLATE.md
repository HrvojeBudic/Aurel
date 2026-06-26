# OMNI REVIEW — {{P_ID}} {{TITLE}}

---

## 0. Review Header

| Field | Value |
|---|---|
| Task ID | {{P_ID}} |
| Title | {{TITLE}} |
| Review date | {{DATE}} |
| Agent report | {{REPORT_PATH}} |
| Prompt contract | {{PROMPT_REFERENCE}} |

---

## 1. Input Received

- Agent report: {{REPORT_PATH}}
- Commit: {{COMMIT_HASH}}
- Files changed: {{FILE_COUNT}}
- Validation output: {{SUMMARY}}

---

## 2. Claimed Outcome

Agent claimed: {{DONE_NOT_DONE_PARTIAL}}

Summary of claim: {{CLAIM_SUMMARY}}

---

## 3. Prompt Obedience Check

| Requirement | Verdict |
|---|---|
| Git discipline | {{PASS_FAIL}} |
| Scope boundaries | {{PASS_FAIL}} |
| Forbidden paths avoided | {{PASS_FAIL}} |
| Validation from TESTS.md | {{PASS_FAIL}} |
| Canon update rules | {{PASS_FAIL}} |
| Report requirement | {{PASS_FAIL}} |
| Commit requirement | {{PASS_FAIL}} |

Deviations: {{NONE_OR_LIST}}

---

## 4. Scope / Diff Check

Expected scope: {{EXPECTED_SCOPE}}

Actual diff: {{ACTUAL_DIFF_SUMMARY}}

Scope creep: {{NONE_OR_DESCRIPTION}}

Wrong files touched: {{NONE_OR_LIST}}

---

## 5. Existing Canon Preservation Check

- No duplicate state surfaces: {{PASS_FAIL}}
- No duplicate decision log: {{PASS_FAIL}}
- No duplicate validation authority: {{PASS_FAIL}}
- No duplicate evidence format: {{PASS_FAIL}}
- Existing agent/ canon preserved: {{PASS_FAIL}}
- Existing docs/ canon preserved: {{PASS_FAIL}}

---

## 6. Integration-First Check

| Layer | Expected | Actual | Honest |
|---|---|---|---|
| Backend | {{EXPECTED}} | {{ACTUAL}} | {{YES_NO}} |
| Contract | {{EXPECTED}} | {{ACTUAL}} | {{YES_NO}} |
| Projection/API | {{EXPECTED}} | {{ACTUAL}} | {{YES_NO}} |
| CLI/binding | {{EXPECTED}} | {{ACTUAL}} | {{YES_NO}} |
| Evidence/report | {{EXPECTED}} | {{ACTUAL}} | {{YES_NO}} |
| Operator path | {{EXPECTED}} | {{ACTUAL}} | {{YES_NO}} |

Fake vertical slice risk: {{LOW_MEDIUM_HIGH}}

---

## 7. Truth Label Check

- LIVE claims supported: {{YES_NO_NA}}
- TRACE_VERIFIED claims supported: {{YES_NO_NA}}
- UNAVAILABLE states have reasons: {{YES_NO_NA}}
- No fake LIVE: {{YES_NO}}
- No fake TRACE_VERIFIED: {{YES_NO}}
- BLUEPRINT vs ACTIVE confusion: {{NONE_OR_DESCRIPTION}}

---

## 8. Boundary / Side-Effect Check

Forbidden changes: {{NONE_OR_LIST}}

Unexpected side effects: {{NONE_OR_LIST}}

---

## 9. Test / Validation Quality

Tests meaningful: {{YES_NO_NA}}

Validation depth matches risk: {{YES_NO}}

Validation commands recorded: {{YES_NO}}

Validation gaps: {{NONE_OR_LIST}}

---

## 10. Evidence / Report Quality

Report complete: {{YES_NO}}

Remaining risks declared: {{YES_NO}}

Report linked in REPORTS.md: {{YES_NO}}

Evidence sufficient for claim: {{YES_NO}}

---

## 11. Git Hygiene

Branch correct: {{YES_NO}}

Commit message appropriate: {{YES_NO}}

Final git clean: {{YES_NO}}

Unrelated files: {{NONE_OR_LIST}}

---

## 12. Acceptance Criteria Review

- [ ] {{AC_1}} — {{PASS_FAIL}}
- [ ] {{AC_2}} — {{PASS_FAIL}}
- [ ] {{AC_3}} — {{PASS_FAIL}}

All criteria met: {{YES_NO}}

---

## 13. Risk Assessment

Remaining risks acceptable: {{YES_NO}}

Critical risks: {{NONE_OR_LIST}}

Warnings: {{NONE_OR_LIST}}

---

## 14. Repair Needed?

{{YES_NO}}

If yes, repair scope: {{REPAIR_SCOPE}}

---

## 15. External Review Needed?

{{YES_NO}}

If yes, reason: {{REASON}}

---

## 16. Seal Readiness

Seal criteria met: {{YES_NO_NA}}

Blockers: {{NONE_OR_LIST}}

---

## 17. Next Step Decision

Primary decision (exactly one):

```
CONTINUE
REPAIR
REVIEW
INTEGRATE
SEAL
STOP
```

**Decision:** {{DECISION}}

Rationale: {{RATIONALE}}

Next task if CONTINUE: {{NEXT_TASK}}

---

## 18. OMNI Verdict

**Verdict:** {{DECISION}}

**Summary:** {{ONE_PARAGRAPH_VERDICT}}

**Required follow-up:** {{NONE_OR_ACTIONS}}
