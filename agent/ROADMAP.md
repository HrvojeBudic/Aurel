# Roadmap

**Macro roadmap version:** Aurel Roadmap v5.1 — Integration-First (evolved from v3.2 macro structure)

## Integration-First law

Every completed Pn.x section must produce a vertical slice:

1. **Backend capability** — real modules, not mocks
2. **Versioned contract/schema** — deterministic, hash-ready read model
3. **Projection/API/CLI-readable state** — honest availability and readiness
4. **Shell/CLI/TUI binding** — or explicit UNAVAILABLE reason
5. **Trace/evidence/report binding** — audit-ready artifacts

Backend remains source of truth. Shell/CLI/TUI are projection surfaces. Mock data is forbidden as operational truth; fixtures must be labeled `DEV_FIXTURE`.

## Current phase

**P1.8.14 complete** — Delegation Trace/Audit BridgeRef Model: DelegationTraceAuditBridgeKind (TRACE_BRIDGE/AUDIT_BRIDGE/LEDGER_BRIDGE/TRACE_EVENT_INTENT/AUDIT_EVENT_INTENT/LEDGER_ENTRY_PLACEHOLDER/REPLAY_CONTEXT/FORK_CONTEXT/CAUSAL_CHAIN_CONTEXT/REFERENCE_ONLY/UNKNOWN), DelegationTraceAuditBridgeReferenceStatus (REFERENCE_ONLY/TRACE_BRIDGE_REFERENCED/AUDIT_BRIDGE_REFERENCED/LEDGER_BRIDGE_REFERENCED/TRACE_EVENT_INTENT_REFERENCED/AUDIT_EVENT_INTENT_REFERENCED/LEDGER_ENTRY_PLACEHOLDER_REFERENCED/REPLAY_CONTEXT_REFERENCED/FORK_CONTEXT_REFERENCED/CAUSAL_CHAIN_CONTEXT_REFERENCED/TRACE_WRITER_UNAVAILABLE/AUDIT_WRITER_UNAVAILABLE/LEDGER_WRITER_UNAVAILABLE/REPLAY_ENGINE_UNAVAILABLE/FORK_ENGINE_UNAVAILABLE/CAUSAL_VERIFIER_UNAVAILABLE/EVIDENCE_VERIFIER_UNAVAILABLE/OUTPUT_PASSPORT_UNAVAILABLE/UNAVAILABLE/ERROR/UNKNOWN), DelegationTraceAuditBridgeStatus (REFERENCE_ONLY/DECLARED/UNAVAILABLE/ERROR/UNKNOWN), DelegationTraceContextKind (TRACE_EVENT_CONTEXT/TRACE_CHAIN_CONTEXT/TRACE_REPLAY_CONTEXT/TRACE_FORK_CONTEXT/TRACE_CAUSAL_CONTEXT/TRACE_EVIDENCE_CONTEXT/UNKNOWN), DelegationAuditContextKind (AUDIT_EVENT_CONTEXT/AUDIT_RECORD_CONTEXT/AUDIT_EVIDENCE_CONTEXT/AUDIT_REVIEW_CONTEXT/AUDIT_LEDGER_CONTEXT/AUDIT_OUTPUT_PASSPORT_CONTEXT/UNKNOWN), DelegationTraceAuditReadinessFamily (20 context families), DelegationTraceBridgeRef/AuditBridgeRef/LedgerBridgeRef/TraceEventIntentRef/AuditEventIntentRef/LedgerEntryPlaceholderRef/ReplayContextRef/ForkContextRef/CausalChainContextRef/TraceAuditReadinessMatrixEntry/TraceAuditReadinessMatrix/TraceAuditReadinessProfile/TraceAuditBridgeEnvelope/TraceAuditBridgeBinding/TraceAuditBridgeBindingSet/SideEffects/StatusReport, 16 all-false side-effects, deterministic hashing for all 18 contracts, closed-world validation, DEV_FIXTURE focused test chain (65 tests), 20 unavailable surface reasons. TraceBridgeRef exists ≠ trace written. AuditBridgeRef exists ≠ audit completed. LedgerBridgeRef exists ≠ Ledger entry written. TraceEventIntentRef exists ≠ trace event emitted. AuditEventIntentRef exists ≠ audit event emitted. LedgerEntryPlaceholderRef exists ≠ Ledger entry. ReplayContextRef exists ≠ replay executed. ForkContextRef exists ≠ fork created. CausalChainContextRef exists ≠ causal chain verified. TraceAuditReadinessMatrix exists ≠ TRACE_VERIFIED. TraceAuditReadinessProfile exists ≠ audit readiness proof. Trace/audit hash exists ≠ TRACE_VERIFIED. TraceAuditBridgeEnvelope ≠ trace write, audit finality, Ledger write. No trace writer/audit writer/Ledger writer/event emission/audit finality/replay/fork/causal verification/evidence verification/Output Passport/P1.9/trace verification/Ledger finality/global trace/runtime mutation. No P1.8.15. No P1.9. Next: **P1.8.15 — Delegation Accountability Packet / Integration SummaryRef Model**.

**P1.8.10 complete** — Delegation Shadow Resolver / Consistency Model: DelegationShadowResolverMode (SHADOW_ONLY/DIAGNOSTIC_ONLY/REFERENCE_ONLY/UNAVAILABLE/UNKNOWN), DelegationConsistencyFamily (FOUNDATION/IDENTITY/ROLES/CONSTRAINTS/AUTHORITY/NON_REPUDIATION/IDENTITY_MESH/SCOPE/LIFECYCLE/CHAIN/UNKNOWN), DelegationConsistencyFindingKind (PRESENT/MISSING/MISMATCH/CONFLICT_REFERENCED/UNAVAILABLE/REFERENCE_ONLY/UNKNOWN), DelegationConsistencySeverity (INFO/NOTICE/WARNING/ERROR/UNKNOWN), DelegationShadowResolverStatus (REFERENCE_ONLY/DIAGNOSTIC_ONLY/SHADOW_EVALUATED/UNAVAILABLE/ERROR/UNKNOWN), DelegationShadowResolverInputEnvelope/ConsistencyFinding/ConsistencyMatrixEntry/ConsistencyMatrix/ShadowResolverReadinessProfile/ConsistencySnapshot/ShadowResolverResult/SideEffects/StatusReport, 13 all-false side-effects, deterministic input_envelope/finding/entry/matrix/readiness/snapshot/result/status hashes, closed-world validation, DEV_FIXTURE focused test chain (70 tests), 20 unavailable surface reasons. ShadowResolverResult exists ≠ policy decision. ConsistencySnapshot exists ≠ delegation verified. ConsistencyMatrix exists ≠ approval matrix. ConsistencyFinding exists ≠ enforcement action. CONFLICT_REFERENCED ≠ runtime denial. PRESENT ≠ verified. MISSING ≠ failed. ReadinessProfile ≠ approval readiness. Resolver hash ≠ TRACE_VERIFIED. Shadow pass ≠ allowed. Shadow fail ≠ blocked. No policy/Custos/approval/authority grant-deny/enforcement/execution/trace/Ledger/mutation. No P1.8.11, no P1.9. P1.8 remains in progress. Next: **P1.8.11 — Delegation Operator Review / ApprovalIntentRef Model**.

