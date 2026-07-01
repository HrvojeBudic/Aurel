# P1.ENF-B Entrypoint Bypass Guard Expansion / Repo Agent Enforcement Audit

**Date:** 2026-07-01  
**Pack:** P1.ENF-B  
**Status:** DONE

## 1. Result Header

P1.ENF-B expands the P1.ENF-A entrypoint classifier seed into a repo-backed
entrypoint governance audit with deterministic discovery records, expanded
classifications, repo_agent enforcement matrix, CLI/shell path audit, AurelShell
contract-only confirmation, unknown-risk blocking, and no-scope-expansion proof.

P1.ENF-A and P1.ENF-A-OMNI-R1 remain DONE. P2.9-B remains NOT DONE. P1.ENF-C
remains next planned Golden Thread pack. No Shell command router, product UI, P2
vertical slice, or repo_agent rewrite was performed.

## 2. Scope

- Entrypoint discovery map with evidence refs
- Expanded `EntrypointGovernanceClassification` enum
- `entrypoint_governance_audit.py` audit objects
- repo_agent path classification from code evidence
- CLI/status/shell/exit path classification
- AurelShell non-executing confirmation
- Unknown execution risk blocking
- Focused tests and agent state/report sync

Not in scope: P1.ENF-C–F, P2.9-B+, Shell command router, product UI, repo_agent
rewrite, identity CLI refactor, sandbox hardening, runtime.submit rewrite.

## 3. Git / Worktree Preflight

- Branch: `master`
- Initial status: clean
- Unrelated dirty files: none
- P2.9-B dirty/untracked files: none
- P1.ENF-C/D/E/F dirty/untracked files: none
- `.venv/bin/python`: present
- Preflight result: **PASS**

## 4. P1.ENF-A / P1.ENF-A-OMNI-R1 Evidence Gate

### P1.ENF-A

- Report found: yes
- Report path: `agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md`
- Indexed: yes (`agent/REPORTS.md`)
- Validation evidence: recorded in P1.ENF-A report and `agent/TESTS.md`
- Commit evidence: `07c65b5ee46aad0f478e99576a793d9d65a6eae1`
- Final/current git clean: yes (clean before P1.ENF-B edits)
- Gate result: **PASS**

### P1.ENF-A-OMNI-R1

- Report found: yes
- Report path: `agent/reports/P1_ENF_A_OMNI_R1_VALIDATION_TRUTH_CORE_INTEGRITY_REPAIR.md`
- Indexed: yes (`agent/REPORTS.md`)
- Validation evidence: recorded in repair report and `agent/TESTS.md`
- Commit evidence: `8bf05de796e0c066c396005c993b82e0b90b5a69` (repair), `fa7429200946838165fd629b9461744ca6aa7f6b` (docs hash record)
- Final/current git clean: yes
- P2.9-B remains NOT DONE: yes
- Gate result: **PASS**

## 5. Entrypoint Discovery Method

Search commands run:

```bash
rg -n "subprocess|os\.system|exec\(|eval\(|runtime\.submit|ToolBus|Sandbox" src tests agent
rg -n "argparse|def main|if __name__|sys\.exit" src tests agent
rg -n "SideEffectProof|no command execution|UNAVAILABLE" src/agentic_runtime/aurel_shell tests/aurel_shell
rg -n "repo_agent|patch|submit|sandbox|trace|write" src/agentic_runtime/repo_agent.py tests
```

Files/directories inspected:

- `src/agentic_runtime/entrypoint_governance_guard.py`
- `src/agentic_runtime/entrypoint_governance_audit.py` (new)
- `src/agentic_runtime/runtime.py`
- `src/agentic_runtime/repo_agent.py`
- `src/agentic_runtime/tools.py`
- `src/agentic_runtime/sandbox.py`
- `src/agentic_runtime/cli.py`
- `src/agentic_runtime/cli_modules/`
- `src/agentic_runtime/aurel_shell/`
- `tests/`, `tests/aurel_shell/`

Discovery records created: 19 seed records in `_SEED_DISCOVERY`

Search limitations: static seed map; not exhaustive dynamic call-graph analysis

Findings not verified: forced-exit supervisor atomic-write claims (NOT VERIFIED)

Findings deferred: full dynamic call-graph, identity CLI per-command audit depth

## 6. Runtime Submit Classification

- runtime.submit located: yes
- runtime.submit file: `src/agentic_runtime/runtime.py`
- runtime.submit symbol: `AgenticRuntime.submit`
- classification: `GOVERNED_RUNTIME_SUBMIT`
- evidence: policy.evaluate → approval → sandbox → verify → trace → memory path at `runtime.py:147+`
- truth label: `NO_BYPASS_EVIDENCE`

