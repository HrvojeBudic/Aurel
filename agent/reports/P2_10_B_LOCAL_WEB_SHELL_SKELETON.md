# P2.10-B — Local Web Shell Skeleton / Contract-Bound Client Read Model

**Date:** 2026-07-01  
**Pack:** P2.10-B  
**Scope:** P2.10-B only  
**Status:** DONE — LOCAL_WEB_SHELL_SKELETON / CONTRACT_BOUND_READ_MODEL / P2_10_C_NEXT / P2_10_C_D_E_NOT_DONE

## 1. Result Header

P2.10-B implements a Python-owned `WebShellReadModel` derived from P2.10-A `ShellClientState` and a minimal contract-bound local web Shell skeleton under `web/shell/` that renders surfaces, truth labels, evidence refs, run modes, and no-overclaim boundaries without claiming Shell LIVE, full local app, desktop/mobile readiness, or command execution.

## 2. Scope

Covered:

- P2.10-A prerequisite gate consumption
- Python `WebShellReadModel` and deterministic JSON export
- Static fixture `web/shell/public/web-shell-read-model.json`
- Minimal Vite/React/TypeScript web skeleton (`web/shell/`)
- Contract binding (surfaces, truth labels, evidence refs, limitations from P2.10-A)
- Focused Python tests (18 tests across 2 files)
- Frontend typecheck, vitest contract binding, and production build validation

Not covered:

- P2.10-C Tauri desktop shell
- P2.10-D CLI/TUI parity binding
- P2.10-E multi-client operator demo seal
- Command execution, approval actions, tool execution
- Production API server or full API/event bridge live path
- Full Aurel product UI or design system

## 3. P2.10-A Prerequisite Gate

| Gate | Result |
|------|--------|
| P2.10-A report found | yes |
| P2.10-A report path | `agent/reports/P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md` |
| P2.10-A report indexed | yes — `agent/REPORTS.md` |
| P2.10-A proves multi-client foundation DONE | yes |
| P2.10-A points next to P2.10-B | yes |
| P2.10-C/D/E started | no |
| Gate result | PASS |

## 4. Git / Worktree Preflight

| Check | Result |
|-------|--------|
| Branch | `master` |
| Initial status | clean |
| Unrelated dirty files | none |
| P2.10-C/D/E dirty/untracked files | none |
| `.venv/bin/python` | present |
| Preflight result | PASS |

## 5. Evidence Consumed

| Evidence | Path | Classification |
|----------|------|----------------|
| P2.10-A | `agent/reports/P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md` | prerequisite / multi-client foundation DONE |
| P2.10-A code | `src/agentic_runtime/aurel_shell/multi_client_foundation.py` | ShellClientState source of truth |
| P2.VSLICE-A | `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md` | PREFLIGHT_ONLY |
| P2.9-D | `agent/reports/P2_9_D_SHELL_EXIT_SEAL_FINAL_TAIL.md` | inherited via P2.10-A |

## 6. Frontend / Web Tooling Decision

| Check | Result |
|-------|--------|
| Frontend structure found | no prior frontend |
| Package manager | npm |
| Existing package.json | none (created `web/shell/package.json`) |
| Existing vite config | none (created) |
| Existing tsconfig | none (created) |
| Chosen path | **Path B** — minimal new Vite/React/TypeScript skeleton |
| Reason | No existing frontend; Python JSON fixture + minimal skeleton is safe and testable |
| Runnable web skeleton attempted | yes |
| Runnable web skeleton claimed | yes — local web skeleton only (not full app, not Shell LIVE) |
| Fallback used | no |

## 7. Web Shell Read Model

Implemented in `src/agentic_runtime/aurel_shell/web_shell_read_model.py`:

