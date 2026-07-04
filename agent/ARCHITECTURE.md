# Architecture Map

## Core law

> **Entity proposes. Runtime disposes.**

The entity (`AgenticEntity`) plans and emits `CommandEnvelope` proposals.
The runtime (`AgenticRuntime`) alone decides whether a command is permitted,
how it executes, and how results are verified, traced, and remembered.

## Canonical source of truth

P1.5.10X establishes `AurelTraceLog` as the only canonical append-only hash-chained event source of truth.

Ledger, Evidence, RuntimeState, Evaluation, Mneme, Shell and Reports are projections over `AurelTraceLog`, not independent truth sources. If an event is not represented in `AurelTraceLog`, it is not canonical.

`trace_id` is a stable run/workflow identity, not a content-address. `event_hash` is content-addressed from canonical event content. Future replay reports and causal graphs may introduce their own content-addressed hashes over canonical trace events.

## Module map

| Module | Role |
|--------|------|
| `entity.py` | Cognitive organism: plan → execute loop, state machine outcomes |
| `runtime.py` | Governed command pipeline kernel |
| `policy.py` | Capability / permission / authority gates + risk re-score |
| `policy_cards/` | P1.6.0 Policy Card Foundation, P1.6.1 Policy Card Schema v1, P1.6.2 Behavioral Contract Schema v1, P1.6.3 Risk Tier Policy Card Model v1, P1.6.4 Human Oversight Policy Card Model v1, P1.6.5 Data Residency Policy Card Model v1, P1.6.6 Tool Permission Policy Card Model v1, P1.6.7 Memory Write Policy Card Model v1, P1.6.8 Prompt Policy Card Model v1: first-class typed/frozen/validated/hashable governance objects; Policy Cards define rules, Behavioral Contracts define how subjects must behave, Risk Tier Policy Cards define R0-R6 risk semantics, Human Oversight Policy Cards define human/operator oversight semantics, Data Residency Policy Cards define data locality/egress/exposure semantics, Tool Permission Policy Cards define deny-by-default tool permission semantics, Memory Write Policy Cards define deny-by-default memory write semantics (zones, write types, decisions, verification statuses, retention classes, requirements), Prompt Policy Cards define strict prompt trust/instruction-boundary semantics (sources, trust levels, roles, decisions, injection-risk vocabulary, boundary requirements); centralized schema versioning, field classifications, deterministic schema export; schema-driven closed-world validation. **P1.6.9 Sandbox Policy Card Model v1** adds backend/filesystem/egress/command-class sandbox semantics with a resolver-ready `evaluate_sandbox_policy_decision()`. **P1.6.10 Custos v0 Policy Runtime Resolver (shadow mode)** (`resolution_context.py`, `resolution_result.py`, `resolver.py`) interprets these cards into a single deterministic `ResolvedPolicySet` with `WOULD_*` shadow outcomes via strictest-wins MVP aggregation — it does NOT enforce, does NOT modify `AgenticRuntime.submit()`, and runs SHADOW-only. **P1.6.11 Policy Resolution Context & Registry Binding** (`registry.py`, `context_binding.py`, `risk_mapping.py`) adds deterministic explicit registry selection, context assembly, conservative risk mapping, and resolver-from-registry invocation. **P1.6.12 Custos Shadow Runtime Projection** (`runtime_projection.py` plus an optional `AgenticRuntime.submit()` hook) can attach deterministic shadow comparison metadata to `ObservationEnvelope.artifacts["policy_shadow_projection"]`; it is observability-only, default-disabled, requires an explicit registry, and never enforces policy-card outcomes. **P1.6.13 Policy Conflict Algebra & Strictest-Wins Rules** (`conflict_algebra.py`) adds deterministic conflict detection/ranking/classification/resolution of Custos shadow policy decisions with 6 enums, 6 frozen dataclasses, specificity scoring, and SHA-256 hashing; conflict metadata is attached to `ResolvedPolicySet` as optional backwards-compatible fields. **P1.6.14 Policy Resolution Trace Hook** (`resolution_trace.py`) adds trace-compatible evidence envelope (`PolicyResolutionTraceEvent`, `PolicyResolutionTraceEnvelope`, `PolicyResolutionEvidenceRef`, `PolicyTraceBinding`) with deterministic hash/identifier for audit-readiness; no Ledger write, no enforcement. **P1.6.15 Policy Violation Trace Hook** (`violation_trace.py`) adds shadow violation evidence (`PolicyViolationTraceEvent`, classification, binding to resolution trace and projection metadata); records mismatch/drift/incompleteness candidates without enforcement or Ledger writes. **P1.6.16 Policy Test Harness** (`test_harness.py`) adds deterministic scenario cases, expected-vs-actual comparison, suite runner, and hashed reports over the Custos shadow stack; validates shadow governance without enforcement. **P1.6.17 Policy Projection/API/Event Contract** (`projection_contract.py`) adds versioned read-model contract with source labels (LIVE, TRACE_VERIFIED, SIMULATED, DEV_FIXTURE, UNAVAILABLE, ERROR), readiness flags, deterministic projection hash, and event payload seed; reports backend capability truth without enforcement; CLI/Shell bindings explicitly UNAVAILABLE until P1.6.18. Still no active policy-card enforcement/approval-workflow/egress-guard/tool-gateway/memory-engine/prompt-compiler/enforcement-adapter |
| `hitl.py` | Approval gates: auto, console, deny-all, preview-only |
| `approval.py` | Approval contracts, risk classes, policy resolver, previews (P0.15) |
| `budget.py` | Resource limits and budget ledger |
| `sandbox.py` | Workspace isolation backends (unsafe local, bwrap, docker) |
| `sandbox_policy.py` | Sandbox profiles, policy, path enforcement, diagnostics (P0.17) |
| `tools.py` | Tool Bus v1: registry/spec/metadata/context/result/error + dispatch |
| `tool_contracts.py` | Input/output schema contracts (P0.10) |
| `verifier.py` | Post-state verification + test integrity |
| `trace.py` | Hash-chained audit ledger (in-memory + persistent) |
| `aurel_trace/` | P5-TRACE-A AurelTrace Spine foundation package (P5.0–P5.4): an adapter and structured hash-verification layer *over* the existing `trace.py` ledger — **not a second trace source of truth**. Imports downward only (from `trace`/`core_types`), adds no ledger/persistence, iterates ledgers read-only, and reuses the ledger's own `sha`/`canonical_json`/`GENESIS`. `trace_hash.py` (shared primitives; `TraceTruthLabel` with **no TRACE_VERIFIED member** — strongest mintable label is `TRACE_INTEGRITY_VERIFIED`; `TraceIntegrityStatus`; deterministic `TraceHashMaterial`; timestamps excluded from hash material), `trace_inventory.py` (`ExistingTraceInventory` cataloguing both trace systems — the operational `trace.py` ledger's nine `core_types` record types + `InMemory`/`Persistent` backends as the P5-A target, and the separate `contracts.trace.AurelTraceLog` canonical event form reported unsupported/deferred with its pre-existing `TraceEventRef`/`TraceBindingRef` naming overlap noted), `trace_doctrine.py` (`AurelTraceDoctrine` with locked machine-checked booleans forbidding duplicate-spine/execution/authorization/semantic-correctness/replay/rust-wasm/shell-ui/api/event-bus/p9-enforcement and requiring trace_verified_requires_verification), `trace_envelope.py` (`CanonicalTraceEventEnvelope` wrapping supported records read-only and deterministically, TRACE_BOUND and unconstructible as INTEGRITY_VERIFIED; strict adapter raises `TraceEnvelopeUnsupportedError`, lenient reports — unsupported records never silently pass; `envelopes_from_ledger` read-only), `trace_refs.py` (`TraceRunRef`/`TraceEntryRef`/`TraceEventRef`/`TraceBindingRef` — stable same-record→same-ref, `TraceBindingRef` cannot claim verification), `trace_verify.py` (`TraceHashVerificationRequest`/`Result`/`TraceHashFinding` + `HashChainVerificationSummary`; `verify_canonical_trace_hash_chain` over FULL_CHAIN/SEGMENT/SINGLE_ENTRY/CHAIN_HEAD returning status+counts+findings+chain head — valid→PASS `TRACE_INTEGRITY_VERIFIED` unconstructible when invalid, broken→FAIL with BROKEN_PREVIOUS_HASH/ENTRY_HASH_MISMATCH/CHAIN_HEAD_MISMATCH, unsupported→PARTIAL, empty→UNAVAILABLE; no auto-repair). A record can be TRACE_BOUND; a supported chain can be TRACE_INTEGRITY_VERIFIED; neither means semantic/business correctness, authority, replay, or production compliance. Existing `trace.py` remains the current ledger — P5-TRACE-A adapts and verifies, it does not replace. Not re-exported from the `agentic_runtime` top level. Deferred to P5-TRACE-B: verification receipts/checkpoints, schema registry/upcasting, submit coverage audit |
| `contracts/` | Canonical trace/projection/evidence/verifier/context/capability contracts: `AurelTraceLog`, immutable `TraceEvent`, `TraceEventRef`, `TraceBindingRef`, `EvidenceRef`, `VerifierResult`, `ContextBindingRef`, `ContextAdequacyReport`, verified capability evidence invariants |
| `golden_threads/` | P1.5.11A/B deterministic vertical contract harnesses; Golden Thread A proves Intent → ContextBindingRef → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → ContextAdequacyReport → CapabilityEvidence without real execution |
| `memory.py` | Multi-tier memory fabric |
| `memory_governance.py` | Memory write governance + promotion (P0.9) |
| `skills.py` | Skill compilation and reflex promotion |
| `plan_validator.py` | Strict plan validation before execution |
| `model_router.py` | Swappable model client routing (mock default); P1.1 config bundle support |
| `model_config.py` | Centralized provider/model profiles and runtime policy (P1.1) |
| `secrets.py` | Env-only secret resolution and redaction boundary (P1.1) |
| `prompt_system.py` | Prompt manifests, registry, policy validation, rendering, and trace-safe summaries (P1.2) |
| `tool_manifest/` | Tool / plugin manifest domain models, validation, loader, registry, quarantine, invocation drafts, lifecycle events, research metadata (P1.3.0–P1.3.7) |
| `evaluation/` | P1.5 Evaluation Mirror foundation: domains, subjects, scopes, criteria, run envelopes (P1.5.0) — **not** full P4 Evaluation Mirror |
| `identity/` | P1.4 identity trust surface: kernel/persona/operator/modes/context/card/autonomy/claim-boundary/doctrine/source-attestation/authority-delta/operator-consent/lifecycle/trust-evidence/seal-readiness/exit-seal/identity-cli-surface modules; P1.4.20 provides final exit seal (SEALED_WITH_LIMITATIONS) |
| `autonomy/` | P1.4 autonomy layer placeholder (P1.4.0) — **not** Autonomy Scale yet |
| `governance/` | P1.4 constitutional floor / profiles placeholder (P1.4.0) |
| `heretic/` | P1.4 heretic mode placeholder (P1.4.0) — cognitive freedom bounds only in docs |
| `metacognition/` | P1.4 self-model / drift hooks placeholder (P1.4.0) |
| `compliance/` | P1.4 regulatory registry placeholder (P1.4.0) |
| `model_providers/` | Optional structured-plan providers (mock/openai/anthropic/ollama) |
| `repo_agent.py` | Bounded repository task loop: context → deterministic/LLM plan → validation → patch → test → report |
| `demo_harness.py` | P0.20 demo harness: scenarios, factory, runner, honest reports, evidence writer (P0.19/P0.20) |
| `praxis.py` | Praxis memory metabolism seed: experience → candidates → promotion gates (P0.16) |
| `state_machine.py` | Execution status transitions |
| `status.py` | Lightweight runtime diagnostics |
| `cli.py` | Minimal CLI (`status`, `demo`, `verify`, `repo-task`, `approve-demo`, `praxis-*`, `sandbox-status`, `demo-harness`, `config`, `models`, `providers`, `prompts`, `policy`, `shell`, `flow` (P3.7 read-only AurelFlow projection inspect: `demo`/`inspect`/`timeline`/`wiring`/`protocol`/`seal`; executes nothing), `identity doctrine`, `identity attestation`, `identity authority-delta`, `identity consent`, `identity seal-readiness`) |
| `cli_modules/policy_commands.py` | P1.6.18 read-only policy projection CLI (`policy status`, `policy projection`, `policy unavailable`, `policy harness list/run`) consuming `PolicyProjectionContract v1` |
| `cli_modules/shell_commands.py` | P2.10-D read-only Shell terminal CLI (`shell status`, `shell clients`, `shell surfaces`, `shell parity`, `shell evidence`, `shell run-modes`, `shell export-json`) consuming `TerminalShellReadModel`; no execution, approvals, runtime control, sandbox control, memory writes, policy mutation, identity mutation, Shell LIVE, full terminal automation, or full TUI product |
| `aurel_shell/` | P2 AurelShell contract package: P2.0-A seven-surface registry, P2.0-B navigation/boundary contracts, P2.0-C continuity contracts, P2.0-D truth label / permission meaning / unavailable-state / fixture disclosure contracts, P2.0-E operator demo / multi-client consistency / shell snapshot / route regression harness / readiness contracts, P2.0-F projection/API/event/CLI/exit-seal contracts, P2.1-A through P2.1-D global topbar/readiness contracts, P2.2-A through P2.2-D per-surface local navigation / section-seal contracts, P2.3-A workspace state foundation contracts in `workspace_state.py`, P2.3-B focus/stack/group/restore semantics in `workspace_window_semantics.py`, P2.3-C cross-surface handoff/docking/conflict/compatibility semantics in `workspace_window_cross_surface.py`, P2.3-D workspace window section projection / binding / readiness / seal contracts in `workspace_window_section_projection.py`, P2.4-A command palette / global commands foundation contracts in `global_command_registry.py`, P2.4-B command discovery/result-set read model in `global_command_discovery.py`, P2.4-C command proposal/no-execution boundary in `global_command_proposal.py`, P2.4-D command section projection / UNAVAILABLE binding / readiness / seal contracts in `global_command_section_projection.py`, P2.5-A cross-surface handoff foundation contracts in `cross_surface_handoff.py`, P2.5-B handoff context / continuity / conflict / availability read-model contracts in `cross_surface_handoff_context.py`, and P2.10-E multi-client demo seal contracts in `multi_client_demo_seal.py`. Contract/read-model/evidence-seal only; no live UI, product readiness, final P2 seal, P3 handoff, storage, route runtime, command execution/router/handler, permission enforcement, API server, event bus, runtime event emission, auth/session backend, Custos/Mneme integration, trace verification, memory writes, tool execution, or workflow execution |
| `aurel_flow/` | P3-FLOW-A AurelFlow runtime foundation package (opened by explicit operator override; P2.11-D–P2.20 deferred): `workflow_graph.py` declarative graph contracts + closed-world fail-closed validation + graph read model, `workflow_state.py` immutable workflow run / lifecycle / node state with safe transition maps and deterministic snapshots (in-memory only, UNAVAILABLE_PERSISTENCE), `scheduler.py` pure ready-queue calculation + scheduler decisions with explicit READY/WAITING_DEPENDENCY/WAITING_APPROVAL/BLOCKED/COMPLETED/FAILED/SKIPPED/UNAVAILABLE/ERROR reasons, `read_model.py` flow runtime foundation read model with all-false no-execution proof and UNAVAILABLE capability declarations, `demo.py` DEV_FIXTURE operator demos, `types.py`/`errors.py` canonical serialization/hash + structured fail-closed errors. P3-FLOW-B behavior loop adds `runtime_events.py` (local runtime events with parent/correlation/caused-by/affected-node relations, immutable streams, deterministic snapshots, RuntimeEvent-is-not-TraceEvent boundary), `state_commitment.py` (mediated actor outputs + internal-only COMMITTED_INTERNAL state commitments), `pause_resume.py` (explicit pause reasons, operator decision signals without authority/execution permission, internal resume/stop/reject via the safe transition maps, responsibility transfer frames without authority transfer), `recovery.py` (failure classification + graph-derived propagation risk, retry eligibility / recovery proposals / rollback candidates without execution), and `runtime_behavior_read_model.py` (aggregate behavior read model with UNAVAILABLE boundaries + all-false no-execution proof). P3-FLOW-C projection/seal layer adds `flow_projection.py` (actual-code inventory with fail-closed integration booleans, read-only FlowStateProjection, commitment/mediated-output/responsibility/pause/failure-recovery/rollback projections, demo truth projection), `flow_timeline.py` (RuntimeBehaviorTimeline — not AurelTrace; RuntimeEventRelationGraph — not Ledger), `flow_wiring.py` (hot/cold wiring matrix, UNAVAILABLE_PERSISTENCE projection, autonomy visibility A0–A5 with A6/A7 future-only, governance profile), `flow_protocol.py` (versioned schema registry, canonical-JSON/sha256 serialization contract, hybrid-ready compatibility with rust_core_active fail-closed False, ExpandedP3ReadinessMatrix P3.10–P3.20), `flow_observability.py` (local metric frames, no exporter), `flow_seal.py` (FlowBaseExitSeal checking P3.0–P3.9 with honest PASS/PARTIAL/BLOCKED/FAIL/UNAVAILABLE aggregation), and `flow_cli.py` (read-only CLI backend with closed-world command kinds and fail-closed side effects; bound as the `flow` family in `cli.py`). P3-FLOW-D authority/control boundary layer adds `flow_boundary.py` (ExecutionProposalEnvelope / PermissionRequestEnvelope / ExecutionRequestEnvelope with fail-closed granting/dispatching booleans, FlowToSubmitBoundary + SubmitCompatibilityReadModel — runtime.submit not wired and never called, BoundaryTruthReadModel carrying the five boundary laws as fail-closed data, ControlPlaneDataPlaneBoundary + reliability control-plane/recovery-policy/budget boundary seeds — recovery policy proposes but never executes repair, budget requirement is not enforcement), `flow_operator_review.py` (closed-world OperatorReviewDecisionKind with no APPROVE/EXECUTE member, review frames/decisions/continue-stop-reject-rollback candidates that cannot authorize/execute/mutate/rollback, deterministic OperatorReviewReadModel), `flow_pause_hooks.py` (reasoning/verifier/operator/evidence pause hooks — reasoning pause stores a safe category with no chain-of-thought field structurally; verifier pause does not verify; operator pause does not authorize; evidence pause cannot produce evidence), and `flow_proof_expectation.py` (ProofExpectationEnvelope — expectation is not proof, EvidenceRequirement — requirement is not evidence, SemanticSupportExpectation, UnsupportedOutputRisk + SemanticSilentFailureBoundary — missing evidence/unsupported output are failure candidates not warnings). P3-FLOW-E dynamic graph / graph plasticity layer adds `flow_dynamic_graph.py` (WorkflowTemplate/WorkflowTemplateRef reusable design distinct from RealizedRuntimeGraph/RealizedRuntimeGraphRef/RuntimeGraphInstance run-specific realization — `realize_runtime_graph()` is a pure function that validates run.graph_id against the template's source graph and never mutates the template; GraphDeterminationTime anchors realization to a logical run_step, never a wall clock), `flow_topology.py` (RuntimeTopologySnapshot/Node/Edge/Version + TopologySnapshotReadModel — deterministic, read-only, not Trace, not proof, edge type mapped to EdgeReliabilityRole; TopologyVulnerabilityScore/CascadeAmplificationRisk/ErrorPropagationPath/FailureAmplificationFrame/IntermediateVerifierPlacementHint/AggregatorAttenuationFrame/TopologyRiskReadModel — advisory only, naming a verifier/aggregator placement never runs a verifier or creates a live aggregator; AgentDiversitySignal/TrainingOverlapRisk/ErrorCorrelationRisk/RedundancyIllusionWarning/ArchitecturalDiversityRequirement/DiversityRequirementFrame/DiversityRiskReadModel — RedundancyIllusionWarning structurally forbids majority_vote_reliable=True unless diversity_proven=True; DecompositionWorthinessSignal/CommunicationOverheadEstimate/AgentSplitRiskHint/SubtaskDimensionalityReductionHint — hints only, never scheduling or spawning), and `flow_graph_revision.py` (closed-world GraphPlasticityMode where STATIC_LOCKED/TEMPLATE_REALIZED_ONCE block revision proposals outright, GraphPlasticityPolicy/GraphPlasticityBoundary, RuntimeGraphRevisionProposal/Decision/Reason/ReadModel with closed-world GraphRevisionCandidateKind and GraphRevisionDecisionKind — no EXECUTE/DISPATCH/APPLY_LIVE/APPROVE/AUTHORIZE member, EdgeAddCandidate/EdgePruneCandidate/EdgeReweightCandidate — candidate construction never mutates the source snapshot's edges). P3-FLOW-F reversible runtime state layer adds `flow_checkpoint.py` (RuntimeCheckpointRef/Kind/Reason/Boundary + closed-world CheckpointTruthLabel with no LIVE/TRACE_VERIFIED member — a checkpoint names a runtime state point anchored to the run's step counter; CheckpointStateEnvelope + RuntimeCheckpointSnapshot/Ref/ReadModel bind run/event-stream/commitments/realized-graph/topology-version with fail-closed run-lineage validation — snapshot is not storage, not Trace, not proof; CheckpointSerializationContract with no database/event-store backend), `flow_replay.py` (RuntimeForkCandidate/Reason/Boundary/SafetyFrame/ReadModel — fork is a conceptual branch, worker_spawned/external_state_duplicated fail-closed False; RuntimeReplayPlan with enumerated ReplayStepRefs + closed-world ReplayAvailability with no EXECUTABLE member + RuntimeReplayCursor as a bounds-checked read-model marker, never a worker cursor + ReplayBoundary/ReadModel; CounterfactualReplayCandidate structurally counterfactual=True/actual_history=False with SIMULATED label + CounterfactualBranchReason/ComparisonFrame/TruthBoundary/ReadModel), `flow_reversible_state.py` (RuntimeRevertCandidate — safe_to_execute/rollback_executed/external_state_reverted fail-closed False, requires operator review + P4 + P5 + P9 fail-closed True; RollbackExecutionBoundary/RevertSafetyFrame/RollbackAuthorityRequirement/RevertReadModel; RuntimeStateDiffSummary via deterministic sorted set arithmetic + Checkpoint/Topology/EventStream/Commitment diff frames + DiffReadModel/DiffTruthBoundary — diff is not proof/replay/rollback; RecoveryCheckpointRequirement + PreRecoveryCheckpointRef/PostRecoveryComparisonFrame/RecoveryStatePreservationFrame/RecoveryCheckpointBoundary/ReadModel — pre-recovery checkpoint discipline for P3-FLOW-G, comparison expectation is not verification, recovery never executes), and `flow_reversible_projection.py` (ReversibleStateProjectionEnvelope + 9 projection-only view models with UI replay/rollback buttons structurally non-executing, ReactProjectionBoundary, PythonRuntimeSourceOfTruth enforcing runtime_source_of_truth=="python", HybridSerializationContract without API server or generated schema tooling, ReversibleStateMigrationReadiness + MigrationProjectionReadinessMatrix + ProjectionCompatibilityReadModel). P3-FLOW-G reliability control plane layer adds `flow_reliability_control.py` (ReliabilityControlPlane/State/ReadModel with checkpoint/budget/operator-review/P4/P5/P9 gates fail-closed True; SelfHealingControlLawBoundary — renamed from the dispatch's ReliabilityControlPlaneBoundary because the P3-FLOW-D seed of that name in flow_boundary.py is preserved; closed-world ControlLoopPhase with no RECOVERED/HEALED/VERIFIED member; ControlLoopTransition must change phase; MonitorFrame -> DetectionFrame -> DiagnosisFrame -> RecoverFrame proposes-only -> VerifyExpectationFrame expects-only + DiagnosticLoopState/ReadModel), `flow_diagnosis.py` (closed-world 22-member RuntimeFailureKind incl. semantic silent failure/unsupported output/evidence missing/retry storm/no progress/topology amplification/diversity correlation/checkpoint-required-missing; deterministic total classification table -> FailureClassificationFrame/ReadModel — classification is not proof; RootCauseDiagnosis with closed-world DiagnosisConfidence (no CERTAIN/PROVEN/VERIFIED member) where low confidence structurally forces human review; DiagnosisEvidenceRef never retrieves; DiagnosisUncertaintyFrame; semantic signals are failure candidates with is_harmless_warning fail-closed False; EvidenceSupportRequirement/ContradictionCheckRequirement retrieve and run nothing; SemanticFailureReadModel), `flow_recovery_policy.py` (TargetedRecoveryPolicy fail-closes unless total over the taxonomy — no blind retry; DEFAULT_TARGETED_RECOVERY_POLICY with the exact dispatch failure->candidate mapping; closed-world RecoveryCandidateKind with no EXECUTED/APPLIED/COMPLETED member; RecoveryCandidateSelection is not execution; RecoveryCandidateEnvelope binds a P3-FLOW-F RecoveryCheckpointRequirement — auto-derived when absent — with RecoveryExecutionRequirement/RecoveryVerificationRequirement; RecoveryCandidateBoundary/ReadModel + RecoveryPolicyReadModel), `flow_recovery_budget.py` (RecoveryBudget aggregating attempt/latency-steps/cost/depth sub-budgets — budget availability is not permission; RecoveryBudgetState/ExhaustedSignal — exhaustion visible per dimension, only representable from a truly exhausted state, degradation never auto-authorized; RetryStormGuard/NoProgressGuard structurally cannot be constructed unblocked at limit and never execute stop; ControlLoopCollapseSignal; LoopHealthSignal with COLLAPSED>STORMING>STALLED>DEGRADING>HEALTHY precedence; LoopSafetyReadModel; GracefulDegradationFrame visible with failure_hidden unconstructible; HumanEscalationFrame escalation-is-not-approval; EscalationReason/ReadModel), and `flow_self_healing_projection.py` (SelfHealingProjectionEnvelope + DiagnosticTimeline/FailureCard/RecoveryCandidate/RecoveryBudget/VerificationExpectation/Escalation view models all react_projection_only with ui_recovery_execution/ui_authority/api_server/frontend fail-closed False; ReliabilityControlReactProjectionBoundary pinning Python-runtime-source-of-truth and UI-retry-button-is-not-recovery-execution). P3-FLOW-H governed autonomy layer adds `flow_autonomy.py` (closed-world GovernedAutonomyLevel A0-A9 with A9 heretic live mode locked unavailable — named GovernedAutonomyLevel because FlowAutonomyLevel (C-pack visibility) and identity AutonomyLevel already exist; OperatorSelectedAutonomyMode with explicit AutonomyModeSource and self_selected/self_upgrade_allowed structurally False; total deterministic resolve_permission_state over all level x decision-class pairs via rules + hard overrides — side-effect classes FORBIDDEN_IN_P3 future-bound P4+P9, proof/authority requests future-bound P5/P9, A9 never ALLOWED_*, unknown raw input fails closed, monotone over the tier ladder; resolve_action_boundary wrapper), `flow_autonomy_scope.py` (16-dimension AutonomyScopeEnvelope — scope limits, never authorizes or executes), `flow_autonomy_gates.py` (deterministic gate ladder over budget/storm/no-progress/risk/reversibility with FREEZE/DOWNGRADE/HOLD/BLOCK/REQUIRE_* outcomes that never execute; candidate-only downgrade/freeze/resume/escalation where a downgrade must strictly lower the tier; self-upgrade drift/violation signals via detect_self_upgrade_violation — review need, never enforcement; OperatorAutonomyOverrideCandidate future-bound to P9 when raising autonomy), and `flow_autonomy_projection.py` (read-only GovernedAutonomyProjection with live resolver posture summary; UI toggle/override/execution authority structurally False). P3-FLOW-I scheduling-intent layer adds `flow_scheduling_intent.py` (WorkflowAtomicUnit/Ref/Boundary/ReadModel — closed-world WorkflowAtomicUnitKind with no WORKER_JOB member, candidate_only fail-closed True, worker_job/dispatch/execution fail-closed False, self-dependency unconstructible; SchedulingIntent/Kind/Reason/Boundary/ReadModel — no dispatch verb, queued/dispatched fail-closed False, requires_p4_dispatch fail-closed True, HOLD/BLOCK force operator review; SchedulingScopeCheck fails closed without an envelope, SchedulingActionBoundaryCheck wraps the H resolver verbatim, evaluate_autonomy_scheduling_gate deterministic ladder BLOCK > REQUIRE_P9_AUTHORITY > HOLD > REQUIRE_OPERATOR_REVIEW > ALLOW_SCHEDULING_CANDIDATE that can never out-allow H, SchedulingAutonomyDecision with no DISPATCH/EXECUTE/APPROVE/AUTHORIZE member, SchedulingGateReadModel), `flow_dispatchability.py` (ReadyStateFrame with policy/proof/execution readiness structurally unavailable; deterministic total classify_dispatchability — every blocking dimension yields its own DispatchabilityReason, guards outrank readiness, fully ready is only a READY_BUT_NO_P4 candidate; DispatchabilityReadModel; QueuePlacementCandidate via a total mapping over all dispatchability reasons — queue_candidate_only True, actual_queue_inserted/worker_assigned False; QueuePlacementBoundary/ReadModel; DependencyWindow/ConcurrencyWindow/ParallelismCandidate/ConcurrencyBoundary/ReadModel — disjoint safe/unsafe parallel sets, no worker spawn), `flow_resource_prediction.py` (16-dimension ResourceDimension; ResourcePredictionFrame/RequirementEstimate/PressureSignal/AvailabilityBoundary/ReadModel — allocated/reserved/measured/permission fail-closed False; Cost/Latency/TokenBudget/ContextWindow estimates with billing/token/measured/proof fail-closed False, exceeds_budget forces operator review, closed-world EstimateConfidence with no MEASURED/PROVEN member; SchedulingEstimateReadModel; Model/Tool/Sandbox/DataAccess requirement frames — requirement is not invocation, requires_p4_execution/requires_p9_authority fail-closed True; ExecutionResourceRequirementReadModel), and `flow_scheduling_projection.py` (SchedulingProjectionEnvelope + Timeline/Intent/ResourcePrediction/Dispatchability/QueueCandidate/ConcurrencyWindow view models all react_projection_only with UI schedule/queue/dispatch/api-server/frontend booleans fail-closed False; SchedulingReactProjectionBoundary enforcing Python source of truth; NoDispatch/NoExecution/NoResourceAllocation proofs explicitly is_p5_trace_proof=False). P3-FLOW-J compound-topology layer adds `flow_compound_topology.py` (CompoundRuntimeTopology topology map — deterministic service-kind counts, duplicate-ref rejection, service runtime/discovery/transport/dispatch/execution fail-closed False; one LogicalServiceRef contract over closed-world RuntimeServiceKind instead of eight ref classes — invocation-bound kinds structurally future-bound to P4+P9, verifier/trace to P5; RuntimeServiceNode is not a live process), `flow_service_topology.py` (candidate-only ServiceCapabilityEnvelope where invocation-bound capabilities force P4+P9 futures; deterministic ServiceDependencyGraph with topology-membership validation and declared-cycle DFS — an edge is never transport; ServiceRoutingCandidate routing_candidate_only with the P9 future inherited from its ref), `flow_interop_topology.py` (InteroperabilityLayerRef over six layer kinds naming future owners P4/P5/P9/Shell — discovery/routing/execution/security/observability unconstructible True; assess_topology_health deterministic declared-contract diagnosis — empty topology/cycle/unknown-boundary/capability-missing signals, never probe, never proof; FailureContainmentBoundary executes nothing; bridge_scheduling_requirements consuming the I ExecutionResourceRequirementReadModel + AutonomySchedulingGate as-is — requirement match is not invocation, service match is not routing; P4HandoffClarityFrame naming consumable refs, convertible candidates, source I read models, and the full deliberately-absent runtime system list — truncated list unconstructible), and `flow_compound_topology_projection.py` (one read-only CompoundTopologyProjection with UI route/invocation/mesh-control booleans fail-closed False). P3-FLOW-K evaluation layer adds `flow_harness_evaluation.py` (deterministic harness suite/case + derive_harness_evaluation_run as a pure function of the suite — never workflow execution; closed-world 20-area × 6-status contract coverage matrix where MISSING/BLOCKED must explain themselves; HarnessScenarioFixture structurally DEV_FIXTURE with catalog/read model), `flow_boundary_probes.py` (run_boundary_compliance_probe over 17 categories via category→forbidden-attribute maps + LIVE/TRACE_VERIFIED truth-label checks — PASS/FAIL/honest NOT_APPLICABLE, FAIL requires findings, enforcement/mutation/punishment unconstructible; probe_runtime_invariant encoding 18 AurelFlow laws as deterministic attribute checks — findings never repair or rewrite), `flow_quality_ops.py` (advisory RuntimeQualityScorecard with no APPROVED/RELEASED status member; report-only RuntimeRegressionGuardRail with FAIL>WARNING>PASS ladder and ci_enforced/git_blocked unconstructible; P4HandoffReadinessAssessment where an unsatisfied check without a gap is unconstructible and readiness stays candidate-only), and `flow_harness_projection.py` (HarnessEvaluationProjectionEnvelope + 7 view models sharing a UI-powerlessness base; HarnessEvaluationReactProjectionBoundary pinning score-is-not-approval and Python source of truth; build_p3_seal_input_frame deriving readiness findings/blocking risks deterministically with seal-ready-with-risks unconstructible, requires_p3_flow_l fail-closed True, final_seal_performed fail-closed False; Harness-prefixed no-execution/no-proof/no-production-claim proofs + P4ReadinessNotP4Proof, all is_p5_trace_proof=False). P3-FLOW-L domain-seal layer adds `flow_domain_seal.py` (closed-world 12-pack P3FlowPack A-L coverage summary with no PROVEN status member — absent/duplicate packs unconstructible, items must explain themselves; summarize_k_evaluation consuming the K seal input as-is with evaluation-is-proof/score-approves-release unconstructible; seal_p3_domain fail-closed final control-plane seal — blocking coverage statuses or K blocking risks reject sealing, p3_control_plane_sealed unconstructible False, 15 production/proof/authority/P4-P5-P9/submit/execution/persistence booleans unconstructible True), `flow_p3_audit.py` (11-category truth-label audit with named offenders and honest NOT_APPLICABLE; total 19-system UnavailableSystemsLedger with structurally UNAVAILABLE entries naming reason + future owner; read-only 20-category boundary exit audit via forbidden-attribute maps — never enforcement), `flow_p4_handoff.py` (13-surface P4ExecutionHandoffPackage total over the surface enum — not P4; candidate-only ExecutionRequestCandidateSurface — a candidate is not a request; RuntimeSubmitBoundaryMap whose status vocabulary has no WIRED member and whose primary status is structurally future-bound with all five P4/P9/P5/operator/persistence requirements mandatory), and `flow_seal_projection.py` (4 read-only seal view models + React boundary pinning seal-badge-is-not-production-readiness and Python source of truth + envelope recommending P4-EXEC-A). Local runtime substrate/behavior/projection/boundary-grammar/topology/reversible-state/reliability-control/governed-autonomy/scheduling-intent/compound-topology/harness-evaluation/domain-seal layer only; scheduler decides readiness and never executes; AurelFlow records/pauses/proposes/marks/projects/seals/requests-permission/expects-proof/realizes-graphs/snapshots-topology/proposes-revisions/scores-risk/names-checkpoints/plans-replay/compares-state but cannot execute, authorize, persist externally, or prove; projection is not execution, inspection is not authority, seal is not TRACE_VERIFIED, proposal is not permission, proof expectation is not proof, template is not realized graph, topology snapshot is not Trace, graph revision is not execution/authority, topology risk is advisory not proof, majority voting is not reliability without proven diversity, checkpoint is not persistence, snapshot is not proof, fork is not execution, replay plan is not replay execution, counterfactual is not history, rollback candidate is not rollback, diff is not proof, recovery requirement is not recovery, a detection is not a fix, a diagnosis is not proof, a recovery candidate is not recovery execution, a budget check is not permission, a loop guard is not stop execution, a verification expectation is not verification, an escalation is not approval, an autonomy level is not authority, a scope envelope is not permission, a gate decision is not execution, Aurel never self-upgrades, an operator override candidate is not Custos authorization, a scheduling intent is not dispatch, an atomic unit is not a worker job, ready is not dispatchable, a resource prediction is not allocation, an estimate is not billing or proof, a queue candidate is not queued work, a concurrency window is not worker spawn, a model/tool/sandbox/data requirement is not invocation, an autonomy-gated scheduling decision is not authority, a compound topology is not a service mesh, a service ref is not a live endpoint, a runtime service node is not a live process, a capability envelope is not permission, a dependency edge is not transport, a routing candidate is not network routing, an interoperability layer ref is not a live protocol, a topology health frame is not proof, a P4 handoff frame is not P4 execution, an evaluation run is not workflow execution, a harness result is not proof, a coverage matrix is not production readiness, a boundary probe is not enforcement, an invariant finding is not repair, a quality score is not approval, a regression guard is not CI enforcement, a P4 readiness assessment is not P4, a P3 seal input is not the final seal, a domain seal is not production readiness or release approval, a coverage summary is not proof, a truth-label audit is not Trace verification, an unavailable ledger is not implementation, a boundary exit audit is not enforcement, a P4 handoff package is not P4, an execution request candidate is not an execution request, a runtime.submit boundary map is not runtime.submit wiring, Python is source of truth and React is projection only; no tool/command/subprocess/network/sandbox execution, worker/agent dispatch, worker fork, approval authority, retry/recovery/rollback execution, replay execution, Runtime.submit bridge, ApprovalGate/HITL bridge, hidden chain-of-thought capture, verifier/aggregator execution, agent spawning, persistence backend, database/event store, React/frontend/API implementation, memory/policy/identity mutation, global Trace/Ledger write, Rust/Go migration, LIVE, or TRACE_VERIFIED |
| `aurel_exec/` | P4-EXEC-A AurelExec execution kernel foundation package (P4.0–P4.3; admission and lease eligibility only — the gate and the key without the key being turned): `exec_types.py` P4 doctrine lock + closed-world contract types (`AUREL_EXEC_CONTRACT_VERSION`; `ExecTruthLabel` with LIVE unassignable at construction and no TRACE_VERIFIED member; `ExecAdmissionState`; `ExecLifecycleState` with no RUNNING/EXECUTED/COMPLETED member; `ExecutionMode`/`ExecutionTopologyKind`/`ExecutionPlasticityLevel`/`ExecutionFailureClass`/`RecoveryActionKind`/`AlgedonicSignalKind` future-pack vocabularies; `TraceBindingStatus` and `ExecTraceStatus` with no BOUND/VERIFIED member; `ExecPolicyStatus`/`ExecCustosStatus` with no ENFORCED/AUTHORIZED member; canonical serialization/hash reused from `aurel_flow.types`), `exec_errors.py` structured fail-closed error codes, `exec_admission.py` (`ExecAdmissionRequest` P3-like candidate contract constructible-with-gaps so gates can reject deterministically; `decide_admission` pure eight-gate NCF chain — source validity → READY_BUT_NO_P4 readiness marker → authority ref → sandbox profile → budget ref → verifier requirement → trace-binding availability → policy/Custos availability — first non-ADMIT gate locks the outcome, non-ADMIT decisions must carry missing requirements, every decision carries unavailable reasons naming P4-EXEC-B/P5/P9 owners; ADMIT is structurally not authorization), `exec_lease.py` (`ExecutionLease`/`LeaseScope`/`LeaseValidationResult` — ADMIT-only issuance, mode/tool/args-hash/sandbox/budget/authority/policy scope binding, deterministic logical-tick expiry, frozen-replace revocation, valid-while-expired/revoked unconstructible; lease is not execution), `exec_job.py` (ADMIT-only minimal `ExecJob` + `ExecutionAttempt` skeleton proving lease-before-attempt — expired/revoked/job-mismatched leases deny attempts fail-closed; `runtime_submit_called=True` unconstructible), and `exec_projection.py` (read-only `ExecProjection` with runtime.submit/trace/policy availability structurally False; `NoRuntimeSubmitProof`/`NoRawExecutionProof`/`NoTraceVerifiedProof`/`NoCustosEnforcementProof` fail-closed boundary proofs; `P4ExecAHandoffFrame` pinning the minimal future bridge chain ExecJob→ExecutionLease→ExecutionAttempt→CommandEnvelope→AgenticRuntime.submit()→ExecutionOutcome with truncation unconstructible). P4-EXEC-B first governed runtime submit bridge adds `exec_session.py` (minimal `ExecutionSession` OPEN/RUNNING/CLOSED/FAILED/ERROR with tick-window consistency — structurally not a workflow/queue/worker/checkpoint; required for submit; `open_execution_session`/`mark_session_running`/`close_execution_session`/`mark_session_failed`/`bind_session_to_job`), `exec_runtime_bridge.py` (`ExecRuntimeBridge` supervising the existing `AgenticRuntime.submit(cmd, card)` kernel — never a second executor; the kernel reference is sanctioned in exactly this module, TYPE_CHECKING-only, sweep-enforced; deterministic pre-kernel guard ladder mode/tool support → request/object coherence → lease validity + scope match incl. bound args hash → active session → submit-eligible states → no resubmit; builds repo-standard `CommandEnvelope.make` and submits exactly once on the read-only TOOL/`read_file` path; `RuntimeBridgeSubmitRequest`/`RuntimeBridgeSubmitResult`/`RuntimeBridgeExecution` with submitted⟺called structural; `RuntimeSubmitProof` from real results only, `NoDirectDispatchProof`, `UnsupportedExecutionModeProof` total over non-TOOL modes), `exec_outcome.py` (deterministic `ExecutionOutcome` normalization — success = observation ∧ state-verifier with structural status agreement, failures preserved honestly, `semantic_success`/`trace_verified` unconstructibly True), and `exec_trace_binding.py` (`ExecTraceBinding` — TRACE_BOUND only from the kernel's real `StateTransitionRecord` refs; trace_verified structurally False, p5_required structurally True); `exec_types.py` gained the 12-member submit-aware lifecycle with total job/attempt transition maps and the TRACE_BOUND label; `exec_job.py` gained lifecycle-capable `ExecJob`/submit-aware `ExecutionAttempt` (claimed-but-unperformed submit unconstructible; resubmit refused); `ExecProjection` gained session/attempt/outcome/submit/trace-bound state with submit availability claimable only on actual call evidence and worker/queue/bus/checkpoint/recovery structurally False. Execution crosses only through the existing kernel: no direct tool dispatch, no subprocess/network/raw-filesystem/sandbox/model/verifier invocation from AurelExec, no manual Trace/Ledger write, no manual policy/Custos enforcement, no worker/queue/bus/checkpoint/recovery, no mode profiles beyond read-only TOOL, no persistence, no CLI binding, no Shell/React/API surface; not re-exported from the `agentic_runtime` top level. P4-EXEC-C managed runtime shape layer adds `exec_queue.py` (`ExecQueueEntry` over an 8-state deterministic queue lifecycle — only LEASED/SESSION_BOUND jobs with their own currently valid lease can enter; CLAIMED entries must name their worker slot; schedules_workflows/executes/dispatches_remotely unconstructible — a queue entry is not a scheduler, P3 schedules), `exec_worker.py` (one local IN_PROCESS_LOCAL `WorkerSlot` with is_worker_pool unconstructible and REMOTE/DISTRIBUTED kinds representable only as structurally UNAVAILABLE and claim-incapable; deterministic fail-closed `claim_queue_entry` blocking double claims from both sides plus foreign/expired/revoked leases; `release_worker_slot`/`fail_worker_slot`; `run_claimed_queue_entry_once` managed helper reusing `ExecRuntimeBridge` unchanged — claim-coherence validated fail-closed with zero kernel calls on any block, exactly one governed submit, ordered ATTEMPT_READY→CHECKPOINT_BOUND→ATTEMPT_SUBMITTED→OUTCOME_RECORDED→CHECKPOINT_BOUND→ROLLBACK_REF_CREATED→WORKER_RELEASED causality chain, runtime failure preserved with the worker still released; `ManagedRuntimeResult`/`ManagedRuntimeExecution`; NoWorkerPool/NoRemoteWorker proofs), `exec_messages.py` (13-kind closed-world `ExecutionMessageKind` + immutable `LocalExecutionMessageLog` whose append returns a new log; transport/pubsub/subscriber claims unconstructible; job/session/attempt/queue-entry filters; NoTransportBus proof — a local log is not a bus), `exec_checkpoint.py` (pre/post attempt `ExecutionCheckpointRef` over real local state views with deterministic stable hashes — availability without a real hash unconstructible, is_persistence_engine/executes_rollback locked False; `ExecutionRollbackRef` with rollback_executed/rollback_available unconstructibly True naming P4-EXEC-E as owner; NoRollbackExecution/NoRecoveryEngine proofs), and read-only `ManagedRuntimeProjection` in `exec_projection.py` (queue/worker/claim/message/checkpoint/rollback state; 18 platform-availability booleans structurally False; single_local_worker_slot_only locked True). P4-EXEC-D execution mode safety layer adds `exec_modes.py` (closed-world `ExecutionModeRegistry` total over ExecutionMode by construction — missing/duplicate modes unconstructible, closed-world/unknown-blocked locked True, fallback/authority/execution locked False; generic `ExecutionModeProfile` where only bridge modes may carry AVAILABLE_FOR_EXISTING_BRIDGE; deterministic `decide_mode_compatibility` — unknown strings blocked, PROFILE_ONLY/UNAVAILABLE/BLOCKED modes blocked with reasons, TOOL allowed only on tool-profile + lease-scope match, allowed⊕blocked structural, fallback unrepresentable; `enforce_mode_compatibility_before_claim` queue hook reusing the C block helper; `NoSilentFallbackProof`) and `exec_mode_profiles.py` (`ToolExecutionProfile` capped at the bridge's read-only path with direct dispatch unconstructible; `ModelExecutionProfile` PROFILE_ONLY with model calls unconstructible; `TerminalExecutionProfile`/`CodeExecutionProfile` UNAVAILABLE with every execution boolean unconstructible and sandbox/operator/verifier/P9 requirements mandatory; `build_default_execution_mode_registry`; NoModelCall/NoTerminalExecution/NoCodeExecution proofs), plus read-only `ModeProjection` in `exec_projection.py` (16 risky-claim booleans structurally False). P4-EXEC-E judgment layer adds `exec_verification.py` (verification request/decision — deterministic ladder with verified=True unconstructible without PASSED + availability + evidence refs; requires_p5_proof locked True; side-effect-free `VerifierHook` with no AVAILABLE member in its availability vocabulary; NoModelVerifierCall/NoP5Proof/NoP9Authority proofs), `exec_failure.py` (12-class × 5-severity closed-world taxonomy over the total `FAILURE_METADATA` table — table-contradicting classifications unconstructible; deterministic `classify_execution_failure` + `classify_pre_submit_block`), `exec_recovery.py` (total `RECOVERY_RECOMMENDATIONS` table; E-local `BoundedRecoveryActionKind`; `BoundedRecoveryPlan` with recovery-execution/automatic-retry/rollback-execution/self-healing unconstructible, retry-without-operator-approval unconstructible, exhausted budgets deterministically downgraded, high-risk classes requiring P9; NoAutomaticRetry/NoSelfHealing proofs), `exec_algedonic.py` (`AlgedonicSignal` for URGENT/CRITICAL only — authority/bypass/action claims unconstructible; `NoFinalPythonKernelClaimProof`/`NoRustRewriteProof` carrying the Runtime Substrate Boundary: Python v1 = governance/control/reference layer; deterministic replay, durable event log, exact copy/fork, Rust/WASM substrate explicitly unavailable), and read-only `JudgmentProjection` in `exec_projection.py`. P4-EXEC-F pressure control plane adds `exec_topology.py` (`ExecutionTopologyProfile` over F-local closed-world `TopologyProfileKind` — only local kinds constructible as active profiles; default LOCAL_SINGLE_SLOT per C canon; capability-support and spawn/distribute claims unconstructible; `NoAsyncDispatcherProof`), `exec_pressure.py` (`ConcurrencyWindow` with structurally-enforced slot arithmetic; deterministic `decide_concurrency_limit` and `decide_backpressure` ladders with flag/kind agreement structural and retry/recovery/rollback/authority execution unconstructible; `ExecutionPressureSnapshot` over pure-integer `derive_pressure_level` consuming real E FailureClassifications/AlgedonicSignals — derivation-contradicting levels unconstructible; `BackpressureSignal` with deterministic kind priority), `exec_bench.py` (measured-only `ExecBenchSample`/`ExecBenchSnapshot` — unmeasured durations and invented counts unconstructible, no throughput vocabulary; `HarnessTelemetrySnapshot`; `NoFakeThroughputProof`), and read-only `TopologyProjection` in `exec_projection.py` (15 structurally-False availability booleans). P4-EXEC-G projection/seal layer adds `exec_status.py` (`ExecStatusReadModel` total over 26 canonical P4-A…F state categories — truncated/extended models unconstructible, UNAVAILABLE categories must carry reasons, a TRACE_VERIFIED category value unconstructible, mutation/verification/enforcement/Shell-UI claims unconstructible; `build_exec_status_read_model` pure aggregator that never touches the kernel; closed-world read-only `ExecCliCommandKind` STATUS/COVERAGE/HANDOFF/SEAL with mutating verbs unconstructible; `ShellBindingContract` with live CLI wiring honestly UNAVAILABLE-with-reason and Shell UI UNAVAILABLE; deterministic JSON `handle_exec_cli_status`) and `exec_seal.py` (`ExecCapabilityCoverageMatrix` total over P4.0–P4.20 with repo-truth statuses — P4.12/P4.14 PROFILE_ONLY, P4.13 UNAVAILABLE; `TruthLabelAudit` where TRACE_VERIFIED forces ERROR; `UnavailableStateAudit` total over eight absent systems with structurally-enforced future owners; `P4HandoffMatrix` assigning P5/P8/P9/P2/Rust-WASM ownership with handoff-is-implementation unconstructible; `ValidationGateResult`/`ValidationSummary` with derived pass verdicts; `P4ExitSeal` where SEALED is unconstructible over failing/missing gates or a failed truth audit — the seal verdict is recorded in `agent/releases/P4_AURELEXEC_EXIT_SEAL.md`). P3 readiness is not P4 admission; admission is not authorization; lease is not execution; runtime submit success is not semantic success; trace-bound is not trace-verified; a queue entry is not a scheduler; a worker slot is not a pool; a local log is not a bus; a checkpoint ref is not persistence; a rollback ref is not rollback execution; a mode registry is not execution; a profile is not permission; unknown mode is blocked and never falls back; a verification decision is not P5 proof; failure classification is not recovery; a recovery plan is not recovery execution; an algedonic signal is visibility, not authority; a topology profile is not a distributed runtime; a concurrency window is not a worker pool; backpressure is feedback, not recovery; ExecBench is telemetry, not theater; projection is not control; CLI status is not runtime mutation; Shell binding is not Shell UI; the exit seal is evidence, not vibes; Python v1 is not the final durable deterministic kernel; proof belongs to P5, routing to P8, authority to P9, operator UI to P2 |

