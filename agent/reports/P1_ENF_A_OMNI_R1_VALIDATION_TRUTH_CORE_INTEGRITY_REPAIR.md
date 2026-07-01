# P1.ENF-A-OMNI-R1 Validation Truth / Fixture Determinism / Core Integrity Repair

**Date:** 2026-07-01  
**Pack:** P1.ENF-A-OMNI-R1  
**Status:** DONE

## 1. Result Header

P1.ENF-A-OMNI-R1 repairs three concrete validation-truth gaps after P1.ENF-A:
tracked consent fixtures no longer mutate during CLI tests, baseline mypy is
distinguished from a scoped core strict probe, and trace Merkle roots recompute
from live payload fields so tampering changes the root.

P1.ENF-A remains DONE. P2.9-B remains NOT DONE. P1.ENF-B is the next planned
enforcement pack. No LIVE, TRACE_VERIFIED, full-suite, coverage, or global type
safety is claimed.

## 2. Repair Scope

- Consent fixture determinism (F-TEST-01)
- Core tooling truth / strict probe (F-TOOL-01)
- Trace Merkle live-payload semantics (F-CORE-01)
- Focused tests and agent report/state sync

Not in scope: P1.ENF-B–F, P2.9-B+, identity CLI refactor, sandbox hardening,
ROADMAP rewrite, global mypy strictness, consent runtime semantics change, trace
ledger architecture rewrite.

## 3. Git / Worktree Preflight

- Branch: `master`
- Initial status: clean
- Unrelated dirty files: none
- Consent fixture dirty files: none
- P2.9-B dirty/untracked files: none
- P1.ENF-B/C/D/E/F dirty/untracked files: none
- `.venv/bin/python`: present
- Preflight result: **PASS**

## 4. P1.ENF-A Evidence Gate

- P1.ENF-A report found: yes
- P1.ENF-A report path: `agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md`
- P1.ENF-A indexed: yes (`agent/REPORTS.md`)
- P1.ENF-A validation evidence: recorded in P1.ENF-A report and `agent/TESTS.md`
- P1.ENF-A commit evidence: `07c65b5ee46aad0f478e99576a793d9d65a6eae1`
- P1.ENF-A final/current git clean: yes (clean before repair edits)
- P2.9-B remains NOT DONE: yes
- Gate result: **PASS**

## 5. OMNI Findings Addressed

| Finding | Status |
|---------|--------|
| F-TEST-01 — consent fixtures mutated by test runs | **ADDRESSED** |
| F-TOOL-01 — baseline mypy/ruff over-claimed on core wiring | **ADDRESSED** (scoped core probe + doctrine) |
| F-CORE-01 — merkle_root not tamper-evident without verify_chain pairing | **ADDRESSED** (C1 recompute) |

Findings not reproduced: none  
Findings deferred: Golden Thread staleness, ROADMAP drift, UnsafeLocalSandbox hardening, global type debt, full-suite/coverage seal

## 6. Consent Fixture Determinism Discovery

- Tracked fixture files inspected: `consent_request.json`, `consent_record.json`, `consent_revoked.json`, `delta_report.json`, `delta_report_mismatch.json`
- Mutation source found: `tests/identity/test_operator_consent_cli.py` module-scoped autouse fixtures calling `_REQUEST_PATH.write_text`, `_RECORD_PATH.write_text`, `_REVOKED_PATH.write_text` on tracked paths
- Current fixture diffs: none at preflight
- Diff type: N/A (clean tree)
- Canonical baseline: stable 2026-06-25 timestamps in tracked JSON
- Action taken: redirect generation to pytest `tmp_path` via `build_consent_cli_workspace()`

## 7. Consent Fixture Repair

- Approach: extract `build_consent_cli_workspace(workspace)`; module fixture uses `tmp_path_factory.mktemp("consent_cli")`
- tmp_path used: yes
- frozen clock used: no (canonical tracked fixtures retain stable timestamps; generated artifacts are ephemeral)
- tracked fixtures restored: not required (already clean)
- consent runtime semantics changed: no
- Focused test file: `tests/test_consent_fixture_determinism.py`
- Focused tests: 4 passed
- Post-test fixture mutation: none
- Post-test git status: clean for `tests/fixtures/consent/`

## 8. Core Tooling Truth Discovery

- pyproject mypy config inspected: yes — `disable_error_code` includes `arg-type`, `call-arg`, `union-attr`, etc.
- pyproject ruff config inspected: yes
- baseline mypy command: `.venv/bin/python -m mypy src/agentic_runtime`
- baseline mypy result: **PASS** (328 source files)
- core strict probe command: five runtime/security files with `--enable-error-code arg-type|call-arg|union-attr` and `--follow-imports=silent`
- core strict probe result: **PASS** (5 source files)
- errors found (scoped probe, before fix): 8 in `runtime.py`, `repo_agent.py`, `__init__.py`
- errors fixed: 8 in target files
- errors deferred: transitive lattice debt when `--follow-imports=silent` is not used (~42+ errors outside scope)
- Scope expansion needed: no
- Action taken: in-scope type guards/casts; document probe doctrine in `agent/TESTS.md`

