# P2.3-A — Floating Windows / Workspace State Foundation

**Pack ID:** P2.3-A  
**Section:** P2.3 — Floating Windows / Workspace State  
**Domain:** P2 — AurelShell Seven-Surface Cognitive OS Foundation  
**Covered checkpoints:** P2.3.0–P2.3.5  
**Status:** DONE  
**Date:** 2026-06-29  
**Next pack:** P2.3-B — likely floating window interaction / workspace projection continuation

---

## 1. Result Header

P2.3-A adds contract-only workspace/window state foundation objects under
`src/agentic_runtime/aurel_shell/workspace_state.py`: section intake gate,
floating window identity/ownership contracts, shell workspace read-model state,
lifecycle/availability contracts, placement/layering intent contracts, workspace
state projection seed, all-false side-effect proof, and pack result envelope.

No product UI, browser/Tauri app, draggable windows, storage, route runtime,
API server, HTTP route, event bus, runtime event emission, memory/trace writes,
P2.3-B, P2.10, or P2.13 implementation.

## 2. Dispatch Gate Evidence

| Gate | Evidence |
|------|----------|
| AUDIT-REPAIR-001 report | present: `agent/reports/AUDIT_REPAIR_001_TEST_PORTABILITY_P2_2_B_CANON_SYNC.md` |
| AUDIT-REPAIR-001 commit | `5d133e0` / docs `70f82b2` |
| AUDIT-REPAIR-001 final state | full suite green; F-001 fixed; F-002 confirmed |
| P2.2-D report | present: `agent/reports/P2_2_D_LOCAL_NAVIGATION_INTEGRATION_TAIL.md` |
| P2.2-D implementation commit | `d5ba094275131d4622339aa7e7c6db14285be34d` |
| Required previous seal | `SEALED_FOR_P2_2_CONTRACT_SCOPE` |
| Required previous readiness | `READY_FOR_P2_3_PLAN` |
| Working tree at dispatch | clean |

**Gate result:** PASS

## 3. Roadmap Authority Chain

1. Aurel Roadmap v5.5 = canonical roadmap truth
2. CodeOps = validation/report/git discipline
3. AUDIT-REPAIR-001 = repair gate
4. P2.2-D = sealed local navigation predecessor and P2.3 plan-readiness
5. P2.3-A = contract/read-model workspace state foundation only
6. local `agent/ROADMAP.md` = progress mirror only

## 4. Roadmap Coverage Matrix P2.3.0–P2.3.5

### P2.3.0 — DONE
Capsule name: P2.3 Section Intake Gate  
Evidence: `P23SectionIntakeGate`, `build_p2_3_section_intake_gate()`  
Tests: `test_p2_3_0_*`, dependency constants tests  
Truth label: CONTRACT_ONLY / P2_2_DEPENDENCY_SEALED / NOT_RUNTIME  
Unavailable reason: n/a — dependency gate only  
Limitations: verifies prior seal/readiness; does not start runtime implementation

### P2.3.1 — DONE
Capsule name: Floating Window Identity / Ownership  
Evidence: `FloatingWindowIdentityContract`, `build_floating_window_identity_contracts()`  
Tests: `test_p2_3_1_*`  
Truth label: READ_MODEL_ONLY / NOT_SOURCE_OF_TRUTH / NOT_AUTHORITY  
Unavailable reason: n/a — identity contract only  
Limitations: no runtime window instances, authority grant, source-of-truth ownership, or UI

### P2.3.2 — DONE
Capsule name: Shell Workspace Read-Model State  
Evidence: `ShellWorkspaceStateContract`, `build_shell_workspace_state_contract()`  
Tests: `test_p2_3_2_*`  
Truth label: READ_MODEL_ONLY / NOT_STORAGE / NOT_RUNTIME  
Unavailable reason: old Workspace surface remains inactive  
Limitations: workspace is a shell coordinate frame, not a top-level surface or storage runtime

### P2.3.3 — DONE
Capsule name: Lifecycle / Availability Representation  
Evidence: `FloatingWindowLifecycleContract`, `build_floating_window_lifecycle_contract()`  
Tests: `test_p2_3_3_*`  
Truth label: CONTRACT_ONLY / READ_MODEL_ONLY / NOT_RUNTIME  
Unavailable reason: runtime lifecycle unavailable by contract  
Limitations: unavailable/deferred/error states require reasons; no event runtime or lifecycle engine