P2.10 local client layers add `multi_client_foundation.py` (shared client truth), `web_shell_read_model.py` (contract-bound local web read model), `desktop_shell_contract.py` (Tauri desktop wrapper contract), `terminal_shell_client.py` (P2.10-D read-only terminal client parity/read model), and `multi_client_demo_seal.py` (P2.10-E evidence seal / P2.11 handoff). The P2.10-E seal aggregates P2.10-A/B/C/D truth into a multi-client evidence bundle, truth consistency matrix, run-mode summary, surface coverage matrix, no-overclaim matrix, P2.10 completion seal, and P2.11 handoff. P2.11-A adds `surface_permission_matrix.py`, a deterministic evidence-bound client x surface x action permission matrix foundation over P2.10 clients and the seven Shell surfaces. P2.11-B adds `surface_permission_projection.py`, a deterministic projection/read model over that matrix with client/surface/action/evidence/sensitive-surface/no-overclaim views and JSON-safe serialization. P2.11-C adds `surface_permission_inspection.py` and read-only `shell permissions` CLI bindings over that read model with query/filter contracts, inspection views, Shell view binding contracts, and JSON export. All are pre-execution Shell authority modeling/projection/inspection only and do not implement final authorization, permission enforcement, full policy runtime, Custos enforcement, command execution, runtime control, sandbox control, policy/identity/memory mutation, P2.11-D parity gate, P2.12+, final P2 seal, P3 handoff, Shell LIVE, product readiness, or new client capability.


