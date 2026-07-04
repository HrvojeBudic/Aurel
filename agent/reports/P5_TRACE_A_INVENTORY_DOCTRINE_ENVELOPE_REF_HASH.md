# P5-TRACE-A — Existing Trace Inventory / Doctrine / Canonical Envelope / TraceRef / Hash Verification

**Date:** 2026-07-04
**Domain:** P5 — AurelTrace Spine (opens P5)
**Pack:** P5-TRACE-A
**Status:** DONE — foundation established, adapter-first, no duplicate trace truth.
**Next pack:** P5-TRACE-B — Receipts / Schema Registry / Submit Coverage Audit

---

## Purpose

Establish the first AurelTrace Spine layer as an **adapter and structured
verification foundation over the existing trace implementation** — not a second
trace engine. P5-TRACE-A inventories the existing trace system, locks doctrine
that forbids duplicate trace truth, wraps existing ledger records into
deterministic canonical envelopes, creates stable references, and verifies
hash-chain integrity with structured findings — while leaving `runtime.submit()`,
P4, Shell, P9, replay, and Rust/WASM completely untouched.

Law: **Runtime emits. Trace canonicalizes. P5 verifies. Projections derive.
Custos authorizes. Operator decides.**

---

## Roadmap coverage (P5.0–P5.4)

| Range | Title | Status | Evidence |
|---|---|---|---|
| P5.0 | Existing Trace Inventory / Compatibility Lock | DONE | `trace_inventory.py`; `test_trace_inventory.py` (7 tests) |
| P5.1 | AurelTrace Doctrine / Boundary Lock | DONE | `trace_doctrine.py`; `test_trace_doctrine.py` (6 tests) |
| P5.2 | Canonical Trace Event Envelope Adapter | DONE | `trace_envelope.py`; `test_canonical_trace_envelope.py` (8 tests) |
| P5.3 | TraceRef / TraceBindingRef Normalization | DONE | `trace_refs.py`; `test_trace_refs.py` (7 tests) |
| P5.4 | Hash Chain Verification Kernel v1 | DONE | `trace_verify.py` + `trace_hash.py`; `test_trace_hash_verification.py` (12 tests) |

40 focused tests total, all passing.

---

## Existing trace inventory summary

The repository has **two** existing trace systems; P5-TRACE-A catalogs both and
adapts the first:

1. **`agentic_runtime.trace`** — the operational hash-chained ledger
   (`InMemoryTraceLedger`, `PersistentTraceLedger`) over the nine record types
   in `agentic_runtime.core_types` (`StateTransitionRecord`,
   `PlanningFailureRecord`, `RuntimeStatusTransitionRecord`,
   `BudgetDecisionRecord`, `MemoryGovernanceRecord`,
   `ToolContractViolationRecord`, `ApprovalReceiptRecord`, `PraxisEventRecord`,
   `SandboxViolationRecord`). Each record exposes `entry_hash`,
   `prev_entry_hash`, `id`, and a deterministic `payload_hash()`; the in-memory
   ledger chains `entry_hash = sha(prev_entry_hash, payload_hash())` from
   `GENESIS`. **This is the P5-A normalization target.**
2. **`agentic_runtime.contracts.trace`** — the contract-first canonical
   `AurelTraceLog` event form, which *already* defines its own `TraceEventRef`,
   `TraceBindingRef`, `TraceIntegrityReport`, and a distinct
   `compute_event_hash` scheme. Catalogued as related repo truth and **deferred**
   as a normalization target (reported as unsupported, never silently claimed
   supported).

- **Trace modules:** `trace`, `core_types`, `contracts.trace`, `contracts.projections`.
- **Ledger types:** `InMemoryTraceLedger`, `PersistentTraceLedger`.
- **Projection types:** `contracts.projections.ProjectionRecord` / `ProjectionKind` / `projection_from_event`.
- **Supported records:** the nine `core_types` ledger record types.
- **Unsupported (deferred):** `contracts.trace.TraceEvent` / `AurelTraceLog` (separate canonical scheme).
- **Compatibility note (naming overlap, reported not resolved):**
  `contracts.trace` already owns `TraceEventRef` and `TraceBindingRef` for its
  event form. The P5 refs of the same conceptual family live in the
  `aurel_trace` namespace and reference the *operational* ledger records and the
  P5 envelope layer. They are a distinct additive layer, not a replacement.

---

## Doctrine proof

`AurelTraceDoctrine` (`trace_doctrine.py`) encodes the P5 boundary as
machine-checked locked booleans:

- **No duplicate trace truth:** `duplicate_trace_spine_allowed == False` (locked; flipping raises).
- **No execution:** `execution_available == False`.
- **No authorization:** `authorization_available == False`.
- **No Shell UI / API / event bus:** `shell_ui_available`, `api_server_available`, `event_bus_available == False`.
- **No replay:** `replay_available == False`.
- **No Rust/WASM:** `rust_wasm_available == False`.
- **No P9 enforcement:** `p9_enforcement_available == False`.
- **TRACE_BOUND ≠ TRACE_VERIFIED:** `trace_bound_is_trace_verified == False`,
  `trace_verified_requires_verification == True`.
