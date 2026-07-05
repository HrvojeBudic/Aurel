# P5-TRACE-D — TRACE_VERIFIED Resolver / Query Read Model / CLI

**Date:** 2026-07-05
**Domain:** P5 — AurelTrace Spine (continues P5 after P5-TRACE-A/B/C)
**Pack:** P5-TRACE-D
**Status:** DONE — the single, strict TRACE_VERIFIED resolver + read-only query model + trace CLI.
**Previous pack:** P5-TRACE-C — Runtime Submit Bridge / P3-P4 Binding / EvidenceRef
**Next pack:** P5-TRACE-E — Projection Feed / Golden Thread / Replay Readiness

---

## Purpose

Across P5-TRACE-A/B/C the truth vocabulary `TraceTruthLabel` deliberately stopped at
`TRACE_INTEGRITY_VERIFIED` — no layer could mint a broad `TRACE_VERIFIED` verdict.
P5-TRACE-D adds the **first and only `TRACE_VERIFIED` gate**: a resolver that combines the A/B/C
evidence (hash verification, receipts, schema decisions, evidence refs, bindings, findings) into
one structured decision; a read-only query model that formats those decisions; and read-only
`trace` CLI commands. The central law: **`TRACE_VERIFIED` is a resolver decision, never a label
any object self-assigns.** Hash PASS alone, a receipt alone, an `EvidenceRef` alone, and a
COMPLETE binding alone are each *not enough*.

Law: **Runtime emits. P5 adapts. Bindings reference. EvidenceRefs identify evidence. Resolver
decides TRACE_VERIFIED. Query model reflects resolver decisions. CLI reads query/resolver output.
Custos authorizes. Operator decides.**

`TRACE_VERIFIED` is added **only** as a member of the resolver-local `TraceVerificationStatus`
enum in `trace_resolver.py` — **not** added to `TraceTruthLabel`. The A/B/C vocabulary is
untouched, so no existing object can carry a `TRACE_VERIFIED` label; only a resolver decision
holds the status.

---

## Roadmap coverage (P5.11–P5.13)

| Range | Title | Status | Evidence |
|---|---|---|---|
| P5.11 | TRACE_VERIFIED Resolver | DONE | `trace_resolver.py`; `test_trace_verified_resolver.py` (10) + `test_trace_verified_overclaim_guard.py` (5) |
| P5.12 | Trace Query Read Model | DONE | `trace_query.py`; `test_trace_query_read_model.py` (5) |
| P5.13 | Trace CLI | DONE | `cli_modules/trace_commands.py` + `cli.py`; `test_trace_cli_commands.py` (6) + `test_trace_cli_read_only_boundaries.py` (3) |

29 focused P5-D tests, all passing; A/B/C + legacy trace regression green (158 in
`tests/aurel_trace` + legacy).

---

## Resolver proof (`trace_resolver.py`)

- **`TraceVerificationTargetKind`** (closed-world): TRACE_RUN, TRACE_EVENT, TRACE_BINDING,
  EVIDENCE_SET, RUNTIME_SUBMIT_BINDING, P3_BINDING, P4_BINDING, CHAIN_HEAD. Unknown kind fails
  closed → ERROR with reason.
- **`TraceVerificationStatus`**: TRACE_VERIFIED, TRACE_BOUND, PARTIAL, UNAVAILABLE, DENIED, ERROR.
- **`TraceVerificationDecision`** (frozen): deterministic `decision_id`, `verified` **iff** status
  is TRACE_VERIFIED (enforced), explicit `blocking_findings`/`warnings`/`required_evidence`/
  `missing_evidence`, and source id tuples (receipts/bindings/evidence refs/schema decisions). A
  TRACE_VERIFIED decision is unconstructible with any blocking finding or missing evidence.
- **`TraceVerifiedResolver`** (stateless; `mutates`/`appends_trace`/`executes` unconstructible)
  with pure helpers `resolve_trace_target` / `resolve_trace_run` / `resolve_chain_head` /
  `resolve_trace_event` / `resolve_evidence_set` / `resolve_runtime_submit_binding` /
  `resolve_p3_binding` / `resolve_p4_binding`.

