# P2.11-A — Surface Permission Matrix Foundation / Client-Surface Authority Baseline

## 1. Result Header

**Status:** DONE — Surface Permission Matrix Foundation / Client-Surface Authority Baseline.

P2.11-A defines a deterministic, evidence-bound client x surface x action permission matrix over the P2.10 multi-client Shell baseline. P2.11 as a whole is not complete. P2.11-B is next. P2.12+ remains not started. No command execution, tool execution, approval execution, runtime control, sandbox control, memory write, policy mutation, identity mutation, full policy runtime, Custos enforcement, Shell LIVE, product readiness, final P2 seal, or P3 handoff is implemented or claimed.

## 2. Scope

Covered: P2.11-A only.

Implemented:

- `SurfacePermissionAction`
- `SurfacePermissionLevel`
- `SurfacePermissionReason`
- `SurfacePermissionEvidenceRef`
- `SurfacePermissionEntry`
- `ClientSurfaceAuthorityBaseline`
- `SurfacePermissionMatrix`
- `SurfacePermissionMatrixSummary`
- `SurfacePermissionNoOverclaimBoundary`
- `P211AHandoff`
- `P211AResult`

Not implemented: P2.11-B, P2.12+, command/tool/approval execution, runtime/sandbox control, workflow execution, agent dispatch, memory writes, policy mutation, identity mutation, full policy runtime, Custos enforcement, Shell LIVE, product readiness, final P2 seal, or P3 handoff.

## 3. P2.10-E Prerequisite Gate

P2.10-E report found: yes.

P2.10-E report path: `agent/reports/P2_10_E_MULTI_CLIENT_OPERATOR_DEMO_SEAL.md`.

P2.10-E report indexed: yes.

P2.10-E proves P2.10 multi-client foundation sealed: yes, through `P210CompletionSeal.p210_done`, `P210OperatorDemoSeal`, `MultiClientShellEvidenceBundle`, and P2.10-A/B/C/D evidence.

P2.10-E points next to P2.11: yes.

P2.12+ started: no.

Gate result: passed.

## 4. Git / Worktree Preflight

Branch: `master`.

Initial status: clean.

Recent head before work: `6a871cb docs(agent): record P2.10-E commit hash`.

Unrelated dirty files: none.

P2.12+ dirty/untracked files: none.

Runtime/sandbox/identity/policy dirty/untracked files: none.

Client/frontend/desktop/CLI/TUI dirty/untracked files: none.

## 5. Evidence Consumed

- P2.10-E: `agent/reports/P2_10_E_MULTI_CLIENT_OPERATOR_DEMO_SEAL.md`, `multi_client_demo_seal.py`, P2.10-E focused tests.
- P2.10-D: `agent/reports/P2_10_D_CLI_TUI_PARITY_BINDING.md`, `terminal_shell_client.py`, terminal/CLI no-execution tests.
- P2.10-C: `agent/reports/P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md`, `desktop_shell_contract.py`.
- P2.10-B: `agent/reports/P2_10_B_LOCAL_WEB_SHELL_SKELETON.md`, `web_shell_read_model.py`.
- P2.10-A: `agent/reports/P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md`, `multi_client_foundation.py`.
- P2.VSLICE-A: `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md`, `tests/test_p2_command_preflight.py`.
- P2.REVIEW-A: `agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md`.
- Agent canon: `agent/ACTIVE_TASK.md`, `agent/ROADMAP.md`, `agent/STATE.md`, `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`, `agent/TESTS.md`, `agent/REPORTS.md`.

## 6. Client / Surface Baseline

Clients included: `WEB`, `DESKTOP_TAURI`, `CLI`, `TUI`, `MOBILE_FOUNDATION`.

Surfaces included: `Aurel CRO`, `HQ`, `CORP`, `HUB`, `IDE`, `SYSTEM`, `Settings`.

Client run modes preserved: `WEB_DEV_RUNNABLE`, `DESKTOP_TAURI_DEV_RUNNABLE`, `CLI_READ_ONLY`, `TUI_CONTRACT_ONLY`, `MOBILE_CONTRACT_ONLY`.

Truth labels preserved: `DEV_FIXTURE`, `READ_ONLY`, `CONTRACT_ONLY`, `PREFLIGHT_ONLY`, `NOT_STARTED`, `UNAVAILABLE`.

Preflight status: `PREFLIGHT_ONLY`, not execution.

Contract-only paths: TUI and mobile foundation.

Read-only paths: CLI inspection/export and read-model actions.

Unavailable paths: CLI visual open/focus, mobile preflight/export/commands future-gated, all execution/runtime/sandbox/policy/identity/memory/workflow actions denied.

