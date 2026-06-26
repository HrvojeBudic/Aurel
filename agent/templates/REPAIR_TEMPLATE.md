# REPAIR PROMPT — {{REPAIR_ID}} {{TITLE}}

**Freeze scope. This is a repair patch, not a redesign.**

---

## 1. Failure

{{FAILURE_DESCRIPTION}}

Observed at: {{WHEN_WHERE}}

---

## 2. Expected Behavior

{{EXPECTED_BEHAVIOR}}

---

## 3. Current Behavior

{{CURRENT_BEHAVIOR}}

---

## 4. Suspected Root Cause

{{SUSPECTED_ROOT_CAUSE}}

Evidence: {{EVIDENCE}}

---

## 5. Allowed Files

Only these files may be modified:

```
{{ALLOWED_FILE_1}}
{{ALLOWED_FILE_2}}
{{ALLOWED_FILE_3}}
```

---

## 6. Forbidden Changes

Do not:

- Redesign architecture
- Expand scope beyond the failure
- Touch unrelated files
- Weaken tests to pass
- Create branch or push
- Duplicate agent/ canon surfaces
- Fake LIVE or TRACE_VERIFIED

Forbidden paths:

```
{{FORBIDDEN_PATH_1}}
{{FORBIDDEN_PATH_2}}
```

---

## 7. Minimal Repair

Apply the smallest fix that restores expected behavior:

{{MINIMAL_REPAIR_DESCRIPTION}}

---

## 8. Regression Validation

Run:

```bash
{{REGRESSION_COMMAND_1}}
{{REGRESSION_COMMAND_2}}
```

Confirm the original failure is resolved and no new failures introduced.

---

## 9. Existing Canon Updates

Update only if required:

| File | Update |
|---|---|
| agent/DECISIONS.md | {{IF_DECISION_MADE}} |
| agent/STATE.md | {{IF_STATE_CHANGED}} |
| agent/reports/ | {{REPAIR_REPORT}} |
| agent/REPORTS.md | Link repair report |

---

## 10. Evidence Update

Update or create evidence showing:

- Failure reproduced (if applicable)
- Fix applied
- Regression validation passed
- Remaining risk declared

---

## 11. Commit Instruction

```bash
git add {{STAGED_FILES}}
git commit -m "fix({{SCOPE}}): {{SHORT_DESCRIPTION}}"
```

Do not push.

---

## 12. Final Report

Return:

```
RESULT — REPAIR {{REPAIR_ID}}

Failure:
Root cause:
Fix applied:
Files changed:
Validation run:
Regression proof:
Remaining risks:
Done / Not Done:
```