## 9. Core Strict Probe / Type Repair

- Target files: `runtime.py`, `trace.py`, `repo_agent.py`, `core_types.py`, `__init__.py`
- arg-type enabled: yes
- call-arg enabled: yes
- union-attr enabled: yes
- Sandbox-None defect found: yes (`build_runtime` Optional sandbox not narrowed)
- Sandbox-None defect fixed: yes (`assert sandbox is not None` + `cast(SandboxBackend, sandbox)`)
- Other core defects fixed: contract None guard in `runtime.submit()`; `files_to_modify` list narrowing in `repo_agent.py`; `ProfiledSandbox` accepted in `build_runtime` signature
- agent/TESTS.md updated: yes
- Validation truth language updated: yes

## 10. Trace Merkle Semantics Discovery

- Trace file: `src/agentic_runtime/trace.py`
- verify_chain behavior: recomputes expected entry hash from `prev_entry_hash` + live `payload_hash()`
- payload_hash behavior: canonical hash of record fields
- entry_hash behavior: stored chain link `sha(prev, payload_hash())`
- merkle_root behavior before repair: used stored `entry_hash` leaves — unchanged when payload mutated in memory
- Call sites inspected: `InMemoryTraceLedger`, `PersistentTraceLedger`, existing trace tests
- Compatibility risk: low — valid chains produce identical roots; tampered payloads now change root

## 11. Trace Merkle Repair / Guard Decision

- Selected option: **C1 recompute**
- Reason: no persisted-evidence compatibility blocker; `verify_chain` already uses live payload recompute
- Implementation: Merkle leaves use `sha(prev, payload_hash())` for in-memory records and `_entry_hash(event)` for persisted events
- Tests added: `tests/test_trace_merkle_integrity.py`
- verify_chain detects mutation: yes (existing + new test)
- merkle_root mutation behavior: root changes after live payload mutation
- Guard behavior: N/A (C1, not C2)
- Existing trace tests: 12 passed

## 12. Tests Added / Updated

| File | Change |
|------|--------|
| `tests/test_consent_fixture_determinism.py` | added (4 tests) |
| `tests/test_trace_merkle_integrity.py` | added (2 tests) |
| `tests/identity/test_operator_consent_cli.py` | refactored to tmp_path generation |

## 13. Validation Run

| Command | Result |
|---------|--------|
| compileall | **PASS** |
| consent fixture determinism tests | **4 passed** |
| trace merkle integrity tests | **2 passed** |
| trace tests | **12 passed** |
| P1.ENF-A regression tests | **24 passed** |
| baseline mypy | **PASS** (328 files) |
| core strict mypy probe | **PASS** (5 files, silent imports) |
| ruff | **PASS** |
| optional selector | not run |
| full suite | **NOT RUN** |
| coverage | **NOT RUN** |
| bandit | **NOT RUN** |
| git status after validation | clean (pre-commit) |

## 14. Clean-Git Proof After Validation

Consent fixture directory unchanged after focused consent + determinism tests.
Full repair validation left only intentional in-scope modifications staged for
commit.

## 15. Files Created / Modified

**Created**

- `agent/reports/P1_ENF_A_OMNI_R1_VALIDATION_TRUTH_CORE_INTEGRITY_REPAIR.md`
- `tests/test_consent_fixture_determinism.py`
- `tests/test_trace_merkle_integrity.py`

**Modified**

- `tests/identity/test_operator_consent_cli.py`
- `src/agentic_runtime/trace.py`
- `src/agentic_runtime/runtime.py`
- `src/agentic_runtime/__init__.py`
- `src/agentic_runtime/repo_agent.py`
- `agent/TESTS.md`
- `agent/REPORTS.md`
- `agent/STATE.md`

## 16. What Was Deliberately Not Implemented

- P1.ENF-B entrypoint bypass expansion
- P1.ENF-C Golden Thread B
- P1.ENF-D identity CLI / kernel deepening
- P1.ENF-E sandbox hardening
- P1.ENF-F full drift gates
- P2.9-B rerun
- P2 true vertical slice
- ROADMAP v5.5 archive cleanup
- stub module sentinel cleanup
- global mypy strictness
- full coverage seal
- product/live behavior

## 17. Remaining Risks / Limitations

- **Golden Thread:** stale follow-up remains
- **ROADMAP drift:** historical drift remains
- **UnsafeLocalSandbox:** still unsafe by design
- **Stub modules:** remain
- **Global type debt:** baseline mypy still disables core-sensitive codes repo-wide; only scoped probe proves five-file wiring
- **Coverage:** not run
- **Full suite:** not run
- **Transitive core probe:** same five files without `--follow-imports=silent` still fail on imported lattice debt — not claimed as repaired

## 18. Next Recommended Step

**P1.ENF-B** — Entrypoint Bypass Guard Expansion / Repo Agent Enforcement Audit

## 19. Commit Hash

_To be recorded after commit._

## 20. Final Git Status

_To be recorded after commit._
