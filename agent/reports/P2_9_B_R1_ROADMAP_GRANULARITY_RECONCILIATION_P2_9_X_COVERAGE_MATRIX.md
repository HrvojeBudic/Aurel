# P2.9-B-R1 — Roadmap Granularity Reconciliation / P2.9.x Coverage Matrix

**Date:** 2026-07-01  
**Pack:** P2.9-B-R1  
**Status:** DONE — ROADMAP_GRANULARITY_RECONCILED / OLD_P2_9_B_EVIDENCE_OVERLAY_RETAINED / TRUE_P2_9_B_NOT_DONE / P2_10_PLUS_NOT_STARTED

## 1. Result Header

P2.9-B-R1 reconciled old P2.9-B (Shell Exit Seal / Vertical Slice Evidence Consumption) against exact P2.9.x roadmap checkpoints extracted from `agent/ROADMAP.md` and verified evidence. Old P2.9-B is retained as a useful evidence/truth seal overlay; it is not proof that P2.9.0–P2.9.20 are all done. True P2.9-B (`P2.9.6–P2.9.10 Shell Exit Seal Readiness / Validation / Evidence Matrix`) remains **NOT DONE**. P2.10+ remains **NOT STARTED**.

## 2. Scope

- Extract P2.9.x checkpoint IDs and titles from `agent/ROADMAP.md`
- Consume P2.9-A, P2.9-A-R1, old P2.9-B, P2.REVIEW-A, P2.VSLICE-A evidence
- Build checkpoint-level P2.9.x coverage matrix
- Reclassify old P2.9-B as evidence overlay
- Correct `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/REPORTS.md` pointers
- Record validation honestly

Not in scope: new Shell features, missing P2.9.x implementation, P2.VSLICE-A changes, command preflight code changes, old P2.9-B revert/deletion, P2.10+ start, roadmap renumbering, broad roadmap rewrite.

## 3. Why R1 Exists

Old P2.9-B sealed P2.1–P2.9 as an honest Shell foundation with vertical slice evidence consumption. That work is valid evidence. It was incorrectly treated in `agent/STATE.md` and `agent/ACTIVE_TASK.md` as if granular P2.9.x checkpoints (especially true P2.9-B `P2.9.6–P2.9.10`) were complete and as if P2.10+ handoff was justified. R1 restores checkpoint-level roadmap truth before any P2.10 jump.

## 4. Git / Worktree Preflight

| Check | Result |
|-------|--------|
| Branch | `master` |
| Initial status | clean |
| Unrelated dirty files | none |
| P2.10+ dirty/untracked files | none |
| Shell/product dirty/untracked files | none |
| Runtime/sandbox/identity/policy dirty/untracked files | none |
| `.venv/bin/python` | present |
| Preflight result | **PASS** |

## 5. Roadmap Source Read

**Source:** `agent/ROADMAP.md` (Aurel Roadmap v5.5 — ACTIVE_CANON)

**Extracted section:** P2.9 — Shell Exit Seal

**Pack-range canon from ROADMAP progress mirrors (verified):**

| Pack range | ROADMAP title |
|------------|---------------|
| P2.9.0–P2.9.5 | Shell Exit Seal Foundation |
| P2.9.6–P2.9.10 | Shell Exit Seal Readiness / Validation / Evidence Matrix |
| P2.9-C | referenced; pack purpose not enumerated as P2.9.x table in v5.5 mirror |
| P2.9-D | referenced; pack purpose not enumerated as P2.9.x table in v5.5 mirror |
| P2.10+ | not started |

**Granular checkpoint titles P2.9.0–P2.9.5:** ROADMAP v5.5 progress mirror lists pack range and artifact names but not per-checkpoint titles. Per-checkpoint capsule titles for P2.9.0–P2.9.5 were established in `agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md` §11 during P2.9-A implementation against the ROADMAP pack; verified against `tests/aurel_shell/test_shell_exit_seal_foundation.py`.

**Granular checkpoint titles P2.9.6–P2.9.20:** **Not individually enumerated in `agent/ROADMAP.md` v5.5 mirror.** Only pack-range titles exist for P2.9.6–P2.9.10. P2.9.11–P2.9.20 have no ROADMAP v5.5 checkpoint titles (P2.9-C/D/P2.10+ referenced at pack level only).