- **Hash integrity ≠ semantic correctness:** `semantic_correctness_claim_available == False`.

The doctrine is `TraceTruthLabel.LIVE`; it cannot be constructed carrying the
`TRACE_INTEGRITY_VERIFIED` label.

---

## No-duplicate-trace-spine proof

- `aurel_trace` **imports downward only** — from `core_types` and `trace`; neither
  `trace.py` nor `core_types.py` imports `aurel_trace` (verified: no circular
  import; `compileall` + import smoke test green).
- No new ledger class; no persistence; `envelopes_from_ledger` and
  `trace_run_ref_from_ledger` **iterate a live ledger read-only** and never
  append or mutate.
- The truth vocabulary `TraceTruthLabel` deliberately has **no `TRACE_VERIFIED`
  member** — the strongest mintable label is `TRACE_INTEGRITY_VERIFIED`.

---

## Canonical envelope proof

- **Class:** `CanonicalTraceEventEnvelope` (frozen). Wraps one supported record;
  captures `payload_hash`, `entry_hash`, `previous_entry_hash` as the ledger
  computed them; TRACE_BOUND by construction; cannot be constructed as
  `TRACE_INTEGRITY_VERIFIED` or `INTEGRITY_VERIFIED`.
- **Adapters:** `canonical_envelope_from_existing_record` (strict, raises on
  unsupported), `try_canonical_envelope` (lenient, reports), `envelopes_from_ledger`.
- **Deterministic serialization:** hash material is stable canonical JSON with
  sorted keys via the repo's `canonical_json`; `payload_hash` is the record's own
  `payload_hash()`; `canonical_event_id` is derived from the stable
  `TraceHashMaterial`. Nondeterministic `created_at` is **metadata only** and is
  excluded from hash material (proven: shifting `created_at` by +999s does not
  change the canonical event id).
- **Unsupported handling:** the strict adapter raises
  `TraceEnvelopeUnsupportedError` for a `contracts.trace` `AurelTraceLog` event;
  the lenient adapter reports `supported=False` with a reason. A record with no
  `entry_hash` (un-appended) is rejected as insufficient. Nothing silently passes.

---

## TraceRef proof

- `TraceRunRef` — stable ref to a run/ledger sequence (id, backend, chain head, count).
- `TraceEntryRef` — stable ref to one existing ledger record (entry hash, record type, prev hash).
- `TraceEventRef` — stable ref to one canonical envelope (canonical event id, entry ref, kind, payload hash).
- `TraceBindingRef` — generic domain→trace binding (domain, object id, event ref id, binding kind).
- **Stability:** same record → same ref; different records → different refs
  (proven over the four-record demo ledger). All refs are serializable via
  `to_dict`.
- **Binding is not verification:** `TraceBindingRef.verification_status` defaults
  to `NOT_VERIFIED`, cannot be constructed as `INTEGRITY_VERIFIED`, and cannot
  carry the `TRACE_INTEGRITY_VERIFIED` label. No ref carries the integrity-verified
  label.

---

## Hash verification proof

- **Request:** `TraceHashVerificationRequest` over scopes `FULL_CHAIN`,
  `SEGMENT`, `SINGLE_ENTRY`, `CHAIN_HEAD` (scope-specific fields validated).
- **Result:** `TraceHashVerificationResult` with `status` ∈
  {PASS, FAIL, PARTIAL, UNAVAILABLE, ERROR}, counts, `first_invalid_index`,
  `chain_head_hash`, and structured `findings`. **PASS is unconstructible when
  invalid_count > 0**, and only a PASS result may carry `verified=True` /
  `TRACE_INTEGRITY_VERIFIED`.
- **Finding model:** `TraceHashFinding` over the ten finding kinds
  (BROKEN_PREVIOUS_HASH, ENTRY_HASH_MISMATCH, PAYLOAD_HASH_MISMATCH,
  CHAIN_HEAD_MISMATCH, UNSUPPORTED_RECORD_TYPE, DUPLICATE_ENTRY_ID, MISSING_ENTRY,
  SCHEMA_UNKNOWN, CAUSAL_REF_BROKEN, INSUFFICIENT_DATA). Findings are evidence
  only.
- **Valid chain:** the real four-record demo ledger verifies FULL_CHAIN → PASS
  with `TRACE_INTEGRITY_VERIFIED`.
- **Broken chain:** tampering `previous_entry_hash` → FAIL with
  BROKEN_PREVIOUS_HASH; tampering `payload_hash` → FAIL with ENTRY_HASH_MISMATCH.
- **Chain head:** matching expected head → PASS; wrong head → FAIL with
  CHAIN_HEAD_MISMATCH.
- **Unsupported record:** `verify_trace_records` over a mixed list yields
  **PARTIAL** with an UNSUPPORTED_RECORD_TYPE finding — never silent PASS.
- **No auto-repair:** verification never mutates input envelopes (proven: the
  tampered value is still present after verification).
