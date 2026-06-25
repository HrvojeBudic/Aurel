# Active Task: P1.7.7 (planned)

**Status:** P1.7.6 COMPLETE; P1.7.7 PLANNED

## Roadmap Position

- Current completed task: **P1.7.6 — Path Authority Scope Model**
- Next planned task: **P1.7.7 — Untrusted Content Boundary Model**
- Roadmap version: **v5.1 Integration-First**

## P1.7 Status

**IN PROGRESS** — path authority scope model added; broader P1.7 path/source governance remains in progress.

P1.7.6 adds `PathAuthoritySubjectKind`, `PathAuthorityBasis`, `PathAuthorityConstraintKind`, `PathAuthoritySubject`, `PathAuthorityConstraint`, `PathAuthorityScope`, `PathAuthorityScopeRegistry`, `build_path_authority_scope()`, and `build_path_authority_scope_registry()` with deterministic subject/constraint/scope/registry hashes, closed-world validation, source-label truth, and declarative-only authority scope semantics.

Authority scope declarations are not permissions, runtime authority, sandbox policy, resolver output, or enforcement. Subject kind does not grant authority. Basis does not grant permission. Constraint does not enforce.

No untrusted content boundary model, path governance resolver, source trust resolver, path permission enforcement, filesystem read/stat/resolve, symlink resolution, sandbox hardening, runtime enforcement, Ledger write, approval activation, CLI/TUI binding, Shell UI, trace hook, or policy bridge was added.

Git status: committed locally, no push performed.

## Completed Reports

- `agent/reports/P1.7.0_PATH_GOVERNANCE_SOURCE_TRUST_FOUNDATION.md`
- `agent/reports/P1.7.1_PATH_IDENTITY_CANONICAL_PATH_SCHEMA.md`
- `agent/reports/P1.7.2_SOURCE_IDENTITY_SOURCE_REF_SCHEMA.md`
- `agent/reports/P1.7.3_SOURCE_TRUST_LABEL_TAXONOMY.md`
- `agent/reports/P1.7.4_TRUSTED_ROOT_SCOPE_REGISTRY_SEED.md`
- `agent/reports/P1.7.5_PATH_NORMALIZATION_ESCAPE_DETECTION_CONTRACT.md`
- `agent/reports/P1.7.6_PATH_AUTHORITY_SCOPE_MODEL.md`