- `WebShellReadModel` derives from `build_shell_client_state(ShellClientKind.WEB)`
- Current client = WEB
- Seven canonical surfaces with selector/right-topbar mapping
- Truth labels: DEV_FIXTURE (skeleton), CONTRACT_ONLY, PREFLIGHT_ONLY, NOT_STARTED
- Evidence refs preserved from P2.10-A plus fixture ref
- Command palette availability: PREFLIGHT_ONLY
- P2.VSLICE-A status: PREFLIGHT_ONLY
- Local run mode: WEB_DEV_SHELL_CONTRACT
- Launch command: `npm run dev` (validated)
- Next pack pointer: P2.10-C

## 8. Deterministic JSON / TypeScript-Safe Contract

- JSON serializable via `to_canonical_json`
- Deterministic `read_model_hash`
- Enum values serialized as strings
- Fixture path: `web/shell/public/web-shell-read-model.json`
- Exported by `export_web_shell_read_model_fixture()`

## 9. Local Web Skeleton

| Check | Result |
|-------|--------|
| Path | `web/shell/` |
| Run command | `npm run dev` (from `web/shell/`) |
| Build command | `npm run build` — PASS |
| Test command | `npm test` — 6 passed |
| Typecheck | `npm run typecheck` — PASS |
| Renders global topbar | yes |
| Renders surface selector | yes (Aurel CRO / HQ / CORP / HUB / IDE) |
| Renders SYSTEM/Settings right-side | yes |
| Renders active surface placeholder | yes |
| Renders truth label badges | yes |
| Renders evidence refs | yes |
| Renders client status | yes |
| Renders local run mode | yes |
| Renders no-overclaim boundaries | yes |
| Execute/approval/runtime buttons | no |

## 10. Contract Binding

- Surfaces come from P2.10-A `ShellClientState` — proven by Python and vitest binding tests
- Truth labels come from contract — no TypeScript-invented availability
- Frontend loads Python-generated JSON only — no hardcoded surface truth

## 11. What Is Sealed

- P2.10-B local web Shell skeleton / contract-bound read model
- Python-owned `WebShellReadModel`
- Deterministic JSON fixture export
- Minimal runnable local web skeleton (DEV_FIXTURE, not Shell LIVE)
- P2.10-C handoff pointer

## 12. What Is Not Sealed

- P2.10-C Tauri desktop shell
- P2.10-D CLI/TUI parity
- P2.10-E operator demo seal
- Shell LIVE, full local app, command execution
- Production API, full API/event bridge live

## 13. Tests / Validation

| Command | Result |
|---------|--------|
| compileall | PASS |
| test_p210b_web_shell_read_model | 11 passed |
| test_p210b_web_shell_contract_binding | 7 passed |
| P2.10-A regression | 22 passed |
| P2.9-D seal regression | 15 passed |
| P2 command palette vertical slice | 25 passed |
| validation truth / drift gates | 18 passed |
| Golden Thread B | 17 passed |
| ruff | PASS |
| mypy (web_shell_read_model) | PASS |
| frontend typecheck | PASS |
| frontend vitest | 6 passed |
| frontend build | PASS |
| Full suite / coverage | NOT RUN |

## 14. No-Scope-Expansion Proof

P2.10-C/D/E, Tauri, mobile, CLI/TUI parity, command execution, production API, Shell LIVE, and full local app were not implemented or claimed.

## 15. Files Created

- `src/agentic_runtime/aurel_shell/web_shell_read_model.py`
- `tests/test_p210b_web_shell_read_model.py`
- `tests/test_p210b_web_shell_contract_binding.py`
- `web/shell/` (package.json, vite, tsconfig, src components, README)
- `web/shell/public/web-shell-read-model.json`
- `web/shell/package-lock.json`
- `agent/reports/P2_10_B_LOCAL_WEB_SHELL_SKELETON.md`

## 16. Files Modified

- `.gitignore` (node_modules/)
- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/TESTS.md`

## 17. Next Recommended Pack

**P2.10-C — Tauri Desktop Local Shell / Desktop Wrapper Contract**

P2.10-C/D/E remain NOT_DONE. No Shell LIVE or command execution claim.

## 18. Commit Hash

_(filled after commit)_

## 19. Final Git Status

_(filled after commit)_
