# Track A / A2 — Typed relation graph (memory-graph primitives)

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (unmerged, not pushed)
**Status:** DONE (additive; no behavior change to existing write/promote/retrieve paths).

## Summary

A2 lays a typed, bi-temporal, **append-only** relation graph *beside* the memory
store and flips `mem_link` from the A1a fail-closed stub (`requires_a2_a4`) to a
live governed op. Records stay the atoms; edges express typed relations
(`SUPERSEDES`, `CONTRADICTS`, `SUPPORTS`, `RELATES_TO`, `DERIVED_FROM`) and are
written only through a new governed funnel that mirrors `request_write`:

```
mem_link → MemoryToolSession._mem_link → one charge_memory_write
        → MemoryFabric.link → MemoryWritePolicy.evaluate_link (disposes)
        → one MemoryGovernanceRecord(action="link")  → graph.add(edge) on allow
```

An edge never carries a truth state, so it can never elevate a record's trust —
promotion stays the only trust-raising path. `SUPERSEDES`/`CONTRADICTS` are
evidence-gated; unknown endpoints, unknown relations, and self-links fail closed.

## Files changed

**New — `src/agentic_runtime/memory_graph.py`**
- `MemoryRelation(str, Enum)` — closed-world relations; `EVIDENCE_GATED_RELATIONS = {SUPERSEDES, CONTRADICTS}`.
- `MemoryEdge` — frozen (append-only), bi-temporal (A0-style default-open valid/transaction stamps), with provenance (writer_kind, created_by, source_run_id, source_trace_ids, evidence_refs, confidence); `make()` uses `new_id("mem_edge")`; `payload_hash()`/`to_dict()`.
- `MemoryGraphIndex` — insertion-ordered append-only edge list + `_out`/`_in` adjacency; reads (`edges_from`/`edges_to`/`neighbors`/`by_relation`) return **copies**, preserve insertion order (never sort by the uuid `edge_id` or `hash()`), and fail closed (`[]`) on unknown ids.
- `detect_supersession_chain(index, memory_id)` — walks `SUPERSEDES` edges oldest→newest, cycle-guarded, deterministic; unknown id ⇒ `[]`.

**Edit — `src/agentic_runtime/memory_governance.py`**
- New `MemoryLinkRequest` (from_id, to_id, relation, writer_kind, created_by, source_run_id, source_trace_ids, evidence_refs, confidence) and `MemoryLinkDecision` (allowed, relation, reason_code, message, edge).
- `MemoryWritePolicy.evaluate_link(req, known_ids, trace=None)` — pure decision reusing the exact `evaluate_write` trace-reference discipline, then: closed-world relation → mandatory trace ref → endpoints exist (fail-closed) & distinct → evidence gate. Reason codes: `illegal_relation`, `missing_trace_reference`, `invalid_trace_reference`, `unknown_endpoint`, `self_link_forbidden`, `link_requires_evidence`, `allowed`.

**Edit — `src/agentic_runtime/memory.py`**
- `MemoryFabric.__init__` gains `self.graph = MemoryGraphIndex()` (additive).
- `link(request)` — the governed funnel above. `_trace_link()` anchors one
  `MemoryGovernanceRecord(action="link")` (memory_id=edge_id, from_state=from_id,
  to_state=to_id, full edge shape incl. relation in `details`). Existing
  write/promote rows still pass `details={}` ⇒ **byte-identical**.

**Edit — `src/agentic_runtime/memory_tools.py`**
- `_mem_link` handler (shaped exactly like `_mem_add`): one `charge_memory_write`
  per attempt (allow or deny), writer identity from the session (never a tool
  arg). `mem_link` removed from `_UNAVAILABLE_TOOLS`.
- The remaining unavailable tools (`mem_update`/`mem_delete`) now report the
  honest narrower reason `requires_a4` (A2 discharged the "a2" half).

**Edit — `src/agentic_runtime/tool_contracts.py`**
- `mem_link` contract: `relation` constrained to `_MEMORY_RELATIONS` (enum),
  added optional `evidence_refs`/`confidence`/`source_trace_ids`; dropped the
  "UNAVAILABLE until A2" wording. Still `SideEffect.MEMORY_WRITE`; still kept out
  of `default_contract_registry()`.

## Governance + trace invariants (how tested)

