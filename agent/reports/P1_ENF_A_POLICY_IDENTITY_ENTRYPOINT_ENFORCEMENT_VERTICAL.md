# P1.ENF-A Policy + Identity Enforcement Readiness / Runtime Submit Wiring

**Date:** 2026-07-01
**Pack:** P1.ENF-A - Policy + Identity Enforcement Readiness / Runtime Submit Wiring
**Status:** DONE pending final commit hash - enforcement bridge implemented; P2.9-B remains NOT DONE

## 1. Result Header

P1.ENF-A begins the enforcement migration with one narrow runtime submit vertical:
policy resolver output can influence `AgenticRuntime.submit()` under an explicit
`ENFORCE_FAIL_CLOSED` mode, identity context can be bound into submit preflight
artifacts, and entrypoint-like surfaces are classified by bypass risk.

Default behavior remains compatible: without an explicit governance enforcement
config or identity loader, runtime submit does not attach the new artifacts and
does not change outcomes. No TRACE_VERIFIED, production LIVE, Shell enforcement,
v1 readiness, P2.9-B completion, or full Custos runtime is claimed.

## 2. Repair / Enforcement Scope

- Added closed-world governance enforcement modes: `SHADOW_ONLY`, `ADVISORY`,
  `ENFORCE_FAIL_CLOSED`, `DISABLED_UNAVAILABLE`.
- Added policy resolver submit influence using existing policy-card registry and
  context binding.
- Added identity submit context binding with deterministic source hashes.
- Added entrypoint bypass guard classifier.
- Integrated the policy and identity preflight into `AgenticRuntime.submit()`.
- Added focused runtime/security tests.
- Updated report index, state, active task, architecture, decisions, tests, and
  roadmap progress mirror minimally.

## 3. Git / Worktree Preflight

- Branch: `master`
- Initial status: clean
- Unrelated dirty files: none
- P2.9-B dirty/untracked files: none
- P2.9-C/P2.9-D/P2.10+ dirty/untracked files: none
- `.venv/bin/python`: present
- Preflight result: PASS

## 4. P2.9-A-R1 Prerequisite Gate

- Report found: yes
- Report path: `agent/reports/P2_9_A_R1_SHELL_EXIT_SEAL_FOUNDATION_EVIDENCE_REF_REPAIR.md`
- Indexed: yes, in `agent/REPORTS.md`
- Validation evidence: recorded in P2.9-A-R1 report and `agent/TESTS.md`
- Commit evidence: latest relevant commit identified as `ab1b2ba38a92c2701d7cc645d697f45adb660794`
- Final/current git clean: current git was clean before P1.ENF-A edits
- Dirty consent fixture blocker resolved: yes
- P2.9-B remains NOT DONE: yes
- P2.9-C/P2.9-D/P2.10+ not started: yes
- Gate result: PASS

## 5. Runtime Submit Discovery

- Runtime submit located: `src/agentic_runtime/runtime.py`
- Submit entrypoint: `AgenticRuntime.submit(cmd, card)`
- `CommandEnvelope` type: `src/agentic_runtime/core_types.py`
- `PolicyVerdict` type: `src/agentic_runtime/core_types.py`
- Existing policy hook: `PolicyEngine.evaluate(cmd, card)`
- Existing shadow artifact: `ObservationEnvelope.artifacts["policy_shadow_projection"]`
- Existing identity hook: none in submit preflight before this pack
- Existing trace behavior: `_append_transition()` appends `StateTransitionRecord`
- Existing memory behavior: `_record_command_memory()` writes after traced success path

## 6. Policy Resolver Discovery

- Resolver located: `src/agentic_runtime/policy_cards/resolver.py`
- Registry/context binding located: `policy_cards/registry.py`, `policy_cards/context_binding.py`
- Shadow projection located: `policy_cards/runtime_projection.py`
- Current enforcement behavior before pack: shadow-only metadata when explicitly enabled
- Gap confirmed: resolver output did not affect submit verdict
- Action taken: added `policy_submit_influence.py` and a submit preflight gate consumed by runtime

## 7. Identity Loader / Config Discovery

- Identity configs located: `config/aurel/*.yaml`
- Identity loaders located: `src/agentic_runtime/identity/source_bundle.py`
- Operator contract located: `config/aurel/operator_contract.yaml`
- Persona/kernel located: `config/aurel/persona_manifest.yaml`, `config/aurel/identity_kernel.yaml`
- Current submit binding before pack: none
- Gap confirmed: identity context hashes were not submit preflight evidence
- Action taken: added `identity_submit_context.py` and optional runtime preflight binding

