# P3-FLOW-G — Self-Healing Runtime Control Loop / Reliability Control Plane Pack

## 1. Result Header

- Task ID: P3-FLOW-G
- Title: Self-Healing Runtime Control Loop / Reliability Control Plane Pack
- Roadmap range: P3.15.0–P3.15.30
- Date: 2026-07-02
- Status: DONE
- Standing operator override remains in force: "override - start p3-Flow-A now,
  p2.11D-p2.20 will contiune after full p3" — P2.11-D through P2.20 remain
  deferred until after full P3; P2 is NOT sealed.

## 2. Pack Scope

AurelFlow gained bounded self-healing control-plane grammar: a reliability
control plane with closed-world loop phases, a Monitor → Detect → Diagnose →
Recover Candidate → Verify Expectation diagnostic loop, a closed-world runtime
failure taxonomy with deterministic classification, advisory root-cause
diagnoses with confidence/evidence-ref/uncertainty contracts, a total
deterministic targeted-recovery policy, recovery candidate envelopes bound to
the P3-FLOW-F checkpoint discipline, attempt/latency/cost/depth recovery
budgets, retry-storm and no-progress loop guards, semantic-silent-failure
signals, graceful degradation and human escalation frames, and a read-only
self-healing projection envelope for future React/AurelShell.

Nothing executes: no retry, repair, recovery, rollback, verifier, source
refresh, tool call, LLM call, runtime.submit, Trace/Ledger write, or
memory/policy/identity mutation. P4 executes. P5 proves. P9 authorizes.

## 3. Canon / Preflight

- Branch: master; initial `git status --short` clean; no unrelated dirty or
  untracked files.
- Chain verified: `c0e7c00` (F hash record) → `86eabd4` (F implementation) →
  `8388cc1` → `3616761`.
- Canon read: AGENT.md, CODEOPS.md, ACTIVE_TASK.md, ROADMAP.md, STATE.md,
  ARCHITECTURE.md, DECISIONS.md, TESTS.md, REPORTS.md, and the P3-FLOW-A/B/C/
  D/E/F reports.
- No canon conflicts found.

## 4. P3-FLOW-F Prerequisite Confirmation

All four F modules (`flow_checkpoint.py`, `flow_replay.py`,
`flow_reversible_state.py`, `flow_reversible_projection.py`) present; all 72
F tests re-run and passing; F report present and indexed. G explicitly
consumes F's `RecoveryCheckpointRequirement` (see DEC-P3FLOWG-04), honoring
the F report's recorded handoff risk that G must not invent a parallel
checkpoint discipline.

## 5. Roadmap Coverage Matrix

| Range | Slice | Status |
| --- | --- | --- |
| P3.15.0–P3.15.4 | Reliability Control Plane | DONE |
| P3.15.5–P3.15.9 | Failure Detection / Classification | DONE |
| P3.15.10–P3.15.14 | Diagnosis / Root Cause | DONE |
| P3.15.15–P3.15.19 | Targeted Recovery Policy / Candidate Selection | DONE |
| P3.15.20–P3.15.24 | Recovery Budgets / Loop Guards | DONE |
| P3.15.25–P3.15.30 | Verification Expectation / Escalation / Projection | DONE |

## 6. P3.15.0–P3.15.4 Reliability Control Plane

`flow_reliability_control.py`: `ReliabilityControlPlane` (deterministic
`flrcp-` id anchored to `run.state.step`), `ReliabilityControlPlaneState`
(all six future gates — checkpoint, budget check, operator review, P4, P5,
P9-if-irreversible — fail-closed True), `SelfHealingControlLawBoundary`
(renamed from the dispatch's ReliabilityControlPlaneBoundary; see
DEC-P3FLOWG-03), `ReliabilityControlReadModel`, `ControlLoopPhase` (16
members; deliberately no RECOVERED/HEALED/VERIFIED member), and
`ControlLoopTransition` (must change phase; `repair_executed`/
`recovery_executed`/`stop_executed` fail-closed False).

## 7. P3.15.5–P3.15.9 Failure Detection / Classification