## Custos v0 Policy Runtime Resolver — Shadow Mode (P1.6.10)

Custos v0 is the first component that turns policy-card *semantics* into a policy
*judgment*. It is the bridge between the P1.6.0–P1.6.9 policy-card families and future
runtime consequence.

Conceptual flow:

```
CommandEnvelope + Agent/Operator context + execution request metadata
  → PolicyResolutionContext        (deterministic, closed-world, hash-ready)
  → applicable policy cards         (explicit list; grouped by family)
  → per-family PolicyFamilyDecision (seven small adapters)
  → strictest-wins aggregation      (DENY > REQUIRE_APPROVAL/ERROR > WARN > ALLOW > N/A)
  → ResolvedPolicySet               (overall + WOULD_* shadow action, deterministic hash)
```

Layer distinction (do not collapse):

- `PolicyResolutionContext` / `ResolvedPolicySet` — describe a proposed action and its
  shadow judgment. They never enforce.
- The resolver interprets cards; it does not compile prompts, run sandboxes, write
  memory, or call tools.
- Enforcement and Policy Conflict Algebra are later phases; registry/context binding is the P1.6.11 bridge.

Non-negotiable law for this phase: **the resolver does not modify
`AgenticRuntime.submit()` and enforces nothing.** "Entity proposes, runtime disposes" —
P1.6.10 does not yet dispose; it teaches Custos how to judge before it is allowed to
enforce. Shadow outcomes are `WOULD_ALLOW`, `WOULD_WARN`, `WOULD_REQUIRE_APPROVAL`,
`WOULD_DENY` (plus `WOULD_NOT_APPLY` / `WOULD_ERROR` at family level). No-applicable-card
resolution is conservative (`WARN`), never a silent allow.