**P1.8.7 complete** — Delegation Scope / Boundary Model: DelegationScopeKind (TASK_SCOPE/TOOL_SCOPE/DATA_SCOPE/MEMORY_SCOPE/PATH_SCOPE/RUNTIME_SCOPE/AGENT_SCOPE/MODEL_SCOPE/NETWORK_SCOPE/APPROVAL_SCOPE/TIME_SCOPE/RISK_SCOPE/UNKNOWN), DelegationBoundaryKind (INCLUSION/EXCLUSION/LIMIT/REQUIREMENT/REFERENCE_ONLY/UNAVAILABLE/UNKNOWN), DelegationScopeDimension (TOOL/DATA/MEMORY/PATH/RUNTIME/AGENT/MODEL/NETWORK/HUMAN_APPROVAL/TIME/RISK/UNKNOWN), DelegationBoundaryPosture (IN_SCOPE/OUT_OF_SCOPE/REFERENCE_ONLY/UNAVAILABLE/UNKNOWN), DelegationScopeStatus (REFERENCE_ONLY/DECLARED/UNAVAILABLE/ERROR/UNKNOWN), DelegationScopeRef, DelegationBoundaryRef, DelegationScopeInclusionRef, DelegationScopeExclusionRef, DelegationBoundaryMatrixEntry, DelegationBoundaryMatrix, DelegationScopeReadinessProfile, DelegationScopeEnvelope, DelegationScopeBinding, DelegationScopeBindingSet, DelegationScopeSideEffects (15 all-false booleans), DelegationScopeStatusReport, deterministic scope/boundary/inclusion/exclusion/matrix/readiness/envelope/binding/set/status hashes, closed-world validation, DEV_FIXTURE focused test chain (82 tests), 18 unavailable surface reasons, side-effect truth all false. DelegationScopeRef exists ≠ permission granted. DelegationBoundaryRef exists ≠ boundary enforced. ScopeEnvelope exists ≠ runtime access control. BoundaryMatrix exists ≠ enforcement matrix. IN_SCOPE ≠ allowed. OUT_OF_SCOPE ≠ blocked. InclusionRef ≠ permission. ExclusionRef ≠ denial. ScopeReadinessProfile ≠ enforcement readiness guarantee. Scope hash ≠ TRACE_VERIFIED. scope_envelope_hash ≠ TRACE_VERIFIED. scope_binding_set_hash ≠ proof of enforcement. No permission/access/boundary/runtime/tool/data/memory/path/network mutation, no policy/Custos/approval/Ledger/trace, no P1.8.8, no P1.9. P1.8 remains in progress. Next: **P1.8.8 — Delegation Expiry / RevocationRef Model**.

**P1.8.5 complete** — Non-RepudiationRef Binding / Evidence Hook: DelegationEvidenceKind (DOCUMENT_REF/ARTIFACT_REF/TRACE_REF/SIGNATURE_REF/ATTESTATION_REF/OPERATOR_STATEMENT_REF/SYSTEM_EVENT_REF/EXTERNAL_REF/UNKNOWN), DelegationEvidenceStatus (REFERENCE_ONLY/DECLARED/UNAVAILABLE/ERROR/UNKNOWN), DelegationProofReferenceStatus (REFERENCE_ONLY/EVIDENCE_REFERENCED/CLAIM_REFERENCED/ATTESTATION_REFERENCED/SIGNATURE_REFERENCED/TRACE_REFERENCED/VERIFIER_UNAVAILABLE/UNAVAILABLE/ERROR/UNKNOWN), DelegationDisputeReadinessStatus, DelegationEvidenceRef, DelegationNonRepudiationClaimRef, DelegationEvidenceEnvelope, DelegationEvidenceCompletenessProfile, DelegationNonRepudiationBinding, DelegationNonRepudiationBindingSet, DelegationNonRepudiationSideEffects (14 all-false booleans), DelegationNonRepudiationStatusReport, deterministic evidence/claim/envelope/profile/binding/set/status hashes, closed-world validation, DEV_FIXTURE focused test chain (51 tests), 16 unavailable surface reasons, side-effect truth all false. NonRepudiationRef exists ≠ non-repudiation proven. EvidenceRef exists ≠ evidence verified. ClaimRef exists ≠ claim proven. AttestationRef exists ≠ attestation verified. SignatureRef exists ≠ signature verified. TraceRef exists ≠ TRACE_VERIFIED. EvidenceEnvelope exists ≠ legal finality. CompletenessProfile exists ≠ trust score. Evidence hash exists ≠ proof. evidence_envelope_hash exists ≠ legal finality. non_repudiation_binding_set_hash exists ≠ proof of non-repudiation. No crypto/signature/trace/evidence/claim/attestation verifier, no Ledger/global trace write, no Output Passport/P1.9, no identity mesh/P1.8.6. P1.8 remains in progress. Next: **P1.8.6 — AgentIdentityMeshRef Binding / Mesh Hook**.

**P1.8.4 complete** — Delegation authority-reference binding: DelegationAuthorityRefKind (OPERATOR_DECLARED/POLICY_CONTEXT_REFERENCED/PATH_AUTHORITY_REFERENCED/SYSTEM_DECLARED/CONSTRAINT_CONTEXT_REFERENCED/UNKNOWN), DelegationAuthorityRefStatus (REFERENCE_ONLY/DECLARED/UNAVAILABLE/ERROR/UNKNOWN), DelegationAuthorityRef, DelegationAuthorityBinding, DelegationAuthorityBindingSet, DelegationAuthoritySideEffects (11 all-false booleans), DelegationAuthorityStatusReport, deterministic authority ref/binding/set/status hashes, closed-world validation, DEV_FIXTURE focused test chain, 16 unavailable surface reasons, side-effect truth all false. AuthorityRef exists ≠ authority granted. Authority basis ≠ authority verified. Policy context ref ≠ policy/Custos decision. Path authority ref ≠ path authorized. Operator declaration ≠ authority proven. Authority binding ≠ approval/permission. Authority hash ≠ TRACE_VERIFIED. Authority binding set ≠ runtime execution. Authority model ≠ resolver. No authority resolver, verifier, grant, policy/Custos, approval, permission, path authorization, constraint enforcement, crypto signing, trace/Ledger, CLI/TUI/projection/API, or non-repudiation verifier. P1.8 remains in progress. Next: **P1.8.5 — Non-RepudiationRef Binding / Evidence Hook**.

**P1.8.3 complete** — Delegation constraint model: DelegationConstraintSeverity (INFO/LOW/MEDIUM/HIGH/CRITICAL/UNKNOWN), DelegationConstraintStatus (DECLARED/REFERENCE_ONLY/UNAVAILABLE/ERROR/UNKNOWN), DelegationConstraintRef, DelegationConstraintBinding, DelegationConstraintSet, DelegationConstraintSideEffects (12 all-false booleans), DelegationConstraintStatusReport, deterministic constraint/binding/set/status hashes, closed-world validation, DEV_FIXTURE focused test chain, 17 unavailable surface reasons, side-effect truth all false. Constraint exists ≠ constraint enforced. Required review exists ≠ approval created. Risk bound exists ≠ policy/Custos decision. Tool bound exists ≠ tool permission changed. Data bound exists ≠ data access changed. Time bound exists ≠ scheduler changed. Constraint hash exists ≠ TRACE_VERIFIED. Constraint set exists ≠ runtime blocking. Constraint model exists ≠ resolver exists. Constraint binding exists ≠ authority granted. No delegation resolver, chain resolver, authority bridge, non-repudiation verifier, crypto signing, policy/Custos, approval, Ledger, global trace write, CLI/TUI/projection/API, agent activation, or identity mesh resolver. P1.8 remains in progress. Next: **P1.8.4 — Delegation AuthorityRef Binding**.

    | Status | Module |
    |--------|--------|
    | **Last completed** | P1.8.5 — Non-RepudiationRef Binding / Evidence Hook |
    | **Current active** | **P1.8.6 — AgentIdentityMeshRef Binding / Mesh Hook (planned)** |
    | **Previous section** | P1.7 — Path Governance & Source Trust (**SEALED**) |
    | **Next planned** | P1.8.6 — AgentIdentityMeshRef Binding / Mesh Hook |

