# AUREL — Track A / Phase A0: Bi-temporal stamps + as-of read model

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (from `master@9749f75`)
**Task ID:** Track A — A0
**Type:** Additive memory-metadata + read-model foundation (no behavior change)
**Status:** DONE — seal + focused regression green; full suite green (8545 passed, 11 skipped, 0 failed).

---

## 1. Purpose / scope

A0 gives every `MemoryRecord` two independent time axes — **valid time** (when a
fact is true in the world) and **transaction time** (when the system believed it)
— and a pure, read-only **as-of** projection to query beliefs at a point in time
and walk supersession chains. It is the metadata/read-model foundation for the
rest of Track A (durable memory, belief revision, hybrid retrieval).

**Adds:** 6 optional, default-open bi-temporal fields on `MemoryRecord`; a pure
`BiTemporalStamp` value object; a snapshot-only `AsOfView` (`as_of`, `current`,
`belief_history`); the Track-A umbrella flag `AUREL_DURABLE_MEMORY`.

**Does NOT:** touch `runtime.submit`, the sandbox, CAS (`state_store`),
`worldline`, `tools`, `tool_contracts`, `memory_governance`, or any trace record /
`payload_hash`; does not populate the new fields (no writer yet — that is A2/A4);
does not persist anything (A3/A8); does not wire as-of into retrieval (A6). No
behavior is gated on a flag in A0.

## 2. Files changed

| File | Change |
|------|--------|
| `src/agentic_runtime/core_types.py` | `MemoryRecord`: +6 optional `None`-default fields (`superseded_by`, `revises`, `valid_from/to`, `transaction_from/to`). `to_dict()` unchanged (`asdict` picks them up). |
| `src/agentic_runtime/memory_bitemporal.py` | **new** — `BiTemporalStamp` (frozen, pure, clock-free): `is_valid_at`, `was_believed_at`, `is_current`, `to_dict`, `from_record`; `_FLAG="AUREL_DURABLE_MEMORY"` + `_flag_enabled()` (defined-not-gating). |
| `src/agentic_runtime/memory_asof.py` | **new** — `AsOfView` snapshot read model: `as_of`, `current`, `belief_history`, `from_fabric`; deterministic sort `(transaction_from, valid_from, memory_id)`, fail-closed. |
| `tests/test_p6a0_bitemporal_seal.py` | **new** — 10 seal tests (6 invariants). |

Per approval decision (c), no `MemoryRecord.bitemporal_stamp()` helper was added —
the adapter lives solely in `memory_bitemporal.from_record` (one-directional;
`core_types` imports nothing from the new modules, no circular-import risk).

## 3. Flag nuance (honest)

The Track-A umbrella flag **`AUREL_DURABLE_MEMORY`** is introduced in A0 (constant
+ `_flag_enabled()`, default **OFF**, truthy set `{"1","true","TRUE","on"}` per the
established `dual_kernel`/`reasoning` idiom). **A0 branches on nothing:** the 6
fields are unconditionally additive and the read model is opt-in by being *called*.

A0's byte-identity is therefore **structural, not flag-gated** — it holds because
the new fields never enter a hashed trace payload, not because a flag hides them.
The grounded reason: the memory-governance funnel
(`memory._trace_memory → MemoryGovernanceRecord.make`) serializes a **fixed scalar
set** and passes **no `details`**; it never embeds the `MemoryRecord` dict. So
`MemoryGovernanceRecord.payload_hash()` is unaffected by the record's new fields.
The flag becomes load-bearing at **A3** (durable persistence) / **A6** (as-of
filtered retrieval). This is stated plainly rather than dressed up as a
flag-guarded change.

## 4. Empty-fixture result (spec caution resolved)

The A0 spec warned that `to_dict()` gaining keys would require updating
`MemoryRecord` golden fixtures "in the same commit; grep tests first." The grep was
re-run:

```
grep -rn "MemoryRecord" tests/            → 0 tests reference MemoryRecord
grep MemoryRecord dict/asdict/keys asserts → NONE
```