Future consumers: Custos runtime governance, AurelRuntime preflight, AurelFlow approval
pauses, AurelExec execution gates, AurelTrace decision evidence, P1.6.12 shadow runtime projection, and P25/P29 hardening. P1.6.10 only produces the
deterministic shadow judgment those consumers will later act on.

## Policy Resolution Context & Registry Binding (P1.6.11)

P1.6.11 is the deterministic bridge between stored/explicit policy-card lists and Custos v0 judgment. It does not enforce.

Conceptual flow:

```
explicit policy card instances/lists
  -> PolicyCardRegistry              (dedupe, ordering, family/scope lookup, applicability)
  -> PolicyResolutionContext         (closed-world runtime-like metadata binding)
  -> applicable cards                (transparent reason codes)
  -> resolve_policy_cards_from_registry()
  -> ResolvedPolicySet               (SHADOW, WOULD_* only)
```

Architectural boundaries:

- The registry is in-memory and explicit; it performs no filesystem discovery and uses no database.
- Context binding consumes plain dicts or lightweight objects and imports no runtime classes.
- Risk mapping is a conservative seed, not full risk-vocabulary unification.
- Registry applicability selects candidate lawbook cards; resolver adapters still produce judgments.
- `AgenticRuntime.submit()` remains untouched; no command blocking, approval activation, or sandbox runtime bridge exists in P1.6.11.