`flow_reliability_control.py` frames + `flow_diagnosis.py` taxonomy:
`MonitorFrame` (read-only observation), `DetectionFrame` (detection is not a
fix; run-mismatch fail-closed), `RuntimeFailureKind` (22 closed-world members
including SEMANTIC_SILENT_FAILURE, UNSUPPORTED_OUTPUT, EVIDENCE_MISSING,
RETRY_STORM, NO_PROGRESS, TOPOLOGY_AMPLIFICATION_RISK,
DIVERSITY_CORRELATION_RISK, CHECKPOINT_REQUIRED_MISSING),
`RuntimeFailureSignal` (`flfsg-`, step-anchored), `FailureSeverity`,
`FailureRootCauseCategory`, `FailureClassificationFrame` via
`classify_runtime_failure()` over a total deterministic table
(`failure_classification_table()` covers every kind), and
`FailureClassificationReadModel`.

## 8. P3.15.10–P3.15.14 Diagnosis / Root Cause

`flow_diagnosis.py`: `RootCauseDiagnosis` (`fldia-`; `diagnosis_is_not_proof`
fail-closed True; VERY_LOW/LOW/UNKNOWN confidence structurally forces
`requires_human_review=True`), `DiagnosisConfidence` (closed-world: no
CERTAIN/PROVEN/VERIFIED member), `DiagnosisEvidenceRef` (names recorded state
by id; `evidence_retrieved`/`retrieval_available` fail-closed False),
`DiagnosisUncertaintyFrame` (doubt is first-class; human review required),
`DiagnosisReadModel`, plus `DiagnosisFrame` in the control-loop module
binding detection → diagnosis.

## 9. P3.15.15–P3.15.19 Targeted Recovery Policy

`flow_recovery_policy.py`: `RecoveryCandidateKind` (17 closed-world members;
no EXECUTED/APPLIED/COMPLETED member), `RecoveryPolicyRule` (primary +
alternative kinds), `TargetedRecoveryPolicy` (construction fail-closes unless
every failure kind is covered exactly once), `DEFAULT_TARGETED_RECOVERY_POLICY`
implementing the dispatch's exact mapping (timeout→backoff retry, rate
limit→delayed retry, tool unavailable→fallback edge, schema
mismatch/type error→argument repair, malformed JSON→structure repair, missing
field→field completion, context decay/stale retrieval→refresh context,
contradictory evidence→cross-check sources, semantic silent failure/
unsupported output/evidence missing→evidence verification, topology
amplification→insert verifier (alt: prune risky edge), diversity
correlation→human escalation (alt: insert verifier), retry storm→graceful
termination, no progress→human escalation, checkpoint-required-missing→hold),
`RecoveryCandidateSelection` (`selection_is_not_execution` fail-closed),
`RecoveryPolicyReadModel` (`covers_all_failure_kinds` fail-closed True),
`RecoveryCandidateEnvelope` (all six requires_* gates fail-closed True; binds
a P3-FLOW-F `RecoveryCheckpointRequirement` id — auto-derived when absent),
`RecoveryExecutionRequirement`, `RecoveryVerificationRequirement`,
`RecoveryCandidateBoundary`, `RecoveryCandidateReadModel`.

## 10. P3.15.20–P3.15.24 Recovery Budgets / Loop Guards

`flow_recovery_budget.py`: `RecoveryBudget` aggregating
`RecoveryAttemptBudget`/`RecoveryLatencyBudget` (logical steps, never wall
clock)/`RecoveryCostBudget`/`RecoveryDepthBudget` (all with non-negative
counters, `budget_enforced`/`permission_granted` fail-closed False),
`RecoveryBudgetState` (plain arithmetic derivation; cannot be both available
and exhausted; `degradation_auto_authorized` fail-closed False),
`RecoveryBudgetExhaustedSignal` (only constructible from an exhausted state;
requires operator review + human escalation), `RecoveryBudgetReadModel`,
`RetryStormGuard` (at/above limit structurally cannot be constructed
unblocked; `stop_executed` fail-closed False), `NoProgressGuard` (at/above
limit forces block + human escalation), `ControlLoopCollapseSignal`,
`LoopHealthSignal` with `LoopHealth` (deterministic precedence: COLLAPSED >
STORMING > STALLED > DEGRADING > HEALTHY/UNKNOWN), `LoopSafetyReadModel`.

## 11. P3.15.25–P3.15.30 Verification Expectation / Escalation / Projection