## 7. repo_agent Enforcement Audit

- repo_agent files inspected: `src/agentic_runtime/repo_agent.py`
- direct file mutation paths: none — `PatchExecutor.apply` delegates via `runtime.submit` (`repo_agent.py:647`)
- patch/apply paths: `PatchExecutor.apply` → `write_file`/`patch_file` tools via submit
- tool/sandbox paths: `RepositoryAgentLoop.run` creates profiled sandbox (`repo_agent.py:777`)
- runtime.submit usage: confirmed in `PatchExecutor.apply` and `TestRunnerAdapter.run`
- approval/HITL evidence: `_approval_gate_for`, approval summaries in patch results
- policy evidence: indirect via runtime.submit policy gate
- trace/evidence behavior: `_finalize_report` reads trace replay, praxis metabolism
- memory behavior: praxis metabolism via `_process_praxis`
- test/dev fixture paths: test helpers in `tests/` only
- classification:
  - `PatchExecutor.apply` → `GOVERNED_DELEGATION_CONFIRMED`
  - `TestRunnerAdapter.run` → `GOVERNED_DELEGATION_CONFIRMED`
  - `RepositoryAgentLoop.run` → `GOVERNED_DELEGATION_REQUIRED`
  - `RepoContextBuilder.build` → `NON_EXECUTING_READ_MODEL_ONLY`
- risks: orchestration path complexity; not every repo_agent symbol individually proven
- follow-ups: deeper per-symbol call-graph audit in P1.ENF-F drift gates

## 8. CLI / Shell / Exit Path Audit

- CLI files inspected: `cli.py`, `cli_modules/`
- status/read-only commands: `cmd_status` → read model only
- execution-like commands: `cmd_repo_task`, `cmd_approve_demo`, `cmd_verify`
- shell/run-command paths: sandbox via repo_task; verify uses direct subprocess
- runtime.submit-routed commands: `cmd_approve_demo`, `cmd_repo_task` (via repo_agent)
- exit/shutdown/interrupt paths: standard argparse/main return codes; no forced-exit bypass audit
- speculative forced-exit claims: **NOT VERIFIED**
- classification:
  - `cmd_status` → `NON_EXECUTING_READ_MODEL_ONLY`
  - `cmd_verify` → `BLOCKED_UNKNOWN_EXECUTION_RISK` (subprocess bypass)
  - `cmd_repo_task` → `GOVERNED_DELEGATION_REQUIRED`
  - identity CLI modules → `BLOCKED_IDENTITY_BYPASS_RISK`
  - policy CLI modules → `BLOCKED_POLICY_BYPASS_RISK`
- risks: `cmd_verify` dev validation subprocess bypasses runtime.submit
- follow-ups: route verify through governed path or mark dev-only fixture explicitly

## 9. AurelShell Contract-Only Confirmation

- AurelShell modules scanned/sampled: `contracts.py`, `shell_exit_seal_foundation.py`, `cli_binding.py`
- side-effect proof evidence: `AurelShellSideEffectProof` all false; P29ASideEffectProof all false
- runtime dispatch found: no
- command execution found: no
- permission enforcement found: no
- trace/memory/storage writes found: no
- product UI created: no
- classification: `NON_EXECUTING_CONTRACT_ONLY` / `UNAVAILABLE` (cli_binding)
- truth label: `CONTRACT_ONLY`

## 10. Unknown Execution Risk Findings

- unknown execution-like paths: `external.plugin.execute_command`, `cmd_verify` subprocess
- blocked unknown risks: external plugins, cmd_verify
- policy bypass risks: `cli_modules.policy_commands`
- identity bypass risks: `cli_modules.identity_commands`
- unavailable paths: AurelShell `cli_binding` product runner
- delegation-required paths: repo_agent loop, ToolRuntime.dispatch, sandbox backends
- safe paths without evidence: none claimed
- classification rule obeyed: yes — unknown marked blocked/delegation-required/unavailable

## 11. Classification Matrix

