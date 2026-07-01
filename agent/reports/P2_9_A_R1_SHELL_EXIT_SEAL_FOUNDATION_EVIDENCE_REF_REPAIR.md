# P2.9-A-R1 Shell Exit Seal Foundation Evidence Ref Repair

**Date:** 2026-07-01
**Repair:** P2.9-A-R1 - Shell Exit Seal Foundation Evidence Ref Repair
**Status:** DONE - evidence refs repaired; P2.9-B remains NOT DONE

## 1. Result Header

P2.9-A-R1 repaired P2.9-A prior-section evidence references and cleared the P2.9-B preflight hygiene blocker. P2.9-A remains DONE at foundation-only contract scope. P2.9-B remains NOT DONE and should be rerun next.

No runtime, policy, Custos, trace, memory, storage, command execution, product UI, LIVE, TRACE_VERIFIED, release seal, product readiness, P2 completion, or Shell completion was implemented or claimed.

## 2. Repair Scope

- Restored unrelated timestamp-only consent fixture churn.
- Repaired stale P2.9-A prior-section test path refs.
- Repaired mismatched prior-section commit refs using real git history.
- Added focused evidence-ref integrity tests.
- Updated report index and minimal state/progress docs.

## 3. Git / Worktree Preflight

- Branch: `master`
- Initial status: three dirty consent fixture files
- Dirty files: `tests/fixtures/consent/consent_record.json`, `tests/fixtures/consent/consent_request.json`, `tests/fixtures/consent/consent_revoked.json`
- Other dirty files: none
- Preflight result: PASS after timestamp-only consent fixture restore

## 4. Consent Fixture Dirty Diff Analysis

- `consent_record.json`: `granted_at` timestamp only
- `consent_request.json`: `created_at` timestamp only
- `consent_revoked.json`: `granted_at` and `revoked_at` timestamps only
- Diff type: timestamp-only fixture churn

## 5. Consent Fixture Action Taken

- Action: restored the three consent fixture files to `HEAD`
- Reason: unrelated timestamp-only fixture churn blocked P2.9-B preflight
- Included in commit: false

## 6. P2.9-A Evidence Ref Discovery

- Source file: `src/agentic_runtime/aurel_shell/shell_exit_seal_foundation.py`
- Focused test file: `tests/aurel_shell/test_shell_exit_seal_foundation.py`
- Repair test file: `tests/aurel_shell/test_shell_exit_seal_foundation_evidence_refs.py`
- Original report: `agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md`
- Prior-section evidence specs found: `_PRIOR_SECTION_EVIDENCE_SPECS` for P2.0 through P2.8

## 7. Broken/Stale Test Refs Found

The stale refs were active only in the P2.9-A prior-section evidence specs:

- `tests/aurel_shell/test_topbar_integration_tail.py`
- `tests/aurel_shell/test_local_navigation_integration_tail.py`
- `tests/aurel_shell/test_workspace_window_section_projection.py`
- `tests/aurel_shell/test_global_command_section_projection.py`
- `tests/aurel_shell/test_cross_surface_handoff_section_projection.py`
- `tests/aurel_shell/test_surface_projection_section_seal.py`

## 8. Test Ref Repairs Applied

- P2.1-D -> `tests/aurel_shell/test_shell_topbar_integration_tail.py`
- P2.2-D -> `tests/aurel_shell/test_shell_local_navigation_integration_tail.py`
- P2.3-D -> `tests/aurel_shell/test_shell_workspace_window_section_projection.py`
- P2.4-D -> `tests/aurel_shell/test_shell_global_command_section_projection.py`
- P2.5-D -> `tests/aurel_shell/test_shell_cross_surface_handoff_section_projection.py`
- P2.6-D -> `tests/aurel_shell/test_shell_surface_projection_section_seal.py`

## 9. Commit Ref Verification

Verified with `git cat-file -e <ref>^{commit}` and subject checks:

| Section | Commit ref | Subject |
|---|---:|---|
| P2.0 | `20c2ac9` | `feat(aurel-shell): seal P2.0 shell contract scope` |
| P2.1 | `d609434` | `feat(aurel-shell): seal P2.1 topbar contract scope` |
| P2.2 | `d5ba094` | `feat(aurel-shell): seal P2.2 local navigation contract scope` |
| P2.3 | `17aea2d` | `feat(aurel-shell): seal P2.3 workspace window section` |
| P2.4 | `c10c642` | `feat(aurel-shell): seal P2.4 command palette contracts` |
| P2.5 | `e279590` | `feat(aurel-shell): seal P2.5 handoff contracts` |
| P2.6 | `9c74a57` | `feat(aurel-shell): seal P2.6 projection contracts` |
| P2.7 | `43e7240` | `feat(aurel-shell): seal P2.7 binding contracts` |
| P2.8 | `da62fb8` | `feat(aurel-shell): seal P2.8 shell state contracts` |

