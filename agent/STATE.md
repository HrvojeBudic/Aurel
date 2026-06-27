# Repository State

_Last updated: 2026-06-27 (P1.8.11 — Delegation Operator Review / ApprovalIntentRef Model)_

## Current Roadmap Pointer

- Last completed: P1.8.13 — Delegation Runtime/Execution ReadinessRef Model
- Current active: **P1.8.14 — Delegation Trace/Audit BridgeRef Model (planned)**
- Next planned: P1.8.14 — Delegation Trace/Audit BridgeRef Model
- Roadmap version: **v5.1 Integration-First**
- P1.7 status: **sealed** (P1.7.0–P1.7.20 complete)
- P1.8 status: **in progress** (P1.8.0–P1.8.13 complete)

## Golden Thread — P1.8 Delegation

Golden Thread is continuity/evidence linkage only.
Golden Thread is not approval.
Golden Thread is not policy decision.
Golden Thread is not Ledger finality.
Golden Thread is not TRACE_VERIFIED unless trace layer explicitly verifies it.

### Chain: P1.8.12 → P1.8.13 → P1.8.14

| Step | Task | Report | Evidence |
|------|------|--------|----------|
| Previous | P1.8.12 — Delegation Policy/Custos BridgeRef Model | `agent/reports/P1.8.12_DELEGATION_POLICY_CUSTOS_BRIDGE_REF_MODEL.md` | 65 focused tests, deterministic hashes, 16 all-false side effects, clean validation |
| Current | P1.8.13 — Delegation Runtime/Execution ReadinessRef Model | `agent/reports/P1.8.13_DELEGATION_RUNTIME_EXECUTION_READINESS_REF_MODEL.md` | 61 focused tests, deterministic hashes, 16 all-false side effects, clean validation |
| Next | P1.8.14 — Delegation Trace/Audit BridgeRef Model | (planned) | (planned) |

**Semantic bridge:**
P1.8.12 PolicyCustosBridgeBindingSet
→ P1.8.13 RuntimeExecutionReadinessEnvelope
→ P1.8.13 RuntimeExecutionReadinessBindingSet
→ P1.8.14 Trace/Audit BridgeRef handoff

**P1.8.13 validation proof:**
```bash
.venv/bin/python -m compileall src tests         # PASS
.venv/bin/python -m pytest tests/delegation/test_p1_8_13_runtime_readiness.py -q  # 61 passed
.venv/bin/python -m ruff check src/agentic_runtime/delegation/runtime_readiness.py tests/delegation/test_p1_8_13_runtime_readiness.py  # PASS
.venv/bin/python -m mypy src/agentic_runtime      # PASS
```

**Truth:** P1.8.13 is reference-only. RuntimeReadinessRef is not runtime ready. ExecutionPreconditionRef is not precondition satisfied. ExecutionBlockerRef is not runtime blocked. RuntimeAdmissionIntentRef is not runtime admitted. RuntimeAdmissionPlaceholderRef is not admission result. RuntimeContextRef is not runtime initialized. ToolExecutionContextRef is not tool dispatch. RuntimeSessionPlaceholderRef is not session creation. ExecutionTargetRef is not dispatch target selected. ReadinessMatrix is not execution readiness. ReadinessProfile is not execution readiness proof. ReadinessEnvelope is not runtime admission. No runtime engine call, execution engine call, admission gate call, runtime admission, runtime block, execution allow/block, tool dispatch, runtime session creation, execution target selection, policy/Custos call, enforcement, trace write, Ledger write, or runtime mutation occurred. Projection/API/CLI remain UNAVAILABLE. Trace/Ledger write remain UNAVAILABLE. P1.8.14 is not implemented. PolicyBridgeRef is not policy evaluation. CustosBridgeRef is not Custos call. PolicyContextRef is not policy compliance. CustosContextRef is not Custos approval. DecisionRequestIntentRef is not decision request. DecisionResponsePlaceholderRef is not decision response. CompatibilityMatrix is not policy evaluation. BridgeReadinessProfile is not decision readiness. BridgeEnvelope is not policy decision. No policy engine call, Custos runtime call, decision request execution, allow/deny emission, approval/rejection creation, authority grant/deny, runtime allow/block, enforcement, trace write, Ledger write, or runtime mutation occurred. Projection/API/CLI remain UNAVAILABLE. Trace/Ledger write remains UNAVAILABLE. P1.8.13 is not implemented.

### P1.8.13 delegation runtime/execution readiness reference model summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationRuntimeReadinessRef | Deterministic `runtime_readiness_hash` | DEV_FIXTURE in tests | Not runtime ready |
| DelegationExecutionPreconditionRef | Deterministic `precondition_hash` | DEV_FIXTURE | Not precondition satisfied |
| DelegationExecutionBlockerRef | Deterministic `blocker_hash` | DEV_FIXTURE | Not runtime blocked |
| DelegationRuntimeAdmissionIntentRef | Deterministic `admission_intent_hash` | DEV_FIXTURE | Not runtime admitted |
| DelegationRuntimeAdmissionPlaceholderRef | Deterministic `admission_placeholder_hash` | DEV_FIXTURE | Not admission result |
| DelegationRuntimeContextRef | Deterministic `runtime_context_hash` | DEV_FIXTURE | Not runtime initialized |
| DelegationToolExecutionContextRef | Deterministic `tool_context_hash` | DEV_FIXTURE | Not tool dispatch |
| DelegationRuntimeSessionPlaceholderRef | Deterministic `session_placeholder_hash` | DEV_FIXTURE | Not session creation |
| DelegationExecutionTargetRef | Deterministic `execution_target_hash` | DEV_FIXTURE | Not dispatch target selected |
| DelegationRuntimeExecutionReadinessMatrix | Deterministic `matrix_hash` | DEV_FIXTURE | Not execution readiness |
| DelegationRuntimeExecutionReadinessProfile | Deterministic `readiness_hash` | DEV_FIXTURE | Not execution readiness proof |
| DelegationRuntimeExecutionReadinessEnvelope | Deterministic `runtime_execution_readiness_envelope_hash` | DEV_FIXTURE | Not runtime admission |
| DelegationRuntimeExecutionReadinessBindingSet | Deterministic `runtime_execution_readiness_binding_set_hash` | DEV_FIXTURE | Not proof of execution or admission |
| DelegationRuntimeExecutionReadinessSideEffects | 16 booleans all false | LIVE schema | Non-admitting, non-executing, non-dispatching, non-mutating |
| DelegationRuntimeExecutionReadinessStatusReport | Deterministic `status_hash` | DEV_FIXTURE | Reference-only metadata reporting |

**Known UNAVAILABLE (P1.8.13):** Projection/API/Event/Read Model, CLI/Shell/TUI Binding, Ledger Write, Global Trace Write, Runtime Engine, Execution Engine, Admission Gate, Tool Dispatcher, Runtime Session Runtime, Execution Target Selector, Runtime Allow/Block, Enforcement Engine, Policy/Custos Evaluator, Trace Writer, P1.8.14 Trace/Audit BridgeRef Model, Output Passport/P1.9, Runtime Delegation Execution.

**Explicit negatives:** RuntimeReadinessRef exists ≠ runtime ready. ExecutionPreconditionRef exists ≠ precondition satisfied. ExecutionBlockerRef exists ≠ runtime blocked. RuntimeAdmissionIntentRef exists ≠ runtime admitted. RuntimeAdmissionPlaceholderRef exists ≠ admission result. RuntimeContextRef exists ≠ runtime initialized. ToolExecutionContextRef exists ≠ tool dispatched. RuntimeSessionPlaceholderRef exists ≠ runtime session created. ExecutionTargetRef exists ≠ dispatch target selected. ReadinessMatrix exists ≠ execution readiness. ReadinessProfile exists ≠ execution readiness proof. ReadinessEnvelope exists ≠ runtime admission. Readiness hash exists ≠ TRACE_VERIFIED. No runtime/execution/admission/dispatch/session/target selection/policy/Custos/enforcement/trace/Ledger/mutation. No P1.8.14, no P1.9.

Report: `agent/reports/P1.8.13_DELEGATION_RUNTIME_EXECUTION_READINESS_REF_MODEL.md`

### P1.8.11 delegation operator review / approval-intent reference model summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationOperatorReviewRef | Deterministic `review_hash` | DEV_FIXTURE in tests | Not review completed |
| DelegationApprovalIntentRef | Deterministic `approval_intent_hash` | DEV_FIXTURE | Not approval granted |
| DelegationRejectionIntentRef | Deterministic `rejection_intent_hash` | DEV_FIXTURE | Not denial |
| DelegationEscalationIntentRef | Deterministic `escalation_intent_hash` | DEV_FIXTURE | Not escalation executed |
| DelegationMoreContextIntentRef | Deterministic `more_context_intent_hash` | DEV_FIXTURE | Not runtime block |
| DelegationReviewRationaleRef | Deterministic `rationale_hash` | DEV_FIXTURE | Not rationale verified |
| DelegationOperatorReviewReadinessProfile | Deterministic `readiness_hash` | DEV_FIXTURE | Not approval readiness |
| DelegationOperatorReviewEnvelope | Deterministic `operator_review_envelope_hash` | DEV_FIXTURE | Not approval record |
| DelegationOperatorReviewBindingSet | Deterministic `operator_review_binding_set_hash` | DEV_FIXTURE | Not proof of approval or denial |
| DelegationOperatorReviewSideEffects | 17 booleans all false | LIVE schema | Non-approving, non-rejecting, non-HITL, non-mutating |
| DelegationOperatorReviewStatusReport | Deterministic `status_hash` | DEV_FIXTURE | Reference-only metadata reporting |

**Known UNAVAILABLE (P1.8.11):** Projection/API/Event/Read Model, CLI/Shell/TUI Binding, Ledger Write, Global Trace Write, Approval Engine, Rejection Engine, Operator Decision System, Signature Verifier, HITL Workflow Executor, Authority Grant/Deny, Policy/Custos Bridge, Policy/Custos Decision, Runtime Authorization, Runtime Allow/Block, Trace Writer, P1.8.12 Policy/Custos BridgeRef Model, Output Passport/P1.9, Runtime Delegation Execution.

**Explicit negatives:** OperatorReviewRef exists ≠ review completed. ApprovalIntentRef exists ≠ approval granted. RejectionIntentRef exists ≠ request denied. EscalationIntentRef exists ≠ escalation executed. MoreContextIntentRef exists ≠ runtime blocked. ReviewRationaleRef exists ≠ rationale verified. OperatorReviewEnvelope exists ≠ approval record. OperatorReviewReadinessProfile exists ≠ approval readiness. Review hash exists ≠ TRACE_VERIFIED. Intent exists ≠ operator decision. REVIEW_REFERENCED ≠ completed. APPROVAL_INTENT_REFERENCED ≠ approved. REJECTION_INTENT_REFERENCED ≠ denied. ESCALATION_INTENT_REFERENCED ≠ escalated. MORE_CONTEXT_INTENT_REFERENCED ≠ runtime block. No approval/rejection/escalation/signature/HITL/authority grant-deny/policy/Custos/runtime allow-block/trace/Ledger/mutation. No P1.8.12, no P1.9.

Report: `agent/reports/P1.8.11_DELEGATION_OPERATOR_REVIEW_APPROVAL_INTENT_REF_MODEL.md`

### P1.8.10 delegation shadow resolver / consistency model summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationShadowResolverInputEnvelope | Deterministic `input_envelope_hash` | DEV_FIXTURE in tests | Not approval request |
| DelegationConsistencyFinding | Deterministic `finding_hash` | DEV_FIXTURE | Not enforcement action |
| DelegationConsistencyMatrixEntry | Deterministic `entry_hash` | DEV_FIXTURE | Not verification |
| DelegationConsistencyMatrix | Deterministic `matrix_hash` | DEV_FIXTURE | Not approval matrix |
| DelegationShadowResolverReadinessProfile | Deterministic `readiness_hash` | DEV_FIXTURE | Not approval/execution readiness |
| DelegationConsistencySnapshot | Deterministic `snapshot_hash` | DEV_FIXTURE | Not delegation verification |
| DelegationShadowResolverResult | Deterministic `result_hash` | DEV_FIXTURE | Not policy decision |
| DelegationShadowResolverSideEffects | 13 booleans all false | LIVE schema | Non-decisioning, non-executing, non-mutating |
| DelegationShadowResolverStatusReport | Deterministic `status_hash` | DEV_FIXTURE | Diagnostic capability metadata only |

**Known UNAVAILABLE (P1.8.10):** Projection/API/Event/Read Model, CLI/Shell/TUI Binding, Ledger Write, Global Trace Write, Policy Decision Engine, Custos Resolver, Approval System, Authority Grant/Deny, Runtime Allow/Block, Enforcement Engine, Delegation Executor, Trace Writer, P1.8.11 Operator Approval Intent Model, Output Passport/P1.9, Runtime Delegation Execution, Chain Verifier, Evidence Verifier, Identity Resolver, Scope Enforcer, Lifecycle Enforcer.

**Explicit negatives:** ShadowResolverResult exists ≠ policy decision. ConsistencySnapshot exists ≠ delegation verified. ConsistencyMatrix exists ≠ approval matrix. ConsistencyFinding exists ≠ enforcement action. CONFLICT_REFERENCED exists ≠ runtime denial. PRESENT exists ≠ verified. MISSING exists ≠ failed. ReadinessProfile exists ≠ approval readiness. Resolver hash exists ≠ TRACE_VERIFIED. Shadow pass ≠ allowed. Shadow fail ≠ blocked. No policy/Custos/approval/authority grant-deny/enforcement/execution/trace/Ledger/mutation. No P1.8.11, no P1.9.

Report: `agent/reports/P1.8.10_DELEGATION_SHADOW_RESOLVER_CONSISTENCY_MODEL.md`

### P1.8.9 delegation chain / handoff model summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationChainRef | Deterministic `chain_hash` | DEV_FIXTURE in tests | Not chain verified |
| DelegationPredecessorRef | Deterministic `predecessor_hash` | DEV_FIXTURE | Not predecessor valid |
| DelegationSuccessorRef | Deterministic `successor_hash` | DEV_FIXTURE | Not successor activated |
| DelegationHandoffRef | Deterministic `handoff_hash` | DEV_FIXTURE | Not handoff executed |
| DelegationHandoffClaimRef | Deterministic `handoff_claim_hash` | DEV_FIXTURE | Not handoff occurred |
| DelegationHandoffAcceptanceClaimRef | Deterministic `acceptance_claim_hash` | DEV_FIXTURE | Not acceptance verified |
| DelegationResponsibilityTransferClaimRef | Deterministic `transfer_claim_hash` | DEV_FIXTURE | Not responsibility transferred |
| DelegationLineageMap | Deterministic `lineage_map_hash` | DEV_FIXTURE | Not graph engine |
| DelegationChainContinuityReadinessProfile | Deterministic `readiness_hash` | DEV_FIXTURE | Not continuity proven |
| DelegationChainEnvelope | Deterministic `chain_envelope_hash` | DEV_FIXTURE | Not TRACE_VERIFIED |
| DelegationChainBindingSet | Deterministic `chain_binding_set_hash` | DEV_FIXTURE | Not proof of transfer or validity |

**Known UNAVAILABLE (P1.8.9):** Projection/API/Event/Read Model, CLI/Shell/TUI Binding, Ledger Write, Global Trace Write, Live Handoff Executor, Responsibility Transfer Engine, Authority Transfer Engine, Handoff Acceptance Verifier, Predecessor/Successor Verifier, Chain Verifier, Lineage Graph Engine, Runtime Owner Mutation, Policy/Custos Decision, Approval Creation, P1.8.10 Shadow Resolver / Consistency Model, Output Passport/P1.9, Runtime Delegation Execution.

**Explicit negatives:** DelegationChainRef exists ≠ chain verified. DelegationHandoffRef exists ≠ handoff executed. DelegationPredecessorRef exists ≠ predecessor valid. DelegationSuccessorRef exists ≠ successor activated. DelegationHandoffClaimRef exists ≠ handoff occurred. DelegationHandoffAcceptanceClaimRef exists ≠ acceptance verified. DelegationResponsibilityTransferClaimRef exists ≠ responsibility transferred. DelegationLineageMap exists ≠ graph engine. DelegationChainContinuityReadinessProfile exists ≠ continuity proven. chain_envelope_hash exists ≠ TRACE_VERIFIED. chain_binding_set_hash exists ≠ proof of transfer, handoff, or chain validity. No live handoff, responsibility transfer, authority transfer, acceptance verification, predecessor/successor verification, chain verification, lineage graph engine, runtime owner mutation, policy/Custos decisioning, trace write, Ledger write, runtime mutation, P1.8.10, or P1.9.

### P1.8.8 delegation lifecycle / expiry / revocation model summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationExpiryRef | Deterministic `expiry_hash` | DEV_FIXTURE in tests | Not runtime expiry |
| DelegationRevocationRef | Deterministic `revocation_hash` | DEV_FIXTURE | Not runtime revocation |
| DelegationSuspensionRef | Deterministic `suspension_hash` | DEV_FIXTURE | Not runtime pause |
| DelegationRenewalRef | Deterministic `renewal_hash` | DEV_FIXTURE | Not authority renewal |
| DelegationSupersessionRef | Deterministic `supersession_hash` | DEV_FIXTURE | Not old delegation invalidation |
| DelegationRevocationReasonRef | Deterministic `reason_hash` | DEV_FIXTURE | Not verified reason |
| DelegationLifecycleReadinessProfile | Deterministic `readiness_hash` | DEV_FIXTURE | Not scheduler active or enforcement guarantee |
| DelegationLifecycleEnvelope | Deterministic `lifecycle_envelope_hash` | DEV_FIXTURE | Not lifecycle enforcement |
| DelegationLifecycleBindingSet | Deterministic `lifecycle_binding_set_hash` | DEV_FIXTURE | Does not expire/revoke delegations |

**Known UNAVAILABLE (P1.8.8):** Projection/API/Event/Read Model, CLI/Shell/TUI Binding, Ledger Write, Global Trace Write, Runtime Expiry Engine, Runtime Revocation Engine, Runtime Suspension Engine, Authority Renewal, Supersession Enforcement, Permission Removal, Scheduler/Timer Activation, Runtime Cancellation, Policy/Custos Decision, Approval Creation, P1.8.9 Chain/Handoff Model, Output Passport/P1.9, Runtime Delegation Execution.

**Explicit negatives:** ExpiryRef exists ≠ delegation expired. RevocationRef exists ≠ delegation revoked. SuspensionRef exists ≠ runtime paused. RenewalRef exists ≠ authority renewed. SupersessionRef exists ≠ old delegation invalidated. ReasonRef exists ≠ reason verified. LifecycleEnvelope exists ≠ lifecycle enforced. LifecycleReadinessProfile exists ≠ scheduler active. Lifecycle hash ≠ TRACE_VERIFIED. lifecycle_envelope_hash ≠ TRACE_VERIFIED. lifecycle_binding_set_hash ≠ proof of revocation or expiry. No runtime expiry/revocation/suspension/cancellation, no scheduler/timer, no permission/authority mutation, no policy/Custos/approval/Ledger/trace, no P1.8.9, no P1.9.

Report: `agent/reports/P1.8.8_DELEGATION_EXPIRY_REVOCATION_REF_MODEL.md`

### P1.8.7 delegation scope / boundary model summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationScopeRef | Deterministic `scope_hash` | DEV_FIXTURE in tests | Not permission granted |
| DelegationBoundaryRef | Deterministic `boundary_hash` | DEV_FIXTURE | Not boundary enforced |
| DelegationScopeInclusionRef | Deterministic `inclusion_hash` | DEV_FIXTURE | Not permission |
| DelegationScopeExclusionRef | Deterministic `exclusion_hash` | DEV_FIXTURE | Not denial |
| DelegationBoundaryMatrix | Deterministic `boundary_matrix_hash` | DEV_FIXTURE | Not enforcement matrix |
| DelegationScopeReadinessProfile | Deterministic `scope_readiness_hash` | DEV_FIXTURE | Not enforcement readiness guarantee |
| DelegationScopeEnvelope | Deterministic `scope_envelope_hash` | DEV_FIXTURE | Not permission grant |
| DelegationScopeBindingSet | Deterministic `scope_binding_set_hash` | DEV_FIXTURE | Does not grant access |

**Known UNAVAILABLE (P1.8.7):** Projection/API/Event/Read Model, CLI/Shell/TUI Binding, Ledger Write, Global Trace Write, Permission Grant, Access Control Engine, Runtime Boundary Enforcer, Tool Permission Mutation, Data Access Mutation, Memory Access Mutation, Path Authorization, Network Access Mutation, Policy/Custos Decision, Approval Creation, Runtime Blocker, P1.8.8 Expiry/Revocation Model, Output Passport/P1.9, Runtime Delegation Execution.

**Explicit negatives:** DelegationScopeRef exists ≠ permission granted. DelegationBoundaryRef exists ≠ boundary enforced. ScopeEnvelope exists ≠ runtime access control exists. BoundaryMatrix exists ≠ enforcement matrix exists. IN_SCOPE ≠ allowed. OUT_OF_SCOPE ≠ blocked. InclusionRef ≠ permission. ExclusionRef ≠ denial. ScopeReadinessProfile ≠ enforcement readiness guarantee. Scope hash ≠ TRACE_VERIFIED. scope_envelope_hash ≠ TRACE_VERIFIED. scope_binding_set_hash ≠ proof of enforcement. No permission/access/boundary/runtime/tool/data/memory/path/network mutation, no policy/Custos/approval/Ledger/trace, no P1.8.8, no P1.9.

Report: `agent/reports/P1.8.7_DELEGATION_SCOPE_BOUNDARY_MODEL.md`

