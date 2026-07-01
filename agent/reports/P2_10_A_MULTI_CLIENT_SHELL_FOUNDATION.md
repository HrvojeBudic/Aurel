# P2.10-A — Multi-Client Shell Foundation / Client Parity Contract

**Date:** 2026-07-01  
**Pack:** P2.10-A  
**Scope:** P2.10-A only  
**Status:** DONE — MULTI_CLIENT_FOUNDATION / CLIENT_PARITY_CONTRACT / P2_10_B_NEXT / P2_10_B_C_D_NOT_DONE

## 1. Result Header

P2.10-A implements the first P2.10 multi-client Shell foundation layer: client taxonomy, shared Shell client state read model, client parity matrix, local run mode boundaries, surface availability across clients, and no-overclaim boundaries.

This pack does not implement P2.10-B/C/D, full web UI, Tauri desktop app, mobile app, arbitrary command execution, Shell LIVE, production API server, or full API/event bridge live path.

## 2. Scope

Covered:

- Client taxonomy (`ShellClientKind`, localities, run modes, truth labels, capabilities)
- Shared Shell client state contract (`ShellClientState`)
- Client parity matrix (`ShellClientParityMatrix`, 5 clients × 10 dimensions)
- Local run mode boundaries (honest CONTRACT_ONLY / READ_ONLY / UNAVAILABLE)
- Surface availability across seven canonical surfaces
- Global topbar / per-surface nav-inspector contracts
- No-overclaim boundary matrix (9 active boundaries)
- P2.9-D prerequisite gate consumption
- Focused tests (22 tests across 3 files)

Not covered:

- P2.10-B local web shell skeleton
- P2.10-C Tauri desktop shell
- P2.10-D CLI/TUI parity binding
- Runnable web/desktop/mobile apps
- Command execution or Shell LIVE

## 3. P2.9-D Prerequisite Gate

| Gate | Result |
|------|--------|
| P2.9-D report found | yes |
| P2.9-D report path | `agent/reports/P2_9_D_SHELL_EXIT_SEAL_FINAL_TAIL.md` |
| P2.9-D report indexed | yes — `agent/REPORTS.md` |
| P2.9-D seals P2.9 as honest Shell exit foundation | yes |
| P2.9-D allows P2.10-A as next pointer | yes |
| P2.10+ already started before pack | no |
| Gate result | PASS |

## 4. Git / Worktree Preflight

| Check | Result |
|-------|--------|
| Branch | `master` |
| Initial status | clean |
| Unrelated dirty files | none |
| P2.10-B/C/D dirty/untracked files | none |
| Shell/product/frontend dirty/untracked files | none |
| Runtime/sandbox/identity/policy dirty/untracked files | none |
| `.venv/bin/python` | present |
| Preflight result | PASS |

## 5. Evidence Consumed

| Evidence | Path | Classification |
|----------|------|----------------|
| P2.9-D | `agent/reports/P2_9_D_SHELL_EXIT_SEAL_FINAL_TAIL.md` | prerequisite / P29_SEALED / P2.10-A handoff |
| P2.9-C | `agent/reports/P2_9_C_SHELL_EXIT_SEAL_FINALIZATION.md` | inherited via P2.9-D |
| true P2.9-B | `agent/reports/P2_9_B_SHELL_EXIT_SEAL_READINESS_VALIDATION_EVIDENCE_MATRIX.md` | inherited |
| P2.9-B-R1 | `agent/reports/P2_9_B_R1_ROADMAP_GRANULARITY_RECONCILIATION_P2_9_X_COVERAGE_MATRIX.md` | inherited |
| old P2.9-B overlay | `agent/reports/P2_9_B_SHELL_EXIT_SEAL_VERTICAL_SLICE_EVIDENCE_CONSUMPTION.md` | retained overlay |
| P2.REVIEW-A | `agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md` | vertical slice decision |
| P2.VSLICE-A | `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md` | PREFLIGHT_ONLY |
| P2.0-E | `agent/reports/P2_0_E_OPERATOR_DEMO_SNAPSHOT_REGRESSION.md` | legacy multi-client parity seed |
| Surface registry | `src/agentic_runtime/aurel_shell/surface_registry.py` | seven-surface canon |
| Topbar | `src/agentic_runtime/aurel_shell/topbar.py` | global topbar contract |
| Nav boundary | `src/agentic_runtime/aurel_shell/navigation_boundary.py` | no universal left nav |
| CLI/TUI binding | `src/agentic_runtime/aurel_shell/cli_binding.py` | CLI read-only / TUI unavailable |
| P2.0-E client consistency | `src/agentic_runtime/aurel_shell/client_consistency.py` | legacy ClientKind retained |