Next planned: P1.7.20 — Path Governance Exit Seal + Live Integration Demo (P1.7.0–P1.7.19 pre-seal); active policy enforcement deferred to later phases (P9/P25).


## Custos Shadow Runtime Projection (P1.6.12)

P1.6.12 is the first submit-time bridge from the P0 runtime to Custos, but only as trace-compatible metadata. The runtime builds a deterministic `RuntimePolicySnapshot`, resolves applicable cards from the explicit in-memory `PolicyCardRegistry`, compares the P0 effective action with Custos `WOULD_*`, and attaches the projection to `ObservationEnvelope.artifacts` before the state transition is appended.

Architectural boundaries:

- The P0 runtime remains authoritative for allow/deny/approval/sandbox/budget/verifier/rollback/memory.
- Custos shadow decisions do not block, approve, execute, or mutate commands.
- No registry or disabled flag means no shadow work.
- Runtime does not create default cards, discover policy files, or use global policy state.
- Resolver/projection errors are observable as `SHADOW_ERROR` metadata and are non-fatal to submit.

## P1.ENF-A Governance Enforcement Bridge

P1.ENF-A is the first explicit-config enforcement bridge from Custos shadow judgment and identity source hashes into `AgenticRuntime.submit()` preflight.

The bridge adds:

- `governance_enforcement.py` for closed-world modes and side-effect proof.
- `policy_submit_influence.py` for policy resolver submit influence.
- `identity_submit_context.py` for deterministic identity context/hash binding.
- `entrypoint_governance_guard.py` for bypass-risk classification.

Default runtime behavior remains compatible. Callers that do not pass a `GovernanceEnforcementConfig` or identity loader do not get new submit artifacts or changed outcomes. Under explicit `ENFORCE_FAIL_CLOSED`, submit can deny before approval, sandbox, or tool execution when the policy resolver returns hard deny/error/strict conflict, or when required policy/identity context is missing.

P1.ENF-A does not implement full Custos runtime, permission matrix, Shell command routing, product UI, identity CLI refactor, Golden Thread B, sandbox backend rewrite, trace ledger rewrite, memory rewrite, P2.9-B, production `LIVE`, or `TRACE_VERIFIED`.

## Risk Tier Policy Cards (P1.6.3)

Risk Tier Policy Cards are AurelCore governance substrate objects. They define stable R0-R6 risk semantics, reversibility expectations, oversight expectations, evidence expectations, and action-class mapping seeds. They are not a runtime risk classifier and do not grant authority, resolve policy, pause workflows, write traces, select sandboxes, route models, write memory, or enforce execution.

Future consumers may include Custos policy resolution, AurelRuntime preflight, AurelFlow approval pauses, AurelExec execution gates, AurelTrace evidence depth, AurelData/Object Plane locality decisions, Mneme memory write policy, Noesis risk-aware planning, Mundus simulation, Atlas model routing, Civitas subagent governance, AgencyHub/ABOS process governance, and P25 hardening. P1.6.3 only defines the deterministic, hash-ready semantic vocabulary those consumers can later use.

## Human Oversight Policy Cards (P1.6.4)

Human Oversight Policy Cards are AurelCore governance substrate objects. They define stable human/operator oversight semantics — what human involvement is required before, during, or after an action. They bridge risk tier → oversight level → approval/confirmation requirement → escalation. They are not an approval runtime and do not grant authority, approve actions, pause workflows, resolve policy, write traces, or enforce execution.

Key oversight vocabulary: `none`, `notify_only`, `review_recommended`, `approval_required`, `explicit_confirmation_required`, `dual_review_required`, `governance_board_required`, `deny`. The critical distinction: `approval_required ≠ explicit_confirmation_required`. R4 requires approval or stricter. R5 requires explicit Operator confirmation with strong confirmation and reviewer requirements. R6 is denied and not approvable.

Human oversight cards cannot grant authority, bypass risk tier policy, or bypass behavioral contracts. They define oversight semantics only — the bridge between risk tier → oversight → approval/confirmation. No runtime approval workflow, policy resolver, or enforcement is implemented in P1.6.4.

## Data Residency Policy Cards (P1.6.5)

Data Residency Policy Cards are AurelCore governance substrate objects. They define stable data locality semantics — which data must stay local, which may be processed in EU/EEA regions, which may be sent to trusted external regions, and which are public. They define 20 data classes with per-class residency zones, egress rules, exposure permissions, redaction requirements, and storage requirements. They are not a runtime egress guard and do not enforce egress, route models, classify data, perform redaction, or encrypt at runtime.

Key residency zones: `local_only` (default), `local_private`, `eu_only`, `trusted_region`, `external_allowed`, `public`, `forbidden`. Key safety rules: `local_only` means zero outbound (no egress, no external model/api/web), credentials never egress + require encryption + audit, sensitive_personal_data/memory_record/trace_record are forced `local_only` with no egress, `forbidden` zone is non-permissive.

Data residency cards define data locality semantics only — the bridge between data class → residency zone → processing locations → egress/permissions. No runtime egress enforcement, model routing, data classification engine, redaction execution, encryption execution, or conflict resolution is implemented in P1.6.5.

## Tool Permission Policy Cards (P1.6.6)

Tool Permission Policy Cards are AurelCore governance substrate objects. They define stable tool permission semantics — which tools may be called, by whom, under which conditions, for which data classes, and at which risk tier. They are deny-by-default with strict safety rules: credential access denied, shell commands governed, external egress controlled, and protected data classes isolated. They are not a Tool Gateway and do not enforce permissions, execute tools, resolve tool registries, or run sandboxes at runtime.

Key permission vocabulary: `ToolCategory` (17 values), `ToolPermissionType` (26 values), `ToolPermissionDecision` (8 values including allow/deny/approval_required/explicit_confirmation_required/sandbox_required/read_only/local_only/conditional). Key safety rules: deny-by-default, credential access always denied, shell command requires sandbox/approval/risk, network/egress governed, execute/delete/config-write require governance, protected data classes (credentials, operator_private, sensitive_personal_data, memory_record, trace_record, source_code) cannot be exposed externally.

Future consumers include Custos policy resolution, AurelRuntime preflight, AurelExec tool/model/code execution gates, Forge tool package manifests, AurelFlow workflow nodes, AurelTrace tool permission decisions, Mneme memory read/write governance, Atlas model/tool routing, Sandbox and Egress Guard layers, Civitas subagent tool ceilings, AgencyHub/ABOS business tool policies, and P25/P28 hardening. P1.6.6 only defines the deterministic, hash-ready semantic vocabulary those consumers can later use.

Future consumers may include Custos policy resolver, AurelRuntime preflight, AurelFlow approval pauses, AurelExec execution gates, AurelTrace approval/evidence recording, Operator Shell / Approval Workbench, Noesis risk-aware planning, Mundus simulation tests, Civitas subagent oversight ceilings, AgencyHub/ABOS business workflow approvals, and P25 governance hardening. P1.6.4 only defines the deterministic, hash-ready semantic vocabulary those consumers can later use.

## Memory Write Policy Cards (P1.6.7)

Memory Write Policy Cards are AurelCore memory governance semantics — the substrate that answers *what is allowed to become memory*. They define stable memory write vocabulary: which memory zone may receive a write, which write type is attempted, which decision applies, which verification status and retention class result, and which evidence/provenance/review requirements must hold first. They encode the core Aurel law: **raw experience does not become capability directly — memory write requires policy, evidence, scope, provenance and review posture.**

A Memory Write Policy Card is distinct from runtime memory storage. The card defines memory write *semantics*; **Mneme** later stores/retrieves/graphs memory; the **Evaluation Mirror** later validates memory evidence; the **Verification Court** later promotes candidates; **Praxis** later matures traces into skills/reflexes; the **policy runtime resolver** later resolves applicable policy; and **P25/P29** later harden and audit memory drift/canon pollution. P1.6.7 is the model/schema/validation layer only — it does not store, write, retrieve, rank, consolidate, graph, promote, canonize or enforce memory, and it does not implement Mneme.

Key memory vocabulary: `MemoryZone` (14 values: scratchpad, working_memory, episodic_memory, semantic_memory, procedural_memory, operator_profile, project_memory, canon_memory, policy_memory, evaluation_memory, skill_candidate_memory, verified_skill_memory, audit_memory, forbidden), `MemoryWriteType` (18 values), `MemoryWriteDecision` (10 values), `MemoryVerificationStatus` (8 values), `MemoryRetentionClass` (6 values), `MemoryWriteRequirementType` (13 values). Key safety laws: deny-by-default; candidate ≠ verified ≠ canon; no silent canon/policy writes; verified skill memory requires evaluation + verification; skill candidate cannot be verified/canonized by default; operator profile requires consent/review/provenance; credentials cannot become durable memory; sensitive personal data writes are strict (evidence + provenance + residency check + review).

Future consumers include the Mneme memory graph, AurelRuntime memory preflight, Custos policy resolver, AurelTrace evidence/provenance binding, the Evaluation Mirror, the Praxis maturation loop (Trace → Evaluation → Candidate → Verification → Skill → Specialist → Reflex), Skill Arena, the Specialist Factory, Reflex compilation, AurelFlow workflow memory writes, AurelExec tool-result memory writes, Noesis planning memory, AgencyHub/ABOS corporate memory, and P25/P29 hardening. P1.6.7 only defines the deterministic, hash-ready semantic vocabulary those consumers can later use — it is the policy language that prevents skipping the maturation ladder.

## Prompt Policy Cards (P1.6.8)

Prompt Policy Cards are AurelCore prompt-trust and instruction-boundary semantics — the substrate that answers *which prompt source is trusted, which may command, and which may only inform*. They encode the core Aurel law: **untrusted content may inform, but must never command.** A prompt rule binds a prompt source (system/developer/operator/task/agent prompt, tool output, retrieved memory/document, web/email/file/code/external-API content, evaluation/critic/planner/reflection/generated prompt, or unknown) to a trust level, a role, a handling decision, and a set of explicit capability flags (instruction/context/tool-request/memory-write/policy-modify/identity-modify) plus injection-risk vocabulary and boundary requirements.

A Prompt Policy Card is distinct from runtime prompt machinery. The card defines prompt-handling *semantics*; the **Prompt System / Prompt Compiler** later assembles and enforces the prompt hierarchy; a **Prompt Injection Detector** later detects suspicious instruction patterns; the **policy runtime resolver** later resolves applicable cards; **Custos** later governs runtime prompt/action boundaries; and **P25/P29** later harden prompt-injection and governance behavior. P1.6.8 is the model/schema/validation layer only — it does not compile prompts, enforce instruction hierarchy, detect injection or jailbreaks, block tools/memory, or modify identity/policy at runtime.

Key prompt vocabulary: `PromptSourceType` (19 values), `PromptTrustLevel` (10 values), `PromptRole` (16 values), `PromptPolicyDecision` (10 values), `PromptInjectionRisk` (5 values), `PromptInjectionPattern` (15 values), `PromptBoundaryRequirementType` (14 values). Key safety laws: strict deny-by-default; unknown source is untrusted; external content cannot be instruction authority; tool output is data/context, not command; retrieved memory is context, not automatic authority; untrusted content cannot request tools, write memory, modify policy, or modify identity; high/critical injection risk cannot pair with permissive instruction authority; prompt authority is never inferred from text content alone.

Future consumers include the Prompt System / Prompt Compiler, Custos policy resolver, AurelRuntime context assembly, AurelExec tool-output handling, Mneme retrieved-memory handling, Atlas model routing, Noesis planner prompt boundaries, Civitas subagent instruction boundaries, AgencyHub/ABOS corporate context handling, and P25/P29 hardening. P1.6.8 only defines the deterministic, hash-ready semantic vocabulary those consumers can later use — it is the policy language that protects the perception/cognition/action boundary against prompt injection, authority spoofing and instruction-hierarchy collapse.

## Repository Reality Seal (P1.6.8S)

P1.6.8S is a stabilization seal, not a feature layer. It does not add policy-card semantics or runtime enforcement. Its architectural role is to keep repository truth aligned with governance truth: P1.6.4-P1.6.8 policy-card artifacts are identified for tracking, P1.6.8 Prompt Policy Card behavior is verified against the existing policy-card family, CLI subprocess tests use the active interpreter through a shared helper, lint/type/full-suite/coverage validation passes, and P1.6.9 remains the next feature phase.

## External doctrine assimilation (P1.4.11)

External doctrine intake is a read-only identity governance layer. Doctrine records carry source identity, SHA-256 source hash, source type, assimilation status, roadmap mappings, claim boundaries, risk notes, and Operator acceptance. The layer maps doctrine to existing roadmap modules and routes implementation-sounding claims through P1.4.10. It does not execute tools, grant autonomy, change policy, override canon, or mark capabilities implemented by declaration.


## Source attestation (P1.4.12)

