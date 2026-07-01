# P1.ENF-F-A Tooling / Determinism / Shadow-Still-Active Drift Gates

**Date:** 2026-07-01  
**Pack:** P1.ENF-F-A  
**Status:** DONE

## 1. Result Header

P1.ENF-F-A adds lightweight executable drift gates that detect validation overclaim,
tracked fixture mutation, weak tooling evidence, shadow/enforcement mismatch,
contract/live overclaim, unknown entrypoint risk drift, and report/code claim drift.

P1.ENF-A, P1.ENF-A-OMNI-R1, and P1.ENF-B remain DONE. P1.ENF-C remains next
planned Golden Thread pack. P2.9-B remains NOT DONE. No full CI, global mypy
strictness, product/live behavior, or all-drift-impossible claim is made.

## 2. Scope

- `validation_truth_gates.py` — determinism/dirty worktree and tooling truth gates
- `drift_gates.py` — shadow/enforcement, contract mismatch, entrypoint risk, claim drift
- Focused gate tests
- Agent report/state/index sync

Not in scope: P1.ENF-C, P1.ENF-F-B, P1.ENF-D1, P1.ENF-E, P2.9-B+, Shell router,
repo_agent rewrite, sandbox hardening, full CI platform.

## 3. Git / Worktree Preflight

- Branch: `master`
- Initial status: clean
- Unrelated dirty files: none
- P1.ENF-C dirty/untracked files: none
- P1.ENF-D/E/F-B dirty/untracked files: none
- P2.9-B dirty/untracked files: none
- `.venv/bin/python`: present
- Preflight result: **PASS**

## 4. Prerequisite Evidence Gate

### P1.ENF-A

- Report found: yes
- Report path: `agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md`
- Indexed: yes (`agent/REPORTS.md`)
- Validation evidence: recorded in P1.ENF-A report and `agent/TESTS.md`
- Commit evidence: `07c65b5ee46aad0f478e99576a793d9d65a6eae1`
- Final/current git clean: yes (clean before P1.ENF-F-A edits)
- Gate result: **PASS**

### P1.ENF-A-OMNI-R1

- Report found: yes
- Report path: `agent/reports/P1_ENF_A_OMNI_R1_VALIDATION_TRUTH_CORE_INTEGRITY_REPAIR.md`
- Indexed: yes (`agent/REPORTS.md`)
- Validation evidence: recorded in repair report and `agent/TESTS.md`
- Commit evidence: `8bf05de796e0c066c396005c993b82e0b90b5a69`
- Final/current git clean: yes
- Gate result: **PASS**

### P1.ENF-B

- Report found: yes
- Report path: `agent/reports/P1_ENF_B_ENTRYPOINT_BYPASS_GUARD_REPO_AGENT_ENFORCEMENT_AUDIT.md`
- Indexed: yes (`agent/REPORTS.md`)
- Validation evidence: recorded in P1.ENF-B report and `agent/TESTS.md`
- Commit evidence: `47ea1286ad2ee681c34c4c5a4b35b5e308f1263a`
- Final/current git clean: yes
- P2.9-B remains NOT DONE: yes
- Gate result: **PASS**

## 5. Gate Families Implemented

| Family | Module | Status |
|--------|--------|--------|
| A — Determinism / Dirty Git | `validation_truth_gates.py` | implemented |
| B — Tooling Truth / Core Strict Probe | `validation_truth_gates.py` | implemented |
| C — Shadow-Still-Active / Enforcement Bridge | `drift_gates.py` | implemented |
| D — Contract / Enforcement Mismatch | `drift_gates.py` | implemented |
| E — Unknown Entrypoint Risk | `drift_gates.py` | implemented |
| F — Report / Code Claim Drift | `drift_gates.py` | implemented |

## 6. Determinism / Dirty Git Gate

Objects: `DeterminismGate`, `DirtyWorktreeGate`, `TrackedFixtureMutationFinding`,
`ValidationSideEffectFinding`, `DeterminismGateResult`, `DeterminismGateInput`,
`DirtyWorktreeGateInput`, `DirtyWorktreeGateResult`.