There are **no `MemoryRecord` dict-shape fixtures** in the suite, so no fixture
update was needed. (The `_to_dict` helpers in `test_memory_write_policy_cards_p167`
serialize `MemoryWritePolicyCard`, a different type.)

## 5. Cross-cutting invariants (§5) held

- **Additive-behind-flags / byte-identical:** new fields never hashed; funnel-built
  records carry open stamps; seal asserts no bitemporal key appears in any
  memory-governance trace row and the chain still verifies.
- **Trace = single source of truth:** A0 adds no trace record and no second store;
  `AsOfView` is a pure projection over records. Stamps are descriptive metadata.
- **No-overclaim (structural):** `is_current()` is True only for fully-open
  intervals; a closed `to` on either axis ⇒ not current. `AsOfView` fabricates
  nothing.
- **Fail-closed:** unknown id / empty view ⇒ `[]`.
- **Stdlib-only, deterministic:** frozen dataclass + list filter/sort by
  `(field, id)`, never `hash()`; no clock read in the value object; no deps.

## 6. Seal test results

`tests/test_p6a0_bitemporal_seal.py` — **10 passed**:
1. `test_memory_record_bitemporal_fields_default_open` — open defaults; `to_dict` keys.
2. `test_governed_writes_do_not_serialize_bitemporal_fields` — trace unaffected; chain verifies.
3. `test_as_of_returns_past_then_current_belief` — past vs current belief.
4. `test_belief_history_is_ordered_and_deterministic` — oldest→newest from either end.
5. `test_valid_time_axis_is_half_open` — `[from, to)` semantics.
6. `test_retrieval_ignores_stamps_in_a0` — closing a stamp does not hide a record from `retrieve`/`assemble_context`.
7. `test_is_current_cannot_lie` — no-overclaim.
8. `test_fail_closed_empty_and_unknown` — `[]` on empty/unknown.
9. `test_as_of_view_from_fabric_snapshot` — snapshot independence.
10. `test_durable_memory_flag_defaults_off` — flag default OFF.

## 7. Validation

| Command | Result |
|---------|--------|
| `compileall` (3 modules + seal) | ok |
| `ruff check` (3 modules + seal) | All checks passed |
| `mypy` (3 modules) | Success: no issues (3 files) |
| `pytest tests/test_p6a0_bitemporal_seal.py` | **10 passed** |
| `pytest tests/test_memory_p09.py tests/test_memory_write_policy_cards_p167.py` | **82 passed** (unchanged) |
| Full suite (`AGENTIC_SKIP_RECURSIVE_SMOKE=1 pytest -q -p no:cacheprovider`) | **8545 passed, 11 skipped, 0 failed** in 1526.55s (25:26) |

Baseline at the `9749f75` branch point is 8535 passed / 11 skipped (per the
masterplan header). A0 adds exactly its **10** seal tests → 8545 passed / 11
skipped: **zero regressions, zero new skips** — the disabled-path byte-identity
invariant holds across the whole suite.

## 8. Deliberately not implemented

- No writer for the stamps (revision/supersession is A2/A4); A0 records are open.
- No persistence (A3/A8); no retrieval wiring (A6); no `runtime.submit`/CAS/tools/
  governance edits.
- No `MemoryRecord.bitemporal_stamp()` helper (per decision c).
- Flag defined but not branched on.

## 9. Remaining risks

- The flag is "defined-not-gating" — a reader could expect it to gate A0 behavior;
  documented here and in the module docstring to avoid that misread.
- Bi-temporal fields are unvalidated in A0 (any float accepted); interval-consistency
  enforcement (e.g. `valid_from <= valid_to`) is deferred to the writer phases.

## 10. Next recommended task

**A1a — Memory ops as governed tools** (`memory_tools.py`: `mem_add/update/delete/
search/link` routed through `fabric.request_write`/`promote`/`retrieve`; one
`charge_memory_write`, zero sandbox-exec charge; `mem_*` do not flow through
`runtime.submit`). Seal: `test_p6a1_memory_tools_governed.py`.