**Placeholder titles used:** none for P2.9.0–P2.9.5 (P2.9-A report verified). For P2.9.6–P2.9.20 without ROADMAP granular titles, matrix uses pack-scope notation (see §9).

**Invented checkpoint names:** none

**Extraction result:** **PASS with granularity gap documented** — P2.9.0–P2.9.5 extractable; P2.9.6–P2.9.10 pack title extractable; P2.9.11–P2.9.20 not granular in ROADMAP v5.5

## 6. Extracted P2.9.x Checkpoint List

| ID | Title source | Title |
|----|--------------|-------|
| P2.9.0 | P2.9-A report §11 (pack P2.9.0–P2.9.5) | Shell Exit Seal Intake / P2.8-D Handoff Gate |
| P2.9.1 | P2.9-A report §11 | Prior Shell Section Evidence Intake Contract |
| P2.9.2 | P2.9-A report §11 | Shell Exit Criteria Catalog Contract |
| P2.9.3 | P2.9-A report §11 | Exit Readiness Dimension / Boundary Contract |
| P2.9.4 | P2.9-A report §11 | Unavailable Capability / No-Release / No-Product Boundary Contract |
| P2.9.5 | P2.9-A report §11 | Shell Exit Seal Foundation Result / P2.9-B Handoff Contract |
| P2.9.6 | ROADMAP pack only | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope; granular title not in ROADMAP v5.5) |
| P2.9.7 | ROADMAP pack only | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope; granular title not in ROADMAP v5.5) |
| P2.9.8 | ROADMAP pack only | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope; granular title not in ROADMAP v5.5) |
| P2.9.9 | ROADMAP pack only | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope; granular title not in ROADMAP v5.5) |
| P2.9.10 | ROADMAP pack only | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope; granular title not in ROADMAP v5.5) |
| P2.9.11–P2.9.15 | ROADMAP pack ref only | P2.9-C pack scope (granular titles not in ROADMAP v5.5) |
| P2.9.16–P2.9.20 | ROADMAP pack ref only | P2.9-D pack scope (granular titles not in ROADMAP v5.5) |

**Other P2.9.x IDs found:** none outside P2.9.0–P2.9.20

## 7. Evidence Sources Consumed

| Source | Used |
|--------|------|
| P2.9-A | `agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md`, `shell_exit_seal_foundation.py`, `test_shell_exit_seal_foundation.py` |
| P2.9-A-R1 | `agent/reports/P2_9_A_R1_SHELL_EXIT_SEAL_FOUNDATION_EVIDENCE_REF_REPAIR.md` |
| old P2.9-B | `agent/reports/P2_9_B_SHELL_EXIT_SEAL_VERTICAL_SLICE_EVIDENCE_CONSUMPTION.md` (commits `9082da7`, hash record `6e8e44e`) |
| P2.REVIEW-A | `agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md` |
| P2.VSLICE-A | `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md`, `p2_command_palette_vslice.py` |
| tests | `test_p2_command_palette_vslice.py`, `test_p2_command_preflight.py`, `test_p2_vertical_slice_review.py`, `test_shell_exit_seal_foundation.py` |
| agent/STATE.md | prior pointer (incorrect premature P2.10+ handoff) |
| agent/ACTIVE_TASK.md | prior pointer |
| agent/REPORTS.md | index |

## 8. Old P2.9-B Reclassification

| Field | Value |
|-------|-------|
| Old report retained | **yes** — `agent/reports/P2_9_B_SHELL_EXIT_SEAL_VERTICAL_SLICE_EVIDENCE_CONSUMPTION.md` |
| Old report reverted | **no** |
| Old report deleted | **no** |
| Classification | **DONE as evidence/truth seal overlay** |
| DONE as granular P2.9.0–P2.9.20 implementation | **no** |
| Reason | Pack consumed P2.REVIEW-A/P2.VSLICE-A and produced section-level evidence matrix; did not implement true P2.9-B readiness/validation/evidence matrix contracts for P2.9.6–P2.9.10 |
| Scope correction | Rename in state only; filename unchanged. Treat as **P2.9-SEAL-OVERLAY** artifact, not true **P2.9-B** granular completion |