### P1.8.6 agent identity mesh reference-binding summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationMeshParticipantRef | Deterministic `participant_hash` | DEV_FIXTURE in tests | Not participant authentication |
| DelegationMeshRelationshipRef | Deterministic `relationship_hash` | DEV_FIXTURE | Not relationship verification |
| DelegationMeshScopeRef | Deterministic `mesh_scope_hash` | DEV_FIXTURE | Not permission scope |
| DelegationIdentityMeshEnvelope | Deterministic `identity_mesh_envelope_hash` | DEV_FIXTURE | Not live mesh |
| DelegationMeshResolutionReadinessProfile | Deterministic `readiness_hash` | DEV_FIXTURE | Not trust score |
| DelegationMeshRelationshipMap | Deterministic `relationship_map_hash` | DEV_FIXTURE | Not graph engine |
| DelegationIdentityMeshBinding | Deterministic `binding_hash` | DEV_FIXTURE | Not authority/permission grant |
| DelegationIdentityMeshBindingSet | Deterministic `identity_mesh_binding_set_hash` | DEV_FIXTURE | Not live agent mesh |
| DelegationIdentityMeshSideEffects | 12 booleans all false | LIVE schema | Non-resolving, non-authenticating, non-activating, non-mutating |
| Identity mesh status report | `delegation_identity_mesh_status_report.v1` | DEV_FIXTURE | Not runtime active |

**Known UNAVAILABLE (P1.8.6):** Projection/API/event/read model, CLI/Shell/TUI, Ledger write, global trace write, identity resolver, participant authenticator, relationship verifier, trust scoring, agent activator, permission grant, authority grant module, policy/Custos decision, runtime mesh engine, live agent network, graph database, P1.8.7 scope/boundary model, Output Passport/P1.9, runtime delegation execution.

**Explicit negatives:** AgentIdentityMeshRef exists ≠ identity resolved. ParticipantRef exists ≠ participant authenticated. RelationshipRef exists ≠ trust verified. IdentityMeshEnvelope exists ≠ live mesh exists. MeshRelationshipMap exists ≠ graph engine exists. MeshResolutionReadinessProfile exists ≠ trust score. MeshScopeRef exists ≠ permission scope. AgentRef exists ≠ agent activated. Mesh hash exists ≠ TRACE_VERIFIED. identity_mesh_envelope_hash exists ≠ TRACE_VERIFIED. identity_mesh_binding_set_hash exists ≠ proof of identity resolution. No identity resolver, participant authenticator, relationship verifier, trust scoring, agent activation, permission/authority grant, policy/Custos, Ledger/global trace, runtime mutation, graph engine, P1.8.7, P1.9.

Report: `agent/reports/P1.8.6_AGENT_IDENTITY_MESH_REF_BINDING.md`

### P1.8.5 delegation evidence / non-repudiation reference binding summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationEvidenceRef | Deterministic `evidence_ref_hash` | DEV_FIXTURE in tests | Not evidence verification |
| DelegationNonRepudiationClaimRef | Deterministic `claim_ref_hash` | DEV_FIXTURE | Not claim proof |
| DelegationEvidenceEnvelope | Deterministic `evidence_envelope_hash` | DEV_FIXTURE | Not legal finality |
| DelegationEvidenceCompletenessProfile | Deterministic `profile_hash` | DEV_FIXTURE | Not trust score |
| DelegationNonRepudiationBinding | Deterministic `binding_hash` | DEV_FIXTURE | Not proof/verification |
| DelegationNonRepudiationBindingSet | Deterministic `non_repudiation_binding_set_hash` | DEV_FIXTURE | Not non-repudiation proof |
| DelegationNonRepudiationSideEffects | 14 booleans all false | LIVE schema | Non-verifying, non-final, non-mutating |
| Non-repudiation status report | `delegation_non_repudiation_status_report.v1` | DEV_FIXTURE | Not runtime active |

**Known UNAVAILABLE (P1.8.5):** Projection/API/event/read model, CLI/Shell/TUI, Ledger write, global trace write, crypto verifier, signature verifier, trace verifier, evidence truth verifier, claim verifier, attestation verifier, legal non-repudiation engine, dispute resolver, Output Passport/P1.9, identity mesh binding/P1.8.6, runtime delegation execution, policy/Custos decision.

**Explicit negatives:** NonRepudiationRef exists ≠ non-repudiation proven. EvidenceRef exists ≠ evidence verified. ClaimRef exists ≠ claim proven. AttestationRef exists ≠ attestation verified. SignatureRef exists ≠ signature verified. TraceRef exists ≠ TRACE_VERIFIED. EvidenceEnvelope exists ≠ legal finality. CompletenessProfile exists ≠ trust score. Evidence hash exists ≠ proof. evidence_envelope_hash exists ≠ legal finality. non_repudiation_binding_set_hash exists ≠ proof of non-repudiation. No crypto/signature/trace/evidence/claim/attestation verifier, no Ledger/global trace, no Output Passport/P1.9, no identity mesh/P1.8.6.

Report: `agent/reports/P1.8.5_NON_REPUDIATION_REF_BINDING.md`

### P1.8.4 delegation authority-reference binding summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationAuthorityRef | Deterministic `authority_ref_hash` | DEV_FIXTURE in tests | Not authority grant |
| DelegationAuthorityBinding | Deterministic `binding_hash` | DEV_FIXTURE | Not approval/permission |
| DelegationAuthorityBindingSet | Deterministic `authority_binding_set_hash` | DEV_FIXTURE | Not runtime execution |
| DelegationAuthoritySideEffects | 11 booleans all false | LIVE schema | Non-authorizing, non-verifying, non-mutating |
| Authority status report | `delegation_authority_status_report.v1` | DEV_FIXTURE | Not runtime active |

**Known UNAVAILABLE (P1.8.4):** Projection/API/event/read model, CLI/Shell/TUI, Ledger write, global trace write, policy/Custos decision, policy/Custos enforcement, approval activation, authority grant, authority resolver, authority verifier, permission grant, path authorization, constraint enforcement, non-repudiation verifier, violation/drift detector, runtime delegation execution.

**Explicit negatives:** AuthorityRef exists ≠ authority granted. Authority basis exists ≠ authority verified. Policy context ref exists ≠ policy/Custos decision. Path authority ref exists ≠ path authorized. Operator declaration exists ≠ legal/operational authority proven. Authority binding exists ≠ approval created. Authority binding exists ≠ permission granted. Authority hash exists ≠ TRACE_VERIFIED. Authority binding set exists ≠ runtime execution. Authority model exists ≠ resolver. No policy/Custos/approval/Ledger/global trace/runtime mutation.

Report: `agent/reports/P1.8.4_DELEGATION_AUTHORITY_REF_BINDING.md`

### P1.8.3 delegation constraint model summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationConstraintRef | Deterministic `constraint_hash` | DEV_FIXTURE in tests | Not constraint enforcement |
| DelegationConstraintBinding | Deterministic `binding_hash` | DEV_FIXTURE | Not authority grant |
| DelegationConstraintSet | Deterministic `constraint_set_hash` | DEV_FIXTURE | Not runtime blocking |
| DelegationConstraintSideEffects | 12 booleans all false | LIVE schema | Non-enforcing, non-mutating |
| Constraint status report | `delegation_constraint_status_report.v1` | DEV_FIXTURE | Not runtime active |

**Known UNAVAILABLE (P1.8.3):** Projection/API/event/read model, CLI/Shell/TUI, Ledger write, global trace write, policy/Custos enforcement, approval activation, constraint enforcement, runtime blocker, tool permission mutation, data access mutation, scheduler mutation, delegation resolver, delegation chain resolver, authority bridge, non-repudiation verifier, violation/drift detector, runtime delegation execution.

**Explicit negatives:** Constraint exists ≠ constraint enforced. Required review exists ≠ approval created. Risk bound exists ≠ policy/Custos decision. Tool bound exists ≠ tool permission changed. Data bound exists ≠ data access changed. Time bound exists ≠ scheduler changed. Constraint hash exists ≠ TRACE_VERIFIED. Constraint set exists ≠ runtime blocking. Constraint model exists ≠ resolver exists. Constraint binding exists ≠ authority granted. No policy/Custos/approval/Ledger/global trace/runtime mutation.

Report: `agent/reports/P1.8.3_DELEGATION_CONSTRAINT_MODEL.md`

### P1.8.2 delegation role model summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationPartyRoleRef | Deterministic `role_ref_hash` | DEV_FIXTURE in tests | Not verified authority |
| DelegatedSubjectRef | Deterministic `subject_role_hash` | DEV_FIXTURE | Not subject execution |
| DelegationRoleBinding | Deterministic `binding_hash` | DEV_FIXTURE | Not approval or permission |
| DelegationRoleBindingSet | Deterministic `role_binding_hash` | DEV_FIXTURE | Not enforcement |
| DelegationRoleSideEffects | 11 booleans all false | LIVE schema | Non-executing |
| Role status report | `delegation_role_status_report.v1` | DEV_FIXTURE | Not runtime active |

**Known UNAVAILABLE (P1.8.2):** Projection/API/event/read model, CLI/Shell/TUI, Ledger write, global trace write, policy/Custos enforcement, approval activation, delegation resolver, delegation chain resolver, authority bridge, identity mesh resolver, non-repudiation verifier, runtime delegation execution.

**Explicit negatives:** DelegationPartyRoleRef is not verified authority. DelegatedSubjectRef is not subject execution. DelegationRoleBinding is not approval or permission. DelegationRoleBindingSet is not enforcement. role_binding_hash is not TRACE_VERIFIED. Role model exists ≠ resolver exists. No policy/Custos/approval/Ledger/global trace/runtime mutation.

Report: `agent/reports/P1.8.2_DELEGATOR_DELEGATE_SUBJECT_MODEL.md`

### P1.8.1 delegation identity/ref summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| DelegationRef | Deterministic `ref_hash` | DEV_FIXTURE in tests | Not approval |
| DelegationIdentity | Deterministic `identity_hash` | DEV_FIXTURE | Not verification |
| DelegationRefBinding | Deterministic `binding_hash` | DEV_FIXTURE | Not trace proof |
| DelegationIdentitySideEffects | All booleans false | LIVE schema | Non-executing |
| Identity status report | `delegation_identity_status_report.v1` | DEV_FIXTURE | Not runtime active |
| P1.8.0→P1.8.1 chain | record_hash → ref → binding → identity | DEV_FIXTURE | Reference only |

**Known UNAVAILABLE (P1.8.1):** Projection/API/event/read model, CLI/Shell/TUI, Ledger write, global trace write, policy/Custos enforcement, approval activation, identity resolver, non-repudiation verifier, runtime delegation execution.

**Explicit negatives:** DelegationRef is not approval. DelegationIdentity is not verification. DelegationRefBinding is not trace proof. record_hash is not TRACE_VERIFIED. identity_hash is not proof. No policy/Custos/approval/Ledger/global trace/runtime mutation.

Report: `agent/reports/P1.8.1_DELEGATION_IDENTITY_REF_SCHEMA.md`

### P1.8.0 delegation foundation summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| Foundation schema | `delegation_foundation.v1` | LIVE | Schema only |
| DelegationRecord | Deterministic `record_hash` | DEV_FIXTURE in tests | Not permission |
| AuthorityRef | Reference context | DEV_FIXTURE | Not granted authority |
| NonRepudiationRef | `REFERENCE_ONLY` default | DEV_FIXTURE | Not verified proof |
| AgentIdentityMeshRef | Mesh context reference | DEV_FIXTURE | Not mesh activation |
| Foundation status | `delegation_foundation_status.v1` | DEV_FIXTURE | Not runtime active |
| Side-effect truth | All booleans false | LIVE schema | No enforcement |

**Known UNAVAILABLE (P1.8.0):** Projection/API/event/read model, CLI/Shell/TUI, Ledger write, global trace write, policy/Custos enforcement, approval activation, identity mesh resolver, crypto verifier, runtime delegation execution.

**Explicit negatives:** No fake LIVE, no fake TRACE_VERIFIED, no policy/Custos/approval/Ledger/global trace/runtime mutation, no delegation resolver, no crypto signing/verification.

Report: `agent/reports/P1.8.0_DELEGATION_NON_REPUDIATION_FOUNDATION.md`

**P1.6 section SEALED WITH WARNINGS** — Integration-First vertical slice verified.

### P1.7.20 exit seal summary

| Component | Status | Source label | Boundary |
|-----------|--------|--------------|----------|
| Exit seal schema | `path_governance_exit_seal.v1` | DEV_FIXTURE demo | Evidence only |
| Demo input | Deterministic `demo_id`/`demo_hash` | DEV_FIXTURE | No side effects |
| Check results | 25+ integration checks | DEV_FIXTURE / UNAVAILABLE | Not policy decision |
| Seal result | Deterministic `seal_id`/`seal_hash` | DEV_FIXTURE | Pass ≠ authority |
| Harness demo | `run_path_governance_harness_suite()` | DEV_FIXTURE | Not allow/deny |
| Policy context demo | `bridge_path_governance_to_policy_context()` | DEV_FIXTURE | `policy_called=false` |
| Projection demo | `build_default_path_governance_capability_projection()` | DEV_FIXTURE | Object contract, not HTTP |
| CLI demo | `handle_path_governance_cli_request()` STATUS/READ_MODEL/UNAVAILABLE | DEV_FIXTURE | Read-only projection |
| Trace payload demo | `build_path_resolution_trace_payload()` | DEV_FIXTURE | No Ledger/global trace |
| Violation demo | `build_path_violation_trace_payload()` | DEV_FIXTURE | No correction/enforcement |
| Unavailable proof | 9 integrations documented | UNAVAILABLE | Honest reasons |
| Side-effect truth | All booleans false | LIVE schema | No enforcement |

No fake LIVE or TRACE_VERIFIED for DEV_FIXTURE demos. No policy runtime, Ledger write, global trace write, source mutation, Shell UI, or HTTP server.

### P1.7 sealed summary (P1.7.0–P1.7.20)

P1.7 Path Governance & Source Trust is **sealed** — all implementation patches through P1.7.20 exit seal are complete.

| Phase | Summary | Boundary |
|-------|---------|----------|
| P1.7.0 | Foundation vocabulary, posture, closed-world validation | Schema only |
| P1.7.1 | Path identity & canonical path schema | Schema only |
| P1.7.2 | Source identity & SourceRef schema | Schema only |
| P1.7.3 | Source trust label taxonomy | Taxonomy only |
| P1.7.4 | Trusted root & scope registry seed | Registry only |
| P1.7.5 | Path normalization & escape detection contract | Shadow candidate only |
| P1.7.6 | Path authority scope model | Declarative only |
| P1.7.7 | Untrusted content boundary model | Declarative only |
| P1.7.8 | Source provenance & evidence binding seed | Reference/binding only |
| P1.7.9 | Path/source risk classification model | Classification only |
| P1.7.10 | Path governance resolver shadow | **Shadow-only** (`enforced=false`) |
| P1.7.11 | Source trust resolver shadow | **Shadow-only** (`enforced=false`) |
| P1.7.12 | Conflict & precedence shadow rules | **Shadow-only** (`enforced=false`) |
| P1.7.13 | Path resolution trace hook | Payload/injected-sink; not Ledger |
| P1.7.14 | Violation/drift trace hook | Evidence only; not correction |
| P1.7.15 | Test harness | **DEV_FIXTURE** scenario harness; not runtime |
| P1.7.16 | Policy context bridge | Context packet; not policy decision |
| P1.7.17 | Projection/API/event contract | Read model; not HTTP server |
| P1.7.18 | CLI/TUI binding | Read-only inspector; not control plane |
| P1.7.19 | Docs/state/reports sync | Evidence metadata; not implementation |
| P1.7.20 | Exit seal + live integration demo | Evidence artifact; not enforcement |

**Known UNAVAILABLE (P1.7):** Shell UI, HTTP API server, policy runtime/Custos enforcement, Ledger write, global trace spine write, runtime enforcement, source trust mutation, approval activation, real allow/deny/block decisions, P1.7.20 exit seal.

**Explicit negatives:** No fake LIVE, no fake TRACE_VERIFIED, no enforcement, no policy runtime, no Ledger write, no global trace write, no Shell UI, no HTTP server, no runtime authority.

**P1.7.20 readiness:** Exit seal + live integration demo must prove end-to-end vertical slice, projection inspectability, CLI read-only inspection, harness demo, policy context packet demo, trace/violation payload demo, and honest UNAVAILABLE reporting.

- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.19_DOCS_STATE_REPORTS_UPDATE.md`

### P1.7.19 Docs / State / Reports Update (COMPLETE — truth-sync only)

- Synchronizes `agent/ACTIVE_TASK.md`, `agent/STATE.md`, `agent/ROADMAP.md`, `agent/TESTS.md`, `agent/REPORTS.md`, `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`.
- Indexes P1.7.0–P1.7.19 report chain; documents shadow-only, trace, policy, projection, and CLI boundaries.
- Adds docs consistency test: `tests/path_governance/test_p1_7_19_docs_state_reports_sync.py`.
- No runtime behavior, resolver, policy bridge, projection, or CLI changes.
- P1.7.20 exit-seal checklist documented in P1.7.19 report; P1.7 is pre-seal for live integration demo.
- Report: `agent/reports/P1.7.19_DOCS_STATE_REPORTS_UPDATE.md`

### P1.7.18 Path Governance CLI/TUI Binding (COMPLETE — read-only projection binding)

- `path_governance/cli_binding.py`: `PathGovernanceCliCommandKind`, `PathGovernanceCliOutputFormat`, `PathGovernanceCliBindingMode`, `PathGovernanceCliSideEffects`, `PathGovernanceCliRequest`, `PathGovernanceCliRenderedLine`, `PathGovernanceCliResponse`, `build_path_governance_cli_request()`, `render_path_governance_status_text()`, `render_path_governance_capability_table()`, `render_path_governance_json_payload()`, `render_path_governance_cli_response()`, `handle_path_governance_cli_request()`.
- PathGovernanceCliCommandKind status: **LIVE schema** — STATUS, CAPABILITIES, READ_MODEL, API_ENVELOPE, EVENTS, HARNESS_SUMMARY, POLICY_CONTEXT_SUMMARY, TRACE_HOOK_SUMMARY, VIOLATION_DRIFT_SUMMARY, UNAVAILABLE_BINDINGS; not runtime action.
- PathGovernanceCliOutputFormat status: **LIVE schema** — TEXT, JSON, TABLE, TUI_TEXT; TUI_TEXT is terminal-readable text, not Shell UI.
- PathGovernanceCliBindingMode status: **LIVE schema** — default READ_ONLY; not authority.
- PathGovernanceCliSideEffects status: **LIVE schema** — all side-effect booleans false in P1.7.18.
- PathGovernanceCliRequest status: **LIVE schema** — deterministic `request_id` and `request_hash`; no side effects.
- PathGovernanceCliRenderedLine status: **LIVE schema** — deterministic `line_id` and `line_hash`.
- PathGovernanceCliResponse status: **LIVE schema** — deterministic `response_id` and `response_hash`; `created_by_task="P1.7.18"`.
- PathGovernanceCliBindingReport status: **NOT IMPLEMENTED** — intentionally skipped; markdown report is the evidence artifact.
- CLI registration status: **LIVE (read-only)** — `cli_modules/path_governance.py` + `cli.py path-governance` subcommands; no `register_path_governance_cli()` (follows P1.6.18 policy pattern).
- Side-effect truth status: **PASS** — `policy_called`, `approval_created`, `ledger_written`, `global_trace_written`, `runtime_mutated`, `enforcement_triggered`, `source_mutated`, `prompt_filtered`, `memory_written`, `tool_blocked` all false.
- Deterministic hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, or filesystem-derived state.
- Closed-world validation status: **PASS** — CLI request/side effects/rendered line/response reject unknown fields with `UNKNOWN_FIELD`.
- Source-label truth status: **PASS** — CLI output preserves `ProjectionSourceLabel`; no fake TRACE_VERIFIED.
- CLI/TUI boundary summary: CLI binding exposes projection state; it does not create authority or execute policy.
- Known unavailable states: Shell UI, Web UI, HTTP server, policy runtime, Ledger integration, enforcement, source trust mutation, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement.
- P1.7.19 readiness: **READY** — next task is Docs/State/Reports Update.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.18_PATH_GOVERNANCE_CLI_TUI_BINDING.md`

### P1.7.17 Path Governance Projection/API/Event Contract (COMPLETE — read-model only)

