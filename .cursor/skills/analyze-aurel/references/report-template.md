# Analysis Report Template

Use this template for Phase 6 deliverable A. Save completed reports under `agent/reports/` and link from `agent/REPORTS.md` when the analysis completes a phase or significant audit.

---

```markdown
# [Title] — Analysis Report

**Date:** YYYY-MM-DD
**Status:** PASS | FAIL | PARTIAL | INVESTIGATION
**Analysis mode:** bug | architecture | module-audit | health-check | pre-patch-review

---

## 1. Summary

[One paragraph: verdict, scope, key finding count by severity, recommended next step.]

---

## 2. Scope and trigger

| Field | Value |
|-------|-------|
| Trigger | [User symptom, failing test, audit request] |
| Boundary | [Module / pipeline stage / phase / full-system] |
| Invariants at risk | [List from invariants.md] |
| Non-goals | [What was explicitly excluded] |

---

## 3. Architecture / pipeline context

[Relevant excerpt from module map or pipeline. Name the pipeline stage(s) involved and owning modules.]

```
[Optional: pipeline snippet showing where the issue occurs]
```

---

## 4. Evidence

### Commands run

| Command | Result |
|---------|--------|
| `python -m agentic_runtime.cli status` | [PASS/FAIL + note] |
| `python3 -m compileall src tests` | [PASS/FAIL] |
| `pytest tests/<file>.py -q` | [N passed, M failed, K skipped] |
| [other commands] | [results] |

### Key observations

- [Observation 1 with file:line reference]
- [Observation 2 with file:line reference]

---

## 5. Findings

| ID | Severity | Module | Location | Root cause | Affected invariant |
|----|----------|--------|----------|------------|-------------------|
| F-001 | Critical/High/Medium/Low | `module.py` | `path:line` | [Cause] | [Invariant] |
| F-002 | ... | ... | ... | ... | ... |

### Finding details

#### F-001: [Short title]

**Severity:** [level]
**Module:** [owner]
**Location:** `src/agentic_runtime/module.py:NN`

[Detailed explanation: what happens, why, impact, reproduction steps.]

---

## 6. Test coverage assessment

| Area | Covered by | Gap |
|------|-----------|-----|
| [Module/feature] | `tests/test_*.py` | [Missing edge case or untested path] |

---

## 7. Known limitations / doc drift

- [Limitation or doc inconsistency found during analysis]
- [Mismatch between STATE.md / ARCHITECTURE.md and observed behavior]

---

## 8. Explicitly not in scope

- [Feature, module, or phase not analyzed]
- [Related work deferred to future phase]

---

## 9. Recommended next step

[One sentence: proceed to fix plan Phase 0, escalate to user, or no action needed.]

Link fix plan: [plan filename or inline reference]
```

---

## Quality checklist

Before delivering the report:

- [ ] Every finding has ID, severity, module, file:line, root cause, invariant
- [ ] Evidence section lists all commands run with outcomes
- [ ] No findings propose governance weakening as resolution
- [ ] Architecture context identifies pipeline stage and owner module
- [ ] Status reflects overall analysis verdict
