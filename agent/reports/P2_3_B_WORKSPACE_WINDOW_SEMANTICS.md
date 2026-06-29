# P2.3-B — Floating Window Focus / Stack / Grouping / Restore Semantics

**Pack ID:** P2.3-B  
**Section:** P2.3 — Floating Windows / Workspace State  
**Domain:** P2 — AurelShell Seven-Surface Cognitive OS Foundation  
**Covered checkpoints:** P2.3.6–P2.3.10  
**Status:** DONE  
**Date:** 2026-06-29  
**Next pack:** P2.3-C — likely P2.3.11–P2.3.15 Cross-Surface Window Handoff / Conflict / Docking Semantics

---

## 1. Result Header

P2.3-B adds contract-only focus, stack/layer order, group/collection,
restore/resume, and workspace focus/stack projection result objects under
`src/agentic_runtime/aurel_shell/workspace_window_semantics.py`.

No product UI, browser/Tauri app, frontend component activation, browser focus,
focus manager runtime, z-index runtime, CSS/layout engine, draggable/resizable
windows, storage, route runtime, API server, event bus, memory/trace writes,
runtime mutation, P2.3-C, P2.10, or P2.13 implementation.

## 2. Dispatch Gate Evidence

| Gate | Evidence |
|------|----------|
| Branch / worktree | `master`; clean before edits |
| AUDIT-REPAIR-001 report | present: `agent/reports/AUDIT_REPAIR_001_TEST_PORTABILITY_P2_2_B_CANON_SYNC.md` |
| AUDIT-REPAIR-001 final state | F-001 fixed; F-002 confirmed; full suite green in report |
| P2.3-A report | present: `agent/reports/P2_3_A_WORKSPACE_STATE_FOUNDATION.md` |
| P2.3-A implementation commit | `1271881fb4d8ac93bbe2172f7dd2ce71bac7bd99` |
| P2.3-A report-hash docs commit | `2e3f6d1` |
| P2.3-A OMNI marker | missing locally; operator explicitly instructed: "Ignore OMNI acceptance evidence and implement." |
| Gate result | PASS by operator waiver, recorded as waiver not false OMNI evidence |

## 3. AUDIT-REPAIR-001 Gate Evidence

AUDIT-REPAIR-001 report records F-001 fixed via portable `tests/repo_root.py`,
F-002 confirmed synced, no P2.3-B/P2.3-C/P2.10/P2.13 work, no LIVE,
TRACE_VERIFIED, or RELEASE_SCOPE claim, and clean final git status.

## 4. P2.3-A Gate Evidence

P2.3-A report records P2.3.0–P2.3.5 DONE, the section intake gate, floating
window identity contracts, shell workspace state contract, lifecycle/availability
contracts, placement/layering intent contracts, workspace state projection seed,
and all-false side-effect proof. P2.3-A records no UI, browser/Tauri app,
draggable window, window manager, layout/z-index runtime, storage, memory/trace,
runtime mutation, P2.3-B, P2.3-C, P2.10, or P2.13 work.

The missing local P2.3-A OMNI acceptance marker is waived only for this P2.3-B
dispatch by explicit operator instruction. This report does not claim false OMNI
acceptance evidence.

## 5. Roadmap Authority Chain

1. Aurel Roadmap v5.5 = canonical roadmap truth
2. CodeOps = validation/report/git discipline
3. AUDIT-REPAIR-001 = repair/test-portability/canon-sync gate
4. P2.3-A = P2.3-B start foundation
5. P2.3-A workspace state projection seed = direct foundation ref
6. P2.3-A side-effect proof = no-UI/no-runtime/no-storage precedent
7. P2.2-D seal/readiness inherited through P2.3-A
8. P2.1 surface registry / official P2 surfaces inherited through P2.3-A
9. `agent/TESTS.md` = validation baseline
10. local `agent/ROADMAP.md` = progress mirror only

## 6. Execution Shape Used

Selected shape: P2.3 Workspace Window Semantics Contract Pack /
Orchestrated Single Executor.

Scope remained contract/read-model only. No split was required.

## 7. Dependency on P2.3-A Projection Seed

`WorkspaceFocusStackProjectionResult.foundation_ref` and
`P23BWorkspaceWindowSemanticsResult.foundation_ref` point to the P2.3-A
`WorkspaceStateProjectionSeed` as:

`p2_3_workspace_state_projection_seed:<projection_hash>`

P2.3-B reuses P2.3-A identity/window/workspace/lifecycle/placement contracts and
does not duplicate them.

