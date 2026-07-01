# P2.11-B — Surface Permission Projection / Matrix Read Model

## 1. Result Header

**Status:** DONE — Surface Permission Projection / Matrix Read Model.

P2.11-B projects the P2.11-A permission matrix into deterministic client, surface, action, evidence, sensitive-surface, and no-overclaim read-model views. P2.11 as a whole is not complete. P2.11-C is next. P2.12+ remains not started. Projection is not enforcement. Read model is not execution. No command execution, tool execution, approval execution, runtime control, sandbox control, memory write, policy mutation, identity mutation, full policy runtime, Custos enforcement, Shell LIVE, product readiness, final P2 seal, or P3 handoff is implemented or claimed.

## 2. Scope

Covered: P2.11-B only.

Implemented:

- `SurfacePermissionProjectionKind`
- `SurfacePermissionProjectionEntry`
- `SurfacePermissionClientView`
- `SurfacePermissionSurfaceView`
- `SurfacePermissionActionView`
- `SurfacePermissionEvidenceView`
- `SurfacePermissionNoOverclaimView`
- `SurfacePermissionReadModel`
- `SurfacePermissionProjectionSummary`
- `P211BHandoff`
- `P211BResult`
- `build_surface_permission_read_model()`
- `serialize_surface_permission_read_model()`
- `project_permissions_by_client()`
- `project_permissions_by_surface()`
- `project_permissions_by_action()`

Not implemented: P2.11-C, P2.12+, command/tool/approval execution, runtime/sandbox control, workflow execution, agent dispatch, memory writes, policy mutation, identity mutation, permission enforcement, full policy runtime, Custos enforcement, Shell LIVE, product readiness, final P2 seal, or P3 handoff.

## 3. P2.11-A Prerequisite Gate

P2.11-A report found: yes.

P2.11-A report path: `agent/reports/P2_11_A_SURFACE_PERMISSION_MATRIX_FOUNDATION.md`.

P2.11-A report indexed: yes.

P2.11-A proves permission matrix foundation DONE: yes.

P2.11-A points to P2.11-B: yes.

P2.12+ started: no.

Gate result: passed.

## 4. Git / Worktree Preflight

Branch: `master`.

Initial status: clean.

Unrelated dirty files: none.

P2.12+ dirty/untracked files: none.

Runtime/sandbox/identity/policy dirty/untracked files: none.

Client/frontend/desktop/CLI/TUI dirty/untracked files: none.

Preflight result: passed.

## 5. Evidence Consumed

- P2.11-A: `agent/reports/P2_11_A_SURFACE_PERMISSION_MATRIX_FOUNDATION.md`, `surface_permission_matrix.py`, P2.11-A focused tests.
- P2.10-E through P2.10-A and P2.VSLICE-A: consumed by reference through P2.11-A matrix evidence refs.
- Agent canon: `agent/ACTIVE_TASK.md`, `agent/ROADMAP.md`, `agent/STATE.md`, `agent/TESTS.md`, `agent/REPORTS.md`.

## 6. Source Permission Matrix Summary

Clients: `WEB`, `DESKTOP_TAURI`, `CLI`, `TUI`, `MOBILE_FOUNDATION`.

Surfaces: `Aurel CRO`, `HQ`, `CORP`, `HUB`, `IDE`, `SYSTEM`, `Settings`.

Actions: 9 safe pre-execution + 11 disabled execution actions.

Permission levels: `ALLOWED`, `READ_ONLY`, `PREFLIGHT_ONLY`, `CONTRACT_ONLY`, `FUTURE_GATED`, `UNAVAILABLE`, `DENIED`, `ERROR`.

Matrix entries: 700.

Matrix summary counts preserved from P2.11-A (`ALLOWED` 56, `READ_ONLY` 98, `PREFLIGHT_ONLY` 21, `CONTRACT_ONLY` 105, `FUTURE_GATED` 21, `UNAVAILABLE` 14, `DENIED` 385, `ERROR` 0).

Sensitive surfaces: `SYSTEM`, `Settings`, `IDE`.

Evidence refs: P2.10-A/B/C/D/E and P2.VSLICE-A refs preserved through projection.

NO_EVIDENCE markers: representable; no silent upgrade in projection.

No-overclaim boundaries: all P2.11-A boundaries preserved in read model and no-overclaim view.

## 7. Projection / Read Model Shape

Primary module: `src/agentic_runtime/aurel_shell/surface_permission_projection.py`.

Read model includes:

- source matrix ref
- source pack refs
- clients, surfaces, safe/disabled actions
- 700 projection entries
- 5 client views
- 7 surface views
- 20 action views
- 3 sensitive surface views
- level summaries (preflight/denied/unavailable/future-gated/contract-only)
- evidence refs, limitations, no-overclaim boundaries
- next pack pointer `P2.11-C`

## 8. Client Permission Views

All five P2.10 clients projected with preserved run modes:

- WEB — `WEB_DEV_RUNNABLE`
- DESKTOP_TAURI — `DESKTOP_TAURI_DEV_RUNNABLE`
- CLI — `CLI_READ_ONLY`
- TUI — `TUI_CONTRACT_ONLY`
- MOBILE_FOUNDATION — `MOBILE_CONTRACT_ONLY`

