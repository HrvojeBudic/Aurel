# P2.7-A Shell / CLI / TUI Binding Foundation

**Date:** 2026-06-30
**Pack:** P2.7-A — P2.7.0–P2.7.5 Shell / CLI / TUI Binding Foundation
**Status:** DONE — CONTRACT_ONLY / BINDING_FOUNDATION_ONLY / NO_COMMAND_EXECUTION_BOUNDARY / NO_RUNTIME_DISPATCH_BOUNDARY

---

## 1. Result Header

P2.7-A establishes contract-only Shell / CLI / TUI binding foundation over P2.6-D section seal evidence: binding section gate, binding target registry, surface binding catalog, capability descriptors, adapter contract, projection consumption contract, read-only command surface, output/render descriptors, no-command-execution boundary, no-runtime-dispatch boundary, binding foundation result, pack result, and side-effect/no-authority proof.

No CLI app, CLI runner, CLI entrypoint, TUI runtime, TUI app, Shell runtime, Shell execution runtime, command parser/router/handler, command execution, tool invocation, workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, surface switching, API server, HTTP routes, live endpoint, event bus, trace/memory/storage writes, permission enforcement, Custos, Mneme, product UI, product behavior, release scope, LIVE, TRACE_VERIFIED, P2.7-B, P2.8, P2.10, or P2.13.

## 2. Git / Worktree Preflight

- **Branch:** master
- **Initial status:** clean
- **Unrelated dirty files:** none
- **P2.7-A dirty/untracked files before implementation:** none
- **P2.7-B dirty/untracked files:** none
- **Future-pack dirty/untracked files:** none
- **Preflight result:** PASS
- **`.venv/bin/python`:** present

## 3. P2.6-D Repo Evidence Gate

| Evidence | Status |
|----------|--------|
| P2.6-D report found | YES |
| P2.6-D report path | `agent/reports/P2_6_D_SURFACE_PROJECTION_API_EVENT_SECTION_SEAL.md` |
| P2.6-D indexed | YES (`agent/REPORTS.md`) |
| P2.6-D validation evidence | YES — compileall, focused 15 passed, aurel_shell 865 passed, ruff, mypy |
| P2.6-D commit evidence | YES — `9c74a57` |
| P2.6-D final/current git clean | YES |
| P2.6-D section seal result | YES — `SurfaceProjectionSectionSealResult` |
| P2.6-D binding availability | YES — `UNAVAILABLE_P2_7_REQUIRED` → P2.7-A |
| P2.6-D no-live-infrastructure proof | YES — `SurfaceProjectionNoLiveInfrastructureProof` |
| P2.6-D side-effect proof | YES — `P26DSideEffectProof` all false |
| P2.6-D overclaim check | PASS |
| P2.6-D P2.7-A ambiguity check | PASS — P2.6-D did not implement P2.7-A |
| P2.6-D future-pack check | PASS |
| **Gate result** | **PASS** |

## 4. OMNI Evidence Ignore Policy

- OMNI evidence required: NO
- OMNI evidence ignored by operator instruction: YES
- Missing OMNI evidence blocked execution: NO
- Notes: repo evidence gate remained mandatory and passed.

## 5. Roadmap Authority Chain

Aurel Roadmap v5.5, operator-confirmed P2 sequence, P2.7 = Shell / CLI / TUI Binding, P2.6-D section seal as immediate predecessor, `agent/TESTS.md` validation authority, `agent/REPORTS.md` report index.

## 6. P2.7 Section Intake

- Confirmed section title: Shell / CLI / TUI Binding
- Roadmap source: Aurel Roadmap v5.5 / operator-confirmed P2 sequence
- Drift found: SURFACE_TAXONOMY_DRIFT inherited; old taxonomy not activated
- Action taken: official seven-surface set only

## 7. Execution Shape Used

Orchestrated Single Executor — standalone `shell_binding_foundation.py` + focused tests + governance sync. No split needed.

## 8. Existing CLI / TUI / Shell Binding Code Discovery

