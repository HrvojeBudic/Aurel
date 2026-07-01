# P1.ENF-E — Sandbox Safe Backend Gating / UnsafeLocalSandbox Hardening

**Date:** 2026-07-01  
**Pack:** P1.ENF-E  
**Status:** DONE — SANDBOX_BACKEND_GATED / P2.9-B_NOT_DONE

## 1. Result Header

P1.ENF-E adds sandbox backend safety classification and a runtime submit/preflight gate so `UnsafeLocalSandbox` and dev fixtures cannot masquerade as LIVE, SAFE_VERIFIED, or product execution boundaries. `SAFE_VERIFIED` remains unavailable (no proof in repo). Does not implement full sandbox platform, P2.REVIEW-A, P2.9-B, or Shell product behavior.

## 2. Scope

- Sandbox backend discovery and safety taxonomy
- Backend requirement / gate model
- Runtime submit binding under explicit governance enforcement config
- Governance signal args stripped before tool contract validation
- Focused tests + regression preservation
- Repair of `all_records` NameError in `identity_kernel_invariants.py` (blocked baseline mypy)

Not in scope: container/Firecracker/seccomp/AppArmor, full AurelExec rewrite, full tool gateway rewrite, Custos runtime, P2 vertical slice, Shell router, product UI, claiming SAFE_VERIFIED without proof.

## 3. Git / Worktree Preflight

- Branch: `master`
- Initial status: clean
- Unrelated dirty files: none
- P2.REVIEW-A dirty/untracked files: none
- P2.9-B dirty/untracked files: none
- Sandbox files dirty/untracked: none (pre-edit)
- Runtime files dirty/untracked: none (pre-edit)
- Identity files dirty/untracked: none (pre-edit)
- Preflight result: **PASS**

## 4. Prerequisite Evidence Gate

- P1.ENF-D1 report found: yes
- P1.ENF-D1 report path: `agent/reports/P1_ENF_D1_IDENTITY_KERNEL_INVARIANT_ENFORCEMENT_DEEPENING.md`
- P1.ENF-D1 indexed: yes (`agent/REPORTS.md`)
- P1.ENF-D1 validation evidence: yes (11 focused + regressions)
- P1.ENF-D1 commit evidence: yes (`1b85e40`, hash record `fbbe7b7`)
- P1.ENF-D1 final/current git clean: yes
- P2.9-B remains NOT DONE: yes
- Gate result: **PASS**

## 5. Sandbox Discovery

- Sandbox code found: yes (`src/agentic_runtime/sandbox.py`, `sandbox_policy.py`)
- UnsafeLocalSandbox found: yes
- UnsafeLocalSandbox path: `src/agentic_runtime/sandbox.py`
- Sandbox backend classes: `UnsafeLocalSandbox`, `BubblewrapSandbox`, `DockerSandbox`, `ProfiledSandbox` wrapper
- Restricted/safe backend found: Bubblewrap/Docker (hard isolation); not SAFE_VERIFIED
- Direct execution paths: `_run_subprocess` in `sandbox.py`; tool dispatch via `ToolRuntime` / `runtime.submit`
- Runtime dispatch paths: `AgenticRuntime.submit` → `tools.dispatch` after policy/approval/sandbox policy checks
- Tool gateway / executor dispatch paths: `ToolRuntime.dispatch`, repo_agent delegates to `runtime.submit`
- Tests depending on unsafe/dev behavior: existing sandbox/policy tests; new gate tests use `UnsafeLocalSandbox` explicitly
- Discovery result: **PASS**

## 6. Sandbox Safety Taxonomy

- Module: `src/agentic_runtime/sandbox_safety.py`
- Safety classes: UNSAFE_LOCAL, DEV_FIXTURE, RESTRICTED_LOCAL, SAFE_VERIFIED, UNAVAILABLE, ERROR
- UNSAFE_LOCAL: local execution without containment guarantee; not a security boundary
- DEV_FIXTURE: test/demo backend; not LIVE
- RESTRICTED_LOCAL: hard isolation backends (bwrap/docker) without SAFE_VERIFIED proof pack
- SAFE_VERIFIED: requires explicit proof refs; none assigned in this repo
- UNAVAILABLE: required safe backend not proven/available
- ERROR: unknown backend classification
- UnsafeLocalSandbox classified: **UNSAFE_LOCAL**
- SAFE_VERIFIED assigned: **no**
- SAFE_VERIFIED proof: none (`SAFE_VERIFIED_PROOF_REFS` empty)
- No-safe-backend behavior: REQUIRE_SAFE_VERIFIED → UNAVAILABLE; REQUIRE_RESTRICTED_OR_SAFE → DENY for unsafe local under ENFORCE_FAIL_CLOSED

## 7. Backend Requirement / Gate Model

- Module: `src/agentic_runtime/sandbox_backend_gate.py`
- Objects: `SandboxBackendRequirement`, `SandboxBackendGateArtifact`, `SandboxBackendGateResult`, `SandboxBackendViolation`, `P1ENFESideEffectProof`
- Decisions: ALLOW, WARN, DENY, UNAVAILABLE, NOT_APPLICABLE
- Gate modes: DEV_ALLOW_UNSAFE, REQUIRE_RESTRICTED_OR_SAFE, REQUIRE_SAFE_VERIFIED, DISABLED_UNAVAILABLE
- DEV_ALLOW_UNSAFE: allows unsafe/dev with `SANDBOX_BACKEND_GATED` truth and warnings
- REQUIRE_RESTRICTED_OR_SAFE: denies UNSAFE_LOCAL/DEV_FIXTURE under ENFORCE_FAIL_CLOSED
- REQUIRE_SAFE_VERIFIED: UNAVAILABLE when no proof; blocks under ENFORCE_FAIL_CLOSED
- DISABLED_UNAVAILABLE: honest unavailable
- Violation model: structured `SandboxBackendViolation` with truth labels including `BLOCKED_UNSAFE_SANDBOX_PROMOTION`
- Unavailable reason model: `SandboxBackendUnavailableReason` enum
- Side-effect proof: `P1ENFESideEffectProof` (all expansion flags false)

