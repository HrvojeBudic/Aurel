# Post-P1.4.14 Health-Check — Fix Plan

**Date:** 2026-06-21
**Linked report:** [ANALYSIS_2026-06-21_POST_P1414_HEALTH_CHECK_REPORT.md](ANALYSIS_2026-06-21_POST_P1414_HEALTH_CHECK_REPORT.md) (F-001–F-013)
**Status:** COMPLETE — applied 2026-06-21

---

## 1. Objective

Bring agent operating docs into alignment with post-P1.4.14 code reality and reconcile P1.4.15 phase naming before the next implementation sprint — without changing runtime behavior or weakening governance.

---

## 2. Constraints (must hold throughout)

- Entity proposes; Runtime disposes
- Identity detection/consent layers remain signal-only until P1.4.15+ explicitly wires runtime enforcement
- No test weakening, policy bypass, or governance shortcuts
- Minimal scope — doc sync and naming only; no refactors

---

## 3. Root cause hypothesis

| Rank | Hypothesis | Confidence | Evidence |
|------|-----------|------------|----------|
| 1 | Parallel agent sessions complete phases faster than ACTIVE_TASK housekeeping | High | F-001: ACTIVE_TASK at P1.4.12 while ROADMAP/STATE at P1.4.14 |
| 2 | Phase names evolved during implementation (Consent Binding vs Integrity Guard) | High | F-003: ROADMAP vs P1.4.14 report naming mismatch |
| 3 | Identity runtime bridge intentionally deferred per phase scope | High | F-004: no imports in runtime.py; all P1.4.x reports state non-goals |

---

## 4. Phased approach

### Phase 0 — Confirm baseline (no code changes)

**Objective:** Lock current green state before doc edits.

| Action | File | Detail |
|--------|------|--------|
| Run full suite | — | Expect 1376 passed, 2 skipped |
| Run alpha-seal | — | Expect exit 0 |
| Run identity focused | `tests/identity/` | Expect 113+ passed (authority_delta + operator_consent) |

**Acceptance:**
- [x] Full suite green
- [x] `cli verify` exits 0
- [x] No unexpected failures

### Phase 1 — ACTIVE_TASK and STATE sync

**Objective:** Resolve F-001, F-002

| Action | File | Detail |
|--------|------|--------|
| Rewrite active task | `agent/ACTIVE_TASK.md` | Set to P1.4.14 completed; list P1.4.13/14 results; Next: P1.4.15 |
| Clean handoff lines | `agent/STATE.md` | Remove stale "Ready for P1.4.13/14" from P1.4.12/13 sections (keep only in historical context if needed) |
| Update test counts | `agent/STATE.md` | P1.4.12 section: update full-suite count note; P1.4.14 section: confirm 1376 passed |

**Acceptance:**
- [x] F-001 resolved — ACTIVE_TASK reflects P1.4.14 complete
- [x] F-002 resolved — no contradictory handoff lines in STATE.md
- [x] Phase 0 baseline still green

### Phase 2 — Phase naming reconciliation (F-003)

**Objective:** Single canonical name for P1.4.15 across ROADMAP, scope contract, and handoff docs.

| Action | File | Detail |
|--------|------|--------|
| Decide canonical name | `docs/P1.4_IDENTITY_AUTONOMY_SCOPE_CONTRACT.md` | Align with constitutional scope doc (source of truth) |
| Update ROADMAP | `agent/ROADMAP.md` | Match canonical P1.4.15 name in header + table |
| Update P1.4.14 handoff | `agent/reports/P1.4.14_OPERATOR_CONSENT_BINDING.md` §15 | Match canonical name |
| Add DECISIONS entry | `agent/DECISIONS.md` | Record naming choice if changed |

**Acceptance:**
- [x] F-003 resolved — canonical name: Principal / Delegate Model
- [x] No conflicting "Identity Integrity Guard" vs "CLI Surface" labels

### Phase 3 — Stale report annotation (F-012, optional)

**Objective:** Prevent confusion from mid-implementation notes in P1.4.12 report.

| Action | File | Detail |
|--------|------|--------|
| Add footnote | `agent/reports/P1.4.12_RAW_SOURCE_CANONICAL_HASH_ATTESTATION.md` | Note that P1.4.13 transient failures were resolved; current suite 1376 passed |