- Existing P2.0-F `cli_binding.py`: read-only inspect contract only; not reused as runtime binding
- Existing P2.7-A binding foundation: none (created new)
- Existing CLI runner / TUI runtime / Shell execution runtime: none in AurelShell scope
- Conflict: none

## 9. P2.6-D Section Seal Result Reuse

- Section seal result reused: YES — by reference in gate and projection consumption contract
- Binding availability reused: YES — gate refs `dependency_binding_availability_ref`
- No-live-infrastructure proof reused: YES — gate refs `dependency_no_live_infrastructure_proof_ref`
- Side-effect proof reused: YES — `P26DSideEffectProof:all_false` ref
- Duplicate source-of-truth created: NO — registry `is_source_of_truth=false`

## 10. P2.6-D Binding Availability Reuse Proof

P2.7-A gate consumes P2.6-D binding availability pointing to P2.7-A. P2.7-A creates contract-level binding foundation only; runtime binding remains `available_as_runtime_binding=false`.

## 11. Official Surface Registry Reuse / Drift Status

- Official surface IDs reused: `aurel_cro`, `hq`, `corp`, `hub`, `ide`, `system`, `settings`
- Surface registry module: `src/agentic_runtime/aurel_shell/surface_registry.py`
- Surface taxonomy drift: DETECTED and reported
- Old surfaces detected: Workspace, Strategy, Forum, Archivium, A-Hub, S-Hub, L-Hub, Society Hub

## 12. Roadmap Coverage Matrix P2.7.0–P2.7.5

### P2.7.0 — DONE
- **Capsule name:** Shell / CLI / TUI Binding Section Intake / Gate
- **Evidence:** `ShellBindingSectionGate`, `ShellBindingSectionGateStatus`
- **Tests:** `test_p2_7_0_binding_section_gate`, `test_gate_dependency_and_omni_policy`
- **Truth label:** BINDING_GATE_ONLY / CONTRACT_ONLY / REPORT_ONLY / NOT_LIVE / NOT_TRACE_VERIFIED
- **Unavailable reason:** binding runtime unavailable by design
- **Limitations:** gate does not create binding runtime

### P2.7.1 — DONE
- **Capsule name:** Binding Target Registry / Surface Binding Catalog
- **Evidence:** `ShellBindingTargetRegistry`, `ShellBindingTargetEntry`, `ShellBindingSurfaceCatalog`
- **Tests:** `test_p2_7_1_target_registry_and_surface_catalog`
- **Truth label:** TARGET_REGISTRY_ONLY / SURFACE_BINDING_CATALOG_ONLY / NOT_SOURCE_OF_TRUTH / NOT_SURFACE_SWITCH
- **Unavailable reason:** runtime binding deferred to P2.7-B+
- **Limitations:** registry is not source-of-truth; catalog is not live surface switcher

### P2.7.2 — DONE
- **Capsule name:** CLI / TUI Capability Descriptor Contract
- **Evidence:** `ShellBindingCapabilityDescriptor`, `ShellBindingCapabilityMode`
- **Tests:** `test_p2_7_2_capability_descriptors`
- **Truth label:** CAPABILITY_DESCRIPTOR_ONLY / NOT_CLI_APP / NOT_TUI_RUNTIME / NOT_SHELL_RUNTIME
- **Unavailable reason:** executable runtime behavior UNAVAILABLE
- **Limitations:** descriptors are not CLI app, TUI runtime, or Shell execution runtime

### P2.7.3 — DONE
- **Capsule name:** Binding Adapter / Projection Consumption Contract
- **Evidence:** `ShellBindingAdapterContract`, `ShellBindingProjectionConsumptionContract`
- **Tests:** `test_p2_7_3_adapter_and_projection_consumption`
- **Truth label:** ADAPTER_CONTRACT_ONLY / PROJECTION_CONSUMPTION_CONTRACT_ONLY / NOT_RUNTIME_DISPATCH
- **Unavailable reason:** live API/event bridge consumption unavailable by design
- **Limitations:** adapter is not runtime dispatch; consumption is by reference only

