# P2.10-D — CLI/TUI Parity Binding / Terminal Client Read Model

**Date:** 2026-07-02  
**Pack:** P2.10-D  
**Scope:** P2.10-D only  
**Status:** DONE — CLI_TUI_PARITY_BINDING / TERMINAL_CLIENT_READ_MODEL / READ_ONLY_TERMINAL_INSPECTION / P2_10_E_NEXT / P2_10_E_NOT_DONE

## 1. Result Header

P2.10-D implements a Python-owned `TerminalShellClientContract`, `TerminalShellReadModel`, `TerminalShellParityMatrix`, terminal no-execution boundary, deterministic terminal JSON export, and read-only CLI commands under `python -m agentic_runtime.cli shell ...`.

The terminal client consumes P2.10-A `ShellClientState`, P2.10-B `WebShellReadModel`, and P2.10-C `DesktopShellReadModel`. Runnable CLI means read-only terminal inspection only. It is not command execution, tool execution, approval execution, runtime control, sandbox control, Shell LIVE, full terminal automation, full TUI product, or P2.10-E.

## 2. Scope

Covered:

- P2.10-C prerequisite gate
- terminal Shell client contract
- terminal read model
- CLI/TUI parity matrix
- terminal no-execution boundary
- read-only CLI commands
- deterministic terminal JSON export
- focused tests and regressions
- state/report/docs sync

Not covered:

- P2.10-E multi-client operator demo seal
- arbitrary command execution
- tool execution
- approval execution
- runtime start/stop
- sandbox control
- workflow execution
- agent dispatch
- memory writes
- policy mutation
- identity mutation
- Shell LIVE
- full CLI automation
- full TUI product

## 3. P2.10-C Prerequisite Gate

| Gate | Result |
|------|--------|
| P2.10-C report found | yes |
| P2.10-C report path | `agent/reports/P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md` |
| P2.10-C report indexed | yes — `agent/REPORTS.md` |
| P2.10-C proves desktop wrapper/read model DONE | yes |
| P2.10-C points next to P2.10-D | yes |
| P2.10-E started | no |
| Gate result | PASS |

## 4. Git / Worktree Preflight

| Check | Result |
|-------|--------|
| Branch | `master` |
| Initial status | clean |
| Unrelated dirty files | none |
| P2.10-E dirty/untracked files | none |
| Runtime/sandbox/identity/policy dirty/untracked files | none |
| CLI/TUI dirty/untracked files | none |
| `.venv/bin/python` | present |
| Preflight result | PASS |

## 5. Evidence Consumed

| Evidence | Path | Classification |
|----------|------|----------------|
| P2.10-C | `agent/reports/P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md` | prerequisite / desktop wrapper DONE / P2.10-D next |
| P2.10-C code | `src/agentic_runtime/aurel_shell/desktop_shell_contract.py` | desktop read model source |
| P2.10-B | `agent/reports/P2_10_B_LOCAL_WEB_SHELL_SKELETON.md` | web read model source |
| P2.10-B code | `src/agentic_runtime/aurel_shell/web_shell_read_model.py` | web Shell truth |
| P2.10-A | `agent/reports/P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md` | ShellClientState source of truth |
| P2.9-D | `agent/reports/P2_9_D_SHELL_EXIT_SEAL_FINAL_TAIL.md` | inherited P2.10 handoff |
| P2.VSLICE-A | `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md` | PREFLIGHT_ONLY |
| P2.REVIEW-A | `agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md` | vertical slice decision |
| tests | `tests/test_p210d_*.py` | focused validation |
| state/index | `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/REPORTS.md` | governance sync |

## 6. Terminal / CLI Tooling Decision