**P1.8.4 complete** — Delegation authority-reference binding: DelegationAuthorityRefKind (OPERATOR_DECLARED/POLICY_CONTEXT_REFERENCED/PATH_AUTHORITY_REFERENCED/SYSTEM_DECLARED/CONSTRAINT_CONTEXT_REFERENCED/UNKNOWN), DelegationAuthorityRefStatus (REFERENCE_ONLY/DECLARED/UNAVAILABLE/ERROR/UNKNOWN), DelegationAuthorityRef, DelegationAuthorityBinding, DelegationAuthorityBindingSet, DelegationAuthoritySideEffects (11 all-false booleans), DelegationAuthorityStatusReport, deterministic authority ref/binding/set/status hashes, closed-world validation, DEV_FIXTURE focused test chain, 16 unavailable surface reasons, side-effect truth all false. AuthorityRef exists ≠ authority granted. Authority basis ≠ authority verified. Policy context ref ≠ policy/Custos decision. Path authority ref ≠ path authorized. Operator declaration ≠ authority proven. Authority binding ≠ approval/permission. Authority hash ≠ TRACE_VERIFIED. Authority binding set ≠ runtime execution. Authority model ≠ resolver. No authority resolver, verifier, grant, policy/Custos, approval, permission, path authorization, constraint enforcement, crypto signing, trace/Ledger, CLI/TUI/projection/API, or non-repudiation verifier. P1.8 remains in progress. Next: **P1.8.5 — Non-RepudiationRef Binding / Evidence Hook**.

**P1.8.3 complete** — Delegation constraint model: DelegationConstraintSeverity (INFO/LOW/MEDIUM/HIGH/CRITICAL/UNKNOWN), DelegationConstraintStatus (DECLARED/REFERENCE_ONLY/UNAVAILABLE/ERROR/UNKNOWN), DelegationConstraintRef, DelegationConstraintBinding, DelegationConstraintSet, DelegationConstraintSideEffects (12 all-false booleans), DelegationConstraintStatusReport, deterministic constraint/binding/set/status hashes, closed-world validation, DEV_FIXTURE focused test chain, 17 unavailable surface reasons, side-effect truth all false. Constraint exists ≠ constraint enforced. Required review exists ≠ approval created. Risk bound exists ≠ policy/Custos decision. Tool bound exists ≠ tool permission changed. Data bound exists ≠ data access changed. Time bound exists ≠ scheduler changed. Constraint hash exists ≠ TRACE_VERIFIED. Constraint set exists ≠ runtime blocking. Constraint model exists ≠ resolver exists. Constraint binding exists ≠ authority granted. No delegation resolver, chain resolver, authority bridge, non-repudiation verifier, crypto signing, policy/Custos, approval, Ledger, global trace write, CLI/TUI/projection/API, agent activation, or identity mesh resolver. P1.8 remains in progress. Next: **P1.8.4 — Delegation AuthorityRef Binding**.

**P1.8.1 complete** — Delegation identity/ref: `DelegationIdentityKind`, `DelegationIdentityStatus`, `DelegationRefBindingKind`, `DelegationRef`, `DelegationIdentity`, `DelegationRefBinding`, `DelegationIdentitySideEffects`, `DelegationIdentityStatusReport`, `build_delegation_*()` helpers, `serialize_delegation_ref/identity()`, `hash_delegation_ref/identity()`, DEV_FIXTURE focused test chain, deterministic ref/binding/identity/status hashes, unavailable surface reasons, side-effect truth all false, closed-world validation. DelegationRef is not approval; DelegationIdentity is not verification; DelegationRefBinding is not trace proof; record_hash is not TRACE_VERIFIED; identity_hash is not proof; no delegation resolver, non-repudiation verifier, crypto signing, policy/Custos, approval, Ledger, global trace write, CLI/TUI/projection/API, runtime execution, or agent activation. P1.8 remains in progress. Next: **P1.8.2 — Delegator / Delegate / Subject Model**.

**P1.8.0 complete** — Delegation foundation: `DelegationSourceLabel`, `DelegationActorKind`, `DelegationSubjectKind`, `DelegationAuthorityKind`, `DelegationConstraintKind`, `NonRepudiationProofStatus`, `DelegationFoundationCapability`, `DelegationActorRef`, `DelegationSubject`, `DelegationAuthorityRef`, `DelegationConstraint`, `NonRepudiationRef`, `AgentIdentityMeshRef`, `DelegationSideEffects`, `DelegationRecord`, `DelegationFoundationStatus`, `build_delegation_*()` helpers, `serialize_delegation_record()`, `hash_delegation_record()`, DEV_FIXTURE focused test chain, deterministic record/status hashes, unavailable surface reasons, side-effect truth all false, closed-world validation. Foundation schema only; DelegationRecord is not permission; AuthorityRef is not granted authority; NonRepudiationRef is not verified proof; AgentIdentityMeshRef is not live mesh activation; no delegation resolver, non-repudiation verifier, crypto signing, policy/Custos, approval, Ledger, global trace write, CLI/TUI/projection/API, runtime execution, or agent activation. P1.8 remains in progress. Next: **P1.8.1 — Delegation Identity / DelegationRef Schema**.

**P1.7.20 complete** — Exit seal + live integration demo: `PathGovernanceExitSealCheckKind`, `PathGovernanceExitSealStatus`, `PathGovernanceExitSealSideEffects`, `PathGovernanceExitSealCheckResult`, `PathGovernanceExitSealDemoInput`, `PathGovernanceExitSealResult`, `build_path_governance_exit_seal_demo_input()`, `build_default_path_governance_exit_seal_checks()`, `run_path_governance_exit_seal()`, `render_path_governance_exit_seal_summary()`, DEV_FIXTURE vertical slice demo chain, deterministic seal hashes, unavailable state proof, side-effect truth all false, closed-world validation. Evidence-only seal; no policy engine, Custos, approval, Ledger, global trace write, enforcement, source mutation, Shell UI, HTTP server, or sandbox changes. **P1.7 is sealed.** Next: **P1.8.0 — Delegation / Non-Repudiation / Agent Identity Mesh**.

**P1.7.19 complete** — Docs/state/reports truth sync: P1.7.0–P1.7.18 report inventory, shadow-only boundaries (P1.7.10–P1.7.12), trace/Ledger boundaries (P1.7.13–P1.7.14), DEV_FIXTURE harness boundary (P1.7.15), policy context packet boundary (P1.7.16), projection read-model boundary (P1.7.17), read-only CLI boundary (P1.7.18), source-label truth, known UNAVAILABLE states, P1.7.20 readiness checklist, docs consistency test. Evidence metadata sync only; no runtime behavior, policy runtime, Ledger write, global trace write, enforcement, source mutation, Shell UI, HTTP server, or sandbox changes.

**P1.7.18 complete** — Path governance CLI/TUI binding: `PathGovernanceCliCommandKind`, `PathGovernanceCliOutputFormat`, `PathGovernanceCliBindingMode`, `PathGovernanceCliSideEffects`, `PathGovernanceCliRequest`, `PathGovernanceCliRenderedLine`, `PathGovernanceCliResponse`, `build_path_governance_cli_request()`, `render_path_governance_status_text()`, `render_path_governance_capability_table()`, `render_path_governance_json_payload()`, `render_path_governance_cli_response()`, `handle_path_governance_cli_request()`, read-only `path-governance` CLI subcommands, deterministic request/line/response hashes, source-label truth, unavailable reason visibility, side-effect truth booleans all false, and closed-world validation. Read-only projection binding; CLI exposes state and does not execute policy; no Shell UI, Web UI, HTTP server, policy engine integration, approval activation, Ledger write, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, or runtime enforcement. P1.7 remains in progress. Next: **P1.7.19 — Docs/State/Reports Update**.