## 7. Permission Action Set

Safe pre-execution actions: `SEE_SURFACE`, `OPEN_SURFACE`, `FOCUS_SURFACE`, `READ_SURFACE_STATE`, `INSPECT_SURFACE_EVIDENCE`, `VIEW_SURFACE_COMMANDS`, `REQUEST_COMMAND_PREFLIGHT`, `EXPORT_SURFACE_READ_MODEL`, `VIEW_LIMITATIONS`.

Disabled/future-gated execution actions: `EXECUTE_COMMAND`, `APPROVE_ACTION`, `RUN_TOOL`, `START_RUNTIME`, `STOP_RUNTIME`, `TRIGGER_SANDBOX`, `WRITE_MEMORY`, `MODIFY_POLICY`, `MUTATE_IDENTITY`, `DISPATCH_AGENT`, `RUN_WORKFLOW`.

## 8. Permission Level / Reason Set

Permission levels: `ALLOWED`, `READ_ONLY`, `PREFLIGHT_ONLY`, `CONTRACT_ONLY`, `FUTURE_GATED`, `UNAVAILABLE`, `DENIED`, `ERROR`.

Permission reasons include P2.10 baseline, read-only client, contract-only client, unavailable client, sensitive surface, preflight-only, execution not implemented, runtime control not implemented, sandbox control not implemented, memory write not implemented, policy mutation not implemented, identity mutation not implemented, mobile foundation only, no evidence, and error.

`PREFLIGHT_ONLY` is distinct from execution. `DENIED`, `UNAVAILABLE`, and `FUTURE_GATED` are distinct. `NO_EVIDENCE` is representable.

## 9. Client-Surface Authority Baseline

Implemented as `ClientSurfaceAuthorityBaseline`.

Baseline rules:

- Safe actions are visibility, navigation, inspection, preflight request, export, and limitations only.
- All execution/runtime/sandbox/policy/identity/memory/workflow actions are denied.
- `PREFLIGHT_ONLY` means governed preflight request only.
- `ALLOWED` is scoped to the named Shell surface action only.
- SYSTEM, Settings, and IDE are sensitive surfaces.
- Mobile remains contract-only/future-gated.

## 10. Surface Permission Matrix

Implemented as `SurfacePermissionMatrix`.

Shape: 5 clients x 7 surfaces x 20 actions = 700 entries.

Counts:

- `ALLOWED`: 56
- `READ_ONLY`: 98
- `PREFLIGHT_ONLY`: 21
- `CONTRACT_ONLY`: 105
- `FUTURE_GATED`: 21
- `UNAVAILABLE`: 14
- `DENIED`: 385
- `ERROR`: 0

Missing entries: none.

Inconsistencies: none.

Every entry includes client, surface, action, level, reason, evidence refs, limitations, source pack refs, and no-overclaim boundaries.

## 11. Sensitive Surface Handling

Sensitive surfaces: `SYSTEM`, `Settings`, `IDE`.

SYSTEM: visible/readable/preflight-only where client evidence supports; all execution/mutation/runtime/sandbox actions denied.

Settings: visible/readable/preflight-only where client evidence supports; no root/system mutation implemented.

IDE: visible/readable/preflight-only where client evidence supports; no runtime execution authority implemented.

Mutation implemented: no.

Runtime control implemented: no.

Sandbox control implemented: no.

Policy mutation implemented: no.

Identity mutation implemented: no.

Execution implemented: no.

## 12. No-Execution Boundary

All required no-overclaim boundaries are encoded in `SurfacePermissionNoOverclaimBoundary`.

Command execution, tool execution, approval execution, runtime control, sandbox control, memory write, policy mutation, identity mutation, full policy runtime, Custos enforcement, Shell LIVE, product readiness, P2.11 completion, P2.12+, final P2 seal, and P3 handoff are not implemented or claimed.

## 13. What Is Sealed

- P2.11-A Surface Permission Matrix foundation.
- Permission action set.
- Permission level/reason set.
- Evidence-bound permission entries.
- Client-surface authority baseline.
- Deterministic surface permission matrix.
- Sensitive-surface conservative handling.
- No-execution/no-overclaim boundary.
- P2.11-B handoff pointer.

## 14. What Is Not Sealed

- P2.11-B.
- P2.11 as a whole.
- P2.12+.
- P2 final seal.
- P3 handoff.
- Command/tool/approval execution.
- Runtime/sandbox control.
- Memory write.
- Policy/identity mutation.
- Full policy runtime.
- Custos enforcement.
- Shell LIVE.
- Product readiness.

## 15. Tests / Validation

Validation run:

