# REVIEW PROMPT — {{REVIEW_ID}} {{TITLE}}

External or adversarial review of: {{TARGET_PATCH_OR_REPORT}}

---

## Review Target

- Patch / task: {{P_ID}} — {{TITLE}}
- Agent report: {{REPORT_PATH}}
- Commit: {{COMMIT_HASH}}
- Prompt contract: {{PROMPT_REFERENCE}}

---

## Review Mandate

Perform an adversarial review. Assume the agent may have overclaimed.

Check:

- scope
- wrong files
- fake done
- fake live
- BLUEPRINT vs ACTIVE confusion
- test quality
- validation quality
- evidence quality
- git hygiene
- next-task safety

---

## 1. Scope Check

Expected scope: {{EXPECTED_SCOPE}}

Actual changes: {{ACTUAL_CHANGES}}

Verdict: {{PASS_FAIL}}

Issues: {{NONE_OR_LIST}}

---

## 2. Wrong Files Check

Files that should not have been touched: {{LIST}}

Files incorrectly modified: {{NONE_OR_LIST}}

---

## 3. Fake Done Check

Claimed status: {{CLAIMED_STATUS}}

Supported by evidence: {{YES_NO}}

Overclaim areas: {{NONE_OR_LIST}}

---

## 4. Fake Live / Truth Label Check

LIVE claims: {{LIST_OR_NONE}}

TRACE_VERIFIED claims: {{LIST_OR_NONE}}

Honest UNAVAILABLE declarations: {{YES_NO}}

Fake LIVE detected: {{YES_NO}}

Fake TRACE_VERIFIED detected: {{YES_NO}}

---

## 5. BLUEPRINT vs ACTIVE Confusion

Future/blueprint systems presented as active: {{NONE_OR_LIST}}

---

## 6. Test Quality

Tests added: {{YES_NO_NA}}

Tests meaningful (not trivial): {{YES_NO_NA}}

Missing test coverage: {{NONE_OR_LIST}}

---

## 7. Validation Quality

Validation commands from `agent/TESTS.md`: {{YES_NO}}

Validation depth matches risk: {{YES_NO}}

Validation gaps: {{NONE_OR_LIST}}

---

## 8. Evidence Quality

Report exists: {{YES_NO}}

Report complete: {{YES_NO}}

Remaining risks declared: {{YES_NO}}

Report linked in REPORTS.md: {{YES_NO}}

---

## 9. Git Hygiene

Clean final status: {{YES_NO}}

Unrelated files: {{NONE_OR_LIST}}

Commit appropriate: {{YES_NO}}

---

## 10. Next-Task Safety

Next task recommendation safe: {{YES_NO}}

Canon conflicts for next task: {{NONE_OR_LIST}}

---

## Required Output

Return:

```
Verdict: PASS / PASS_WITH_WARNINGS / FAIL

Critical issues:
- {{ISSUE_OR_NONE}}

Warnings:
- {{WARNING_OR_NONE}}

Required repair:
- {{REPAIR_OR_NONE}}

Safe to continue: yes/no
```

---

## Reviewer Notes

{{ADDITIONAL_NOTES}}
