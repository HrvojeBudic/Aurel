# P2.1-A — Global Topbar / Surface Registry Foundation

**Pack ID:** P2.1-A  
**Section:** P2.1 — Global Topbar / Surface Registry  
**Domain:** P2 — AurelShell Seven-Surface Cognitive OS Foundation  
**Covered checkpoints:** P2.1.0–P2.1.5  
**Status:** DONE  
**Date:** 2026-06-29  
**Next pack:** P2.1-B — likely P2.1.6–P2.1.10 Topbar Status Slots / Availability / Operator Context

---

## 1. Result Header

P2.1-A opens P2.1 by creating a deterministic Global Topbar / Surface Registry
contract and read-model foundation over the sealed P2.0 AurelShell stack. It adds
section intake / P2.0 handoff gate, topbar-oriented surface registry entries,
canonical topbar registry builder, active surface state, proposal-only switch
intents, and a global topbar projection seed. No product UI, frontend topbar,
clients, CLI/TUI live binding, route runtime, local navigation, permission
enforcement, Custos integration, memory writes, trace writes, or P2.1-B+ work was
implemented.

## 2. Dispatch Gate Evidence

| Gate | Evidence |
|------|----------|
| P1.9.30-SEAL-CRITERIA-REPAIR accepted | yes — `SEALED_FOR_P1_CONTRACT_SCOPE` (`agent/reports/P1_9_30_SEAL_CRITERIA_REPAIR.md`) |
| Pre-P2 audit rerun decision | `READY_FOR_P2_REVIEW` (`agent/reports/P1_PRE_P2_FULL_AUDIT_AND_SEAL_RERUN.md`) |
| P2.0-A report / OMNI / git | present; OMNI accepted; `ca08c91` |
| P2.0-B report / OMNI / git | present; OMNI accepted; `8fe4a59` |
| P2.0-C report / OMNI / git | present; waiver pattern; `3e22b04` |
| P2.0-D report / OMNI / git | present; DEC-P20E-01 waiver; `f897746` |
| P2.0-E report / OMNI / git | present; DEC-P20F-01 waiver; `1f0f6a9` |
| P2.0-F report / OMNI / git | present; OMNI accepted per P2.0-F dispatch; `20c2ac9` |
| P2.0-F seal | `SEALED_FOR_P2_CONTRACT_SCOPE` |
| Working tree clean at dispatch | yes |
| Premature P2.1-A files | none |

**Gate result:** PASS

## 3. Roadmap Authority Chain

Aurel Roadmap v5.5 = canonical truth; P1 seal / pre-P2 audit = P2 permission gate;
P2.0-A–F reports + seals = dependency gates; Implementation Pack Doctrine =
grouping; CodeOps = validation/report/git; local `agent/ROADMAP.md` = progress
mirror only.

## 4. Execution Shape Used

Global Topbar / Surface Registry Foundation Contract Pack / Orchestrated Single
Executor. Shape obeyed. No split. No scope expansion into UI, route runtime,
local nav, or P2.1-B+.

## 5. Dependency on P2.0-A/B/C/D/E/F

- **P2.0-A registry reused:** `build_default_surface_registry`, `CANONICAL_SURFACE_ORDER`, `AurelSurfaceKind`, `SURFACE_KIND_IDS` — no duplicate surface enum or second canonical list.
- **P2.0-B boundaries reused:** `build_aurel_logo_route_binding`, `build_no_universal_left_nav_contract` — logo→CRO, no universal left nav.
- **P2.0-C/D/E/F:** respected via read-only derivation; no bypass of continuity, truth/permission, snapshot, or projection boundaries.

## 6. Roadmap Coverage Matrix P2.1.0–P2.1.5

### P2.1.0 — DONE
Capsule name: P2.1 Section Intake + P2.0 Handoff Gate  
Evidence: `P21SectionIntake`, `P21AHandoffGate`, `build_p2_1_section_intake()`, `build_p2_1_a_handoff_gate()`  
Tests: `test_p2_1_a_section_intake_builds`, `test_p2_0_f_report_dependency_represented`, `test_p2_0_contract_scope_seal_dependency_represented`, `test_p2_1_a_does_not_require_*`, `test_p2_1_a_does_not_start_p2_2`  
Truth label: CONTRACT_SCOPE / REPORT_EVIDENCE / NOT_LIVE / NOT_TRACE_VERIFIED  
Unavailable reason: n/a — contract foundation only  
Limitations: No UI, route runtime, or P2.2

