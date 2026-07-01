# P2.10-C — Tauri Desktop Local Shell / Desktop Wrapper Contract

**Date:** 2026-07-02  
**Pack:** P2.10-C  
**Scope:** P2.10-C only  
**Status:** DONE — TAURI_DESKTOP_WRAPPER_CONTRACT / DESKTOP_TAURI_DEV_RUNNABLE / P2_10_D_NEXT / P2_10_D_E_NOT_DONE

## 1. Result Header

P2.10-C implements a Python-owned `DesktopShellReadModel` and `DesktopShellCapabilityBoundary` derived from P2.10-A `ShellClientState` and P2.10-B `WebShellReadModel`, plus a minimal contract-bound Tauri desktop wrapper under `web/shell/src-tauri/` that loads the P2.10-B web skeleton with desktop wrapper status, capability boundaries, and no-overclaim panels. Runnable desktop wrapper is DEV_FIXTURE only — not Shell LIVE, not full desktop app, not command execution, not native authority.

## 2. Scope

Covered:

- P2.10-B prerequisite gate consumption
- Python `DesktopShellWrapperContract`, `DesktopShellCapabilityBoundary`, `DesktopShellReadModel`
- Deterministic JSON export `web/shell/public/desktop-shell-read-model.json`
- Minimal Tauri 2 wrapper (`web/shell/src-tauri/`)
- Desktop wrapper UI panel + wrapped web shell rendering
- Contract binding to P2.10-A/B truth
- Focused Python tests (20 tests across 3 files)
- Frontend typecheck, vitest contract binding, build, and `npm run tauri:build` validation

Not covered:

- P2.10-D CLI/TUI parity binding
- P2.10-E multi-client operator demo seal
- Command execution, approval actions, tool execution
- Native file/secrets/shell/runtime/sandbox authority bridges
- Production desktop app or Shell LIVE
- Mobile app or CLI/TUI parity

## 3. P2.10-B Prerequisite Gate

| Gate | Result |
|------|--------|
| P2.10-B report found | yes |
| P2.10-B report path | `agent/reports/P2_10_B_LOCAL_WEB_SHELL_SKELETON.md` |
| P2.10-B report indexed | yes — `agent/REPORTS.md` |
| P2.10-B proves local web shell/read model DONE | yes |
| P2.10-B points next to P2.10-C | yes |
| P2.10-D/E started | no |
| Gate result | PASS |

## 4. Git / Worktree Preflight

| Check | Result |
|-------|--------|
| Branch | `master` |
| Initial status | clean |
| Unrelated dirty files | none |
| P2.10-D/E dirty/untracked files | none |
| `.venv/bin/python` | present |
| Preflight result | PASS |

## 5. Evidence Consumed

| Evidence | Path | Classification |
|----------|------|----------------|
| P2.10-B | `agent/reports/P2_10_B_LOCAL_WEB_SHELL_SKELETON.md` | prerequisite / web shell DONE |
| P2.10-B code | `src/agentic_runtime/aurel_shell/web_shell_read_model.py` | wrapped web read model |
| P2.10-A | `src/agentic_runtime/aurel_shell/multi_client_foundation.py` | ShellClientState source of truth |
| P2.VSLICE-A | `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md` | PREFLIGHT_ONLY |

## 6. Desktop / Tauri Tooling Decision

| Check | Result |
|-------|--------|
| Frontend structure found | yes — `web/shell/` from P2.10-B |
| Desktop/Tauri structure found | created `web/shell/src-tauri/` |
| Package manager | npm |
| Existing package.json | yes — extended |
| Existing vite config | yes |
| Existing tsconfig | yes |
| Existing src-tauri | created |
| Existing tauri config | created |
| Existing Cargo.toml | created |
| Chosen path | **Path B** — minimal new Tauri wrapper around tested P2.10-B web shell |
| Reason | P2.10-B web skeleton is runnable; Tauri 2 scaffold is safe and testable |
| Runnable desktop wrapper attempted | yes |
| Runnable desktop wrapper claimed | yes — local desktop wrapper only (DEV_FIXTURE, not full app) |
| Fallback used | no |

## 7. Desktop Shell Contract

Implemented in `src/agentic_runtime/aurel_shell/desktop_shell_contract.py`:

- `DesktopShellWrapperContract` with `client_kind=DESKTOP_TAURI`, `wrapped_client_kind=WEB`
- Surfaces, truth labels, evidence refs inherited from P2.10-A DESKTOP_TAURI client state
- Wrapped web read model ref: `web/shell/public/web-shell-read-model.json`
- P2.VSLICE-A status: PREFLIGHT_ONLY
- Next pack pointer: P2.10-D

## 8. Desktop Capability Boundary

- Allowed minimal: LOAD_LOCAL_WEB_SHELL, DISPLAY_CONTRACT_STATE, DISPLAY_TRUTH_LABELS, DISPLAY_EVIDENCE_REFS, DISPLAY_LIMITATIONS
- Disabled: NATIVE_FILE_READ, NATIVE_FILE_WRITE, NATIVE_SECRET_ACCESS, NATIVE_SHELL_EXEC
- Future-gated: NATIVE_NETWORK_BRIDGE, NATIVE_APPROVAL_BRIDGE, NATIVE_RUNTIME_CONTROL, NATIVE_SANDBOX_CONTROL

## 9. Desktop Read Model / JSON Contract