Source attestation is the identity integrity layer that binds raw source input to canonical typed meaning. It captures raw SHA-256, canonical typed SHA-256, source kind, validator metadata, validation status, rejected unknown fields, warnings, errors, and evidence references.

Identity source loading now attaches attestations to `IdentitySourceBundle` for identity kernel, persona manifest, operator contract, communication modes, identity prompt compiler policy, self-model policy, and agent identity card config. External doctrine records can also produce `external_doctrine` attestations.

Architectural law:

- Raw hash is not canonical meaning.
- Canonical typed hash is not raw source integrity.
- Hash-based attestation is not truth, trust, capability, cryptographic signing, or tamper-proof storage.
- Unknown governance/authority-shaped fields must be rejected and attested, not silently ignored.

## Authority Delta Detector (P1.4.13)

Authority delta detection is the semantic comparison layer that identifies authority-relevant changes between two attested canonical states. It does not grant consent or execute tools.

The detector extracts authority surfaces from known source kinds (operator_contract, agent_identity_card_config, self_model_policy, external_doctrine, capability_claims, source_attestation), compares old and new surfaces, classifies each difference by authority meaning, and produces an `AuthorityDeltaReport` with severity, consent, and evidence requirements.

**Core module:** `src/agentic_runtime/identity/authority_delta.py`

Architectural law:

- Valid source does not imply safe authority change.
- Authority detection is not consent.
- Detection does not execute actions or modify source.
- High/critical deltas carry `requires_operator_consent: true`.
- Claim/capability/doctrine status escalation carries `requires_evidence: true`.
- Conservative tool heuristics err on the side of marking tools as dangerous.

## Operator Consent Binding (P1.4.14)

Operator consent binding is the formal layer that binds Operator approval to specific authority deltas. Consent is bound to exact delta IDs, source kind, and old/new attestation pairs — it is not global, not permanent by default, and not transferable.

The binding layer exposes consent requests from delta reports, grants/denies with fail-closed validation, revocation of granted records, and binding validation that verifies status, attestation, delta coverage, risk acknowledgement, scope, and expiry constraints.

**Core module:** `src/agentic_runtime/identity/operator_consent.py`

Architectural law:

- Consent is bound to exact delta IDs and attestation pairs.
- Consent is not global — it does not cover any other authority delta.
- Consent is not permanent by default — expiry is enforced.
- Revoked or expired consent is permanently invalid.
- HIGH/CRITICAL deltas require explicit risk acknowledgement.
- Consent does not execute changes, modify source, or grant capabilities.
- Consent validation exposes structured blockers (not just true/false).

The consent layer is a primitive for P1.4.15 CLI surface and future governance automation. It does not implement approval workflows, policy cards, or capability promotion.

### Runtime integration status (P1.4.15)

**NOT YET WIRED.** Authority delta detection and operator consent binding are identity governance signals exposed via CLI and in-memory models. They do **not** gate `AgenticRuntime.submit()` today. Runtime commands proceed through policy → approval → sandbox without checking `validate_operator_consent_binding()`. Wiring consent enforcement into the command pipeline is deferred to P1.4.16+.

## Identity Governance Command Surface (P1.4.15)

The command surface is the unified CLI layer that exposes the entire identity governance stack through one namespace. It provides `identity status` and `identity verify` as read-only inspection endpoints with a standardized JSON output envelope `{ok, command, status, errors, warnings, result}`.

The surface probes 6 subsystems (kernel, claims, doctrine, attestation, authority-delta, consent) via lightweight import checks and routes subcommands to their respective module CLI handlers.

**Core module:** `src/agentic_runtime/identity/identity_cli_surface.py`

Architectural law:

- The surface is a command interface, not an interactive terminal agent.
- Status and verify are read-only — no file writes, no tool execution, no consent grants.
- JSON envelope is stable across all identity commands.
- Human-readable output exposes blockers and suggested next commands.
- Module boundaries are preserved — each subcommand routes to its owning module.
- Governance failures are visible, not hidden.

## Command pipeline

```
Provider structured plan
  → Schema validation
  → PlanValidator
  → CommandEnvelope
  → Tool contract (input)     # registry + schema
  → Budget precheck
  → Policy                    # capability ≠ permission ≠ authority
  → Approval resolver         # risk class, preview, confirmation requirement
  → HITL / approver           # if required
  → Approval receipt trace
  → Sandbox profile check     # capability/path gate (P0.17)
  → Budget charge
  → Sandbox snapshot (writes)
  → Tool Bus execution        # registered tool handler inside sandbox
  → Tool contract (output)
  → State verifier
  → Rollback (failed writes)
  → Trace append
  → Governed memory update
  → ObservationEnvelope + VerifierResult
```

## Wiring

`build_runtime()` in `__init__.py` constructs a `Kernel` bundle:
sandbox, tools, policy, verifier, trace, memory, budget, router, skills, runtime.

Default sandbox: `UnsafeLocalSandbox` (demo/trusted only — not a security boundary).

## Repository Agent Loop

`RepositoryAgentLoop` is an application-level loop, not a new authority system.
It builds bounded repository context directly from the local repo, creates an
explicit `RepoTaskPlan` with deterministic, LLM, hybrid, or dry-run planning, then submits patch/test commands through
`AgenticRuntime.submit()` so policy, HITL, budget, sandbox, verifier, trace, and
memory governance still dispose execution.

```
RepoTaskRequest
  → RepoContextBuilder
  → CodeTaskPlanner / LLMRepoPlanner
  → RepoPlanValidator   # strict repository-plan schema + path/test constraints
  → PatchExecutor       # Runtime.submit(patch_file/write_file)
  → TestRunnerAdapter   # Runtime.submit(run_tests/run_shell)
  → TestFailureAnalyzer
  → RepairLoop          # bounded iterations
  → CodeTaskReport
  → PraxisMetabolism    # experience + memory candidates + PraxisReport (P0.16)
```

## Praxis memory metabolism (P0.16)

Trace is not memory. `PraxisMetabolism` captures `PraxisExperience` from command
results and repo reports, generates evidence-backed `MemoryCandidate` records,
evaluates conservative promotion to procedure/skill candidates, and submits
candidate-level writes through `memory_governance` — never auto-promoting canon.
Reflex eligibility checks document that runtime governance remains mandatory.

## Sandbox profiles (P0.17)

`SandboxPolicy` evaluates tools and paths against a declared `SandboxProfile`
before Tool Bus handlers run. `ProfiledSandbox` enforces filesystem boundaries
(traversal, secrets, workspace root). Docker/Bubblewrap profiles are honest
about availability — no silent downgrade to unsafe mode.

## Sandbox layer disambiguation (P1.6.10H)

Four distinct sandbox layers exist. They must not be confused:

1. **Runtime sandbox policy** (`sandbox_policy.py`)
   - Currently enforced runtime sandbox policy / runtime gate.
   - Owns `SandboxPolicy`, `ProfiledSandbox`, profile templates, path/tool gating.

2. **Sandbox backend** (`sandbox.py`)
   - Execution backend / local sandbox abstraction.
   - `UnsafeLocalSandbox` (NOT a security boundary), `BubblewrapSandbox`, `DockerSandbox`.
   - `create_sandbox()` safety gate (`allow_unsafe=True` required for UNSAFE_LOCAL).

3. **Sandbox policy card** (`policy_cards/sandbox.py`)
   - P1.6.9 semantic policy-card model.
   - Resolver-ready, NOT runtime-enforced yet.
   - `SandboxPolicyCard`, `evaluate_sandbox_policy_decision()`, `SandboxPolicyDecision`.

4. **Custos v0 resolver** (`policy_cards/resolver.py` + `resolution_context.py` + `resolution_result.py`)
   - P1.6.10 shadow-only resolver.
   - Produces `WOULD_*` decisions. Does NOT block runtime behavior.

**P1.6.9 sandbox policy cards and P1.6.10 resolver do not yet enforce runtime sandbox behavior. Runtime enforcement still flows through the P0 runtime policy and sandbox layers.**

## Policy Projection, CLI Binding & Exit Seal (P1.6.17–P1.6.20)

Integration-First vertical slice for operator inspection of the P1.6 policy subsystem:

```
policy_cards/ backend (P1.6.0–P1.6.16)
  → build_policy_projection_contract()
  → PolicyProjectionContract v1 (policy_projection.v1)
  → policy_projection_to_json_safe_dict()
  → cli_modules/policy_commands.py
  → python -m agentic_runtime.cli policy …
  → build_policy_exit_seal_report()  [P1.6.20]
  → agent/reports/P1.6.20_*          [evidence binding]
```

Architectural boundaries:

- **Backend is source of truth** — `policy_cards/` modules (registry, resolver, conflict algebra, trace hooks, harness).
- **Projection is not authority** — contract reports module availability and readiness; it does not enforce policy or mutate runtime state.
- **Source labels are mandatory** — `LIVE`, `TRACE_VERIFIED`, `SIMULATED`, `DEV_FIXTURE`, `UNAVAILABLE`, `ERROR`. No fake LIVE state.
- **CLI consumes contract** — `policy status`, `policy projection`, `policy unavailable`, `policy harness list/run` call P1.6.17 builders; no parallel projection logic.
- **Shell/TUI UNAVAILABLE** — `shell_binding` section stays UNAVAILABLE until Shell UI exists; P1.6.18 is CLI binding only, not a full TUI app.
- **Exit seal is proof, not expansion** — P1.6.20 `exit_seal.py` verifies the vertical slice read-only; no enforcement, Ledger writes, or runtime mutation.
- **No enforcement** — policy CLI and exit seal do not import runtime, approval, ledger, or sandbox; harness reports `enforced: false`.

Key modules:

| Module | Role |
|--------|------|
| `policy_cards/projection_contract.py` | P1.6.17 — `PolicyProjectionContract v1`, sections, readiness, hashing |
| `policy_cards/test_harness.py` | P1.6.16 — shadow scenario harness engine |
| `policy_cards/policy_harness_registry.py` | P1.6.18 — built-in harness case registry for CLI |
| `cli_modules/policy_commands.py` | P1.6.18 — read-only operator CLI binding |
| `policy_cards/exit_seal.py` | P1.6.20 — exit seal proof layer, deterministic report hash |

P1.6 section **sealed with warnings** (2026-06-25). P1.7 Path Governance & Source Trust is **pre-seal** (P1.7.0–P1.7.19 complete). Next: P1.7.20 — Exit Seal + Live Integration Demo.

## LLM repository planning (P0.21)

`LLMRepoPlanner` uses `ModelRouter.complete_structured()` with a repository-plan schema. Providers return JSON only: objective summary, files to inspect/modify, proposed non-executing steps, risk, expected tests, approval flag, assumptions, and optional refusal. `RepoPlanValidator` rejects invalid JSON, missing fields, disallowed paths, excessive file counts, and test-file modifications unless explicitly allowed. Invalid LLM output becomes `planning_failed` in `llm` mode or a recorded deterministic fallback in `hybrid` mode.

The LLM never receives tool authority and never executes tools. Patch/test execution remains in `RepositoryAgentLoop → Runtime → Tool Bus → Approval → Sandbox → Verifier / Trace / Praxis`.

## Prompt system (P1.2)

Prompts live under the top-level `prompts/` directory as YAML manifests. `PromptRegistry` loads and validates manifests, optionally checks `allowed_model_profiles` against P1.1 `ModelConfigBundle`, and renders templates with explicit `{{ variable }}` placeholders. Missing variables fail closed. Prompt policies may not request secrets or authority expansion, and planning prompts may not request tool execution or file modification.

Rendered prompts produce `PromptTraceSummary` records with prompt id, version, owner, purpose, allowed profiles/tasks, risk tier, template/rendered hashes, variables used, and `raw_prompt_stored: false`. Raw rendered prompt text is not persisted by default. CLI render output omits rendered previews; module summaries may carry bounded redacted previews for tests or future trace integration.

## Tool / plugin manifest domain (P1.3.0)

P1.3.0 adds typed backend models under `tool_manifest/` only — no registry loader, no execution path, no marketplace UI.

| Model | Role |
|-------|------|
| `PluginManifest` | Package/source metadata declaring one or more tool ids, trust, policies, and compatibility |
| `ToolManifest` | Declared identity and contract for a single tool (schemas, risk, side effects, trace level) |
| `ToolCapability` | Runtime-normalized view of a valid `ToolManifest` — contracts and profiles, not a handler |
| `ToolRegistryEntry` | Placeholder registry record with validation issues and optional normalized capability |
| `ToolInvocationDraft` | Proposed tool use with purpose, payload, and predicted effect — **not execution** |
| `PredictedEffect` | Seed for future planning / world-model layers |
| `ValidationIssue` | Structured manifest validation finding |

Architectural law (unchanged from the governed runtime):

- **Tool access is not authority.** Listing or declaring a tool does not grant write/network/secret authority.
- **Tool visibility is not execution right.** Seeing a manifest or capability does not permit invocation.
- **Tool registration is not trust.** Registry entries record state; trust is evaluated separately.
- **Tool manifest is not permission.** Policy, HITL, and sandbox still dispose any future execution.
- **Tool invocation draft is not execution.** Drafts are proposals only; the existing `CommandEnvelope → Runtime → Tool Bus` pipeline remains the execution surface.

Later phases (P1.3+) may add manifest loading, validation, quarantine, and draft-to-command bridging. P1.3.0 intentionally stops at serializable domain types with helpers such as `is_high_risk()`, `is_external()`, and `requires_human_approval()`.

## Tool manifest validation (P1.3.1)

`tool_manifest/validation.py` inspects `PluginManifest` and `ToolManifest` metadata and returns structured `ValidationIssue` lists. Validation is read-only — it does not mutate manifests, grant authority, register tools, or execute anything.