**P1.7.17 complete** — Path governance projection/API/event contract: `PathGovernanceCapabilityKind`, `PathGovernanceProjectionEventKind`, `PathGovernanceProjectionRecord`, `PathGovernanceReadModel`, `PathGovernanceProjectionEvent`, `PathGovernanceApiEnvelope`, `build_path_governance_projection_record()`, `build_path_governance_read_model()`, `build_path_governance_projection_event()`, `build_path_governance_api_envelope()`, `build_default_path_governance_capability_projection()`, deterministic record/read-model/event/envelope identifiers and hashes, default P1.7.0–P1.7.17 capability projection, CLI_TUI_BINDING marked UNAVAILABLE, source-label truth, unavailable reason handling, and closed-world validation. Read-model only; projection exposes state and does not execute state; no CLI/TUI, Shell UI, HTTP server, policy engine integration, approval activation, Ledger write, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, or runtime enforcement. P1.7 remains in progress. Next: **P1.7.18 — Path Governance CLI/TUI Binding**.

**P1.7.16 complete** — Policy context bridge: `PathPolicyContextSubjectKind`, `PathPolicyDecisionSurface`, `PathPolicyRequirementKind`, `PathPolicyBridgeMode`, `PathPolicyBridgeDisposition`, `PathPolicyContextInput`, `PathPolicyContextSubjectRef`, `PathPolicyContextPacket`, `PathPolicyContextBridgeResult`, `build_path_policy_context_subject_ref()`, `derive_path_policy_requirements()`, `build_path_policy_context_packet()`, `bridge_path_governance_to_policy_context()`, deterministic input/subject/packet/bridge identifiers and hashes, advisory requirement derivation, source-label truth, and closed-world validation. Context-only bridge with `policy_called=false`, `policy_decision_made=false`, `approval_created=false`, `ledger_written=false`, `runtime_mutated=false`, and `enforcement_triggered=false`; no policy engine integration, approval activation, Ledger write, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement, CLI/TUI, or Shell UI. P1.7 remains in progress. Next: **P1.7.17 — Path Governance Projection/API/Event Contract**.

**P1.7.15 complete** — Path governance test harness: `PathGovernanceHarnessScenarioKind`, `PathGovernanceHarnessExpectation`, `PathGovernanceHarnessStatus`, `PathGovernanceHarnessScenario`, `PathGovernanceHarnessRunInput`, `PathGovernanceHarnessStepResult`, `PathGovernanceHarnessRunResult`, `build_path_governance_harness_scenario()`, `build_default_path_governance_harness_suite()`, `run_path_governance_harness_scenario()`, `run_path_governance_harness_suite()`, deterministic scenario/run/step/result identifiers and hashes, default DEV_FIXTURE scenario suite, advisory expectation checks, source-label truth, and closed-world validation. Shadow-chain harness only; harness pass is not allow and harness fail is not deny; no policy engine integration, approval activation, Ledger write, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement, CLI/TUI, or Shell UI. P1.7 remains in progress. Next: **P1.7.16 — Policy Context Bridge**.

**P1.7.14 complete** — Path violation/drift trace hook: `PathViolationTraceEventKind`, `PathViolationSeverity`, `PathViolationTraceHookMode`, `PathViolationTraceDisposition`, `PathViolationTraceReason`, `PathViolationTraceInput`, `PathViolationTracePayload`, `PathViolationTraceHookResult`, `PathSourceDriftSignal`, `build_path_violation_trace_payload()`, `record_path_violation_trace_hook()`, `detect_path_source_drift_signals()`, deterministic input/payload/hook/drift-signal identifiers and hashes, observational `violation_summary`, expected/current refs, drift reasons, source-label truth, and closed-world validation. Observability-only violation/drift hook with `PAYLOAD_ONLY` default, optional injected sink, `ledger_written=false`, `runtime_mutated=false`, and `enforcement_triggered=false`; no correction, rollback, global trace spine write by default, fake TRACE_VERIFIED, policy engine integration, approval activation, Ledger write, source trust mutation, source blocking, runtime quarantine, memory canonization, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement, CLI/TUI, or Shell UI. P1.7 remains in progress. Next: **P1.7.15 — Path Governance Test Harness**.

**P1.7.13 complete** — Path resolution trace hook: `PathResolutionTraceEventKind`, `PathResolutionTraceHookMode`, `PathResolutionTraceDisposition`, `PathResolutionTraceReason`, `PathResolutionTraceInput`, `PathResolutionTracePayload`, `PathResolutionTraceHookResult`, `build_path_resolution_trace_payload()`, `record_path_resolution_trace_hook()`, deterministic input/payload/hook identifiers and hashes, advisory `decision_summary`, source-label truth, and closed-world validation. Observability-only trace hook with `PAYLOAD_ONLY` default, optional injected sink, `ledger_written=false`, and `runtime_mutated=false`; no global trace spine write by default, fake TRACE_VERIFIED, policy engine integration, approval activation, Ledger write, source trust mutation, source blocking, runtime quarantine, memory canonization, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement, CLI/TUI, or Shell UI. P1.7 remains in progress. Next: **P1.7.14 — Path Violation / Drift Trace Hook**.

**P1.7.12 complete** — Path/source conflict & precedence shadow rules: `PathSourceConflictKind`, `PrecedenceRuleKind`, `ConflictSeverity`, `ConflictPrecedencePosture`, `PathSourceConflictSignal`, `PrecedenceRule`, `ConflictPrecedenceInput`, `ConflictPrecedenceResult`, `resolve_path_source_conflicts_shadow()`, deterministic signal/rule/input/result identifiers and hashes, advisory `recommended_shadow_decision`, source-label truth, and closed-world validation. Shadow conflict/precedence only with `shadow_only=true` and `enforced=false`; no trace hooks, policy engine integration, approval activation, trace emission, Ledger write, source trust mutation, source blocking, runtime quarantine, memory canonization, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement, CLI/TUI, or Shell UI. P1.7 remains in progress. Next: **P1.7.13 — Path Resolution Trace Hook**.

**P1.7.11 complete** — Source trust resolver v0 / shadow mode: `SourceTrustShadowDecision`, `SourceTrustDecisionReason`, `SourceTrustResolverInput`, `SourceTrustResolverResult`, `resolve_source_trust_shadow()`, deterministic input/result identifiers and hashes, advisory `recommended_trust_label`, source-label truth, and closed-world validation. Shadow trust resolver only with `WOULD_*` recommendations, `shadow_only=true`, and `enforced=false`; no path/source conflict rules, precedence rules, policy engine integration, approval activation, trace emission, Ledger write, source trust mutation, source taxonomy mutation, source identity mutation, source blocking, runtime quarantine, memory canonization, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement, CLI/TUI, or Shell UI.

**P1.7.10 complete** — Path governance resolver v0 / shadow mode: `PathGovernanceShadowDecision`, `PathGovernanceDecisionReason`, `PathGovernanceResolverInput`, `PathGovernanceResolverResult`, `resolve_path_governance_shadow()`, deterministic input/result identifiers and hashes, source-label truth, and closed-world validation. Shadow resolver only with `WOULD_*` recommendations, `shadow_only=true`, and `enforced=false`; no source trust resolver, conflict rules, policy engine integration, approval activation, trace emission, Ledger write, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement, CLI/TUI, or Shell UI.

**P1.7.9 complete** — Path/source risk classification model: `PathSourceRiskLevel`, `PathSourceRiskSignalKind`, `RiskClassificationBasis`, `RiskClassificationPosture`, `PathSourceRiskSignal`, `PathSourceRiskClassification`, `PathSourceRiskRegistry`, `build_path_source_risk_signal()`, `build_path_source_risk_classification()`, `build_path_source_risk_registry()`, `derive_path_source_risk_classification()`, deterministic signal/classification/registry hashes, source-label truth, and closed-world validation. Classification-only without resolver, policy engine, approval, trace, Ledger, or enforcement.

