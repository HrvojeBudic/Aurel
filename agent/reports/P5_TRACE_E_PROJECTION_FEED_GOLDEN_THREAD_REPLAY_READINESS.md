# P5-TRACE-E — Projection Feed / Golden Thread / Replay Readiness

**Date:** 2026-07-05
**Domain:** P5 — AurelTrace Spine (continues P5 after P5-TRACE-A/B/C/D)
**Pack:** P5-TRACE-E
**Status:** DONE — resolver truth made projection-ready and causally legible, read-only, no replay.
**Previous pack:** P5-TRACE-D — TRACE_VERIFIED Resolver / Query Read Model / CLI
**Next pack:** P5-TRACE-F — Privacy / Export / Persistent Backend Integrity

---

## Purpose

P5-TRACE-D produced the single `TRACE_VERIFIED` resolver and `TraceVerificationDecision` objects.
P5-TRACE-E turns that resolver-backed truth into **projection-ready causal continuity** through
three read-only layers: a projection **feed** that packages resolver decisions for future
Shell/API/event consumers, a **Golden Thread / causal graph** that links P3→P4→P5→Evidence→
Decision→Feed refs into a legible causal story, and a **replay-readiness** assessment that
describes the structural prerequisites for *future* replay tooling — without implementing replay.

Law: **Runtime emits. P5 adapts. Resolver decides. Query reflects. Projection feed presents.
Golden Thread links. Replay-readiness assesses prerequisites. Custos authorizes. Operator decides.**

Everything here is read-only and side-effect free. The feed **reflects** resolver truth (it never
assigns `TRACE_VERIFIED`); the Golden Thread **links** (it never executes/schedules/replays/
repairs); readiness **assesses** (it never replays/forks/restores). Actual replay, fork,
exact-copy, state restore, Shell UI, API/event bus, P9, and Rust/WASM remain UNAVAILABLE.
`READY_FOR_ANALYSIS` means structurally analyzable later — **not** replay implemented.

---

## Roadmap coverage (P5.14–P5.16)

| Range | Title | Status | Evidence |
|---|---|---|---|
| P5.14 | Projection Feed Contract | DONE | `trace_projection_feed.py`; `test_trace_projection_feed.py` (9) |
| P5.15 | Golden Thread / Causal Graph Spine | DONE | `golden_thread.py`; `test_golden_thread.py` (5) + `test_causal_graph_read_only.py` (8) |
| P5.16 | Replay Readiness / Time-Slice Refs | DONE | `replay_readiness.py`; `test_replay_readiness.py` (8) |

33 focused P5-E tests, all passing; A–D + legacy trace regression green (191 in
`tests/aurel_trace` + legacy).

---

## Projection feed proof (`trace_projection_feed.py`)

- **`TraceProjectionFeedEntry`** reflects one P5-D `TraceVerificationDecision`: it copies the
  decision's `status`, `verified`, `missing_evidence`, and `blocking_findings` verbatim, and
  surfaces an UNAVAILABLE decision's reason as `unavailable_reason`. Its own `truth_label` is
  `LIVE` (a read model) — the resolver verdict lives only in `verification_status`. Invariant:
  `verified` iff `verification_status is TRACE_VERIFIED`, so an entry cannot claim verified unless
  its source decision did (proven; a hand-built entry with a mismatch raises). Deterministic
  `feed_entry_id`; `created_at` excluded from the id.
- **`TraceProjectionFeed`** is a read-model contract with deterministic per-status counts; its
  `is_api_server`/`is_event_bus`/`is_shell_ui`/`mutates` are unconstructible True — it is **not**
  an API server, event bus, or Shell UI, and mutates nothing.
- Builders `build_trace_projection_feed_entry` / `build_trace_projection_feed` /
  `summarize_projection_feed` copy decisions verbatim — no re-decision, no upgrade. Over the demo
  substrate the feed honestly shows the TRACE_VERIFIED CHAIN_HEAD entry and the PARTIAL
  runtime-submit-binding entry with its missing evidence (COMMAND/ROLLBACK/MEMORY) preserved.

