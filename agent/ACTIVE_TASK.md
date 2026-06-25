# Active Task: P1.7.2 (planned)

**Status:** P1.7.1 COMPLETE; P1.7.2 PLANNED

## Roadmap Position

- Current completed task: **P1.7.1 — Path Identity & Canonical Path Schema**
- Next planned task: **P1.7.2 — Source Identity & SourceRef Schema**
- Roadmap version: **v5.1 Integration-First**

## P1.7 Status

**IN PROGRESS** — path identity schema added; broader P1.7 path/source governance remains in progress.

P1.7.1 adds `PathKind`, `PathSensitivity`, `CanonicalizationStatus`, `PathRef`, `CanonicalPathRef`, `PathIdentity`, and `build_path_identity()` with deterministic `path_hash`, `canonical_hash`, and `identity_hash`. It preserves raw path separately from normalized/display representation and keeps closed-world validation.

No path resolver, source resolver, trusted root registry, path escape detection, runtime enforcement, Ledger write, approval activation, sandbox behavior change, CLI/TUI binding, Shell UI, trace hook, or policy bridge was added.

## Completed Reports

- `agent/reports/P1.7.0_PATH_GOVERNANCE_SOURCE_TRUST_FOUNDATION.md`
- `agent/reports/P1.7.1_PATH_IDENTITY_CANONICAL_PATH_SCHEMA.md`