**P1.7.8 complete** — Source provenance and evidence binding seed: `SourceProvenanceKind`, `EvidenceBindingKind`, `EvidenceConfidence`, `SourceClaimKind`, `SourceEvidenceRef`, `SourceClaimRef`, `SourceProvenanceRef`, `ProvenanceBinding`, `ProvenanceBindingRegistry`, `build_source_evidence_ref()`, `build_source_claim_ref()`, `build_source_provenance_ref()`, `build_provenance_binding()`, `build_provenance_binding_registry()`, deterministic evidence/claim/provenance/binding/registry hashes, source-label truth, and closed-world validation. Reference/binding objects only without truth verification, trace emission, Ledger writes, resolver, or enforcement. Next: **P1.7.9 — Path/Source Risk Classification Model**.

**P1.7.7 complete** — Untrusted content boundary model: `UntrustedContentKind`, `ContentInfluenceSurface`, `BoundaryRestrictionKind`, `UntrustedBoundaryPosture`, `BoundaryRestriction`, `UntrustedContentBoundary`, `UntrustedContentBoundaryRegistry`, `build_untrusted_content_boundary()`, `build_untrusted_content_boundary_registry()`, trust-label default declaration helpers, deterministic restriction/boundary/registry hashes, source-label truth, and closed-world validation. Declarative information-vs-instruction boundaries only without prompt filtering, memory gating, tool blocking, resolver, or enforcement. Next: **P1.7.8 — Source Provenance & Evidence Binding Seed**.

**P1.7.6 complete** — Path authority scope model: `PathAuthoritySubjectKind`, `PathAuthorityBasis`, `PathAuthorityConstraintKind`, `PathAuthoritySubject`, `PathAuthorityConstraint`, `PathAuthorityScope`, `PathAuthorityScopeRegistry`, `build_path_authority_scope()`, `build_path_authority_scope_registry()`, deterministic subject/constraint/scope/registry hashes, source-label truth, and closed-world validation. Declarative authority scope only without permission, resolver, sandbox policy, filesystem access, or enforcement.

**P1.7.5 complete** — Path normalization and shadow escape detection contract: `PathNormalizationStatus`, `PathEscapeSignal`, `PathNormalizationResult`, `normalize_path_for_governance()`, `PathBoundaryStatus`, `PathBoundaryCheckResult`, `EscapeDetectionContract`, `detect_path_escape_candidates()`, deterministic hashes, source-label truth, segment-aware string comparison, and closed-world validation. Shadow-only candidate classification without permission, sandbox policy, filesystem access, or enforcement.

**P1.6.20 complete** — Exit seal + live integration demo: `exit_seal.py` proof layer, 20 checks, `PASS_WITH_WARNINGS` verdict, 42 focused + 137 regression tests pass. P1.6 Integration-First vertical slice sealed. No enforcement, no Ledger writes, no runtime changes.

**P1.6.19 complete** — Policy Docs/State/Reports Update: truth-sync of roadmap, state, reports, architecture, decisions, operator runbook, source-label doctrine, P1.6.10–P1.6.19 report index, and P1.6.20 exit-seal checklist.

**P1.6.18 complete** — Policy CLI/TUI Binding: read-only `policy` CLI commands consume `PolicyProjectionContract v1` for status/projection/unavailable; harness list/run bind to P1.6.16 registry. Shell binding remains UNAVAILABLE. No enforcement, no Ledger writes.

**P1.6.17 complete** — Policy Projection/API/Event Contract: versioned read-model for P1.6 policy subsystem with source labels, readiness, deterministic hashing, and event payload seed. CLI binding added in P1.6.18; Shell remains UNAVAILABLE.

**P1.6.14 complete** — Policy Resolution Trace Hook: trace-compatible evidence envelope for policy resolution, conflict algebra, and shadow projection metadata. Produces deterministic hashes/identifiers for audit-readiness without Ledger writes.

**P1.6.10H complete** — Runtime Security, Coverage & Governance Truth Hotfix sealed runtime/security/coverage/documentation truth before registry binding. See `agent/reports/P1.6.10H_RUNTIME_SECURITY_COVERAGE_GOVERNANCE_TRUTH_HOTFIX_REPORT.md`.

**P1.6.10H complete (hotfix)** — Runtime Security, Coverage & Governance Truth Hotfix: snapshot path traversal fix, unsafe/restricted_local honesty (allow_unsafe gate in materialize_sandbox_backend), canonical validation commands (venv requirement), coverage truth (src/agentic_runtime target), sandbox layer disambiguation, local composer state exclusion. 12 new security + honesty tests.

**P1.6.9 complete** — Sandbox Policy Card Model: 6 enums (SandboxBackend, FilesystemScope, EgressPolicy, CommandClass, SandboxCommandDecision, ApprovalRequirement), backend/filesystem/egress/command-class rules, risk-tier sandbox mappings, approval policy, and a resolver-ready `evaluate_sandbox_policy_decision()` producing `SandboxPolicyDecision` (consumed by P1.6.10). Deny-by-default posture, secrets-path/escape detection, deterministic serialization + hash — semantics only, no real sandbox execution, no Docker/Bubblewrap hard dependency.

**P1.6.8S stabilization complete** — Repository Reality & Policy Card Stabilization Seal: reconciles git/docs/test/lint reality after P1.6.8, preserves legitimate P1.6.4-P1.6.8 policy-card artifacts for final staging, fixes bare-python CLI subprocess tests through a shared helper, clears ruff/mypy/full-suite/coverage validation, records deferred structural debt, and keeps P1.6.9 as the next feature phase. No Sandbox Policy Card behavior is implemented here.

**P1.6.8 complete** — Prompt Policy Card Model: 7 enums (PromptSourceType 19 values, PromptTrustLevel 10 values, PromptRole 16 values, PromptPolicyDecision 10 values, PromptInjectionRisk 5 values, PromptInjectionPattern 15 values, PromptBoundaryRequirementType 14 values), 5 frozen dataclasses, strict deny-by-default posture, unknown-source-untrusted, external-content-not-instruction, tool-output-is-data, retrieved-memory-is-context, untrusted-cannot request-tools/write-memory/modify-policy/modify-identity, high/critical injection-risk cannot pair with permissive instruction authority, closed-world validation, deterministic serialization + hash, 15-rule strict default — semantics only, no prompt compiler / assembly engine / instruction-hierarchy enforcement / injection detector / jailbreak detector / resolver / runtime enforcement.

**P1.6.7 complete** — Memory Write Policy Card Model: 6 enums (MemoryZone 14 values, MemoryWriteType 18 values, MemoryWriteDecision 10 values, MemoryVerificationStatus 8 values, MemoryRetentionClass 6 values, MemoryWriteRequirementType 13 values), 5 frozen dataclasses, deny-by-default posture, no silent canon/policy/operator-profile writes, verified-skill verification requirement, skill-candidate-not-verified guard, credentials-not-durable, sensitive-data strictness, closed-world validation, deterministic serialization + hash, 14-rule conservative default — semantics only, no Mneme storage / retrieval / consolidation / canon promotion / skill promotion / Verification Court / resolver / runtime enforcement.

**P1.6.6 complete** — Tool Permission Policy Card Model: 5 enums (ToolCategory 17 values, ToolPermissionType 26 values, ToolPermissionDecision 8 values, ToolScopeType 12 values, ToolMatchMode 5 values), 6 frozen dataclasses, deny-by-default posture, credential access denial, shell command governance, dangerous permission safety validation, data residency compatibility, closed-world validation, deterministic serialization + hash — semantics only, no Tool Gateway / registry resolver / sandbox execution / runtime enforcement.

**P1.6.5 complete** — Data Residency Policy Card Model: 6 enums (Zone, Class, Location, RedactionType, StorageType, ExposurePermission), 20 data classes with strict local-first defaults, credentials no-egress safety, sensitive_personal_data/memory/trace local-only enforcement, forbidden zone non-permissive, closed-world validation, deterministic serialization + hash — semantics only, no runtime egress/resolution/redaction.