- **Edges are governed writes; agents can't elevate trust.** Seal §3: agent
  `SUPERSEDES` without evidence → `link_requires_evidence` (no edge); an allowed
  agent `SUPPORTS` edge leaves the target's `truth_state` = CANDIDATE unchanged.
- **Fail-closed endpoints.** Seal §2: `unknown_endpoint` → deny, no edge. Seal §7
  (policy-level): `illegal_relation`, `self_link_forbidden`, `missing_trace_reference`.
- **One trace record per edge write.** Seal §1: exactly one
  `memory_governance` row with `action=="link"`, zero `StateTransitionRecord`.
- **One charge per attempt, zero sandbox.** Seal §1/§2/§4: `memory_writes==1`
  after each attempt (allow OR deny), `sandbox_executions==0`.
- **No-collapse.** Seal §5: `fabric.stats()` and `retrieve()` results are
  unchanged by linking; a later `mem_add` still works; graph reads are copies.
- **Deterministic chain.** Seal §6: `detect_supersession_chain` returns the
  ordered chain across two `SUPERSEDES` edges; unknown id ⇒ `[]`.

## Feature flag

No new gate. `AUREL_DURABLE_MEMORY` stays **defined-not-gating** (A0 posture);
`memory_graph` imports its `_flag_enabled` for continuity but branches on nothing.
`mem_link` goes live unconditionally and additively (consistent with A1a's ungated
`mem_add`). Byte-identity is structural: with no `link` traffic, existing paths are
unchanged. No wiring into `build_runtime`/entity (that's A8).

## Spec-vs-code drift + decisions

- **D4 (the substantive one) — supersession has two candidate homes.** A0 already
  shipped `AsOfView.belief_history()`/`is_current()` reading `superseded_by`/
  `revises` **off the record**, while the A2 spec puts supersession in
  `MemoryEdge`/`detect_supersession_chain` (graph). **A2 takes the edge-only path:**
  a `SUPERSEDES` edge is the supersession record; A2 does **not** write
  `MemoryRecord.superseded_by` or close any interval. Rationale: smallest correct
  honest path — keeps A2 strictly append-only and byte-identical for records, and
  leaves record-field supersession + interval closure to **A4 (belief revision)**,
  where the spec places `revises`/retract/forget anyway. Consequence (honest):
  A0's `belief_history` stays inert until A4; the graph's
  `detect_supersession_chain` is the A2 supersession read model. Flagged so A4
  reconciles the two views.
- **D2 — `replay()` drops `details`.** trace.py `replay()` surfaces the
  memory-governance scalar set (incl. `action`/`memory_id`/`from`/`to`) but not
  `details`, so `relation` is hash-covered in the record yet not in the replay
  projection A7 rebuilds from. Accepted for A2 (matches the §6 deferred-seam note);
  A7 can extend the `action=="link"` replay branch or read the durable store.
- **D3 — new `MemoryLinkDecision`.** `MemoryWriteDecision.record` is typed
  `Optional[MemoryRecord]`, not an edge, so a dedicated small decision type is the
  honest choice (no field-punning).
- **D5 — narrowed reason.** `mem_update`/`mem_delete` now report `requires_a4`
  (was `requires_a2_a4`); the A1a seal assertion was updated accordingly.
- **Minor.** `new_id` is uuid4 (non-deterministic) ⇒ graph ordering is
  insertion-based, never id-sorted. Contract-level `relation` enum means a bogus
  relation is rejected by the input validator before governance; the governance
  `illegal_relation` path is still exercised directly at the policy layer (seal §7).

## Validation (focused-first; full ~25 min suite intentionally skipped this phase)

- `compileall` OK; `ruff` clean; `python -m mypy` — no issues, on the 5 source files.
- Seals: `test_p6a2_memory_graph.py` (7) + updated `test_p6a1_memory_tools_governed.py` (7) → **14 passed**.
- Directly-affected regression (timeout-wrapped): memory_p09, memory_write_policy_cards_p167, tool_contract_p10, tool_registry_p133, builtin_tool_manifests_p138, p6a0_bitemporal, p6a1, p6a2 → **173 passed, 0 failed**.

## Next: A3 — DurableMemoryFabric

Persistence as a projection over the trace (`durable_memory.py`,
`memory_persistence.py` JSONL + atomic `os.replace`; re-verify `source_trace_ids`,
quarantine unanchored; `ExternalMemoryBackend` unconstructible-available). The
`AUREL_DURABLE_MEMORY` flag goes load-bearing here.