| Check | Result |
|-------|--------|
| Existing CLI structure found | yes — `src/agentic_runtime/cli.py` |
| Existing command module found | yes — `src/agentic_runtime/cli_modules/` |
| Existing `__main__` found | no package-level shell `__main__` needed |
| Existing console_scripts found | no extra console script required |
| Existing CLI tests found | yes — `tests/cli_helpers.py`, policy/path/identity CLI tests |
| Chosen path | Path A — extend existing argparse CLI with read-only `shell` namespace |
| Reason | Existing CLI has read-only projection command precedent; no separate terminal product needed |
| Runnable terminal path attempted | yes |
| Runnable terminal path claimed | yes — read-only Shell inspection only |
| Fallback used | no |

## 7. Terminal Shell Client Contract

Implemented in `src/agentic_runtime/aurel_shell/terminal_shell_client.py`:

- `TerminalShellClientKind`: CLI, TUI
- `TerminalShellRunMode`: CLI_READ_ONLY, CLI_CONTRACT_ONLY, TUI_READ_ONLY, TUI_CONTRACT_ONLY, TERMINAL_JSON_EXPORT, UNAVAILABLE, ERROR
- `TerminalShellCapability` and `TerminalShellCapabilityStatus`
- `TerminalShellClientContract`
- source refs to P2.10-A/B/C truth
- next pack pointer: P2.10-E

Read-only capabilities:

- VIEW_SHELL_STATUS
- VIEW_CLIENTS
- VIEW_SURFACES
- VIEW_TRUTH_LABELS
- VIEW_EVIDENCE_REFS
- VIEW_LOCAL_RUN_MODES
- VIEW_PARITY_MATRIX
- EXPORT_JSON

Disabled execution capabilities:

- EXECUTE_COMMAND
- APPROVE_ACTION
- RUN_TOOL
- START_RUNTIME
- STOP_RUNTIME
- DISPATCH_AGENT
- RUN_WORKFLOW
- WRITE_MEMORY
- MODIFY_POLICY
- MUTATE_IDENTITY
- TRIGGER_SANDBOX

## 8. Terminal Read Model

`TerminalShellReadModel` includes:

- terminal client status: READ_ONLY
- available clients: WEB, DESKTOP_TAURI, CLI, TUI, MOBILE_FOUNDATION
- seven canonical surfaces
- surface availability from P2.10-A CLI `ShellClientState`
- truth label summary with READ_ONLY / CONTRACT_ONLY / PREFLIGHT_ONLY / NOT_STARTED / UNAVAILABLE
- evidence refs from P2.10-A/B/C and P2.VSLICE-A
- local run modes: CLI_READ_ONLY, TUI_CONTRACT_ONLY, TERMINAL_JSON_EXPORT
- P2.VSLICE-A status: PREFLIGHT_ONLY
- JSON export available: true
- execution disabled: true
- next pack pointer: P2.10-E
- source hashes for CLI ShellClientState, WebShellReadModel, DesktopShellReadModel

## 9. CLI/TUI Parity Matrix

`TerminalShellParityMatrix` compares:

- WEB
- DESKTOP_TAURI
- CLI
- TUI
- MOBILE_FOUNDATION

Dimensions:

- SURFACE_LIST_VISIBLE
- SURFACE_AVAILABILITY_VISIBLE
- TRUTH_LABELS_VISIBLE
- EVIDENCE_REFS_VISIBLE
- LOCAL_RUN_MODES_VISIBLE
- COMMAND_PREFLIGHT_STATUS_VISIBLE
- NO_OVERCLAIM_BOUNDARIES_VISIBLE
- JSON_EXPORT_AVAILABLE
- EXECUTION_DISABLED

Missing parity is honest: TUI and mobile do not claim JSON export. CLI exposes JSON export. Every client exposes execution-disabled proof.

## 10. Terminal No-Execution Boundary

Machine-testable no-execution boundary is implemented through disabled capability entries and no-overclaim boundaries.

Disabled in P2.10-D:

- EXECUTE_COMMAND
- APPROVE_ACTION
- RUN_TOOL
- START_RUNTIME
- STOP_RUNTIME
- DISPATCH_AGENT
- RUN_WORKFLOW
- WRITE_MEMORY
- MODIFY_POLICY
- MUTATE_IDENTITY
- TRIGGER_SANDBOX

