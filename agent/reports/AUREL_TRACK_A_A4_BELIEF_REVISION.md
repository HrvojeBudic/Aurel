# Track A / A4 — Belief revision (update, retract, forget, supersession)

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (unmerged, not pushed)
**Status:** DONE (additive; existing paths unchanged).

## Summary

A4 adds governed belief revision and flips the last two memory tools live.
`mem_update` supersedes a prior belief with a new governed version; `mem_delete`
is a **non-destructive forget**. Every op is governed, emits exactly one trace
row, charges one `memory_write`, and fails closed on unknown ids and protected
memory. Crucially, A4 **writes the record-level supersession fields** A0 shipped
but nothing populated yet, so A0's `belief_history` / `is_current` go live, and it
adds a `SUPERSEDES` edge so A2's edge-view **agrees** with the record-view.

```
mem_update → apply_update → evaluate_revision (re-scores the new belief via
             evaluate_write) → one MemoryGovernanceRecord(action="update") →
             close old (valid_to/transaction_to, superseded_by, DEPRECATED),
             store new (revises), add new-SUPERSEDES-old edge
mem_delete → forget      → one MemoryGovernanceRecord(action="forget") →
             mark EXPIRED + close transaction interval (record kept for audit)
retract    → (fabric primitive) close intervals + DEPRECATED
```

## Files changed

**New — `src/agentic_runtime/memory_revision.py`**
- `apply_update(fabric, req)`, `retract(fabric, req)`, `forget(fabric, req)` —
  governed primitives operating on the fabric. Each looks up the target, calls
  `policy.evaluate_revision`, emits **one** `MemoryGovernanceRecord` via
  `_trace_revision`, and (on allow) mutates records. `apply_update` closes the old
  belief, stores the successor via the **base** `MemoryFabric._store`, and adds the
  `SUPERSEDES` reconciliation edge.

**Edit — `src/agentic_runtime/memory_governance.py`**
- `MemoryRevisionRequest` / `MemoryRevisionDecision`; `_REVISION_PROTECTED = {CANON, REJECTED}`.
- `MemoryWritePolicy.evaluate_revision(req, target, trace)` — pure decision: op is
  closed-world; target must exist (`unknown_memory`); trace-reference discipline
  (reused); protected targets fail closed (`revision_forbidden_on_protected`); for
  `update` the new belief is **re-scored through `evaluate_write`**, so an agent
  cannot elevate trust and a failed run cannot mint success via the back door
  (the honest write reason, e.g. `agent_cannot_write_restricted`, is propagated).

**Edit — `src/agentic_runtime/memory_tools.py`**
- `_mem_update` (→ `apply_update`) and `_mem_delete` (→ `forget`) handlers, each
  charging exactly one `charge_memory_write` per attempt; writer identity from the
  session (never a tool arg). Removed the now-obsolete `_UNAVAILABLE_TOOLS`
  set + `_unavailable` stub (all five tools are live). `_revision_result` shapes
  the honest allow/deny dict.

**Edit — `src/agentic_runtime/tool_contracts.py`**
- `mem_update` contract: `content` now required, `truth_state` enum, optional
  `confidence`/`evidence_refs`/`source_trace_ids`. `mem_delete`: optional
  `source_trace_ids`. Both dropped the "UNAVAILABLE" wording.

## Governance + trace invariants (how tested)

- **Entity proposes / runtime disposes.** `evaluate_revision` disposes; the new
  belief on update is re-scored by `evaluate_write`. Seal §4: agent update→verified
  denied `agent_cannot_write_restricted`, old untouched, no successor, still charged.
- **Governance layered on, not around.** No path revises a record except through
  `evaluate_revision`; protected memory (canon/policy, rejected/audit) is never
  revised. Seal §3: `mem_delete` on canon and on a rejected/audit record →
  `revision_forbidden_on_protected`.
- **Trace = single source of truth.** Exactly one `MemoryGovernanceRecord`
  (`action` = update/retract/forget) per op; zero `StateTransitionRecord`. Seal
  §1/§2 assert one row per op and no state transitions.
