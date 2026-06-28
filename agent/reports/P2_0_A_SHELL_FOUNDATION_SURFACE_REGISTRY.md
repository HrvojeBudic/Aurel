# P2.0-A — Shell Foundation + Surface Registry

_Date: 2026-06-28_

## 1. Result Header

**Pack ID:** P2.0-A
**Pack Name:** Shell Foundation + Surface Registry
**Status:** DONE
**Execution Shape Used:** Contract Foundation Pack / Orchestrated Single Executor
**Roadmap Section:** P2.0 — Seven-Surface Cognitive OS Lock
**Covered Checkpoints:** P2.0.0–P2.0.8
**Next Pack:** P2.0-B — P2.0.9–P2.0.14 Navigation + Boundary Contracts

## 2. Dispatch Gate Evidence

| Gate | Result |
| --- | --- |
| P1.9.30-SEAL-CRITERIA-REPAIR report exists | yes — `agent/reports/P1_9_30_SEAL_CRITERIA_REPAIR.md` |
| Criteria repair final decision | SEALED / SEALED_FOR_P1_CONTRACT_SCOPE |
| Criteria repair OMNI accepted | yes (Model B) |
| Pre-P2 audit rerun after criteria repair | yes — `agent/reports/P1_PRE_P2_FULL_AUDIT_AND_SEAL_RERUN.md` |
| P2 readiness decision | READY_FOR_P2_REVIEW |
| Working tree clean at dispatch | yes (unrelated consent fixture drift restored before coding) |

## 3. Roadmap Authority Chain

1. Aurel Roadmap v5.5 = canonical roadmap truth
2. P1 seal / pre-P2 audit = permission gate for P2 work
3. Implementation Pack Doctrine = grouping strategy
4. Execution Shape Selector = coding shape
5. CodeOps = validation/report/git discipline
6. local `agent/ROADMAP.md` = repo progress mirror, not roadmap authority

## 4. Execution Shape Used

Selected shape: **Contract Foundation Pack / Orchestrated Single Executor**. Shape obeyed. No scope expansion. No split needed.

## 5. Roadmap Coverage Matrix P2.0.0–P2.0.8

P2.0.0 — DONE
Canonical name: Phase 2 Shell Lock Foundation
Evidence: `AurelShellContract`, `build_aurel_shell_contract()`, `AUREL_SHELL_INVARIANTS`
Tests: `test_p2_0_0_shell_contract_builds_and_serializes`, `test_p2_0_0_shell_truth_label_is_not_live`, `test_p2_0_0_shell_has_no_ui_product_claim`
Truth label: CONTRACT_ONLY / READ_MODEL_ONLY / NOT_LIVE
Unavailable reason: n/a — contract foundation only
Limitations: No product UI, runtime shell, navigation, or routes

P2.0.1 — DONE
Canonical name: AurelShell as Operator Command Skin Contract
Evidence: `AurelShellBoundary`, `AurelShellRole.OPERATOR_COMMAND_SKIN`, `build_aurel_shell_boundary()`
Tests: `test_p2_0_1_shell_boundary_operator_command_skin`
Truth label: CONTRACT_ONLY / PROJECTION_ONLY
Unavailable reason: n/a — contract foundation only
Limitations: No command palette, CLI/TUI, or runtime execution

P2.0.2 — DONE
Canonical name: Aurel CRO Surface Contract
Evidence: `AurelSurfaceContract(kind=AUREL_CRO)`, registry entry `aurel_cro`
Tests: `test_p2_0_2_aurel_cro_surface_contract`, `test_cro_registered_exactly_once`
Truth label: SURFACE_CONTRACT_ONLY
Unavailable reason: surface_contract_only_no_autonomous_cro_runtime
Limitations: No autonomous CRO runtime or self-command execution

P2.0.3 — DONE
Canonical name: HQ Sovereign Operations Surface Contract
Evidence: `AurelSurfaceContract(kind=HQ)`, projection-only source-of-truth relation
Tests: `test_p2_0_3_hq_surface_contract`
Truth label: SURFACE_CONTRACT_ONLY
Unavailable reason: surface_contract_only_no_hq_ui_or_operations_runtime
Limitations: No HQ UI, operations runtime, or live command board

P2.0.4 — DONE
Canonical name: CORP BusinessEnvironment Surface Contract
Evidence: `AurelSurfaceContract(kind=CORP)`, BusinessEnvironment purpose
Tests: `test_p2_0_4_corp_surface_contract`
Truth label: SURFACE_CONTRACT_ONLY
Unavailable reason: surface_contract_only_no_business_environment_mutation
Limitations: No business execution or AGY runtime

P2.0.5 — DONE
Canonical name: HUB Tool Constellation Surface Contract
Evidence: `AurelSurfaceContract(kind=HUB)`, tool constellation purpose
Tests: `test_p2_0_5_hub_surface_contract`
Truth label: SURFACE_CONTRACT_ONLY
Unavailable reason: surface_contract_only_no_tool_execution_or_permission
Limitations: No tool execution or permission grants

P2.0.6 — DONE
Canonical name: IDE / CodeOps Engineering Surface Contract
Evidence: `AurelSurfaceContract(kind=IDE)`, CodeOps engineering purpose
Tests: `test_p2_0_6_ide_surface_contract`
Truth label: SURFACE_CONTRACT_ONLY
Unavailable reason: surface_contract_only_no_ide_implementation
Limitations: No IDE implementation or runtime execution