## 8. Roadmap Coverage Matrix P2.3.6–P2.3.10

### P2.3.6 — DONE
Capsule name: Floating Window Focus Intent Contract  
Evidence: `FloatingWindowFocusIntentContract`, `build_floating_window_focus_intent_contracts()`  
Tests: `test_p2_3_6_*`, focus contract coverage  
Truth label: FLOATING_WINDOW_FOCUS_INTENT_CONTRACT / DECLARATIVE_INTENT_ONLY / NOT_FOCUS_MANAGER / NOT_BROWSER_FOCUS  
Unavailable reason: focus manager runtime unavailable by contract  
Limitations: declarative active-window candidate only; no browser focus or frontend activation

### P2.3.7 — DONE
Capsule name: Floating Window Stack / Layer Order Contract  
Evidence: `FloatingWindowStackOrderContract`, `build_floating_window_stack_order_contract()`  
Tests: `test_p2_3_7_*`  
Truth label: FLOATING_WINDOW_STACK_ORDER_CONTRACT / READ_MODEL_ORDER_ONLY / NOT_Z_INDEX_RUNTIME / NOT_LAYOUT_ENGINE  
Unavailable reason: z-index/layout runtime unavailable by contract  
Limitations: read-model ordering only; no CSS, z-index, or layout engine

### P2.3.8 — DONE
Capsule name: Floating Window Group / Collection Contract  
Evidence: `FloatingWindowGroupContract`, `build_floating_window_group_contract()`  
Tests: `test_p2_3_8_*`  
Truth label: FLOATING_WINDOW_GROUP_CONTRACT / LOGICAL_COLLECTION_ONLY / NOT_DESKTOP_WORKSPACE_UI / NOT_FRONTEND_TABS  
Unavailable reason: desktop workspace UI and tabs UI unavailable by contract  
Limitations: logical collections only; no frontend group or tabs UI

### P2.3.9 — DONE
Capsule name: Floating Window Restore / Resume Contract  
Evidence: `FloatingWindowRestoreContract`, `build_floating_window_restore_contract()`  
Tests: `test_p2_3_9_*`  
Truth label: FLOATING_WINDOW_RESTORE_CONTRACT / STATE_RECONSTRUCTION_CONTRACT_ONLY / NOT_PERSISTENCE / NOT_MEMORY_WRITE  
Unavailable reason: storage/persistence/memory/trace unavailable by contract  
Limitations: read-model reconstruction only; no local/browser storage, memory write, trace write, or route execution

### P2.3.10 — DONE
Capsule name: Workspace Focus/Stack Projection Result  
Evidence: `WorkspaceFocusStackProjectionResult`, `P23BWorkspaceWindowSemanticsResult`  
Tests: `test_p2_3_10_*`, result serialization tests  
Truth label: WORKSPACE_FOCUS_STACK_PROJECTION_RESULT / READ_MODEL_RESULT_ONLY / NOT_FRONTEND_STATE_STORE / NOT_PRODUCT_BEHAVIOR  
Unavailable reason: frontend/product behavior unavailable by contract  
Limitations: bundles P2.3-B semantics over P2.3-A projection seed only; does not start P2.3-C/P2.10/P2.13

## 9. Floating Window Focus Intent Contract Proof

Focus intent carries `focus_id`, `window_id`, P2.3-A `workspace_state_id`,
closed-world focus source/reason, active-window candidate, previous active window,
availability, reason, truth label, and non-goals. All focus runtime fields remain
false: browser focus, frontend activation, focus manager runtime, runtime
mutation, memory write, and trace write.

## 10. Floating Window Stack / Layer Order Contract Proof

Stack order carries ordered P2.3-A window IDs, active window, role map, layer
order hint, z-order hint text, ordering reason, truth label, and non-goals. It
creates no z-index runtime, layout engine, CSS, runtime mutation, memory write,
or trace write.

## 11. Floating Window Group / Collection Contract Proof

Window group carries closed-world group kind, group scope, P2.3-A window IDs,
primary window, canonical surface scope, group reason, availability, truth label,
and non-goals. It creates no desktop workspace UI, frontend group UI, tabs UI,
runtime mutation, memory write, or trace write.

## 12. Floating Window Restore / Resume Contract Proof

Restore carries closed-world restore source/mode, restored P2.3-A window IDs,
restored active window, restored group IDs, availability, resume reason, truth
label, and non-goals. It uses no local storage, browser storage, memory write,
trace write, runtime mutation, or route execution.

