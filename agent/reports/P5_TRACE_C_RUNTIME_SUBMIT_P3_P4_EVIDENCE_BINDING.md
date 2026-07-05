# P5-TRACE-C — Runtime Submit Bridge / P3-P4 Binding / EvidenceRef

**Date:** 2026-07-05
**Domain:** P5 — AurelTrace Spine (continues P5 after P5-TRACE-A and P5-TRACE-B)
**Pack:** P5-TRACE-C
**Status:** DONE — runtime/P3/P4 artifacts bound to evidence refs; no runtime mutation, no execution.
**Previous pack:** P5-TRACE-B — Receipts / Schema Registry / Submit Coverage Audit
**Next pack:** P5-TRACE-D — TRACE_VERIFIED Resolver / Query Read Model / CLI

---

## Purpose

P5-TRACE-A made trace structurally verifiable; P5-TRACE-B made verification portable,
schema-aware, and submit-coverage-aware, handing forward an explicit gap list.
P5-TRACE-C turns those gaps into **explicit trace-binding and evidence-reference contracts**
for runtime-submit, P3 (AurelFlow control-plane), and P4 (AurelExec) artifacts — the input
P5-TRACE-D's resolver will consume. It adds:

1. An **EvidenceRef object model** (`EvidenceKind` / `EvidenceStatus` / `EvidenceRef`).
2. A **runtime submit trace bridge** that maps the P5-B `SubmitTraceCoverageReport` into a
   `RuntimeSubmitTraceBinding` of evidence refs, preserving gaps.
3. **P3TraceBinding** and **P4TraceBinding** over closed-world source-object-kind descriptors.

Law: **Runtime emits. P5 adapts. Bindings reference. EvidenceRefs identify evidence.
P5-D resolves verification. Custos authorizes. Operator decides.**

This pack is adapter/read-model only. Binding is not execution; an `EvidenceRef` is not
verification; trace-bound is not `TRACE_VERIFIED`; a COMPLETE binding is not `TRACE_VERIFIED`.
Missing evidence stays explicit — it is P5-TRACE-D handoff material, not a defect.

---

## Roadmap coverage (P5.8–P5.10)

| Range | Title | Status | Evidence |
|---|---|---|---|
| P5.8 | Runtime Submit Trace Canonical Bridge | DONE | `runtime_submit_bridge.py`; `test_runtime_submit_trace_bridge.py` (11) |
| P5.9 | P3/P4 Trace Binding Bridge | DONE | `p3_binding.py` + `p4_binding.py`; `test_p3_trace_binding.py` (6) + `test_p4_trace_binding.py` (6) |
| P5.10 | EvidenceRef / Proof Object Model | DONE | `evidence_ref.py`; `test_evidence_refs.py` (9) + `test_submit_bridge_boundaries.py` (3) |

35 focused P5-C tests, all passing; 80 P5-A/B tests still passing (115 in `tests/aurel_trace`).

---

## Repo truth vs prompt names (canon rule: repo truth wins)

To be **import-safe and side-effect-free by construction**, the bindings take a **closed-world
source-object-kind enum + a string `source_object_id`** — they do **not** import `aurel_flow` /
`aurel_exec` and do **not** accept live objects. The enum values name the real repo classes:

- **P3** (`aurel_flow`): `SCHEDULING_INTENT`→`SchedulingIntent`,
  `WORKFLOW_ATOMIC_UNIT`→`WorkflowAtomicUnit`, `FLOW_STATE_PROJECTION`→`FlowStateProjection`,
  `READY_CANDIDATE`→`ExecutionRequestCandidateSurface` (no `ReadyCandidate` class),
  `FLOW_SEAL_REPORT`→`P3DomainSeal` (no `FlowSealReport` class).
- **P4** (`aurel_exec`): `EXEC_ADMISSION_DECISION`→`ExecAdmissionDecision`,
  `EXECUTION_LEASE`→`ExecutionLease`, `EXEC_JOB`→`ExecJob`, `EXECUTION_ATTEMPT`→`ExecutionAttempt`,
  `EXECUTION_OUTCOME`→`ExecutionOutcome`, `EXECUTION_FAILURE`→`FailureClassification`
  (no `ExecutionFailure` class), `RECOVERY_PLAN`→`BoundedRecoveryPlan` (no `RecoveryPlan` class),
  `BACKPRESSURE_DECISION`→`BackpressureDecision`, `EXEC_BENCH_SNAPSHOT`→`ExecBenchSnapshot`.

