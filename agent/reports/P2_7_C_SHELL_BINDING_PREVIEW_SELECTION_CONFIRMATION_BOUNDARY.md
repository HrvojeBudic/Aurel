# P2.7-C Shell Binding Preview / Selection / Operator Confirmation Boundary

**Date:** 2026-06-30
**Pack:** P2.7-C — P2.7.11–P2.7.15 Shell Binding Preview / Selection / Operator Confirmation Boundary
**Status:** DONE — CONTRACT_ONLY / PREVIEW_ONLY / SELECTION_INTENT_ONLY / NO_COMMAND_EXECUTION_BOUNDARY / NO_RUNTIME_DISPATCH_BOUNDARY / NO_APPROVAL_ACTIVATION_BOUNDARY

---

## 1. Result Header

P2.7-C establishes contract-only Shell binding preview / selection / confirmation-boundary contracts over P2.7-B binding read model / command surface adapter evidence: binding preview gate, preview bundle, preview items, preview risk notes, selected binding intent, selection candidates, selection state, operator confirmation requirement, confirmation intent, confirmation outcome read model, cancel / reject / defer descriptors, confirmation boundary result, side-effect/no-authority proof, and pack result.

No UI, product UI, CLI app/runner/entrypoint, TUI runtime/app, Shell runtime/execution runtime, command parser/router/handler, command execution/invocation, output writer runtime, render runtime, operator confirmation runtime, approval runtime, HITL approval activation, authorization, permission enforcement/grant/denial, Custos/Mneme integration, tool invocation, workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, surface switching, navigation mutation, API server, HTTP routes, live endpoint, event bus, trace/memory/storage writes, source-of-truth store, product behavior, release scope, LIVE, TRACE_VERIFIED, P2.7-D, P2.8, P2.10, or P2.13.

## 2. Git / Worktree Preflight

- **Branch:** master
- **Initial status:** clean
- **Unrelated dirty files:** none
- **P2.7-C dirty/untracked files before implementation:** none
- **P2.7-D dirty/untracked files:** none
- **Future-pack dirty/untracked files:** none
- **Preflight result:** PASS
- **`.venv/bin/python`:** present (Python 3.12.3)

## 3. P2.7-B Repo Evidence Gate

| Evidence | Status |
|----------|--------|
| P2.7-B report found | YES |
| P2.7-B report path | `agent/reports/P2_7_B_SHELL_BINDING_READ_MODELS_COMMAND_SURFACE_ADAPTER.md` |
| P2.7-B indexed | YES (`agent/REPORTS.md`) |
| P2.7-B validation evidence | YES — compileall, focused 14 passed, aurel_shell 892 passed, ruff, mypy (317 files) |
| P2.7-B commit evidence | YES — `c6cc7a0` (report-recorded; `79e9718` records the hash in the pack report) |
| P2.7-B final/current git clean | YES |
| P2.7-B binding read model gate | YES — `ShellBindingReadModelGate` |
| P2.7-B read model registry | YES — `ShellBindingReadModelRegistry` |
| P2.7-B read model inventory | YES — `ShellBindingReadModelInventory` |
| P2.7-B command descriptor read model | YES — `ShellCommandDescriptorReadModel` |
| P2.7-B command surface adapter read model | YES — `ShellCommandSurfaceAdapterReadModel` |
| P2.7-B output preview schema | YES — `ShellBindingOutputPreviewSchema` |
| P2.7-B render preview schema | YES — `ShellBindingRenderPreviewSchema` |
| P2.7-B context descriptor | YES — `ShellBindingContextDescriptor` |
| P2.7-B availability read model | YES — `ShellBindingAvailabilityReadModel` |
| P2.7-B selection descriptor | YES — `ShellBindingSelectionDescriptor` |
| P2.7-B adapter expansion result | YES — `ShellBindingAdapterExpansionResult` |
| P2.7-B side-effect proof | YES — `P27BSideEffectProof` all false (47 booleans) |
| P2.7-B overclaim check | PASS — no LIVE/TRACE_VERIFIED/RELEASE_SCOPE/product behavior |
| P2.7-B P2.7-C ambiguity check | PASS — P2.7-B did not implement P2.7-C |
| P2.7-B future-pack check | PASS — no P2.7-D/P2.8/P2.10/P2.13 |
| **Gate result** | **PASS** |

## 4. OMNI Evidence Ignore Policy

- OMNI evidence required: NO
- OMNI evidence ignored by operator instruction: YES
- Missing OMNI evidence blocked execution: NO
- Notes: repo evidence gate remained mandatory and passed. The gate object encodes `omni_evidence_required=False` and `omni_evidence_ignored_by_operator_instruction=True`.