**P1.4.20 complete** — P1.4 Identity & Autonomy Exit Seal (**SEALED_WITH_LIMITATIONS** — 56 seal checks, 5 categories, 28 new tests, 412 identity total). **P1.4 is sealed.**

**P1.5.11B complete** — Capability Evidence ↔ Trace / Context Binding: verified capability evidence now requires source hash integrity, evidence strength `strong|verified`, verifier pass, limitations, canonical trace binding, and adequate/safe context; Golden Thread A includes `ContextBindingRef` and `ContextAdequacyReport`.

**P1.5.11A complete** — Golden Thread A Minimal Contract Harness: deterministic Intent → Context → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → CapabilityEvidence path, canonical TraceEventRef binding, verifier limitations, capability limitations, and negative tests for impossible verified states.

**P1.5.10X complete** — Single Source of Truth + TraceLog Integrity Patch: AurelTraceLog is the only canonical append-only hash-chained event source; Ledger/Evidence/Runtime/Evaluation/Mneme/Shell/Reports are projections; TraceEventRef/TraceBindingRef provide future binding targets.

**P1.5.10 complete** — Baseline Comparison Model + Sparse Comparison Readiness: categorical baseline comparison, adversarial/hygiene coverage comparison, sparse dimensions, 69 new tests.

**P1.5.9 complete** — Adversarial Evaluation Cases + Sparse Trap Readiness: adversarial case schemas, registry, resolution, 15 default trap cases, sparse trap readiness, 76 new tests.

**P1.5.8 complete** — Benchmark Hygiene Guard + Sparse Hygiene Readiness: fixture boundary model, contamination/freshness/representativeness classification, hygiene decisions, binding downgrade helper, sparse hygiene risks, 66 new tests.

**P1.5.7 complete** — Evidence-to-Claim Binding + Sparse Binding Readiness: evidence-to-claim impact modeling, 13 invariants, 76 new tests.

**P1.5.6 complete** — Result Classification Engine + Sparse Classification Readiness: supplies observation classification into evaluation semantics, 17 invariants, 74 new tests.

**P1.5.5 complete** — Evaluation Run Envelope + Sparse Run Readiness: governed envelope binding, evidence/readiness resolution, 5 sparse run bools, 54 new tests.

**P1.5.4 complete** — Evaluation Criteria Schema + Sparse Criteria Readiness: reusable criteria layer, 8 sparse criterion kinds, 64 new tests.

**P1.5.3 complete** — Evaluation Subject Registry + Sparse Cognition Readiness: governed subject registration, 9 ASCL categories, Hub origins, 75 new tests.

**P1.5.2 complete** — Capability Evidence Record: evaluation-to-evidence bridge, categorical aggregation, USABLE is not VERIFIED.

**P1.5.1 complete** — Evaluation Object Model.

Canonical P1.4 detail: `docs/P1.4_IDENTITY_AUTONOMY_SCOPE_CONTRACT.md`, `docs/P1.4_AGENT_TRUST_CONSTITUTION.md`

## Roadmap v3.2 doctrine

**Historical P1.5 note:** P1.5.11B is implemented, and later P1.5 modules advanced through the P1.5 integrated seal. P1.6 advanced through P1.6.19 truth-sync; current active work is **P1.6.20 exit seal**.

- **P1–P2 remain stable** — completed foundation is not reset.
- **P3–P21 are refined, not reset.**
- **P22–P24 are added** for L-Hub / A-Hub / S-Hub architecture (not started early).
- **P25 = Aurel v0.9** | **P30 = Aurel v1.0**
- **P25–P30 = hardening, polish, patches, deployment, stabilization**

## System map (v3.2)

```
Aurel Core          — sovereign intelligence, governance, orchestration, memory, evidence, fusion
HQ                  — Aurel-native command center
A-Hub / AgencyHub   — independent ABOS / business / agency operating tool
S-Hub / StudioHub   — independent knowledge / source / artifact / media studio
L-Hub / LabHub      — independent model / agent / LoRA / dataset / flow laboratory
IDE                 — independent engineering / coding / terminal / repo tool
```

**Hub doctrine:** A-Hub, S-Hub, L-Hub, and IDE are independent tools with their own native LLM/runtime layers. Aurel can coordinate, govern, audit, receive handoffs, request evidence, and promote memory/dataset/skill/canon when authorized. Users can also use Hub tools without Aurel.

**Execution discipline:** Do not start P22–P24 early. Finish P1.5–P1.9, then lock P2.0, then proceed through P3+.

## Near-term execution order

```
P1.5.0–P1.5.20   Evaluation Mirror & Verified Capability Evidence
P1.6.0–P1.6.20   Policy Cards & Behavioral Contracts
P1.7.0–P1.7.20   Path Governance Engine
P1.8.0–P1.8.20   Delegation / Non-Repudiation / Agent Identity Mesh
P1.9.0–P1.9.20   Provenance / Disclosure / Output Passport
P2.0.0–P2.0.20   Phase 2 lock
```

## P1.6 — Policy Cards & Behavioral Contracts (v5.1 patch table)

| Patch | Name |
| ----- | ---- |
| P1.6.0 | Policy Card Foundation |
| P1.6.1 | Policy Card Schema |
| P1.6.2 | Behavioral Contract Schema |
| P1.6.3 | Risk Tier Policy Card Model |
| P1.6.4 | Human Oversight Policy Card Model |
| P1.6.5 | Data Residency Policy Card Model |
| P1.6.6 | Tool Permission Policy Card Model |
| P1.6.7 | Memory Write Policy Card Model |
| P1.6.8 | Prompt Policy Card Model |
| P1.6.9 | Sandbox Policy Card Model |
| P1.6.10 | Custos v0 Policy Runtime Resolver / Shadow Mode |
| P1.6.10H | Runtime Security, Coverage & Governance Truth Hotfix |
| P1.6.11 | Policy Resolution Context & Registry Binding |
| P1.6.12 | Custos Shadow Runtime Projection & Submit Observability Hook |
| P1.6.13 | Policy Conflict Algebra & Strictest-Wins Rules |
| P1.6.14 | Policy Resolution Trace Hook |
| P1.6.15 | Policy Violation Trace Hook |
| P1.6.16 | Policy Test Harness |
| P1.6.17 | **Policy Projection/API/Event Contract** |
| P1.6.18 | **Policy CLI/TUI Binding** |
| P1.6.19 | **Policy Docs/State/Reports Update** |
| P1.6.20 | **P1.6 Exit Seal + Live Integration Demo** |

### P1.6.18 handoff

P1.6.18 binds `PolicyProjectionContract v1` to read-only CLI commands (`policy status`, `policy projection`, `policy unavailable`, `policy harness list/run`). Shell binding remains UNAVAILABLE. No enforcement. **P1.6.19 synchronizes documentation and prepares exit seal.**

### P1.6.19 handoff

P1.6.19 is a consolidation/audit gate: P1.6 capability map, source-label doctrine, operator runbook, reports index P1.6.10–P1.6.19, and 20-item P1.6.20 checklist. It adds no governance semantics and does not mutate runtime. **P1.6 is seal-ready. P1.6.20 performs live integration demo and exit seal verification.**

### P1.6.20 forward hook

P1.6.20 — P1.6 Exit Seal + Live Integration Demo: run checklist, produce seal report, demonstrate Integration-First vertical slice. Enforcement remains deferred to later phases (P9/P25).

## P1.7 — Path Governance Engine (v5.1 patch table — foundation started)