Because no runtime/P3/P4 module is imported, "does not execute workflow/job/dispatch" is
structural (proven by the boundary source-sweep), not merely tested behaviorally.

---

## EvidenceRef layer proof (`evidence_ref.py`)

- **`EvidenceKind`** is closed-world: the 11 prompt-required runtime kinds plus `ROLLBACK_EVIDENCE`
  and `OBSERVATION_EVIDENCE` (so all 14 P5-B `SubmitEvidenceRequirementKind`s map 1:1 without
  coercion), plus the P3 (3) and P4 (9) evidence kinds.
- **`EvidenceStatus`**: PRESENT / MISSING / PARTIAL / UNSUPPORTED / TRACE_BOUND /
  TRACE_INTEGRITY_VERIFIED / ERROR.
- **`EvidenceRef`** references evidence; it does not create evidence, mutate trace, or authorize.
  Its `evidence_ref_id` is deterministic over `(kind, domain, object_id)` (proven: same input →
  same id, different source → different id). A `MISSING`/`UNSUPPORTED` ref **must** carry a
  `missing_reason` (enforced). The `TRACE_INTEGRITY_VERIFIED` truth label is constructible **only**
  when backed by a `verification_receipt_id` (proven: a hand-built ref without a receipt raises);
  `make_evidence_ref` promotes to `TRACE_INTEGRITY_VERIFIED` only when a receipt id is supplied,
  otherwise stays `TRACE_BOUND`. `PRESENT`/`TRACE_BOUND` do not imply verification. There is **no**
  `TRACE_VERIFIED` label (asserted). `evidence_ref_has_no_authority` returns True — an EvidenceRef
  has no authority-granting field and the truth vocabulary has no authority member.
- `make_missing_evidence_ref` fails closed on an unknown kind and requires a reason.

---

## Runtime submit binding layer proof (`runtime_submit_bridge.py`)

- **`RuntimeSubmitTraceBinding`** holds 13 named optional evidence slots
  (`command_evidence_ref` … `error_evidence_ref`), a generic `evidence_refs` tuple, a
  `coverage_status`, and explicit `missing_evidence`/`partial_evidence`. Locked booleans make
  `submits_command`/`calls_tool`/`appends_trace`/`authorizes`/`trace_verified` unconstructible True.
- **`build_runtime_submit_trace_binding`** consumes the P5-B `SubmitTraceCoverageReport`: each of
  the 14 requirements becomes one evidence ref via a total `SubmitEvidenceRequirementKind →
  EvidenceKind` map, with status mapped from `SubmitCoverageStatus` (COVERED→PRESENT,
  PARTIAL→PARTIAL, MISSING→MISSING+reason, UNSUPPORTED→UNSUPPORTED, UNKNOWN→ERROR). Against the
  real P5-B report the binding is honestly **PARTIAL** — 7 present, **5 partial**
  (command, policy, tool-invocation, observation, error) and **2 missing** (rollback, memory-write),
  each missing ref carrying a reason. A COMPLETE coverage status (only when every requirement is
  PRESENT) does **not** set any verified truth label (proven with an all-covered fixture).
- Supplying `receipt_ids` promotes a present requirement's ref to `TRACE_INTEGRITY_VERIFIED`
  (proven) — the only route to that label, and never a broad `TRACE_VERIFIED` claim.
- **`RuntimeSubmitTraceBridge`** is a stateless adapter holding no runtime handle;
  `calls_runtime_submit`/`calls_tool_dispatch`/`appends_trace` are unconstructible True.
  Helpers: `binding_from_submit_coverage_report`, `missing_evidence_from_coverage_report`,
  `runtime_submit_binding_status`, `summarize_binding_coverage` (read-only
  `TraceBindingCoverageSummary`).

---

## P3 binding layer proof (`p3_binding.py`)

- **`P3SourceObjectKind`** (closed-world) + **`P3TraceBinding`** (locked
  `executes_workflow`/`mutates_scheduling`/`appends_trace` unconstructible True).