## 5. Roadmap Authority Chain

Aurel Roadmap v5.5, operator-confirmed P2 sequence, P2.7 = Shell / CLI / TUI Binding, P2.7-B binding read model / adapter expansion as immediate predecessor, P2.7-B adapter expansion result as immediate technical dependency, P2.7-B side-effect proof as safety dependency, inherited P2.7-A no-command-execution / no-runtime-dispatch boundaries, `agent/TESTS.md` validation authority, `agent/REPORTS.md` report index. Local `agent/ROADMAP.md` updated as progress mirror only.

## 6. P2.7 Section Context

- Confirmed section title: Shell / CLI / TUI Binding
- Roadmap source: Aurel Roadmap v5.5 / operator-confirmed P2 sequence
- P2.7-C expands P2.7 as preview / selection / confirmation-boundary contracts only; not executable CLI/TUI/Shell runtime, not real operator confirmation or approval runtime

## 7. Execution Shape Used

Orchestrated Single Executor — standalone `shell_binding_preview_selection.py` + focused tests + governance sync. No split needed. Selected shape obeyed.

## 8. Existing Preview / Selection / Confirmation / Approval Code Discovery

- Existing P2.7-B `shell_binding_read_models.py`: binding read model / adapter contracts (reused by reference, not duplicated)
- Existing P2.5-C `cross_surface_handoff_preview.py`: handoff preview / confirmation boundary (contract-only, different section); not reused as runtime
- Existing P2.4-C `global_command_proposal.py`: command proposal / no-execution boundary (contract-only); not command execution
- Existing shell binding preview/selection code (P2.7-C): none (created new)
- Existing operator confirmation runtime / approval runtime / HITL approval / permission enforcement / Custos decisioning / command execution / runtime dispatch / trace write / product UI: none in AurelShell scope
- Existing P2.7-D code: none
- Conflict: none
- Action taken: created new `shell_binding_preview_selection.py` module

## 9. P2.7-B Adapter Expansion Result Reuse Proof

- Adapter expansion result reused: YES — by reference in preview gate (`dependency_adapter_expansion_result_ref`), preview bundle (`source_read_model_ref`), and pack result (`p2_7_b_evidence_ref`)
- Side-effect proof reused: YES — `P27BSideEffectProof:all_false` ref in gate
- Duplicate source-of-truth created: NO — preview/selection/confirmation contracts are derived read models; no source-of-truth store created; `P27CSideEffectProof.source_of_truth_created=False`

## 10. Official Surface Registry Reuse / Drift Status

- Official surface IDs reused: `OFFICIAL_ACTIVE_SURFACE_NAMES` (Aurel CRO, HQ, CORP, HUB, IDE, SYSTEM, Settings) — carried on the preview bundle (`official_surface_set`)
- Surface registry module: `src/agentic_runtime/aurel_shell/surface_registry.py`
- Surface taxonomy drift: detected via `detect_surface_taxonomy_drift()` and reported in pack result; old taxonomy not activated
- Old surfaces detected: Workspace, Strategy, Forum, Archivium, A-Hub, S-Hub, L-Hub, Society Hub — verified absent from active surface set by `test_surface_taxonomy_drift_does_not_activate_old_surfaces`

## 11. Roadmap Coverage Matrix P2.7.11–P2.7.15

### P2.7.11 — DONE
- **Capsule name:** Binding Preview Bundle / Safe Preview Contract
- **Evidence:** `ShellBindingPreviewGate`, `ShellBindingPreviewGateStatus`, `ShellBindingPreviewBundle`, `ShellBindingPreviewItem`, `ShellBindingPreviewItemKind`, `ShellBindingPreviewRiskNote`, `ShellBindingPreviewRiskKind`
- **Tests:** `test_p2_7_11_preview_gate_bundle_items_risk_notes`, `test_gate_dependency_and_omni_policy`
- **Truth label:** PREVIEW_ONLY / PREVIEW_BUNDLE_ONLY / PREVIEW_ITEM_ONLY / PREVIEW_RISK_NOTE_ONLY / PREVIEW_GATE_ONLY / CONTRACT_ONLY / NOT_UI / NOT_PRODUCT_UI / NOT_APPROVAL_RUNTIME / NOT_PERMISSION_ENFORCEMENT
- **Unavailable reason:** UI rendering / product UI unavailable by design
- **Limitations:** preview bundle is not UI; preview item is not product UI; risk note does not enforce policy or activate approval

