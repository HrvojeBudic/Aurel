# AUREL F6.0–F6.2 — Mandate Walking Skeleton (object → trace → enforcement)

_2026-07-10, branch `feat/f6-aureleu`. `mandate_id` stops being a passenger and becomes authority._

## What shipped

The F6 walking skeleton: a mandate is now a real runtime object that resolves, rides every
governed trace record, and is **enforced fail-closed** before execution. This closes the F5 N5
seam ("PROPOSE gated on the room's mandate → full enforcement in F6").

- **F6.0 — Mandate object + registry** (`mandate/`, flag `AUREL_MANDATE`): `Mandate` (versioned,
  content-hashed, **un-constructible without a declared `MandateScope`** — structural
  no-overclaim), `MandateScope` (paths / repos / client_id / budget / allowed_tools / risk
  ceiling), `MandateRegistry` (resolves `mandate_id`, fail-closed on unknown, reuses the existing
  `PolicyCardRegistry` for the policy bundle), and a **default passthrough** mandate reproducing F5.
- **F6.1 — `mandate_id` in the trace** (`core_types.py`, `trace.py`, `conversation.py`): additive
  `mandate_id` field on the five governed records (Praxis / Approval / RuntimeStatusTransition /
  MemoryGovernance / BudgetDecision) with **conditional hash inclusion** — an empty `mandate_id`
  leaves every pre-F6 hash byte-identical. It survives both InMemory replay and **persistent
  reload** (stamped in `_locked_append`, restored in `_record_from_event`). Conversation turns
  carry a *real* mandate only (the "default" sentinel stays empty → byte-identical).
- **F6.2 — Scope-enforcement gate** (`mandate/enforcement.py`, `runtime.py`): a new gate in
  `runtime.submit` **between the policy resolver and approval** (fail-closed). It only *tightens*:
  it runs after the policy engine has verified `card.authority` and can only add a denial. Checks:
  tool allow-list, risk ceiling, write-path confinement, expiry. An out-of-mandate command is
  **DENIED before approval**, nothing executes. Conservatively gated so the default path is
  byte-identical: no registry / flag off / default mandate / non fail-closed governance ⇒ the gate
  does nothing. `AgentCard.mandate_id` binds a card to a mandate; `build_runtime(mandate_registry=…)`.

## Evidence

- `tests/test_p6f6_0_mandate.py` — **9**: no-overclaim (scope required), deterministic content
  hash, expiry fail-closed, registry resolve + fail-closed, order-independent registry hash.
- `tests/test_p6f6_1_mandate_trace.py` — **7**: empty `mandate_id` ⇒ hash unchanged; all five
  records carry it; replay surfaces it only when present; conversation default stays byte-identical;
  real mandate is traced; **survives persistent reload**.
- `tests/test_p6f6_2_mandate_enforcement.py` — **11**: pure gate (path / tool / risk / fail-closed);
  end-to-end path + tool denial **before approval** with zero execution; in-scope passes the gate;
  flag-off / default-sentinel / shadow-mode all skip the gate.
- ruff + mypy clean; broad runtime/policy/approval/exec/dual_kernel regression green.

## Boundary (honest)

Policy-card aggregation over `mandate.policy_card_ids` (strictest-wins via the resolver) is a
declared follow-up seam — F6.2 enforces the concrete scope (paths / tools / risk / expiry). Path
confinement reads well-known arg keys (`path`, `file_path`, …); a tool using an exotic key isn't
confined yet. Enforcement is G0–G3 (ENFORCE_FAIL_CLOSED) only, per doctrine. Persona/role
resolution (AurelEU dispatcher) and delegation windows are the next slices (F6.3–F6.5).

## Next

- **F6.3** — Constitution delegation windows (cite-or-deny, violation → G0).
- **F6.4** — AurelEU role-fluid persona switch (wires `identity_prompt_compiler`), flipping the F5
  `claims_aureleu_dispatcher_live` seam.