- **`build_p3_trace_binding`**: a supported kind with no supplied evidence yields a binding whose
  single expected evidence ref is `MISSING` (coverage MISSING — evidence stays explicit); a
  supported kind with a PRESENT evidence ref is COMPLETE (but still `TRACE_BOUND`); an
  unknown/unsupported string fails closed → `UNSUPPORTED` coverage with a reason (proven). An empty
  `source_object_id` raises. Default evidence-kind mapping: scheduling→`P3_SCHEDULING_EVIDENCE`,
  workflow→`P3_WORKFLOW_EVIDENCE`, projection/seal→`P3_PROJECTION_EVIDENCE`.

---

## P4 binding layer proof (`p4_binding.py`)

- **`P4SourceObjectKind`** (closed-world) + **`P4TraceBinding`** (locked
  `executes_job`/`triggers_retry`/`triggers_recovery`/`dispatches_worker`/`appends_trace`
  unconstructible True).
- **`build_p4_trace_binding`**: same shape as P3 — supported kind → binding (MISSING until evidence
  supplied, COMPLETE with a PRESENT ref, still `TRACE_BOUND`); unsupported string fails closed →
  `UNSUPPORTED` with a reason (proven). Default mapping: admission→`P4_ADMISSION_EVIDENCE`,
  lease→`P4_LEASE_EVIDENCE`, job→`P4_JOB_EVIDENCE`, attempt→`P4_ATTEMPT_EVIDENCE`,
  outcome→`P4_OUTCOME_EVIDENCE`, failure/recovery→`P4_FAILURE_EVIDENCE`,
  backpressure→`P4_BACKPRESSURE_EVIDENCE`, bench→`P4_BENCH_EVIDENCE`.

---

## Coverage summary

`TraceBindingCoverageStatus` = COMPLETE / PARTIAL / MISSING / UNSUPPORTED / ERROR (shared by all
three binding layers). Coverage is derived from the evidence refs: COMPLETE iff every ref is
present, MISSING iff none present, else PARTIAL; ERROR if any ref is ERROR. **COMPLETE does not
mean `TRACE_VERIFIED`** — the binding truth label stays `TRACE_BOUND` regardless of coverage.
PARTIAL/MISSING bindings list their missing/partial evidence; UNSUPPORTED carries a reason.

---

## Truth label posture

- **LIVE** — the bridge object, coverage summaries, and the evidence/binding contracts as
  contracts.
- **TRACE_BOUND** — every runtime/P3/P4 binding and every evidence ref not backed by a receipt.
- **TRACE_INTEGRITY_VERIFIED** — only an evidence ref backed by an explicit P5-A/B verification
  receipt id.
- **TRACE_VERIFIED** — **unavailable** until the P5-TRACE-D resolver; no such label exists in the
  vocabulary and none was added.
- **UNAVAILABLE** — TRACE_VERIFIED resolver, trace CLI, projection feed, replay, P9 enforcement,
  Shell UI/API, Rust/WASM.
- **ERROR** — invalid binding, missing required evidence surfaced as ERROR status, or an
  UNKNOWN-coverage requirement.

---

## Boundary / side-effect proof

`runtime.submit` modified: **no** · `runtime.submit` called: **no** · trace append hook added:
**no** · `ToolRuntime.dispatch` called: **no** · new execution path: **no** · P3 workflow
execution: **no** · P3 scheduling mutation: **no** · P4 job execution: **no** · P4 retry/recovery:
**no** · P4 worker dispatch: **no** · EvidenceRef authority: **no** · EvidenceRef semantic
correctness: **no** · trace CLI: **no** · projection feed: **no** · Shell UI: **no** · API server:
**no** · event bus: **no** · P9 enforcement: **no** · Rust/WASM: **no** · replay engine: **no** ·
new ledger: **no**.

The four new modules import **downward only** — from P5-A/B public objects and `trace_hash`; they
import **no** `runtime`, `aurel_exec`, `aurel_flow`, `tool_runtime`, `sandbox`, `policy`, or
`verifier` module. `test_submit_bridge_boundaries.py` proves this structurally: an `ast`-based
sweep confirms the binding modules contain no `AgenticRuntime` / `ToolRuntime` / `.submit(` /
`.dispatch(` / `trace.append` / `_append_transition` / `record_transition` call fragments in
executable code and import only relative aurel_trace or stdlib modules. Only
`src/agentic_runtime/aurel_trace/` (four new modules + `__init__.py` exports) and
`tests/aurel_trace/` (five new test files) were touched in source; no file under `aurel_exec/`,
`aurel_flow/`, `aurel_shell/`, `runtime.py`, `tool_runtime.py`, `policy.py`, `sandbox.py`,
`verifier.py`, `trace.py`, or `web/`/`ui/` was modified.

