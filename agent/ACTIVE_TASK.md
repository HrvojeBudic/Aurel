# Active Task: P1.7.15 (planned)

**Status:** P1.7.14 COMPLETE; P1.7.15 PLANNED

## Roadmap Position

- Current completed task: **P1.7.14 — Path Violation / Drift Trace Hook**
- Next planned task: **P1.7.15 — Path Governance Test Harness**
- Roadmap version: **v5.1 Integration-First**

## P1.7 Status

**IN PROGRESS** — path violation/drift trace payload/hook model added; broader P1.7 path/source governance remains in progress.

P1.7.14 adds `PathViolationTraceEventKind`, `PathViolationSeverity`, `PathViolationTraceHookMode`, `PathViolationTraceDisposition`, `PathViolationTraceReason`, `PathViolationTraceInput`, `PathViolationTracePayload`, `PathViolationTraceHookResult`, `PathSourceDriftSignal`, `build_path_violation_trace_payload()`, `record_path_violation_trace_hook()`, `detect_path_source_drift_signals()`, deterministic input/payload/hook/drift-signal identifiers and hashes, closed-world validation, source-label truth, `PAYLOAD_ONLY` default mode, optional injected sink testability, and observability-only violation/drift hook boundary semantics.

Violation/drift trace hook records evidence of mismatch. It does not correct, enforce, rollback, or punish. Every hook result has `ledger_written=false`, `runtime_mutated=false`, and `enforcement_triggered=false`.

No path governance test harness, policy engine integration, real conflict enforcement, real precedence enforcement, source trust mutation, source taxonomy mutation, source identity mutation, trust promotion, source blocking, runtime quarantine, memory canonization, approval activation, global trace spine write by default, fake TRACE_VERIFIED, Ledger write, correction, rollback, active prompt filtering, prompt rewriting, memory write gating, tool argument blocking, filesystem access, network access, sandbox hardening, runtime enforcement, CLI/TUI binding, Shell UI, or policy bridge was added.

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
