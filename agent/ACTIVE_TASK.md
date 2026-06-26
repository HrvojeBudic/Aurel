# Active Task: P1.7.19 (planned)

**Status:** P1.7.18 COMPLETE; P1.7.19 PLANNED

## Roadmap Position

- Current completed task: **P1.7.18 — Path Governance CLI/TUI Binding**
- Next planned task: **P1.7.19 — Docs/State/Reports Update**
- Roadmap version: **v5.1 Integration-First**

## P1.7 Status

**IN PROGRESS** — CLI/TUI binding added; broader P1.7 path/source governance remains in progress.

P1.7.18 adds `PathGovernanceCliCommandKind`, `PathGovernanceCliOutputFormat`, `PathGovernanceCliBindingMode`, `PathGovernanceCliSideEffects`, `PathGovernanceCliRequest`, `PathGovernanceCliRenderedLine`, `PathGovernanceCliResponse`, `build_path_governance_cli_request()`, `render_path_governance_status_text()`, `render_path_governance_capability_table()`, `render_path_governance_json_payload()`, `render_path_governance_cli_response()`, `handle_path_governance_cli_request()`, read-only `path-governance` CLI subcommands, deterministic request/line/response hashes, closed-world validation, source-label truth, unavailable reason visibility, and read-only side-effect truth booleans (all false).

Path Governance CLI/TUI Binding exposes projection state to the operator. It does not create authority. It does not execute policy. It does not mutate path/source governance state.

No Shell UI, Web UI, HTTP server, policy engine integration, approval activation, real enforcement, Ledger write, global trace spine write, source trust mutation, prompt filtering, memory/tool gating, filesystem access, network access, sandbox hardening, or runtime enforcement was added.

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
- `agent/reports/P1.7.18_PATH_GOVERNANCE_CLI_TUI_BINDING.md`
