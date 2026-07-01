# P2.9-B - Shell Exit Seal Readiness / Validation / Evidence Matrix

**Date:** 2026-07-01  
**Pack:** true P2.9-B  
**Scope:** P2.9.6-P2.9.10 only  
**Status:** DONE - SHELL_EXIT_READINESS_VALIDATION_EVIDENCE_MATRIX / P2_9_6_TO_P2_9_10_DONE / P2_9_C_NEXT / P2_10_BLOCKED

## 1. Result Header

True P2.9-B implements the Shell exit readiness / validation / evidence matrix for P2.9.6-P2.9.10. It adds checkpoint-level readiness contracts, validation checks, P2.VSLICE-A PREFLIGHT_ONLY evidence binding, checkpoint seal objects, and an integration tail that points to P2.9-C rather than P2.10.

This pack does not implement Shell LIVE, Shell product UI, arbitrary command execution, full command runtime, full API/event bridge, P2.9-C, P2.9-D, or P2.10+.

## 2. Scope

Covered:

- P2.9.6 - working label: Shell Exit Readiness Contract
- P2.9.7 - working label: Shell Exit Validation Matrix
- P2.9.8 - working label: Vertical Slice Evidence Binding
- P2.9.9 - working label: Checkpoint-Level Seal Evidence Matrix
- P2.9.10 - working label: Integration Tail / P2.9-C Handoff Contract

Working labels are not canonical ROADMAP title renames. ROADMAP checkpoint IDs were not changed.

## 3. R1 Input / Corrected Pointer

P2.9-B-R1 report found: `agent/reports/P2_9_B_R1_ROADMAP_GRANULARITY_RECONCILIATION_P2_9_X_COVERAGE_MATRIX.md`

R1 identifies P2.9.6 as the first missing/partial checkpoint and true P2.9-B / P2.9.6-P2.9.10 as next. It classifies old P2.9-B as retained evidence overlay and keeps P2.10+ NOT STARTED.

## 4. Git / Worktree Preflight

| Check | Result |
|-------|--------|
| Branch | `master` |
| Initial status | clean |
| Unrelated dirty files | none |
| P2.9-C/P2.9-D/P2.10+ dirty/untracked files | none |
| Shell/product dirty/untracked files | none |
| Runtime/sandbox/identity/policy dirty/untracked files | none |
| `.venv/bin/python` | present |
| Preflight result | PASS |

## 5. Evidence Consumed

| Evidence | Path | Classification |
|----------|------|----------------|
| P2.9-B-R1 coverage matrix | `agent/reports/P2_9_B_R1_ROADMAP_GRANULARITY_RECONCILIATION_P2_9_X_COVERAGE_MATRIX.md` | corrected pointer / evidence input |
| old P2.9-B overlay | `agent/reports/P2_9_B_SHELL_EXIT_SEAL_VERTICAL_SLICE_EVIDENCE_CONSUMPTION.md` | retained evidence overlay only |
| P2.REVIEW-A | `agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md` | vertical slice decision |
| P2.VSLICE-A | `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md` | PREFLIGHT_ONLY slice evidence |
| P2.9-A | `agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md` | P2.9.0-P2.9.5 foundation |
| P2.9-A-R1 | `agent/reports/P2_9_A_R1_SHELL_EXIT_SEAL_FOUNDATION_EVIDENCE_REF_REPAIR.md` | evidence ref repair |
| P1.ENF-A | `agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md` | enforcement bridge evidence |
| P1.ENF-D1 | `agent/reports/P1_ENF_D1_IDENTITY_KERNEL_INVARIANT_ENFORCEMENT_DEEPENING.md` | identity invariant evidence |
| P1.ENF-E | `agent/reports/P1_ENF_E_SANDBOX_SAFE_BACKEND_GATING_UNSAFE_LOCAL_HARDENING.md` | sandbox truth evidence |
| State / active / reports | `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/REPORTS.md` | source-of-truth sync |

## 6. P2.9.6 Readiness Contract

Implemented in `src/agentic_runtime/aurel_shell/shell_exit_readiness.py`:

- `ShellExitReadinessContract`
- `ShellExitReadinessDimension`
- required vs optional readiness dimensions
- allowed evidence kinds
- allowed truth labels
- forbidden claim checks
- DONE/PARTIAL/NOT_DONE decision support

Acceptance met: checkpoint status cannot be DONE unless all required readiness dimensions are DONE.

## 7. P2.9.7 Validation Matrix

Implemented:

- `ShellExitValidationMatrix`
- `ShellExitValidationCheck`
- `ShellExitValidationStatus`
- required check aggregation
- PASS / FAIL / NOT_RUN / UNAVAILABLE / N_A classification

Acceptance met: NOT_RUN and UNAVAILABLE are tracked separately and are never promoted to PASS.

## 8. P2.9.8 Vertical Slice Evidence Binding

Implemented:

- `ShellExitEvidenceRef`
- `ShellExitEvidenceBinding`
- `build_p2_vslice_a_evidence_binding()`

P2.VSLICE-A is bound as `PREFLIGHT_ONLY`. It supports vertical-slice evidence binding for P2.9.8 but does not support Shell LIVE, command execution, full command runtime, or safe sandbox claims.

## 9. P2.9.9 Checkpoint-Level Seal Evidence Matrix

Implemented:

- `ShellExitCheckpointSeal`
- `build_shell_exit_checkpoint_seal()`
- `build_shell_exit_evidence_bindings()`
- `render_p2_9_b_coverage_rows()`

Each checkpoint P2.9.6-P2.9.10 has a seal object with checkpoint ID, working label, status, truth label, readiness dimensions, validation checks, evidence bindings, remaining gaps, and next action.

