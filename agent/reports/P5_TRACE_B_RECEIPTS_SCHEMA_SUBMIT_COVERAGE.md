# P5-TRACE-B — Receipts / Schema Registry / Submit Coverage Audit

**Date:** 2026-07-05
**Domain:** P5 — AurelTrace Spine (continues P5 after P5-TRACE-A)
**Pack:** P5-TRACE-B
**Status:** DONE — verification made portable, schema-aware, and submit-coverage-aware; no runtime change.
**Previous pack:** P5-TRACE-A — Existing Trace Inventory / Doctrine / Canonical Envelope / TraceRef / Hash Verification
**Next pack:** P5-TRACE-C — Runtime Submit Bridge / P3-P4 Binding / EvidenceRef

---

## Purpose

P5-TRACE-A made trace **structurally verifiable** (canonical envelopes, refs, and a
hash-chain verification kernel producing `TraceHashVerificationResult`). P5-TRACE-B
makes that verification **portable, schema-aware, and submit-coverage-aware** without
changing any runtime behavior. It adds three additive layers over the P5-A foundation:

1. **Verification receipts** — portable, referenceable evidence derived from an actual
   P5-A verification result (plus verified ranges and checkpoint-ready / chain-head receipts).
2. **A closed-world trace schema registry** — explicit compatibility decisions and a
   declared-only upcaster boundary; unknown schemas fail closed.
3. **A read-only submit trace coverage audit/report** — an evidence-backed inventory of
   what `AgenticRuntime.submit()` records today vs. what P5-TRACE-C must bridge.

Law: **Runtime emits. Trace canonicalizes. P5 verifies. Receipts record verification
evidence. Schema registry describes compatibility. Coverage audit reports gaps. P5-C
bridges gaps. Projections derive. Custos authorizes. Operator decides.**

---

## Roadmap coverage (P5.5–P5.7)

| Range | Title | Status | Evidence |
|---|---|---|---|
| P5.5 | Verification Receipts / Incremental Checkpoints | DONE | `trace_receipts.py`; `test_trace_receipts.py` (13 tests) |
| P5.6 | Trace Schema Registry / Upcasting | DONE | `trace_schema.py`; `test_trace_schema_registry.py` (7) + `test_trace_schema_compatibility.py` (8) |
| P5.7 | Runtime Submit Trace Ingestion Audit | DONE | `submit_coverage.py`; `test_submit_trace_coverage_audit.py` (8) + `test_submit_trace_coverage_report.py` (6) |

40 focused P5-B tests, all passing; 40 P5-A tests still passing (80 in `tests/aurel_trace`).

---

## Receipt layer proof (`trace_receipts.py`)

- **`TraceVerificationReceipt`** derives from an actual P5-A `TraceHashVerificationResult`.
  It preserves the source `status`, `verified`, and `finding_count`. `verified` is true
  **iff** the source status is `PASS`; a receipt never upgrades a non-PASS result. Only a
  PASS-derived receipt may carry `TRACE_INTEGRITY_VERIFIED`; every other receipt is
  `TRACE_BOUND`. Proven: a real PASS chain over the demo ledger yields an integrity-verified
  receipt; a tampered-payload FAIL result yields a `TRACE_BOUND` receipt that does not upgrade.
- **Deterministic receipt hash.** `receipt_hash` is stable canonical JSON with sorted keys
  over the verification material; the nondeterministic `created_at` is metadata only and is
  **excluded** from hash material (proven: two receipts with different `created_at` share the
  same hash). Changing the chain head changes the receipt hash (proven).
- **`VerifiedTraceRange`** represents a verified segment (`start_index`/`end_index`/`end_hash`/
  `checked_count`); it enforces `start_index <= end_index` and `checked_count == end - start + 1`,
  and its identity folds in `end_hash`. It is evidence of scope — not replay state, state
  restore, or a workflow fork.