P2.0.7 — DONE
Canonical name: SYSTEM Operator-Only Root Surface Contract
Evidence: `AurelSurfaceContract(kind=SYSTEM)`, `AurelSurfaceAgentAccess.FORBIDDEN`
Tests: `test_p2_0_7_system_surface_contract`
Truth label: SURFACE_CONTRACT_ONLY / OPERATOR_ONLY_CONTRACT
Unavailable reason: surface_contract_only_no_system_ui_or_enforcement_runtime
Limitations: No SYSTEM UI, enforcement runtime, or agent access

P2.0.8 — DONE
Canonical name: Settings Non-Root Configuration Surface Contract
Evidence: `AurelSurfaceContract(kind=SETTINGS)`, non-root configuration boundary
Tests: `test_p2_0_8_settings_surface_contract`
Truth label: SURFACE_CONTRACT_ONLY / NON_ROOT_CONFIG_CONTRACT
Unavailable reason: surface_contract_only_no_settings_ui_or_root_control
Limitations: No settings UI or root control

## 6. Surface Registry Summary

- Module: `src/agentic_runtime/aurel_shell/`
- Registry: exactly 7 canonical v5.5 surfaces
- Stable order: `aurel_cro`, `hq`, `corp`, `hub`, `ide`, `system`, `settings`
- Truth labels: CONTRACT_ONLY, SURFACE_CONTRACT_ONLY, NOT_LIVE, OPERATOR_ONLY_CONTRACT, NON_ROOT_CONFIG_CONTRACT

## 7. Seven Surface Contract Proof

All seven surfaces built via `build_surface_contract()` and registered in `build_default_surface_registry()`. Display names match v5.5 enum/display pairing. No duplicate or missing surfaces.

## 8. Shell Boundary Proof

`AurelShellBoundary`: `reveals_state=True`, `owns_truth=False`, `executes_commands=False`, `grants_permission=False`, `mutates_runtime=False`. Invariant helpers enforce shell law.

## 9. SYSTEM / Settings Boundary Proof

SYSTEM forbids agent access; Settings is non-root config only; distinct surface IDs and kinds by construction. Settings cannot grant root authority.

## 10. HUB / IDE Authority Boundary Proof

HUB: `tool_execution=False`, `permission_grant=False`. IDE: `runtime_execution=False`, `bypass_validation_discipline=False`.

## 11. Surface Taxonomy Drift Status

**SURFACE_TAXONOMY_DRIFT: YES**

Legacy A-Hub/S-Hub/L-Hub references remain in `agent/ARCHITECTURE.md` and `evaluation_foundation.py` as independent tools — not active P2.0-A registry surfaces. P1.9 `surface_read_model.py` covers five output-passport consumer surfaces without SYSTEM/Settings — separate read-model layer, not P2.0-A registry.

## 12. Integration-First Proof

Contract foundation only. No changes to flow/execution/custos/trace/memory/sandbox/atlas. No frontend/app paths touched.

## 13. Truth Label Proof

No LIVE, UI_LIVE, ROUTE_LIVE, RUNTIME_AUTHORITY, or SOURCE_OF_TRUTH labels claimed. Shell and surfaces use CONTRACT_ONLY / SURFACE_CONTRACT_ONLY / NOT_LIVE.

## 14. Side-Effect / No-Authority Proof

All 19 `AurelShellSideEffectProof` booleans default false and remain false in pack result. No UI, routes, navigation, command palette, permission matrix, runtime mutation, or P2.0-B/P2.1 work.

## 15. Files Created / Modified

Created:
- `src/agentic_runtime/aurel_shell/__init__.py`
- `src/agentic_runtime/aurel_shell/contracts.py`
- `src/agentic_runtime/aurel_shell/surface_registry.py`
- `src/agentic_runtime/aurel_shell/read_model.py`
- `tests/aurel_shell/test_shell_foundation_surface_registry.py`
- `agent/reports/P2_0_A_SHELL_FOUNDATION_SURFACE_REGISTRY.md`

Modified:
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/STATE.md`
- `agent/ROADMAP.md`

## 16. Tests Added / Updated

28 focused tests in `tests/aurel_shell/test_shell_foundation_surface_registry.py`

## 17. Validation Run

```text
.venv/bin/python -m compileall src tests — PASS
.venv/bin/python -m pytest tests/aurel_shell/test_shell_foundation_surface_registry.py -q — 28 passed
.venv/bin/python -m ruff check src/agentic_runtime/aurel_shell tests/aurel_shell — PASS
.venv/bin/python -m mypy src/agentic_runtime/aurel_shell — PASS (4 source files)
```

## 18. What Was Deliberately Not Implemented

- Product UI, routes, topbar, local navigation, floating windows
- Command palette, CLI/TUI binding, permission matrix
- Cross-surface handoff, runtime execution, tool execution
- SYSTEM enforcement runtime, P2.0.9+ navigation/boundary work, P2.1+

## 19. Limitations

Contract/read-model foundation only. Surfaces are UNAVAILABLE for live UI. Registry does not enforce runtime boundaries yet.

## 20. Next Pack

P2.0-B — P2.0.9–P2.0.14 Navigation + Boundary Contracts

## 21. Commit Hash

(set at commit time)

## 22. Final Git Status

(set at commit time)
