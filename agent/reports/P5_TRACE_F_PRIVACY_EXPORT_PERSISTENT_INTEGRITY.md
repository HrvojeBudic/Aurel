# P5-TRACE-F — Privacy / Export / Persistent Backend Integrity

**Date:** 2026-07-05
**Domain:** P5 — AurelTrace Spine (continues P5 after P5-TRACE-A/B/C/D/E)
**Pack:** P5-TRACE-F
**Status:** DONE — P5-E trace material made privacy/redaction/export/persistence-integrity-aware, read-only, no compliance/upload/storage claims.
**Previous pack:** P5-TRACE-E — Projection Feed / Golden Thread / Replay Readiness
**Next pack:** P5-TRACE-G — P5 Exit Seal / P6-P8-P9 Handoff

---

## Purpose

P5-TRACE-E made trace truth projection-ready (feed / Golden Thread / replay-readiness).
P5-TRACE-F makes that P5-E material **safer to label, redact, bundle, and assess**: it labels
feed/thread/readiness refs with privacy and locality posture, produces deterministic redaction
decisions and a safe redacted view, builds an export manifest and audit bundle listing exactly
what is included/excluded/redacted/hashed, and profiles + assesses a persistent trace backend's
integrity posture.

Law: **Runtime emits. P5 adapts. Resolver decides. Projection feed presents. Golden Thread links.
Replay-readiness assesses prerequisites. P5-F labels, redacts, bundles, and assesses persistence
posture. Custos authorizes. Operator decides.**

P5-F **labels, filters, bundles, and assesses only**. It does not certify compliance, upload,
encrypt, scan PII/secrets, migrate a DB, retain, or replace storage. Privacy label ≠ redaction;
redaction decision ≠ compliance; export manifest ≠ external export; audit bundle ≠ legal
certification; persistent-integrity profile ≠ production storage. `UNKNOWN`, `LOCAL_ONLY`,
`SECRET`, and `EXPORT_RESTRICTED` fail closed — never raw export.

---

## P5-E dependency (read + used as source material)

The P5-E report (`agent/reports/P5_TRACE_E_PROJECTION_FEED_GOLDEN_THREAD_REPLAY_READINESS.md`)
was read, and the P5-E source outputs are used as the source material — this is not a generic
privacy/export module. `build_redacted_trace_view` and `build_trace_export_manifest` accept a
`TraceProjectionFeed`, a `GoldenThreadGraph`, and a `ReplayReadinessAssessment`; the manifest
preserves the P5-E `feed_entry_id`s, the `GoldenThreadRef` id, and the `ReplayReadinessAssessment`
id, and the P5-D `TraceVerificationDecision` ids (`source_resolver_decisions`). Proven by
`test_trace_export_manifest.py::test_p5_refs_preserved` and
`test_trace_audit_bundle.py::test_bundle_includes_golden_thread_and_replay_material`.

---

## Roadmap coverage (P5.17–P5.19)

| Range | Title | Status | Evidence |
|---|---|---|---|
| P5.17 | Privacy / Redaction / Locality Labels | DONE | `privacy_labels.py`; `test_privacy_labels.py` (8) + `test_redacted_trace_view.py` (7) |
| P5.18 | Export Manifest / Audit Bundle | DONE | `trace_export.py`; `test_trace_export_manifest.py` (5) + `test_trace_audit_bundle.py` (5) |
| P5.19 | Persistent Backend Integrity Profile | DONE | `persistent_integrity.py`; `test_persistent_integrity_profile.py` (8) |

36 focused P5-F tests (incl. 3 boundary), all passing; A–E + legacy regression green (227 in
`tests/aurel_trace` + legacy).

---

## Privacy / redaction proof (`privacy_labels.py`)

- **`TracePrivacyLabel`** (PUBLIC … UNKNOWN) and **`TraceLocalityLabel`** (LOCAL_ONLY … UNKNOWN)
  are closed-world. **`TraceRedactionMode`** (NONE/MASK/HASH/SUMMARY_ONLY/EXCLUDE/ERROR) has a
  fixed severity order so combining the privacy-derived and locality-derived modes takes the
  **strictest**.