**The gate law (deterministic, fail-closed order):** unknown target/empty id → ERROR; blocking
findings (severity ERROR/CRITICAL) → DENIED; schema UNKNOWN/UNSUPPORTED/REQUIRES_UPCASTER/ERROR →
DENIED (COMPATIBLE_WITH_WARNINGS adds a warning); any evidence ref in ERROR → ERROR; failing
receipt/hash → DENIED; no integrity input → UNAVAILABLE; PASS hash but no receipt → TRACE_BOUND
("hash PASS alone is not enough"); required evidence missing → PARTIAL; binding coverage not
COMPLETE → PARTIAL; PASS receipt but nothing corroborates (no required evidence and no binding) →
TRACE_BOUND ("receipt alone is not enough"); **all gates satisfied → TRACE_VERIFIED**.

## TRACE_VERIFIED overclaim-guard proof

Proven negatively (`test_trace_verified_overclaim_guard.py`): hash PASS alone → TRACE_BOUND;
receipt alone → TRACE_BOUND; `EvidenceRef` PRESENT alone (no integrity proof) → UNAVAILABLE;
`TraceBindingCoverageStatus.COMPLETE` alone (no integrity proof) → UNAVAILABLE; UNKNOWN schema
decision → DENIED. Each returns a downgraded status; none returns TRACE_VERIFIED. Proven
positively: a PASS receipt + all required evidence PRESENT (receipt-backed) + no findings →
TRACE_VERIFIED with `verified=True`. `TRACE_VERIFIED` is producible **only** through the resolver.

---

## Query read model proof (`trace_query.py`)

- **`TraceQueryReadModel`** (frozen; `decides_verification`/`mutates` unconstructible True) holds a
  fixed tuple of resolver decisions and formats them. Each `summarize_*` method **copies**
  `status`/`verified` verbatim from a decision — it cannot upgrade a TRACE_BOUND/PARTIAL decision
  to TRACE_VERIFIED (proven).
- Summaries — `TraceRunSummary`, `TraceEventSummary`, `TraceBindingSummary`, `TraceEvidenceSummary`,
  `TraceVerificationSummary`, `TraceAuditSummary` — preserve missing evidence, blocking findings,
  warnings, and the resolver `reason`. `TraceAuditSummary` counts per status deterministically.

---

## CLI proof (`cli_modules/trace_commands.py` + `cli.py`)

- Read-only commands registered under `trace`: `trace status`, `trace verify`,
  `trace inspect --target <id>`, `trace audit` (each mirrors the `exec status` registration idiom;
  `--json` on status/verify/audit). All return exit 0 and produce resolver-backed output over a
  **DEV_FIXTURE** demo substrate (`trace_demo.py`).
- The demo runs the real P5-A→P5-D pipeline over an isolated in-memory demo ledger and honestly
  yields a mix: the fully-corroborated **CHAIN_HEAD** target resolves **TRACE_VERIFIED**, while the
  **RUNTIME_SUBMIT_BINDING** target (real P5-B coverage, incomplete evidence) resolves **PARTIAL**
  with its missing evidence (COMMAND/ROLLBACK/MEMORY) listed. A test cross-checks the CLI output
  against the resolver decisions: the CLI prints TRACE_VERIFIED only for a resolver-verified target
  and `verified=False` for every other, and at least one target is honestly not verified.
- No mutating subcommands exist; `trace inspect` without `--target` returns a usage error (exit 2),
  and an unknown target returns honest UNAVAILABLE (exit 0).

## Read-only boundary proof

`test_trace_cli_read_only_boundaries.py` ast-sweeps the modules: `trace_resolver.py` and
`trace_query.py` are **pure** — no `AgenticRuntime`/`ToolRuntime`/`.submit(`/`.dispatch(`/
`trace.append`/`_append_transition`/`.rollback(` fragments and no import of
runtime/tool_runtime/policy/sandbox/verifier/memory/aurel_exec/aurel_flow/aurel_shell. The CLI
module `trace_commands.py` contains no mutating operation (`runtime.submit`/`.dispatch(`/
`trace.append`/repair/replay/approve/memory_write/file-write). `trace_demo.py` (DEV_FIXTURE)
builds an isolated in-memory ledger but never calls `runtime.submit`/dispatch and writes no files.

---

## Truth label posture

- **LIVE** — resolver, query model, CLI commands, and all decision/summary contracts.
- **TRACE_VERIFIED** — a resolver decision status only (never a `TraceTruthLabel`); produced solely
  when every gate passes.
- **TRACE_BOUND** — integrity proven but not corroborated (hash-only, or receipt-only).
- **PARTIAL** — integrity proven but required evidence missing or binding coverage incomplete.
- **UNAVAILABLE** — no integrity proof supplied; and the deferred substrate (projection feed,
  Shell UI, API/event bus, replay, P9, Rust/WASM, semantic/business/policy correctness).