`VerifyExpectationFrame` (verification_required True; verification_available/
executed/proof/trace fail-closed False), `RecoveryVerificationRequirement`,
semantic signals (`SemanticSilentFailureSignal`, `UnsupportedOutputSignal`,
`EvidenceMissingSignal` — all `treated_as_runtime_failure_candidate` True and
`is_harmless_warning` fail-closed False), `EvidenceSupportRequirement`,
`ContradictionCheckRequirement`, `SemanticFailureReadModel`,
`GracefulDegradationFrame` (`degradation_is_visible` True, `failure_hidden`
fail-closed False), `HumanEscalationFrame` (`escalation_is_not_approval`
True; approval/authority fail-closed False), `EscalationReason` (14 members),
`EscalationReadModel`, and the full projection layer in
`flow_self_healing_projection.py` (section 14 below).

## 12. Reliability Control Plane Proof

- Deterministic: identical run + creator → identical `flrcp-` id (tested).
- Phase vocabulary closed-world: the test asserts the exact 16-member set and
  the absence of RECOVERED/HEALED/VERIFIED.
- Transitions record; a same-phase transition and any `repair_executed=True`
  construction raise `AurelFlowValidationError`
  (FORBIDDEN_BOUNDARY_CLAIM / INVALID_LIFECYCLE_TRANSITION).
- Non-mutation proven against `build_flow_demo_bundle()` (step, lifecycle,
  history unchanged).

## 13. Failure Taxonomy Proof

- Exact closed-world membership asserted in tests.
- Classification table proven total over `RuntimeFailureKind`.
- Classification deterministic and `classification_is_not_proof` fail-closed.
- CONTROL_LOOP_COLLAPSE → CRITICAL/CONTROL_LOOP;
  SEMANTIC_SILENT_FAILURE → HIGH/SEMANTIC_OUTPUT (tested).

## 14. Diagnosis Boundary Proof

- `proof_available=True` unconstructible on signal, classification, diagnosis.
- Low confidence structurally forces human review (builder and direct
  construction both tested).
- Evidence refs cannot claim retrieval.
- Confidence vocabulary has no proof-grade member.

## 15. Targeted Recovery Policy Proof

- 12 parametrized mapping tests pin the dispatch's deterministic table.
- Partial policies fail-close at construction.
- Selection determinism tested; `authority_granted`/`recovery_executed`
  fail-closed False.

## 16. Recovery Budget / Guard Proof

- Exhaustion visible per dimension ("ATTEMPTS", "DEPTH", …) and only
  representable from a genuinely exhausted state.
- Budget availability is not permission: `permission_granted` and
  `execution_available` fail-closed False on budget, state, read model, and
  view model.
- Retry-storm guard at limit blocks and cannot be constructed unblocked;
  `stop_executed` fail-closed False everywhere.
- No-progress guard at limit forces block + human escalation.

## 17. Semantic Silent Failure Proof

- All three semantic signals are failure candidates
  (`treated_as_runtime_failure_candidate` fail-closed True,
  `is_harmless_warning` fail-closed False).
- Evidence support requirement retrieves nothing; contradiction check
  requirement runs no verifier.
- Policy maps all three semantic kinds to EVIDENCE_VERIFICATION_CANDIDATE.

## 18. Graceful Degradation / Human Escalation Proof

- Degradation is visible and `failure_hidden=True` is unconstructible.
- Escalation is not approval: `approval_granted`, `authority_granted`,
  `execution_available` fail-closed False on frames, read model, view model.
- Budget exhaustion and blocked guards require, not grant, escalation.

## 19. Projection / React Readiness Proof

- Seven view models + `SelfHealingProjectionEnvelope`, all
  `react_projection_only=True`, `frontend_mutation_allowed=False`,
  `ui_recovery_execution_allowed=False`, `ui_authority_granted=False`,
  `api_server_implemented=False`, `frontend_implemented=False`.
- `ReliabilityControlReactProjectionBoundary` pins the law: React is
  projection only, Python runtime is source of truth, a UI retry button is
  not recovery execution, UI approval is not Custos authority.
- Envelope deterministic and run-lineage validated.

## 20. No-Execution / No-Authority / No-Proof Proof

`test_p3_flow_g_no_execution_boundary.py` (7 tests): forbidden source
patterns (subprocess/socket/requests/pickle/open/eval/exec, `.submit(`,
AgenticRuntime/ApprovalGate/TraceLedger, trace/memory/policy/sandbox/tools/
runtime imports, worker spawning, `def execute_retry/repair/recovery/
rollback/verifier/stop`, React/FastAPI/Flask/Django/WebSocket imports, JSX)
over all 5 G modules; AST proof that G modules import only
`__future__`/`dataclasses`/`enum`/`typing` plus package-relative modules; no
LIVE/TRACE_VERIFIED assignment anywhere; construction chain never mutates the
demo run; no forbidden truth labels in outputs; full chain never claims
execution/proof/authority; package-wide execution scan still holds.

