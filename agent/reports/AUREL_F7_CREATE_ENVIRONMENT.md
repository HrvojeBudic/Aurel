# AUREL F7 — corp_create_environment: governed creation + trace-projected registry

_2026-07-11, branch `feat/f7-corp-create-env`. Closes the third F7 forward seam — klijent nula is now fully creatable._

## What shipped

The Agency wizard (F7.6) drafted a {client + job + mandate} and could preview it, but could not *create*
one. This closes the loop: a created environment is a **governed trace record**, and the Corp registry the
read models use is **rebuilt from the trace** — so a created client/job/mandate persists and appears in the
portfolio, cost, budget, and workbench views. Additive; byte-identical to klijent nula when nothing was
created.

- **`corp/environment.py`**:
  - `record_environment(trace, *, client_name, job_title, scope, …)` appends a governed `corp_environment`
    praxis event (hash-chained, like the Risk Register / Board journal), carrying the client + job +
    mandate as a JSON payload. Ids are **content-hashed** (deterministic, replayable). Returns the record
    and the created `{client_id, job_id, mandate_id}`. `record_environment_from_payload` parses the
    wizard's `to_proposal()` args.
  - `corp_registry_from_trace(trace)` rebuilds a `CorpRegistry` seeded by klijent nula (the default) plus
    every environment created on the trace — the created mandate is folded into the projected
    `MandateRegistry` so cost/budget attribution resolves. **With no environment events it is
    byte-identical to `default_corp_registry()`** (same canonical hash).
- **`proposal_dispatcher.py`** intercepts an `act` proposal with `tool == "corp_create_environment"` and
  routes it to `record_environment_from_payload` (governed append, never the sandbox executor); invalid
  input fails closed.
- **Read models rewired** (`corp_read_model`, `workbench`, `f7_projection`, the `aurel corp vault/export`
  CLI): the Corp registry fallback is now `corp_registry_from_trace(inner.trace)` instead of the static
  `default_corp_registry()`, so created environments show up everywhere the registry is used.

## Evidence

- Seal `tests/test_p6f7_create_environment.py` — **6 passed**: an empty-trace registry equals klijent nula
  (same canonical hash — byte-identical); a recorded environment appears in the projected registry with a
  resolvable mandate; ids are deterministic/replayable; the wizard `to_proposal()` → dispatcher → the
  created client shows in the CORP portfolio (and via `/read/corp/portfolio`); invalid input fails closed.
- Rewire regression (corp read-model / workbench / f7-exit-seal / evidence-vault / cost / budget / seam
  wires / create-env / F5.0a / F5.2): **79 passed, 0 failed**. ruff + mypy clean.

## Boundary (honest)

Environment creation is a **governed front-server append** (like the Board journal and the Risk Register),
not a `runtime.submit` sandbox tool — it is operator config, recorded as governed evidence. The registry is
a pure projection over the trace (seeded by klijent nula); it does not persist to a separate store, so it
is replayable and byte-identical when empty. Content-hashed ids mean creating the *same* environment twice
is idempotent (same ids). Klijent nula is now truly end-to-end: an operator can create a client/job/mandate
through the one door and see it drive cost, budget, portfolio, and workbench.

## Next

- **F8 — Time Plane (Chronos + System ekran).**