| Patch | Name |
| ----- | ---- |
| P1.7.0 | **Path Governance & Source Trust Foundation** |
| P1.7.1 | **Path Identity & Canonical Path Schema** |
| P1.7.2 | **Source Identity & SourceRef Schema** |
| P1.7.3 | **Source Trust Label Taxonomy** |
| P1.7.4 | **Trusted Root & Scope Registry Seed** |
| P1.7.5 | **Path Normalization & Escape Detection Contract** |
| P1.7.6 | **Path Authority Scope Model** |
| P1.7.7 | **Untrusted Content Boundary Model** |
| P1.7.8 | **Source Provenance & Evidence Binding Seed** |
| P1.7.9 | **Path/Source Risk Classification Model** |
| P1.7.10 | **Path Governance Resolver v0 / Shadow Mode** |
| P1.7.11 | **Source Trust Resolver v0 / Shadow Mode** |
| P1.7.12 | **Path/Source Conflict & Precedence Rules** |
| P1.7.13 | **Path Resolution Trace Hook** |
| P1.7.14 | **Path Violation / Drift Trace Hook** |
| P1.7.15 | **Path Governance Test Harness** |
| P1.7.16 | **Policy Context Bridge** |
| P1.7.17 | **Path Governance Projection/API/Event Contract** |
| P1.7.18 | **Path Governance CLI/TUI Binding** |
| P1.7.19 | **Docs / State / Reports Update** |
| P1.7.20 | **Exit Seal + Live Integration Demo** |

### P1.7.19 handoff

P1.7.19 is a consolidation/audit gate: P1.7 capability map, source-label doctrine, report index P1.7.0–P1.7.19, shadow-only and unavailable boundaries, and P1.7.20 exit-seal readiness checklist. It adds no governance semantics and does not mutate runtime. **P1.7 is pre-seal. P1.7.20 performs live integration demo and exit seal verification.**

### P1.7.20 forward hook

P1.7.20 — Exit Seal + Live Integration Demo: run checklist, produce seal report, demonstrate Integration-First vertical slice for path governance. Enforcement remains deferred to later phases (P9/P25). Expected: `path_governance/exit_seal.py` proof module (pattern from P1.6.20).

### P1.7.0 handoff

P1.7.0 delivers foundation vocabulary (`ProjectionSourceLabel`, `SourceTrustLabel`), posture reporting (`FoundationPosture`, `PathGovernanceCapabilityStatus`), closed-world validation, deterministic serialization, and honest UNAVAILABLE reasons. No resolver, enforcement, CLI, projection, trace hooks, or policy bridge.

### P1.7.1 handoff

P1.7.1 delivers schema-only path identity objects: `PathKind`, `PathSensitivity`, `CanonicalizationStatus`, `PathRef`, `CanonicalPathRef`, `PathIdentity`, `build_path_identity()`, deterministic `path_hash`, `canonical_hash`, `identity_hash`, and closed-world validation. It preserves raw path separately from normalized/display representation. It does not implement SourceRef, resolvers, trusted roots, path escape detection, enforcement, Ledger writes, approval activation, sandbox behavior changes, CLI/TUI, Shell UI, trace hooks, or policy bridge. **P1.7.2 — Source Identity & SourceRef Schema is next.**

### P1.7.2 handoff

P1.7.2 delivers schema-only source identity objects: `SourceKind`, `SourceOrigin`, `SourceLineageRelationship`, `SourceRef`, `SourceLineageRef`, `SourceIdentity`, `build_source_identity()`, deterministic `source_id`, `lineage_hash`, `identity_hash`, and closed-world validation. It represents source kinds, origins, and lineage seeds without trust resolution or authority. It does not implement source trust taxonomy expansion, trust resolver, authority resolver, provenance/evidence binding, memory write authority, prompt authority, command authority, untrusted content boundary decisions, network fetching, filesystem reads, enforcement, Ledger writes, approval activation, sandbox behavior changes, CLI/TUI, Shell UI, trace hooks, or policy bridge. **P1.7.3 — Source Trust Label Taxonomy is next.**

### P1.7.3 handoff

P1.7.3 delivers taxonomy-only source trust semantics: `TrustPosture`, `TrustLabelDefinition`, `SourceTrustTaxonomy`, `build_source_trust_taxonomy()`, deterministic `definition_hash`, order-insensitive `taxonomy_hash`, closed-world validation, and explicit semantic boundaries for every `SourceTrustLabel`. It defines allowed interpretations, forbidden interpretations, and authority statements without trust resolution or authority decisions. It does not implement source trust resolver, source authority resolver, untrusted content boundary decisions, provenance/evidence binding, memory write authority, prompt authority, command authority, tool permission authority, runtime enforcement, Ledger writes, approval activation, sandbox behavior changes, CLI/TUI, Shell UI, trace hooks, or policy bridge. **P1.7.4 — Trusted Root & Scope Registry Seed is next.**

### P1.7.4 handoff

P1.7.4 delivers registry-only trusted root declarations: `TrustedRootKind`, `PathScopeAction`, `PathScopeReason`, `TrustedRoot`, `PathScopeGrant`, `PathScopeDeny`, `TrustedRootRegistry`, `build_trusted_root_registry()`, deterministic `root_id`, `grant_id`, `deny_id`, order-insensitive `registry_hash`, source-label truth, and closed-world validation. It represents root/scope declarations without permission, sandbox policy, escape detection, filesystem security, or enforcement. It does not implement path normalization, path escape detection, trusted root authority resolver, path/source resolver, path permission enforcement, filesystem reads/stat/resolve, symlink resolution, runtime enforcement, Ledger writes, approval activation, CLI/TUI, Shell UI, trace hooks, or policy bridge. **P1.7.5 — Path Normalization & Escape Detection Contract is next.**

## Completed (latest)


| Phase         | Focus                                                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| P1.6.4        | Human Oversight Policy Card Model - **COMPLETE**, oversight levels, approval/confirmation semantics, R0-R6 oversight mappings, strict R4/R5/R6 safety validation, 68 tests |
| P1.6.3        | Risk Tier Policy Card Model - **COMPLETE**, R0-R6 semantics, strict R5/R6 validation, deterministic hash-ready typed card, 36 tests |
| P1.4.20       | P1.4 Identity & Autonomy Exit Seal — **SEALED_WITH_LIMITATIONS**, 56 seal checks across 5 categories (import/object, CLI, governance invariants, adversarial, docs consistency), CLI `identity p14-seal run/list-checks/run-check`, 28 new tests, 412 identity total |
| P1.4.19       | Identity Docs / Reports / State Update — consolidation/audit gate, seal-readiness CLI, 18 CLI groups, 15 P1.4 invariants, 10 P1.4.19 invariants, 15 known limitations, 22-item P1.4.20 exit seal checklist, 29 new tests, 384 identity total |
| P1.4.18       | Trust Evidence Linkage — categorical trust posture, evidence bundle, linkage report, 57 new tests, 355 identity total        |
| P1.4.17       | Agent Lifecycle Eligibility State Machine — 8 states, 24 reason codes, 9 lanes, 17 invariants, 60 new tests, 1520 passed/2 skipped        |
| P1.4.16       | Identity Test Battery — 26 test cases/7 categories, battery CLI `run/list/run-case`, 31 new tests, 1460 passed/2 skipped                |
| P1.4.15       | Identity Governance Command Surface — unified CLI, `identity status`/`verify`, JSON envelope, 53 tests                            |
| P1.4.14       | Operator Consent Binding - delta-bound consent, attestation binding, risk acknowledgement, 55 tests                                     |
| P1.4.13       | Authority Delta Detector - semantic authority delta detection, 30 delta types, 58 tests                                            |
| P1.4.12       | Raw Source + Canonical Hash Attestation - raw/canonical source binding, identity/doctrine attestations, 41 focused tests           |
| P1.4.11       | External Doctrine Assimilation Registry — doctrine intake, source hashes, roadmap impact mapping, claim boundaries, 33 tests       |
| P1.4.10       | Capability Claim Boundary Engine — anti-hype firewall, evidence-gated 14-claim registry, 51 tests                                  |
| P1.4.2        | Persona Manifest v2.0 — validated, hashable expression contract + safe summary                                                     |
| P1.4.1        | Identity Kernel v2.0 — validated, hashable trust anchor                                                                            |
| P1.4.0        | Identity + Autonomy Scope Contract — constitutional docs, package stubs, `p14_scope.py`                                            |
| P1.3.9        | Tool Manifest Layer Seal — lifecycle/boundary seal tests, docs sync, governance confirmation                                       |
| P1.3.0–P1.3.8 | Tool / Plugin Manifest Seed — domain model, validation, loader, registry, quarantine, drafts, events, research metadata, built-ins |
| P1.2.1        | Public Entry + Runtime Verification Patch — demo crash fix, sandbox CPU mismatch, ruff/mypy cleanup, smoke tests                   |
| P1.2          | Prompt System Seed — versioned prompt manifests, registry, rendering, trace-safe summaries                                         |
| P1.1          | Model Configuration + Secret Boundary — centralized config, env-only secrets, local_only                                           |
| P1.0.1        | Alpha Seal Integrity Patch — release docs, evidence, seal report, doc consistency                                                  |
| P1.0          | Runtime Alpha Seal — **PRE-SEAL**, CI config, alpha-seal CLI, deployment guide                                                     |
| P0.21         | LLM Planning Bridge for Repository Agent — **PASS**, optional LLM planner with strict validation                                   |
| P0.20         | First Real Coding Agent Demo — **PASS**, governed loop proven end-to-end with evidence                                             |
| P0.19         | P0.20 Demo Harness — controlled scenarios, factory, runner, `buggy_calculator`                                                     |