## 10. Commit Ref Repairs / Ambiguities

Repaired mismatched refs:

- P2.0-F: `4565798` -> `20c2ac9`
- P2.1-D: `e279590` -> `d609434`
- P2.2-D: `196c3ba` -> `d5ba094`
- P2.3-D: `790f930` -> `17aea2d`
- P2.4-D: `04060b9` -> `c10c642`

Already correct:

- P2.5-D: `e279590`
- P2.6-D: `9c74a57`
- P2.7-D: `43e7240`
- P2.8-D: `da62fb8`

Commit refs marked ambiguous/unavailable: none.

## 11. Report Ref Verification

All active P2.9-A prior-section report refs point to existing files under `agent/reports/`.

## 12. Evidence Integrity Tests Added

Added `tests/aurel_shell/test_shell_exit_seal_foundation_evidence_refs.py`:

- `test_p2_9_a_prior_section_test_refs_exist`
- `test_p2_9_a_report_refs_exist_or_are_marked_unavailable`
- `test_p2_9_a_commit_refs_resolve_or_are_marked_ambiguous`
- `test_p2_9_a_no_stale_prior_section_test_paths_remain`
- `test_p2_9_a_repair_does_not_claim_trace_verified`
- `test_p2_9_a_repair_does_not_claim_live`
- `test_p2_9_a_repair_does_not_claim_release_or_product_readiness`
- `test_p2_9_a_repair_does_not_start_p2_9_b`
- `test_p2_9_a_repair_does_not_claim_p2_or_shell_complete`
- `test_p2_9_a_repair_does_not_change_runtime_policy_trace_memory_or_storage`

## 13. P2.9-A No-Overclaim Proof

- P2.9-B implemented: false
- P2.9-C started: false
- LIVE claimed: false
- TRACE_VERIFIED claimed: false
- Release seal claimed: false
- Product readiness claimed: false
- P2 complete claimed: false
- Shell complete claimed: false

## 14. No P2.9-B Implementation Proof

The only P2.9-B surface remains the existing handoff contract. `starts_p2_9_b` and `is_p2_9_b_implementation` remain false. No P2.9-B readiness matrix, validation evidence matrix, or command reference matrix was created.

## 15. No Runtime / Policy / Trace / Memory / Storage Change Proof

Only P2.9-A evidence refs, tests, and agent docs/reports were changed. No runtime, policy, Custos, trace, memory, storage, command execution, frontend, or product UI modules were modified.

## 16. Files Created / Modified

Created:

- `tests/aurel_shell/test_shell_exit_seal_foundation_evidence_refs.py`
- `agent/reports/P2_9_A_R1_SHELL_EXIT_SEAL_FOUNDATION_EVIDENCE_REF_REPAIR.md`

Modified:

- `src/agentic_runtime/aurel_shell/shell_exit_seal_foundation.py`
- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/ROADMAP.md`
- `agent/TESTS.md`

## 17. Validation Run

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_exit_seal_foundation.py -q
.venv/bin/python -m pytest tests/aurel_shell/test_shell_exit_seal_foundation_evidence_refs.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results:

- compileall: PASS
- P2.9-A focused tests: 16 passed
- Evidence ref integrity tests: 10 passed
- Nearby AurelShell tests: 1004 passed
- ruff: PASS
- mypy: PASS (`324 source files`)

## 18. What Was Deliberately Not Implemented

P2.9-B, P2.9-C, P2.9-D, P2.10, P2.11, P2.12, P2.13, Shell Exit Seal completion, release seal, product readiness, validation execution, final evidence validation, command reference matrix, readiness matrix, runtime behavior, policy behavior, Custos behavior, trace write, memory write, storage write, command execution, frontend/product UI, LIVE, TRACE_VERIFIED, P2 completion, and Shell completion.

## 19. Remaining Limitations

- Old roadmap/surface drift remains historical drift only; it was not rewritten.
- Golden Thread B / P1.8-to-P2.9 continuity remains a recommended later follow-up.
- No ambiguous commit refs remain in active P2.9-A prior-section evidence specs.
- This repair does not itself rerun or implement P2.9-B.

## 20. Next Required Step

Rerun P2.9-B - P2.9.6-P2.9.10 Shell Exit Seal Readiness / Validation / Evidence Matrix.

## 21. Commit Hash

Pending until this repair commit is created. Final response records the commit hash.

## 22. Final Git Status

Pending final commit. Expected final status: clean.
