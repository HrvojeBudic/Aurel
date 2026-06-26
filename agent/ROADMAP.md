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

**P1.7 — Path Governance & Source Trust Foundation**

| Status | Module |
|--------|--------|
| **Last completed** | P1.7.8 — Source Provenance & Evidence Binding Seed |
| **Current active** | **P1.7.9 — Path/Source Risk Classification Model (planned)** |
| **Previous section** | P1.6 — Policy Cards & Behavioral Contracts (**SEALED WITH WARNINGS**) |
| **Next planned** | P1.7.9 — Path/Source Risk Classification Model |

**P1.7.8 complete** — Source provenance and evidence binding seed: `SourceProvenanceKind`, `EvidenceBindingKind`, `EvidenceConfidence`, `SourceClaimKind`, `SourceEvidenceRef`, `SourceClaimRef`, `SourceProvenanceRef`, `ProvenanceBinding`, `ProvenanceBindingRegistry`, `build_source_evidence_ref()`, `build_source_claim_ref()`, `build_source_provenance_ref()`, `build_provenance_binding()`, `build_provenance_binding_registry()`, deterministic evidence/claim/provenance/binding/registry hashes, source-label truth, and closed-world validation. Reference/binding objects only without truth verification, trace emission, Ledger writes, resolver, or enforcement. P1.7 remains in progress. Next: **P1.7.9 — Path/Source Risk Classification Model**.

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