WEB/DESKTOP retain broad visibility/open/read/preflight projection where P2.11-A allows. CLI retains read/export inspection without visual open. TUI and mobile remain contract-only/future-gated. Sensitive-surface limitations preserved.

## 9. Surface Permission Views

All seven Shell surfaces projected with client visibility/open/read/preflight/contract/future-gated/unavailable/denied sets. Sensitive flags set for `SYSTEM`, `Settings`, and `IDE`.

## 10. Action Permission Views

All 20 actions projected. Safe actions preserve allowed/read-only/preflight/contract/future-gated/unavailable splits. Disabled execution actions remain denied everywhere with no allowed/preflight/read-only upgrade.

## 11. Sensitive Surface Projection

Dedicated sensitive surface views for `SYSTEM`, `Settings`, and `IDE`. Mutation, runtime control, sandbox control, policy mutation, identity mutation, and execution remain not implemented. `PREFLIGHT_ONLY` remains non-execution.

## 12. Evidence Ref Projection

Evidence views built per P2.11-A evidence ref with supported entry keys. `NO_EVIDENCE` is not upgraded to stronger authority.

## 13. No-Execution / No-Overclaim Projection

No-overclaim view preserves all P2.11-A boundaries with zero violations. Projection/read model explicitly states:

- projection is not enforcement
- read model is not execution
- `PREFLIGHT_ONLY` is not command execution
- `ALLOWED` is not final authorization

## 14. JSON / Serialization Status

Serialization implemented: yes.

Command: `serialize_surface_permission_read_model()`.

JSON-safe, deterministic, truth-preserving, non-executable.

## 15. What Is Sealed

- P2.11-B permission projection / matrix read model.
- Projection object family.
- Client/surface/action/evidence/no-overclaim views.
- Deterministic JSON export.
- P2.11-C handoff pointer.

## 16. What Is Not Sealed

- P2.11-C.
- P2.11 as a whole.
- P2.12+.
- P2 final seal.
- P3 handoff.
- Command/tool/approval execution.
- Runtime/sandbox control.
- Memory write.
- Policy/identity mutation.
- Permission enforcement.
- Full policy runtime.
- Custos enforcement.
- Shell LIVE.
- Product readiness.

## 17. Tests / Validation

Validation run:

- `.venv/bin/python -m compileall src tests` — PASS
- `.venv/bin/python -m pytest tests/test_p211b_surface_permission_projection.py -q` — PASS, 6 passed
- `.venv/bin/python -m pytest tests/test_p211b_matrix_read_model.py -q` — PASS, 7 passed
- `.venv/bin/python -m pytest tests/test_p211b_permission_projection_no_execution.py -q` — PASS, 7 passed
- `.venv/bin/python -m pytest tests/test_p211b_p211c_handoff.py -q` — PASS, 3 passed
- P2.11-A regression — PASS, 15 passed
- P2.10-E/D/C/B/A regression — PASS, 90 passed
- P2 command preflight regression — PASS, 6 passed
- validation truth / drift gate regression — PASS, 18 passed
- Golden Thread B regression — PASS, 17 passed
- `.venv/bin/python -m mypy src/agentic_runtime` — PASS
- `.venv/bin/python -m ruff check src tests` — PASS

Validation not run: full pytest suite, coverage, Bandit.

## 18. No-Scope-Expansion Proof

P2.11-C implemented: no.

P2.11 claimed complete: no.

P2.12+ implemented: no.

P2 final seal claimed: no.

P3 handoff claimed: no.

Command/tool/approval execution implemented: no.

Runtime/sandbox control implemented: no.

Memory write implemented: no.

Policy/identity mutation implemented: no.

Permission enforcement implemented: no.

Full policy runtime implemented: no.

Custos enforcement implemented: no.

P2.VSLICE-A behavior changed: no.

PREFLIGHT_ONLY upgraded to execution: no.

ALLOWED upgraded to final authorization: no.

Shell LIVE claimed: no.

Product readiness claimed: no.

## 19. P2.11-C Handoff

Next pack: P2.11-C.

Next title: Surface Permission Operator Inspection / CLI-Shell View Binding.

Handoff status: pointer only; P2.11-C not implemented.

Operator view needs: CLI/TUI permission inspection, filter/group read model, sensitive-surface/no-execution display.

CLI/Shell binding needs: bind read model to read-only `python -m agentic_runtime.cli shell` inspect path with stable JSON export.

## 20. Files Created / Modified

Created:

- `src/agentic_runtime/aurel_shell/surface_permission_projection.py`
- `tests/test_p211b_surface_permission_projection.py`
- `tests/test_p211b_matrix_read_model.py`
- `tests/test_p211b_permission_projection_no_execution.py`
- `tests/test_p211b_p211c_handoff.py`
- `agent/reports/P2_11_B_SURFACE_PERMISSION_PROJECTION_READ_MODEL.md`

Modified:

- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/ARCHITECTURE.md`
- `agent/TESTS.md`

## 21. Remaining Risks / Limitations

- Projection/read model is inspection only; misuse could be mistaken for enforcement without P2.11-C operator binding discipline.
- P2.11-C CLI/TUI binding not implemented.
- P2.12 truth-label fixture discipline not implemented.
- Mobile remains contract-only/future-gated.
- Full suite/coverage not run in this pack.

## 22. Commit Hash

`bdb2e930cc404be21dcb5779c48a9837865672d7`

## 23. Final Git Status

Clean after commit.