**Resolver-truth reflection:** `TRACE_VERIFIED` appears in a feed entry only when the source
decision is TRACE_VERIFIED (proven); TRACE_BOUND/PARTIAL/DENIED/ERROR/UNAVAILABLE are preserved
exactly, and blocking findings + missing evidence + unavailable reasons remain visible.

---

## Golden Thread / causal graph proof (`golden_thread.py`)

- **`GoldenThreadSegment`** links a `source_ref → target_ref` causal step with optional
  evidence/decision/feed-entry ref ids and explicit `missing_links`; it is `TRACE_BOUND` and
  cannot claim `TRACE_INTEGRITY_VERIFIED`. **`GoldenThreadRef`** is a stable reference whose id
  changes with root target, segment count, and head segment (proven).
- **`CausalGraphNode`** (closed-world `CausalNodeKind` — P3_INTENT … TIME_SLICE) and
  **`CausalGraphEdge`** (closed-world `CausalEdgeKind` — CAUSED/PRODUCED/REFERENCED/VERIFIED_BY/
  PROJECTED_AS/BELONGS_TO_SLICE/MISSING_LINK) are diagnostic only. Unknown node/edge kinds fail
  closed; a `MISSING_LINK` edge requires a `missing_reason` (proven).
- **`GoldenThreadGraph`** is a read-only graph model whose `executes`/`schedules`/`replays`/
  `mutates`/`repairs` are unconstructible True — it is **not** a scheduler, planner, or execution
  DAG. `build_causal_graph` derives distinct-ref nodes and `CAUSED` edges from segments and emits
  a `MISSING_LINK` edge (carrying its reason) for each segment-level missing link; missing links
  are surfaced at the graph level. Deterministic graph id.

---

## Replay-readiness proof (`replay_readiness.py`)

- **`TraceTimeSliceRef`** is a range pointer (`start_ref`/`end_ref`/optional indices/chain head);
  it enforces `start_index <= end_index` (inverted range fails closed) and its
  `is_replay`/`is_snapshot`/`is_state_restore`/`is_fork` are unconstructible True — a time-slice
  ref is not replay, snapshot, restore, or fork. Deterministic id.
- **`ReplayReadinessStatus`**: READY_FOR_ANALYSIS / PARTIAL / MISSING_REQUIRED_DATA / UNSUPPORTED
  / UNAVAILABLE / ERROR.
- **`ReplayReadinessAssessment`** describes prerequisites only: its
  `replay_implemented`/`supports_fork`/`supports_exact_copy`/`supports_state_restore`/`executes`
  are unconstructible True, and every assessment carries `unavailable_reason` stating that actual
  replay is not implemented. A `READY_FOR_ANALYSIS` assessment **still** reports actual replay
  UNAVAILABLE (proven) — `READY_FOR_ANALYSIS` ≠ replay implemented.
- `assess_replay_readiness` over the closed-world input keys (`trace_run_ref`, `chain_head_hash`,
  `event_range`, `canonical_event_refs`, `evidence_refs`, `verification_decisions`,
  `schema_compatibility`): unsupported key → UNSUPPORTED; all required present →
  READY_FOR_ANALYSIS; none present → MISSING_REQUIRED_DATA; some present → PARTIAL; no required
  inputs → ERROR. Deterministic.

---

## Truth label posture

- **LIVE** — the feed and its entries/summary, the readiness assessment, and all contracts as
  read models.
- **TRACE_VERIFIED** — reflected in a feed entry only from a P5-D resolver decision; never
  assigned here and never a `TraceTruthLabel`.
- **TRACE_BOUND** — Golden Thread refs/segments, causal nodes/edges, and time-slice refs (links,
  not verdicts).
- **READY_FOR_ANALYSIS** — a `ReplayReadinessStatus` meaning structurally analyzable later; not a
  truth label and not replay.
- **PARTIAL / MISSING_REQUIRED_DATA / UNSUPPORTED** — honest replay-readiness downgrades.
- **UNAVAILABLE** — actual replay/fork/exact-copy/state restore, Shell UI, API/event bus, P9,
  Rust/WASM.