Statuses: `PASS`, `FAIL_DIRTY_WORKTREE`, `FAIL_FIXTURE_MUTATION`,
`BLOCKED_UNRELATED_DIRTY_FILES`, `WARN_GATE_INPUT_UNAVAILABLE`, `UNAVAILABLE`.

Behavior:

- compares expected vs observed tracked fixture hashes
- blocks unrelated dirty paths from done-state
- represents dirty tracked fixture mutation as `FAIL_FIXTURE_MUTATION`

## 7. Tooling Truth Gate

Objects: `ToolingTruthGate`, `CoreStrictProbeGate`, `ValidationClaimStrength`,
`ValidationOverclaimFinding`, `ToolingTruthGateResult`, `CoreStrictProbeGateResult`.

Statuses: `PASS`, `FAIL_CORE_STRICT_PROBE_MISSING`, `FAIL_CORE_STRICT_PROBE_FAILED`,
`WARN_BASELINE_ONLY`, `BLOCKED_TOOLING_OVERCLAIM`, `UNAVAILABLE`.

Behavior:

- requires `arg-type`, `call-arg`, `union-attr` on core strict probe input
- warns on baseline-only mypy evidence
- does not enable global mypy strictness

## 8. Shadow-Still-Active Gate

Objects: `ShadowStillActiveGate`, `PolicyShadowMigrationFinding`,
`IdentityShadowMigrationFinding`, `EnforcementBridgePresence`,
`ShadowMigrationGateResult`.

Statuses: `PASS_ENFORCEMENT_BRIDGE_PRESENT`,
`WARN_SHADOW_COMPATIBILITY_MODE_PRESENT`, `FAIL_SHADOW_ONLY_AFTER_ENFORCEMENT_REQUIRED`,
`FAIL_PASSIVE_ARTIFACT_ONLY`, `UNAVAILABLE`.

Behavior:

- allows `SHADOW_ONLY` compatibility when bridge exists and no overclaim
- fails passive artifact-only enforcement claims
- does not fail merely because shadow compatibility mode exists

## 9. Contract / Enforcement Mismatch Gate

Objects: `ContractEnforcementMismatchGate`, `SealedContractReadinessFinding`,
`BindingUnavailableFinding`, `FakeVerticalSliceRisk`, `ContractMismatchGateResult`.

Statuses: `PASS_HONEST_CONTRACT_ONLY`, `WARN_BINDING_UNAVAILABLE`,
`FAIL_FAKE_LIVE_CLAIM`, `FAIL_FAKE_TRACE_VERIFIED_CLAIM`,
`FAIL_SEALED_WITHOUT_UNAVAILABLE_REASON`, `UNAVAILABLE`.

Behavior:

- passes honest contract-only modules with all-false side effects
- warns on honest binding unavailable disclosure
- fails fake LIVE / TRACE_VERIFIED without evidence

## 10. Unknown Entrypoint Risk Gate

Objects: `UnknownEntrypointRiskGate`, `BypassRiskFinding`,
`UnknownEntrypointRiskGateResult`.

Statuses: `PASS`, `FAIL_P1_ENF_B_EVIDENCE_MISSING`, `FAIL_UNKNOWN_MARKED_SAFE`,
`WARN_DELEGATION_REQUIRED_REMAINS`, `BLOCKED_UNKNOWN_EXECUTION_RISK`, `UNAVAILABLE`.

Behavior:

- requires P1.ENF-B report evidence input
- fails unknown-marked-safe metadata
- warns when delegation-required classifications remain visible

## 11. Report / Code Claim Drift Gate

Objects: `ReportCodeClaimDriftGate`, `TruthLabelOverclaimFinding`,
`EvidenceClaimRequirement`, `ClaimDriftGateResult`.

Statuses: `PASS`, `WARN_WEAK_EVIDENCE`, `FAIL_FAKE_LIVE`,
`FAIL_FAKE_TRACE_VERIFIED`, `FAIL_TOOLING_OVERCLAIM`,
`FAIL_FULL_SUITE_OVERCLAIM`, `FAIL_COVERAGE_OVERCLAIM`, `UNAVAILABLE`.

