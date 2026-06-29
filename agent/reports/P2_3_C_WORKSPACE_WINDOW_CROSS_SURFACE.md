# P2.3-C — Cross-Surface Window Handoff / Conflict / Docking Semantics

**Pack ID:** P2.3-C
**Section:** P2.3 — Floating Windows / Workspace State
**Covered checkpoints:** P2.3.11-P2.3.15
**Status:** DONE — contract/read-model scope only
**Report date:** 2026-06-29
**Next pack:** P2.3-D — likely P2.3.16-P2.3.20 P2.3 Integration Tail / Projection / Binding / Docs / Section Seal

## 1. Result Header

P2.3-C adds contract-only cross-surface window handoff, docking/undocking
intent, conflict/collision state, window-surface compatibility constraints, and
a cross-surface window projection result over P2.3-A and P2.3-B. It does not
create UI, route runtime, drag/drop, docking UI, layout engine, conflict
resolver runtime, permission enforcement, Custos integration, storage,
memory/trace writes, runtime mutation, product behavior, P2.3-D, P2.10, or
P2.13.

## 2. Dispatch Gate Evidence

| Gate item | Evidence |
| --- | --- |
| Current branch | `master` |
| Initial worktree | clean |
| AUDIT-REPAIR-001 | report and commit chain present |
| P2.3-A | report, projection seed, side-effect proof, and commit chain present |
| P2.3-B | report, projection result, side-effect proof, and commit chain present |
| P2.3-B OMNI marker | missing locally; operator explicitly instructed: "ignore OMNI aceptance evidance and contiune" |
| Gate result | PASS by operator waiver, recorded as waiver not false OMNI evidence |

## 3. AUDIT-REPAIR-001 Gate Evidence

`agent/reports/AUDIT_REPAIR_001_TEST_PORTABILITY_P2_2_B_CANON_SYNC.md` records
F-001 fixed through portable repo-root discovery, F-002 canon sync confirmed,
no P2.3-C/P2.3-D/P2.10/P2.13 work, no LIVE/TRACE_VERIFIED/RELEASE_SCOPE claim,
and clean final git status.

## 4. P2.3-A Gate Evidence

`agent/reports/P2_3_A_WORKSPACE_STATE_FOUNDATION.md` records P2.3-A complete
with `WorkspaceStateProjectionSeed`, side-effect proof, final clean evidence,
and no P2.3-C/P2.3-D/P2.10/P2.13 implementation. The missing local P2.3-A
OMNI acceptance marker was previously waived only for the P2.3-B dispatch.

## 5. P2.3-B Gate Evidence

`agent/reports/P2_3_B_WORKSPACE_WINDOW_SEMANTICS.md` records P2.3-B complete
with `WorkspaceFocusStackProjectionResult`, side-effect proof, commit hash
`650dddf`, report-hash docs commit `90bab5c`, and no P2.3-C/P2.3-D/P2.10/P2.13
implementation. The missing local P2.3-B OMNI acceptance marker is waived only
for this P2.3-C dispatch by explicit operator instruction. This report does
not claim false OMNI acceptance evidence.

## 6. Roadmap Authority Chain

Roadmap v5.5 remains canonical. Local `agent/ROADMAP.md` is a progress mirror.
Official section name remains `P2.3 — Floating Windows / Workspace State`.
P2.3-C extends P2.3-A/B at contract/read-model semantics scope only.

## 7. Execution Shape Used

Selected shape: P2.3 Cross-Surface Window Semantics Contract Pack /
Orchestrated Single Executor. No split was needed. UI/product, browser app,
Tauri, route runtime, drag/drop, docking UI, layout engine, conflict resolver,
permission enforcement, Custos, API server, event bus, P2.3-D, P2.10, and
P2.13 shapes were rejected.

## 8. Dependency on P2.3-A/B Projection Results

`workspace_window_cross_surface.py` reuses:

- P2.3-A `build_p2_3_a_workspace_state_foundation_result()` and its
  `WorkspaceStateProjectionSeed` as `foundation_ref`.
- P2.3-B `build_p2_3_b_workspace_window_semantics_result()` and its
  `WorkspaceFocusStackProjectionResult` as `semantics_ref`.

No P2.3-A identity/workspace/lifecycle/placement contracts or P2.3-B
focus/stack/group/restore contracts are duplicated.

## 9. Roadmap Coverage Matrix P2.3.11-P2.3.15

