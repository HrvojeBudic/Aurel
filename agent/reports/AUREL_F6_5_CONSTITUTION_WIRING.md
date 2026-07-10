# AUREL F6.5 — Constitution ↔ Dispatch Wiring

_2026-07-10, branch `feat/f6-aureleu`. A sub-agent dispatch needs both authority and autonomy._

## What shipped

F6.5 ties the three F6 primitives together at the AurelEU dispatch boundary. Before AurelEU
dispatches a sub-agent (an autonomous action), it must clear a single pre-dispatch gate that
requires **both**:

- a valid, **in-scope mandate** (authority — F6.0/F6.2): the `mandate_id` resolves, is not
  expired, and the intended action (tool / path / risk) is within the mandate's scope; and
- a cited **active delegation** (autonomy — F6.3): an active `DelegationWindow` covers the
  requested autonomy level + category.

Any gap ⇒ fail-closed: no dispatch, a traced `constitution_violation` praxis event (carrying the
`mandate_id` via the F6.1 field), and `drop_to_g0=True` on the returned `DispatchAuthorization`.

- **`front_server/aureleu.py`** — `AurelEUDispatcher.authorize_dispatch(...)` runs mandate
  presence/expiry → mandate scope (reusing `evaluate_mandate_scope_check`, F6.2) → delegation
  coverage (`require_delegation`, F6.3). `DispatchAuthorization` is the verdict;
  `_deny_dispatch` records the violation.

## Evidence

- `tests/test_p6f6_5_constitution_wiring.py` — **6**: mandate + delegation ⇒ allowed (cited
  delegation id, no violation); missing delegation ⇒ drop-to-G0 + one violation carrying the
  mandate_id; out-of-scope path ⇒ DENY ("outside mandate paths") + violation; unknown / expired
  mandate ⇒ fail-closed; autonomy above the delegated ceiling ⇒ denied.
- ruff + mypy clean. Full F6 suite (F6.0–F6.5) green (**52**); F5+F6 front regression green.

## Boundary (honest)

`authorize_dispatch` is AurelEU's **pre-flight** gate (refuse-to-dispatch + notification). The
hard runtime enforcement remains the F6.2 mandate gate in `runtime.submit`; the two are
complementary (AurelEU stops the dispatch early; the runtime gate is the backstop if a command
still reaches it). Actual runtime **profile** switching to G0 on violation (vs. the recorded
`drop_to_g0` signal + notification) is a governance-profile refinement carried forward.

## Next

- **F6.6–F6.7** — DN mechanisms: surface `dual_kernel` σ-governor (graduated autonomy) + merge-gate
  (weighted verdict, absolute verifier veto); challenger pass + anti-stagnation tripwire + `aurel panic`.
- **F6.8–F6.10** — Board two-persona generator, AUREL_CRO surface, derived exit seal + merge.