### P2.7.12 — DONE
- **Capsule name:** Binding Selection Intent / Non-Executable Selection Contract
- **Evidence:** `ShellBindingSelectedIntent`, `ShellBindingSelectionCandidate`, `ShellBindingSelectionState`, `ShellBindingSelectionMode`
- **Tests:** `test_p2_7_12_selection_intent_candidate_state`
- **Truth label:** SELECTION_INTENT_ONLY / SELECTION_CANDIDATE_ONLY / SELECTION_STATE_ONLY / CONTRACT_ONLY / NOT_COMMAND_EXECUTION / NOT_RUNTIME_DISPATCH / NOT_RUNTIME_MUTATION
- **Unavailable reason:** command execution / runtime mutation unavailable by design
- **Limitations:** selected binding is not invoked binding; selection candidate is selectable as contract only; selection state does not mutate runtime/shell state or execute selection

### P2.7.13 — DONE
- **Capsule name:** Operator Confirmation Requirement / Confirmation Intent Boundary
- **Evidence:** `ShellBindingConfirmationRequirement`, `ShellBindingConfirmationIntent`, `ShellBindingConfirmationRequirementStatus`
- **Tests:** `test_p2_7_13_confirmation_requirement_and_intent`
- **Truth label:** CONFIRMATION_REQUIREMENT_ONLY / CONFIRMATION_INTENT_ONLY / CONTRACT_ONLY / NOT_APPROVAL_RUNTIME / NOT_HITL_APPROVAL / NOT_AUTHORIZATION / NOT_PERMISSION_GRANT / NOT_COMMAND_EXECUTION
- **Unavailable reason:** approval runtime / HITL activation unavailable by design
- **Limitations:** confirmation requirement is not approval and activates no approval/HITL; confirmation intent records operator intent as contract only, grants no authority/permission, executes no binding

### P2.7.14 — DONE
- **Capsule name:** Confirmation Outcome / Cancel / Reject / Defer Read Model
- **Evidence:** `ShellBindingConfirmationOutcomeReadModel`, `ShellBindingConfirmationOutcomeStatus`, `ShellBindingCancelDescriptor`, `ShellBindingRejectDescriptor`, `ShellBindingDeferDescriptor`
- **Tests:** `test_p2_7_14_outcome_cancel_reject_defer`
- **Truth label:** CONFIRMATION_OUTCOME_READ_MODEL_ONLY / CANCEL_DESCRIPTOR_ONLY / REJECT_DESCRIPTOR_ONLY / DEFER_DESCRIPTOR_ONLY / CONTRACT_ONLY / NOT_CUSTOS_DECISION / NOT_PERMISSION_GRANT / NOT_PERMISSION_DENIAL / NOT_RUNTIME_MUTATION
- **Unavailable reason:** Custos decisioning / permission grant / runtime transition unavailable by design
- **Limitations:** outcome is read model only, not Custos decision; confirmed state is contract only, not permission grant; cancel/reject/defer are descriptors, not runtime transitions

### P2.7.15 — DONE
- **Capsule name:** Preview Selection Boundary Result / No-Execution / No-Approval-Activation Contract
- **Evidence:** `ShellBindingConfirmationBoundaryResult`, `ShellBindingPreviewSelectionTruthBoundary`, `P27CSideEffectProof`, `P27CShellBindingPreviewSelectionResult`
- **Tests:** `test_p2_7_15_confirmation_boundary_result`, `test_side_effect_proof_all_false`, `test_p2_7_c_does_not_start_future_work`
- **Truth label:** BOUNDARY_RESULT_ONLY / NO_COMMAND_EXECUTION_BOUNDARY / NO_RUNTIME_DISPATCH_BOUNDARY / NO_APPROVAL_ACTIVATION_BOUNDARY / CONTRACT_ONLY / NOT_UI / NOT_APPROVAL_RUNTIME / NOT_CUSTOS_DECISION / NOT_COMMAND_EXECUTION / NOT_RUNTIME_DISPATCH / NOT_PRODUCT_BEHAVIOR / NOT_LIVE / NOT_TRACE_VERIFIED
- **Unavailable reason:** command execution, approval activation, permission enforcement, Custos decisioning, runtime dispatch, trace write unavailable by design
- **Limitations:** boundary result bundles contracts only; next pack is P2.7-D; no future work started

## 12–25. Boundary Proofs

All no-UI/product-UI, no-command-parser/router/handler/execution, no-CLI-runner/TUI-runtime/Shell-runtime, no-operator-confirmation-runtime/approval/HITL-activation, no-permission-enforcement/Custos-decisioning, no-tool/workflow/runtime-dispatch, no-trace/memory/storage-write, no-product/release/LIVE/TRACE_VERIFIED, and no-P2.7-D/P2.8/P2.10/P2.13 proofs are verified via `P27CSideEffectProof` (49 booleans all false), the `ShellBindingConfirmationBoundaryResult` `creates_*` / `activates_*` flags (all false), the preview/selection/confirmation invariant assertions, and focused tests.