- **ERROR** — inconsistent causal input, inverted time-slice range, or a readiness call with no
  required inputs.

---

## Boundary / side-effect proof

runtime.py modified: **no** · runtime.submit called: **no** · trace append: **no** · trace
repair: **no** · trace mutation: **no** · `ToolRuntime.dispatch`: **no** · policy enforcement:
**no** · approval activation: **no** · memory write: **no** · workflow/job execution: **no** ·
retry/recovery: **no** · actual replay: **no** · fork: **no** · exact copy: **no** · state
restore: **no** · Shell UI: **no** · API server: **no** · event bus: **no** · P9 enforcement:
**no** · Rust/WASM: **no** · new ledger: **no** · semantic/business/policy correctness claim:
**no**.

`test_projection_feed_boundaries.py` ast-sweeps the three new modules: no `AgenticRuntime`/
`ToolRuntime`/`.submit(`/`.dispatch(`/`trace.append`/`_append_transition`/`.rollback(` fragments,
and no import of runtime/tool_runtime/policy/sandbox/verifier/memory/aurel_exec/aurel_flow/
aurel_shell. The feed builders consume already-made decisions (no `resolve_*` call, no
`TraceVerifiedResolver()`), and `golden_thread.py`/`replay_readiness.py` do not depend on the
resolver at all. Only `src/agentic_runtime/aurel_trace/` (three new modules + `__init__.py`
exports) and `tests/aurel_trace/` (five new test files) were touched.

---

## Validation

| Gate | Command | Result | Notes |
|---|---|---|---|
| compileall | `python -m compileall src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | |
| Focused P5-E tests | `pytest test_trace_projection_feed.py test_golden_thread.py test_causal_graph_read_only.py test_replay_readiness.py test_projection_feed_boundaries.py -q` | PASS | 33 passed |
| A–D + legacy regression | `pytest tests/aurel_trace tests/test_trace*.py -q` | PASS | 191 passed |
| ruff | `ruff check src/agentic_runtime/aurel_trace tests/aurel_trace` | PASS | All checks passed |
| mypy | `mypy src/agentic_runtime/aurel_trace` | PASS | 20 files, no issues |
| git status | `git status --short` | clean | after in-scope commit |

---

## Files created

- `src/agentic_runtime/aurel_trace/trace_projection_feed.py`
- `src/agentic_runtime/aurel_trace/golden_thread.py`
- `src/agentic_runtime/aurel_trace/replay_readiness.py`
- `tests/aurel_trace/test_trace_projection_feed.py`
- `tests/aurel_trace/test_golden_thread.py`
- `tests/aurel_trace/test_causal_graph_read_only.py`
- `tests/aurel_trace/test_replay_readiness.py`
- `tests/aurel_trace/test_projection_feed_boundaries.py`
- `agent/reports/P5_TRACE_E_PROJECTION_FEED_GOLDEN_THREAD_REPLAY_READINESS.md` (this report)

## Files modified

- `src/agentic_runtime/aurel_trace/__init__.py` (exports only)
- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/ARCHITECTURE.md`,
  `agent/DECISIONS.md`, `agent/TESTS.md` (canon)

---

## Remaining risks

- **Projection feed:** it is only as complete as the decisions fed to it; it reflects, never
  decides. A future Shell/API/event surface must treat it as a read model, not an authority.
- **Golden Thread / causal graph:** `build_causal_graph` currently kinds nodes generically as
  `TRACE_EVENT`; richer per-ref node kinds can be supplied by callers as segments carry more
  typed refs — a natural extension without changing the read-only contract.
- **Replay-readiness:** the assessment describes prerequisites only; actual replay stays
  UNAVAILABLE by construction. The input-key set is closed-world, so a new prerequisite must be
  added deliberately (and would otherwise be reported UNSUPPORTED).
- **P5-F handoff:** privacy/redaction/locality labels, an export manifest / audit bundle, and a
  persistent-backend integrity profile should consume the feed entries and readiness truth labels
  and preserve their missing-data posture.

**Next recommended task:** P5-TRACE-F — Privacy / Export / Persistent Backend Integrity.