### P2.7.4 — DONE
- **Capsule name:** Read-Only Command Surface / Output Descriptor Contract
- **Evidence:** `ShellBindingReadOnlyCommandSurface`, `ShellBindingOutputDescriptor`, `ShellBindingRenderDescriptor`
- **Tests:** `test_p2_7_4_read_only_command_surface_and_output_descriptors`
- **Truth label:** READ_ONLY_COMMAND_SURFACE_ONLY / OUTPUT_DESCRIPTOR_ONLY / RENDER_DESCRIPTOR_ONLY / NOT_PRODUCT_UI
- **Unavailable reason:** command execution unavailable by design
- **Limitations:** command surface is descriptor-only; output/render are not product UI

### P2.7.5 — DONE
- **Capsule name:** Binding Foundation Result / No-Command-Execution Boundary
- **Evidence:** `ShellBindingNoCommandExecutionBoundary`, `ShellBindingNoRuntimeDispatchBoundary`, `ShellBindingFoundationResult`, `P27ASideEffectProof`, `P27AShellBindingFoundationResult`
- **Tests:** `test_p2_7_5_boundaries_and_foundation_result`, `test_side_effect_proof_all_false`
- **Truth label:** BINDING_FOUNDATION_ONLY / NO_COMMAND_EXECUTION_BOUNDARY / NO_RUNTIME_DISPATCH_BOUNDARY
- **Unavailable reason:** runtime dispatch and command execution unavailable by design
- **Limitations:** foundation is not operator-testable product behavior

## 13–27. Boundary Proofs

All required no-CLI-runner / no-TUI-runtime / no-Shell-runtime / no-command-execution / no-runtime-dispatch / no-trace-write / no-product / no-future-pack proofs verified via `P27ASideEffectProof`, active boundaries, and focused tests. P2.7-B/P2.8/P2.10/P2.13 not started.

## 28. Truth Label Boundary Proof

Truth labels remain closed-world: CONTRACT_ONLY, BINDING_FOUNDATION_ONLY, DEV_FIXTURE, REPORT_ONLY, UNAVAILABLE, NOT_LIVE, NOT_TRACE_VERIFIED, NOT_PRODUCT_BEHAVIOR, NOT_RELEASE_SCOPE. No LIVE or TRACE_VERIFIED claims.

## 29. Side-Effect / No-Authority Proof

All `P27ASideEffectProof` fields false (43 booleans). Verified by `test_side_effect_proof_all_false`.

## 30. Files Created / Modified

**Created:**
- `src/agentic_runtime/aurel_shell/shell_binding_foundation.py`
- `tests/aurel_shell/test_shell_binding_foundation.py`
- `agent/reports/P2_7_A_SHELL_CLI_TUI_BINDING_FOUNDATION.md`

**Modified:**
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/ROADMAP.md`
- `agent/STATE.md`
- `agent/TESTS.md`

## 31. Tests Added / Updated

- `tests/aurel_shell/test_shell_binding_foundation.py` — 13 focused tests

## 32. Validation Run

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_binding_foundation.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.7-A **13 passed**; `tests/aurel_shell` **878 passed**; ruff **PASS**; mypy **PASS** (316 source files).

## 33. What Was Deliberately Not Implemented

CLI app, CLI runner, CLI entrypoint, TUI runtime, TUI app, Shell runtime, Shell execution runtime, command parser/router/handler, command execution, tool invocation, workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, surface switching, API server, HTTP routes, live endpoint, event bus, trace/memory/storage writes, permission enforcement, approval runtime, Custos, Mneme, product UI, product behavior, P2.7-B, P2.8, P2.10, P2.13.

## 34. Limitations

Binding foundation is contract-only. Runtime binding deferred to P2.7-B+. Read-only command surface names are descriptors only. Projection consumption references P2.6-D evidence; it does not consume live API or event bridge.

## 35. Next Recommended Step

**P2.7-B — P2.7.6–P2.7.10 Shell Binding Read Models / Command Surface Adapter Expansion**

## 36. Commit Hash

PENDING_AT_COMMIT

## 37. Final Git Status

PENDING_AT_COMMIT