- Verification reuses the **operational ledger's own `sha`/`GENESIS`** — one hash
  truth, no second scheme.

---

## Truth label posture

- **LIVE** — inventory, doctrine, canonical envelope adapter, refs, structured verification kernel.
- **TRACE_BOUND** — existing records present and referenced but not verified (all envelopes and refs).
- **TRACE_INTEGRITY_VERIFIED** — only a supported chain/segment/head that actually passes P5-A hash verification.
- **TRACE_VERIFIED** — **not claimed** (no such label exists in the P5-A vocabulary).
- **UNAVAILABLE** — replay, exact copy, distributed store, Rust/WASM, P9 enforcement, Shell UI, API/event bus, semantic verification, empty/insufficient verification input.
- **ERROR** — reserved for inconsistent/broken integrity state (result status).

---

## Boundary / side-effect proof

`runtime.submit` rewritten: **no** · new execution path: **no** · new ledger
implementation: **no** · legacy `trace.py` replaced: **no** (untouched) · Shell
UI: **no** · API server: **no** · event bus: **no** · P9 enforcement: **no** ·
Rust/WASM: **no** · replay engine: **no** · semantic verifier: **no** ·
auto-repair: **no**. No file under `aurel_exec/`, `aurel_shell/`, `runtime.py`,
`tool_runtime.py`, `policy.py`, `sandbox.py`, `verifier.py`, or `web/`/`ui/` was
touched. `trace.py`, `contracts/trace.py`, and `contracts/projections.py` were
read-only references — **not modified**.

---

## Validation

| Gate | Command | Result | Notes |
|---|---|---|---|
| compileall | `python -m compileall src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | |
| Focused P5-A tests | `pytest tests/aurel_trace/ -q` | PASS | 40 passed |
| Legacy trace regression | `pytest tests/test_trace*.py -q` | PASS | 14 passed (trace.py untouched) |
| P4 seal-adjacent regression | `pytest tests/aurel_exec/test_exec_status_projection.py tests/aurel_exec/test_exec_p4_exit_seal.py -q` | PASS | 12 passed |
| ruff | `ruff check src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | All checks passed |
| mypy | `mypy src/agentic_runtime/aurel_trace` | PASS | 7 files, no issues |
| git status | `git status --short` | clean | after in-scope commit |

Legacy trace modules were not modified, so the broader `test_runtime*` suite was
not required (lean scope per §11).

---

## Files created

- `src/agentic_runtime/aurel_trace/__init__.py`
- `src/agentic_runtime/aurel_trace/trace_hash.py`
- `src/agentic_runtime/aurel_trace/trace_refs.py`
- `src/agentic_runtime/aurel_trace/trace_envelope.py`
- `src/agentic_runtime/aurel_trace/trace_verify.py`
- `src/agentic_runtime/aurel_trace/trace_doctrine.py`
- `src/agentic_runtime/aurel_trace/trace_inventory.py`
- `tests/aurel_trace/conftest.py`
- `tests/aurel_trace/test_trace_inventory.py`
- `tests/aurel_trace/test_trace_doctrine.py`
- `tests/aurel_trace/test_canonical_trace_envelope.py`
- `tests/aurel_trace/test_trace_refs.py`
- `tests/aurel_trace/test_trace_hash_verification.py`
- `agent/reports/P5_TRACE_A_INVENTORY_DOCTRINE_ENVELOPE_REF_HASH.md` (this report)

## Files modified (canon only)

- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`,
  `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`, `agent/TESTS.md`.

No source file outside `aurel_trace/` and no legacy trace module was modified.

---

## Remaining risks

- **Trace inventory:** the inventory is a static catalog; if new record types are
  added to `core_types`, the inventory and the envelope's supported map must be
  extended together (both derive names from the imported classes, reducing drift).
- **Envelope adapter:** only the in-memory ledger's `entry_hash = sha(prev,
  payload_hash())` invariant is verified; the `PersistentTraceLedger`'s
  canonical-JSON event-body hashing is a distinct scheme and is deferred (its
  record objects still expose the fields, so envelopes still build).
- **Refs:** the naming overlap with `contracts.trace.TraceEventRef` /
  `TraceBindingRef` is reported and namespaced, not unified — a future pack may
  reconcile the two layers.
- **Hash verification:** proves structural integrity only; PAYLOAD_HASH_MISMATCH
  vs source records and CAUSAL_REF_BROKEN detection are modeled in the finding
  vocabulary but exercised only at the envelope level in P5-A.
- **Unsupported records:** the `AurelTraceLog` canonical event form is deferred,
  not adapted.

## P5-B handoff

Deferred to P5-TRACE-B by design: `TraceVerificationReceipt`,
`TraceCheckpointReceipt`, `TraceSchemaRegistry`, `TracePayloadSchemaVersion`,
`TraceEventUpcaster`, `SubmitTraceCoverageReport`. P5-A proves the foundation;
P5-B makes verification scalable, schema-aware, and receipt-backed.

**Next recommended task:** P5-TRACE-B — Receipts / Schema Registry / Submit
Coverage Audit.