## 10. P2.9.10 Integration Tail / P2.9-C Handoff

Implemented:

- `ShellExitIntegrationTail`
- `ShellExitP29BHandoff`
- `build_shell_exit_integration_tail()`
- `build_shell_exit_p29b_handoff()`

Handoff result:

- `next_pack = P2.9-C`
- `next_range = P2.9.11-P2.9.15`
- `p29c_handoff_ready = true`
- `p29d_handoff_ready = false`
- `p210_allowed = false`
- `p210_block_reason = P2.9-C and P2.9-D are not done`

## 11. P2.9.6-P2.9.10 Coverage Matrix

| Checkpoint | Working label | Status | Truth label | Evidence | Gap | Next |
|------------|---------------|--------|-------------|----------|-----|------|
| P2.9.6 | Shell Exit Readiness Contract | DONE | CONTRACT_ONLY | R1 matrix, old overlay, focused tests | no Shell LIVE / no execution / P2.9-C not implemented | covered by true P2.9-B |
| P2.9.7 | Shell Exit Validation Matrix | DONE | CONTRACT_ONLY | validation matrix object, focused tests | NOT_RUN/UNAVAILABLE honesty remains required | covered by true P2.9-B |
| P2.9.8 | Vertical Slice Evidence Binding | DONE | PREFLIGHT_ONLY | P2.VSLICE-A report/tests, old overlay | preflight only; no Shell LIVE or command execution | covered by true P2.9-B |
| P2.9.9 | Checkpoint-Level Seal Evidence Matrix | DONE | CONTRACT_ONLY | checkpoint seal objects and coverage rows | section seal is not product seal | covered by true P2.9-B |
| P2.9.10 | Integration Tail / P2.9-C Handoff Contract | DONE | CONTRACT_ONLY | integration tail and handoff object | P2.9-C/D not done; P2.10 blocked | P2.9-C |

## 12. What Is Sealed

- P2.9.6 readiness contract
- P2.9.7 validation matrix
- P2.9.8 vertical-slice evidence binding
- P2.9.9 checkpoint-level seal evidence matrix
- P2.9.10 integration tail / P2.9-C handoff
- true P2.9-B as P2.9.6-P2.9.10 readiness/validation/evidence matrix
- P2.9-C handoff readiness

## 13. What Is Not Sealed

- P2.9-C
- P2.9-D
- P2.10+
- Shell LIVE
- Full Shell product UI
- Arbitrary command execution
- Full command runtime
- Full API/event bridge
- Safe sandbox

## 14. Tests / Validation

| Check | Result |
|-------|--------|
| compileall | PASS |
| `tests/test_shell_exit_readiness.py` | 6 passed |
| `tests/test_shell_exit_validation_matrix.py` | 4 passed |
| `tests/test_p29b_shell_exit_evidence_matrix.py` | 7 passed |
| `tests/test_p2_command_palette_vslice.py` | 10 passed |
| `tests/test_p2_command_preflight.py` | 6 passed |
| `tests/test_p2_vertical_slice_review.py` | 9 passed |
| validation truth / drift gate regression | 18 passed |
| Golden Thread B regression | 17 passed |
| baseline mypy | PASS - 342 source files |
| ruff | PASS |
| git status after validation | in-scope files dirty/untracked before docs/report commit |

Validation not run: full suite, coverage, Bandit. These were not required for this contract/readiness pack by `agent/TESTS.md` lean validation doctrine or the dispatch validation list.

## 15. No-Scope-Expansion Proof

| Forbidden scope | Result |
|-----------------|--------|
| P2.9-C implemented | no |
| P2.9-D implemented | no |
| P2.10+ started | no |
| P2.VSLICE-A behavior changed | no |
| Command preflight behavior expanded | no |
| Arbitrary command execution implemented | no |
| Shell product UI implemented | no |
| Safe sandbox claimed | no |
| Shell LIVE claimed | no |
| Old P2.9-B deleted | no |
| Old P2.9-B reverted | no |
| Roadmap checkpoint IDs renamed | no |
| Roadmap numbering changed | no |

## 16. Files Created / Modified

Created:

- `src/agentic_runtime/aurel_shell/shell_exit_readiness.py`
- `tests/test_shell_exit_readiness.py`
- `tests/test_shell_exit_validation_matrix.py`
- `tests/test_p29b_shell_exit_evidence_matrix.py`
- `agent/reports/P2_9_B_SHELL_EXIT_SEAL_READINESS_VALIDATION_EVIDENCE_MATRIX.md`

Modified:

- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`

## 17. Remaining Risks / Limitations

- ROADMAP v5.5 lacks individual canonical titles for P2.9.6-P2.9.20; this report uses working labels only.
- P2.9-C remains NOT DONE and next.
- P2.9-D remains NOT DONE.
- P2.10 remains blocked.
- P2.VSLICE-A remains preflight-only.
- Shell product UI is not implemented.
- Command execution is not implemented.
- SAFE_VERIFIED sandbox remains unavailable without proof.
- Full suite, coverage, and Bandit were not run.

## 18. Next Recommended Pack

P2.9-C - Shell Exit Seal Finalization / P2.9.11-P2.9.15.

Exact P2.9-C scope should be confirmed from the next operator dispatch because ROADMAP v5.5 does not provide individual canonical titles for P2.9.11-P2.9.15.

## 19. Commit Hash

Implementation commit: `161fb8b` - `feat(shell): add P2.9-B exit readiness matrix`

## 20. Final Git Status

Clean after implementation commit `161fb8b`; this report hash field is recorded by the follow-up docs hash-record commit.