P2.3.11 — DONE
Capsule name: Cross-Surface Window Handoff Contract
Evidence: `CrossSurfaceWindowHandoffContract`, closed-world handoff intent/reason/truth enums
Tests: `test_p2_3_11_*`
Truth label: `CROSS_SURFACE_WINDOW_HANDOFF_CONTRACT / NOT_ROUTE_RUNTIME`
Unavailable reason: route/surface-switch runtime unavailable by contract
Limitations: declarative handoff only; no route execution, surface runtime switch, or frontend movement

P2.3.12 — DONE
Capsule name: Window Docking / Undocking Intent Contract
Evidence: `WindowDockingIntentContract`, `WindowDockingMode`, `WindowDockingRegion`
Tests: `test_p2_3_12_*`
Truth label: `WINDOW_DOCKING_INTENT_CONTRACT / NOT_DOCKING_UI`
Unavailable reason: docking UI and drag/drop unavailable by contract
Limitations: intent grammar only; no docking UI, drag/drop, or real layout change

P2.3.13 — DONE
Capsule name: Window Conflict / Collision Contract
Evidence: `WindowConflictContract`, `WindowConflictKind`, `WindowConflictSeverity`
Tests: `test_p2_3_13_*`
Truth label: `WINDOW_CONFLICT_CONTRACT / NOT_CONFLICT_RESOLVER_RUNTIME`
Unavailable reason: conflict resolver and real collision detection unavailable by contract
Limitations: declarative conflict evidence only; no resolver, collision detector, or layout engine

P2.3.14 — DONE
Capsule name: Window Constraint / Compatibility Contract
Evidence: `WindowSurfaceCompatibilityContract`, `WindowCompatibilityKind`
Tests: `test_p2_3_14_*`
Truth label: `WINDOW_SURFACE_COMPATIBILITY_CONTRACT / NOT_PERMISSION_ENFORCEMENT`
Unavailable reason: permission enforcement and Custos integration unavailable by contract
Limitations: compatibility only; no permission grant, denial, or runtime block

P2.3.15 — DONE
Capsule name: Cross-Surface Window Projection Result
Evidence: `CrossSurfaceWindowProjectionResult`, `P23CWindowCrossSurfaceSemanticsResult`
Tests: `test_p2_3_15_*`
Truth label: `CROSS_SURFACE_WINDOW_PROJECTION_RESULT / NOT_PRODUCT_BEHAVIOR`
Unavailable reason: frontend/product behavior unavailable by contract
Limitations: bundles P2.3-C semantics over P2.3-A/B projections only

## 10. Cross-Surface Window Handoff Contract Proof

Handoff contracts represent `window_id`, source/target canonical surface IDs,
workspace state ID, handoff intent/reason, payload refs, availability, and
unavailable reason. `executes_route`, `switches_surface_runtime`,
`moves_frontend_window`, `mutates_runtime`, `writes_memory`, and `writes_trace`
are false.

## 11. Window Docking / Undocking Intent Contract Proof

Docking contracts represent target surface, region, mode, reason,
availability, and unavailable reason. `creates_docking_ui`,
`executes_drag_drop`, `changes_real_layout`, `mutates_runtime`, `writes_memory`,
and `writes_trace` are false.

## 12. Window Conflict / Collision Contract Proof

Conflict contracts represent window IDs, conflict kind/reason, severity,
suggested resolution intent, availability, and unavailable reason.
`detects_real_collision`, `resolves_conflict_runtime`, `changes_layout`,
`mutates_runtime`, `writes_memory`, and `writes_trace` are false.

## 13. Window Constraint / Compatibility Contract Proof

Compatibility contracts represent window kind, source/target surfaces,
contract allowance, compatibility kind/reason, operator review flag, and future
permission-check flag. `enforces_permission`, `grants_permission`,
`denies_permission`, `blocks_runtime`, and `mutates_runtime` are false.

## 14. Cross-Surface Window Projection Result Proof

`CrossSurfaceWindowProjectionResult` sets `section_id=P2.3`,
`created_for_pack=P2.3-C`, `next_pack=P2.3-D`, references P2.3-A/B through
`foundation_ref` and `semantics_ref`, includes all P2.3-C contract groups and
side-effect proof, and keeps frontend state store, product behavior, P2.3-D,
P2.10, and P2.13 starts false.

## 15. No Drag/Drop / Docking UI / Route Runtime Proof

No route runtime, routes, drag/drop, docking UI, undocking UI, frontend window
movement, or surface runtime switch is created. The contracts are declarative
read-model records only.

## 16. No Conflict Resolver / Layout Engine Proof

No real collision detection, automatic conflict resolution, resolver runtime,
layout engine, CSS, or real layout change is created.

## 17. No Permission Enforcement / Custos Proof

