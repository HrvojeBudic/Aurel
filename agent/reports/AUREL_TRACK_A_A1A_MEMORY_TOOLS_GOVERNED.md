# Track A / A1a — Memory ops as governed tools

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (unmerged, not pushed)
**Status:** DONE (recovery + seal). Additive; no behavior change to existing paths.

## Summary

A1a adds `MemoryToolSession` — a thin *governed dispatcher* that lets an entity
**propose** memory operations without ever storing directly. Every write routes
through the pre-existing `MemoryFabric.request_write` funnel (policy →
`_trace_memory` → a single `MemoryGovernanceRecord`); reads route through
`retrieve`. Memory tools are deliberately **not** sandbox tools and **not** a
`runtime.submit` path: they take no sandbox snapshot, emit no
`StateTransitionRecord`, and charge exactly one `charge_memory_write` per
governed write attempt (allow OR deny) and zero `charge_sandbox_execution`.

Files:
- `src/agentic_runtime/memory_tools.py` (new) — `MEMORY_TOOL_NAMES` frozenset,
  `MemoryToolSession`, `mem_add` (governed write), `mem_search` (read-only),
  and honestly-unavailable `mem_update`/`mem_delete`/`mem_link`.
- `src/agentic_runtime/tool_contracts.py` — dedicated `memory_contract_registry()`
  (NOT injected into `default_contract_registry()`; keeps the sandbox contract
  surface byte-identical). `mem_add` declares `MEMORY_WRITE`; `mem_search` has an
  empty side-effect profile (read-only); update/delete/link declared.
- `src/agentic_runtime/tools.py` — fail-closed guard at the top of
  `ToolBus.execute`: any `mem_*` name → `memory_tool_wrong_path` error. Memory
  tools are never added to `self.registered`.

No new flag; no wiring into `build_runtime`/entity/`__init__` (that is A8).

## Root cause of the reported import hang

The prior session reportedly **hung** on a bare
`python -c "import agentic_runtime.memory_tools ..."` circular-import check.

**Finding: the module on disk is import-safe — there is no module-level blocking
code.** The top level contains only imports, `frozenset` constants, one pure
helper (`_writer_kind_from_card`), and a class definition; the one governance
import (`MemoryWriteRequest`) is deferred into `_mem_add`. Verified empirically
(timeout-wrapped, never bare):

```
timeout 30 .venv/bin/python -c "import agentic_runtime.memory_tools; print('IMPORT_OK')"   → IMPORT_OK, exit 0 (instant)
timeout 30 .venv/bin/python -c "import agentic_runtime.tools; import agentic_runtime.tool_contracts; import agentic_runtime.memory_tools; print('CHAIN_OK')"  → CHAIN_OK, exit 0
```

`tool_contracts.py` imports only `core_types` (no `tools`), so the
`tools → memory_tools → tool_contracts` chain has **no cycle**.

**Conclusion:** the hang was an *invocation artifact*, not a code defect — a bare
`python -c "…"` with broken shell quoting/heredoc drops Python into an
interactive REPL that blocks reading `stdin` forever. The durable fix is the
mandated discipline: always wrap import checks as
`timeout 30 .venv/bin/python -c "import …; print('ok')"` and abandon+diagnose on
any hang rather than retry blind. As a small hardening this pass, `memory_tools`
keeps its only governance import lazy and defines `_AGENT_WRITER` locally so
import time stays trivial.

## Refinement this pass

To honor the approved signature (`MemoryToolSession(fabric, budget, *, card=None,
contracts=None)` with *writer_kind derived from card*), `writer_kind` now defaults
to `None` and is derived from the card via `_writer_kind_from_card` (least
privilege — `agent` — when absent). An explicit `writer_kind` still wins for the
runtime/tests. The security invariant is unchanged: identity is a property of the
constructor (the runtime), never a tool arg, so an agent cannot self-elevate.

## Seal — `tests/test_p6a1_memory_tools_governed.py` (6 tests, 7 assertions)

1. **agent `mem_add(canon)` denied** `agent_cannot_write_restricted`, not stored,
   one governance **deny** row; **and** `memory_writes == 1`,
   `sandbox_executions == 0` (attempt charged exactly once).
2. **operator `mem_add(raw)` allowed**, stored (L1 +1), one governance **allow**,
   `memory_writes == 1`, `sandbox_executions == 0`.
3. **one governance row per write, zero `StateTransitionRecord`** from the session.
4. **`mem_search` read-only** — `memory_writes == 0`, `sandbox_executions == 0`,
   store byte-for-byte unchanged (`fabric.stats()` equal before/after).
5. **`mem_add` via `ToolBus.execute`** refused (`memory_tool_wrong_path`), not
   registered, no write, no state transition.
6. **`mem_update`/`mem_delete`/`mem_link`** honestly `unavailable=True`,
   `requires_a2_a4`, no write, no charge.

Result: **6 passed in 0.19s.**

## Validation

- `compileall` OK; `ruff check` clean; `python -m mypy` — no issues, all on the 3
  in-scope files.
- Seal: **6 passed**.
- Regression (timeout-wrapped): `test_memory_p09.py`,
  `test_memory_write_policy_cards_p167.py`, `test_tool_contract_p10.py`,
  `test_tool_registry_p133.py`, `test_builtin_tool_manifests_p138.py`,
  `test_p6a0_bitemporal_seal.py` → **159 passed, 0 failed**.
- Full ~25 min suite intentionally NOT run (operator skipped it for this phase).

## Next: A2

Memory graph primitives (typed edges) — backs `mem_link`; unlocks the first of
the two `requires_a2_a4` gates.