## 21. Tests / Validation

New tests (89 total):

| File | Tests |
| --- | --- |
| tests/test_p3_flow_g_reliability_control.py | 13 |
| tests/test_p3_flow_g_failure_taxonomy.py | 11 |
| tests/test_p3_flow_g_diagnosis.py | 11 |
| tests/test_p3_flow_g_recovery_policy.py | 22 |
| tests/test_p3_flow_g_recovery_budget_guards.py | 14 |
| tests/test_p3_flow_g_projection.py | 11 |
| tests/test_p3_flow_g_no_execution_boundary.py | 7 |

Validation run (all from `.venv`):

- `python -m compileall src tests` — PASS.
- G tests: 89 passed (first full run, zero test-logic fixes).
- Regressions unchanged: A 50 (all five A files), B 53, C 65, D 42, E 62,
  F 72 — 344 regression tests passed.
- `ruff check src tests` — "All checks passed!".
- `mypy src/agentic_runtime` — "Success: no issues found in 390 source files".
- `git status --short` after validation — only the 13 in-scope files.

Not run (lean doctrine, no runtime/security/sandbox path touched): full
repository pytest suite, coverage, Bandit.

## 22. Files Created / Modified

Created (source):
- `src/agentic_runtime/aurel_flow/flow_reliability_control.py`
- `src/agentic_runtime/aurel_flow/flow_diagnosis.py`
- `src/agentic_runtime/aurel_flow/flow_recovery_policy.py`
- `src/agentic_runtime/aurel_flow/flow_recovery_budget.py`
- `src/agentic_runtime/aurel_flow/flow_self_healing_projection.py`

Created (tests): the seven files listed in section 21.

Created (canon): this report.

Modified:
- `src/agentic_runtime/aurel_flow/__init__.py` (193 new exports; 813 total,
  all verified to resolve with no duplicates)
- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`,
  `agent/ROADMAP.md`, `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`,
  `agent/TESTS.md`

## 23. What Was Deliberately Not Implemented

P3.16 autonomy enforcement; P3.17 scheduling/resource allocation; P3.18 live
compound topology; P3.19 harness evaluation; P3.20 extended seal; P4 recovery
execution; P5 proof/Trace verification; P9 Custos authority; runtime.submit
bridge; actual retry/repair/recovery/rollback/verifier/source-refresh
execution; tool/LLM/subprocess/network/sandbox execution; Trace/Ledger write;
memory/policy/identity mutation; React components/routes/frontend state;
AurelShell product UI; API server/REST/WebSocket; persistence; migration.

## 24. Remaining Risks

- Guard counters (`retry_count`, `same_failure_count`, `no_progress_count`)
  are caller-declared; nothing in P3 measures them from live execution — P4
  must feed real counters.
- Diagnosis confidence is operator/caller-assigned advisory judgment, not a
  measured quantity; P3-FLOW-K harness evaluation should later measure
  diagnosis quality.
- The default policy's severity and mapping tables are deterministic policy
  choices, not learned behavior; future packs may version new tables (v2)
  but must not mutate v1.
- Budget latency is logical-step denominated; wall-clock latency budgeting
  belongs to the execution plane.
- P3-FLOW-H must consume these budgets/guards/escalation boundaries rather
  than invent parallel autonomy limits.
- P4/P5/P9 handoffs remain contract-only until those phases exist.

## 25. Next Pack: P3-FLOW-H

P3-FLOW-H — Governed Autonomy Levels / Scope Envelopes Pack (P3.16). It
should consume `RecoveryBudget*`, `RetryStormGuard`/`NoProgressGuard`,
`HumanEscalationFrame`, and the semantic failure boundaries when defining
autonomy levels. Not started; awaiting explicit dispatch.

## 26. Commit Hash

Implementation commit: recorded in the follow-up docs(agent) commit, per pack
convention — a report cannot honestly contain its own commit's hash before
that commit exists. See `agent/REPORTS.md` and `git log` for the final
hashes.

## 27. Final Git Status

Clean after commit (verified with `git status --short`); branch master; no
branch created; no push; no history rewrite; only the 20 in-scope files
staged (5 source modules, 1 `__init__.py`, 7 test files, this report, 7 canon
files updated as listed in section 22).