Compatibility does not grant, deny, enforce, or block permission and does not
integrate Custos. Future permission checks are represented only as contract
flags.

## 18. No Storage / Memory / Trace Proof

All local/browser storage, memory, trace, runtime mutation, source-of-truth,
event, API, and runtime-event side-effect fields are false.

## 19. No Frontend / Browser / Tauri / Product Behavior Proof

P2.3-C creates no frontend UI, browser app, Tauri app, desktop app, frontend
components, product behavior, LIVE claim, TRACE_VERIFIED claim, or release
scope claim.

## 20. Truth Label / DEV_FIXTURE Boundary Proof

Truth labels are contract/read-model labels:
`CROSS_SURFACE_WINDOW_HANDOFF_CONTRACT`, `WINDOW_DOCKING_INTENT_CONTRACT`,
`WINDOW_CONFLICT_CONTRACT`, `WINDOW_SURFACE_COMPATIBILITY_CONTRACT`, and
`CROSS_SURFACE_WINDOW_PROJECTION_RESULT`. Projection truth includes
`DEV_FIXTURE`, `READ_MODEL_RESULT_ONLY`, `NOT_FRONTEND_STATE_STORE`, and
`NOT_PRODUCT_BEHAVIOR`.

## 21. Surface Taxonomy Drift Status

**SURFACE_TAXONOMY_DRIFT:** YES — inherited legacy
Forum/Archivium/A-Hub/S-Hub/L-Hub/Workspace references remain
drift/future/historical references only. P2.3-C does not activate them as
canonical P2 surfaces.

## 22. Side-Effect / No-Authority Proof

`P23CSideEffectProof` has all fields false, including frontend UI, browser app,
Tauri app, desktop app, frontend movement, surface switch, route runtime,
routes, drag/drop, docking/undocking UI, layout engine, CSS, real layout
change, conflict resolver, collision detection, automatic resolution,
permission enforcement/grant/denial, Custos, API server, HTTP routes, event
bus, runtime events, local/browser storage, memory, trace, runtime mutation,
source of truth, LIVE, TRACE_VERIFIED, RELEASE_SCOPE, P2.3-D, P2.10, and
P2.13.

## 23. Files Created / Modified

Created:
- `src/agentic_runtime/aurel_shell/workspace_window_cross_surface.py`
- `tests/aurel_shell/test_shell_workspace_window_cross_surface.py`
- `agent/reports/P2_3_C_WORKSPACE_WINDOW_CROSS_SURFACE.md`

Modified:
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/ROADMAP.md`
- `agent/STATE.md`
- `agent/ARCHITECTURE.md`
- `agent/DECISIONS.md`
- `agent/TESTS.md`

## 24. Tests Added / Updated

Added `tests/aurel_shell/test_shell_workspace_window_cross_surface.py` with
focused coverage for imports, dependencies, closed-world enums, handoff,
docking, conflict, compatibility, projection, side-effect proof, serialization,
canonical surface preservation, inherited surface taxonomy drift, and future
pack boundaries.

## 25. Validation Run

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_workspace_window_cross_surface.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall PASS; focused P2.3-C tests 15 passed; `tests/aurel_shell`
539 passed; ruff PASS; mypy PASS (302 source files).

## 26. What Was Deliberately Not Implemented

No UI, browser app, Tauri app, frontend component, frontend window movement,
surface runtime switch, route runtime, route handler, route execution,
drag/drop, docking UI, undocking UI, CSS/frontend layout, layout engine, real
collision detection, conflict resolver runtime, automatic conflict resolution,
permission enforcement, permission grant, permission denial, runtime block,
Custos integration, API server, HTTP routes, event bus, runtime event emission,
local/browser storage, memory writes, trace writes, runtime mutation,
source-of-truth store, P2.3-D, P2.10, P2.13, LIVE, TRACE_VERIFIED, or release
scope.

## 27. Limitations

P2.3-C is not operator-testable product behavior. It is a contract/read-model
pack for future consumers. The P2.3-B OMNI acceptance marker is missing locally
and waived only for this dispatch by operator instruction.

## 28. Next Recommended Step

P2.3-D — likely P2.3.16-P2.3.20 P2.3 Integration Tail / Projection / Binding /
Docs / Section Seal.

## 29. Commit Hash

Implementation commit: `b0c09ec18e4f528738247474d24dc35504d83d5b`
Report-hash docs commit: this follow-up commit records the implementation hash.

## 30. Final Git Status

Clean after implementation commit before report-hash update. Final clean status
confirmed after the report-hash docs commit.
