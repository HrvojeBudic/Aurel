# Track A — Merge to master + connect the code

**Date:** 2026-07-08
**Branch:** `master` (merged from `feat/track-a-memory`; not pushed)
**Status:** DONE. Track A merged and wired into the live runtime + public API.

## What happened

1. **Merge.** `feat/track-a-memory` (A0–A8, 9 commits) merged into `master` with a
   `--no-ff` merge commit (`4592253`), preserving the track as a unit. Master had
   not diverged (0 commits behind), so the merge was a clean, conflict-free
   integration. Full suite at merge was already green (8594 passed / 11 skipped).

2. **Connect — public API (`d158cc3`).** The Track A modules were reachable only
   via submodule paths; they are now exported as first-class `agentic_runtime`
   symbols in `__init__.py` (additive imports + `__all__`): `MemoryToolSession`,
   `MEMORY_TOOL_NAMES`, `MemoryEdge`/`MemoryGraphIndex`/`MemoryRelation`/
   `detect_supersession_chain`, `DurableMemoryFabric` + backends
   (`FileMemoryBackend`/`ExternalMemoryBackend`/`MemoryBackend`),
   `MemoryRevisionRequest`/`Decision` + `memory_apply_update`/`memory_retract`/
   `memory_forget`, `memory_consolidate`, `hybrid_retrieve`, `MemoryProjection`,
   `NeuralEmbedderSeam`, `MemoryCandidateBridge`, `HashingEmbedder`,
   `BiTemporalStamp`, `AsOfView`, `MemoryLinkRequest`/`Decision`,
   `DurableMemoryGovernanceRecord`.

3. **Connect — agent-facing `mem_*` dispatch.** Previously an agent that submitted
   a `mem_add`/`mem_search`/`mem_link`/`mem_update`/`mem_delete`/`mem_consolidate`
   command via `runtime.submit` was rejected (`memory_tool_wrong_path` / contract
   gate) — the memory tools were only reachable by constructing a
   `MemoryToolSession` directly. They are now routed through the governed funnel
   from the normal submit path (see below).

## Agent `mem_*` dispatch — design

`AgenticRuntime.submit`, right after the issuer check, intercepts memory tools:

```
if self._durable_memory_enabled and cmd.tool in MEMORY_TOOL_NAMES:
    return self._dispatch_memory_command(cmd, card)
```

`_dispatch_memory_command` builds a `MemoryToolSession(self.memory, self.budget,
card=card)` and calls `session.invoke(cmd.tool, cmd.args)`. The result becomes a
`CommandResult(observation, verifier="memory", decision, transition=None)`.

Invariants held:
- **Governance layered on, not around.** The memory funnel
  (`MemoryWritePolicy` → one `MemoryGovernanceRecord`, one `charge_memory_write`
  for a write, none for a read) is the governance for these tools; the dispatch
  adds no bypass.
- **Entity proposes, runtime disposes / no self-elevation.** `writer_kind` is
  derived from the card (`_writer_kind_from_card` ⇒ least privilege `agent` for a
  normal `AgentCard`), never a tool arg — so an agent's `mem_add(canon)` is denied
  `agent_cannot_write_restricted`.
- **Not the sandbox.** No sandbox snapshot, no `StateTransitionRecord`
  (`transition=None`), zero `charge_sandbox_execution` (per A1a). Consumers already
  guard on `res.transition` (`entity.py`, `demo.py`), so `None` is safe.
- **Fail-closed / never crashes submit.** A `BudgetExceeded` or any error inside
  the session becomes an honest denied `CommandResult` (`budget_exceeded` /
  `memory_dispatch_error`), never an exception out of `submit`.
- **Flag-gated / byte-identical OFF.** Gated on `_durable_memory_enabled`
  (snapshot of `AUREL_DURABLE_MEMORY`). Flag OFF ⇒ the branch is skipped and
  `mem_*` falls through to the pre-existing rejection — byte-identical.

**Design note (identity model):** a normal `AgentCard` carries no writer-kind, so
agents get the least-privilege `agent` identity (cannot mint verified/procedural/
canon). Elevated writer kinds (operator/runtime) come from a card that declares
`memory_writer_kind`/`writer_kind`, or from the runtime's own paths
(`_record_command_memory`, promotion bridge) — not from an agent-submitted command.
This is the conservative, no-overclaim default; a richer card→writer-kind mapping
can be layered later without changing the dispatch.

## Files changed (connect)

- `src/agentic_runtime/__init__.py` — public exports (`d158cc3`).
- `src/agentic_runtime/runtime.py` — `MEMORY_TOOL_NAMES`/`MEMORY_READ_TOOLS`
  import, the `submit` interception, and `_dispatch_memory_command`.
- `tests/test_p6a9_memory_dispatch.py` — dispatch seal (7 tests).

## Validation

- `compileall` + `ruff` + `python -m mypy` clean on `__init__.py` and `runtime.py`.
- Dispatch seal `test_p6a9_memory_dispatch.py` — **7 passed** (funnel-routed
  mem_add; agent-can't-elevate; read-only search + live link; flag-OFF byte-identical
  rejection; update/delete reachable; malformed fails closed).
- Directly-affected regression (submit-path users + all memory seals): **212 passed**.
- Post-merge smoke on master: **89 passed**.
- **Full suite (post-connect seal):** `AGENTIC_SKIP_RECURSIVE_SMOKE=1
  .venv/bin/python -m pytest -q -p no:cacheprovider` → **8601 passed, 11 skipped,
  0 failed in 31:10 (1870.98s)** — +7 vs merge baseline 8594/11 (the new dispatch
  seal), zero regressions.

## Result

Track A is merged to `master` and fully connected: the memory subsystem is a
first-class public API and agents can invoke the governed `mem_*` tools through
`runtime.submit` (flag-gated, governed, no self-elevation, byte-identical when the
flag is OFF). **Not pushed** (local only). Recommended next: push `master` when
ready, then Track C remainder.