## 6. Client Taxonomy

Implemented in `src/agentic_runtime/aurel_shell/multi_client_foundation.py`:

| ShellClientKind | Locality | Default run mode | Truth label |
|-----------------|----------|------------------|-------------|
| WEB | LOCAL_DEV | WEB_DEV_SHELL_CONTRACT | CONTRACT_ONLY |
| DESKTOP_TAURI | LOCAL_DESKTOP | DESKTOP_TAURI_CONTRACT | CONTRACT_ONLY |
| MOBILE_FOUNDATION | MOBILE_CONTRACT_ONLY | MOBILE_CONTRACT_ONLY | CONTRACT_ONLY |
| CLI | LOCAL_TERMINAL | CLI_TUI_CONTRACT | READ_ONLY |
| TUI | LOCAL_TERMINAL | UNAVAILABLE | UNAVAILABLE |

Legacy mapping to P2.0-E `ClientKind`: WEB→WEB, DESKTOP_TAURI→DESKTOP, MOBILE_FOUNDATION→MOBILE, CLI→CLI, TUI→TUI.

## 7. Shared Shell Client State Contract

`ShellClientState` is JSON-serializable, deterministic, and includes:

- active/available clients
- active/available surfaces (seven canonical surfaces)
- surface availability rollup
- global topbar contract (selector + SYSTEM/Settings right-side)
- per-surface left nav / right inspector contracts
- capabilities per client kind
- command palette availability: `PREFLIGHT_ONLY`
- truth labels and evidence refs
- local run mode and limitations

## 8. Client Parity Matrix

`ShellClientParityMatrix` — 50 entries (5 clients × 10 dimensions):

- SURFACE_SELECTOR_VISIBLE
- SURFACE_AVAILABILITY_VISIBLE
- TRUTH_LABELS_VISIBLE
- EVIDENCE_REFS_VISIBLE
- COMMANDS_LIST_VISIBLE
- COMMAND_PREFLIGHT_VISIBLE (PREFLIGHT_ONLY when supported)
- LOCAL_RUN_MODE_VISIBLE
- RIGHT_INSPECTOR_CONTRACT_VISIBLE
- LEFT_NAV_CONTRACT_VISIBLE
- CLIENT_LIMITATIONS_VISIBLE

Parity summary: client parity preserves the same truth labels, evidence refs, and availability states — not identical UI.

## 9. Local Run Mode Boundaries

| Run mode | Locally runnable | Launch command | Claim |
|----------|------------------|----------------|-------|
| PYTHON_BACKEND_ONLY | no | none | READ_ONLY contract |
| WEB_DEV_SHELL_CONTRACT | no | none | no npm scaffold |
| DESKTOP_TAURI_CONTRACT | no | none | no Tauri scaffold |
| CLI_TUI_CONTRACT (CLI) | no | none | read-only inspect |
| CLI_TUI_CONTRACT (TUI) | no | none | UNAVAILABLE |
| MOBILE_CONTRACT_ONLY | no | none | contract only |

## 10. Surface Availability Across Clients

All seven surfaces (Aurel CRO, HQ, CORP, HUB, IDE, SYSTEM, Settings) are CONTRACT_ONLY available for WEB, DESKTOP_TAURI, MOBILE_FOUNDATION, and CLI. TUI is unsupported for surface viewing.

Top bar contract: surface selector surfaces (CRO/HQ/CORP/HUB/IDE) vs right-side SYSTEM/Settings. Per-surface left nav and right inspector contracts reference P2.0-B / P2.2 navigation law.

## 11. No-Overclaim Boundaries

All nine boundaries active:

- NO_FULL_LOCAL_APP_CLAIM
- NO_DESKTOP_APP_COMPLETE_CLAIM
- NO_MOBILE_APP_CLAIM
- NO_SHELL_LIVE_CLAIM
- NO_COMMAND_EXECUTION_CLAIM
- NO_SAFE_SANDBOX_CLAIM_UNLESS_PROVEN
- NO_PRODUCTION_API_CLAIM
- NO_FULL_API_EVENT_BRIDGE_LIVE_CLAIM
- NO_P2_10_B_C_D_CLAIM