| Classification | Examples |
|----------------|----------|
| GOVERNED_RUNTIME_SUBMIT | `AgenticRuntime.submit` |
| GOVERNED_DELEGATION_CONFIRMED | `PatchExecutor.apply`, `TestRunnerAdapter.run` |
| GOVERNED_DELEGATION_REQUIRED | `RepositoryAgentLoop.run`, `ToolRuntime.dispatch`, `cmd_repo_task`, `UnsafeLocalSandbox.run_shell` |
| NON_EXECUTING_CONTRACT_ONLY | AurelShell modules |
| NON_EXECUTING_READ_MODEL_ONLY | `cmd_status`, `RepoContextBuilder.build` |
| TEST_ONLY_EXECUTION_FIXTURE | `tests.*` prefix |
| DEV_FIXTURE_ONLY | `demo_harness` |
| BLOCKED_UNKNOWN_EXECUTION_RISK | `external.plugin.execute_command`, `cmd_verify` |
| BLOCKED_POLICY_BYPASS_RISK | `cli_modules.policy_commands` |
| BLOCKED_IDENTITY_BYPASS_RISK | `cli_modules.identity_commands` |
| UNAVAILABLE | AurelShell `cli_binding` product runner |

## 12. Guard / Audit Objects Added

- `EntrypointGovernanceAudit`: assembles discovery map and result
- `EntrypointDiscoveryRecord`: path, symbol, surface, kind, side-effect vectors, classification, evidence
- `SideEffectVector`: boolean side-effect flags
- `P1ENFBResult`: audit rollup with counts
- `P1ENFBSideEffectProof`: no-scope-expansion proof
- Evidence refs: file:line citations in seed records
- Files: `entrypoint_governance_audit.py`, extended `entrypoint_governance_guard.py`

## 13. Tests Added / Updated

- `tests/test_entrypoint_governance_audit.py` — 10 tests
- `tests/test_repo_agent_entrypoint_audit.py` — 6 tests
- `tests/test_entrypoint_governance_guard.py` — updated repo_agent assertion for expanded classification

## 14. Validation Run

| Command | Result |
|---------|--------|
| compileall | **PASS** |
| entrypoint governance audit tests | **10 passed** |
| repo_agent entrypoint audit tests | **6 passed** |
| entrypoint governance guard regression | **6 passed** |
| P1.ENF-A regression tests | **18 passed** |
| P1.ENF-A-OMNI-R1 repair tests | **7 passed** |
| baseline mypy | **PASS** (329 files) |
| core strict mypy probe | **PASS** (5 files) |
| ruff | **PASS** |
| optional aurel_shell tests | NOT RUN |
| optional selector | NOT RUN |
| bandit | NOT RUN |
| git status after validation | clean (pre-commit) |

## 15. No-Scope-Expansion Proof

All `P1ENFBSideEffectProof` booleans false:

- P1.ENF-C implemented: no
- P1.ENF-D implemented: no
- P1.ENF-E implemented: no
- P1.ENF-F implemented: no
- P2.9-B implemented: no
- Shell command router created: no
- Product UI created: no
- repo_agent rewritten: no
- identity CLI refactored: no
- sandbox backend hardened: no
- runtime.submit rewritten: no
- trace/memory rewritten: no

## 16. Files Created / Modified

Created:

- `src/agentic_runtime/entrypoint_governance_audit.py`
- `tests/test_entrypoint_governance_audit.py`
- `tests/test_repo_agent_entrypoint_audit.py`
- `agent/reports/P1_ENF_B_ENTRYPOINT_BYPASS_GUARD_REPO_AGENT_ENFORCEMENT_AUDIT.md`

Modified:

- `src/agentic_runtime/entrypoint_governance_guard.py`
- `src/agentic_runtime/__init__.py`
- `tests/test_entrypoint_governance_guard.py`
- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/TESTS.md`

## 17. What Was Deliberately Not Implemented

- P1.ENF-C Golden Thread B
- P1.ENF-D identity kernel / CLI work
- P1.ENF-E sandbox hardening
- P1.ENF-F drift gates
- P2.9-B rerun
- P2 true vertical slice
- Shell command router
- product UI
- repo_agent broad rewrite
- identity CLI refactor
- sandbox backend hardening
- ROADMAP archive cleanup

## 18. Remaining Risks / Limitations

- Golden Thread: stale sections remain follow-up
- ROADMAP drift: historical drift not repaired
- UnsafeLocalSandbox: remains unsafe demo backend
- Stub modules: contract-only stubs remain
- P2 contract-only lattice: unchanged
- repo_agent remaining risks: not every symbol individually proven governed
- CLI remaining risks: `cmd_verify` subprocess bypass; identity/policy CLI not submit-governed
- Unknown execution risks: static seed map not exhaustive call-graph
- Other: forced-exit atomic-write claims NOT VERIFIED

## 19. Next Recommended Step

**P1.ENF-F-A — Tooling / Determinism / Shadow-Still-Active Drift Gates**

Alternative operator path: **P2.9-B** Shell Exit Seal Readiness rerun.

## 20. Commit Hash

`47ea1286ad2ee681c34c4c5a4b35b5e308f1263a`

## 21. Final Git Status

Clean — `git status --short` empty after commit.