Required truth: The old P2.9-B artifact is retained. It is not reverted. It remains useful as a P2 evidence boundary. It cannot by itself close all P2.9.x roadmap checkpoints.

## 9. P2.9.x Roadmap Coverage Matrix

| Checkpoint | Roadmap Title | Evidence | Status | Truth Label | Gap | Next Action |
|------------|---------------|----------|--------|-------------|-----|-------------|
| P2.9.0 | Shell Exit Seal Intake / P2.8-D Handoff Gate | P2.9-A code/tests/report | DONE | CONTRACT_ONLY | Foundation only; not completed exit seal | — |
| P2.9.1 | Prior Shell Section Evidence Intake Contract | P2.9-A, P2.9-A-R1 ref repair | DONE | READ_ONLY | Not TRACE_VERIFIED | — |
| P2.9.2 | Shell Exit Criteria Catalog Contract | P2.9-A code/tests | DONE | CONTRACT_ONLY | Catalog is not validation execution | — |
| P2.9.3 | Exit Readiness Dimension / Boundary Contract | P2.9-A code/tests | DONE | CONTRACT_ONLY | Not product readiness | — |
| P2.9.4 | Unavailable Capability / No-Release / No-Product Boundary Contract | P2.9-A code/tests | DONE | CONTRACT_ONLY | Boundaries are contract firewalls only | — |
| P2.9.5 | Shell Exit Seal Foundation Result / P2.9-B Handoff Contract | P2.9-A code/tests | DONE | CONTRACT_ONLY | Handoff is not P2.9-B implementation | Implement true P2.9-B |
| P2.9.6 | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope) | old P2.9-B overlay (section matrix only) | PARTIAL | EVIDENCE_SEALED | No P2.9-B readiness contract module/tests for this checkpoint | true P2.9-B pack |
| P2.9.7 | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope) | old P2.9-B overlay (validation rollup absent at checkpoint level) | PARTIAL | EVIDENCE_SEALED | No validation execution matrix artifact | true P2.9-B pack |
| P2.9.8 | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope) | old P2.9-B overlay (P2.VSLICE-A consumed) | PARTIAL | PREFLIGHT_ONLY | Vertical slice is preflight-only; not full readiness matrix | true P2.9-B pack |
| P2.9.9 | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope) | old P2.9-B overlay (section seal matrix) | PARTIAL | EVIDENCE_SEALED | Section-level not checkpoint-level contracts | true P2.9-B pack |
| P2.9.10 | Shell Exit Seal Readiness / Validation / Evidence Matrix (P2.9-B scope) | old P2.9-B report/state sync only | PARTIAL | EVIDENCE_SEALED | No P2.9.10 integration tail / evidence matrix seal module | true P2.9-B pack |
| P2.9.11 | P2.9-C pack scope (title not in ROADMAP v5.5) | none | NOT_DONE | NOT_DONE | P2.9-C not started | defer until true P2.9-B |
| P2.9.12 | P2.9-C pack scope | none | NOT_DONE | NOT_DONE | — | defer |
| P2.9.13 | P2.9-C pack scope | none | NOT_DONE | NOT_DONE | — | defer |
| P2.9.14 | P2.9-C pack scope | none | NOT_DONE | NOT_DONE | — | defer |
| P2.9.15 | P2.9-C pack scope | none | NOT_DONE | NOT_DONE | — | defer |
| P2.9.16 | P2.9-D pack scope (title not in ROADMAP v5.5) | none | NOT_DONE | NOT_DONE | P2.9-D not started | defer until P2.9-C |
| P2.9.17 | P2.9-D pack scope | none | NOT_DONE | NOT_DONE | — | defer |
| P2.9.18 | P2.9-D pack scope | none | NOT_DONE | NOT_DONE | — | defer |
| P2.9.19 | P2.9-D pack scope | none | NOT_DONE | NOT_DONE | — | defer |
| P2.9.20 | P2.9-D pack scope | none | NOT_DONE | NOT_DONE | — | defer |

## 10. Covered / Partial / Missing Summary