- **`TraceRedactionPolicy`** (default maps: LOCAL_ONLY/SECRET/SENSITIVE_PERSONAL_DATA → EXCLUDE,
  CONFIDENTIAL/PERSONAL_DATA → MASK, UNKNOWN → SUMMARY_ONLY, EXPORT_RESTRICTED/LOCAL_ONLY locality
  → EXCLUDE). `make_trace_redaction_decision` is deterministic and fails closed on a non-enum
  label. Proven: PUBLIC/EXPORT_ALLOWED → NONE; LOCAL_ONLY (privacy **or** locality) → EXCLUDE;
  EXPORT_RESTRICTED → EXCLUDE; UNKNOWN/UNKNOWN → SUMMARY_ONLY (never NONE); strictest-of-two wins.
- **`RedactedTraceItem`** cannot carry a raw `safe_value` unless mode is NONE, and an EXCLUDE item
  carries no payload at all (enforced). **`RedactedTraceView`** is a safe read model whose
  `mutates` is unconstructible True; `build_redacted_trace_view` labels each source ref, decides,
  and emits safe items **without mutating** the frozen source feed/graph/assessment (proven:
  `feed.to_dict()` is byte-identical before and after). Unmapped refs default to UNKNOWN/UNKNOWN
  and fail closed to a non-raw mode.

---

## Export manifest / audit bundle proof (`trace_export.py`)

- **`TraceBundleInclusionDecision`** derives exactly one inclusion flag from a redaction mode
  (NONE→include_raw; MASK→include_redacted; HASH→include_hash; SUMMARY_ONLY→include_summary;
  EXCLUDE→exclude).
- **`TraceExportManifest`** lists `included_refs`/`excluded_refs`/`redacted_refs`/`hashed_refs`/
  `summary_only_refs`, preserves P5-D/P5-E source refs, records deterministic `checksums`, and
  always carries `unavailable_compliance_claims` (legal compliance certification, external
  export/upload, encryption/KMS, PII/secret detection, production distributed ledger). Its
  `is_external_export`/`uploads`/`encrypts`/`certifies_compliance` are unconstructible True. Only
  NONE-mode material lands in `included_refs` raw — proven that LOCAL_ONLY/SECRET/UNKNOWN never
  enter `included_refs`.
- **`TraceAuditBundle`** packages a manifest + redacted view, preserves resolver/feed/golden-thread/
  readiness refs, respects LOCAL_ONLY exclusion (the excluded ref is not among included items), is
  deterministic, and its `is_external_export`/`is_legal_certification`/`is_encrypted`/`uploads` are
  unconstructible True.

---

## Persistent backend integrity proof (`persistent_integrity.py`)

- **`PersistentTraceBackendKind`** (IN_MEMORY…UNKNOWN), **`PersistentTraceBackendStatus`**
  (DEV_ONLY…ERROR), **`PersistentIntegrityRisk`** (LOW…CRITICAL).
- **`PersistentTraceBackendProfile`** describes posture only: `migrates_storage`/`replaces_backend`/
  `is_distributed_ledger`/`certifies_durability` are unconstructible True, and a LOCAL_DURABLE
  profile must record the "not a production distributed ledger" limitation (enforced).
  `profile_persistent_trace_backend`: IN_MEMORY → DEV_ONLY (durability unavailable); JSONL/
  FILE_SYSTEM/SQLITE → LOCAL_DURABLE only with append-only + hash-chain + fsync claims, else
  PARTIAL; EXTERNAL_DB → UNAVAILABLE unless durability flags; UNKNOWN → UNSUPPORTED (proven).
- **`PersistentTraceIntegrityAssessment`** runs eight checks (append-only, hash-chain, receipt,
  fsync durability, tamper detection, schema compatibility, privacy labels, export compatibility)
  → passed/missing/unsupported + deterministic `risk_level` + limitations + recommendations. For
  IN_MEMORY the durability checks are structurally UNSUPPORTED. The assessment never certifies
  production and lists missing guarantees; LOCAL_DURABLE is explicitly not a production ledger.

---

## Truth label posture

- **LIVE** — privacy/locality labels, redaction policy/decisions, redacted view, inclusion
  decisions, export manifest, audit bundle, backend profile, integrity assessment.
- **TRACE_VERIFIED** — only ever reflected from P5-D decisions via P5-E feed entries; never minted
  here.
- **REDACTED / EXPORT_ALLOWED / EXPORT_RESTRICTED / LOCAL_ONLY** — carried by the module-local
  redaction/privacy/locality enums, not by `TraceTruthLabel`.
- **UNAVAILABLE** — legal/regulatory certification, external export / cloud upload, encryption/KMS,
  PII/secret detection, DB migration, production retention, production distributed ledger, Shell/API
  export UI (all listed on every manifest).
