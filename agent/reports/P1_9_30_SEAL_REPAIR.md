# P1.9.30-SEAL-REPAIR - Exit Seal Focused Repair

_Date: 2026-06-28_

## 1. Result Header

**Repair:** P1.9.30-SEAL-REPAIR - Exit Seal Focused Repair
**Status:** REPAIR_DONE_PARTIAL
**Final seal decision:** PARTIAL
**Feature coding performed:** Yes, limited to P1.9.30 seal model/test repair.
**P2 work performed:** No.
**Scope expanded:** No.

## 2. Repair Scope

This repair handled R1 from `P1_PRE_P2_REPAIR_MATRIX.md`: P1.9-D exit seal remained PARTIAL and blocked P2.

It did not perform the full pre-P2 validation/audit rerun. It did not implement P2, a P2 shell, API runtime, event bus, trace verification, Ledger proof, memory writes, Custos enforcement, or workflow/tool/runtime execution.

## 3. Why Repair Was Needed

The pre-P2 audit stopped because `agent/reports/P1_9_D_INTEGRATION_TAIL_PACK.md` recorded:

- Exit seal decision: `PARTIAL`
- P2 readiness: `NOT_READY_FOR_P2`
- Production LIVE path: unavailable
- Trace verification: unavailable

## 4. Evidence Inspected