## 8. Shell / repo_agent Entrypoint Discovery

- AurelShell modules inspected: `src/agentic_runtime/aurel_shell/`
- repo_agent modules inspected: `src/agentic_runtime/repo_agent.py`
- Execution-like paths found: `ToolRuntime.dispatch`, sandbox `run_shell`, repo agent patch/test helpers
- Non-executing contract modules: AurelShell contract/read-model modules
- Governed submit paths: `AgenticRuntime.submit`
- Governed delegation required paths: repo_agent execution-like paths
- Blocked unknown risk paths: unknown execution-like entrypoint strings
- Action taken: added `entrypoint_governance_guard.py` classifier only

## 9. Enforcement Mode Contract

- Module: `src/agentic_runtime/governance_enforcement.py`
- Mode enum: `GovernanceEnforcementMode`
- Modes: `SHADOW_ONLY`, `ADVISORY`, `ENFORCE_FAIL_CLOSED`, `DISABLED_UNAVAILABLE`
- Default mode: `SHADOW_ONLY`
- Closed-world validation: invalid mode object rejected by dataclass validation
- Truth label: `ENFORCEMENT_BRIDGE`

## 10. Policy Resolver Submit Influence

- Module: `src/agentic_runtime/policy_submit_influence.py`
- Influence object: `PolicyResolverSubmitInfluence`
- Gate result object: `PolicyResolverSubmitGateResult`
- Artifact object: `PolicyResolverSubmitArtifact`
- Runtime integration point: after P0 policy allow and before approval/sandbox/execution
- `SHADOW_ONLY`: records resolver decision without blocking
- `ADVISORY`: records resolver influence without blocking
- `ENFORCE_FAIL_CLOSED`: blocks on policy deny, policy error, strict conflict, or required missing policy context
- Policy deny blocks submit: yes, under explicit `ENFORCE_FAIL_CLOSED`
- Missing required policy context blocks submit: yes, under explicit `ENFORCE_FAIL_CLOSED`
- Artifact/evidence emitted: yes, under explicit governance enforcement config
- Truth label: `ENFORCEMENT_BRIDGE`

## 11. Identity Submit Context Binding

- Module: `src/agentic_runtime/identity_submit_context.py`
- Identity context object: `IdentitySubmitContext`
- Identity hash: `IdentitySubmitContextHash`
- Submit/preflight binding point: before P0 policy evaluation and before sandbox/tool execution
- Missing identity behavior: advisory in shadow/advisory unless required in fail-closed mode
- `ENFORCE_FAIL_CLOSED` missing identity behavior: submit denied before sandbox/tool execution
- Identity state mutated: false
- Artifact/evidence emitted: yes, when governance enforcement is explicitly configured
- Truth label: `ENFORCEMENT_BRIDGE`

## 12. Entrypoint Bypass Guard

- Module: `src/agentic_runtime/entrypoint_governance_guard.py`
- Guard object: `EntrypointGovernanceGuard`
- Classifications: `NON_EXECUTING_CONTRACT_ONLY`, `GOVERNED_RUNTIME_SUBMIT`,
  `GOVERNED_DELEGATION_REQUIRED`, `BLOCKED_UNKNOWN_EXECUTION_RISK`, `UNAVAILABLE`
- Runtime submit classification: governed runtime submit
- AurelShell classification: non-executing contract/read-model only
- repo_agent classification: governed delegation required
- Unknown execution-like classification: blocked unknown execution risk
- Command router created: false
- Product execution created: false
- Truth label: `CONTRACT_ONLY` classifier plus `ENFORCEMENT_BRIDGE` result evidence

## 13. Integration-First Proof

- Backend capability: yes, runtime submit preflight gate is implemented and tested
- Versioned contract/schema: yes, mode/config/result/artifact/context/classifier objects
- Projection/API/read model: yes, submit artifacts and entrypoint guard result
- CLI/Shell/TUI binding: partial classifier only; no product UI or command router
- Trace/evidence/report binding: submit artifacts participate in observation hash when explicit config is used
- Operator-testable path: focused pytest exercises runtime submit behavior

## 14. Truth Label Proof

- LIVE: not claimed
- TRACE_VERIFIED: not claimed
- DEV_FIXTURE: synthetic test command, policy card, identity hash, and entrypoint fixtures
- CONTRACT_ONLY: entrypoint guard read model
- ENFORCEMENT_BRIDGE: runtime submit preflight gate under explicit mode
- UNAVAILABLE: full Custos, Shell product execution, permission matrix, safe sandbox hardening