## 12. P2.10-A Coverage Matrix

| Area | Status | Truth | Evidence | Gap | Next |
|------|--------|-------|----------|-----|------|
| Client taxonomy | DONE | CONTRACT_ONLY | multi_client_foundation.py, tests | no runnable clients | P2.10-B |
| Shared Shell client state | DONE | CONTRACT_ONLY | ShellClientState, tests | no live frontend | P2.10-B |
| Client parity matrix | DONE | CONTRACT_ONLY | 50 parity entries, tests | TUI limited parity | P2.10-D |
| Local run modes | DONE | CONTRACT_ONLY/UNAVAILABLE | run mode entries, tests | no launch commands | P2.10-B/C |
| Surface availability | DONE | CONTRACT_ONLY | 7 surfaces, topbar contract | not live UI | P2.10-B |
| No-overclaim boundaries | DONE | CONTRACT_ONLY | 9 boundaries, tests | — | P2.10-B |

## 13. What Is Sealed

- P2.10-A multi-client Shell foundation / client parity contract
- Canonical `ShellClientKind` taxonomy with legacy P2.0-E mapping
- Shared `ShellClientState` read model for future clients
- Truth-preserving parity matrix
- Honest local run mode boundaries
- Surface availability and topbar/nav-inspector contracts
- P2.10-B handoff readiness (`p210b_ready=True`, `p210b_not_started=True`)

## 14. What Is Not Sealed

- P2.10-B local web shell skeleton
- P2.10-C Tauri desktop shell
- P2.10-D CLI/TUI parity binding
- Full local app
- Runnable web app
- Runnable desktop/Tauri app
- Mobile app
- Shell LIVE
- Arbitrary command execution
- Full command runtime
- Production API server
- Full API/event bridge live
- Safe sandbox proof

## 15. Tests / Validation

Focused tests:

```bash
.venv/bin/python -m pytest tests/test_p210a_multi_client_foundation.py -q
.venv/bin/python -m pytest tests/test_shell_client_parity_matrix.py -q
.venv/bin/python -m pytest tests/test_shell_client_run_modes.py -q
```

Regressions run: P2.9-D/C/B seal tests, P2 command palette/preflight/review, validation truth/drift gates, Golden Thread B, P2.0-E operator demo (140 passed). compileall PASS. mypy PASS on new module. ruff PASS.

Full suite and coverage: NOT_RUN (not claimed).

## 16. No-Scope-Expansion Proof

| Check | Result |
|-------|--------|
| P2.10-B implemented | no |
| P2.10-C implemented | no |
| P2.10-D implemented | no |
| Full web app implemented | no |
| Tauri desktop app implemented | no |
| Mobile app implemented | no |
| Arbitrary command execution implemented | no |
| Command preflight behavior changed | no |
| P2.VSLICE-A behavior changed | no |
| Policy/identity/sandbox behavior changed | no |
| Shell LIVE claimed | no |
| Full local app claimed | no |
| Desktop app runnable claimed | no |
| Mobile app runnable claimed | no |

## 17. Files Created / Modified

Created:

- `src/agentic_runtime/aurel_shell/multi_client_foundation.py`
- `tests/test_p210a_multi_client_foundation.py`
- `tests/test_shell_client_parity_matrix.py`
- `tests/test_shell_client_run_modes.py`
- `agent/reports/P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md`

Modified:

- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/TESTS.md`

## 18. Remaining Risks / Limitations

- No runnable web/desktop/mobile path until P2.10-B/C
- P2.0-E `ClientKind` naming differs from P2.10-A `ShellClientKind` (legacy mapping provided)
- TUI parity intentionally limited (CLI binding unavailable pattern retained)
- TypeScript/Rust consumers not yet wired
- Full pytest suite and coverage not run in this pack

## 19. Next Recommended Pack

**P2.10-B — Local Web Shell Skeleton / Contract-Bound Client Read Model**

P2.10-B/C/D remain NOT_DONE. No Shell LIVE or command execution claim.

## 20. Commit Hash

`0e177e6`

## 21. Final Git Status

Clean after commit on `master`.