---

## P5-D handoff recommendations

P5-TRACE-D (TRACE_VERIFIED resolver / query read model / CLI) should consume these bindings and
evidence refs: resolve a `TRACE_VERIFIED` verdict per binding by requiring that every
required-for-integrity evidence ref be backed by a PASS P5-A/B verification receipt (the
`verification_receipt_id` slot already exists on `EvidenceRef`); expose a read-only query read
model over runtime/P3/P4 bindings and their coverage; and add the operator trace-status CLI.
P5-D must **not** weaken P5-A/B semantics, must not treat a binding or evidence ref as authority
or semantic correctness, and must keep replay, projection feed, Shell UI/API, P9, and Rust/WASM
unavailable.

---

## Validation

| Gate | Command | Result | Notes |
|---|---|---|---|
| compileall | `python -m compileall src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | |
| Focused P5-C tests | `pytest test_evidence_refs.py test_runtime_submit_trace_bridge.py test_p3_trace_binding.py test_p4_trace_binding.py test_submit_bridge_boundaries.py -q` | PASS | 35 passed |
| P5-A/B + legacy + P4 projection | `pytest tests/aurel_trace tests/test_trace*.py tests/aurel_exec/test_exec_status_projection.py -q` | PASS | 135 passed |
| ruff | `ruff check src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | All checks passed |
| mypy | `mypy src/agentic_runtime/aurel_trace` | PASS | 14 source files, no issues |
| git status | `git status --short` | clean | after in-scope commit |

No runtime/P3/P4 runtime module was modified, so the broader `test_runtime*` / full `aurel_exec`
suites were not required (lean scope per the dispatch §11).

---

## Files created

- `src/agentic_runtime/aurel_trace/evidence_ref.py`
- `src/agentic_runtime/aurel_trace/runtime_submit_bridge.py`
- `src/agentic_runtime/aurel_trace/p3_binding.py`
- `src/agentic_runtime/aurel_trace/p4_binding.py`
- `tests/aurel_trace/test_evidence_refs.py`
- `tests/aurel_trace/test_runtime_submit_trace_bridge.py`
- `tests/aurel_trace/test_p3_trace_binding.py`
- `tests/aurel_trace/test_p4_trace_binding.py`
- `tests/aurel_trace/test_submit_bridge_boundaries.py`
- `agent/reports/P5_TRACE_C_RUNTIME_SUBMIT_P3_P4_EVIDENCE_BINDING.md` (this report)

## Files modified

- `src/agentic_runtime/aurel_trace/__init__.py` (exports only)
- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/ARCHITECTURE.md`,
  `agent/DECISIONS.md`, `agent/TESTS.md` (canon)

---

## Remaining risks

- **EvidenceRef:** an EvidenceRef references or expects evidence; a `PRESENT` ref is not verified
  and a receipt-backed `TRACE_INTEGRITY_VERIFIED` ref proves only hash-chain integrity, not
  semantic correctness. Enforced structurally; downstream consumers must not over-read it.
- **Runtime submit binding:** the binding derives from the P5-B coverage report, which is a
  deterministic documented mapping, not a live per-run trace diff. It is honestly PARTIAL — the
  2 missing + 5 partial kinds are the P5-D bridge targets, not defects.
- **P3/P4 bindings:** they use closed-world kind/id descriptors rather than live objects, so they
  are decoupled from the exact P3/P4 class shapes (a deliberate import-safety choice); the enum→
  class mapping is documented and must be revisited if those classes are renamed.
- **P5-D handoff:** the resolver has a concrete surface — evidence refs with a
  `verification_receipt_id` slot and per-binding coverage — to drive a real `TRACE_VERIFIED`
  verdict without touching runtime.

**Next recommended task:** P5-TRACE-D — TRACE_VERIFIED Resolver / Query Read Model / CLI.