## P1.4 — Identity, Autonomy & Agent Trust Constitution


| Patch   | Name                                      |
| ------- | ----------------------------------------- |
| P1.4.0  | Identity + Autonomy Scope Contract        |
| P1.4.1  | Identity Kernel                           |
| P1.4.2  | Persona Manifest                          |
| P1.4.3  | Operator Relationship Contract            |
| P1.4.4  | Communication Modes✅                      |
| P1.4.5  | Identity Prompt Context Compiler✅         |
| P1.4.6  | Self-Model v0.1✅                          |
| P1.4.7  | Agent Identity Card✅                      |
| P1.4.8  | Autonomy Scale Engine✅                    |
| P1.4.9  | Measured Autonomy Score✅                  |
| P1.4.10 | Capability Claim Boundary Engine ✅        |
| P1.4.11 | External Doctrine Assimilation Registry ✅ |
| P1.4.12 | Raw Source + Canonical Hash Attestation ✅ |
| P1.4.13 | Authority Delta Detector ✅                |
| P1.4.14 | Operator Consent Binding ✅                |
| P1.4.15 | Identity Governance Command Surface ✅   |
| P1.4.16 | Identity Test Battery ✅                   |
| P1.4.17 | Agent Lifecycle Eligibility State Machine ✅ |
| P1.4.18 | Trust Evidence Linkage ✅                  |
| P1.4.19 | Identity Docs / Reports / State Update ✅  |
| P1.4.20 | P1.4 Identity & Autonomy Exit Seal ✅      |


### P1.4.18 handoff

P1.4.18 Trust Evidence Linkage provides categorical trust posture resolution (no numeric score), evidence bundle construction from source attestations/test battery/consent/authority delta/lifecycle records, and a structured linkage report explaining WHY an identity has its current posture. P1.4.19 Identity Docs/Reports/State Update will synchronize all agent documentation files (STATE, ROADMAP, TESTS, REPORTS, DECISIONS, ARCHITECTURE) and identity reports to reflect the completed P1.4.18 trust evidence surface.

### P1.4.19 handoff

P1.4.19 Identity Docs / Reports / State Update is a consolidation/audit gate that provides structured P1.4 inventory (18 CLI groups, 15 invariants, 15 known limitations, 22-item P1.4.20 exit seal checklist) via `p14_seal_readiness.py` and `identity seal-readiness --json`. It adds no new governance semantics, does not overclaim autonomy, and does not mutate state. **P1.4 is seal-ready. P1.4.20 performs final exit seal verification.**

### P1.4.20 handoff

P1.4.20 is the **final boundary seal for P1.4 Identity & Autonomy**. Seal result: `SEALED_WITH_LIMITATIONS`. **P1.4 is sealed.**

### P1.5.0 handoff

P1.5.0 opened P1.5 with minimal evaluation foundation and Roadmap v3.2 alignment. **Next: P1.5.1 — Evaluation Object Model.**

### P1.5.1 handoff

P1.5.1 defines the stable Evaluation Object Model. PASS does not mean VERIFIED. **Next: P1.5.2 — Capability Evidence Record.**

### P1.5.5 handoff

P1.5.5 creates governed evaluation run envelopes that bind registered subjects, resolved criteria, evidence requirements, evaluator metadata, and sparse-context trace requirements. Envelopes do not execute evaluation, create EvaluationResult, verify capability, or call LLMs/tools. Sparse run metadata does not implement ASCL / SSA / subquadratic attention. **Next: P1.5.6 — Result Classification Engine.**

### P1.5.4 handoff

P1.5.4 defines reusable evaluation criteria schemas — correctness, groundedness, evidence quality, traceability, policy compliance, and 8 sparse context criterion kinds. Criteria do not run evaluation or verify capability. Sparse criteria do not implement ASCL / SSA / subquadratic model attention. **Next: P1.5.5 — Evaluation Run Envelope.**

### P1.5.3 handoff

P1.5.3 defines the governed Evaluation Subject Registry and Sparse Cognition readiness. No registered subject, no governed evaluation. Subject registration does not verify capability. Hub/sparse origin subjects are future-ready references only. **Next: P1.5.4 — Evaluation Criteria Schema.**

### P1.5.2 handoff

P1.5.2 creates CapabilityEvidenceRecord — evaluation results become admissible evidence, not verification. USABLE is not VERIFIED. **Next: P1.5.3 — Evaluation Subject Registry.**

## Next phases (forward hooks from P1.4 / P1.5)

See `docs/P1.4_IDENTITY_AUTONOMY_SCOPE_CONTRACT.md` § Forward Hooks.


| Phase | Focus (v3.2 reference)                             |
| ----- | -------------------------------------------------- |
| P1.5  | Evaluation Mirror & Verified Capability Evidence (CURRENT) |
| P1.6  | Policy Cards & Behavioral Contracts                |
| P1.7  | Path Governance Engine                           |
| P1.8  | Delegation / Non-Repudiation / Agent Identity Mesh |
| P1.9  | Provenance / Disclosure / Output Passport          |
| P22   | L-Hub / LabHub (added v3.2 — not started)          |
| P23   | A-Hub / AgencyHub (added v3.2 — not started)     |
| P24   | S-Hub / StudioHub (added v3.2 — not started)     |
| P25   | Aurel v0.9                                         |
| P30   | Aurel v1.0                                         |


Legacy next-cycle notes remain in `agent/releases/P1.0_NEXT_CYCLE_ROADMAP.md` where not superseded by v3.0 P1.4+ naming.

## Completed hardening (reference)

- P0.1–P0.2 Canonical path security
- P0.3 Sandbox backend separation
- P0.4 Test integrity verification
- P0.5 Planning failure truth discipline
- P0.6 Persistent trace ledger
- P0.7 Runtime state machine + failure semantics
- P0.8 Budget / resource enforcement
- P0.9 Memory write governance + provenance
- P0.10 Tool contract + schema enforcement
- P0.11 Runtime stabilization + agent docs seed
- P0.12 Real LLM adapter layer
- P0.13 Tool Bus v1
- P0.14 Repository Agent Loop
- P0.15 HITL / Approval Upgrade
- P0.16 Praxis Memory Seed
- P0.17 Sandbox Hardening
- P0.17.1 Pre-P0.20 Readiness Patch
- P0.19 P0.20 Demo Harness
- P0.20 First Real Coding Agent Demo (PASS)
- P0.21 LLM Planning Bridge for Repository Agent (PASS)