## 13. Workspace Focus/Stack Projection Result Proof

The projection bundles focus, stack, group, restore, and side-effect proof over
the P2.3-A projection seed. It sets `section_id=P2.3`,
`created_for_pack=P2.3-B`, `next_pack=P2.3-C`, and keeps frontend state store,
product behavior, P2.3-C start, P2.10 start, and P2.13 start false.

## 14. No Focus Manager / Z-Index Runtime / Layout Engine Proof

Tests assert focus intent is not focus manager/browser focus, stack order is not
z-index runtime, and layer order hint is not layout engine.

## 15. No Persistence / Storage / Memory / Trace Proof

Tests assert restore/resume uses no local storage, browser storage, memory write,
trace write, runtime mutation, or route execution.

## 16. No Frontend / Browser / Tauri / Product Behavior Proof

`P23BSideEffectProof` keeps frontend UI, browser app, Tauri app, desktop app,
frontend activation, keyboard shortcut, command palette, route runtime, API
server, event bus, and product behavior fields false.

## 17. Truth Label / DEV_FIXTURE Boundary Proof

Truth labels identify contract/read-model status only. `DEV_FIXTURE` appears only
as a projection truth boundary vocabulary value and does not claim LIVE,
TRACE_VERIFIED, release scope, or operator-testable product behavior.

## 18. Surface Taxonomy Drift Status

**SURFACE_TAXONOMY_DRIFT:** YES — inherited legacy Forum/Archivium/A-Hub/S-Hub/L-Hub/Workspace references remain drift/future/historical references only. P2.3-B does not activate them as canonical P2 surfaces.

## 19. Side-Effect / No-Authority Proof

`build_p2_3_b_side_effect_proof()` returns all false for frontend UI,
browser/Tauri/desktop app, browser focus, frontend activation, focus manager,
draggable/resizable windows, window manager, z-index runtime, layout engine, CSS,
frontend group/tabs/desktop workspace UI, keyboard shortcuts, command palette,
route runtime, route execution, API server, HTTP routes, event bus, runtime event
emission, local/browser storage, memory/trace writes, runtime mutation,
permission enforcement, Custos integration, source of truth, LIVE,
TRACE_VERIFIED, RELEASE_SCOPE, P2.3-C, P2.10, and P2.13.

## 20. Files Created / Modified

Created:
- `src/agentic_runtime/aurel_shell/workspace_window_semantics.py`
- `tests/aurel_shell/test_shell_workspace_window_semantics.py`
- `agent/reports/P2_3_B_WORKSPACE_WINDOW_SEMANTICS.md`

Modified:
- `agent/ACTIVE_TASK.md`
- `agent/ARCHITECTURE.md`
- `agent/DECISIONS.md`
- `agent/REPORTS.md`
- `agent/ROADMAP.md`
- `agent/STATE.md`
- `agent/TESTS.md`

## 21. Tests Added / Updated

15 focused tests in `tests/aurel_shell/test_shell_workspace_window_semantics.py`.

## 22. Validation Run

```text
.venv/bin/python -m compileall src tests — PASS
.venv/bin/python -m pytest tests/aurel_shell/test_shell_workspace_window_semantics.py -q — 15 passed
.venv/bin/python -m pytest tests/aurel_shell -q — 524 passed
.venv/bin/python -m ruff check src tests — PASS
.venv/bin/python -m mypy src/agentic_runtime — PASS (301 files)
```

## 23. What Was Deliberately Not Implemented

Product UI, browser UI, Tauri desktop app, frontend components, browser focus,
frontend component activation, focus manager runtime, z-index runtime,
CSS/frontend layout, layout engine, draggable windows, resizable windows, window
manager runtime, keyboard shortcuts, command palette, route runtime, route
execution, API server, HTTP routes, event bus, runtime event emission, local or
browser storage, memory writes, trace writes, runtime mutation, permission
enforcement, Custos integration, desktop workspace UI, frontend group UI, tabs
UI, source-of-truth store, P2.3-C, P2.10, or P2.13.

## 24. Limitations

Contract/read-model pack only. Focus is intent, not focus runtime. Stack/layer
order is metadata, not z-index/CSS/layout. Groups are logical collections, not UI.
Restore/resume is reconstruction metadata, not persistence.

## 25. Next Recommended Step

P2.3-C — likely P2.3.11–P2.3.15 Cross-Surface Window Handoff / Conflict /
Docking Semantics.

## 26. Commit Hash

Pending initial commit.

## 27. Final Git Status

Pending initial commit.