- **Fail-closed.** Unknown id → `unknown_memory` (seal §5); protected → forbidden.
- **One charge per op.** Seal §1/§4 assert `memory_writes` increments once per
  attempt (allow or deny), `sandbox_executions == 0`.

## Non-destructive forget + forbidden targets (proof)

Seal §3: after `mem_delete`, the record is **still in `by_id`** but `truth_state`
is `EXPIRED` and `is_active()` is False — inactive, never popped/deleted, history
preserved. `mem_delete` on canon (policy/identity) and on a rejected (audit) record
is denied `revision_forbidden_on_protected` and leaves the target untouched.

## A0 goes live: `belief_history` / `is_current`

A0 shipped `superseded_by`/`revises` + the bi-temporal stamps and an `AsOfView`
that reads them, but **nothing wrote them** (the A0 record comment said
supersession/revision "arrive in A2/A4"). A4 is that writer: `apply_update` sets
`old.superseded_by = new`, `new.revises = old`, and closes the old belief's
`valid_to`/`transaction_to`. Seal §1 proves `AsOfView.belief_history(new)` and
`belief_history(old)` both return `[old, new]`, and `is_current(old)` is False
while `is_current(new)` is True — the A0 read model is now meaningful.

## A2 reconciliation: edge-view and record-view agree

A2 represented supersession as a `SUPERSEDES` edge (edge-only, by decision D4).
A4's `apply_update` writes **both** the record fields **and** a `new SUPERSEDES old`
edge, so the two views agree: seal §1 asserts
`detect_supersession_chain(graph, old) == [old, new]` (edge-view) equals
`belief_history` (record-view). The reconciliation edge is created as part of the
single governed update op (no second governance row).

## Spec-vs-code drift + decisions

- **D1 (main) — one governance row per op forces a funnel bypass.** Reusing
  `request_write` (for the new version) + `link` (for the edge) would emit 2–3
  governance rows per update. To hold "one row per op", `apply_update` calls
  `evaluate_write` **purely** (no trace), emits a single `action="update"` row,
  and stores the successor via the base `MemoryFabric._store`. Same governance
  logic, one audit anchor.
- **D2 — A4 does not write to the durable (A3) backend.** Because the successor is
  stored via the *base* `_store`, a `DurableMemoryFabric` does **not** mirror
  revision mutations to JSONL (and the reconciliation edge isn't persisted). This
  is deliberate and honest: the trace records every revision (source of truth);
  the durable JSONL cache would otherwise gain entries A3's rebuild can't anchor
  (revision-row `memory_id`s live in row `details`, which `replay()` drops — the
  D2 seam noted in A2/A3). Projecting revision rows onto the durable store is
  deferred to A7 (memory explorer / trace→store projection) / A8. No `memory.py`
  or `durable_memory.py` edits were needed (matches the spec's file list).
- **D3 — retract also honors protected targets.** The spec forbids *forget* on
  audit/canon/policy; A4 applies the same fail-closed rule to *retract* and
  *update* (`_REVISION_PROTECTED = {CANON, REJECTED}`) — you cannot un-believe or
  overwrite identity/policy or the audit trail. Operator-approved canon revision is
  a future extension (noted).
- **D4 — `mem_delete` maps to forget** (non-destructive) rather than retract; the
  stronger "no longer retained" semantics fit a delete verb, and retract stays a
  fabric primitive (sealed directly). Both are non-destructive.

## Validation (focused-first; full ~25 min suite intentionally skipped)

- `compileall` OK; `ruff` clean; `python -m mypy` — no issues, on the 4 source files.
- Seals: `test_p6a4_belief_revision.py` (6) + updated `test_p6a1_memory_tools_governed.py` (7) → **13 passed**.
- Directly-affected regression (timeout-wrapped): memory_p09, memory_write_policy_cards_p167, tool_contract_p10, tool_registry_p133, builtin_tool_manifests_p138, p6a0, p6a1, p6a2, p6a3, p6a4 → **186 passed, 0 failed**.

## Next: A5 — Consolidation

`memory_consolidation.py` (deterministic clustering → CANDIDATE + `SUMMARIZES`
edges); edit `memory_tools.py`, `praxis.py`. NC: never auto-canonizes; summarize ⇒
CANDIDATE only; provenance preserved.