- **`TraceCheckpointReceipt`** is checkpoint-ready proof over a PASS receipt + range. Locked
  booleans `is_replay_checkpoint` / `is_snapshot_restore` / `enables_workflow_fork` are
  unconstructible True — it does not claim replay/restore and does not itself implement
  incremental verification. Building one from a FAIL receipt raises.
- **`TraceChainHeadReceipt`** records the verified `event_count` and `chain_head_hash` for
  quick integrity status; its `receipt_hash` changes when either the event count or the head
  hash changes (proven). It does not replace the ledger.
- No receipt claims semantic/business/policy/production correctness, and no `TRACE_VERIFIED`
  label exists to claim.

---

## Schema layer proof (`trace_schema.py`)

- **`TraceSchemaDescriptor`** describes one schema (id/name/version/record type + required/
  optional/hash/previous-hash/payload fields + status). **`TraceSchemaStatus`**:
  SUPPORTED / PARTIAL / DEPRECATED / UNSUPPORTED / UNKNOWN.
- **`TraceSchemaRegistry`** is **closed-world** (`closed_world` locked True;
  `silent_fallback_used` / `is_migration_engine` unconstructible True).
  `build_default_trace_schema_registry()` seeds descriptors directly from the P5-A
  `ExistingTraceInventory`: the nine `core_types` ledger record types become SUPPORTED
  descriptors, and the deferred `contracts.trace.AurelTraceLog` form becomes an UNSUPPORTED
  descriptor — so the two layers cannot drift. Proven: supported/unsupported descriptor sets
  equal the inventory's.
- **`TraceSchemaCompatibilityDecision`** (`decision` ∈ COMPATIBLE / COMPATIBLE_WITH_WARNINGS /
  REQUIRES_UPCASTER / UNSUPPORTED / UNKNOWN / ERROR). `registry.decide(...)`:
  known SUPPORTED → COMPATIBLE (version mismatch → COMPATIBLE_WITH_WARNINGS); DEPRECATED →
  REQUIRES_UPCASTER referencing a declared-only upcaster; UNSUPPORTED → UNSUPPORTED with reason;
  **unknown record type → UNKNOWN with reason — no silent fallback to the default schema**
  (proven even when the caller passes the default version). Every non-COMPATIBLE decision must
  carry a non-empty reason (enforced structurally).
- **`TraceEventUpcasterContract`** is the declared-only boundary. `TraceUpcasterStatus` default
  is `DECLARED_ONLY`; `SUPPORTED` is unconstructible in P5-B; `rewrites_records` /
  `migrates_records` are unconstructible True. The registry is a schema contract layer, **not**
  a migration engine, and rewrites no historical records.

---

## Submit coverage layer proof (`submit_coverage.py`)

- **`SubmitEvidenceRequirementKind`** enumerates all 14 evidence kinds
  (`COMMAND_ENVELOPE_RECORDED` … `ERROR_RECORDED`). **`SubmitCoverageStatus`**:
  COVERED / PARTIAL / MISSING / UNSUPPORTED / UNKNOWN. Every **`SubmitEvidenceRequirement`**
  names an `owner_pack` and does not create/mutate any trace.
- **`SubmitTraceCoverageAudit`** is read-only. Locked booleans `modifies_submit` /
  `adds_trace_append` / `is_bridge` are unconstructible True. The audit is derived from a
  documented evidence map grounded in a read-only inspection of the submit path (it performs
  **no** ledger writes and imports **no** runtime side-effect path). `build_submit_trace_coverage_audit`
  covers all 14 kinds deterministically.
- The evidence map reflects what `submit()` actually records: it appends one hash-chained
  `StateTransitionRecord` (carrying `before_state_hash`, `after_state_hash`, `observation_hash`,
  `command_hash`, `policy_verdict`, `verifier_result`) plus discrete `ApprovalReceiptRecord` /
  `BudgetDecisionRecord` / `SandboxViolationRecord` / `ToolContractViolationRecord` /
  `PlanningFailureRecord` records on their paths.