| Function | Role |
|----------|------|
| `validate_plugin_manifest` | Identity + provenance/trust checks for plugins |
| `validate_tool_manifest` | Full composed validation (optional plugin context) |
| `validate_tool_risk_metadata` | Risk class ↔ side-effect/trace/evidence rules |
| `validate_tool_permission_metadata` | Permissions + plugin secret/network policy requirements |
| `validate_tool_side_effect_metadata` | Side-effect ↔ risk, data access, environment rules |
| `validate_tool_provenance_metadata` | Plugin origin/trust/status vs tool risk |
| `is_tool_manifest_valid` / `is_plugin_manifest_valid` | Convenience pass/fail (no blocking issues) |
| `has_blocking_validation_issues` | True when any `error` or `critical` issue exists |
| `validation_summary` | Counts by severity + stable issue codes |

Key rules enforced:

- **R0/R1** read-only tools cannot declare write/execute/network/secret side effects.
- **R4/R5/R6** require approval; R5 requires evidence; R6 must be disabled; high-risk trace must be detailed/forensic.
- **External/network/secret** tools require matching plugin policies and explicit permissions.
- **State-changing** tools should declare `PredictedEffect` (warning at R2/R3, error at R4/R5).
- **Generated/external/unknown** plugin origins are validated more strictly; unknown origin + enabled R3+ tool is critical.

No manifest with blocking validation issues should become a `ToolCapability` in later registry phases. Validation does not replace runtime policy, HITL, or sandbox gates.

## Manifest loader (P1.3.2)

`tool_manifest/loader.py` reads local declarative manifest files (JSON primary; YAML via `yaml_minimal` when extension is `.yaml`/`.yml`).

| Function / type | Role |
|-----------------|------|
| `load_manifest_file` | Read, hash, parse, validate one manifest file |
| `load_manifest_directory` | Deterministic sorted directory scan; continues after bad files |
| `parse_manifest_bundle` | Parse root `{plugin, tools}` dict into domain objects |
| `validate_manifest_bundle` | P1.3.1 validation + bundle consistency rules |
| `compute_manifest_hash` | SHA-256 over raw file bytes |
| `determine_manifest_load_status` | Map issues → `loaded` / `loaded_with_warnings` / `invalid` |
| `ManifestLoadResult` | Structured load outcome (path, hash, issues, status) |

Loader law:

- **Manifest loading is not registry activation.** Parsed manifests are not registered with Tool Bus.
- **Manifest loading does not execute tools.** No handlers run; no side effects occur.
- **Manifest loading does not grant authority.** Validation reports unsafe metadata only.

See `TOOL_MANIFESTS.md` for file format and fixture examples.

## Tool capability registry (P1.3.3)

`tool_manifest/registry.py` builds a runtime-visible catalog of validated `ToolCapability` objects.

| Type / function | Role |
|-----------------|------|
| `ToolRegistry` | In-memory catalog of `ToolRegistryEntry` records |
| `ToolRegistryResult` | Structured outcome for register/disable/enable operations |
| `ToolRegistryOperationStatus` | `registered`, `already_exists`, `rejected`, `disabled`, `enabled`, `not_found`, … |
| `create_tool_capability_from_manifest` | Normalize `ToolManifest` + optional `PluginManifest` → `ToolCapability` |
| `register_manifest_result` | Loader output → catalog entries (valid loads only) |
| `register_bundle` / `register_tool_manifest` | Direct bundle/tool registration |
| `list_active_tools` | Excludes disabled/invalid/quarantined/deprecated/experimental/R6 |
| `get_capability_roles` | Derived role tags (metadata/query only) |

Registry law:

- **Registry visibility is not permission.** Listing a capability does not authorize execution.
- **Registry does not execute tools.** No Tool Bus dispatch or handler invocation.
- **Registration is not trust.** Validation issues are preserved on each entry.
- High-risk helpers (`list_high_risk_tools`, `requires_approval`) expose approval-bound metadata only.

Manifest loading (P1.3.2) and registry activation (P1.3.3) remain separate: load → validate → optionally register.

## Quarantine and validation reports (P1.3.4)

`tool_manifest/quarantine.py` adds structured safety-state handling on top of P1.3.1 validation.

| Type / function | Role |
|-----------------|------|
| `ValidationReport` | Severity counts and blocking summary for issue lists |
| `QuarantineDecision` | `should_quarantine`, `should_reject`, `should_disable`, reasons |
| `QuarantineRecord` | Isolation record with issues, hash, source path, suggested action |
| `QuarantineStore` | In-memory quarantine catalog |
| `classify_validation_issues` | Build `ValidationReport` |
| `decide_quarantine_for_plugin/tool/manifest_result` | Policy decisions without mutation |
| `create_quarantine_record` | Materialize isolation record |
| `registry_should_activate_entry` | Active-list gate used by `ToolRegistry` |

Quarantine law:

- **Quarantine is isolation, not deletion** — objects remain auditable with preserved evidence.
- **Quarantine is not approval workflow** — no HITL or execution side effects.
- **Registry must not expose quarantined tools as active** — integrated via `ToolRegistry.quarantine_store`.
- **Warning-only paths keep warnings visible** on registry entries without automatic quarantine.

## Tool invocation drafts (P1.3.5)

`tool_manifest/invocation.py` prepares structured tool-use **proposals** from active registry capabilities.

| Type / function | Role |
|-----------------|------|
| `ToolInvocationContext` | Who/why/source metadata for a draft request |
| `ToolInputValidationResult` | Minimal JSON-schema input validation outcome |
| `ToolInvocationDraft` | Intention object (payload, risk, evidence plan) — not execution |
| `ToolInvocationDraftResult` | Structured create outcome with status and issues |
| `validate_tool_input_payload` | Required fields, unexpected fields, primitive type checks |
| `derive_approval_requirement` | Conservative approval flag from capability metadata |
| `derive_evidence_plan` | Seed evidence capture guidance (not evidence itself) |
| `create_tool_invocation_draft` | Registry → validate → draft; never invokes tools |
| `is_tool_invocation_draft_policy_ready` | Structural readiness for a future policy gate |

Draft law:

- **Tool invocation draft is not execution** — no Tool Bus dispatch, network, or file mutation.
- **Draft creation does not grant authority** — registry visibility and drafts are metadata only.
- **`ready_for_policy` / policy-ready ≠ executable** — future policy/approval layers decide execution.
- **High-risk drafts** carry `approval_required` and `requires_approval` status for downstream HITL.
- **`predicted_effect` is preserved** for future world-model/planning layers, not autonomous selection.

## Tool lifecycle trace events (P1.3.6)

`tool_manifest/events.py` records serializable lifecycle transitions for manifest load, registry, quarantine, and invocation-draft stages.

| Type / function | Role |
|-----------------|------|
| `ToolLifecycleEventType` | Event taxonomy (`manifest_loaded`, `tool_capability_registered`, …) |
| `ToolLifecycleEvent` | Serializable lifecycle record with issues and metadata |
| `ToolLifecycleEventRecorder` | In-memory event store with list/filter/get helpers |
| `build_manifest_loaded_event` / `build_manifest_rejected_event` | Manifest loader outcomes |
| `build_tool_registered_event` / `build_tool_rejected_event` | Registry outcomes |
| `build_quarantine_record_created_event` | Quarantine isolation records (immune-system seed) |
| `build_invocation_draft_event` | Draft create/block/reject/approval outcomes |

Trace law:

- **Trace event is not execution** — recording does not invoke tools or grant authority.
- **Trace event is not verified evidence** — validated execution support comes later.
- **Composable builders** — loader/registry/quarantine/draft modules are not auto-instrumented; callers opt in via `recorder.record(build_*_event(result))`.
- **`predicted_effect` metadata** is preserved on draft/registry events for future world-model loops.
- **Separate from P0.6 hash-chain ledger** — lifecycle events use a lightweight in-memory recorder, not `PersistentTraceLedger`.

## Research-inspired tool metadata (P1.3.7)

`tool_manifest/research_metadata.py` adds optional schema, derivation, and validation for world-model / simulation / governance / learning **readiness** metadata.

| Type / function | Role |
|-----------------|------|
| `ToolRole` | Foundation-Agent loop role (perception, action, …) |
| `StateDeltaContract` | Expected state delta seed for Action → Predicted → Observed loops |
| `SimulationProfile` | Dry-run/simulation strategy declarations (not execution) |
| `ToolSafetySurface` | Threat surfaces and externality classification |
| `ToolLearningProfile` | Skill/procedure/evaluation hints (no learning) |
| `derive_*` helpers | Conservative metadata seeds from manifest/capability |
| `validate_tool_research_metadata` | Warnings/errors for high-risk missing explicit metadata |

Research metadata is copied onto `ToolCapability`, `ToolInvocationDraftResult.research_metadata`, and lifecycle event metadata.

## Built-in seed manifests (P1.3.8)

`tool_manifest/builtin_manifests.py` and `tool_manifest/manifests/*.json` ship seven declarative built-in tool capabilities. See `TOOL_MANIFESTS.md` for the tool table and integration path.

## P1.3 Tool Manifest Layer — sealed boundary (P1.3.9)

P1.3 is a **declarative capability layer**. It is separate from the executable Tool Bus.

| Layer | Module | Role |
|-------|--------|------|
| Declarative manifest | `tool_manifest/` | Parse, validate, quarantine, catalog, draft, trace |
| Executable runtime | `tools.py`, `runtime.py` | `CommandEnvelope` → `AgenticRuntime.submit()` → `ToolRuntime.dispatch()` |

Naming note (docs only):

- `tools.py` `ToolRegistry` ≈ **ExecutionToolRegistry** (handler registry)
- `tool_manifest/registry.py` `ToolRegistry` ≈ **ManifestToolCatalog** (capability metadata catalog)

Boundary laws enforced by P1.3.9 seal tests:

- **No bridge in P1.3** — `ToolInvocationDraft` does not become `CommandEnvelope`; no `runtime.submit` or `ToolRuntime` calls from `tool_manifest/`.
- **Registry visibility is not permission** — active catalog entries do not authorize execution.
- **Trace events are not verified evidence** — lifecycle recorder is separate from P0.6 hash-chain ledger.

Future bridge (not implemented — planned at **P6 Governed Tool Bus Expansion**):

```
ManifestToolCatalog → ToolInvocationDraft → Authority/Policy → CommandEnvelope → runtime.submit → ToolRuntime → ObservedEffect → Trace/Evidence
```

Seal tests: `tests/test_p13_tool_manifest_layer_seal.py`

## P1.4 Identity, Autonomy & Agent Trust Constitution (P1.4.0)

P1.4.0 is a **scope-contract and preparation layer only**. Constitutional doctrine lives in:

- `docs/P1.4_IDENTITY_AUTONOMY_SCOPE_CONTRACT.md`
- `docs/P1.4_AGENT_TRUST_CONSTITUTION.md`
- `docs/P1.4_RESEARCH_ALIGNMENT_NOTES.md`

Boundary laws (P1.4):

- **Identity is not policy.**
- **Persona is not authority.**
- **Communication mode is not permission.**
- **Tool access is not tool authority** (extends P1.3 manifest boundary).
- **Operator remains final authority; Aurel cannot self-escalate autonomy.**

Stub packages under `identity/`, `autonomy/`, `governance/`, `heretic/`, `metacognition/`, `compliance/` have no runtime integration with `policy.py`, `runtime.py`, or execution paths in P1.4.0.

Static patch map: `identity/p14_scope.py` (`P14_PATCHES`, `P14_SCOPE_IN`, `P14_SCOPE_OUT`, `P14_FORWARD_HOOKS`).

Next implementation: **P1.4.2 Persona Manifest**.

## P1.4.1 Identity Kernel

Machine-readable trust anchor at `config/aurel/identity_kernel.yaml`:

- `load_identity_kernel()` → `AurelIdentityKernel`
- `validate_identity_kernel()` → fail-closed on critical invariant violations
- `compute_identity_kernel_hash()` → deterministic SHA-256
- CLI: `python -m agentic_runtime.cli identity kernel {show,validate,hash,attest}`

Spec: `docs/P1.4.1_IDENTITY_KERNEL_SPEC.md`. Identity Kernel is **not** persona, autonomy, or tool authority.

## P1.4.2 Persona Manifest

Validated expression contract at `config/aurel/persona_manifest.yaml`:

- `load_persona_manifest()` → `AurelPersonaManifest`
- `validate_persona_manifest()` → fail-closed on critical boundary violations
- `compute_persona_manifest_hash()` → deterministic SHA-256
- `build_persona_safe_summary()` → prompt-safe preparation object (no raw YAML)
- CLI: `python -m agentic_runtime.cli identity persona {show,validate,hash,attest,summary}`

Spec: `docs/P1.4.2_PERSONA_MANIFEST_SPEC.md`. Persona is **not** authority, policy, autonomy, Operator Contract, or Identity Kernel. Next: **P1.4.3 Operator Relationship Contract**.

## P1.4.16 Identity Test Battery

The identity test battery is a **verification/test harness**, not a new governance engine. It sits above P1.4.13-14-15 (authority delta, consent, command surface) and below P1.4.17 (continuity capsule), wrapping all prior identity layers into a single battery with an aggregate PASSED/FAILED/DEGRADED/SKIPPED status.

**Core modules:**
- `src/agentic_runtime/identity/identity_test_battery.py` — battery engine (case model, scoring, aggregation, CLI entry point)
- `src/agentic_runtime/identity/identity_test_battery_scenarios.py` — scenario runners (late imports to avoid circular dependencies)

**Data flow:**
```
P1.4.13 AuthorityDelta → P1.4.14 Consent → P1.4.15 CommandSurface
                                                     ↓
                              P1.4.16 Battery wraps them all
                              (26 cases, 7 categories, aggregate status)
                                                     ↓
                                         P1.4.17 Lifecycle → P1.4.18 TrustEvidence
```

**Architectural law:**

