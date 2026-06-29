# P2.2-A — Per-Surface Local Navigation Foundation

**Pack ID:** P2.2-A  
**Section:** P2.2 — Per-Surface Local Navigation  
**Domain:** P2 — AurelShell Seven-Surface Cognitive OS Foundation  
**Covered checkpoints:** P2.2.0–P2.2.5  
**Status:** DONE  
**Date:** 2026-06-29  
**Next pack:** P2.2-B — likely P2.2.6–P2.2.10 Local Navigation Hierarchy / Interaction Constraints

---

## 1. Result Header

P2.2-A opens P2.2 by creating deterministic per-surface local navigation contract
and read-model foundation over the sealed P2.1 topbar/surface registry stack. It adds
P2.2 section intake / P2.1 handoff gate, local navigation ownership contracts,
per-surface nav registries, nav group contracts, nav item contracts,
visibility/availability states, local nav projection seed, pack result, and
side-effect/no-authority proof. No product UI, frontend sidebar, global left nav,
frontend routes, clients, route runtime, click handlers, keyboard shortcuts,
command palette, floating windows, API server, event bus, permission enforcement,
Custos integration, memory writes, trace writes, P2.2-B, or P2.3 work was
implemented.

## 2. Dispatch Gate Evidence

| Gate | Evidence |
|------|----------|
| P1.9.30-SEAL-CRITERIA-REPAIR accepted | yes — `SEALED_FOR_P1_CONTRACT_SCOPE` |
| Pre-P2 audit rerun | `READY_FOR_P2_REVIEW` |
| P2.0-F report / OMNI / seal | present; OMNI accepted; `SEALED_FOR_P2_CONTRACT_SCOPE`; commit `20c2ac9` |
| P2.1-A report / OMNI / git | present; OMNI accepted; commit `29d1e7d` |
| P2.1-B report / OMNI / git | present; OMNI accepted; commit `975f904` |
| P2.1-C report / OMNI / git | present; OMNI accepted; commit `75f6550` |
| P2.1-D report / OMNI / git | present; OMNI accepted; commit `d609434` |
| P2.1-D seal | `SEALED_FOR_P2_1_CONTRACT_SCOPE` |
| P2.1-D readiness | `READY_FOR_P2_2_PLAN` |
| P2.1-D P2.2 implementation check | no P2.2 code in P2.1-D |
| Working tree clean at dispatch | yes |
| Premature P2.2-A files | none |

**Gate result:** PASS

## 3. Roadmap Authority Chain

1. Aurel Roadmap v5.5 = canonical roadmap truth  
2. P1 seal / pre-P2 audit = permission gate  
3. P2.0-A–F = sealed contract-scope shell dependencies  
4. P2.1-A–D = topbar/surface registry section seal + P2.2 plan readiness  
5. P2.2-A starts P2.2 contract work only  
6. local `agent/ROADMAP.md` = progress mirror only  

## 4. Execution Shape Used

Selected: P2.2 Section Intake + Local Navigation Foundation Contract Pack /
Orchestrated Single Executor. Single vertical slice: contract module, focused
tests, report/docs sync, validation. No UI/product, route runtime, or P2.2-B shape.

## 5. Dependency on P2.1-D

- Reuses `P21TopbarSealDecision.SEALED_FOR_P2_1_CONTRACT_SCOPE`  
- Reuses `P21P22ReadinessDecision.READY_FOR_P2_2_PLAN`  
- Reuses `build_p2_1_topbar_exit_seal()` and `build_p2_2_readiness_result()` for handoff evidence  
- Reuses `P2_1_D_REPORT_FILENAME` as previous section report ref  
- Reuses `CANONICAL_SURFACE_ORDER` and `SURFACE_KIND_DISPLAY_NAMES` from P2.1-A/P2.0-A  
- Does not duplicate surface enum or canonical registry  

## 6. Roadmap Coverage Matrix P2.2.0–P2.2.5

### P2.2.0 — DONE
Capsule name: P2.2 Section Intake + P2.1 Handoff Gate  
Evidence: `P22SectionIntake`, `P22P21HandoffGate`, `build_p2_2_section_intake()`, `build_p2_1_handoff_gate()`  
Tests: `test_p2_2_0_*`, `test_p2_1_d_seal_and_readiness_dependencies`  
Truth label: SECTION_INTAKE / HANDOFF_GATE / CONTRACT_SCOPE / NOT_UI / NOT_P2_3  
Unavailable reason: n/a  
Limitations: handoff evidence derived from P2.1-D contract builders, not runtime inspection  

### P2.2.1 — DONE
Capsule name: Local Navigation Ownership Contract  
Evidence: `LocalNavigationOwnershipContract`, `build_local_navigation_ownership_contracts()`  
Tests: `test_p2_2_1_*`  
Truth label: SURFACE_OWNED_LOCAL_NAV / NOT_GLOBAL_TOPBAR / NOT_ROUTE_RUNTIME  
Unavailable reason: n/a  
Limitations: ownership is contract declaration only  