**Coverage classification (14 requirements; coverage_percent = required-covered / required-for-integrity = 7/9 = 77.78%):**

- **Covered (7)** — discrete or first-class transition evidence:
  `SANDBOX_BEFORE_HASH_RECORDED`, `SANDBOX_AFTER_HASH_RECORDED`, `VERIFIER_RESULT_RECORDED`,
  `TOOL_RESULT_RECORDED`, `TRACE_APPEND_RECORDED`, `HITL_DECISION_RECORDED` (ApprovalReceiptRecord),
  `BUDGET_DECISION_RECORDED` (BudgetDecisionRecord).
- **Partial (5)** — present only as a field/hash inside the transition, not a discrete,
  independently referenceable record: `COMMAND_ENVELOPE_RECORDED` (command_hash),
  `POLICY_DECISION_RECORDED` (policy_verdict), `TOOL_INVOCATION_RECORDED` (command_hash),
  `OBSERVATION_RECORDED` (observation_hash), `ERROR_RECORDED` (some error paths only).
- **Missing (2)** — no discrete record on the observed path: `ROLLBACK_RESULT_RECORDED`
  (rollback runs but is recorded only as observation/verifier evidence),
  `MEMORY_WRITE_RECORDED` (`MemoryGovernanceRecord` exists in core_types but submit does not
  emit a discrete memory-write record on the observed path).
- **Unsupported:** none in the default map.

- **`SubmitTraceCoverageReport`** lists covered/partial/missing/unsupported and turns every
  partial/missing/unsupported requirement into a **`SubmitTraceGap`** with a P5-TRACE-C
  recommendation. It cannot claim complete coverage while any required evidence is partial or
  missing (`claims_complete_coverage=True` over a required gap raises). `coverage_percent` is
  deterministic and honestly below 100%.

---

## P5-C handoff recommendations

P5-TRACE-C should bridge submit trace ingestion by binding **discrete, referenceable
evidence records/refs** during `submit()` for the gap kinds above — primarily a discrete
command-envelope evidence ref and a discrete policy-decision evidence ref (both currently
PARTIAL and required for integrity), plus discrete tool-invocation, observation, rollback,
memory-write, and error evidence refs (required for future trace verification). P5-C should
also introduce the `EvidenceRef` object model and the P3/P4 trace-binding bridge. P5-C must
**not** weaken P5-A verification semantics, must not treat a receipt as ledger truth or
semantic correctness, and must keep replay, trace CLI, projection feed, Shell UI/API, P9
enforcement, and Rust/WASM UNAVAILABLE (those remain later-pack owners).

---

## Truth label posture

- **LIVE** — receipt contracts, verified-range/checkpoint/chain-head contracts, schema
  descriptors/registry/compatibility decisions, upcaster contracts, submit evidence
  requirements, coverage audit/report.
- **TRACE_BOUND** — a receipt derived from a non-PASS result; a verified range; a checkpoint /
  chain-head receipt (the range/head carries whatever proof exists).
- **TRACE_INTEGRITY_VERIFIED** — only a receipt derived from an actual PASS
  `TraceHashVerificationResult`.
- **TRACE_VERIFIED** — **not claimed** (no such label exists; a receipt existing does not make
  it so).
- **UNAVAILABLE** — runtime submit bridge, trace CLI, projection feed, replay, P9 enforcement,
  Shell UI/API/event bus, Rust/WASM, schema migration/upcasting execution.
- **ERROR** — reserved for inconsistent receipt/schema/audit state.

---

## Boundary / side-effect proof

