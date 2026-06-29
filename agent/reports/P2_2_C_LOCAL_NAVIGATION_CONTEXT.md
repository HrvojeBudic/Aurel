# P2.2-C — Local Navigation Context / Surface-Specific Profiles

**Pack ID:** P2.2-C  
**Section:** P2.2 — Per-Surface Local Navigation  
**Domain:** P2 — AurelShell Seven-Surface Cognitive OS Foundation  
**Covered checkpoints:** P2.2.11–P2.2.15  
**Status:** DONE  
**Date:** 2026-06-29  
**Next pack:** P2.2-D — likely P2.2.16–P2.2.20 P2.2 Integration Tail / Projection / Binding / Docs / Section Seal

---

## 1. Result Header

P2.2-C extends P2.2-A/P2.2-B with deterministic local navigation context carryover,
surface-specific profiles, state restoration, degraded/unavailable profiles, and
context projection read models. No product UI, frontend sidebar, global left nav,
frontend routes, clients, route runtime, click handlers, keyboard shortcuts,
command palette, floating windows, API server, event bus, permission enforcement,
Custos integration, memory writes, trace writes, local/browser storage, P2.2-D,
or P2.3 work was implemented.

## 2. Dispatch Gate Evidence

| Gate | Evidence |
|------|----------|
| AUDIT-REPAIR-001 report | present; commit `5d133e0` / docs `70f82b2` |
| AUDIT-REPAIR-001 F-001 | FIXED — portable `tests/repo_root.py` |
| AUDIT-REPAIR-001 F-002 | CONFIRMED — P2.2-B canon synced |
| AUDIT-REPAIR-001 git clean | yes |
| AUDIT-REPAIR-001 P2.2-C/P2.3 check | did not start P2.2-C or P2.3 |
| P2.2-B report / git | present; commit `e9c25ad` |
| P2.2-B hierarchy projection | `LocalNavHierarchyProjectionResult` reused |
| P2.2-B P2.2-C/P2.3 check | P2.2-B did not implement P2.2-C or P2.3 |
| Operator dispatch | P2.2-C implementation plan accepted |
| Working tree clean at dispatch | yes |

**Gate result:** PASS

## 3. AUDIT-REPAIR-001 Gate Evidence

- Report: `agent/reports/AUDIT_REPAIR_001_TEST_PORTABILITY_P2_2_B_CANON_SYNC.md`
- F-001 fixed; full suite 6151 passed post-repair
- P2.2-C dependency recorded via `audit_repair_ref` in pack result

## 4. Roadmap Authority Chain

1. Aurel Roadmap v5.5 = canonical roadmap truth  
2. CodeOps = validation/report/git discipline  
3. AUDIT-REPAIR-001 = repair gate  
4. P2.2-A = local navigation foundation  
5. P2.2-B = hierarchy / interaction dependency  
6. P2.2-C extends P2.2 contract work only  
7. local `agent/ROADMAP.md` = progress mirror only  

## 5. Execution Shape Used

Selected: P2.2 Local Navigation Context + Surface Profile Contract Pack /
Orchestrated Single Executor. Single vertical slice: context module, focused
tests, report/docs sync, validation.

## 6. Dependency on P2.2-B

- Reuses `build_local_nav_hierarchy_projection_result()` as hierarchy ref  
- Reuses `build_local_nav_selection_states()` for carryover/restoration  
- Reuses P2.2-A registries and item contracts for surface profiles  
- Does not duplicate hierarchy/ordering/selection/interaction contracts  

## 7. Roadmap Coverage Matrix P2.2.11–P2.2.15

### P2.2.11 — DONE
Capsule name: Local Nav Context Carryover Contract  
Evidence: `LocalNavContextCarryoverContract`, `build_local_nav_context_carryover_contracts()`  
Tests: `test_p2_2_11_*`  
Truth label: CONTEXT_CARRYOVER_CONTRACT / READ_MODEL_CONTINUITY_ONLY / NOT_MEMORY_PERSISTENCE / NOT_ROUTE_EXECUTION  
Unavailable reason: n/a  
Limitations: carryover links projection refs only; no persistence  

### P2.2.12 — DONE
Capsule name: Surface-Specific Local Nav Profile Contract  
Evidence: `SurfaceLocalNavProfileContract`, `SurfaceLocalNavProfileKind`, `build_surface_local_nav_profile_contracts()`  
Tests: `test_p2_2_12_*`  
Truth label: SURFACE_LOCAL_NAV_PROFILE_CONTRACT / OFFICIAL_SURFACES_ONLY / NOT_SURFACE_TAXONOMY / NOT_UI  
Unavailable reason: n/a  
Limitations: profile shape derived from P2.2-A items; closed-world profile kinds  

