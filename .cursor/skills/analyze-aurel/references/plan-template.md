# Fix Plan Template

Use this template for Phase 6 deliverable B. Hand off to `debug-aurel` for implementation after plan approval.

---

```markdown
# [Title] — Fix Plan

**Date:** YYYY-MM-DD
**Linked report:** [Analysis report filename or F-xxx finding IDs]
**Status:** DRAFT | APPROVED | IN PROGRESS | COMPLETE

---

## 1. Objective

[Single sentence: the outcome this plan achieves.]

---

## 2. Constraints (must hold throughout)

- Entity proposes; Runtime disposes
- [Specific invariant 1 from analysis]
- [Specific invariant 2]
- No test weakening, policy bypass, or governance shortcuts
- Minimal scope — no unrelated refactors

---

## 3. Root cause hypothesis

| Rank | Hypothesis | Confidence | Evidence |
|------|-----------|------------|----------|
| 1 | [Most likely cause] | High/Medium/Low | F-001, [file:line] |
| 2 | [Alternative cause] | Low | [supporting evidence] |

---

## 4. Phased approach

### Phase 0 — Reproduce and lock behavior

**Objective:** [Create failing test or confirm reproduction]

| Action | File | Detail |
|--------|------|--------|
| Add regression test | `tests/test_*.py` | [What the test asserts] |
| Confirm failure | — | [Expected pytest output] |

**Acceptance:** Regression test fails before fix, passes after.

### Phase 1 — Minimal fix

**Objective:** [Core fix in owning module]

| Action | File | Detail |
|--------|------|--------|
| Modify | `src/agentic_runtime/module.py` | [Specific change] |

**Acceptance:**
- [ ] F-001 resolved
- [ ] Phase 0 regression test passes
- [ ] No new linter/type errors

### Phase 2 — Validation and docs (if needed)

**Objective:** [Broader validation, doc sync]

| Action | File | Detail |
|--------|------|--------|
| Run full suite | — | `PYTHONPATH=src:. pytest -q` |
| Update docs | `agent/STATE.md` | [If behavior changed] |

**Acceptance:**
- [ ] Full test suite passes
- [ ] `ruff check` and `mypy` pass (if public API touched)
- [ ] Agent docs consistent

---

## 5. File change map

| File | Action | Rationale |
|------|--------|-----------|
| `tests/test_*.py` | Create/Modify | Regression test for F-001 |
| `src/agentic_runtime/module.py` | Modify | Fix in owning module |
| `agent/STATE.md` | Modify | Doc sync (if applicable) |

**Files explicitly NOT changed:** [List to prevent scope creep]

---

## 6. Test strategy

### Focused (run first)

```bash
PYTHONPATH=src:. pytest tests/test_<module>.py -q
```

### Regression

```bash
PYTHONPATH=src:. pytest tests/test_<new_regression>.py -q
```

### Full suite

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest -q
python -m agentic_runtime.cli verify
```

### Release surface (if public API touched)

```bash
ruff check src tests
mypy src/agentic_runtime
python -m agentic_runtime.cli alpha-seal
```

---

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Fix breaks adjacent module] | Low/Med/High | [Impact] | [Focused test + full suite] |
| [Regression in pipeline stage X] | Low | [Impact] | [Specific test to run] |

**Rollback plan:** Revert Phase 1 changes; Phase 0 test documents expected behavior.

---

## 8. Acceptance criteria (final)

- [ ] All findings (F-001, F-00N) resolved or explicitly deferred with rationale
- [ ] Phase 0 regression test passes
- [ ] Focused module tests pass
- [ ] Full test suite passes (note any expected skips)
- [ ] No governance invariants violated
- [ ] Agent docs updated if behavior changed
- [ ] Analysis report status updated to COMPLETE

---

## 9. Agent doc updates

| Doc | Update needed? | Detail |
|-----|-----------------|--------|
| `agent/ACTIVE_TASK.md` | Yes/No | [Status change] |
| `agent/STATE.md` | Yes/No | [Capability/limit change] |
| `agent/DECISIONS.md` | Yes/No | [Non-obvious choice] |
| `agent/reports/` | Yes | [Completion report] |
| `agent/REPORTS.md` | Yes/No | [Link new report] |
```

---

## Handoff

After plan delivery:

> Ready for implementation — invoke `debug-aurel` or proceed with Phase 0.

Do not skip Phase 0 (reproduce/lock) unless the failure is already captured by an existing failing test.