- `path_governance/projection_contract.py`: `PathGovernanceCapabilityKind`, `PathGovernanceProjectionEventKind`, `PathGovernanceProjectionRecord`, `PathGovernanceReadModel`, `PathGovernanceProjectionEvent`, `PathGovernanceApiEnvelope`, `build_path_governance_projection_record()`, `build_path_governance_read_model()`, `build_path_governance_projection_event()`, `build_path_governance_api_envelope()`, `build_default_path_governance_capability_projection()`.
- PathGovernanceCapabilityKind status: **LIVE schema** — P1.7.0–P1.7.18 capability taxonomy; not runtime action.
- PathGovernanceProjectionEventKind status: **LIVE schema** — event contract vocabulary; not global trace emission.
- PathGovernanceProjectionRecord status: **LIVE schema** — projection state card with deterministic `record_id` and `record_hash`; not source of truth.
- PathGovernanceReadModel status: **LIVE schema** — aggregated projection with counts and `overall_state`; not source of truth.
- PathGovernanceProjectionEvent status: **LIVE schema** — event contract object with deterministic `event_id` and `event_hash`; does not emit global trace.
- PathGovernanceApiEnvelope status: **LIVE schema** — API-ready envelope with `unavailable_bindings`; not HTTP server.
- PathGovernanceProjectionReport status: **NOT IMPLEMENTED** — intentionally skipped; markdown report is the trace/evidence/report binding for this task.
- Default capability projection status: **LIVE** — 19 records covering P1.7.0–P1.7.17 plus CLI_TUI_BINDING UNAVAILABLE.
- CLI/TUI binding status: **UNAVAILABLE** — `CLI_TUI_BINDING` record and envelope binding marked unavailable until P1.7.18.
- Shell binding status: **UNAVAILABLE** — envelope `unavailable_bindings.shell` reports not implemented in P1.7.17.
- HTTP server status: **UNAVAILABLE** — envelope `unavailable_bindings.http_server` reports not implemented in P1.7.17.
- Policy runtime status: **UNAVAILABLE** — envelope reports policy runtime not called in P1.7.17.
- Ledger write status: **UNAVAILABLE** — envelope reports Ledger write not part of P1.7.17.
- Deterministic hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, or filesystem-derived state.
- Closed-world validation status: **PASS** — projection record/read model/event/envelope reject unknown fields with `UNKNOWN_FIELD`.
- Source-label truth status: **PASS** — projection objects preserve `ProjectionSourceLabel`; no fake TRACE_VERIFIED in default projection.
- Projection boundary summary: Projection contract exposes state; it does not execute state; read model is not source of truth.
- Known unavailable states: CLI/TUI binding, Shell inspector, Shell UI, HTTP server, policy runtime, Ledger integration, global trace spine write, enforcement, source trust mutation, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement.
- P1.7.18 readiness: **READY** — next task is Path Governance CLI/TUI Binding.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.17_PATH_GOVERNANCE_PROJECTION_API_EVENT_CONTRACT.md`

### P1.7.16 Policy Context Bridge (COMPLETE — context-only bridge)

- `path_governance/policy_context_bridge.py`: `PathPolicyContextSubjectKind`, `PathPolicyDecisionSurface`, `PathPolicyRequirementKind`, `PathPolicyBridgeMode`, `PathPolicyBridgeDisposition`, `PathPolicyContextInput`, `PathPolicyContextSubjectRef`, `PathPolicyContextPacket`, `PathPolicyContextBridgeResult`, `build_path_policy_context_subject_ref()`, `derive_path_policy_requirements()`, `build_path_policy_context_packet()`, `bridge_path_governance_to_policy_context()`.
- PathPolicyContextSubjectKind status: **LIVE schema** — subject classification vocabulary; not policy decision.
- PathPolicyDecisionSurface status: **LIVE schema** — future policy surface vocabulary; descriptive only.
- PathPolicyRequirementKind status: **LIVE schema** — advisory requirement vocabulary; not approval creation.
- PathPolicyBridgeMode status: **LIVE schema** — default `CONTEXT_ONLY`; does not invoke policy runtime.
- PathPolicyBridgeDisposition status: **LIVE schema** — bridge outcome disposition; not policy decision.
- PathPolicyContextInput status: **LIVE schema** — optional references to P1.7.0–P1.7.15 objects; deterministic `input_id` and `input_hash`.
- PathPolicyContextSubjectRef status: **LIVE schema** — lightweight upstream refs with `subject_ref_id`; not raw payload embedding.
- PathPolicyContextPacket status: **LIVE schema** — advisory `advisory_summary`, subjects, requirements, decision surfaces, deterministic `packet_id` and `packet_hash`, `created_by_task="P1.7.16"`, `schema_version="path_policy_context_packet.v1"`.
- PathPolicyContextBridgeResult status: **LIVE schema** — bridge mode, disposition, truth fields all false, deterministic `bridge_id` and `bridge_hash`, `created_by_task="P1.7.16"`, `bridge_version="path_policy_context_bridge.v1"`.
- PathPolicyContextBridgeReport status: **NOT IMPLEMENTED** — intentionally skipped; markdown report is the trace/evidence/report binding for this task.
- `build_path_policy_context_subject_ref()` status: **LIVE backend helper** — extracts ref_id/ref_hash from upstream objects without mutation.
- `derive_path_policy_requirements()` status: **LIVE backend helper** — advisory requirement derivation from risk/provenance/source/conflict/authority/trace context.
- `build_path_policy_context_packet()` status: **LIVE backend helper** — builds deterministic policy-ready context packet without policy call.
- `bridge_path_governance_to_policy_context()` status: **LIVE backend helper** — default `CONTEXT_ONLY`; never calls policy engine or mutates runtime.
- policy_called=false status: **PASS** — enforced in bridge result `__post_init__`.
- policy_decision_made=false status: **PASS** — enforced in bridge result `__post_init__`.
- approval_created=false status: **PASS** — enforced in bridge result `__post_init__`.
- ledger_written=false status: **PASS** — enforced in bridge result `__post_init__`.
- runtime_mutated=false status: **PASS** — enforced in bridge result `__post_init__`.
- enforcement_triggered=false status: **PASS** — enforced in bridge result `__post_init__`.
- Deterministic hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, or filesystem-derived state.
- Closed-world validation status: **PASS** — policy context input/subject/packet/bridge result reject unknown fields with `UNKNOWN_FIELD`.
- Source-label truth status: **PASS** — bridge objects preserve `ProjectionSourceLabel`; test fixtures use `DEV_FIXTURE`.
- Bridge boundary summary: Policy Context Bridge prepares governance context; it does not decide policy; requirement is not approval.
- Known unavailable states: projection/API/event contract, CLI/TUI binding, Shell inspector, policy engine integration, Custos runtime, real enforcement, Ledger integration, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement.
- P1.7.17 readiness: **READY** — next task is Path Governance Projection/API/Event Contract.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.16_POLICY_CONTEXT_BRIDGE.md`

### P1.7.15 Path Governance Test Harness (COMPLETE — shadow-chain harness only)

- `path_governance/test_harness.py`: `PathGovernanceHarnessScenarioKind`, `PathGovernanceHarnessExpectation`, `PathGovernanceHarnessStatus`, `PathGovernanceHarnessScenario`, `PathGovernanceHarnessRunInput`, `PathGovernanceHarnessStepResult`, `PathGovernanceHarnessRunResult`, `build_path_governance_harness_scenario()`, `build_default_path_governance_harness_suite()`, `run_path_governance_harness_scenario()`, `run_path_governance_harness_suite()`.
- PathGovernanceHarnessScenarioKind status: **LIVE schema** — scenario classification vocabulary; not runtime action.
- PathGovernanceHarnessExpectation status: **LIVE schema** — advisory expectation vocabulary; does not enforce.
- PathGovernanceHarnessStatus status: **LIVE schema** — harness step status; FAIL is not enforcement.
- PathGovernanceHarnessScenario status: **LIVE schema** — deterministic DEV_FIXTURE scenario with `scenario_id`.
- PathGovernanceHarnessRunInput status: **LIVE schema** — deterministic suite input with `run_id` and `input_hash`.
- PathGovernanceHarnessStepResult status: **LIVE schema** — per-scenario step outcome with `step_id` and `step_hash`.
- PathGovernanceHarnessRunResult status: **LIVE schema** — aggregated suite outcome with `result_id` and `result_hash`, `created_by_task="P1.7.15"`, `harness_version="path_governance_test_harness.v1"`.
- PathGovernanceHarnessReport status: **NOT IMPLEMENTED** — intentionally skipped; markdown report is the trace/evidence/report binding for this task.
- Default DEV_FIXTURE suite status: **PASS** — nine deterministic default scenarios, all labeled `DEV_FIXTURE`.
- `run_path_governance_harness_scenario()` status: **LIVE backend helper** — runs P1.7 shadow helpers only; no policy/approval/Ledger/runtime mutation.
- `run_path_governance_harness_suite()` status: **LIVE backend helper** — deterministic suite aggregation; same suite yields same `result_hash`.
- Deterministic hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, or filesystem-derived state.
- Closed-world validation status: **PASS** — harness scenario/run/step/result reject unknown fields with `UNKNOWN_FIELD`.
- Source-label truth status: **PASS** — harness objects preserve `ProjectionSourceLabel`; default fixtures use `DEV_FIXTURE`.
- Harness boundary summary: Path Governance Test Harness verifies shadow governance behavior; harness pass is not allow; harness fail is not deny.
- Known unavailable states: policy context bridge, projection/API/event contract, CLI/TUI binding, Shell inspector, policy engine integration, approval activation, real enforcement, Ledger integration, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem/network access, sandbox hardening, runtime enforcement.
- P1.7.16 readiness: **READY** — next task is Policy Context Bridge.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.15_PATH_GOVERNANCE_TEST_HARNESS.md`

### P1.7.14 Path Violation / Drift Trace Hook (COMPLETE — observability-only violation/drift payload)

- `path_governance/`: `PathViolationTraceEventKind`, `PathViolationSeverity`, `PathViolationTraceHookMode`, `PathViolationTraceDisposition`, `PathViolationTraceReason`, `PathViolationTraceInput`, `PathViolationTracePayload`, `PathViolationTraceHookResult`, `PathSourceDriftSignal`, `build_path_violation_trace_payload()`, `record_path_violation_trace_hook()`, `detect_path_source_drift_signals()`.
- PathViolationTraceEventKind status: **LIVE schema** — violation/drift event classification vocabulary; not deny or correction.
- PathViolationSeverity status: **LIVE schema** — severity candidate vocabulary; does not block or enforce.
- PathViolationTraceHookMode status: **LIVE schema** — `PAYLOAD_ONLY`, `INJECTED_SINK`, `TRACE_SPINE_UNAVAILABLE`, `ERROR`, `UNKNOWN`; does not imply enforcement.
- PathViolationTraceDisposition status: **LIVE schema** — hook outcome disposition; not runtime action.
- PathViolationTraceReason status: **LIVE schema** — violation/drift payload construction reason vocabulary; does not enforce.
- PathViolationTraceInput status: **LIVE schema** — expected/current references to P1.7.6–P1.7.13 objects; deterministic `input_id` and `input_hash`.
- PathViolationTracePayload status: **LIVE schema** — observational `violation_summary`, expected/current refs, drift reasons, deterministic `payload_id` and `payload_hash`, `created_by_task="P1.7.14"`, `schema_version="path_violation_trace_payload.v1"`.
- PathViolationTraceHookResult status: **LIVE schema** — hook mode, disposition, truth fields including `enforcement_triggered`, deterministic `hook_id` and `hook_hash`, `created_by_task="P1.7.14"`, `hook_version="path_violation_trace_hook.v1"`.
- PathSourceDriftSignal status: **LIVE schema** — observational drift signal with deterministic `drift_signal_id`; not correction or enforcement.
- PathViolationTraceReport status: **NOT IMPLEMENTED** — intentionally skipped to keep P1.7.14 narrow; markdown report is the trace/evidence/report binding for this task.
- `build_path_violation_trace_payload()` status: **LIVE backend helper** — compares expected/current context and produces deterministic observability payload without trace/Ledger write or runtime mutation.
- `record_path_violation_trace_hook()` status: **LIVE backend helper** — default `PAYLOAD_ONLY`; optional injected sink only; never writes Ledger, mutates runtime, or triggers enforcement.
- `detect_path_source_drift_signals()` status: **LIVE backend helper** — deterministic observational drift signal detection from expected/current context.
- PAYLOAD_ONLY default status: **PASS** — no sink means `trace_written=false`, `ledger_written=false`, `runtime_mutated=false`, `enforcement_triggered=false`.
- INJECTED_SINK testability status: **PASS** — explicit sink callback receives payload; `trace_written=true` only on sink success.
- TRACE_SPINE_UNAVAILABLE honesty status: **PASS** — drift reasons include `TRACE_SPINE_UNAVAILABLE`; no fake TRACE_VERIFIED.
- ledger_written=false status: **PASS** — enforced in hook result `__post_init__`.
- runtime_mutated=false status: **PASS** — enforced in hook result `__post_init__`.
- enforcement_triggered=false status: **PASS** — enforced in hook result `__post_init__`.
- Violation/drift payload hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, or cwd-derived live state.
- Closed-world validation status: **PASS** — violation input/payload/hook result/drift signal reject unknown fields with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — violation/drift objects preserve `ProjectionSourceLabel`; test fixtures use `DEV_FIXTURE`.
- Violation/drift hook boundary summary: violation/drift trace hook records evidence of mismatch; it does not correct, enforce, rollback, or punish.
- Known unavailable states: path governance test harness, policy engine integration, policy bridge, global trace spine write by default, fake TRACE_VERIFIED, real conflict enforcement, real precedence enforcement, correction, rollback, source trust mutation, source taxonomy mutation, source identity mutation, trust promotion/demotion, source blocking, runtime quarantine, memory canonization, approval activation, Ledger integration, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem security, network access, sandbox hardening, runtime enforcement, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.15 readiness: **READY** — next task is Path Governance Test Harness.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.14_PATH_VIOLATION_DRIFT_TRACE_HOOK.md`

### P1.7.13 Path Resolution Trace Hook (COMPLETE — observability-only trace payload)

- `path_governance/`: `PathResolutionTraceEventKind`, `PathResolutionTraceHookMode`, `PathResolutionTraceDisposition`, `PathResolutionTraceReason`, `PathResolutionTraceInput`, `PathResolutionTracePayload`, `PathResolutionTraceHookResult`, `build_path_resolution_trace_payload()`, `record_path_resolution_trace_hook()`.
- PathResolutionTraceEventKind status: **LIVE schema** — trace event classification vocabulary; not Ledger finality.
- PathResolutionTraceHookMode status: **LIVE schema** — `PAYLOAD_ONLY`, `INJECTED_SINK`, `TRACE_SPINE_UNAVAILABLE`, `ERROR`, `UNKNOWN`; does not imply enforcement.
- PathResolutionTraceDisposition status: **LIVE schema** — hook outcome disposition; not runtime action.
- PathResolutionTraceReason status: **LIVE schema** — trace payload construction reason vocabulary; does not enforce.
- PathResolutionTraceInput status: **LIVE schema** — optional references to P1.7.6–P1.7.12 objects; deterministic `input_id` and `input_hash`.
- PathResolutionTracePayload status: **LIVE schema** — advisory `decision_summary`, upstream refs, trace reasons, deterministic `payload_id` and `payload_hash`, `created_by_task="P1.7.13"`, `schema_version="path_resolution_trace_payload.v1"`.
- PathResolutionTraceHookResult status: **LIVE schema** — hook mode, disposition, truth fields, deterministic `hook_id` and `hook_hash`, `created_by_task="P1.7.13"`, `hook_version="path_resolution_trace_hook.v1"`.
- PathResolutionTraceReport status: **NOT IMPLEMENTED** — intentionally skipped to keep P1.7.13 narrow; markdown report is the trace/evidence/report binding for this task.
- `build_path_resolution_trace_payload()` status: **LIVE backend helper** — produces deterministic observability payload without trace/Ledger write or runtime mutation.
- `record_path_resolution_trace_hook()` status: **LIVE backend helper** — default `PAYLOAD_ONLY`; optional injected sink only; never writes Ledger or mutates runtime.
- PAYLOAD_ONLY default status: **PASS** — no sink means `trace_written=false`, `ledger_written=false`, `runtime_mutated=false`.
- INJECTED_SINK testability status: **PASS** — explicit sink callback receives payload; `trace_written=true` only on sink success.
- TRACE_SPINE_UNAVAILABLE honesty status: **PASS** — trace reasons include `TRACE_SPINE_UNAVAILABLE`; no fake TRACE_VERIFIED.
- ledger_written=false status: **PASS** — enforced in hook result `__post_init__`.
- runtime_mutated=false status: **PASS** — enforced in hook result `__post_init__`.
- Input/payload/hook hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, or cwd-derived live state.
- Closed-world validation status: **PASS** — trace input/payload/hook result reject unknown fields with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — trace objects preserve `ProjectionSourceLabel`; test fixtures use `DEV_FIXTURE`.
- Trace hook boundary summary: trace hook is observability, not authority; trace payload is not Ledger finality; trace hook result is not runtime enforcement.
- Known unavailable states: path violation/drift trace hook, path governance test harness, policy engine integration, policy bridge, global trace spine write by default, fake TRACE_VERIFIED, real conflict enforcement, real precedence enforcement, source trust mutation, source taxonomy mutation, source identity mutation, trust promotion/demotion, source blocking, runtime quarantine, memory canonization, approval activation, Ledger integration, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem security, network access, sandbox hardening, runtime enforcement, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.14 readiness: **READY** — next task is Path Violation / Drift Trace Hook.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.13_PATH_RESOLUTION_TRACE_HOOK.md`

### P1.7.12 Path/Source Conflict & Precedence Rules (COMPLETE — shadow conflict/precedence only)

- `path_governance/`: `PathSourceConflictKind`, `PrecedenceRuleKind`, `ConflictSeverity`, `ConflictPrecedencePosture`, `PathSourceConflictSignal`, `PrecedenceRule`, `ConflictPrecedenceInput`, `ConflictPrecedenceResult`, `resolve_path_source_conflicts_shadow()`.
- PathSourceConflictKind status: **LIVE schema** — deterministic conflict classification vocabulary; does not resolve or enforce.
- PrecedenceRuleKind status: **LIVE schema** — precedence recommendation vocabulary; does not apply runtime action.
- ConflictSeverity status: **LIVE schema** — severity marker only; does not block or enforce.
- ConflictPrecedencePosture status: **LIVE schema** — posture recommendation only; not runtime action.
- PathSourceConflictSignal status: **LIVE schema** — deterministic `signal_id`, conflict kind, severity, reason, source label, JSON-safe metadata.
- PrecedenceRule status: **LIVE schema** — deterministic `rule_id`, rule kind, applies_to, severity, recommended posture, reason, source label, JSON-safe metadata.
- ConflictPrecedenceInput status: **LIVE schema** — optional references to P1.7.6–P1.7.11 objects; deterministic `input_id` and `input_hash`.
- ConflictPrecedenceResult status: **LIVE schema** — conflict signals, precedence rules, `final_shadow_posture`, advisory `recommended_shadow_decision`, deterministic `result_id` and `result_hash`, `created_by_task="P1.7.12"`, `resolver_version="path_source_conflict_precedence.v0.shadow"`.
- ConflictPrecedenceReport status: **NOT IMPLEMENTED** — intentionally skipped to keep P1.7.12 narrow; markdown report is the trace/evidence/report binding for this task.
- `resolve_path_source_conflicts_shadow()` status: **LIVE backend helper** — produces deterministic non-enforcing conflict signals and precedence recommendations from supplied P1.7 context.
- Shadow-only/enforced truth status: **PASS** — every result has `shadow_only=true` and `enforced=false`.
- Recommended shadow decision status: **ADVISORY ONLY** — `recommended_shadow_decision` uses WOULD_* vocabulary only; does not mutate source identity, source trust label, or source trust taxonomy.
- Signal/rule/input/result hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, or cwd-derived live state.
- Closed-world validation status: **PASS** — conflict/precedence input/result/signal/rule reject unknown fields with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — conflict/precedence objects preserve `ProjectionSourceLabel`; test fixtures use `DEV_FIXTURE`.
- Conflict/precedence boundary summary: conflict detection is not conflict enforcement; precedence rule is not runtime authority; strictest-wins is shadow-only; recommended_shadow_decision is advisory only.
- Known unavailable states: path resolution trace hook, path violation/drift trace hook, policy engine integration, policy bridge, real conflict enforcement, real precedence enforcement, source trust mutation, source taxonomy mutation, source identity mutation, trust promotion/demotion, source blocking, runtime quarantine, memory canonization, approval activation, trace hooks, Ledger integration, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem security, network access, sandbox hardening, runtime enforcement, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.13 readiness: **READY** — next task is Path Resolution Trace Hook.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.12_PATH_SOURCE_CONFLICT_PRECEDENCE_RULES.md`

### P1.7.11 Source Trust Resolver v0 / Shadow Mode (COMPLETE — shadow trust resolver only)