## 26. Truth Label Boundary Proof

Truth labels remain closed-world via `ShellBindingPreviewSelectionTruthBoundary`: CONTRACT_ONLY, PREVIEW_ONLY, PREVIEW_BUNDLE_ONLY, PREVIEW_ITEM_ONLY, PREVIEW_RISK_NOTE_ONLY, SELECTION_INTENT_ONLY, SELECTION_CANDIDATE_ONLY, SELECTION_STATE_ONLY, CONFIRMATION_REQUIREMENT_ONLY, CONFIRMATION_INTENT_ONLY, CONFIRMATION_OUTCOME_READ_MODEL_ONLY, CANCEL_DESCRIPTOR_ONLY, REJECT_DESCRIPTOR_ONLY, DEFER_DESCRIPTOR_ONLY, BOUNDARY_RESULT_ONLY, PREVIEW_GATE_ONLY, NO_COMMAND_EXECUTION_BOUNDARY, NO_RUNTIME_DISPATCH_BOUNDARY, NO_APPROVAL_ACTIVATION_BOUNDARY, DEV_FIXTURE, REPORT_ONLY, UNAVAILABLE, and the NOT_* boundary labels. No LIVE or TRACE_VERIFIED claims.

## 27. Side-Effect / No-Authority Proof

All `P27CSideEffectProof` fields false (49 booleans). Verified by `test_side_effect_proof_all_false`. The `ShellBindingConfirmationBoundaryResult` carries `creates_ui`, `creates_product_ui`, `creates_command_execution`, `creates_operator_confirmation_runtime`, `creates_approval_runtime`, `activates_hitl_approval`, `creates_permission_enforcement`, `creates_custos_decision`, `creates_runtime_dispatch`, `creates_runtime_mutation`, `creates_trace_write`, `creates_product_behavior` — all false.

## 28. Files Created / Modified

**Created:**
- `src/agentic_runtime/aurel_shell/shell_binding_preview_selection.py`
- `tests/aurel_shell/test_shell_binding_preview_selection.py`
- `agent/reports/P2_7_C_SHELL_BINDING_PREVIEW_SELECTION_CONFIRMATION_BOUNDARY.md`

**Modified:**
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/ROADMAP.md`
- `agent/STATE.md`
- `agent/TESTS.md`

`src/agentic_runtime/aurel_shell/__init__.py` was deliberately **not** modified — P2.7-A/P2.7-B established the precedent that binding modules are imported directly by path (no `__init__` re-export), keeping scope minimal.

## 29. Tests Added / Updated

- `tests/aurel_shell/test_shell_binding_preview_selection.py` — 14 focused tests

## 30. Validation Run

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_binding_preview_selection.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.7-C **14 passed**; `tests/aurel_shell` **906 passed**; ruff **PASS**; mypy **PASS** (318 source files).

## 31. What Was Deliberately Not Implemented

UI, product UI, CLI app/runner/entrypoint, TUI runtime/app, Shell runtime/execution runtime, command parser/router/handler, command execution/invocation, output writer runtime, render runtime, operator confirmation runtime, approval runtime, HITL approval activation, authorization, permission enforcement/grant/denial, Custos/Mneme integration, tool invocation, workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, surface switching, navigation mutation, API server, HTTP routes, live endpoint, event bus, trace/memory/storage writes, source-of-truth store, product behavior, P2.7-D, P2.8, P2.10, P2.13.

## 32. Limitations

Preview, selection and confirmation contracts are contract-only. Preview bundle is an intent explanation, not UI; preview item does not render UI. Selection records contract-level intent (`invokes_binding=False`, `executes_command=False`, `dispatches_runtime=False`); selection state does not mutate runtime/shell state. Confirmation requirement marks that future execution must pass confirmation (`required_before_future_execution=True`) but does not require/activate approval or HITL. Confirmation intent records operator intent as contract only. Confirmation outcome read model is not a Custos decision; confirmed state is not a permission grant. Cancel/reject/defer are descriptors, not runtime transitions. All execution / approval / permission / Custos / runtime behavior remains deferred to P2.7-D and beyond.

## 33. Next Recommended Step

**P2.7-D — P2.7.16–P2.7.20 Shell / CLI / TUI Binding Section Seal**

## 34. Commit Hash

`47d69d2` — `feat(aurel-shell): add P2.7 binding preview boundary`

## 35. Final Git Status

Clean — all in-scope files committed on `master`.