### P2.2.2 — DONE
Capsule name: Per-Surface Nav Registry Contract  
Evidence: `PerSurfaceLocalNavRegistry`, `LocalNavGroupContract`, builders for all official surfaces  
Tests: `test_p2_2_2_*`  
Truth label: LOCAL_NAV_REGISTRY_CONTRACT / READ_MODEL_ONLY / NOT_SOURCE_OF_TRUTH / NOT_UI  
Unavailable reason: n/a  
Limitations: seed groups/items are contract placeholders, not product nav trees  

### P2.2.3 — DONE
Capsule name: Surface-Specific Nav Item Contract  
Evidence: `LocalNavItemContract`, `LocalNavItemKind`, closed-world validation  
Tests: `test_p2_2_3_*`  
Truth label: NAV_ITEM_CONTRACT / NOT_ACTION_EXECUTION / NOT_ROUTE_EXECUTION / NOT_CLICK_HANDLER  
Unavailable reason: n/a  
Limitations: route_hint is contract hint only  

### P2.2.4 — DONE
Capsule name: Local Nav Visibility / Availability Contract  
Evidence: `LocalNavVisibilityAvailabilityState`, builders from nav items  
Tests: `test_p2_2_4_*`  
Truth label: VISIBILITY_CONTRACT / AVAILABILITY_CONTRACT / NOT_PERMISSION / NOT_LIVE  
Unavailable reason: n/a  
Limitations: no runtime health or auth evaluation  

### P2.2.5 — DONE
Capsule name: Local Nav Projection Seed  
Evidence: `LocalNavProjectionSeed`, `P22ALocalNavigationFoundationResult`, `serialize_p2_2_a_result()`  
Tests: `test_p2_2_5_*`  
Truth label: PROJECTION_SEED / READ_MODEL_ONLY / NOT_UI / NOT_P2_2_B / NOT_P2_3  
Unavailable reason: n/a  
Limitations: projection seed is inspectable read model, not rendered nav  

## 7–12. Contract Proofs

All six checkpoint objects build, serialize, and enforce boundary invariants via
assert helpers. Official seven surfaces preserved via `CANONICAL_SURFACE_ORDER`.
SYSTEM protected and Settings non-root represented in seed nav items/groups.

## 13. Truth Label / Local Nav Boundary Proof

Section intake, ownership, registry, nav item, visibility/availability, and
projection seed all declare contract-scope truth labels. No LIVE, TRACE_VERIFIED,
or release scope claims.

## 14. No UI / Global Left Nav / Route Runtime Proof

All 38 P2.2-A side-effect booleans in `P22ASideEffectProof` remain false.

## 15. Side-Effect / No-Authority Proof

`build_p2_2_a_side_effect_proof()` returns all-false dataclass; tests assert
critical fields.

## 16. Surface Taxonomy Drift Status

**SURFACE_TAXONOMY_DRIFT:** YES — legacy Forum/Archivium/A-Hub terms remain in
repo docs/code per existing drift signal; not activated as P2.2-A registry surfaces.

## 17. Files Created / Modified

Created:
- `src/agentic_runtime/aurel_shell/local_navigation.py`
- `tests/aurel_shell/test_shell_local_navigation_foundation.py`
- `agent/reports/P2_2_A_LOCAL_NAVIGATION_FOUNDATION.md`

Modified:
- `src/agentic_runtime/aurel_shell/__init__.py`
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/STATE.md`
- `agent/ROADMAP.md`
- `agent/TESTS.md`

## 18. Tests Added / Updated

24 focused tests in `tests/aurel_shell/test_shell_local_navigation_foundation.py`.

## 19. Validation Run

```text
.venv/bin/python -m compileall src tests — PASS
.venv/bin/python -m pytest tests/aurel_shell/test_shell_local_navigation_foundation.py -q — 24 passed
.venv/bin/python -m pytest tests/aurel_shell -q — 440 passed
.venv/bin/python -m ruff check src tests — PASS
.venv/bin/python -m mypy src/agentic_runtime — PASS (296 files)
```

## 20. What Was Deliberately Not Implemented

UI, frontend sidebar, global left nav, frontend routes, web/desktop/mobile clients,
live CLI/TUI, route runtime, click handlers, keyboard shortcuts, command palette,
floating windows, API server, event bus, permission enforcement, Custos, memory/trace
writes, P2.2-B, P2.2.6+, P2.3+.

## 21. Limitations

Contract/read-model seed only. Nav items use route hints, not executable routes.
P2.2 readiness from P2.1-D was plan-only permission; P2.2-A creates contract
foundation, not product local navigation.

## 22. Next Pack

P2.2-B — likely P2.2.6–P2.2.10 Local Navigation Hierarchy / Interaction Constraints

## 23. Commit Hash

`de1932a6f6b06195966b89367be11834de38f453`

## 24. Final Git Status

Clean — `git status --short` empty after commit on `master`.