## 11. Read-Only CLI/TUI Commands Or Fallback

Implemented read-only CLI commands in `src/agentic_runtime/cli_modules/shell_commands.py`, wired through `src/agentic_runtime/cli.py`:

```bash
python -m agentic_runtime.cli shell status
python -m agentic_runtime.cli shell clients
python -m agentic_runtime.cli shell surfaces
python -m agentic_runtime.cli shell parity
python -m agentic_runtime.cli shell evidence
python -m agentic_runtime.cli shell run-modes
python -m agentic_runtime.cli shell export-json
```

Also available:

```bash
python -m agentic_runtime.cli shell read-model --json
```

Commands are read-only and render text/JSON from `TerminalShellReadModel`. They do not mutate state, execute tools, start runtime, trigger sandbox, write memory, mutate policy, or mutate identity.

TUI fallback: TUI is represented as contract-only parity. No interactive TUI product is claimed.

## 12. Terminal JSON Export

Implemented through `serialize_terminal_shell_read_model()` and CLI `shell export-json`.

Properties:

- JSON serializable
- deterministic canonical JSON
- stable key ordering
- truth labels preserved
- evidence refs preserved
- execution-disabled proof included through read model and parity matrix
- P2.10-A/B/C source hashes included
- P2.VSLICE-A preserved as PREFLIGHT_ONLY
- runtime-only objects excluded

## 13. Truth Label / Evidence Ref Preservation

Truth labels preserved:

- LIVE — not used / not claimed
- TRACE_VERIFIED — not claimed
- PREFLIGHT_ONLY — P2.VSLICE-A / command preflight status
- READ_ONLY — CLI terminal inspection
- CONTRACT_ONLY — TUI parity and inherited contracts
- DEV_FIXTURE — inherited web/desktop evidence only, not terminal LIVE
- UNAVAILABLE — unavailable/future surfaces such as full TUI product
- ERROR — available enum value only, not active result
- NOT_STARTED — P2.10-E and future clients

Evidence refs include P2.10-A/B/C reports/code and P2.VSLICE-A report. P2.VSLICE-A remains PREFLIGHT_ONLY.

## 14. Terminal Local Run Mode

| Run mode | Claim |
|----------|-------|
| CLI_READ_ONLY | real runnable CLI commands exist and were tested |
| CLI_CONTRACT_ONLY | enum retained; not the active CLI claim |
| TUI_READ_ONLY | not claimed |
| TUI_CONTRACT_ONLY | active TUI parity truth |
| TERMINAL_JSON_EXPORT | real deterministic CLI export exists and was tested |
| UNAVAILABLE | enum retained |
| ERROR | enum retained |

CLI runnable: yes, read-only inspection only.  
TUI runnable: no, contract-only parity.  
Command execution exposed: no.  
Shell LIVE claimed: no.  
Full terminal automation claimed: no.

## 15. Operator-Testable Terminal Path

| Command | Result |
|---------|--------|
| `python -m agentic_runtime.cli shell status --json` | PASS |
| `python -m agentic_runtime.cli shell clients --json` | PASS |
| `python -m agentic_runtime.cli shell surfaces --json` | PASS |
| `python -m agentic_runtime.cli shell parity --json` | PASS |
| `python -m agentic_runtime.cli shell evidence --json` | PASS via tests |
| `python -m agentic_runtime.cli shell run-modes --json` | PASS |
| `python -m agentic_runtime.cli shell export-json` | PASS / deterministic |

Claim level: read-only terminal inspection. No command execution.

## 16. What Is Sealed

- P2.10-D CLI/TUI parity binding / terminal client read model
- Terminal Shell client contract
- Terminal read model
- CLI/TUI parity matrix
- terminal no-execution boundary
- read-only CLI commands
- terminal JSON export
- truth label preservation
- evidence ref preservation
- P2.10-E handoff pointer

## 17. What Is Not Sealed