### P2.3.4 — DONE
Capsule name: Placement / Layering Intent  
Evidence: `FloatingWindowPlacementIntentContract`, `build_floating_window_placement_intent_contract()`  
Tests: `test_p2_3_4_*`  
Truth label: PROJECTION_SEED_ONLY / NOT_UI  
Unavailable reason: layout runtime unavailable by contract  
Limitations: semantic placement hints only; no CSS, z-index runtime, drag/drop, or UI

### P2.3.5 — DONE
Capsule name: Workspace State Projection Seed  
Evidence: `WorkspaceStateProjectionSeed`, `P23AWorkspaceStateFoundationResult`  
Tests: `test_p2_3_5_*`, result serialization tests  
Truth label: PROJECTION_SEED_ONLY / NOT_RUNTIME  
Unavailable reason: API/event/storage runtime unavailable by contract  
Limitations: bundles P2.3-A contracts and hands off to P2.3-B only

## 5. Contract Boundary Proof

P2.3-A reuses `CANONICAL_SURFACE_ORDER` and P2.2-D seal/readiness builders.
It does not duplicate the surface registry or create a new surface taxonomy.
`Workspace` remains a legacy/future taxonomy reference only and is not activated
as a top-level P2 surface.

P2.3 floating window vocabulary is prompt-scoped and closed-world in
`workspace_state.py`. Existing P2.0-C `FloatingWindowKind` and
`FloatingWindowAvailability` remain untouched.

## 6. Side-Effect / No-Authority Proof

`build_p2_3_a_side_effect_proof()` returns an all-false `P23ASideEffectProof`.
Tests assert every field remains false, including UI, browser/Tauri app,
draggable window, window manager, route runtime, API server, event bus, storage,
permission enforcement, memory write, trace write, runtime mutation, LIVE,
TRACE_VERIFIED, release scope, P2.3-B, P2.10, and P2.13 fields.

## 7. Surface Taxonomy Drift Status

**SURFACE_TAXONOMY_DRIFT:** YES — inherited legacy Forum/Archivium/A-Hub/S-Hub/L-Hub/Workspace references remain drift/future/historical references only. P2.3-A does not activate them as canonical P2 surfaces.

## 8. Files Created / Modified

Created:
- `src/agentic_runtime/aurel_shell/workspace_state.py`
- `tests/aurel_shell/test_shell_workspace_state_foundation.py`
- `agent/reports/P2_3_A_WORKSPACE_STATE_FOUNDATION.md`

Modified:
- `agent/ACTIVE_TASK.md`
- `agent/ARCHITECTURE.md`
- `agent/REPORTS.md`
- `agent/ROADMAP.md`
- `agent/STATE.md`
- `agent/TESTS.md`

## 9. Tests Added / Updated

12 focused tests in `tests/aurel_shell/test_shell_workspace_state_foundation.py`.

## 10. Validation Run

```text
.venv/bin/python -m compileall src tests — PASS
.venv/bin/python -m pytest tests/aurel_shell/test_shell_workspace_state_foundation.py -q — 12 passed
.venv/bin/python -m pytest tests/aurel_shell -q — 509 passed
.venv/bin/python -m ruff check src tests — PASS
.venv/bin/python -m mypy src/agentic_runtime — PASS (300 files)
```

## 11. What Was Deliberately Not Implemented

Product UI, browser app, Tauri app, draggable windows, window manager, CSS layout,
z-index runtime, frontend routes, live CLI/TUI product, route runtime, route
handler, API server, HTTP routes, event bus, runtime event emission, permission
enforcement, Custos integration, memory writes, trace writes, local/browser
storage, old `Workspace` activation, production LIVE, TRACE_VERIFIED, release
scope, P2.3-B, P2.10, or P2.13 work.

## 12. Limitations

Contract/read-model pack only. Placement is semantic intent, not layout. Lifecycle
is representation, not runtime lifecycle. Workspace state is projection seed and
coordinate frame, not persisted state or source of truth.

## 13. Next Pack

P2.3-B — likely floating window interaction / workspace projection continuation.

## 14. Commit Hash

Pending implementation commit.

## 15. Final Git Status

Pending final clean status after commit.