### P2.1.1 — DONE
Capsule name: Surface Registry Entry Model  
Evidence: `SurfaceRegistryEntry`, `SurfaceRegistryTruthBoundary`, `SurfaceRegistryAvailabilityState`, `build_surface_registry_entry()`  
Tests: `test_surface_registry_entry_builds`, `test_invalid_surface_id_rejected`, `test_system_protected_operator_only`, `test_settings_non_root`, `test_entry_does_not_*`  
Truth label: CONTRACT_ONLY / READ_MODEL_ONLY / NOT_AUTHORITY / NOT_EXECUTION  
Unavailable reason: n/a — entry model only  
Limitations: No permission enforcement, route execution, or UI mount

### P2.1.2 — DONE
Capsule name: Canonical Surface Registry Builder  
Evidence: `SurfaceRegistry`, `SurfaceRegistryResult`, `SurfaceTaxonomyDriftSignal`, `build_default_topbar_surface_registry()`  
Tests: `test_default_topbar_surface_registry_builds`, `test_official_p2_0_surface_ids_preserved`, `test_logo_route_target_aurel_cro`, `test_forum_archivium_future_refs_not_active`, `test_taxonomy_drift_signal_produced`  
Truth label: CONTRACT_SCOPE / REGISTRY_ONLY / READ_MODEL_ONLY / FUTURE_REF_UNAVAILABLE  
Unavailable reason: legacy taxonomy as future refs only  
Limitations: No second canonical surface list; Forum/Archivium not active surfaces

### P2.1.3 — DONE
Capsule name: Active Surface State Contract  
Evidence: `ActiveSurfaceState`, `ActiveSurfaceActivationSource`, `ActiveSurfaceTruthBoundary`, `build_active_surface_state()`  
Tests: `test_active_surface_state_builds`, `test_default_active_surface_deterministic`, `test_invalid_active_surface_blocked`, `test_system_active_state_protected`, `test_active_state_does_not_*`  
Truth label: SHELL_STATE_ONLY / READ_MODEL_ONLY / NOT_SOURCE_OF_TRUTH  
Unavailable reason: n/a — shell state contract only  
Limitations: No persistent store or route runtime

### P2.1.4 — DONE
Capsule name: Topbar Surface Switch Intent Contract  
Evidence: `TopbarSurfaceSwitchIntent`, `TopbarSurfaceSwitchDisposition`, `TopbarSwitchTruthBoundary`, `propose_topbar_surface_switch()`  
Tests: `test_topbar_switch_intent_builds`, `test_normal_switch_intent_is_proposal_only`, `test_unknown_target_blocked`, `test_agent_to_system_blocked`, `test_operator_to_system_protected_not_executed`, `test_intent_does_not_*`  
Truth label: PROPOSAL_ONLY / NOT_PERMISSION / NOT_EXECUTION / NOT_PROOF  
Unavailable reason: n/a — intent contract only  
Limitations: No navigation engine or permission engine

### P2.1.5 — DONE
Capsule name: Global Topbar Read Model / Projection Seed  
Evidence: `TopbarReadModel`, `TopbarVisibleSurfaceEntry`, `TopbarProtectedSurfaceEntry`, `TopbarGlobalNavigationPolicy`, `TopbarUnavailableBinding`, `build_global_topbar_read_model()`  
Tests: `test_topbar_read_model_builds`, `test_visible_surfaces_match_registry`, `test_logo_route_aurel_cro`, `test_no_universal_left_nav`, `test_local_nav_deferred_to_p2_2`, `test_ui_unavailable_reason_present`, `test_read_model_is_not_live_ui`  
Truth label: PROJECTION_ONLY / READ_MODEL_ONLY / NOT_LIVE_UI  
Unavailable reason: UI/CLI/TUI live bindings UNAVAILABLE with explicit reasons  
Limitations: No actual UI component, command palette, or floating window state

## 7. P2.1 Section Intake / P2.0 Handoff Gate Proof

`build_p2_1_section_intake()` records section `P2.1`, pack `P2.1-A`, checkpoints
P2.1.0–P2.1.5, dependency on P2.0-F, seal requirement
`SEALED_FOR_P2_CONTRACT_SCOPE`, and explicit false flags for production-live,
trace-verified, and release scope requirements. `build_p2_1_a_handoff_gate()`
references `P2_0_F_PROJECTION_CLI_EXIT_SEAL.md` and asserts the contract-scope
seal dependency.

## 8. Surface Registry Entry Model Proof

Each `SurfaceRegistryEntry` derives from the P2.0 `AurelSurfaceContract` for the
same surface id. Invalid ids are rejected. SYSTEM is operator-only/root-protected
with agent access blocked. Settings is non-root configuration scope. All no-authority
flags remain false.