- `agent/reports/P1_PRE_P2_FULL_AUDIT_AND_SEAL.md`
- `agent/reports/P1_PRE_P2_REPAIR_MATRIX.md`
- `agent/reports/P1_9_D_INTEGRATION_TAIL_PACK.md`
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/STATE.md`
- `agent/ROADMAP.md`
- `agent/TESTS.md`
- `agent/DECISIONS.md`
- `agent/ARCHITECTURE.md`
- `src/agentic_runtime/output_passport/exit_seal.py`
- `src/agentic_runtime/output_passport/integration_tail.py`
- `src/agentic_runtime/output_passport/projection.py`
- `tests/output_passport/test_passport_integration_tail_pack.py`

## 5. Root Cause of PARTIAL Seal

The PARTIAL seal was honest, not a failed implementation bug. P1.9.30 had contract/projection/CLI/docs/dev-fixture evidence, but it did not have production `LIVE_TESTED` operator-path evidence or actual `TRACE_VERIFIED` proof.

The existing P1.9-D contract did not permit converting `UNAVAILABLE_LIVE_PATH` into a sealed production outcome. The repair therefore kept the final decision PARTIAL and made the gate stricter and more explicit.

One concrete report-chain gap was found: `build_p1_9_exit_seal_checklist()` checked P1.9-A/B/C reports but did not check that the P1.9-D report existed. This is now repaired.

## 6. Code Changes

- Added explicit live-demo statuses: `LIVE_TESTED`, `DEV_FIXTURE_TESTED`, `PROJECTION_ONLY_TESTED`, `CLI_READ_ONLY_TESTED`, `UNAVAILABLE_LIVE_PATH`, `NOT_RUN`, `FAILED`.
- Added explicit unavailable reasons for production LIVE path and trace verification.
- Added P1.9-D report presence to the exit seal checklist.
- Added unavailable checklist items for production LIVE path and trace verification.
- Added `derive_p1_9_exit_seal_decision()` to derive `SEALED`, `NOT_SEALED`, `PARTIAL`, or `BLOCKED` from explicit evidence.
- Added `derive_p1_9_p2_readiness()` to derive P2 review readiness from seal decision only.
- Added `p2_readiness_status` to `P19ExitSeal`.
- Updated P1.9-D integration-tail result to consume the seal result readiness instead of duplicating readiness logic.

## 7. Test Changes

Created `tests/output_passport/test_passport_exit_seal_repair.py` with focused repair coverage for:

- P1.9-D report missing
- P1.9-A/B/C/D report chain missing
- fake `LIVE`
- fake `TRACE_VERIFIED`
- fake `EXIT_SEALED`
- P2 readiness derivation for `NOT_SEALED`, `PARTIAL`, `BLOCKED`, and `SEALED`
- default PARTIAL seal blocks P2
- DEV_FIXTURE demo is not LIVE
- projection-only demo is not LIVE
- CLI read-only inspect does not grant authority
- unavailable LIVE path reason
- unavailable trace verification reason
- non-LIVE demo cannot derive SEALED
- `LIVE_TESTED` builder path is unavailable without external runtime evidence

## 8. Seal Decision Rules After Repair

- Checklist failure or fake truth labels -> `BLOCKED`
- Demo not run, failed, or unavailable as live path -> `NOT_SEALED`
- Checklist passed but unavailable gates remain -> `PARTIAL`
- Checklist passed with no unavailable gates but demo is not `LIVE_TESTED` -> `PARTIAL`
- `SEALED` requires explicit `LIVE_TESTED` evidence and no unavailable gates

Current repo state still has unavailable production LIVE path and trace verification, so the repaired default decision remains `PARTIAL`.

## 9. Live Demo Truth Boundary

Current demo result:

- Status: `DEV_FIXTURE_TESTED`
- Truth label: `DEV_FIXTURE`
- Evidence: projection contract + read-only CLI inspect + invariant harness
- Unavailable reason: `UNAVAILABLE_LIVE_PATH` and `UNAVAILABLE_TRACE_VERIFICATION`

`DEV_FIXTURE_TESTED`, `PROJECTION_ONLY_TESTED`, and `CLI_READ_ONLY_TESTED` do not become `LIVE_TESTED`.

## 10. P2 Readiness Derivation

P2 readiness is derived only from the seal decision:

- `SEALED` -> `READY_FOR_P2_REVIEW`
- `NOT_SEALED` -> `NOT_READY_FOR_P2`
- `PARTIAL` -> `NOT_READY_FOR_P2`
- `BLOCKED` -> `BLOCKED`

No path returns `P2_READY` or coding readiness.

## 11. Validation Run

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest tests/output_passport/test_passport_exit_seal_repair.py -q` | PASS, 15 passed |
| `.venv/bin/python -m pytest tests/output_passport/test_passport_integration_tail_pack.py -q` | PASS, 21 passed |
| `.venv/bin/python -m compileall src tests` | PASS |
| `.venv/bin/python -m pytest tests/output_passport -q` | PASS, 136 passed |
| `.venv/bin/python -m ruff check src tests` | PASS |
| `.venv/bin/python -m mypy src/agentic_runtime` | PASS, 265 source files |
| `.venv/bin/python -m pytest tests -q -k "output_passport or passport"` | PASS, 142 passed, 5541 deselected |

## 12. Remaining Limitations

- P1.9.30 remains `PARTIAL`, not `SEALED`.
- Production LIVE operator path is unavailable.
- Actual trace verification is unavailable.
- API runtime remains contract-only.
- Event runtime remains contract-only.
- TUI product surface remains unavailable.
- Full pre-P2 audit/validation sweep remains a separate follow-up.

## 13. Repair Matrix Resolution

R1: addressed as a focused repair. The gate is now explicit and stricter, but final decision remains PARTIAL because missing evidence cannot be faked.

R2: not addressed. Full pre-P2 validation/audit rerun remains required after OMNI review or further repair.

R3: P1.9.30-related truth-label guard subset addressed. Broad repo truth-label adjudication remains separate.

## 14. Final Seal Decision

**PARTIAL**

Reason: P1.9.30 now has explicit seal-gate decision logic and passing focused validation, but production `LIVE_TESTED` evidence and actual `TRACE_VERIFIED` proof remain unavailable.

## 15. Next Step

OMNI Review this repair and decide whether PARTIAL is acceptable for a follow-up pre-P2 audit, or whether another targeted repair is required. P2 remains blocked unless a follow-up pre-P2 audit confirms readiness.

## 16. Commit Hash

Pending at report write.

## 17. Final Git Status

Pending at report write.