- JSON serializable via `serialize_desktop_shell_read_model`
- Deterministic `read_model_hash`
- Fixture path: `web/shell/public/desktop-shell-read-model.json`
- Exported by `export_desktop_shell_read_model_fixture()`

## 10. Tauri Wrapper Implementation

| Check | Result |
|-------|--------|
| Path | `web/shell/src-tauri/` |
| Dev command | `npm run tauri:dev` (from `web/shell/`) |
| Build command | `npm run tauri:build` — PASS |
| Loads/wraps P2.10-B web shell | yes — same Vite app with desktop mode |
| Displays desktop wrapper status | yes — `DesktopWrapperPanel` |
| Native command bridge added | no |
| Native approval bridge added | no |
| Native runtime bridge added | no |
| Native sandbox bridge added | no |
| Native arbitrary file read/write added | no |
| Native secrets bridge added | no |

## 11. Contract Binding To P2.10-B Web Shell

- Desktop surfaces derive from P2.10-A DESKTOP_TAURI `ShellClientState`
- Wrapped web read model hash binds to live `WebShellReadModel`
- Truth labels and evidence refs preserved from inherited contracts
- Limitations come from desktop capability boundary
- P2.VSLICE-A remains PREFLIGHT_ONLY

## 12. Truth Label / Evidence Ref Preservation

- Desktop wrapper: DEV_FIXTURE when runnable, CONTRACT_ONLY baseline
- Web shell skeleton: inherited DEV_FIXTURE / CONTRACT_ONLY from P2.10-B
- P2.VSLICE-A: PREFLIGHT_ONLY
- Shell LIVE: not claimed
- Command execution: not exposed

## 13. Desktop Local Run Mode

- Active run mode when Tauri scaffold present: `DESKTOP_TAURI_DEV_RUNNABLE`
- Runnable desktop wrapper does not equal full desktop app, Shell LIVE, command execution, or native authority

## 14. Operator-Testable Desktop Path

| Command | Result |
|---------|--------|
| `npm install` (web/shell) | PASS |
| `npm run typecheck` | PASS |
| `npm test` | 11 passed |
| `npm run build` | PASS |
| `npm run tauri:build` | PASS |
| Claim level | local desktop wrapper runnable (DEV_FIXTURE) — not full desktop app |

## 15. What Is Sealed

- P2.10-C Tauri desktop local shell / desktop wrapper contract
- Python-owned `DesktopShellReadModel` and capability boundary
- Minimal Tauri wrapper around P2.10-B web skeleton
- P2.10-D handoff pointer

## 16. What Is Not Sealed

- P2.10-D CLI/TUI parity
- P2.10-E operator demo seal
- Shell LIVE, full local app, command execution
- Native file/secrets/shell/runtime/sandbox authority
- Production desktop app

## 17. Tests / Validation

| Command | Result |
|---------|--------|
| compileall | PASS |
| test_p210c_desktop_shell_contract | 10 passed |
| test_p210c_desktop_capability_boundary | 4 passed |
| test_p210c_tauri_wrapper_truth | 6 passed |
| P2.10-B web shell regression | 18 passed |
| P2.10-A multi-client foundation regression | 23 passed |
| P2.9-D seal regression | 15 passed |
| P2 command palette vertical slice | 25 passed |
| validation truth / drift gates | 18 passed |
| Golden Thread B | 17 passed |
| ruff | PASS |
| mypy (desktop_shell_contract, web_shell_read_model) | PASS |
| frontend typecheck | PASS |
| frontend vitest | 11 passed |
| frontend build | PASS |
| tauri build | PASS |
| Full suite / coverage | NOT RUN |

## 18. No-Scope-Expansion Proof

P2.10-D/E, mobile app, CLI/TUI parity, command execution, native authority bridges, Shell LIVE, and full desktop app were not implemented or claimed.

## 19. Files Created

- `src/agentic_runtime/aurel_shell/desktop_shell_contract.py`
- `tests/test_p210c_desktop_shell_contract.py`
- `tests/test_p210c_desktop_capability_boundary.py`
- `tests/test_p210c_tauri_wrapper_truth.py`
- `web/shell/src-tauri/` (Cargo.toml, tauri.conf.json, capabilities, main.rs, icons)
- `web/shell/public/desktop-shell-read-model.json`
- `web/shell/src/desktop-types.ts`
- `web/shell/src/DesktopApp.tsx`
- `web/shell/src/components/DesktopWrapperPanel.tsx`
- `web/shell/src/desktop-contract-binding.test.ts`
- `agent/reports/P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md`

## 20. Files Modified

- `src/agentic_runtime/aurel_shell/multi_client_foundation.py`
- `src/agentic_runtime/aurel_shell/web_shell_read_model.py`
- `tests/test_p210a_multi_client_foundation.py`
- `tests/test_p210b_web_shell_read_model.py`
- `tests/test_shell_client_run_modes.py`
- `web/shell/package.json`
- `web/shell/package-lock.json`
- `web/shell/public/web-shell-read-model.json`
- `web/shell/src/main.tsx`
- `web/shell/src/styles.css`
- `web/shell/src/contract-binding.test.ts`
- `.gitignore`
- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/TESTS.md`

## 21. Next Recommended Pack

**P2.10-D — CLI/TUI Parity Binding / Terminal Client Read Model**

P2.10-D/E remain NOT_DONE. No Shell LIVE or command execution claim.

## 22. Commit Hash

`f57fcc6`

## 23. Final Git Status

Clean after commit on `master` (expected).