| Category | Checkpoints |
|----------|-------------|
| DONE | P2.9.0, P2.9.1, P2.9.2, P2.9.3, P2.9.4, P2.9.5 |
| PARTIAL | P2.9.6, P2.9.7, P2.9.8, P2.9.9, P2.9.10 (old P2.9-B evidence overlay only) |
| NOT_DONE | P2.9.11–P2.9.20 |
| BLOCKED | none |
| UNAVAILABLE | granular ROADMAP titles for P2.9.6–P2.9.20 individually |
| N/A_WRONG_SCOPE | old P2.9-B treated as true P2.9-B granular completion (corrected by R1) |

**Coverage result:** P2.9.0–P2.9.5 DONE. True P2.9-B range P2.9.6–P2.9.10 **NOT DONE** (PARTIAL overlay only). P2.9.11–P2.9.20 **NOT DONE**. P2.10+ **not justified**.

## 11. Corrected Roadmap Pointer

| Field | Value |
|-------|-------|
| First missing/partial checkpoint | **P2.9.6** |
| Next exact P2.9.x checkpoint | **P2.9.6** |
| Next recommended pack | **true P2.9-B — P2.9.6–P2.9.10 Shell Exit Seal Readiness / Validation / Evidence Matrix** |
| True P2.9-B still needed | **yes** |
| True P2.9-C still needed | **yes** (after true P2.9-B) |
| True P2.9-D still needed | **yes** (after P2.9-C) |
| P2.10+ justified | **no** |
| P2.10+ remains NOT STARTED | **yes** |
| Pointer correction | Removed premature P2.10+ next pointer; old P2.9-B reclassified as evidence overlay retained |

## 12. What Is Not Changed

| Item | Changed |
|------|---------|
| Old P2.9-B report file | no |
| Old P2.9-B commits (`9082da7`, `6e8e44e`) | no |
| Roadmap numbering | no |
| P2.VSLICE-A behavior | no |
| Command preflight code | no |
| Shell feature implementation | no |
| P2.10+ code | no |

## 13. Validation Run

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_p2_command_palette_vslice.py -q
.venv/bin/python -m pytest tests/test_p2_command_preflight.py -q
.venv/bin/python -m pytest tests/test_p2_vertical_slice_review.py -q
.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m ruff check src tests
git status --short
```

| Check | Result |
|-------|--------|
| compileall | PASS |
| P2 command palette vertical slice tests | 10 passed |
| P2 command preflight tests | 6 passed |
| P2 vertical slice review tests | 9 passed |
| validation truth / drift gate regression | 18 passed |
| Golden Thread B regression | 17 passed |
| baseline mypy | PASS |
| ruff | PASS |
| git status after validation | clean (before R1 doc commit) |

**Validation not run:** full suite, coverage (not required for R1 reconciliation scope)

## 14. No-Scope-Expansion Proof

All forbidden items: **no** — docs/state/report reconciliation only.

## 15. Files Created / Modified

**Created:**

- `agent/reports/P2_9_B_R1_ROADMAP_GRANULARITY_RECONCILIATION_P2_9_X_COVERAGE_MATRIX.md`

**Modified:**

- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/ROADMAP.md` (active canon table pointer only)

## 16. Remaining Risks / Limitations

- ROADMAP v5.5 mirror lacks individual P2.9.6–P2.9.20 checkpoint titles; true P2.9-B implementation must read pack title and P2.9-A handoff contract, not assume overlay completion
- Old P2.9-B scope ambiguity may persist in historical report wording; R1 state pointer is corrected
- P2.10 handoff remains premature until P2.9.6–P2.9.20 are DONE or explicitly accepted
- Contract-only Shell sections remain contract-only
- Golden Thread B may still list P2.9-B NOT_DONE at node level (historical continuity; not mutated in R1)

## 17. Next Recommended Pack

**true P2.9-B — P2.9.6–P2.9.10 Shell Exit Seal Readiness / Validation / Evidence Matrix**

Do not start P2.10+ until true P2.9-B/C/D coverage is closed or operator explicitly accepts partial closure with evidence.

## 18. Commit Hash

`0ce98df` — `docs(shell): reconcile P2.9 roadmap coverage`

## 19. Final Git Status

Clean after commit `0ce98df`.