- **DENIED** — blocking findings, failing integrity proof, or unsupported/unknown schema.
- **ERROR** — unknown target kind, empty id, or an evidence ref in ERROR state.

---

## Boundary / side-effect proof

runtime.submit modified/called: **no** · trace append: **no** · trace repair: **no** · trace
mutation: **no** · `ToolRuntime.dispatch`: **no** · policy enforcement: **no** · approval
activation: **no** · memory write: **no** · workflow/job execution: **no** · retry/recovery:
**no** · replay: **no** · delete: **no** · Shell UI / API / event bus: **no** · P9 enforcement:
**no** · Rust/WASM: **no** · new ledger: **no** · semantic/business/policy correctness claim:
**no**. `TRACE_VERIFIED` was **not** added to `TraceTruthLabel`. The only edit outside
`aurel_trace/` and `cli_modules/` is the additive `trace` subcommand registration in `cli.py`;
`runtime.py`, `tool_runtime.py`, `policy.py`, `sandbox.py`, `verifier.py`, `memory*`, `trace.py`,
`aurel_exec/`, `aurel_flow/`, `aurel_shell/`, and web/ui were not modified.

---

## Validation

| Gate | Command | Result | Notes |
|---|---|---|---|
| compileall | `python -m compileall src/agentic_runtime/aurel_trace src/agentic_runtime/cli_modules tests/aurel_trace` | PASS | |
| Focused P5-D tests | `pytest test_trace_verified_resolver.py test_trace_verified_overclaim_guard.py test_trace_query_read_model.py test_trace_cli_commands.py test_trace_cli_read_only_boundaries.py -q` | PASS | 29 passed |
| A/B/C + legacy regression | `pytest tests/aurel_trace tests/test_trace*.py -q` | PASS | 158 passed |
| CLI smoke | `cli trace status` / `cli trace verify` | PASS | exit 0, resolver-backed |
| CLI-adjacent regression | `pytest tests/test_entrypoint_governance_audit.py tests/test_doctrine_cli.py tests/aurel_exec/test_exec_status_projection.py -q` | PASS | 22 passed |
| ruff | `ruff check src/agentic_runtime/aurel_trace src/agentic_runtime/cli_modules tests/aurel_trace` | PASS | All checks passed |
| mypy | `mypy src/agentic_runtime/aurel_trace src/agentic_runtime/cli_modules` | PASS | 28 files, no issues |
| git status | `git status --short` | clean | after in-scope commit |

---

## Files created

- `src/agentic_runtime/aurel_trace/trace_resolver.py`
- `src/agentic_runtime/aurel_trace/trace_query.py`
- `src/agentic_runtime/aurel_trace/trace_demo.py`
- `src/agentic_runtime/cli_modules/trace_commands.py`
- `tests/aurel_trace/test_trace_verified_resolver.py`
- `tests/aurel_trace/test_trace_verified_overclaim_guard.py`
- `tests/aurel_trace/test_trace_query_read_model.py`
- `tests/aurel_trace/test_trace_cli_commands.py`
- `tests/aurel_trace/test_trace_cli_read_only_boundaries.py`
- `agent/reports/P5_TRACE_D_TRACE_VERIFIED_RESOLVER_QUERY_CLI.md` (this report)

## Files modified

- `src/agentic_runtime/aurel_trace/__init__.py` (exports only)
- `src/agentic_runtime/cli.py` (additive `trace` subcommand registration only)
- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/ARCHITECTURE.md`,
  `agent/DECISIONS.md`, `agent/TESTS.md` (canon)

---

## Remaining risks

- **Resolver:** the gate is intentionally strict — it proves trace/evidence integrity, **not**
  semantic/business/policy correctness (explicitly UNAVAILABLE). Callers choose the
  `required_evidence_kinds` per target; a too-lax required set would understate what
  TRACE_VERIFIED means, so P5-E should standardize required-evidence profiles per target kind.
- **Query model:** it reflects decisions and cannot self-decide; it is only as complete as the
  decisions fed to it.
- **CLI:** the demo substrate is DEV_FIXTURE, not a live trace run — the CLI demonstrates the
  resolver honestly but does not yet query a live/persistent ledger (deferred).
- **P5-E handoff:** the projection feed, golden thread / causal graph, and replay readiness should
  consume `TraceVerificationDecision` / the query summaries; the decision objects already carry
  stable ids, source ids, and status suitable for a feed.

**Next recommended task:** P5-TRACE-E — Projection Feed / Golden Thread / Replay Readiness.
