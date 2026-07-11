# AUREL F7.1 — Cost attribution: per-mandate bucket + client pivot

_2026-07-11, branch `feat/f7-corp`. The pivot that turns budget facts into a business answer._

## What shipped

Cost attribution answers *what did this client / this job cost?* — by pivoting facts the runtime
already records. F6.1 already carries a `mandate_id` on every budget-decision trace record; the ledger
already counts everything per run; F7.0 gives jobs that reference mandates. F7.1 adds the missing bucket
and the pivot. Additive behind `AUREL_CORP`; the no-mandate world is **byte-identical**.

- **`budget.py`** — additive `per_mandate: dict[str, dict]` bucket + `current_mandate_id` runtime
  context + `set_mandate(mandate_id)`. A guarded `_accrue_mandate(**deltas)` mirrors each cost-bearing
  charge (`precheck_command`, `charge_tool`, `charge_sandbox_execution`, `charge_memory_write`,
  `charge_llm`) into the per-mandate bucket — and **no-ops when no mandate is bound** (returns before
  touching anything), so with `current_mandate_id == ""` the bucket is never created and every existing
  counter, `snapshot()`, and trace record is unchanged. `_trace_budget` now stamps
  `mandate_id=self.current_mandate_id` onto the `BudgetDecisionRecord` — `""` reproduces the F6.1 default
  (empty ⇒ the replay dict omits the key), so this too is byte-identical when no mandate is set.
  Attribution accrues alongside the run counters but makes **no cap check** — it is a report, never a
  verdict, and can never block.
- **`runtime.py`** — after `ensure_context`, `runtime.submit` binds the card's authority with
  `self.budget.set_mandate(getattr(card, "mandate_id", ""))`. A card with no mandate (the common / F6-off
  case) binds `""` ⇒ no attribution, byte-identical.
- **`corp/cost.py`** — `CostAttributionView.from_ledger(ledger, corp_registry, *, mandate_registry=None)`
  pivots the per-mandate bucket up: mandate → job (via `JobRecord.mandate_ids`) → client. Produces
  `by_mandate` / `by_job` (with `client_id`) / `by_client` rollups and — honestly — an `unattributed`
  bucket for mandates no job references (never dropped, never invented). No ledger ⇒ `available=False`
  with a reason (F5.5 discipline); no corp registry ⇒ a mandate-only rollup (everything unattributed,
  reason stated). A static `cost_cents_by_mandate_from_trace(trace)` reads the max cumulative cost each
  mandate reached from the audit — a per-run cross-check that attribution matches the trace.

## Evidence

- Seal `tests/test_p6f7_1_cost_attribution.py` — **11 passed**: no mandate context ⇒ bucket empty +
  `snapshot()` identical + per-run counters identical (timestamp aside); charges accrue to
  `per_mandate[M]` (commands/tool/sandbox/memory/llm/tokens/cents); estimate-only vs. substantiated split
  honest; two mandates separated; view pivots mandate → job → client (klijent nula under the default
  mandate); unattributed mandate reported honestly; no-corp-registry mandate-only rollup; no-ledger
  UNAVAILABLE; trace cross-check equals ledger cost; budget records carry the bound `mandate_id`; empty
  mandate not stamped (byte-identical).
- ruff clean; mypy clean (6 files). Byte-identical regression (budget/state-machine/hitl/trace/persistence/
  merkle/mandate-trace/mandate-enforcement/governance-submit/repo-agent/flow-budget-guards/reasoning-binding
  + F7.0/F7.1): **142 passed, 0 failed** (~2:50).

## Boundary (honest)

Attribution is **read-only reporting**, never enforcement — the budget cap gate and the F6.2 mandate gate
are unchanged. The per-mandate bucket does **not** appear in `snapshot()` (HQ.Command burn stays the
run-level view); it is exposed only through `CostAttributionView`. A pre-existing quirk left untouched:
`_trace_budget` guards with `if not self._trace`, and `InMemoryTraceLedger` defines `__len__`, so the
*first* budget decision on an empty trace ledger is skipped (in a real run the trace already carries
status transitions before any budget charge) — I did not change this, as doing so would add records in
that edge case and break byte-identical. The trace cross-check reader takes the max cumulative cost per
mandate (the replay dict has no `run_id` to sum across runs), so it is a per-run consistency check.

## Next

- **F7.5** — portfolio map + task-runtime feed (`/read/corp/*`), closing the walking skeleton
  (F7.0 → F7.1 → F7.5). Then **F7.3** Watchtower flips the oldest F5 seam.