- `path_governance/`: `SourceTrustShadowDecision`, `SourceTrustDecisionReason`, `SourceTrustResolverInput`, `SourceTrustResolverResult`, `resolve_source_trust_shadow()`.
- SourceTrustShadowDecision status: **LIVE schema** — `WOULD_TRUST`, `WOULD_REVIEW`, `WOULD_DISTRUST`, `WOULD_QUARANTINE`, `WOULD_REQUIRE_OPERATOR_REVIEW`, `WOULD_REQUIRE_POLICY_REVIEW`, `UNKNOWN`; vocabulary only, not source mutation or runtime action.
- SourceTrustDecisionReason status: **LIVE schema** — deterministic explanation vocabulary for source identity, source label, boundary, provenance/evidence, risk, path resolver shadow output, policy bridge unavailable, and shadow-only reasons.
- SourceTrustResolverInput status: **LIVE schema** — optional references to `SourceIdentity`, `SourceTrustLabel`, `SourceTrustTaxonomy`, `UntrustedContentBoundary`, `ProvenanceBinding`, `PathSourceRiskClassification`, and `PathGovernanceResolverResult`; deterministic `input_id` and `input_hash`.
- SourceTrustResolverResult status: **LIVE schema** — shadow trust decision, deterministic ordered reasons, advisory `recommended_trust_label`, risk level, source label, advisory flags, deterministic `result_id` and `result_hash`, `created_by_task="P1.7.11"`, `resolver_version="source_trust_resolver.v0.shadow"`.
- SourceTrustResolverReport status: **NOT IMPLEMENTED** — intentionally skipped to keep P1.7.11 narrow; markdown report is the trace/evidence/report binding for this task.
- `resolve_source_trust_shadow()` status: **LIVE backend helper** — produces deterministic non-mutating `WOULD_*` trust recommendations from supplied P1.7 context.
- Shadow-only/enforced truth status: **PASS** — every result has `shadow_only=true` and `enforced=false`.
- Recommended trust label status: **ADVISORY ONLY** — `recommended_trust_label` is hash-ready output metadata; it does not mutate `SourceIdentity`, `SourceTrustLabel`, or `SourceTrustTaxonomy`.
- Input/result hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, or cwd-derived live state.
- Closed-world validation status: **PASS** — resolver input/result reject unknown fields with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — resolver input/result preserve `ProjectionSourceLabel`; test fixtures use `DEV_FIXTURE`.
- Shadow trust resolver boundary summary: Source Trust Resolver v0 is shadow-only; trust recommendation is not trust mutation; `WOULD_TRUST` is not `TRUSTED`; `WOULD_DISTRUST` is not source blocking; `WOULD_QUARANTINE` is not quarantine action.
- Known unavailable states: path/source conflict rules, precedence rules, policy engine integration, policy bridge, real source trust mutation, source taxonomy mutation, source identity mutation, trust promotion/demotion, source blocking, runtime quarantine, memory canonization, approval activation, trace hooks, Ledger integration, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem security, network access, sandbox hardening, runtime enforcement, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.12 readiness: **READY** — next task is Path/Source Conflict & Precedence Rules.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.11_SOURCE_TRUST_RESOLVER_SHADOW_MODE.md`

### P1.7.10 Path Governance Resolver v0 / Shadow Mode (COMPLETE — shadow resolver only)

- `path_governance/`: `PathGovernanceShadowDecision`, `PathGovernanceDecisionReason`, `PathGovernanceResolverInput`, `PathGovernanceResolverResult`, `resolve_path_governance_shadow()`.
- PathGovernanceShadowDecision status: **LIVE schema** — `WOULD_ALLOW`, `WOULD_REVIEW`, `WOULD_RESTRICT`, `WOULD_DENY`, `WOULD_QUARANTINE`, `WOULD_REQUIRE_OPERATOR_REVIEW`, `WOULD_REQUIRE_POLICY_REVIEW`, `UNKNOWN`; vocabulary only, not runtime action.
- PathGovernanceDecisionReason status: **LIVE schema** — deterministic explanation vocabulary for source trust, path boundary, authority, untrusted boundary, risk, provenance/evidence, policy bridge unavailable, and shadow-only reasons.
- PathGovernanceResolverInput status: **LIVE schema** — optional references to `PathIdentity`, `SourceIdentity`, `TrustedRootRegistry`, `PathBoundaryCheckResult`, `PathAuthorityScope`, `UntrustedContentBoundary`, `ProvenanceBinding`, and `PathSourceRiskClassification`; deterministic `input_id` and `input_hash`.
- PathGovernanceResolverResult status: **LIVE schema** — shadow decision, deterministic ordered reasons, risk level, source label, advisory flags, deterministic `result_id` and `result_hash`, `created_by_task="P1.7.10"`, `resolver_version="path_governance_resolver.v0.shadow"`.
- PathGovernanceResolverReport status: **NOT IMPLEMENTED** — intentionally skipped to keep P1.7.10 narrow; markdown report is the trace/evidence/report binding for this task.
- `resolve_path_governance_shadow()` status: **LIVE backend helper** — produces deterministic non-enforcing `WOULD_*` recommendations from supplied P1.7 context.
- Shadow-only/enforced truth status: **PASS** — every result has `shadow_only=true` and `enforced=false`.
- Input/result hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, or cwd-derived live state.
- Closed-world validation status: **PASS** — resolver input/result reject unknown fields with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — resolver input/result preserve `ProjectionSourceLabel`; test fixtures use `DEV_FIXTURE`.
- Shadow resolver boundary summary: resolver v0 is shadow-only; shadow decision is not enforcement; recommended action is not runtime action; `WOULD_DENY` is not `DENY`; `WOULD_ALLOW` is not `ALLOW`; `WOULD_RESTRICT` is not `RESTRICT`; `WOULD_QUARANTINE` is not `QUARANTINE`.
- Known unavailable states: source trust resolver, path/source conflict rules, precedence rules, policy engine integration, policy bridge, real allow/deny/block decisions, approval activation, trace hooks, Ledger integration, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem security, network access, sandbox hardening, runtime enforcement, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.11 readiness: **READY** — next task is Source Trust Resolver v0 / Shadow Mode.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.10_PATH_GOVERNANCE_RESOLVER_SHADOW_MODE.md`

### P1.7.9 Path/Source Risk Classification Model (COMPLETE — classification model only)

- `path_governance/`: `PathSourceRiskLevel`, `PathSourceRiskSignalKind`, `RiskClassificationBasis`, `RiskClassificationPosture`, `PathSourceRiskSignal`, `PathSourceRiskClassification`, `PathSourceRiskRegistry`, `build_path_source_risk_signal()`, `build_path_source_risk_classification()`, `build_path_source_risk_registry()`, `derive_path_source_risk_classification()`.
- PathSourceRiskLevel status: **LIVE schema** — declared risk level only; does not block, approve, or authorize.
- PathSourceRiskSignalKind status: **LIVE schema** — declared risk signal kind; signal is not decision, block, or allow/deny.
- RiskClassificationBasis status: **LIVE schema** — explains classification source; does not grant or deny anything.
- RiskClassificationPosture status: **LIVE schema** — recommends future handling; does not enforce.
- PathSourceRiskSignal status: **LIVE schema** — deterministic `signal_id`, basis, risk level, reason, source label, JSON-safe metadata.
- PathSourceRiskClassification status: **LIVE schema** — binds signals, optional source/path/boundary/authority/provenance references, risk level, posture, deterministic `classification_id` and `classification_hash`, `created_by_task="P1.7.9"`, `classification_version="path_source_risk_classification.v1"`.
- PathSourceRiskRegistry status: **LIVE schema** — binds classifications with `created_by_task="P1.7.9"`, `registry_version="path_source_risk_registry.v1"`, explicit source label, notes, metadata, and deterministic order-insensitive `registry_hash`.
- Signal/classification/registry hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, or cwd-derived live state.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — test fixtures use `DEV_FIXTURE`; production helper defaults remain `LIVE`.
- Risk classification boundary summary: risk classification is not resolver; risk level is not deny; risk posture is not policy decision; risk signal is not block; classification does not activate approval, write trace, write Ledger, filter prompt, write memory, or block tools.
- Known unavailable states: path governance resolver, source trust resolver, path/source conflict rules, policy engine integration, allow/deny/block decisions, approval activation, trace hooks, Ledger integration, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem security, network access, sandbox hardening, runtime enforcement, policy bridge, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.10 readiness: **READY** — next task is Path Governance Resolver v0 / Shadow Mode.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.9_PATH_SOURCE_RISK_CLASSIFICATION_MODEL.md`

### P1.7.8 Source Provenance & Evidence Binding Seed (COMPLETE — binding seed only)

- `path_governance/`: `SourceProvenanceKind`, `EvidenceBindingKind`, `EvidenceConfidence`, `SourceClaimKind`, `SourceEvidenceRef`, `SourceClaimRef`, `SourceProvenanceRef`, `ProvenanceBinding`, `ProvenanceBindingRegistry`, `build_source_evidence_ref()`, `build_source_claim_ref()`, `build_source_provenance_ref()`, `build_provenance_binding()`, `build_provenance_binding_registry()`.
- SourceProvenanceKind status: **LIVE schema** — declared provenance kind only; does not assert truth or grant authority.
- EvidenceBindingKind status: **LIVE schema** — declared evidence binding kind; does not resolve truth or write trace.
- EvidenceConfidence status: **LIVE schema** — confidence marker only; not a truth guarantee or resolver output.
- SourceClaimKind status: **LIVE schema** — claim classification only; does not accept, reject, execute, or enforce.
- SourceEvidenceRef status: **LIVE schema** — deterministic `evidence_id` and `evidence_hash`, `SourceIdentity`, confidence, source label, JSON-safe metadata.
- SourceClaimRef status: **LIVE schema** — deterministic `claim_id` and `claim_hash`, short `claim_summary`, confidence, source label, JSON-safe metadata.
- SourceProvenanceRef status: **LIVE schema** — deterministic `provenance_id` and `provenance_hash`, optional `parent_source_id`, sorted `derived_from`, lineage seed without graph engine.
- ProvenanceBinding status: **LIVE schema** — binds source identity, provenance/evidence/claim refs, optional `boundary_ref_id`, `authority_scope_id`, `path_identity_hash`, deterministic `binding_id` and `binding_hash`, `created_by_task="P1.7.8"`, `binding_version="source_provenance_binding.v1"`.
- ProvenanceBindingRegistry status: **LIVE schema** — binds bindings with `created_by_task="P1.7.8"`, `registry_version="source_provenance_binding_registry.v1"`, explicit source label, notes, metadata, and deterministic order-insensitive `registry_hash`.
- Evidence/claim/provenance/binding/registry hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, or cwd-derived live state.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — test fixtures use `DEV_FIXTURE`; production helper defaults remain `LIVE`.
- Provenance/evidence boundary summary: provenance binding is not truth verification; evidence reference is not Ledger write; claim binding is not claim acceptance; confidence marker is not truth guarantee; binding registry is not audit ledger.
- Known unavailable states: full provenance graph, graph query, replay, path/source risk classifier, path governance resolver, source trust resolver, truth verification, trace hooks, Ledger integration, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem security, network access, sandbox hardening, runtime enforcement, policy bridge, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.9 readiness: **READY** — next task is Path/Source Risk Classification Model.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.8_SOURCE_PROVENANCE_EVIDENCE_BINDING_SEED.md`

### P1.7.7 Untrusted Content Boundary Model (COMPLETE — declarative boundary model only)

- `path_governance/`: `UntrustedContentKind`, `ContentInfluenceSurface`, `BoundaryRestrictionKind`, `UntrustedBoundaryPosture`, `BoundaryRestriction`, `UntrustedContentBoundary`, `UntrustedContentBoundaryRegistry`, `build_untrusted_content_boundary()`, `build_untrusted_content_boundary_registry()`, trust-label default declaration helpers.
- UntrustedContentKind status: **LIVE schema** — declared content kind only; does not decide trust or authority.
- ContentInfluenceSurface status: **LIVE schema** — declared influence surface; does not grant permission.
- BoundaryRestrictionKind status: **LIVE schema** — future-governance restriction vocabulary; does not enforce.
- UntrustedBoundaryPosture status: **LIVE schema** — declared posture; does not execute, block, or authorize.
- BoundaryRestriction status: **LIVE schema** — deterministic `restriction_id`, surface, reason, source label, JSON-safe metadata.
- UntrustedContentBoundary status: **LIVE schema** — binds `SourceIdentity`, `SourceTrustLabel`, posture, influence surfaces, restrictions, deterministic `boundary_id` and `boundary_hash`, `created_by_task="P1.7.7"`, `boundary_version="untrusted_content_boundary.v1"`.
- UntrustedContentBoundaryRegistry status: **LIVE schema** — binds boundaries with `created_by_task="P1.7.7"`, `registry_version="untrusted_content_boundary_registry.v1"`, explicit source label, notes, metadata, and deterministic order-insensitive `registry_hash`.
- Restriction/boundary/registry hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, content body scans, filesystem stat/exists/resolve data, environment variables, or cwd-derived live state.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — test fixtures use `DEV_FIXTURE`; production helper defaults remain `LIVE`.
- Information vs instruction boundary summary: untrusted content may inform but must never command; content boundary model is not active firewall; restriction is not enforcement; TRUSTED does not imply command authority; QUARANTINED means restricted not deleted.
- Known unavailable states: source provenance/evidence binding, path/source risk classifier, path governance resolver, source trust resolver, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem security, network access, sandbox hardening, runtime enforcement, trace hooks, policy bridge, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.8 readiness: **READY** — next task is Source Provenance & Evidence Binding Seed.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.7_UNTRUSTED_CONTENT_BOUNDARY_MODEL.md`

### P1.7.6 Path Authority Scope Model (COMPLETE — declarative scope model only)

- `path_governance/`: `PathAuthoritySubjectKind`, `PathAuthorityBasis`, `PathAuthorityConstraintKind`, `PathAuthoritySubject`, `PathAuthorityConstraint`, `PathAuthorityScope`, `PathAuthorityScopeRegistry`, `build_path_authority_scope()`, `build_path_authority_scope_registry()`.
- PathAuthoritySubjectKind status: **LIVE schema** — declared subject kind only; subject kind does not grant authority.
- PathAuthorityBasis status: **LIVE schema** — declared reason a scope exists; basis does not grant permission.
- PathAuthorityConstraintKind status: **LIVE schema** — future-governance constraint vocabulary; constraint kind does not enforce.
- PathAuthoritySubject status: **LIVE schema** — deterministic `subject_id`, display name, source label, JSON-safe metadata.
- PathAuthorityConstraint status: **LIVE schema** — deterministic `constraint_id`, reason, source label, JSON-safe metadata.
- PathAuthorityScope status: **LIVE schema** — binds subject, optional `root_id`, optional `PathIdentity`, `PathScopeAction` values, basis, constraints, deterministic `scope_id` and `scope_hash`, `created_by_task="P1.7.6"`, `scope_version="path_authority_scope.v1"`.
- PathAuthorityScopeRegistry status: **LIVE schema** — binds scopes with `created_by_task="P1.7.6"`, `registry_version="path_authority_scope_registry.v1"`, explicit source label, notes, metadata, and deterministic order-insensitive `registry_hash`.
- Subject/constraint/scope/registry hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, cwd-derived live state, or source/path content scans.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — test fixtures use `DEV_FIXTURE`; production helper defaults remain `LIVE`.
- Authority scope boundary summary: authority scope model is not an authority decision; authority declaration is not runtime permission; constraint does not enforce; scope registry is not sandbox; `PathScopeAction` remains declaration vocabulary only; no allow/deny/can_* APIs exist.
- Known unavailable states: untrusted content boundary model, path governance resolver, source trust resolver, path/source resolvers, path permission enforcement, filesystem security, sandbox hardening, runtime enforcement, trace hooks, policy bridge, projection/API/event contract, CLI/TUI binding, and Shell UI.
- P1.7.7 readiness: **READY** — next task is Untrusted Content Boundary Model.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.6_PATH_AUTHORITY_SCOPE_MODEL.md`

### P1.7.5 Path Normalization & Escape Detection Contract (COMPLETE — shadow contract only)

- `path_governance/`: `PathNormalizationStatus`, `PathEscapeSignal`, `PathNormalizationResult`, `normalize_path_for_governance()`, `PathBoundaryStatus`, `PathBoundaryCheckResult`, `EscapeDetectionContract`, `detect_path_escape_candidates()`.
- PathNormalizationStatus: **LIVE schema** — `NORMALIZED`, `NORMALIZED_WITH_WARNINGS`, `UNRESOLVED`, `UNSUPPORTED`, `ERROR`; not safety, permission, or authority.
- PathEscapeSignal: **LIVE schema** — `TRAVERSAL_SEGMENT`, `ROOT_MISMATCH_CANDIDATE`, `UNC_PATH_CANDIDATE`, etc.; shadow observation only, never enforcement.
- PathNormalizationResult: **LIVE schema** — preserves `raw_path`, `normalization_status`, `signals`, deterministic `normalized_path`/`display_path`, and `result_hash`.
- PathBoundaryStatus: **LIVE schema** — `PATH_OK`, `PATH_OUTSIDE_TRUSTED_ROOT`, `PATH_TRAVERSAL_CANDIDATE`, `PATH_UNKNOWN`, `PATH_UNRESOLVED`, `PATH_ERROR`; `PATH_OK` is string-context match only.
- PathBoundaryCheckResult: **LIVE schema** — `path_identity`, `trusted_root_id`, `trusted_root_normalized_path`, `boundary_status`, `reason`; always `shadow_only=True`, `enforced=False`.
- EscapeDetectionContract: **LIVE schema** — binds normalization and boundary results with `contract_version="path_escape_detection_contract.v1"`, `created_by_task="P1.7.5"`, and deterministic `contract_hash`.
- Deterministic hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, cwd-derived live state, or source/path content scans.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — test fixtures use `DEV_FIXTURE`; production helper defaults remain `LIVE`.
- Boundary summary: normalization means represent not resolve; escape detection means classify candidates not deny/block; traversal `..` segments are preserved and signaled; absolute paths without root context return `PATH_UNRESOLVED`.
- Known unavailable states: full path authority scope model, source provenance/evidence binding, source/path resolvers, trace hooks, policy bridge, projection/API/event contract, CLI/TUI binding, Shell UI, trusted root authority resolution, filesystem security, sandbox hardening, and runtime enforcement.
- P1.7.6 readiness: **READY** — next task is Path Authority Scope Model.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.5_PATH_NORMALIZATION_ESCAPE_DETECTION_CONTRACT.md`

### P1.7.4 Trusted Root & Scope Registry Seed (COMPLETE — registry schema only)

- `path_governance/`: `TrustedRootKind`, `PathScopeAction`, `PathScopeReason`, `TrustedRoot`, `PathScopeGrant`, `PathScopeDeny`, `TrustedRootRegistry`, `build_trusted_root_registry()`.
- TrustedRootKind status: **LIVE schema** — declared root boundary kind only; not permission, safety, sandbox policy, or authority.
- PathScopeAction status: **LIVE schema** — declared action vocabulary only; not runtime permission.
- PathScopeReason status: **LIVE schema** — explanation metadata only; not enforcement.
- TrustedRoot status: **LIVE schema** — represents a root declaration around a `PathIdentity`, source label, trust label, declared actions, reason, deterministic `root_id`, and metadata.
- PathScopeGrant status: **LIVE schema** — represents grantable scope declaration with deterministic `grant_id`; does not grant runtime authority.
- PathScopeDeny status: **LIVE schema** — represents denied/restricted scope declaration with deterministic `deny_id`; does not enforce runtime blocking.
- TrustedRootRegistry status: **LIVE schema** — binds roots/grants/denies with `created_by_task="P1.7.4"`, `registry_version="trusted_root_registry.v1"`, explicit source label, notes, metadata, and deterministic order-insensitive `registry_hash`.
- Root/grant/deny/registry hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat/exists/resolve data, environment variables, cwd-derived live state, or source/path content scans.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Source-label truth status: **PASS** — registry/root source labels are preserved; test fixture roots use `DEV_FIXTURE`; no fake LIVE fixture root state is claimed.
- Registry boundary summary: Trusted root does not mean permission; scope grant does not mean runtime authority; scope deny does not mean enforcement; registry seed does not mean sandbox; repo root does not mean executable-safe; workspace root does not mean sandbox permission; operator-approved does not override policy; uploads do not become trusted; denied root does not block runtime yet.
- Known unavailable states: Path normalization / escape detection, full path authority scope model, source provenance/evidence binding, source/path resolvers, trace hooks, policy bridge, projection/API/event contract, CLI/TUI binding, Shell UI, trusted root authority resolution, filesystem security, sandbox hardening, and runtime enforcement.
- P1.7.5 readiness: **READY** — next task is Path Normalization & Escape Detection Contract.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.4_TRUSTED_ROOT_SCOPE_REGISTRY_SEED.md`

### P1.7.3 Source Trust Label Taxonomy (COMPLETE — taxonomy only)

- `path_governance/`: `TrustPosture`, `TrustLabelDefinition`, `SourceTrustTaxonomy`, `build_source_trust_taxonomy()`.
- TrustPosture status: **LIVE schema** — semantic grouping only; not resolver output, permission, memory authority, prompt authority, command authority, or enforcement.
- TrustLabelDefinition status: **LIVE schema** — every `SourceTrustLabel` has a definition, allowed interpretations, forbidden interpretations, authority statement, explicit review default, deterministic `definition_hash`, and JSON-safe metadata.
- SourceTrustTaxonomy status: **LIVE schema** — covers every `SourceTrustLabel` exactly once, carries `ProjectionSourceLabel`, `created_by_task="P1.7.3"`, `taxonomy_version="source_trust_taxonomy.v1"`, notes, metadata, and deterministic `taxonomy_hash`.
- Deterministic hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat data, environment variables, cwd values, or source content scans.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Semantic boundary summary: TRUSTED does not mean unlimited authority; OPERATOR_PROVIDED does not override policy; INTERNAL_REPO does not mean executable-safe; LOCAL_PRIVATE does not mean safe to expose; TOOL_GENERATED does not mean true; EXTERNAL can inform but cannot command; UNTRUSTED can be identified/cited but cannot command; UNKNOWN is explicit uncertainty, not implicit trust; QUARANTINED means restricted, not deleted.
- Known unavailable states: Source provenance/evidence binding, source/path resolvers, trace hooks, policy bridge, projection/API/event contract, CLI/TUI binding, Shell UI, source authority resolution, memory/prompt/command authority, untrusted content boundary decisions, path/source conflict rules, and runtime enforcement.
- P1.7.4 readiness: **READY** — next task is Trusted Root & Scope Registry Seed.
- Local commit status: committed locally, no push performed.
- Report: `agent/reports/P1.7.3_SOURCE_TRUST_LABEL_TAXONOMY.md`

### P1.7.2 Source Identity & SourceRef Schema (COMPLETE — schema only)

- `path_governance/`: `SourceKind`, `SourceOrigin`, `SourceLineageRelationship`, `SourceRef`, `SourceLineageRef`, `SourceIdentity`, `build_source_identity()`.
- SourceKind status: **LIVE schema** — represents operator input, repo file, local file, uploaded file, external web, tool output, model output, agent output, memory entry, path-ref source, and unknown source kinds.
- SourceOrigin status: **LIVE schema** — represents operator, internal repo, local machine, upload, external network, governed tool, model, agent, memory, and unknown origins.
- SourceLineageRelationship status: **LIVE schema** — flat lineage seed relationships only; no provenance graph or evidence binding.
- SourceRef status: **LIVE schema** — deterministic `source_id`, kind/origin labels, projection source label, trust label metadata, optional display name, optional URI/path, optional explicit content hash, and JSON-safe metadata.
- SourceLineageRef status: **LIVE schema** — deterministic `lineage_hash` over parent source ID, relationship, notes, and metadata; no parent lookup.
- SourceIdentity status: **LIVE schema** — binds source ref and lineage refs with deterministic `identity_hash`, `created_by_task="P1.7.2"`, `schema_version="source_identity.v1"`.
- Deterministic source/hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, network data, file contents, filesystem stat data, or environment variables.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Known unavailable states: Source Trust Label Taxonomy expansion, source trust resolver, source authority resolver, provenance/evidence binding, full provenance graph, memory/prompt/command authority, untrusted content boundary decisions, projection/API/event contract, CLI/TUI, Shell UI, trace hooks, policy bridge, and enforcement.
- P1.7.3 readiness: **READY** — next task is Source Trust Label Taxonomy.
- Report: `agent/reports/P1.7.2_SOURCE_IDENTITY_SOURCE_REF_SCHEMA.md`