`runtime.submit` modified: **no** · trace append hook added: **no** · submit bridge implemented:
**no** · P3 binding bridge: **no** · P4 binding bridge: **no** · EvidenceRef full model: **no** ·
trace CLI: **no** · projection feed: **no** · Shell UI: **no** · API server: **no** · event bus:
**no** · P9 enforcement: **no** · Rust/WASM: **no** · replay engine: **no** · schema migration
engine: **no** · new ledger: **no**. Only `src/agentic_runtime/aurel_trace/` (three new modules
+ `__init__.py` exports) and `tests/aurel_trace/` (five new test files) were touched in source;
no file under `aurel_exec/`, `aurel_shell/`, `runtime.py`, `tool_runtime.py`, `policy.py`,
`sandbox.py`, `verifier.py`, `trace.py`, or `web/`/`ui/` was modified. The coverage audit
imports only stable P5-A public objects and `core_types`; it performs no ledger writes.

---

## Validation

| Gate | Command | Result | Notes |
|---|---|---|---|
| compileall | `python -m compileall src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | |
| Focused P5-B tests | `pytest tests/aurel_trace/test_trace_receipts.py test_trace_schema_registry.py test_trace_schema_compatibility.py test_submit_trace_coverage_audit.py test_submit_trace_coverage_report.py -q` | PASS | 40 passed |
| P5-A regression | `pytest tests/aurel_trace/test_trace_hash_verification.py test_canonical_trace_envelope.py test_trace_refs.py -q` | PASS | within full run |
| Legacy trace regression | `pytest tests/test_trace*.py -q` | PASS | 41 passed (with above); `trace.py` untouched |
| Full aurel_trace | `pytest tests/aurel_trace -q` | PASS | 80 passed |
| ruff | `ruff check src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | All checks passed |
| mypy | `mypy src/agentic_runtime/aurel_trace` | PASS | 10 source files, no issues |
| git status | `git status --short` | clean | after in-scope commit |

Legacy `trace.py` / `runtime.py` were not modified, so the broader `test_runtime*` suite was
not required (lean scope per the dispatch §11).

---

## Files created

- `src/agentic_runtime/aurel_trace/trace_receipts.py`
- `src/agentic_runtime/aurel_trace/trace_schema.py`
- `src/agentic_runtime/aurel_trace/submit_coverage.py`
- `tests/aurel_trace/test_trace_receipts.py`
- `tests/aurel_trace/test_trace_schema_registry.py`
- `tests/aurel_trace/test_trace_schema_compatibility.py`
- `tests/aurel_trace/test_submit_trace_coverage_audit.py`
- `tests/aurel_trace/test_submit_trace_coverage_report.py`
- `agent/reports/P5_TRACE_B_RECEIPTS_SCHEMA_SUBMIT_COVERAGE.md` (this report)

## Files modified

- `src/agentic_runtime/aurel_trace/__init__.py` (exports only)
- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/ARCHITECTURE.md`,
  `agent/DECISIONS.md`, `agent/TESTS.md` (canon)

---

## Remaining risks

- **Receipts:** a receipt proves that a verification result was produced for a scope and chain
  head — it is not ledger truth and not semantic correctness. This is enforced structurally,
  but downstream consumers must not over-read a `TRACE_INTEGRITY_VERIFIED` receipt.
- **Schema registry:** descriptors are seeded from the P5-A inventory; if new `core_types`
  record types are added, the inventory and the registry seed must extend together (both derive
  names from the shared inventory, reducing drift). The `AurelTraceLog` form remains UNSUPPORTED,
  not adapted.
- **Submit coverage:** the audit is a deterministic mapping grounded in a read-only inspection,
  not a live per-run trace diff. If `submit()` changes which records it emits, the evidence map
  must be revisited. Several kinds are honestly PARTIAL/MISSING — that is the P5-C handoff, not
  a defect.
- **P5-C handoff:** the gap list is explicit and machine-readable (`SubmitTraceGap` +
  `p5c_recommendation`), so P5-C bridging can be evidence-driven.

**Next recommended task:** P5-TRACE-C — Runtime Submit Bridge / P3-P4 Binding / EvidenceRef.