- **ERROR** — inconsistent privacy/export/integrity state (e.g. a non-enum label, or a bundle
  inclusion decision with not exactly one flag).

---

## Boundary / side-effect proof

runtime.py modified: **no** · runtime.submit called: **no** · trace append/repair/mutation: **no**
· `ToolRuntime.dispatch`: **no** · policy enforcement: **no** · approval activation: **no** · memory
write: **no** · workflow/job execution: **no** · external export: **no** · cloud upload: **no** ·
network call: **no** · encryption/KMS: **no** · PII detector: **no** · secret scanner: **no** · DB
migration/write: **no** · production retention: **no** · distributed ledger: **no** · Shell UI: **no**
· API server: **no** · event bus: **no** · P9 enforcement: **no** · Rust/WASM: **no** · new ledger:
**no** · legal/regulatory compliance claim: **no** · complete P5 seal claim: **no**.

`test_privacy_export_boundaries.py` ast-sweeps the three modules: no `AgenticRuntime`/`ToolRuntime`/
`.submit(`/`.dispatch(`/`trace.append`/`.rollback(`/`.upload(`/`.post(`/`.put(`/`open(`/`.write(`/
`.execute(`/`cursor(`/`subprocess`/`socket.`/`.connect(`/`.encrypt(` fragments in code; no import of
runtime/tool_runtime/policy/sandbox/verifier/memory/aurel_exec/aurel_flow/aurel_shell/requests/
urllib/http/socket/boto3/sqlite3/cryptography/ssl/subprocess; and building a redacted view leaves
the source feed byte-identical. Only `aurel_trace/` (three new modules + `__init__.py` exports) and
`tests/aurel_trace/` (six new test files) were touched.

---

## Validation

| Gate | Command | Result | Notes |
|---|---|---|---|
| compileall | `python -m compileall src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | |
| Focused P5-F tests | `pytest test_privacy_labels.py test_redacted_trace_view.py test_trace_export_manifest.py test_trace_audit_bundle.py test_persistent_integrity_profile.py test_privacy_export_boundaries.py -q` | PASS | 36 passed |
| A–E + legacy regression | `pytest tests/aurel_trace tests/test_trace*.py -q` | PASS | 227 passed |
| ruff | `ruff check src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | All checks passed |
| mypy | `mypy src/agentic_runtime/aurel_trace` | PASS | 23 files, no issues |
| git status | `git status --short` | clean | after in-scope commit |

---

## Files created

- `src/agentic_runtime/aurel_trace/privacy_labels.py`
- `src/agentic_runtime/aurel_trace/trace_export.py`
- `src/agentic_runtime/aurel_trace/persistent_integrity.py`
- `tests/aurel_trace/test_privacy_labels.py`
- `tests/aurel_trace/test_redacted_trace_view.py`
- `tests/aurel_trace/test_trace_export_manifest.py`
- `tests/aurel_trace/test_trace_audit_bundle.py`
- `tests/aurel_trace/test_persistent_integrity_profile.py`
- `tests/aurel_trace/test_privacy_export_boundaries.py`
- `agent/reports/P5_TRACE_F_PRIVACY_EXPORT_PERSISTENT_INTEGRITY.md` (this report)

## Files modified

- `src/agentic_runtime/aurel_trace/__init__.py` (exports only)
- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/ARCHITECTURE.md`,
  `agent/DECISIONS.md`, `agent/TESTS.md` (canon)

---

## Remaining risks

- **Privacy labels:** labels are supplied by the caller (a `label_map`); P5-F does not detect
  PII/secrets and unlabeled refs fail closed to UNKNOWN → non-raw. A future pack could add an
  operator-driven labeling surface, still without an automatic detector.
- **Redaction:** the redacted view carries only masked/summary/hash/excluded safe representations;
  it never touches raw sensitive payload because the P5-E source refs are ids, not raw content.
- **Export/audit bundle:** these are in-memory read-model contracts; there is no serializer to disk
  or network by design, and every manifest lists what is UNAVAILABLE (compliance/upload/encryption/
  ledger).
- **Persistent integrity:** the profile/assessment describe posture from declared capability flags;
  they verify nothing at runtime and migrate no storage. LOCAL_DURABLE is a local posture only.
- **P5-G handoff:** the exit seal should consume P5-F truth labels, the explicit unavailable-claims
  list, the backend integrity posture, and these remaining risks when deciding whether P5 can be
  sealed and handed to P6/P8/P9.

**Next recommended task:** P5-TRACE-G — P5 Exit Seal / P6-P8-P9 Handoff.