**Acceptance:**
- [x] F-012 resolved or annotated as historical

### Phase 4 — Forward-looking architecture note (F-004, documentation only)

**Objective:** Document the identity→runtime enforcement gap explicitly.

| Action | File | Detail |
|--------|------|--------|
| Add wiring status | `agent/ARCHITECTURE.md` | Section under P1.4.14: "Runtime integration: NOT YET WIRED — consent/delta are CLI/report signals only" |
| Add to STATE limitations | `agent/STATE.md` | Known limitation: identity consent not enforced in `submit()` |

**Acceptance:**
- [x] F-004 documented (not fixed — enforcement is P1.4.15+ scope)
- [x] No accidental runtime wiring in this phase

---

## 5. File change map

| File | Action | Rationale |
|------|--------|-----------|
| `agent/ACTIVE_TASK.md` | Modify | F-001 |
| `agent/STATE.md` | Modify | F-002, F-004 doc |
| `agent/ROADMAP.md` | Modify | F-003 |
| `agent/ARCHITECTURE.md` | Modify | F-004 doc |
| `agent/DECISIONS.md` | Modify | F-003 naming decision |
| `agent/reports/P1.4.12_*.md` | Modify (footnote) | F-012 |
| `agent/reports/P1.4.14_*.md` | Modify (handoff) | F-003 |
| `agent/REPORTS.md` | Modify | Link new analysis reports |

**Files explicitly NOT changed:**
- `src/agentic_runtime/runtime.py` (no premature wiring)
- `src/agentic_runtime/identity/*` (no code changes)
- `tests/*` (no test changes)
- `tool_manifest/validation.py` (deferred split)
- `tools.py` / `tool_manifest/registry.py` (deferred rename)

---

## 6. Test strategy

### Baseline (before and after each phase)

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest -q
python -m agentic_runtime.cli verify
```

### Identity focused

```bash
PYTHONPATH=src:. pytest tests/identity/ -q
```

### Release surface (unchanged code — smoke only)

```bash
ruff check src tests
mypy src/agentic_runtime
python -m agentic_runtime.cli alpha-seal
```

---

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Doc edits introduce incorrect phase claims | Low | Misleading agents | Cross-check against ROADMAP + test counts |
| Accidental runtime wiring during doc phase | Low | Governance scope creep | File change map excludes runtime.py |
| P1.4.15 naming change breaks existing references | Med | Doc confusion | Single DECISIONS entry + grep for old name |

**Rollback plan:** Revert doc-only commits; code and tests unchanged.

---

## 8. Acceptance criteria (final)

- [x] F-001, F-002, F-003 resolved
- [x] F-004 documented as known limitation (not silently ignored)
- [x] F-012 annotated or resolved
- [x] Full suite: 1376 passed, 2 skipped
- [x] `cli verify` and `alpha-seal` exit 0
- [x] No governance invariants violated
- [x] Analysis report status updated to COMPLETE

---

## 9. Agent doc updates

| Doc | Update needed? | Detail |
|-----|----------------|--------|
| `agent/ACTIVE_TASK.md` | **Yes** | P1.4.14 complete, next P1.4.15 |
| `agent/STATE.md` | **Yes** | Remove stale handoffs, add runtime-wiring limitation |
| `agent/ROADMAP.md` | **Yes** | P1.4.15 naming reconciliation |
| `agent/ARCHITECTURE.md` | **Yes** | Runtime integration status note |
| `agent/DECISIONS.md` | **Yes** | P1.4.15 naming decision |
| `agent/reports/` | **Yes** | Link analysis + fix plan |
| `agent/REPORTS.md` | **Yes** | Index new analysis artifacts |

---

## Deferred (not in this plan)

| Finding | Deferred to |
|---------|------------|
| F-005 Dual ToolRegistry rename | P6 Governed Tool Bus Expansion |
| F-006 validation.py split | P6/P7 |
| F-007 identity DRY helpers | P1.4.20 seal or dedicated refactor patch |
| F-010 consent persistence | P1.7+ state DB layer |
| F-011 coverage margin | Incremental test additions per phase |
| F-013 P1.0 CI seal | Baseline commit + GitHub Actions green |

---

## Handoff

> Ready for implementation — invoke `debug-aurel` or proceed with Phase 0.

Do not skip Phase 0 (baseline lock) before doc edits.