### P1.7.1 Path Identity & Canonical Path Schema (COMPLETE — schema only)

- `path_governance/`: `PathKind`, `PathSensitivity`, `CanonicalizationStatus`, `PathRef`, `CanonicalPathRef`, `PathIdentity`, `build_path_identity()`.
- PathRef status: **LIVE schema** — preserves `raw_path`, kind/sensitivity declaration, source label, and JSON-safe metadata.
- CanonicalPathRef status: **LIVE schema** — separates raw/normalized/display paths, status, warnings, `path_hash`, and `canonical_hash`.
- PathIdentity status: **LIVE schema** — binds path/canonical refs with deterministic `identity_hash`, `created_by_task="P1.7.1"`, `schema_version="path_identity.v1"`.
- Deterministic hash readiness: **PASS** — stable SHA-256 over canonical JSON; no timestamps, UUIDs, random values, cwd-derived state, or filesystem stat data.
- Closed-world validation: **PASS** — unknown fields reject with `UNKNOWN_FIELD`; `shadow_authority_grant` is rejected.
- Known unavailable states: SourceRef, path/source resolver, trusted roots, path escape detection, projection/API/event contract, CLI/TUI, Shell UI, trace hooks, policy bridge, and enforcement.
- P1.7.2 handoff: **COMPLETE** — Source Identity & SourceRef Schema now follows this layer.
- Report: `agent/reports/P1.7.1_PATH_IDENTITY_CANONICAL_PATH_SCHEMA.md`

### P1.7.0 Path Governance & Source Trust Foundation (COMPLETE — foundation only)

- `path_governance/`: `ProjectionSourceLabel`, `SourceTrustLabel`, `FoundationPosture`, `PathGovernanceCapabilityStatus`, closed-world validation, canonical JSON + stable hash, `get_path_governance_foundation_status()`.
- Posture: **FOUNDATION_ONLY**; enforcement/resolver/projection/CLI/trace/policy-bridge all **false** with honest unavailable reasons.
- Report: `agent/reports/P1.7.0_PATH_GOVERNANCE_SOURCE_TRUST_FOUNDATION.md`

### P1.6.20 P1.6 Exit Seal + Live Integration Demo (COMPLETE — seal only)

- `policy_cards/exit_seal.py`: read-only exit seal proof layer; 20 checks; deterministic report hash; `PASS_WITH_WARNINGS` verdict.
- Proves backend → `PolicyProjectionContract v1` → CLI binding → report/evidence without enforcement.
- Shell UI: **UNAVAILABLE** (honest). Trace modules: LIVE; full Ledger integration **not claimed** (WARN).
- Report: `agent/reports/P1.6.20_POLICY_EXIT_SEAL_LIVE_INTEGRATION_DEMO.md`

### P1.6.19 Policy Docs/State/Reports Update (COMPLETE — truth-sync only)

- `policy_cards/projection_contract.py`: `PolicyProjectionContract v1` (`policy_projection.v1`), eight sections, readiness flags, source labels, deterministic `projection_hash`, JSON-safe payload, event payload seed.
- Backend modules report availability via symbol presence; projection does not execute resolver during build.
- Report: `agent/reports/P1.6.17_POLICY_PROJECTION_API_EVENT_CONTRACT_REPORT.md`

### P1.6.18 Policy CLI/TUI Binding (COMPLETE — CLI only)

- `cli_modules/policy_commands.py`: read-only `policy status`, `policy projection`, `policy unavailable`, `policy harness list/run` consuming P1.6.17 contract.
- Entry: `python -m agentic_runtime.cli policy …` (not `aurel`).
- `cli_binding` section: **LIVE**; `shell_binding`: **UNAVAILABLE** (no Shell UI, no full TUI app).
- Report: `agent/reports/P1.6.18_POLICY_CLI_TUI_BINDING_REPORT.md`

### P1.6.19 Policy Docs/State/Reports Update (COMPLETE — truth-sync only)

