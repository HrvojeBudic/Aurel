# Active Task: P1.7.17 (planned)

**Status:** P1.7.16 COMPLETE; P1.7.17 PLANNED

## Roadmap Position

- Current completed task: **P1.7.16 — Policy Context Bridge**
- Next planned task: **P1.7.17 — Path Governance Projection/API/Event Contract**
- Roadmap version: **v5.1 Integration-First**

## P1.7 Status

**IN PROGRESS** — policy context bridge added; broader P1.7 path/source governance remains in progress.

P1.7.16 adds `PathPolicyContextSubjectKind`, `PathPolicyDecisionSurface`, `PathPolicyRequirementKind`, `PathPolicyBridgeMode`, `PathPolicyBridgeDisposition`, `PathPolicyContextInput`, `PathPolicyContextSubjectRef`, `PathPolicyContextPacket`, `PathPolicyContextBridgeResult`, `build_path_policy_context_subject_ref()`, `derive_path_policy_requirements()`, `build_path_policy_context_packet()`, `bridge_path_governance_to_policy_context()`, deterministic input/subject/packet/bridge identifiers and hashes, closed-world validation, source-label truth, advisory requirement derivation, and context-only bridge boundary semantics.

Policy Context Bridge prepares governance context. It does not decide policy. Context readiness is not authority. Policy bridge is input shaping, not enforcement.

No projection/API/event contract, CLI/TUI binding, Shell UI, policy engine integration, approval activation, real enforcement, Ledger write, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem access, network access, sandbox hardening, or runtime enforcement was added.

Git status: committed locally, no push performed.

## Completed Reports

- `agent/reports/P1.7.0_PATH_GOVERNANCE_SOURCE_TRUST_FOUNDATION.md`
- `agent/reports/P1.7.1_PATH_IDENTITY_CANONICAL_PATH_SCHEMA.md`
- `agent/reports/P1.7.2_SOURCE_IDENTITY_SOURCE_REF_SCHEMA.md`
- `agent/reports/P1.7.3_SOURCE_TRUST_LABEL_TAXONOMY.md`
- `agent/reports/P1.7.4_TRUSTED_ROOT_SCOPE_REGISTRY_SEED.md`
- `agent/reports/P1.7.5_PATH_NORMALIZATION_ESCAPE_DETECTION_CONTRACT.md`
- `agent/reports/P1.7.6_PATH_AUTHORITY_SCOPE_MODEL.md`
- `agent/reports/P1.7.7_UNTRUSTED_CONTENT_BOUNDARY_MODEL.md`
- `agent/reports/P1.7.8_SOURCE_PROVENANCE_EVIDENCE_BINDING_SEED.md`
- `agent/reports/P1.7.9_PATH_SOURCE_RISK_CLASSIFICATION_MODEL.md`
- `agent/reports/P1.7.10_PATH_GOVERNANCE_RESOLVER_SHADOW_MODE.md`
- `agent/reports/P1.7.11_SOURCE_TRUST_RESOLVER_SHADOW_MODE.md`
- `agent/reports/P1.7.12_PATH_SOURCE_CONFLICT_PRECEDENCE_RULES.md`
- `agent/reports/P1.7.13_PATH_RESOLUTION_TRACE_HOOK.md`
- `agent/reports/P1.7.14_PATH_VIOLATION_DRIFT_TRACE_HOOK.md`
- `agent/reports/P1.7.15_PATH_GOVERNANCE_TEST_HARNESS.md`
- `agent/reports/P1.7.16_POLICY_CONTEXT_BRIDGE.md`