- P2.10-E
- arbitrary command execution
- tool execution
- approval execution
- runtime control
- sandbox control
- workflow execution
- agent dispatch
- memory write
- policy mutation
- identity mutation
- Shell LIVE
- full terminal automation
- full TUI product
- production API
- full API/event bridge live

## 18. Tests / Validation

| Command | Result |
|---------|--------|
| `.venv/bin/python -m compileall src tests` | PASS |
| `tests/test_p210d_terminal_shell_client.py` | 7 passed |
| `tests/test_p210d_cli_tui_parity_matrix.py` | 5 passed |
| `tests/test_p210d_terminal_no_execution.py` | 5 passed |
| `tests/test_p210d_cli_commands.py` | 6 passed |
| P2.10-C desktop wrapper regression | 20 passed |
| P2.10-B web shell regression | 18 passed |
| P2.10-A multi-client foundation regression | 23 passed |
| P2.9-D final seal regression | 15 passed |
| P2 command palette vertical slice tests | 10 passed |
| P2 command preflight tests | 6 passed |
| P2 vertical slice review tests | 9 passed |
| validation truth / drift gate regression | 18 passed |
| Golden Thread B regression | 17 passed |
| baseline mypy | PASS — 349 source files |
| ruff | PASS |
| git status after validation | in-scope files dirty/untracked before commit |

Validation not run: full pytest suite, coverage, Bandit, frontend/Tauri npm builds. Not required for P2.10-D terminal Python read-model scope and not claimed.

## 19. No-Scope-Expansion Proof

| Forbidden scope | Implemented/claimed |
|-----------------|---------------------|
| P2.10-E implemented | no |
| Arbitrary command execution implemented | no |
| Tool execution implemented | no |
| Approval execution implemented | no |
| Runtime start/stop implemented | no |
| Sandbox control implemented | no |
| Workflow execution implemented | no |
| Agent dispatch implemented | no |
| Memory write implemented | no |
| Policy mutation implemented | no |
| Identity mutation implemented | no |
| Command preflight behavior changed | no |
| P2.VSLICE-A behavior changed | no |
| Policy/identity/sandbox behavior changed | no |
| Shell LIVE claimed | no |
| Full terminal automation claimed | no |
| Full TUI product claimed | no |
| Runnable CLI/TUI claimed | CLI read-only only; no runnable TUI claim |

## 20. Files Created / Modified

Created:

- `src/agentic_runtime/aurel_shell/terminal_shell_client.py`
- `src/agentic_runtime/cli_modules/shell_commands.py`
- `tests/test_p210d_terminal_shell_client.py`
- `tests/test_p210d_cli_tui_parity_matrix.py`
- `tests/test_p210d_terminal_no_execution.py`
- `tests/test_p210d_cli_commands.py`
- `agent/reports/P2_10_D_CLI_TUI_PARITY_BINDING.md`

Modified:

- `src/agentic_runtime/cli.py`
- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/ARCHITECTURE.md`
- `agent/DECISIONS.md`
- `agent/TESTS.md`

## 21. Remaining Risks / Limitations

- Runnable CLI is read-only inspection only.
- Runnable TUI is not implemented; TUI remains contract-only parity.
- Command execution is unavailable and not exposed.
- Tool execution is unavailable and not exposed.
- Approval execution is unavailable and not exposed.
- Runtime control is unavailable and not exposed.
- Sandbox control is unavailable and not exposed.
- Workflow execution is unavailable and not exposed.
- Agent dispatch is unavailable and not exposed.
- Memory write is unavailable and not exposed.
- Policy mutation is unavailable and not exposed.
- Identity mutation is unavailable and not exposed.
- Shell LIVE is not claimed.
- Full terminal automation is not claimed.
- Full suite, coverage, Bandit, frontend/Tauri validation were not run.

## 22. Next Recommended Pack

**P2.10-E — Multi-Client Operator Demo Seal / Web-Desktop-CLI Evidence Bundle**

P2.10-E remains NOT_DONE.

## 23. Commit Hash

Pending until post-validation feature commit.

## 24. Final Git Status

Pending until post-validation commit.