## 9. Canonical Surface Registry Builder Proof

`build_default_topbar_surface_registry()` preserves all seven official P2.0 surface
ids in canonical order, sets logo route to `aurel_cro`, lists SYSTEM as protected,
and records legacy taxonomy terms as `future_surface_refs` with drift signals —
not as active registry entries.

## 10. Active Surface State Contract Proof

Default active surface is deterministically `aurel_cro`. Unknown surfaces are
rejected. SYSTEM active state is operator-aware; agent activation to SYSTEM sets
`can_switch=False`. State is shell/read-model only with all mutation/authority
flags false.

## 11. Topbar Surface Switch Intent Proof

`propose_topbar_surface_switch()` always returns `is_proposal=True`. Unknown
targets are blocked. Agent→SYSTEM is blocked. Operator→SYSTEM is
`PROTECTED_PROPOSAL` only — not executed. No authority, permission, route
execution, runtime mutation, proof creation, memory, or trace writes.

## 12. Global Topbar Read Model / Projection Seed Proof

Read model derives visible/protected surfaces from the topbar registry, includes
active surface state, Settings non-root entry, logo route to Aurel CRO via P2.0-B
binding, forbids universal left nav, defers local navigation to P2.2, and lists
UI/CLI/TUI unavailable bindings with reasons. `is_live_ui=False`, `creates_ui=False`.

## 13. Surface Taxonomy Drift Status

**SURFACE_TAXONOMY_DRIFT: YES**

Legacy terms Forum, Archivium, A-Hub, S-Hub, L-Hub, Workspace, Strategy, Society
Hub are recorded as `future_surface_refs` and `SurfaceTaxonomyDriftSignal` metadata.
`activated_as_registry_truth=False`. Official P2.0 seven-surface lock remains the
only active registry truth.

## 14. Truth Label / Fixture Boundary Proof

All objects carry CONTRACT_SCOPE / READ_MODEL_ONLY / PROJECTION_ONLY / NOT_LIVE_UI
labels as appropriate. No LIVE, TRACE_VERIFIED, or release scope claims. DEV_FIXTURE
not used in this pack.

## 15. No UI / Client / Runtime / Route / Authority Proof

All 26 `P21ASideEffectProof` fields are false. No product UI, clients, route
runtime, permission enforcement, Custos, memory writes, trace writes, P2.1-B, or
P2.2 work was created.

## 16. Side-Effect / No-Authority Proof

`build_p2_1_a_side_effect_proof()` returns all-false proof. Pack result embeds the
same proof. Tests assert critical forbidden fields.

## 17. Files Created / Modified

Created:
- `src/agentic_runtime/aurel_shell/topbar.py`
- `tests/aurel_shell/test_shell_topbar_surface_registry.py`
- `agent/reports/P2_1_A_GLOBAL_TOPBAR_SURFACE_REGISTRY.md`

Modified:
- `src/agentic_runtime/aurel_shell/__init__.py`
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/STATE.md`
- `agent/ROADMAP.md`
- `agent/TESTS.md`

## 18. Tests Added / Updated

75 focused tests in `tests/aurel_shell/test_shell_topbar_surface_registry.py`.
Full AurelShell suite: 306 passed.

## 19. Validation Run

```bash
.venv/bin/python -m compileall src tests          # PASS
.venv/bin/python -m pytest tests/aurel_shell/test_shell_topbar_surface_registry.py -q  # 75 passed
.venv/bin/python -m pytest tests/aurel_shell -q   # 306 passed
.venv/bin/python -m ruff check src tests          # PASS
.venv/bin/python -m mypy src/agentic_runtime      # PASS (292 files)
```

## 20. What Was Deliberately Not Implemented

Product UI, frontend topbar, web/desktop/mobile clients, live CLI/TUI, route
runtime, browser tests, live shell, source-of-truth store, permission enforcement,
Custos integration, memory writes, trace writes, event bus, API server, command
palette, floating window state, per-surface local navigation (P2.2), P2.1-B, P2.1.6+.

## 21. Limitations

Topbar read model is projection-only. Switch intents are proposals only. Registry
is read-model over P2.0 — not source of truth. UI/CLI/TUI live bindings are
explicitly UNAVAILABLE. Taxonomy drift is reported but not remediated in docs.

## 22. Next Pack

P2.1-B — likely P2.1.6–P2.1.10 Topbar Status Slots / Availability / Operator Context

## 23. Commit Hash

_(recorded after commit)_

## 24. Final Git Status

_(recorded after commit)_