- Synchronizes `agent/ROADMAP.md`, `STATE.md`, `TESTS.md`, `REPORTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `ACTIVE_TASK.md`.
- Full report: `agent/reports/P1.6.19_POLICY_DOCS_STATE_REPORTS_UPDATE.md`
- P1.6.20 exit-seal checklist (20 items) documented; P1.6 is seal-ready for live integration demo.

### Source label doctrine (v5.1)

| Label | Meaning |
|-------|---------|
| LIVE | Real backend/projection/runtime data |
| TRACE_VERIFIED | Trace/evidence hash present |
| SIMULATED | Dry-run/simulation |
| DEV_FIXTURE | Visible test/demo fixture |
| UNAVAILABLE | Not implemented — reason required |
| ERROR | Failed attempt — safe error info required |

Backend is source of truth. No unlabelled mock operational state. Shell UI remains UNAVAILABLE unless implemented.

### P1.6.20 readiness

- P1.6 section sealed with warnings (2026-06-25).
- Exit seal module + 42 focused tests + 137 regression tests pass.
- Known UNAVAILABLE: Shell UI, full Ledger trace write, policy enforcement.
- Next path-governance task: P1.7.20 — Exit Seal + Live Integration Demo.

### P1.6.17 Policy Projection/API/Event Contract (COMPLETE — read model only)

Security fixes:
- **Snapshot path traversal**: `_WorkspaceBackend.read_snapshot_file` now routes through `CanonicalPathResolver` (already used by `read_file`, `write_file`, `delete_file`). Parent traversal (`../`), absolute paths, and symlink escapes are rejected. 9 security tests in `tests/test_snapshot_security_p1610h.py`.
- **Unsafe/restricted_local honesty**: `materialize_sandbox_backend` now routes non-hard backends through `create_sandbox(allow_unsafe=True)` instead of silently instantiating `UnsafeLocalSandbox`. The `allow_unsafe=True` gate makes the safety trade-off explicit. 3 honesty tests.

Coverage truth:
- Canonical coverage command: `.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75`
- Coverage measures `src/agentic_runtime` (real runtime source) — not the `agentic_runtime` package namespace.

Local state:
- `.git/info/exclude` cleaned — `.composer/` and `.strategic-composer/` directories excluded from git tracking.

Documentation:
- Canonical validation commands updated (venv requirement, coverage path, fail-under gate).
- Sandbox layer disambiguation: four layers clearly distinguished (runtime sandbox policy, sandbox backend, sandbox policy card, Custos v0 resolver).
- All agent docs updated for P1.6.10H phase.

### P1.6.11 Policy Resolution Context & Registry Binding (COMPLETE — shadow binding only)

- `policy_cards/registry.py`: `PolicyCardRegistry` accepts explicit typed card instances/lists, detects duplicate card IDs deterministically, deduplicates identical duplicates, rejects same ID with different canonical hash, returns stable family/scope lookups, applicability explanations, source hashes, canonical dict, and canonical hash. No database, no filesystem discovery, no runtime imports.
- `policy_cards/context_binding.py`: `build_policy_resolution_context()`, `normalize_resolution_context()`, and `context_from_*_like()` helpers convert runtime-like dicts/lightweight objects into deterministic `PolicyResolutionContext`. Dict inputs are closed-world; list/set-like fields are sorted; metadata is JSON-safe and non-authoritative.
- `policy_cards/risk_mapping.py`: minimal risk-vocabulary bridge maps known runtime/approval/policy/identity values to P1.6 `RiskTier`. Unknown present values map conservatively to R5 with explicit reason codes; invalid value types fail closed.
- `policy_cards/resolver.py`: `resolve_policy_cards_from_registry()` and `PolicyRuntimeResolver.resolve_from_registry()` feed registry-selected applicable cards into the existing Custos v0 resolver. Output remains `ResolvedPolicySet` in SHADOW mode with `WOULD_*` actions.
- `tests/test_policy_registry_binding_p1611.py`: 22 focused tests for registry construction, duplicate handling, family/scope lookup, applicability, context binding, risk mapping, resolver integration, exports, and non-enforcement guarantees.

**P1.6.11 binds policy-card discovery and context assembly to the Custos v0 resolver, but it does not enforce resolver outcomes through `AgenticRuntime.submit()`.** No command blocking, approval activation, sandbox runtime bridge, or active runtime policy-card enforcement is implemented.

### P1.6.12 Custos Shadow Runtime Projection & Submit Observability Hook (COMPLETE — observability only)

- `policy_cards/runtime_projection.py`: `RuntimePolicySnapshot`, `PolicyShadowProjection`, effective-action/alignment/mismatch enums, deterministic canonical dict/hash helpers, and JSON-safe validation. Projection objects are hard-coded shadow-only (`mode="shadow_only"`, `enforced=False`) and expose no enforcement-like methods.
- `AgenticRuntime.submit()`: optional default-disabled hook attaches `ObservationEnvelope.artifacts["policy_shadow_projection"]` before transition append when both `enable_policy_shadow_projection=True` and an explicit `PolicyCardRegistry` are configured.
- `build_runtime()`: accepts `policy_card_registry` and `enable_policy_shadow_projection`, both defaulting to no-op behavior. Runtime creates no default cards, discovers no files, and uses no global registry.
- Runtime behavior remains P0-authoritative: policy, approval, sandbox, budget, verifier, rollback, trace, and memory outcomes are unchanged by Custos shadow decisions. Shadow failures attach `SHADOW_ERROR` metadata and do not crash submit.
- `tests/test_policy_runtime_projection_p1612.py` and `tests/test_runtime_custos_shadow_submit_p1612.py`: 26 focused tests covering projection determinism, matrix behavior, no-enforcement invariants, submit no-op modes, stricter Custos/runtime visibility, sandbox mismatch visibility, shadow failure degradation, approval behavior, verifier, and rollback-preserving write success.

**Custos shadow decisions are not enforcement decisions. P0 runtime remains authoritative.** Fail-closed apply, `run_shell` string rejection, and Bandit B310/B108 fixes remain deferred.

### P1.6.13 Policy Conflict Algebra & Strictest-Wins Rules (COMPLETE — shadow-only)

- `policy_cards/conflict_algebra.py`: new pure module with 6 enums (`PolicyDecisionRank`, `PolicyConflictType` 14 values, `PolicyConflictSeverity`, `PolicyConflictResolutionStrategy`), 6 frozen dataclasses (`PolicySpecificityScore`, `PolicyPrecedenceRule`, `PolicyConflict`, `PolicyConflictSet`, `PolicyConflictResolution`, `StrictestWinsResult`), normalization helpers, strictest-wins resolution algorithm, 14-type conflict classifier, specificity scoring, deterministic SHA-256 hashing. No runtime/enforcement imports.
- `policy_cards/resolution_result.py`: optional `conflict_resolution: dict | None` and `conflict_hash: str | None` fields on `ResolvedPolicySet` (default `None`, fully backwards compatible).
- `policy_cards/resolver.py`: `_attach_conflict_metadata()` calls into `resolve_policy_conflicts_strictest_wins()` after `aggregate_family_decisions()`, attaching conflict metadata to the `ResolvedPolicySet` before hashing.
- `policy_cards/__init__.py`: ~14 new public exports.
- Strictest-wins rules: ERROR(5) > DENY(4) > REQUIRE_APPROVAL(3) > WARN(2) > ALLOW(1) > NOT_APPLICABLE(0); tie-breaks: specificity → family_order → lexical card_id.
- `tests/test_policy_conflict_algebra_p1613.py`: 73 pure-module tests for ranking, strictest-wins matrix, determinism, taxonomy, specificity, non-enforcement.
- `tests/test_policy_resolver_conflict_algebra_p1613.py`: resolver integration tests for metadata, backwards compat, shadow-only invariants.

**P1.6.13 formalizes Custos shadow conflict resolution through deterministic strictest-wins algebra; it does not enforce policy decisions, activate approvals, block commands, or change runtime sandbox behavior.**

### P1.6.14 Policy Resolution Trace Hook (COMPLETE — trace-compatible evidence only)

- `policy_cards/resolution_trace.py`: new module with `PolicyResolutionTraceEvent` (frozen dataclass, shadow_only=True enforced=False, 20+ trace fields), `PolicyResolutionTraceEnvelope`, `PolicyResolutionEvidenceRef`, `PolicyTraceBinding` frozen dataclasses; `build_policy_resolution_trace_event()`, `build_policy_resolution_trace_envelope()`, `policy_trace_canonical_dict()`, `policy_trace_hash()` builder/hash functions. All hash fields optional (explicit empty string), trace_id derived from deterministic SHA-256 hash. No runtime/Ledger imports.
- `policy_cards/resolution_result.py`: optional `resolution_trace: dict | None`, `resolution_trace_hash: str | None`, `resolution_trace_id: str | None` fields on `ResolvedPolicySet` (default `None`). Included in canonical dict when `include_hash=True`, excluded from `canonical_hash`.
- `policy_cards/resolver.py`: `_attach_trace_metadata()` builds trace event from resolution, conflict, and source metadata; called after `_attach_conflict_metadata()`.
- `policy_cards/runtime_projection.py`: `resolution_trace_id` and `resolution_trace_hash` fields on `PolicyShadowProjection`; propagated from `ResolvedPolicySet` in `project_policy_resolution_against_runtime()`.
- `policy_cards/__init__.py`: ~8 new public exports.
- `tests/test_policy_resolution_trace_p1614.py`: 32 tests for construction, canonicalization/hash determinism, safety, invariants, envelope/binding.
- `tests/test_policy_resolver_trace_hook_p1614.py`: 14 tests for resolver integration, backwards compat, non-enforcement.
- `tests/test_policy_runtime_projection_trace_p1614.py`: 9 tests for projection trace metadata, shadow-only invariants.

**P1.6.14 creates trace-compatible policy resolution evidence; it does not write to the Ledger, enforce policy decisions, activate approvals, block commands, or change runtime sandbox behavior.**

### Sandbox Layer Disambiguation

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
   - Resolver-ready — NOT runtime-enforced yet.
   - `SandboxPolicyCard`, `evaluate_sandbox_policy_decision()`, `SandboxPolicyDecision`.

4. **Custos v0 resolver** (`policy_cards/resolver.py` + `resolution_context.py` + `resolution_result.py`)
   - P1.6.10 shadow-only resolver.
   - Produces `WOULD_*` decisions.
   - Does NOT block runtime behavior.

**P1.6.9 sandbox policy cards and P1.6.10 resolver do not yet enforce runtime sandbox behavior. Runtime enforcement still flows through the P0 runtime policy and sandbox layers.**

### P1.6.10 Custos v0 Policy Runtime Resolver (COMPLETE — shadow mode only)

- `policy_cards/resolution_context.py`: `PolicyResolutionContext` (closed-world, deterministic canonical serialization + SHA-256 `context_hash`, `from_dict`); `EnforcementMode` (SHADOW supported; ENFORCE/SIMULATE reserved, fail-closed rejected).
- `policy_cards/resolution_result.py`: `PolicyFamily`, `FamilyDecision`, `ShadowAction` (WOULD_*), `PolicyFamilyDecision`, `ResolvedPolicySet` (deterministic canonical dict + SHA-256 `canonical_hash`; `would_allow/would_warn/would_require_approval/would_deny`).
- `policy_cards/resolver.py`: seven family adapters (risk tier, human oversight, data residency, tool permission, memory write, prompt, sandbox), strictest-wins MVP aggregation, `resolve_policy_cards()`, `PolicyRuntimeResolver`, `aggregate_family_decisions()`.
- Resolver accepts explicit cards, determines applicable cards minimally, emits per-family decisions, SHADOW only, WOULD_* effective actions, strictest-wins works, no-card / no-applicable-card behavior is conservative WARN (never silent allow); result carries reason codes, applicable card IDs, source hashes, context hash; deterministic serialization + hashes.
- **`AgenticRuntime.submit()` is NOT modified; nothing is enforced.** Custos interprets policy cards; it does not yet dispose. 5 resolver error classes added. 51 new tests in `tests/test_policy_resolver_p1610.py`.
- Limitations: MVP adapters (not full semantics), no Policy Conflict Algebra, registry/context binding is implemented in P1.6.11, and active runtime enforcement remains deferred to P1.6.12+.

### P1.6.9 Sandbox Policy Card (COMPLETE)

- `policy_cards/sandbox.py` + `sandbox_schema.py`: 6 enums, backend/filesystem/egress/command-class rules, risk-tier sandbox mappings, approval policy, deny-by-default, secrets-path/escape detection, deterministic serialization + hash, and resolver-ready `evaluate_sandbox_policy_decision()` → `SandboxPolicyDecision` consumed by P1.6.10. No real sandbox execution; no Docker/Bubblewrap dependency.

## What works

- Full governed command pipeline: policy → HITL → budget → sandbox → verify → trace → memory
- ...
- P1.4.14 Operator Consent Binding: delta-bound consent with attestation binding, risk acknowledgement, 55 tests
- P1.4.15 Identity Governance Command Surface: unified CLI, `identity status`/`verify`, JSON envelope, 53 tests
- Plan validation halts on empty/invalid/unsupported plans
- Persistent and in-memory trace ledgers with hash-chain verification
- P1.5.10X canonical AurelTraceLog contracts
- P1.5.11A Golden Thread A
- P1.5.11B Capability Evidence ↔ Trace / Context Binding
- P1.5.12 Evaluation Case Extraction Seed: candidate EvaluationCase/RegressionCandidate from capability evidence, 42 extraction tests
- **P1.5.13 Verifier Normalization with Limitations**:
  - `src/agentic_runtime/contracts/verifier.py` upgraded with `VerifierKind` enum (6 kinds), `VerifierNormalizationReport`, and enhanced `VerifierResult` v2 with `verifier_kind`, `normalized_from`, `created_at`
  - `src/agentic_runtime/evaluation/verifier_normalization.py`: 6 stub verifier normalizers (deterministic, operator review, policy check, LLM judge stub, context adequacy, evidence integrity)
  - Golden Thread A now uses normalized `VerifierResult` via `EvidenceIntegrityVerifierStub`
  - Hard invariants enforced: non-empty limitations, evidence_refs for pass, source_trace_event_ref required, reason non-empty, confidence 0.0–1.0
  - 32 new normalization tests, all 802 core tests pass
  - No raw verifier output reaches capability evidence or evaluation cases
  - Next: P1.5.14 Evaluation Mirror Runtime Hook
- **P1.5.14 Evaluation Mirror Runtime Hook**:
  - `src/agentic_runtime/contracts/evaluation_runtime.py`: 5 new contracts (EvaluationTargetRef, EvaluationRequest, EvaluationRun, EvaluationEvent, EvaluationRunResult) + 5 enums
  - `src/agentic_runtime/evaluation/runtime_hook.py`: `run_evaluation()` runtime-callable hook
  - Golden Thread A extended with evaluation runtime integration; GoldenThreadAResult gains 5 new fields
  - Anti-promotion structural enforcement: no capability_promoted, memory_written, skill_created, reflex_created, policy_changed fields in any contract
  - 49 new tests (25 hook, 18 invariants, 6 golden thread), all 851 core tests pass
  - **P1.5.18 Evaluation ↔ Memory Candidate Bridge (COMPLETE)**:
  - Bridges evaluation/feedback/capability outputs to MemoryCandidate records
  - MemoryCandidate is candidate-only; NEVER committed, NEVER active recall, NEVER creates skills/reflexes/policies
  - 6 enums, 4 dataclasses with strict __post_init__ validation
  - 41 new tests (21 bridge, 8 derivation, 12 invariants)
  - Golden Thread A extended with memory candidate + bridge report fields
  - memory_committed is structurally always False
  - **P1.5.19 P1.5 Integrated Seal (COMPLETE)**:
  - Seals the entire P1.5 subsystem — proves coherence, trace-binding, evidence-binding, limitation-binding, candidate-safety, and non-promotional guarantees
  - 4 new contracts: P15IntegratedSealReport, GoldenThreadASealReport, ContractInvariantChecklist (18 invariants), ColdCacheVerificationReport
  - 1 seal runner: run_p15_integrated_seal()
  - 41 new tests: full seal, trace integrity, candidate boundaries, anti-overclaim, no-promotion, verification gate
  - Golden Thread A produces seal reports after P1.5.18 memory bridge
  - All 18 hard invariants pass; cold-cache verification required; no hidden promotions
  - P1.5 sealed — next is P1.6.0 Policy Cards & Behavioral Contracts
  - **P1.6.0 Policy Card Foundation (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/` — first-class policy card foundation module
  - 3 enums: `PolicyCardKind` (10 kinds), `PolicyCardStatus` (5 statuses), `PolicyCardScopeType` (10 scope types)
  - 8 frozen dataclasses: `PolicyCard`, `PolicyCardIdentity`, `PolicyCardScope`, `PolicyCardRiskBinding`, `PolicyCardAuthorityBinding`, `PolicyCardSource`, `PolicyCardValidationIssue`, `PolicyCardValidationResult`
  - Closed-world validation: unknown top-level fields fail, dangerous metadata keys fail
  - Deterministic canonical serialization (sorted keys, compact JSON)
  - SHA-256 canonical hash readiness
  - Error taxonomy: 6 error classes (`PolicyCardError`, `PolicyCardValidationError`, etc.)
  - `load_policy_card_from_dict()` dict loader
  - 59 tests; no runtime resolver, conflict detector, CLI, or P25 hardening
  - Policy cards are foundation only — no enforcement yet
  - **P1.6.1 Policy Card Schema (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/schema.py` — centralized schema v1 contract
  - `schema_version` added to `PolicyCard` (required, must be "1.0")
  - Centralized field classifications: required/optional/forbidden/canonical/control/governance/source/descriptive/identity/runtime-future
  - Expanded dangerous field set (25 top-level + 31 metadata keys from 18 + 21 in P1.6.0)
  - Deterministic `export_policy_card_schema()` and helpers
  - Validation refactored to use schema definitions (no scattered inline lists)
  - Runtime-future reserved fields rejected (resolver, enforcement, conditions, etc.)
  - 61 new tests (120 total policy card tests); no resolver/enforcement/CLI yet
  - **P1.6.2 Behavioral Contract Schema (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/contracts.py` — 24 enums + 15 frozen dataclasses for behavioral contracts
  - `src/agentic_runtime/policy_cards/contract_schema.py` — centralized Behavioral Contract Schema v1
  - BehavioralContract models: identity, subject, scope, obligations, prohibitions, preconditions, postconditions, evidence requirements, escalation rules
  - Behavioral contracts can reference policy card IDs via `policy_card_refs`
  - Closed-world validation, deterministic serialization, SHA-256 canonical hashing
  - Behavioral contract error hierarchy (6 classes) extending PolicyCardError
  - ~44 new public exports; 96 new tests
  - No runtime enforcement, no resolver, no CLI
  - **P1.6.3 Risk Tier Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/risk_tiers.py` - R0-R6 typed risk-tier model, validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/risk_tier_schema.py` - Risk Tier Policy Card Schema v1, required fields, dangerous metadata keys, default definitions, action-class mapping seeds
  - RiskTierPolicyCard exists and remains compatible with generic `PolicyCard(kind="risk_tier")`
  - Default R0-R6 tier definitions exist with reversibility, oversight, evidence expectations, and semantic default flags
  - R5 requires trace, evidence, approval, irreversible reversibility, and explicit Operator confirmation
  - R6 is denied/non-permissive and cannot allow execution, external egress, memory write, or tool write
  - Reversible and compensatable remain distinct
  - Closed-world dict loading rejects unknown top-level/nested fields and dangerous metadata
  - Deterministic canonical serialization and SHA-256 canonical hash are available
  - 36 new focused tests; P1.6.0-P1.6.3 focused suite passes
  - No runtime risk classifier, no policy resolver, and no runtime enforcement yet
  - **P1.6.4 Human Oversight Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/human_oversight.py` - 5 enums (HumanOversightLevel/Mode/Trigger/Action, OversightEvidenceType), 7 frozen dataclasses (ConfirmationRequirement, ReviewerRequirement, OversightEvidenceRequirement, RiskTierOversightMapping, HumanOversightEscalationRule, HumanOversightPolicyCard), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/human_oversight_schema.py` - Human Oversight Policy Card Schema v1, required/optional/forbidden/canonical fields, dangerous metadata keys, default R0-R6 oversight mappings, default escalation rules
  - HumanOversightPolicyCard exists and remains compatible with generic `PolicyCard(kind="human_oversight")`
  - Default R0-R6 oversight mappings exist: R0-R1 none, R2 notify_only, R3 review_recommended, R4 approval_required, R5 explicit_confirmation_required (with strong confirmation and reviewer requirements), R6 deny
  - R4 must be approval_required or stricter; R5 must be explicit_confirmation_required with strong confirmation requirement; R6 must be deny and not approvable
  - Closed-world dict loading rejects unknown top-level/nested fields and dangerous metadata (auto_approve, operator_not_required, bypass_policy, etc.)
  - Deterministic canonical serialization and SHA-256 canonical hash are available
  - 68 new focused tests; P1.6.0-P1.6.4 focused suite passes (320 tests)
  - No runtime approval engine, no policy resolver, no enforcement, no CLI/report yet
  - **P1.6.5 Data Residency Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/data_residency.py` - 6 enums (DataResidencyZone 7 values, DataClass 20 values, ProcessingLocation 7 values, RedactionRequirementType 9 values, StorageRequirementType 6 values, DataExposurePermission 8 values), 8 frozen dataclasses (RedactionRequirement, StorageRequirement, DataEgressRule, DataExposureRule, DataResidencyRule, DataResidencyPolicyCard, DataResidencyValidationIssue, DataResidencyValidationResult), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/data_residency_schema.py` - Data Residency Policy Card Schema v1, 10 required data classes, 6 strict local-only data classes, required/optional/forbidden/canonical field tuples, sub-object field tuples, dangerous metadata keys (17), schema export functions
  - DataResidencyPolicyCard exists and remains compatible with generic `PolicyCard(kind="data_residency")`
  - Strict safety rules enforced at card validation: local_only zero-outbound (no egress/external-model/API/web), credentials no-egress + encryption + audit required, sensitive_personal_data/memory_record/trace_record local-only + no-egress, forbidden zone non-permissive
  - Default factory produces 20 data class rules with strict defaults: all classes local-only except public; credentials/sensitive_personal_data with redaction/storage/encryption requirements
  - Closed-world dict loading rejects unknown fields and dangerous metadata keys (allow_secret_egress, bypass_residency, skip_encryption, etc.)
  - Deterministic canonical serialization (sorted key stable) and SHA-256 hash
  - 48 new focused tests; P1.6.0-P1.6.5 focused suite passes (368 tests)
  - No runtime egress enforcement, model routing, data classification, redaction/encryption execution, or conflict resolution yet
  - **P1.6.6 Tool Permission Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/tool_permissions.py` - 5 enums (ToolCategory 17 values, ToolPermissionType 26 values, ToolPermissionDecision 8 values, ToolScopeType 12 values, ToolMatchMode 5 values), 6 frozen dataclasses (ToolIdentityMatcher, ToolPermissionCondition, ToolPermissionRule, ToolPermissionPolicyCard, ToolPermissionValidationIssue, ToolPermissionValidationResult), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/tool_permission_schema.py` - Tool Permission Policy Card Schema v1, required/optional/forbidden/canonical field tuples, sub-object field tuples, dangerous metadata keys (17), dangerous/high-risk permission types, default deny categories, schema export functions
  - ToolPermissionPolicyCard exists and remains compatible with generic `PolicyCard(kind="tool_permission")`
  - Strict deny-by-default posture: default_decision must be deny, unknown categories must deny, credential access denied, shell command requires sandbox/approval, network/egress governed, execute/delete/config-write require governance
  - Data residency compatibility: protected data classes (credentials, operator_private, sensitive_personal_data, memory_record, trace_record, source_code) cannot be exposed through external tools
  - Default factory produces 18 rules: unknown deny, credential deny, shell sandbox, egress deny/governed, filesystem read/write/delete governed, memory read/write governed, model local-only, email explicit confirmation, artifact export governed, config write approved, network governed, browser governed, GitHub/database governed
  - Closed-world dict loading rejects unknown fields and dangerous metadata keys (allow_all_tools, bypass_tool_policy, shell_unrestricted, etc.)
  - Deterministic canonical serialization and SHA-256 hash
  - 38 new focused tests; P1.6.0-P1.6.6 focused suite passes (406 tests)
  - No Tool Gateway enforcement, registry resolver, sandbox execution, network blocking, filesystem/path enforcement, credential system, memory write enforcement, model routing, or runtime permission engine yet
  - **P1.6.7 Memory Write Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/memory_write.py` - 6 enums (MemoryZone 14 values, MemoryWriteType 18 values, MemoryWriteDecision 10 values, MemoryVerificationStatus 8 values, MemoryRetentionClass 6 values, MemoryWriteRequirementType 13 values), 5 frozen dataclasses (MemoryWriteRequirement, MemoryWriteRule, MemoryWritePolicyCard, MemoryWriteValidationIssue, MemoryWriteValidationResult), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/memory_write_schema.py` - Memory Write Policy Card Schema v1, required/optional/forbidden/canonical field tuples, sub-object field tuples, dangerous metadata keys (19), PROTECTED_MEMORY_ZONES, STRICT_MEMORY_DATA_CLASSES, DEFAULT_MEMORY_WRITE_RULES (14 rules), schema export functions
  - MemoryWritePolicyCard exists and remains compatible with generic `PolicyCard(kind="memory_write")`
  - Memory zone / write type / decision / verification status / retention class vocabulary exists
  - Conservative deny-by-default posture: default_decision must be deny/forbidden
  - No silent canonical memory writes: canon_memory cannot be plain allow and requires source/evidence/trace references + operator review + explicit confirmation + conflict check
  - Policy memory protection: policy_memory requires policy authority + source/evidence/trace + operator review or explicit confirmation
  - Verified skill memory requires evaluation result + verification + evidence/trace references
  - Skill candidate memory cannot be verified/canonized by default (candidate ≠ verified ≠ canon)
  - Operator profile protection: requires user consent or operator review + source/provenance, trace when durable
  - Credentials cannot become durable memory by default; sensitive_personal_data writes are strict (evidence + provenance + residency check + review)
  - Scratchpad ephemeral and working memory session-scoped writes permitted with low friction
  - Closed-world dict loading rejects unknown fields and dangerous metadata keys (auto_canonize, bypass_memory_policy, remember_everything, consent_not_required, store_credentials, etc.)
  - Deterministic canonical serialization (sorted key stable) and SHA-256 hash
  - 60 new focused tests; P1.6.0-P1.6.7 focused suite passes (466 tests)
  - No Mneme storage engine, memory writing, retrieval, ranking, consolidation, memory graph, canon promotion engine, skill promotion engine, Verification Court, operator consent workflow, memory conflict detector, policy runtime resolver, or runtime enforcement yet
  - **P1.6.8 Prompt Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/prompt_policy.py` - 7 enums (PromptSourceType 19 values, PromptTrustLevel 10 values, PromptRole 16 values, PromptPolicyDecision 10 values, PromptInjectionRisk 5 values, PromptInjectionPattern 15 values, PromptBoundaryRequirementType 14 values), 5 frozen dataclasses (PromptBoundaryRequirement, PromptInjectionSignal, PromptHandlingRule, PromptPolicyCard, PromptPolicyValidationIssue, PromptPolicyValidationResult), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/prompt_policy_schema.py` - Prompt Policy Card Schema v1, required/optional/forbidden/canonical field tuples, sub-object field tuples, dangerous metadata keys (21), TRUSTED/UNTRUSTED/EXTERNAL/PROTECTED prompt source sets, DEFAULT_PROMPT_HANDLING_RULES (15 rules), schema export functions
  - PromptPolicyCard exists and remains compatible with generic `PolicyCard(kind="prompt")`
  - Prompt source / trust level / role / decision / injection-risk vocabulary exists
  - Strict deny-by-default posture: default_decision must be deny/forbidden
  - Core law enforced — untrusted content may inform but never command: unknown source cannot be trusted; external content (web/email/file/code/external_api/retrieved_document/tool_output/unknown) cannot be instruction authority; tool output is data/context, not command; retrieved memory is context, not automatic authority
  - Untrusted/external/tool-output/retrieved trust levels cannot request tools, write memory, modify policy, or modify identity
  - High/critical injection risk cannot pair with allow + instruction authority
  - Closed-world dict loading rejects unknown fields and dangerous metadata keys (bypass_prompt_policy, reveal_system_prompt, grant_tool_access, external_as_instruction, trust_unknown_source, etc.)
  - Deterministic canonical serialization (sorted key stable) and SHA-256 hash
  - 74 new focused tests; P1.6.0-P1.6.8 focused suite passes (540 tests)
  - No prompt compiler, prompt assembly engine, instruction-hierarchy runtime enforcement, prompt injection detector, jailbreak detector, tool-call runtime blocking, memory write enforcement, identity compiler change, policy resolver, or runtime enforcement yet
  - **P1.6.8S Repository Reality & Policy Card Stabilization Seal (COMPLETE)**:
  - Git/docs/test/lint reality reconciled after P1.6.8 and before P1.6.9
  - Legitimate P1.6.4-P1.6.8 policy-card source, test, and report artifacts identified for final staging
  - Bare-python CLI subprocess tests replaced with shared `tests/cli_helpers.py` helper using active interpreter and `PYTHONPATH=src:.`
  - Ruff, mypy, full pytest, and coverage validation pass locally
  - Accidental root pager/help artifact removed; `.composer/` left as unrelated local tool state
  - Deferred structural debt recorded for identity CLI splitting, shared policy-card base, mypy tightening, security scan gates, and slow-test marker hardening

## What works

- Full governed command pipeline: policy → HITL → budget → sandbox → verify → trace → memory
- ...
- P1.4.14 Operator Consent Binding: delta-bound consent with attestation binding, risk acknowledgement, 55 tests
- P1.4.15 Identity Governance Command Surface: unified CLI, `identity status`/`verify`, JSON envelope, 53 tests
- Plan validation halts on empty/invalid/unsupported plans
- Persistent and in-memory trace ledgers with hash-chain verification
- P1.5.10X canonical AurelTraceLog contracts:
  - `src/agentic_runtime/contracts/trace.py` defines append-only `AurelTraceLog`, immutable `TraceEvent`, `TraceEventRef`, `TraceBindingRef`, `TraceIntegrityReport`, stable canonical JSON hashing, and chain verification
  - `src/agentic_runtime/contracts/projections.py` defines projection records that cannot claim canonical status
  - AurelTraceLog is the only source of truth; Ledger/Evidence/Runtime/Evaluation/Mneme/Shell/Reports are projections
  - Future serious evidence/evaluation/memory/output records must bind back to canonical `TraceEventRef`
- P1.5.11A Golden Thread A:
  - `src/agentic_runtime/golden_threads/thread_a.py` runs deterministic Intent → Context → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → CapabilityEvidence path
  - `src/agentic_runtime/contracts/evidence.py` defines trace-bound `EvidenceRef`
  - `src/agentic_runtime/contracts/verifier.py` defines `VerifierResult` with pass/evidence/limitations invariants
  - `src/agentic_runtime/contracts/capability.py` defines verified capability evidence factory and validation
  - Verified capability evidence cannot exist without canonical trace, evidence, verifier pass, verifier limitations, and capability limitations
- P1.5.11B Capability Evidence ↔ Trace / Context Binding:
  - `src/agentic_runtime/contracts/context.py` defines `ContextBindingRef`, `ContextAdequacyStatus`, and `ContextAdequacyReport`
  - `CapabilityEvidenceRecord` now stores `source_event_hash`, context refs, context adequacy ref, and evidence strength
  - Golden Thread A now includes ContextBindingRef and ContextAdequacyReport
  - Verified capability evidence requires trace, source hash, evidence, verifier pass, limitations, evidence strength `strong|verified`, and safe/adequate context
  - Unsafe/insufficient context, weak evidence, projection-only sources, and trace-hash mismatch block verification
- P1.5.12 Evaluation Case Extraction Seed:
  - `src/agentic_runtime/contracts/evaluation_cases.py` defines `FailureMode`, `EvaluationCase`, `RegressionCandidate`, `EvaluationCaseExtractionReport`
  - `src/agentic_runtime/evaluation/extraction.py` implements extraction from `CapabilityEvidenceRecord` → `EvaluationCase`/`RegressionCandidate`
  - Golden Thread A now produces a candidate `EvaluationCase`; `GoldenThreadAResult` extended with extraction fields
  - Extraction routing: review > regression > positive
  - All extracted records are candidate/needs_review by default — nothing is auto-accepted
  - Impossible states (positive case without trace, without evidence, with mismatched hash, with accepted status, etc.) are blocked by invariant validation
  - 46 tests across extraction, golden thread integration, serialization, failure mode mapping, and candidate-only guards
- Runtime state machine with structured `ExecutionOutcome`
- Budget enforcement with traced decisions
- Memory write governance with provenance and promotion gates
- Tool input/output contract enforcement (P0.10)
- End-to-end demo: fix calc bug, authority denial, HITL denial, test integrity, skill maturation
- Minimal CLI: `python -m agentic_runtime.cli {status,demo,verify}`
- P0.12 model provider layer:
  - deterministic mock provider by default
  - optional OpenAI / Anthropic / Ollama adapters
  - structured plan schema validation before `PlanValidator`
- P0.13 Tool Bus v1:
  - structured tool registry/spec/metadata/result/error concepts
  - builtin read/search/git-read/write/patch/execution tools
  - contract-bound input validation before handler execution
  - structured tool errors instead of uncaught exceptions
- P0.14 Repository Agent Loop:
  - bounded repository context builder
  - deterministic plan-first coding loop
  - patch/test execution through `AgenticRuntime.submit()` and Tool Bus tools
  - structured `CodeTaskReport` with bounded repair attempts
- P0.15 HITL / Approval Upgrade:
  - structured approval requests, decisions, receipts
  - risk classes R0–R5 with preview/confirmation rules
  - runtime trace receipts for approval outcomes
  - repo-agent dry-run approval summaries and CLI approval modes
- P0.16 Praxis Memory Seed:
  - `PraxisExperience` capture from runtime/repo/approval/test/verifier sources
  - governed memory/procedure/skill **candidates** (not verified truth)
  - conservative promotion gates and reflex eligibility checks
  - repo-agent `PraxisReport` and trace `PraxisEventRecord` events
  - CLI: `praxis-demo`, `memory-candidates`, `praxis-report`
- P0.17 Sandbox Hardening:
  - sandbox profiles (`no_exec_readonly`, `restricted_local`, `unsafe_local_demo`, docker, bubblewrap)
  - `SandboxPolicy` + `ProfiledSandbox` path/exec enforcement
  - structured `SandboxViolation` + trace records
  - runtime status diagnostics and repo-agent profile selection
  - CLI: `sandbox-status`, repo-task `--sandbox`
- P0.17.1 Pre-P0.20 Readiness Patch:
  - missing-file safety in repo context builder
  - `TestRunnerAdapter` uses `run_tests` for list commands
  - `AutoApprover` predicate cannot widen risk envelope
  - explicit repo auto-approval R0–R3 only
- P0.19 P0.20 Demo Harness:
  - `DemoScenario` / `DemoRepoFactory` / `DemoHarness` contracts
  - `buggy_calculator` controlled scenario (initial fail → patch → test)
  - plan-first verification, approval/sandbox/praxis/trace summaries
  - honest failure when initial tests pass unexpectedly or final tests fail
  - CLI: `demo-harness buggy_calculator`
- P0.20 First Real Coding Agent Demo (**PASS**):
  - governed loop proven end-to-end: objective → context → plan → approval preview
    → governed patch → tests → trace → sandbox summary → praxis report → evidence
  - `write_evidence` / `build_sandbox_summary` evidence adapters
  - CLI: `demo-harness ... --evidence-dir`
  - evidence artifacts under `agent/evidence/p0.20/`
  - seal tests `tests/test_p020_demo_seal.py`
- P0.21 LLM Planning Bridge for Repository Agent (**PASS**):
  - planner modes: `deterministic`, `llm`, `hybrid`, `dry_run`
  - `LLMRepoPlanner` calls ModelRouter/provider structured output for plans only
  - strict repository plan schema + `RepoPlanValidator` fail closed
  - hybrid fallback records fallback reason without bypassing governance
  - new `missing_validation` demo scenario and mock LLM planner coverage
  - CLI: `repo-task --planner ... --provider ...`, `demo-harness ... --planner ... --provider ...`
- P1.0 Runtime Alpha Seal (**PRE-SEAL** — P1.0.1 integrity patch 2026-06-17):
  - GitHub Actions CI configured: compileall, ruff, mypy, pytest+coverage (≥75%), alpha-seal
  - `python -m agentic_runtime.cli alpha-seal` readiness checks (local PASS on Python 3.12.3)
  - `--apply` auto-selects hard sandbox: bubblewrap → docker → restricted_local
  - timeout subprocess tests skip in restricted CI sandboxes (`requires_subprocess`)
  - deployment guide: `docs/DEPLOYMENT.md`
  - dev tooling: pytest-cov, ruff, mypy
  - release docs: `agent/releases/P1.0_*.md`
  - P1.0 evidence: `agent/evidence/p1.0/`
  - seal report: `agent/reports/P1.0_RUNTIME_ALPHA_SEAL_REPORT.md`
  - **PASS** pending: baseline commit + CI green on Python 3.11/3.12
- P1.1 Model Configuration + Secret Boundary (**PASS**):
  - centralized config: `agent/config/{providers,models,runtime}.yaml`
  - `model_config.py`, `secrets.py`, `yaml_minimal.py`
  - `ModelRouter` accepts `ModelConfigBundle`, profile/task selection, `local_only` enforcement
  - secrets from env only; `SecretRedactor` on errors/status; raw API keys rejected in YAML
  - CLI: `config validate`, `models list`, `providers status`
  - tests: `tests/test_model_config_p11.py` (21 tests)
- P1.2.1 Public Entry + Runtime Verification Patch (**PASS**):
  - `demo.py` crash fixed: safe no-skill outcome when evidence gates not satisfied, exits 0
  - sandbox CPU/timeout mismatch fixed: `materialize_sandbox_backend` passes `cpu_seconds` from profile
  - `model_router.py` ruff/mypy noise cleaned: `ModelResponse` module import, `rows` rename, 3 unused ignores removed
  - `tests/test_public_entrypoints_p121.py` added (8 smoke tests)
  - README quick-start updated to accurately describe demo outcome
  - `slow` marker registered in `pyproject.toml`
- P1.2 Prompt System Seed (**PASS**):
  - top-level prompt assets under `prompts/system/` and `prompts/packs/`
  - `prompt_system.py` with `PromptRegistry`, metadata/policy validation, simple template rendering, and trace-safe `PromptTraceSummary`
  - prompt manifests declare owner, version, allowed model profiles, task tags, schemas, forbidden requests, evals, policy, and template
  - P1.1 model profile validation is optional and enabled by prompt CLI default validation
  - raw prompt text is not stored by default; CLI render emits hashes and metadata only
  - `SecretRedactor` applied to prompt summaries and CLI output; raw secret-like prompt material is rejected
  - CLI: `prompts validate`, `prompts list`, `prompts show`, `prompts render`
  - tests: `tests/test_prompt_system_p12.py` (26 tests)
- P1.3 Tool / Plugin Manifest Seed (**SEALED** via P1.3.9):
  - declarative manifest layer under `src/agentic_runtime/tool_manifest/`
  - lifecycle: load → validate → quarantine → register → invocation draft → lifecycle event
  - built-in seed manifests (7 tools across 6 JSON files)
  - research-inspired metadata (AWM/JEPA/LaMo/simulation/learning readiness fields)
  - **not** wired to Tool Bus, `CommandEnvelope`, or `runtime.submit`
  - tests: `tests/test_tool_manifest_p130.py` … `tests/test_builtin_tool_manifests_p138.py`, `tests/test_p13_tool_manifest_layer_seal.py` (58 seal tests)
- P1.3.9 Tool Manifest Layer Seal (**SEALED** — 2026-06-21):
  - end-to-end lifecycle seal without execution
  - declarative-vs-executable boundary tests (manifest `ToolRegistry` ≠ `tools.py` `ToolRegistry`)
  - governance hotfix confirmation (prompt risk_tier, YAML, restricted_local honesty, run_shell R4)
  - report: `agent/reports/P1.3_TOOL_PLUGIN_MANIFEST_REPORT.md`
- P1.4.0 Identity + Autonomy Scope Contract (**PASS**):
  - constitutional docs under `docs/P1.4_*.md`
  - stub packages: `identity/`, `autonomy/`, `governance/`, `heretic/`, `metacognition/`, `compliance/` (placeholders only)
  - static scope constants: `identity/p14_scope.py`
  - **not** Identity Kernel, Autonomy Scale, Measured Autonomy Score, or Heretic Sandbox runtime
  - tests: `tests/test_p14_scope_contract_docs.py`
  - report: `agent/reports/P1.4.0_IDENTITY_AUTONOMY_SCOPE_CONTRACT_REPORT.md`
- P1.4.1 Identity Kernel v2.0 (**PASS**):
  - `config/aurel/identity_kernel.yaml` with IK-001–IK-008 invariant registry
  - loader, validator, SHA-256 hash, attestation builder
  - CLI: `identity kernel {show,validate,hash,attest}`
  - **not** Persona Manifest, Operator Contract, Autonomy Scale, or Identity Card
  - tests: `tests/test_identity_kernel*.py` (27 tests)
  - report: `agent/reports/P1.4.1_IDENTITY_KERNEL_REPORT.md`
- P1.4.2 Persona Manifest v2.0 (**PASS**):
  - `config/aurel/persona_manifest.yaml` expression contract with PM-001–PM-007 invariants
  - loader, validator, SHA-256 hash, attestation, deterministic safe summary
  - CLI: `identity persona {show,validate,hash,attest,summary}`
  - **not** Operator Contract, Communication Modes, Prompt Context Compiler, or Autonomy
  - tests: `tests/test_persona_manifest*.py` (36 tests)
  - report: `agent/reports/P1.4.2_PERSONA_MANIFEST_REPORT.md`
- P1.4.3 Operator Relationship Contract v2.0 (**PASS**):
  - `config/aurel/operator_contract.yaml` — principal/delegate authority, ORC-001–ORC-008 invariants
  - loader, validator, SHA-256 hash, authority anchor, prompt-safe summary
  - CLI: `identity operator {show,validate,hash,attest,summary}`
  - tests: `tests/test_operator_contract*.py` (57 tests)
  - report: `agent/reports/P1.4.3_OPERATOR_RELATIONSHIP_CONTRACT_REPORT.md`
- P1.4.4 Communication Modes v2.0 (**PASS**):
  - `config/aurel/communication_modes.yaml` — cognitive/output mode registry, CM-001–CM-008 invariants
  - loader, validator, SHA-256 hash, case-insensitive lookup, per-mode safe summaries
  - CLI: `identity modes {show,validate,hash,attest,summary}`
  - tests: `tests/test_communication_modes*.py` (34 tests)
  - report: `agent/reports/P1.4.4_COMMUNICATION_MODES_REPORT.md`
- P1.4.5 Identity Prompt Context Compiler v2.0 (**PASS**):
  - `config/aurel/identity_prompt_compiler.yaml` — compile identity sources into prompt context
  - dominance rules, contradiction detection, deterministic SHA-256 context hash
  - CLI: `identity context {show,validate,hash,compile,render}`
  - tests: `tests/test_identity_prompt_context*.py` (55 tests)
  - report: `agent/reports/P1.4.5_IDENTITY_PROMPT_CONTEXT_COMPILER_REPORT.md`
- P1.4.6 Self-Model v2.0 (**PASS**):
  - `config/aurel/self_model_policy.yaml` — honest runtime self-description
  - identity summary, authority boundaries, capability-honest inventory, known limitations
  - CLI: `identity self {show,validate,hash,build}`
  - tests: `tests/test_self_model*.py` (48 tests)
  - report: `agent/reports/P1.4.6_SELF_MODEL_REPORT.md`
- P1.4.18 Trust Evidence Linkage (**COMPLETE** ✓):
  - `src/agentic_runtime/identity/trust_evidence.py` — trust evidence linkage layer operational
  - `TrustEvidenceKind`, `TrustEvidenceStatus`, `TrustPosture`, `TrustEvidenceRef`, `TrustEvidenceRequirement`, `TrustEvidenceLink`, `TrustEvidenceBundle`, `TrustEvidenceLinkageReport`
  - categorical trust posture resolution working (no fake numeric trust score)
  - engine: `default_trust_evidence_requirements_for_lifecycle()`, `build_trust_evidence_bundle()`, `validate_trust_evidence_bundle()`, `resolve_trust_posture()`
  - 5 helper builders: `evidence_ref_from_source_attestation`, `from_test_battery_report`, `from_consent_record`, `from_authority_delta_report`, `from_lifecycle_decision`
  - CLI: `identity trust-evidence {requirements,build,validate,explain}`
  - tests: 57 new (34 core + 23 seal/CLI), 355 identity total
  - reports: `agent/reports/P1.4.18_TRUST_EVIDENCE_LINKAGE.md`
- P1.4.19 Identity Docs / Reports / State Update (**COMPLETE** ✓):
  - consolidation/audit gate before P1.4.20 exit seal; no new governance semantics
  - `src/agentic_runtime/identity/p14_seal_readiness.py` — read-only seal readiness helper
  - data models: `P14ModuleStatus`, `P14SealReadinessReport`
  - pre-built constants: `P14_CLI_GROUPS` (18 entries), `P14_INVARIANTS` (15), `P1419_INVARIANTS` (10), `P14_KNOWN_LIMITATIONS` (15), `P1420_SEAL_CHECKLIST` (22)
  - CLI: `identity seal-readiness --json`
  - tests: 29 new anti-overclaim + seal-readiness tests (`test_p1419_anti_overclaim.py`), 384 identity total
  - report: `agent/reports/P1.4.19_IDENTITY_DOCS_REPORTS_STATE_UPDATE.md`
  - P1.4.18 verified complete before implementation
  - **Current active module: P1.4.20**
  - **Next module: P1.5.0 — Evaluation Mirror Foundation**
- P1.4.20 P1.4 Identity & Autonomy Exit Seal (**COMPLETE** ✓, SEALED_WITH_LIMITATIONS):
  - `src/agentic_runtime/identity/p14_exit_seal.py` — final P1.4 boundary seal, validates, does not add governance
  - 56 seal checks across 5 categories: import/object, CLI, governance invariants, adversarial, docs consistency
  - CLI: `identity p14-seal run/list-checks/run-check --json` — read-only, no mutation, no authority grant, no consent grant
  - Tests: 28 new (`test_p14_exit_seal.py`), 412 identity total
  - Seal result: **SEALED_WITH_LIMITATIONS** — honest; P1.5/P1.6/P1.8/P6/P7 not yet implemented
  - 15 known limitations carried forward from P1.4.19
  - Report: `agent/reports/P1.4.20_P14_IDENTITY_AUTONOMY_EXIT_SEAL.md`
  - P1.4.19 verified complete before implementation
  - **P1.4 is sealed. P1.5.0 Evaluation Mirror Foundation Gate is next.**
- P1.5.0 Evaluation Mirror Foundation Gate + Roadmap v3.2 Alignment (**COMPLETE**):
  - **Current phase:** P1.5 — Evaluation Mirror & Verified Capability Evidence Foundation
  - **Macro roadmap version:** Aurel Roadmap v3.2 (based on v3.1 macro update — refined, not reset)
  - `src/agentic_runtime/evaluation/evaluation_foundation.py` — minimal evaluation foundation
  - data models: `EvaluationDomain`, `EvaluationSubjectType`, `EvaluationSubject`, `EvaluationScope`, `EvaluationCriterion`, `EvaluationRunEnvelope`, `EvaluationFoundationReport`
  - engine: `default_evaluation_scope_for_domain()`, `build_evaluation_subject()`, `build_evaluation_run_envelope()`, `validate_evaluation_run_envelope()`, `build_p150_foundation_report()`
  - CLI: `evaluation foundation status/scope --json` — read-only, does not verify capability
  - Core law: No capability claim may become VERIFIED without evaluation evidence
  - P1.5.0 is foundation gate, **not** full P4 Evaluation Mirror
  - Roadmap v3.2 alignment: Aurel Core vs Hub tools, HQ/A-Hub/S-Hub/L-Hub/IDE taxonomy, memory boundaries, open-weight model doctrine
  - **Execution discipline:** Do not jump to P22–P24. Finish P1.5–P1.9, then lock P2.0, then continue P3+.
  - P1.4.20 verified complete (SEALED_WITH_LIMITATIONS) before implementation
  - Historical P1.5.0 pointer superseded; later P1.5 modules advanced through P1.5.19 and current work is P1.6.8S.
- P1.5.10 Baseline Comparison Model + Sparse Comparison Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/baseline_comparison.py` — baseline comparison model
  - enums: `BaselineReferenceKind`, `BaselineStatus`, `ComparisonDimension`, `ComparisonSignal`, `ComparisonConfidence`
  - dataclasses: `BaselineReference`, `BaselineComparisonInput`, `BaselineComparisonDecision`, `BaselineComparisonPolicy`, `BaselineComparisonReport`
  - engine: `validate_baseline_reference()`, `validate_baseline_comparison_input()`, `compare_evaluation_results()`, `compare_adversarial_coverage()`, `compare_hygiene_refs()`, `resolve_baseline_comparison_decision()`, `build_p1510_baseline_comparison_report()`
  - CLI: `evaluation baseline status/examples --json` — read-only, does not run evaluations or verify capability
  - Core law: baseline comparison may detect improvement or degradation; comparison is not verification
  - Sparse comparison readiness: 8 sparse dimensions supported categorically; Sparse Context Compiler NOT implemented
  - 13 invariants (`P1510_INVARIANTS`) including 3 sparse-specific
  - P1.5.9 verified complete before implementation
- P1.5.10X Single Source of Truth + TraceLog Integrity Patch (**COMPLETE**):
  - `src/agentic_runtime/contracts/trace.py` — canonical trace contracts and append-only in-memory `AurelTraceLog`
  - `TraceEvent` includes hash-chain fields, payload hash, event hash, refs, policy/context/verifier refs, severity and status
  - `TraceEventRef`, `TraceBindingRef`, and `TraceIntegrityReport` provide future evidence/evaluation/memory/output binding and replay integrity primitives
  - `src/agentic_runtime/contracts/projections.py` — projection contract layer for ledger, runtime, evaluation, memory, shell, report and evidence projections
  - Core law: AurelTraceLog is the only source of truth; Ledger/Evidence/Runtime/Evaluation/Mneme/Shell/Reports are projections
  - No full AurelFlow, AurelExec, tool execution, shell execution, LLM execution, full Ledger rewrite, or full Mneme lifecycle introduced
  - ADR: `docs/adr/ADR-004-aurel-tracelog-source-of-truth.md`
  - Report: `docs/roadmap/P1.5.10X_TRACELOG_INTEGRITY_PATCH.md`
  - Next module: P1.5.11A — Golden Thread A Minimal Contract Harness
- P1.5.11A Golden Thread A Minimal Contract Harness (**COMPLETE**):
  - `src/agentic_runtime/golden_threads/thread_a.py` — deterministic vertical contract harness
  - stubs: `OperatorIntentStub`, `AurelContextStub`, `PolicyDecisionStub`, `LeaseStub`, `StubExecutionResult`
  - result: `GoldenThreadAResult`
  - contracts: `EvidenceRef`, `VerifierResult`, P1.5.11A `CapabilityEvidenceRecord`
  - canonical event: `TraceEventType.STUB_EXECUTION_COMPLETED` appended to `AurelTraceLog`
  - Golden Thread A path: Intent → Context → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → CapabilityEvidence
  - Core law: verified capability evidence requires canonical `TraceEventRef`, at least one `EvidenceRef`, linked `VerifierResult`, verifier status `pass`, non-empty verifier limitations, and non-empty capability limitations
  - No full AurelFlow, AurelExec, real tool/model/shell execution, full Ledger migration, or full Mneme lifecycle introduced
  - Report: `docs/roadmap/P1.5.11A_GOLDEN_THREAD_A_MINIMAL_CONTRACT_HARNESS.md`
  - Next module: P1.5.11B — Capability Evidence ↔ Trace / Context Binding
- P1.5.11B Capability Evidence ↔ Trace / Context Binding (**COMPLETE**):
  - `src/agentic_runtime/contracts/context.py` — context binding and adequacy contracts
  - `src/agentic_runtime/contracts/capability.py` — capability evidence v2 with source event hash, context binding, context adequacy ref, and evidence strength
  - `src/agentic_runtime/golden_threads/thread_a.py` — updated Golden Thread A path: Intent → ContextBindingRef → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → ContextAdequacyReport → CapabilityEvidenceRecord v2
  - Core law: verified capability evidence requires canonical trace, matching source_event_hash, EvidenceRef, VerifierResult pass, verifier limitations, capability limitations, evidence strength `strong|verified`, and no unsafe/insufficient context
  - Partial context requires explicit context limitation
  - Projection-only source cannot verify capability evidence
  - No full AurelBrain, AurelContextPacket, AurelFlow, AurelExec, tool/model/shell execution, full Ledger migration, full Mneme lifecycle, CapabilityClaimRegistry, or EvaluationCase extraction introduced
  - Report: `docs/roadmap/P1.5.11B_CAPABILITY_EVIDENCE_TRACE_CONTEXT_BINDING.md`
  - Historical next module was P1.5.12; current work is P1.6.8S and next planned feature is P1.6.9.
- P1.5.9 Adversarial Evaluation Cases + Sparse Trap Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/adversarial_cases.py` — adversarial case definitions and registry
  - enums: `AdversarialCaseType`, `AdversarialCaseStatus`, `AdversarialCaseSeverity`, `AdversarialAttackSurface`, `AdversarialExpectedOutcome`
  - dataclasses: `AdversarialEvaluationCase`, `AdversarialCaseRegistry`, `AdversarialCaseValidation`, `AdversarialCaseReport`
  - engine: `validate_adversarial_case()`, `register_adversarial_case()`, `validate_adversarial_case_registry()`, `resolve_adversarial_cases_for_subject()`, `list_adversarial_cases()`, `build_default_adversarial_case_set()`, `build_p159_adversarial_case_report()`
  - CLI: `evaluation adversarial status/examples --json` — read-only, does not execute cases or verify capability
  - Core law: Aurel cannot trust only positive/pass cases; adversarial cases are first-class evaluation fixtures
  - Sparse trap readiness: omission, lost-context, multi-hop, contradiction survival, needle-in-context, context budget pressure traps represented; Sparse Context Compiler NOT implemented
  - 17 invariants (`P159_INVARIANTS`) including 6 sparse-specific
  - P1.5.8 verified complete before implementation
- P1.5.8 Benchmark Hygiene Guard + Sparse Hygiene Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/benchmark_hygiene.py` — benchmark/context hygiene guard
  - enums: `BenchmarkHygieneStatus`, `BenchmarkHygieneRisk`, `BenchmarkContaminationType`, `BenchmarkFreshnessStatus`, `BenchmarkRepresentativeness`
  - dataclasses: `BenchmarkFixtureBoundary`, `BenchmarkHygieneAssessment`, `BenchmarkHygienePolicy`, `BenchmarkHygieneDecision`, `BenchmarkHygieneReport`
  - engine: `validate_benchmark_fixture_boundary()`, `classify_contamination_risk()`, `classify_freshness_status()`, `assess_benchmark_hygiene()`, `resolve_hygiene_decision()`, `apply_hygiene_to_evidence_binding()`
  - CLI: `evaluation hygiene status/examples --json` — read-only, does not run benchmarks or verify capability
  - Core law: benchmark-derived evidence cannot strongly support a claim unless hygiene is acceptable
  - Sparse hygiene readiness: context leakage, retrieval leakage, lost-context risk, contradiction omission, and multi-hop edge missing represented as hygiene risks; Sparse Context Compiler NOT implemented
  - 17 invariants (`P158_INVARIANTS`) including 6 sparse-specific
  - P1.5.7 verified complete before implementation
- P1.5.7 Evidence-to-Claim Binding + Sparse Binding Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evidence_claim_binding.py` — evidence-to-claim binding layer
  - enums: `ClaimBindingRelationship` (8 types), `ClaimBindingStatus` (9 statuses), `ClaimSupportLevel` (5 levels), `ClaimConflictLevel` (6 levels)
  - dataclasses: `EvidenceClaimBinding`, `EvidenceClaimBindingPolicy`, `EvidenceClaimBindingDecision`, `EvidenceClaimBindingReport`
  - engine: `bind_evidence_to_claim()`, `validate_evidence_claim_binding()`, `aggregate_evidence_claim_bindings()`, `build_p157_evidence_claim_binding_report()`
  - CLI: `evaluation binding status/examples --json` — read-only, does not verify capability
  - Core law: Evidence can affect a claim, does not automatically verify it; no VERIFIED status
  - Sparse binding readiness: sparse-context evidence binds to sparse-related claims; Sparse Context Compiler NOT implemented
  - 13 invariants (`P157_INVARIANTS`) including 3 sparse-specific
  - P1.5.6 verified complete before implementation
- P1.5.6 Result Classification Engine + Sparse Classification Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/result_classification.py` — result classification engine
  - enums: `EvaluationObservationType` (18 types), `EvaluationObservationStatus` (7 statuses)
  - dataclasses: `EvaluationObservation`, `CriterionClassificationInput`, `CriterionClassificationDecision`, `ResultClassificationInput`, `ResultClassificationDecision`, `ResultClassificationPolicy`, `ResultClassificationReport`
  - engine: `validate_evaluation_observation()`, `classify_criterion_observation()`, `criterion_decision_to_result()`, `classify_result_from_criterion_decisions()`, `result_classification_to_evaluation_result()`, `classify_result_from_observations()`, `build_p156_result_classification_report()`
  - CLI: `evaluation classify status/examples --json` — read-only, does not execute evaluation
  - Core law: Classification is not verification; classification does not execute evaluation, call LLMs/tools, verify capability, or bind evidence to claims
  - Sparse classification readiness: 7 sparse observation types classifiable; Sparse Context Compiler NOT implemented
  - Conversion to P1.5.1 EvaluationCriterionResult and EvaluationResult objects
  - 17 invariants (`P156_INVARIANTS`)
  - P1.5.5 verified complete before implementation
- P1.5.5 Evaluation Run Envelope + Sparse Run Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evaluation_run_envelope.py` — governed run envelope layer
  - enums: `EvaluationRunStatus`, `EvaluationRunIntent`, `EvaluationRunMode`, `EvaluationEvaluatorType`
  - dataclasses: `EvaluationRunEvidenceRequirement`, `GovernedEvaluationRunEnvelope`, `EvaluationRunEnvelopeValidation`, `EvaluationRunEnvelopeReport`
  - engine: `build_governed_evaluation_run_envelope()`, `validate_governed_evaluation_run_envelope()`, `resolve_run_readiness()`, `build_evidence_requirements_from_criteria()`, `build_p155_run_envelope_report()`
  - CLI: `evaluation runs status/examples --json` — read-only, does not execute evaluation
  - Core law: No governed evaluation execution without a valid run envelope; envelopes do not run evaluation
  - Sparse run metadata: 5 boolean fields derived from criteria; ASCL not implemented
  - 13 invariants (`P155_INVARIANTS`)
  - P1.5.4 verified complete before implementation
- P1.5.4 Evaluation Criteria Schema + Sparse Criteria Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evaluation_criteria_schema.py` — reusable criteria schema layer
  - enums: `EvaluationCriterionKind`, `EvaluationCriterionSeverity`, `EvaluationCriterionRequirementLevel`, `EvaluationCriterionEvidenceRequirement`
  - dataclasses: `EvaluationCriterionApplicability`, `EvaluationCriteriaSchemaItem`, `EvaluationCriteriaSchema`, `EvaluationCriteriaSchemaRegistry`, `EvaluationCriteriaSchemaResolution`, `EvaluationCriteriaSchemaReport`
  - engine: `validate_criteria_schema_item()`, `resolve_criteria_for_subject()`, `list_criteria_schemas()`, `build_default_criteria_schema_for_subject_type()`, `build_default_sparse_criteria_schema()`, `build_p154_criteria_schema_report()`
  - CLI: `evaluation criteria status/examples --json` — read-only, does not run evaluation
  - Core law: No criteria schema, no governed evaluation run; criteria do not verify capability
  - Sparse criteria: 8 sparse criterion kinds, 6-criteria default sparse schema; Sparse Context Compiler NOT implemented
  - 15 invariants (`P154_INVARIANTS`)
  - P1.5.3 verified complete before implementation
- P1.5.3 Evaluation Subject Registry + Sparse Cognition Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evaluation_subject_registry.py` — governed subject registry
  - enums: `EvaluationSubjectStatus`, `EvaluationSubjectOrigin`, `EvaluationSubjectCategory`
  - dataclasses: `EvaluationSubjectRegistryEntry`, `EvaluationSubjectRegistrationRequest`, `EvaluationSubjectRegistrationDecision`, `EvaluationSubjectRegistry`, `EvaluationSubjectRegistryReport`
  - engine: `register_evaluation_subject()`, `resolve_evaluation_subject()`, `list_evaluation_subjects()`, `validate_evaluation_subject_registry()`, `build_p153_subject_registry_report()`
  - CLI: `evaluation subjects status/examples --json` — read-only, does not run evaluation
  - Core law: No registered subject, no governed evaluation; registration is not verification
  - Sparse Cognition readiness: 9 future ASCL categories registerable; Sparse Context Compiler NOT implemented
  - Hub origins: A_HUB/S_HUB/L_HUB/IDE registrable as future-ready references; Hub runtimes NOT implemented
  - 16 invariants (`P153_INVARIANTS`)
  - P1.5.2 verified complete before implementation
- P1.5.2 Capability Evidence Record (**COMPLETE**):
  - `src/agentic_runtime/evaluation/capability_evidence.py` — evidence bridge layer
  - enums: `CapabilityEvidenceKind`, `CapabilityEvidenceStatus`, `CapabilityEvidenceStrength`
  - dataclasses: `CapabilityEvidenceRecord`, `CapabilityEvidenceRequirement`, `CapabilityEvidenceLink`, `CapabilityEvidenceRecordSet`, `CapabilityEvidenceRecordReport`
  - engine: `capability_evidence_from_evaluation_result()`, `capability_evidence_from_result_set()`, `validate_capability_evidence_record()`, `aggregate_capability_evidence_records()`, `build_capability_evidence_link()`, `build_p152_capability_evidence_report()`
  - CLI: `evaluation capability-evidence status/examples --json` — read-only, does not verify capability
  - Core law: USABLE is not VERIFIED; evidence records support future claim binding (P1.5.7)
  - 11 invariants (`P152_INVARIANTS`)
  - P1.5.1 verified complete before implementation
- P1.5.1 Evaluation Object Model (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evaluation_objects.py` — stable evaluation result language
  - enums: `EvaluationResultStatus`, `EvaluationOutcome`, `EvaluationVerdict`, `EvaluationConfidenceClass`, `EvaluationEvidenceQuality`, `EvaluationFailureMode`
  - dataclasses: `EvaluationCriterionResult`, `EvaluationResult`, `EvaluationResultSet`, `EvaluationObjectModelReport`
  - engine: `validate_evaluation_criterion_result()`, `validate_evaluation_result()`, `resolve_evaluation_result_from_criteria()`, `aggregate_evaluation_results()`, `build_p151_object_model_report()`
  - CLI: `evaluation objects status/examples --json` — read-only, does not verify capability
  - Core law: PASS does not mean VERIFIED; no numeric capability score
  - 11 invariants (`P151_INVARIANTS`)
  - P1.5.0 verified complete before implementation

## Known limitations

- Default sandbox is `UnsafeLocalSandbox` — **not** a production security boundary
- Real providers are optional and unverified without API keys/local services
- Single-entity demo; no multi-agent orchestration
- HITL uses `AutoApprover` in demo (bounded predicate, defaults deny)
- Tool Bus does not make authority decisions; Runtime policy remains mandatory
- No network, delete, git commit, or git push tools are implemented
- Prompt manifests are governance metadata and language templates only; prompts do not grant tool authority
- Two `ToolRegistry` types exist: manifest catalog (`tool_manifest/registry.py`) vs executable Tool Bus registry (`tools.py`) — not merged in P1.3
- Tool manifest invocation drafts do not become `CommandEnvelope`; future bridge planned at P6 Governed Tool Bus Expansion
- P1.4.1–P1.4.19 identity trust surface is implemented (kernel through seal readiness) but **not wired into `AgenticRuntime.submit()`** — delta detection, consent binding, trust posture, and seal readiness are CLI/report signals only until a later patch explicitly adds runtime enforcement
- P1.4.0 placeholder packages (`autonomy/`, `governance/`, `heretic/`, `metacognition/`, `compliance/`) remain stubs; substantive logic lives under `identity/` for delivered patches
- Repository agent patch synthesis remains intentionally small/deterministic; LLM planning proposes structured plans only and is not a general autonomous coding agent
- Repository-agent context building reads bounded local files directly, while
  mutations and test execution go through Runtime/Tool Bus governance
- One pytest (`test_timeout_kills_long_running_command`) may fail in restricted CI sandboxes when nested `python3` subprocesses are blocked; passes in normal environments — **P1.0:** both timeout tests skip automatically via `requires_subprocess` when subprocess spawn is blocked
- CLI `demo-harness --apply` with auto bubblewrap may report harness `failed` while independent `final_test` passes; use `--sandbox restricted_local` for scenario-default smoke or see P1.0 seal report

## P1.4.19 Known Limitations Index

P1.4.19 catalogued 15 known limitations (`P14_KNOWN_LIMITATIONS`) for P1.4.20 exit seal verification:

1. Identity trust surface (kernel through seal readiness) not wired into `AgenticRuntime.submit()`
2. P1.4.0 placeholder packages (`autonomy/`, `governance/`, `heretic/`, `metacognition/`, `compliance/`) remain stubs
3. Authority delta detection / consent binding are CLI/report signals only
4. Trust evidence linkage is classification-only, not runtime enforcement
5. P1.4 seal-readiness is read-only; no authority, permission, or tool changes
6. No cryptographic signatures on attestations (SHA-256 only)
7. No tamper-proof storage for identity sources or attestations
8. Capability claims are evidence-gated but not runtime-enforced
9. Autonomy scale engine is action-scoped only, not wired to runtime
10. Measured autonomy score is measurement-only, not an execution gate
11. Lifecycle state machine is eligibility-only, not permission enforcement
12. Identity test battery is verification-only, not continuous monitoring
13. External doctrine assimilation is roadmap influence only, not implementation
14. Two `ToolRegistry` types remain separate (manifest catalog vs execution registry)
15. Default sandbox is `UnsafeLocalSandbox` — not a production security boundary

## How to run

```bash
# from repo root, with dev deps installed
pip install -e ".[dev]"

python -m agentic_runtime.cli status
python -m agentic_runtime.cli demo
python -m agentic_runtime.cli verify
python -m agentic_runtime.cli repo-task "replace 'old' with 'new' in src/file.py"
python -m agentic_runtime.cli repo-task "replace 'old' with 'new' in src/file.py" --apply
python -m agentic_runtime.cli approve-demo --mode deny
python -m agentic_runtime.cli repo-task "objective" --dry-run --approval-mode deny
python -m agentic_runtime.cli praxis-demo
python -m agentic_runtime.cli memory-candidates
python -m agentic_runtime.cli praxis-report
python -m agentic_runtime.cli sandbox-status
python -m agentic_runtime.cli sandbox-status --profile restricted_local --json
python -m agentic_runtime.cli repo-task "objective" --sandbox restricted_local
python -m agentic_runtime.cli repo-task "objective" --dry-run --sandbox no_exec_readonly
python -m agentic_runtime.cli demo-harness buggy_calculator
python -m agentic_runtime.cli demo-harness buggy_calculator --apply
python -m agentic_runtime.cli demo-harness buggy_calculator --apply --evidence-dir agent/evidence/p0.20
python -m agentic_runtime.cli demo-harness missing_validation --planner hybrid --provider mock --apply
python -m agentic_runtime.cli demo-harness list
python -m agentic_runtime.cli alpha-seal
python -m agentic_runtime.cli config validate
python -m agentic_runtime.cli models list
python -m agentic_runtime.cli providers status
python -m agentic_runtime.cli prompts validate
python -m agentic_runtime.cli prompts list
python -m agentic_runtime.cli prompts show repo_planner
python -m agentic_runtime.cli prompts render repo_planner --var objective="test" --dry-run
python -m agentic_runtime.cli identity trust-evidence requirements --lifecycle-state ACTIVE --json
python -m agentic_runtime.cli identity trust-evidence build --lifecycle-state ACTIVE --json
python -m agentic_runtime.cli identity trust-evidence validate --json
python -m agentic_runtime.cli identity trust-evidence explain --json
python -m agentic_runtime.cli identity seal-readiness --json
python -m agentic_runtime.cli identity p14-seal run --json
python -m agentic_runtime.cli identity p14-seal list-checks --json
python -m agentic_runtime.cli identity p14-seal run-check import_objects --json
```

See `agent/releases/P1.0_ALPHA_MANIFEST.md` for seal status and required verification.

Provider selection:

```bash
AUREL_MODEL_PROVIDER=mock python -m agentic_runtime.cli demo
AUREL_MODEL_PROVIDER=openai OPENAI_API_KEY=... python -m agentic_runtime.cli demo
AUREL_MODEL_PROVIDER=anthropic ANTHROPIC_API_KEY=... python -m agentic_runtime.cli demo
AUREL_MODEL_PROVIDER=ollama AUREL_OLLAMA_MODEL=llama3.1 python -m agentic_runtime.cli demo
```

See `TESTS.md` for canonical compile and pytest commands.



## P1.4.12 - Raw Source + Canonical Hash Attestation (2026-06-21)

- P1.4.12: hash-based source attestation - `source_attestation.py`, `source_bundle.py`, identity attestation CLI
- source model: `SourceKind`, `SourceValidationStatus`, `SourceHashPair`, `SourceAttestation`
- raw source hash is computed from unnormalized raw bytes/text; canonical typed hash is computed from deterministic typed JSON
- identity bundle now carries attestations for identity kernel, persona manifest, operator contract, communication modes, identity prompt compiler, self-model policy, and agent identity card config
- external doctrine records can produce full attestations without becoming implementation or capability evidence
- unknown governance/authority-shaped fields are rejected/attested instead of silently trusted
- CLI: `identity attestation {list,show,validate,verify-bundle,compare}`
- 41 focused identity tests; full suite was `1263 passed, 2 skipped` at P1.4.12 seal (now `1376 passed, 2 skipped` with P1.4.13/14)
- invariants `INV-P1412-01` through `INV-P1412-10`
- report: `agent/reports/P1.4.12_RAW_SOURCE_CANONICAL_HASH_ATTESTATION.md`

P1.4.12 provides hash-based source attestation. It does not provide cryptographic signatures, tamper-proof storage, trust scoring, or capability verification.

## P1.4.13 - Authority Delta Detector (2026-06-21)

- P1.4.13: semantic authority delta detection — `authority_delta.py`, CLI `identity authority-delta compare`
- domain model: `AuthorityDeltaType` (30 types), `AuthorityDeltaSeverity` (5 levels), `AuthorityDelta`, `AuthorityDeltaInput`, `AuthorityDeltaReport`
- authority surface extraction for operator_contract, agent_identity_card_config, self_model_policy, external_doctrine, capability_claims, source_attestation source kinds
- semantic delta classification for risk ceiling, human oversight, tool permissions, write scope, external effect, claim/capability/doctrine status escalation
- severity resolution (INFO/LOW/MEDIUM/HIGH/CRITICAL), consent/evidence requirement markers
- attestation reference linkage (old_attestation_id, new_attestation_id)
- conservative tool classification heuristic (external-effect, write, read-only tokens)
- CLI: `identity authority-delta compare --old/--new/--source-kind/--json`
- 58 tests (core, seal, CLI); full suite `1321 passed, 2 skipped`
- invariants `INV-P1413-01` through `INV-P1413-10`
- report: `agent/reports/P1.4.13_AUTHORITY_DELTA_DETECTOR.md`

P1.4.13 detects authority-relevant changes. It does not grant Operator consent, approve actions, or execute tools.

## P1.4.14 - Operator Consent Binding (2026-06-21)

- P1.4.14: delta-bound Operator consent — `operator_consent.py`, CLI `identity consent {request,grant,deny,revoke,show,validate}`
- domain model: `OperatorConsentStatus` (6 states), `OperatorConsentScope` (4 scopes), `OperatorConsentRequest`, `OperatorConsentRecord`, `ConsentBindingValidation`, `OperatorConsentDecision`
- `build_operator_consent_request()` from `AuthorityDeltaReport`, `grant_operator_consent()` with fail-closed risk acknowledgement, `deny_operator_consent()`, `revoke_operator_consent()`, `validate_operator_consent_binding()`
- binding rules: consent is bound to exact delta_ids and old/new attestation_ids, not global, not transferable, requires risk acknowledgement for HIGH/CRITICAL
- revoked/expired/denied consent is permanently invalid for binding validation
- scope behavior: SINGLE_DELTA, DELTA_REPORT, SOURCE_UPDATE, SESSION_LIMITED (unsupported)
- JSON serialization for all consent data models
- 55 tests (27 core, 14 seal, 10 CLI, 4 fixtures); full suite `1376 passed, 2 skipped`
- invariants `INV-P1414-01` through `INV-P1414-10`
- report: `agent/reports/P1.4.14_OPERATOR_CONSENT_BINDING.md`
- **Ready for P1.4.15** Principal / Delegate Model

P1.4.14 binds Operator consent to specific authority deltas. It does not execute changes, grant capabilities, or create global/permanent consent.

## P1.4.15 — Identity Governance Command Surface (2026-06-21)

- P1.4.15: unified identity CLI surface — `identity_cli_surface.py`, CLI `identity status` / `identity verify`
- Data models: `IdentityCliStatus` (OK/DEGRADED/BLOCKED/UNKNOWN), `IdentityCliEnvelope`, `IdentitySubsystemStatus`, `IdentityStatusReport`
- Standardized JSON envelope with `ok`/`command`/`status`/`errors`/`warnings`/`result`
- `build_identity_status_report()` — lightweight subsystem probes (read-only)
- `verify_identity_surface()` — non-destructive validator checks (read-only)
- Commands: `identity status --json`, `identity verify --json` with human-readable output
- All P1.4 subcommand groups (autonomy, claims, doctrine, attestation, authority-delta, consent) routed under one namespace
- Human-readable output exposes blockers and suggested next commands
- 53 tests (21 core/envelope, 23 routing, 9 seal); full suite `1429 passed, 2 skipped`
- invariants `INV-P1415-01` through `INV-P1415-10`
- report: `agent/reports/P1.4.15_IDENTITY_GOVERNANCE_COMMAND_SURFACE.md`
- **Ready for P1.4.16** Identity Test Battery

P1.4.15 implements a command surface, not an interactive agent terminal. It does not execute tools, grant consent, mutate identity sources, or create new authority.

## P1.4.11 — External Doctrine Assimilation Registry (2026-06-21)

- P1.4.11: source-hashed external doctrine registry — `external_doctrine.py`, `doctrine_registry.py`, `doctrine_mapping.py`, and `doctrine_claim_boundaries.py`
- seeded doctrine: `agentic_os_asymmetric_teardown`, `abos_design_principles_v1`, `aether_v0_2`
- each seeded doctrine has source hash, roadmap impact mapping, claim boundaries, risk notes, and Operator acceptance
- P1.4.10 integration: doctrine-derived overclaims are blocked/downgraded through the capability claim boundary engine
- CLI: `identity doctrine {list,show,validate,impact,claims}`
- 33 tests in `tests/test_external_doctrine_registry.py`, `tests/test_doctrine_cli.py`, `tests/test_doctrine_seal.py`
- invariants `INV-P1411-01` through `INV-P1411-10`
- report: `agent/reports/P1.4.11_EXTERNAL_DOCTRINE_ASSIMILATION_REGISTRY.md`
- **Ready for P1.4.12** Raw Source + Canonical Hash Attestation

P1.4.11 allows external doctrine to influence roadmap mapping. It does not allow doctrine to become implemented capability by declaration.

## P1.4.10 — Capability Claim Boundary Engine (2026-06-21)

- P1.4.10: evidence-gated capability claim evaluation — `capability_claims.py` with 14-claim static registry, anti-hype firewall, roadmap/implementation/verification boundary enforcement, global-autonomy blocking, safe rewrite engine that preserves truth, fail-closed on unknown claims or missing evidence
- CLI: `identity claims {evaluate,list,show,validate,rewrite}`
- 51 tests in `tests/test_capability_claim_boundary.py`
- 12 invariants `INV-P1410-01` through `INV-P1410-12`
- report: `agent/reports/P1.4.10_CAPABILITY_CLAIM_BOUNDARY_ENGINE.md`
- **Ready for P1.4.11** External Doctrine Assimilation Registry

## P1.4.7 / P1.4.7-MG — Agent Identity Card (2026-06-21)

- P1.4.7: machine-readable Agent Identity Card with six source-bound hashes, stable/runtime SHA-256, CLI `identity card {show,validate,hash,attest,taxonomy}`
- P1.4.7-MG merge gate: `self_model_policy_path` respected at final validation; `agent_identity_card` capability marked `implemented`; `IdentitySourceBundle` for single-load card path; identity CLI extracted to `cli_modules/`
- Canonical card hash snapshots updated after self-model inventory correction
- **Ready for P1.4.10** Capability Claim Boundary Engine (see P1.4.9 report for handoff)

## P1.4.9 — Measured Autonomy Score (2026-06-21)

- P1.4.9: evidence-backed measurement layer — `measure_autonomy_score()` from AutonomyDecision records, 9 measured autonomy classes, top blockers, confidence scoring
- `identity/autonomy_measurement.py` — domain types, engine, classification, JSONL persistence
- CLI: `identity autonomy measure` with `--json`, `--evaluate-and-record`
- 45 tests in `tests/test_measured_autonomy_score.py`
- 10 invariants `INV-P149-01` through `INV-P149-10`
- report: `agent/reports/P1.4.9_MEASURED_AUTONOMY_SCORE.md`
- **Ready for P1.4.10** Capability Claim Boundary Engine

## P1.4.8 — Autonomy Scale Engine (2026-06-21)

- P1.4.8: action-scoped autonomy decision engine — `resolve_autonomy_decision()` with A0–A7 scale, fail-closed validation, risk/reversibility/lifecycle escalation, capability honesty
- `identity/autonomy_scale_engine.py` — domain types, baseline matrix, resolver
- `identity/autonomy_scale_engine_validation.py` — fail-closed validation, invariant enforcement
- CLI: `identity autonomy evaluate` with `--json`, `--json` output
- 40 tests in `tests/test_autonomy_scale_engine.py`
- 10 invariants `INV-P148-01` through `INV-P148-10`
- report: `agent/reports/P1.4.8_AUTONOMY_SCALE_ENGINE.md`
- **Ready for P1.4.9** Measured Autonomy Score

## P1.4.16 — Identity Test Battery (2026-06-21)

- P1.4.16: full identity governance test battery — `identity_test_battery.py` (battery engine, models + engine) and `identity_test_battery_scenarios.py` (scenario runners)
- 26 test cases across 7 categories: kernel, persona, operator_contract, communication_modes, identity_context, self_model, identity_card
- Battery wraps all 26 cases into a single PASSED/FAILED/DEGRADED/SKIPPED status; each case individually scorable (OK/FAIL/SKIP)
- 10 invariants defined (INV-P1416-01 through INV-P1416-10), all passing
- New CLI under identity namespace: `identity test-battery {run,list,run-case}` with `--scenarios` toggle for adversarial cases
- Two-file split: battery engine (`identity_test_battery.py`) holds models + engine; scenario runners (`identity_test_battery_scenarios.py`) hold concrete scenarios with late imports to avoid circular imports
- New tests: `tests/identity/test_identity_test_battery.py` (18 core tests) and `tests/identity/test_identity_test_battery_seal.py` (13 integrated/seal tests) — 31 new tests
- Full test suite: **1460 passed, 2 skipped** (zero regressions from P1.4.15's 1429)
- Battery status: **PASSED (26/26)** — all kernel/persona/operator/modes/context/self_model/card categories green
- Adversarial scenarios included by default; CLI `--scenarios` toggleable
- report: `agent/reports/P1.4.16_IDENTITY_TEST_BATTERY.md`
- **Ready for P1.4.17** Continuity Capsule

P1.4.16 is a verification/test harness, not a new governance engine. It sits above P1.4.13-14-15 (authority delta, consent, command surface) and below P1.4.17, wrapping all prior identity layers into a single battery.

## P1.4.17 — Agent Lifecycle Eligibility State Machine (2026-06-21)

- P1.4.17: lifecycle eligibility state machine — `agent_lifecycle.py`, CLI `identity lifecycle {show,profile,validate-transition,transitions,recommend}`
- 8 lifecycle states: DRAFT, ACTIVE, SUSPENDED, RESTRICTED, MAINTENANCE, DEPRECATED, ARCHIVED, REVOKED
- 24 reason codes for state transitions (e.g. OPERATOR_INITIATED, CONSENT_EXPIRED, COMPLIANCE_VIOLATION, EOL_DECLARED)
- 9 lanes model — each lifecycle state maps to eligible/blocked lanes + required gates
- REVOKED is terminal — no transitions out; DRAFT→ACTIVE denied; SUSPENDED→ACTIVE denied
- RESTRICTED is reason-sensitive — restrictions depend on the transition reason, not a blanket block
- ACTIVE is gated — lane eligibility is explicit, not unlimited
- Lifecycle does NOT grant authority — it determines lane eligibility only; permission remains with Policy and HITL
- Recommendation engine reads governance signals (authority delta, consent, battery) but does not apply transitions
- 17 invariants: INV-P1417-01 through INV-P1417-17
- 60 new tests (38 core in test_agent_lifecycle.py, 22 seal/CLI in test_agent_lifecycle_seal.py)
- Full suite: 1520 passed, 2 skipped
- All validation/recommendation is read-only — no mutation of identity sources, no consent grants, no tool execution

P1.4.17 governs which lifecycle state an agent is in and which lanes it is eligible for. It does not execute tools, grant permissions, or decide authority — those remain with Policy, HITL, and the Operator Consent Binding.

## Package layout

```
src/agentic_runtime/   # runtime kernel
tests/                 # pytest suite
examples/demo.py       # thin wrapper around agentic_runtime.demo
agent/                 # agent operating docs (this folder)
```