Behavior:

- maps claims (LIVE, TRACE_VERIFIED, full suite, coverage, tooling) to required evidence
- fails overclaim when evidence missing
- no broad natural-language report parser

## 12. Tests Added / Updated

- `tests/test_validation_truth_gates.py` — 6 tests
- `tests/test_drift_gates.py` — 12 tests

## 13. Validation Run

| Command | Result |
|---------|--------|
| compileall | **PASS** |
| validation truth gate tests | **6 passed** |
| drift gate tests | **12 passed** |
| P1.ENF-A-OMNI-R1 repair tests | **6 passed** (consent 4 + trace Merkle 2; consent CLI subprocess test included) |
| P1.ENF-B audit tests | **16 passed** |
| P1.ENF-A enforcement tests | **24 passed** |
| baseline mypy | **PASS** (331 source files) |
| core strict mypy probe | **PASS** (5 files, `--follow-imports=silent`) |
| ruff | **PASS** |
| optional selector | **NOT RUN** |
| bandit | **NOT RUN** |
| git status after validation | clean |

Validation not run: full suite, coverage, Bandit, optional `-k` selector.

## 14. No-Scope-Expansion Proof

`P1ENFFASideEffectProof` defaults all forbidden scope flags to false:

- P1.ENF-C: not implemented
- P1.ENF-F-B: not implemented
- P1.ENF-D1 / P1.ENF-E: not implemented
- P2.9-B: not implemented
- Shell router / product UI / repo_agent rewrite / sandbox hardening: not implemented
- Full CI / global mypy strictness: not implemented

## 15. Files Created / Modified

Created:

- `src/agentic_runtime/validation_truth_gates.py`
- `src/agentic_runtime/drift_gates.py`
- `tests/test_validation_truth_gates.py`
- `tests/test_drift_gates.py`
- `agent/reports/P1_ENF_F_A_TOOLING_DETERMINISM_SHADOW_DRIFT_GATES.md`

Modified:

- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/TESTS.md`
- `agent/ACTIVE_TASK.md`

## 16. What Was Deliberately Not Implemented

- P1.ENF-C Golden Thread B
- P1.ENF-F-B roadmap/docs archive cleanup
- P1.ENF-D1 identity kernel invariant enforcement
- P1.ENF-E sandbox safe backend gating
- P2.9-B rerun
- P2 true vertical slice
- full CI platform
- global mypy strictness
- Shell product implementation
- full Custos runtime
- full permission matrix
- repo_agent rewrite
- sandbox backend rewrite

## 17. Remaining Risks / Limitations

- Golden Thread: stale sections remain follow-up
- ROADMAP drift: not repaired in this pack
- UnsafeLocalSandbox: remains unsafe demo backend
- Stub modules: contract-only stubs remain
- P2 contract-only lattice: unchanged
- Full CI: not built
- Global type debt: baseline mypy still disables broad error codes
- Coverage: not run
- Full suite: not run
- Gate inputs: structured/test-first; no repo-wide automatic report parser

## 18. Next Recommended Step

**P1.ENF-C — Golden Thread B / P1.8–P2.9 Governance Continuity**

Alternative operator path: **P2.9-B** Shell Exit Seal Readiness rerun.

## 19. Commit Hash

`d91d2e25bfea6e313bd79a3d0f2aa10966f2efd8`

## 20. Final Git Status

Clean after commit (`git status --short` empty).

## Gate Input Conventions

**Structured inputs:** tests and callers construct `*GateInput` dataclasses directly with
explicit booleans, hashes, classifications, and evidence maps.

**Report inputs:** gates accept booleans like `p1_enf_b_report_present`; callers derive
these from known report paths without NL parsing.

**Code inputs:** enforcement bridge presence, entrypoint classifications, and tooling
probe metadata are passed explicitly from verified repo evidence.

**Natural-language parser created:** no

**Limitations:** gates detect drift when inputs are supplied; they do not scan the entire
repository by default.