- `.venv/bin/python -m compileall src tests` — PASS
- `.venv/bin/python -m pytest tests/test_p211a_surface_permission_matrix.py -q` — PASS, 4 passed
- `.venv/bin/python -m pytest tests/test_p211a_client_surface_authority_baseline.py -q` — PASS, 4 passed
- `.venv/bin/python -m pytest tests/test_p211a_surface_permission_no_execution.py -q` — PASS, 4 passed
- `.venv/bin/python -m pytest tests/test_p211a_p211b_handoff.py -q` — PASS, 3 passed
- `.venv/bin/python -m pytest tests/test_p210e_multi_client_demo_seal.py tests/test_p210e_truth_consistency_matrix.py tests/test_p210e_no_overclaim_matrix.py tests/test_p210e_p211_handoff.py -q` — PASS, 16 passed
- `.venv/bin/python -m pytest tests/test_p210d_terminal_shell_client.py tests/test_p210d_cli_tui_parity_matrix.py tests/test_p210d_terminal_no_execution.py -q` — PASS, 17 passed
- `.venv/bin/python -m pytest tests/test_p210d_cli_commands.py -q` — PASS, 6 passed
- `.venv/bin/python -m pytest tests/test_p210c_desktop_shell_contract.py tests/test_p210c_desktop_capability_boundary.py tests/test_p210c_tauri_wrapper_truth.py -q` — PASS, 20 passed
- `.venv/bin/python -m pytest tests/test_p210b_web_shell_read_model.py tests/test_p210b_web_shell_contract_binding.py -q` — PASS, 18 passed
- `.venv/bin/python -m pytest tests/test_p210a_multi_client_foundation.py tests/test_shell_client_parity_matrix.py tests/test_shell_client_run_modes.py -q` — PASS, 23 passed
- `.venv/bin/python -m pytest tests/test_p2_command_preflight.py -q` — PASS, 6 passed
- `.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q` — PASS, 18 passed
- `.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q` — PASS, 17 passed
- `.venv/bin/python -m mypy src/agentic_runtime` — PASS
- `.venv/bin/python -m ruff check src tests` — PASS

Validation not run: full pytest suite, coverage, Bandit.

## 16. No-Scope-Expansion Proof

P2.11-B implemented: no.

P2.11 claimed complete: no.

P2.12+ implemented: no.

P2 final seal claimed: no.

P3 handoff claimed: no.

Command execution implemented: no.

Tool execution implemented: no.

Approval execution implemented: no.

Runtime control implemented: no.

Sandbox control implemented: no.

Memory write implemented: no.

Policy mutation implemented: no.

Identity mutation implemented: no.

Full policy runtime implemented: no.

Custos enforcement implemented: no.

P2.VSLICE-A behavior changed: no.

Shell LIVE claimed: no.

Product readiness claimed: no.

## 17. P2.11-B Handoff

Next pack: P2.11-B.

Next title: Surface Permission Projection / Matrix Read Model.

Handoff status: pointer only; P2.11-B not implemented.

Projection needs: operator-facing matrix projection, query/filter/grouping read model, stable JSON export contract.

Remaining risks: permission matrix is not runtime enforcement; mobile remains contract-only/future-gated; P2.12 truth-label fixture discipline is not implemented.

## 18. Files Created / Modified

Created:

- `src/agentic_runtime/aurel_shell/surface_permission_matrix.py`
- `tests/test_p211a_surface_permission_matrix.py`
- `tests/test_p211a_client_surface_authority_baseline.py`
- `tests/test_p211a_surface_permission_no_execution.py`
- `tests/test_p211a_p211b_handoff.py`
- `agent/reports/P2_11_A_SURFACE_PERMISSION_MATRIX_FOUNDATION.md`

Modified:

- `src/agentic_runtime/aurel_shell/multi_client_demo_seal.py`
- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/ARCHITECTURE.md`
- `agent/DECISIONS.md`
- `agent/TESTS.md`

## 19. Remaining Risks / Limitations

Permission matrix: foundation/read-model contract only, not runtime enforcement.

Sensitive surfaces: conservative but not a final policy runtime.

Mobile foundation: contract-only/future-gated.

Command execution: unavailable/denied; not implemented.

Policy runtime: not implemented.

Custos enforcement: not implemented.

Runtime control: not implemented.

Sandbox control: not implemented.

P2.11-B: not implemented.

P2.12: not implemented.

Shell LIVE: not claimed.

Product readiness: not claimed.

Full suite: not run.

Coverage: not run.

## 20. Commit Hash

Implementation commit hash: pending at report creation; recorded in follow-up docs commit if needed.

## 21. Final Git Status

Pending at report creation.