## 8. Runtime Submit / Dispatch Binding

- Runtime file(s): `runtime.py`
- Dispatch seam: after identity invariant gate, before policy evaluation
- Policy result context reused: yes (existing governance config/modes)
- Identity invariant context reused: yes (same explicit enforcement path)
- Sandbox requirement source: `GovernanceEnforcementConfig.require_safe_sandbox_backend` + `_sandbox_backend_signals` in submit args
- Sandbox gate result attached: `governance_enforcement.sandbox_backend_gate` artifact
- Unsafe backend blocked when safe required: yes (`require_safe_sandbox_backend=True`)
- Dev/test unsafe preserved: yes (default DEV_ALLOW_UNSAFE under SHADOW/ADVISORY)
- AurelExec rewritten: no
- Shell/product behavior created: no
- Governance signal args stripped before tool contract validation/dispatch

## 9. Trace / Evidence Binding

- Evidence fields in gate artifact:
  - `sandbox_backend_kind`
  - `sandbox_safety_class`
  - `sandbox_requirement` (via requirement dict)
  - `sandbox_gate_decision`
  - `sandbox_unavailable_reason`
  - `unsafe_backend_allowed_reason`
  - `safe_backend_proof_ref`
- Trace verification claimed: no
- Trace tests affected: none

## 10. Tests Added / Updated

- Sandbox backend gate tests: `tests/test_sandbox_backend_gate.py` (9 tests)
- Sandbox safe backend submit tests: `tests/test_sandbox_safe_backend_submit.py` (4 tests)
- Regression tests: governance enforcement submit, identity invariant enforcement submit, identity submit context, entrypoint guard, validation truth/drift gates, Golden Thread B — **68 passed**

## 11. Validation Run

- compileall: **PASS**
- sandbox backend gate tests: **9 passed**
- sandbox safe backend submit tests: **4 passed**
- governance enforcement submit regression: **PASS**
- identity invariant enforcement regression: **PASS**
- identity submit context regression: **PASS**
- entrypoint governance guard regression: **PASS**
- validation truth / drift gate regression: **PASS**
- Golden Thread B regression: **PASS**
- baseline mypy: **PASS** (336 source files)
- core strict mypy probe: **PASS** (5 files, `--follow-imports=silent`)
- ruff: **PASS**
- optional selector: **NOT RUN**
- bandit: **NOT RUN**
- git status after validation: clean (pre-commit)

## 12. No-Scope-Expansion Proof

- Full sandbox platform rewrite: no
- Container runtime implemented: no
- Firecracker/seccomp/AppArmor implemented: no
- Network/filesystem policy platform implemented: no
- Full AurelExec redesign: no
- Full tool gateway rewrite: no
- Full Custos runtime: no
- P2.REVIEW-A implemented: no
- P2.9-B implemented: no
- P2.9-C/P2.9-D/P2.10+ started: no
- Shell command router created: no
- Product UI created: no
- P2 vertical slice created: no
- repo_agent rewritten: no
- identity CLI refactored: no
- Global mypy strictness enabled: no

## 13. Files Created / Modified

Created:

- `src/agentic_runtime/sandbox_safety.py`
- `src/agentic_runtime/sandbox_backend_gate.py`
- `tests/test_sandbox_backend_gate.py`
- `tests/test_sandbox_safe_backend_submit.py`
- `agent/reports/P1_ENF_E_SANDBOX_SAFE_BACKEND_GATING_UNSAFE_LOCAL_HARDENING.md`

Modified:

- `src/agentic_runtime/runtime.py`
- `src/agentic_runtime/governance_enforcement.py`
- `src/agentic_runtime/__init__.py`
- `src/agentic_runtime/identity_kernel_invariants.py` (mypy-blocking bugfix)
- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/TESTS.md`

## 14. What Was Deliberately Not Implemented

- Full sandbox platform rewrite
- Container/Firecracker/seccomp/AppArmor/OS isolation
- Remote executor
- Full AurelExec / tool gateway / Custos runtime redesign
- P2.REVIEW-A, P2.9-B, P2 vertical slice, Shell product behavior
- repo_agent rewrite, identity CLI refactor
- Global mypy strictness
- SAFE_VERIFIED backend or proof claims

## 15. Remaining Risks / Limitations

- No safe backend: SAFE_VERIFIED remains UNAVAILABLE
- UnsafeLocalSandbox dev/test availability: preserved under explicit DEV_ALLOW_UNSAFE / default advisory paths
- SAFE_VERIFIED: not assigned; requires future proof pack
- Sandbox platform: Bubblewrap/Docker exist but classified RESTRICTED_LOCAL only
- P2.REVIEW-A: next planned true P2 vertical slice decision pack
- P2.9-B: NOT DONE
- P2 contract-only lattice: unchanged
- Full suite / coverage / Bandit: NOT RUN

## 16. Next Recommended Step

**P2.REVIEW-A — First True P2 Vertical Slice Decision**

## 17. Commit Hash

`b271065664205781282a0a2463d7edda8fd897c0`

## 18. Final Git Status

Clean after commit `b271065`.