## 15. Side-Effect Proof

- P2.9-B implemented: false
- P2.9-C started: false
- P2.9-D started: false
- P2.10+ started: false
- Full Custos runtime created: false
- Permission matrix created: false
- Shell command router created: false
- Product UI created: false
- Identity CLI refactored: false
- Golden Thread B created: false
- Sandbox backend rewritten: false
- Memory behavior rewritten: false
- Trace ledger rewritten: false
- Fake TRACE_VERIFIED claimed: false
- Fake LIVE Shell claimed: false

## 16. Files Created / Modified

Created:

- `src/agentic_runtime/governance_enforcement.py`
- `src/agentic_runtime/policy_submit_influence.py`
- `src/agentic_runtime/identity_submit_context.py`
- `src/agentic_runtime/entrypoint_governance_guard.py`
- `tests/test_governance_enforcement_submit.py`
- `tests/test_identity_submit_context.py`
- `tests/test_entrypoint_governance_guard.py`
- `agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md`

Modified:

- `src/agentic_runtime/runtime.py`
- `src/agentic_runtime/__init__.py`
- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/ARCHITECTURE.md`
- `agent/DECISIONS.md`
- `agent/TESTS.md`
- `agent/ROADMAP.md`

## 17. Tests Added / Updated

- `tests/test_governance_enforcement_submit.py`
- `tests/test_identity_submit_context.py`
- `tests/test_entrypoint_governance_guard.py`

Coverage includes shadow/advisory compatibility, fail-closed policy deny, missing
policy context, identity hash stability, identity submit artifact binding,
missing required identity fail-closed, no identity mutation, runtime submit
classification, AurelShell non-executing classification, repo_agent governed
delegation requirement, unknown execution risk blocking, and no-overclaim proof.

## 18. Validation Run

Commands and results:

```bash
.venv/bin/python -m compileall src tests
```

Result: PASS.

```bash
.venv/bin/python -m pytest tests/test_governance_enforcement_submit.py -q
```

Result: 11 passed.

```bash
.venv/bin/python -m pytest tests/test_identity_submit_context.py -q
```

Result: 7 passed.

```bash
.venv/bin/python -m pytest tests/test_entrypoint_governance_guard.py -q
```

Result: 6 passed.

```bash
.venv/bin/python -m pytest tests -q -k "runtime or policy or policy_cards or identity or repo_agent or aurel_shell"
```

Result: 3229 passed, 3493 deselected.

```bash
.venv/bin/python -m ruff check src tests
```

Result: PASS, all checks passed.

```bash
.venv/bin/python -m mypy src/agentic_runtime
```

Result: PASS, no issues found in 328 source files.

Optional manual full suite:

```bash
.venv/bin/python -m pytest -q --tb=line
```

Result: interrupted after extended runtime; 4140 passed before interrupt, no
failure output before interrupt. Not claimed as a full-suite PASS.

Coverage:

```bash
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
```

Result: not run. The optional full-suite run exceeded the manual-seal time window.

Bandit:

```bash
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

Result: PASS for medium/high severity scan; no issues identified.

## 19. What Was Deliberately Not Implemented

- P2.9-B readiness/evidence matrix
- P2.9-C gap/risk evaluation
- P2.9-D section seal
- P2.10+ multi-client/product work
- Full P9 Custos runtime
- Full P2.11 permission matrix
- Full Shell command router
- Product UI
- Identity CLI monolith refactor
- Golden Thread B
- Sandbox backend rewrite
- Automated drift verifier
- Full safe sandbox enforcement

## 20. Remaining Risks / Limitations

- Enforcement bridge is explicit-config only; broad default production enforcement remains future work.
- Entry point guard classifies known strings and does not yet audit every importable function.
- Identity submit context binding is optional through loader/config and does not refactor identity CLI.
- UnsafeLocalSandbox hardening remains future work.
- Full Custos runtime and permission matrix remain unavailable.
- Old roadmap docs may contain historical drift.
- Golden Thread B remains a separate follow-up.

## 21. Next Recommended Step

Rerun P2.9-B - Shell Exit Seal Readiness / Validation / Evidence Matrix, unless the
operator chooses P1.ENF-B first.

## 22. Commit Hash

Pending until commit. Final response records the repair commit hash.

## 23. Final Git Status

Pending until commit. Expected final status: clean.
