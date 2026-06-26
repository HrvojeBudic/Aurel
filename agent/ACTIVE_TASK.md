# Active Task: P1.7.18 (planned)

**Status:** P1.7.17 COMPLETE; P1.7.18 PLANNED

## Roadmap Position

- Current completed task: **P1.7.17 — Path Governance Projection/API/Event Contract**
- Next planned task: **P1.7.18 — Path Governance CLI/TUI Binding**
- Roadmap version: **v5.1 Integration-First**

## P1.7 Status

**IN PROGRESS** — projection/API/event contract added; broader P1.7 path/source governance remains in progress.

P1.7.17 adds `PathGovernanceCapabilityKind`, `PathGovernanceProjectionEventKind`, `PathGovernanceProjectionRecord`, `PathGovernanceReadModel`, `PathGovernanceProjectionEvent`, `PathGovernanceApiEnvelope`, `build_path_governance_projection_record()`, `build_path_governance_read_model()`, `build_path_governance_projection_event()`, `build_path_governance_api_envelope()`, `build_default_path_governance_capability_projection()`, deterministic record/read-model/event/envelope identifiers and hashes, closed-world validation, source-label truth, unavailable reason handling, and projection-only boundary semantics.

Projection contract exposes state. It does not execute state. API/event contract is not CLI binding. Read model is not source of truth.

No CLI/TUI binding, Shell UI, HTTP server, policy engine integration, approval activation, real enforcement, Ledger write, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem access, network access, sandbox hardening, or runtime enforcement was added.

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
- `agent/reports/P1.7.17_PATH_GOVERNANCE_PROJECTION_API_EVENT_CONTRACT.md`