- The battery is a test harness, not a governance engine — it verifies identity layers, it does not add new authority.
- Battery status is computed from individual case results, never declared.
- Late imports in scenario runners prevent import-time coupling between identity modules.
- Aggregate status (PASSED/FAILED/DEGRADED/SKIPPED) provides a single go/no-go signal for CI and operator health checks.
- Adversarial scenarios are included by default — the battery must not provide false confidence.
- The battery does not mutate identity sources, grant consent, execute tools, or change runtime state.

## P1.4.18 Trust Evidence Linkage

The trust evidence linkage layer is a **classification and explanation layer**, not a permission or authority layer. It sits above P1.4.17 (Agent Lifecycle Eligibility State Machine) and below P1.4.19 (Identity Docs/Reports/State Update), linking evidence references from across the identity stack into a structured trust posture classification.

**Core module:** `src/agentic_runtime/identity/trust_evidence.py`

**Data flow:**
```
P1.4.17 Lifecycle → eligibility state
                         ↓
           P1.4.18 Trust Evidence Linkage
           ← source attestations (P1.4.12)
           ← test battery (P1.4.16)
           ← consent records (P1.4.14)
           ← authority deltas (P1.4.13)
           ← lifecycle decisions (P1.4.17)
                         ↓
           Trust Evidence Bundle → posture resolution
                         ↓
              P1.4.19 Docs/Reports/State Update
```

**Domain models:**

| Type | Role |
|------|------|
| `TrustEvidenceKind` | Enum classifying evidence source type (SOURCE_ATTESTATION, TEST_BATTERY, CONSENT, AUTHORITY_DELTA, LIFECYCLE) |
| `TrustEvidenceStatus` | Enum for evidence resolution status (PRESENT, MISSING, INVALID, EXPIRED, REVOKED) |
| `TrustPosture` | Enum for categorical trust classification (UNTRUSTED through BLOCKED) |
| `TrustEvidenceRef` | Reference to a specific evidence artifact with kind, status, and attestation id |
| `TrustEvidenceRequirement` | Expected evidence requirement derived from lifecycle state |
| `TrustEvidenceLink` | Binding between a requirement and its resolved evidence ref |
| `TrustEvidenceBundle` | Complete set of evidence links assembled for posture evaluation |
| `TrustEvidenceLinkageReport` | Structured report with posture, evidence links, and human-readable explanation |

**Engine functions:**
- `default_trust_evidence_requirements_for_lifecycle()` — derive required evidence kinds from lifecycle state
- `build_trust_evidence_bundle()` — assemble evidence links from 5 helper builders
- `validate_trust_evidence_bundle()` — structural integrity and reference consistency checks
- `resolve_trust_posture()` — classify categorical posture from bundle (no numeric score)

**Helper builders:**
- `evidence_ref_from_source_attestation` — source attestation → evidence ref
- `from_test_battery_report` — battery aggregate status → evidence ref
- `from_consent_record` — consent record → evidence ref
- `from_authority_delta_report` — delta report → evidence ref
- `from_lifecycle_decision` — lifecycle state/transition → evidence ref

**Architectural law:**

- Trust posture is strictly categorical — no numeric trust score, percentage, or aggregate rating.
- Evidence linkage is not truth validation — hashes prove integrity, not correctness.
- Trust evidence bundle validation is read-only — no authority grants, tool execution, lifecycle mutation, or truth assessment.
- The linkage report explains WHY an identity has its current posture by cross-referencing evidence from across the P1.4 stack.
- P1.4.18 does not grant authority, execute tools, mutate lifecycle, calculate numeric score, or validate truth.
- 10 invariants (INV-P1418-01 through INV-P1418-10) enforce these laws at validation time.

## P1.4.19 Seal Readiness Consolidation Layer

The seal readiness layer is a **consolidation and audit layer**, not a new governance layer. It sits above P1.4.18 (Trust Evidence Linkage) and below P1.4.20 (P1.4 Identity & Autonomy Exit Seal), providing structured P1.4 inventory for exit seal verification.

**Core module:** `src/agentic_runtime/identity/p14_seal_readiness.py`

**Data flow:**
```
P1.4.18 Trust Evidence → categorical posture
                               ↓
              P1.4.19 Seal Readiness Consolidation
              ← identity module map (all P1.4 modules)
              ← CLI groups (18 total)
              ← invariants (15 P14 + 10 P1419)
              ← known limitations (15 total)
              ← P1.4.20 checklist (22 items)
                               ↓
              P1.4.20 Exit Seal Verification
```

**Domain models:**

| Type | Role |
|------|------|
| `P14ModuleStatus` | Status record for each P1.4 module (implemented/stub/placeholder) |
| `P14SealReadinessReport` | Structured seal readiness report with module map, CLI groups, invariants, limitations, checklist |

**Pre-built constants:**
- `P14_CLI_GROUPS` — 18 CLI command groups indexed for P1.4.20 verification
- `P14_INVARIANTS` — 15 P1.4 scope contract invariants
- `P1419_INVARIANTS` — 10 consolidation/audit-specific invariants
- `P14_KNOWN_LIMITATIONS` — 15 catalogued known limitations
- `P1420_SEAL_CHECKLIST` — 22 items for P1.4.20 exit seal verification

**CLI:** `identity seal-readiness --json`

**Architectural law:**

- P1.4.19 is consolidation, not new governance — it adds no authority, permission, or tool changes.
- P1.4.19 prepares P1.4.20 and does not replace it — the seal-readiness report identifies what must be verified, not performs the seal.
- All indexes (`P14_CLI_GROUPS`, `P14_INVARIANTS`, `P1419_INVARIANTS`, `P14_KNOWN_LIMITATIONS`, `P1420_SEAL_CHECKLIST`) are canonical for P1.4.20 verification.
- P1.4.19 does not overclaim autonomy, claim production readiness, claim ABOS/AETHER implementation, grant authority, or mutate state.

## P1.4.20 P1.4 Identity & Autonomy Exit Seal

The exit seal is the **final P1.4 boundary verification layer**. It validates — does not add governance. It runs 56 seal checks across 5 categories and produces a seal result that is honest about what P1.4 has and hasn't achieved.

**Core module:** `src/agentic_runtime/identity/p14_exit_seal.py`

**Data flow:**
```
P1.4.19 Seal Readiness → structured P1.4 inventory
                               ↓
              P1.4.20 Exit Seal Verification
              ← import/object checks (P1.4 modules load correctly)
              ← CLI checks (p14-seal commands accessible)
              ← governance invariants (P14_INVARIANTS, P1419_INVARIANTS)
              ← adversarial checks (edge cases, boundary violations)
              ← docs consistency (agent/*.md, docs/*.md synced)
                               ↓
              Seal Result: SEALED_WITH_LIMITATIONS
                               ↓
              P1.5.0 Evaluation Mirror Foundation
```

**Seal check registry:** 56 checks across 5 categories — `identity p14-seal run/list-checks/run-check`

**CLI:** `identity p14-seal run/list-checks/run-check --json` — read-only, no mutation, no authority grant, no consent grant

**Architectural law:**

- P1.4.20 is the final boundary seal for P1.4 — it validates, it does not add governance.
- SEALED_WITH_LIMITATIONS is the honest outcome — limitations are explicit and documented.
- The seal is read-only by construction — repeated calls produce identical output, no side effects.
- P1.5.0 Evaluation Mirror Foundation is the next phase.
- The seal does not execute tools, grant consent, mutate identity sources, or change runtime state.
- 15 known limitations carry forward from P1.4.19.

**Seal result for P1.4 foundation: SEALED_WITH_LIMITATIONS.** P1.4.20 is the final P1.4 patch.

## P1.4.17 Agent Lifecycle Eligibility State Machine

The lifecycle state machine is an **eligibility layer**, not a permission layer. It sits above P1.4.16 (Identity Test Battery) and below P1.4.18 (Trust Evidence Linkage), determining which agentic lanes an agent is eligible for based on its current lifecycle state.

**Core module:** `src/agentic_runtime/identity/agent_lifecycle.py`

**Data flow:**
```
P1.4.16 Battery → aggregate PASSED/FAILED status
                         ↓
           P1.4.17 Lifecycle ← reads battery status
           (eligibility, not permission)
                         ↓
       P1.4.18 Trust Evidence Linkage
```

**Lifecycle states (8):**

| State | Meaning | Lane Eligibility |
|-------|---------|-----------------|
| DRAFT | Under construction | Read-only lanes |
| ACTIVE | Operational | Gated lane set |
| SUSPENDED | Temporarily paused | Read-only lanes |
| RESTRICTED | Reason-sensitive limits | Varies by reason |
| MAINTENANCE | Under operator maintenance | Read-only lanes |
| DEPRECATED | Scheduled for removal | Read-only lanes |
| ARCHIVED | Retired, read-only history | Read-only lanes |
| REVOKED | Terminal revocation | No lanes |

**Lane model:** Each state maps eligible/blocked lanes + required gates across 9 lanes. Replaces per-agent tool boolean flags with structured lane eligibility.

**Architectural law:**

- Lifecycle determines lane eligibility, not permission — Policy, HITL, and Operator Consent remain the permission authorities.
- Lifecycle state changes are Operator-initiated; the recommendation engine only reads governance signals.
- REVOKED is terminal and irreversible — no lanes, no transitions out, hard-fail-closed.
- DRAFT→ACTIVE is denied — an agent must pass through structured activation, not self-promote.
- SUSPENDED→ACTIVE is denied — reactivation requires explicit Operator approval.
- RESTRICTED is reason-sensitive — lane blocking depends on the transition reason, not a blanket.
- ACTIVE is gated — explicit lane eligibility, not unlimited access.
- All validation and recommendation is read-only — no mutation of identity sources, no consent grants, no tool execution.
- 17 invariants (INV-P1417-01 through INV-P1417-17) enforce these laws at validation time.

## Roadmap v3.2 — System Architecture (P1.5.0)

> **Historical / Reference Notice:** This section preserves v3.2 macro architecture reference (`HISTORICAL_REFERENCE`). Active roadmap canon is Aurel Roadmap v5.5 in `agent/ROADMAP.md`. Current Shell surface taxonomy follows P2.0+ seven-surface canon (Aurel CRO, HQ, CORP, HUB, IDE, SYSTEM, Settings). See `agent/CANON_INDEX.md`.

### Aurel Core vs independent Hub tools

```
Aurel Core     — sovereign intelligence, governance, orchestration, memory, evidence, fusion
HQ             — Aurel-native command center
A-Hub          — independent ABOS / business / agency operating tool (AgencyHub)
S-Hub          — independent knowledge / source / artifact / media studio (StudioHub)
L-Hub          — independent model / agent / LoRA / dataset / flow laboratory (LabHub)
IDE            — independent engineering / coding / terminal / repo tool
```

A-Hub, S-Hub, L-Hub, and IDE are **independent tools** with their own native LLM/runtime layers. Aurel can coordinate, govern, audit, receive handoffs, request evidence, and promote memory/dataset/skill/canon when authorized. Users can also use Hub tools without Aurel.

**Hub memory does not automatically become Aurel Core memory.**

| Memory domain | Scope |
|---------------|-------|
| Aurel Core Memory | Sovereign agent memory, governed writes, promotion gates |
| ABOS Corporate Memory | A-Hub business/agency context |
| Studio Source / Artifact Memory | S-Hub knowledge and media artifacts |
| Lab Learning / Dataset Memory | L-Hub model training and dataset candidates |
| IDE Engineering Trace Memory | IDE coding sessions and repo traces |

### Model foundation doctrine

**Sovereign open-weight lanes (foundation):** Mistral, DeepSeek, GLM, Llama families.

**External API escalation lanes (optional):** Codex, GPT/GPT-5.5, Claude/Opus, Gemini, OpenRouter, other external APIs. External API lanes are **not** Aurel's identity foundation.

### Dual auto-modeling doctrine (future)

- **Model-of-Models** — which model is good for which job
- **Model-of-Work** — how a type of work should flow through Aurel/Core/Hub systems
- Fusion runtime should eventually use both (not implemented in P1.5.0)

### P1.5 vs P4 Evaluation Mirror distinction

| Layer | Scope |
|-------|-------|
| **P1.5** | Minimal verified capability evidence foundation — domains, subjects, scopes, criteria, run envelopes |
| **P4** | Full Evaluation Mirror across Aurel Core, Hub outputs, model lanes, memory, context packs, artifacts, IDE patches, dataset candidates |

P1.5.0 does **not** implement scoring engines, benchmark runners, Model-of-Models, Model-of-Work, or Hub-native evaluation.

## P1.5.0 Evaluation Mirror Foundation Gate

**Core module:** `src/agentic_runtime/evaluation/evaluation_foundation.py`

**Core law:** No capability claim may become VERIFIED without evaluation evidence.

**Data flow:**
```
P1.4.20 Seal (SEALED_WITH_LIMITATIONS)
         ↓
P1.5.0 Evaluation Foundation
  ← EvaluationDomain / EvaluationSubjectType (closed-world)
  ← EvaluationSubject (typed, evidence-ref-bound)
  ← EvaluationScope (domain-scoped, non-goals explicit)
  ← EvaluationCriterion (required, evidence_required)
  ← EvaluationRunEnvelope (auditable run prep — does NOT verify capability)
         ↓
P1.5.1 Evaluation Object Model (next)
```

**CLI:** `evaluation foundation status/scope --json` — read-only, no capability verification, no claim/lifecycle/trust mutation.

**Architectural law:**

- P1.5.0 starts only after P1.4.20 seal.
- EvaluationRunEnvelope prepares an auditable run — it does not itself verify capability.
- P1.5.0 is foundation, not full P4 Evaluation Mirror.
- Roadmap v3.2 is a macro update, not a reset. P22–P24 are added but not started.
- P1.5.1 Evaluation Object Model is the next coding module.
