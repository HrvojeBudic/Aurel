# Aurel / GG Agentic Runtime — Post-Health-Check Fix Plan

**Date:** 2026-06-21
**Linked report:** `agent/reports/ANALYSIS_2026-06-21_HEALTH_CHECK_REPORT.md`
**Status:** DRAFT

---

## 1. Objective

Resolve the 4 test failures (F-001, F-002) and sync documentation (F-005, F-006, F-008) to achieve a clean full-suite green state before P1.4.8.

---

## 2. Constraints (must hold throughout)

- Entity proposes; Runtime disposes
- No governance weakening — issuer validation must remain active
- No test weakening or deletion
- Minimal scope — 3 test lines + doc updates only
- No P1.4.8 implementation
- Identity/card stack already green (395/395) — must stay green

---

## 3. Root cause hypothesis

| Rank | Hypothesis | Confidence | Evidence |
|------|-----------|------------|----------|
| 1 | `_card()` called separately for cmd issuer and submit card produces different `card.id` values | **High** | `AgentCard.make()` assigns `new_id("card")` each call; `runtime.py:101` validates `cmd.issuer_card_id == card.id` |
| 2 | Runtime identity validation is too strict for test fixtures using mock cards | **Low** | The issuer check is correct — it's the test helper that's wrong |

---

## 4. Phased approach

### Phase 0 — Reproduce and lock behavior

**Objective:** Confirm the issuer mismatch is caused by separate `_card()` calls.

**Action:** Already reproduced — 3 test failures all show `ISSUER_MISMATCH`.

### Phase 1 — Minimal fix (tool-bus tests)

**Objective:** Fix 3 failing tests by reusing a single `_card()` instance.

| Action | File | Detail |
|--------|------|--------|
| Modify test | `tests/test_tool_bus_p13.py:121-127` | `card = _card()` → `kernel.runtime.submit(_cmd(card, ...), card)` |
| Modify test | `tests/test_tool_bus_p13.py:161-168` | Same pattern for `test_patch_file_applies_simple_fixture` |
| Modify test | `tests/test_tool_bus_p13.py:173-181` | Same pattern for `test_patch_file_rejects_invalid_patch_cleanly` |

**Acceptance:**
- [ ] F-001 resolved — 3 tool-bus tests pass
- [ ] F-002 resolved — `test_cli_verify_exits_zero` passes
- [ ] Full suite: 1051 passed, 4 skipped
- [ ] Identity/card stack still 395/395

### Phase 2 — Doc sync

**Objective:** Update STATE.md, ROADMAP.md, REPORTS.md for P1.4.7-MG completion.

| Action | File | Detail |
|--------|------|--------|
| Update header | `agent/STATE.md` | `_Last updated: 2026-06-21 (P1.4.7-MG)` |
| Update header | `agent/ROADMAP.md` | Current phase: "P1.4.7-MG — Next: P1.4.8" |
| Add entries | `agent/STATE.md` | P1.4.3–P1.4.6 capabilities in "What works" |
| Add report | `agent/REPORTS.md` | Link to `ANALYSIS_2026-06-21_HEALTH_CHECK_REPORT.md` |

**Acceptance:**
- [ ] STATE.md reflects P1.4.7-MG as latest completed
- [ ] ROADMAP.md reflects P1.4.7-MG as current phase
- [ ] All P1.4.x capabilities listed in STATE.md

---

## 5. File change map

| File | Action | Rationale |
|------|--------|-----------|
| `tests/test_tool_bus_p13.py` | Modify (3 locations) | Fix issuer mismatch: reuse same card for cmd + submit |
| `agent/STATE.md` | Modify | Sync last-updated date, add P1.4.3–P1.4.6 capabilities |
| `agent/ROADMAP.md` | Modify | Update current phase from P1.4.2 to P1.4.7-MG |
| `agent/REPORTS.md` | Modify | Link analysis report |

**Files explicitly NOT changed:**
- `src/agentic_runtime/runtime.py` — issuer validation is correct
- `src/agentic_runtime/identity/` — identity/card stack is clean
- Any governance/policy/sandbox modules

---

## 6. Test strategy

### Focused (run first)

```bash
PYTHONPATH=src:. pytest tests/test_tool_bus_p13.py -q
# Expected: 18 passed (currently 15 passed, 3 failed)
```

### Regression

```bash
PYTHONPATH=src:. pytest tests/test_public_entrypoints_p121.py -q
# Expected: 8 passed (currently 7 passed, 1 failed cascading)
```

### Full suite

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest -q
# Expected: 1051 passed, 4 skipped
```

### Identity stack (must stay green)

```bash
PYTHONPATH=src:. pytest tests/test_identity_*.py tests/test_agent_identity_card*.py \
  tests/test_self_model*.py tests/test_communication_modes*.py \
  tests/test_operator_contract*.py tests/test_persona_manifest*.py \
  tests/test_identity_prompt_context*.py tests/test_p14_scope_contract_docs.py \
  tests/test_p147_mg_agent_identity_card.py tests/test_identity_taxonomy.py -q
# Expected: 395 passed
```

### Release surface

```bash
ruff check .
mypy src
python3 -m agentic_runtime.cli identity card validate --json
# Expected: ruff clean; mypy clean; CLI exit 0, valid: true
```

---

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Card reuse changes test semantics | Low | None — same card values, only `id` reused | Verify tool-bus tests still exercise the correct behavior |
| Identity/card hash snapshots break | Low | Medium — if self-model changes | Identity stack tests catch this immediately |
| Doc sync introduces stale data | Low | Low | Cross-reference STATE.md with ROADMAP.md and DECISIONS.md |

**Rollback plan:** Revert test changes; analyze whether issuer check should be relaxed for mock/test cards (requires user decision).

---

## 8. Acceptance criteria (final)

- [ ] F-001 resolved — `test_tool_bus_p13.py` all 18 pass
- [ ] F-002 resolved — `test_cli_verify_exits_zero` passes
- [ ] F-005 resolved — STATE.md header reflects P1.4.7-MG
- [ ] F-006 resolved — ROADMAP.md header reflects P1.4.7-MG
- [ ] F-008 resolved — P1.4.3–P1.4.6 in STATE.md "What works"
- [ ] Full suite: zero failures, 4 expected skips
- [ ] Identity/card stack: 395 passed
- [ ] ruff clean, mypy clean
- [ ] No governance invariants violated
- [ ] P1.4.8 ready to begin

---

## 9. Agent doc updates

| Doc | Update needed? | Detail |
|-----|-----------------|--------|
| `agent/ACTIVE_TASK.md` | No | Already set to P1.4.7-MG complete |
| `agent/STATE.md` | Yes | Date + P1.4.3–P1.4.6 capabilities + analysis link |
| `agent/ROADMAP.md` | Yes | Current phase header |
| `agent/DECISIONS.md` | No | P1.4.7-MG decisions already logged |
| `agent/REPORTS.md` | Yes | Link analysis report |
| `agent/TESTS.md` | No | Already has P1.4.7-MG verification section |

---

> Ready for implementation — invoke `debug-aurel` or proceed with Phase 0.