### P2.2.13 — DONE
Capsule name: Local Nav State Restoration Contract  
Evidence: `LocalNavStateRestorationContract`, `LocalNavRestoreSource`, `build_local_nav_state_restoration_contracts()`  
Tests: `test_p2_2_13_*`  
Truth label: STATE_RESTORATION_CONTRACT / READ_MODEL_ONLY / NOT_ROUTE_EXECUTION / NOT_RUNTIME_MUTATION  
Unavailable reason: n/a  
Limitations: restoration describes read-model state only  

### P2.2.14 — DONE
Capsule name: Local Nav Unavailable / Degraded Profile Contract  
Evidence: `LocalNavDegradedProfileContract`, `build_local_nav_degraded_profile_contracts()`  
Tests: `test_p2_2_14_*`  
Truth label: DEGRADED_PROFILE_CONTRACT / UNAVAILABLE_PROFILE_CONTRACT / NOT_RUNTIME_FAILURE_CLAIM / NOT_REPAIR_AUTOMATION  
Unavailable reason: n/a  
Limitations: SYSTEM degraded (protected boundary); hub unavailable placeholder disclosure  

### P2.2.15 — DONE
Capsule name: Local Nav Context Projection Result  
Evidence: `LocalNavContextProjectionResult`, `P22CLocalNavigationContextResult`, `serialize_p2_2_c_result()`  
Tests: `test_p2_2_15_*`, `test_p2_2_c_*`  
Truth label: CONTEXT_PROJECTION / READ_MODEL_ONLY / NOT_UI / NOT_PERSISTENCE / NOT_P2_2_D / NOT_P2_3  
Unavailable reason: n/a  
Limitations: bundled projection is inspectable read model, not UI  

## 8–12. Contract Proofs

All five checkpoint object families build, serialize, and enforce boundary
invariants via assert helpers. Official seven surfaces preserved. P2.2-B hierarchy
projection referenced, not duplicated.

## 13. Truth Label / Context/Profile Boundary Proof

Context carryover, surface profiles, restoration, degraded profiles, and
projection all declare contract-scope truth labels. No LIVE, TRACE_VERIFIED, or
release scope claims.

## 14. No UI / Persistence / Route Runtime / New Surface Taxonomy Proof

All P2.2-C side-effect booleans in `P22CSideEffectProof` remain false including
local_storage_written, browser_storage_written, surface_taxonomy_created,
future_surface_activated, p2_2_d_started, p2_3_started.

## 15. Side-Effect / No-Authority Proof

`build_p2_2_c_side_effect_proof()` returns all-false dataclass; tests assert
critical fields.

## 16. Surface Taxonomy Drift Status

**SURFACE_TAXONOMY_DRIFT:** YES — legacy Forum/Archivium/A-Hub terms remain in
repo docs/code per existing drift signal; not activated as P2.2-C registry surfaces.

## 17. Files Created / Modified

Created:
- `src/agentic_runtime/aurel_shell/local_navigation_context.py`
- `tests/aurel_shell/test_shell_local_navigation_context.py`
- `agent/reports/P2_2_C_LOCAL_NAVIGATION_CONTEXT.md`

Modified:
- `src/agentic_runtime/aurel_shell/__init__.py`
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/STATE.md`
- `agent/ROADMAP.md`
- `agent/TESTS.md`

## 18. Tests Added / Updated

19 focused tests in `tests/aurel_shell/test_shell_local_navigation_context.py`.

## 19. Validation Run

```text
.venv/bin/python -m compileall src tests — PASS
.venv/bin/python -m pytest tests/aurel_shell/test_shell_local_navigation_context.py -q — 19 passed
.venv/bin/python -m pytest tests/aurel_shell -q — 479 passed
.venv/bin/python -m ruff check src tests — PASS
.venv/bin/python -m mypy src/agentic_runtime — PASS (298 files)
```

## 20. What Was Deliberately Not Implemented

UI, frontend sidebar, global left nav, frontend routes, web/desktop/mobile clients,
live CLI/TUI, route runtime, click handlers, keyboard shortcuts, command palette,
floating windows, API server, event bus, permission enforcement, Custos, memory/trace
writes, local/browser storage, P2.2-D, P2.2.16+, P2.3+.

## 21. Limitations

Contract/read-model context projection only. Degraded/unavailable profile examples
use honest contract disclosure for SYSTEM protected boundary and hub placeholder.
Context carryover uses P2.2-B selection state defaults.

## 22. Next Pack

P2.2-D — likely P2.2.16–P2.2.20 P2.2 Integration Tail / Projection / Binding / Docs / Section Seal

## 23. Commit Hash

`b33269202e267dcd6d101ade828c8ae3e35ac871`

## 24. Final Git Status

Clean — `git status --short` empty after commit on `master`; no push performed.
