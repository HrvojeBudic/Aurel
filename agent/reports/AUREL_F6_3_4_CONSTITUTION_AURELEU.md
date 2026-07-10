# AUREL F6.3–F6.4 — Constitution Delegation + AurelEU Role-Fluid Persona

_2026-07-10, branch `feat/f6-aureleu`. The operator delegates autonomy; AurelEU speaks in role._

## What shipped

- **F6.3 — Constitution delegation windows** (`constitution/`, flag `AUREL_CONSTITUTION`):
  `DelegationWindow` (operator grant = scope + `autonomy_ceiling` A0–A6 + time window + `consent_ref`;
  a ceiling **cannot be A7_DENIED**). `require_delegation(level, category, windows, at)` is the
  cite-or-deny primitive: an autonomous action must cite an **active** window that covers it, else
  it's denied fail-closed with `drop_to_g0=True`. The constitutional floor holds — A7 is never
  covered, and a delegation cannot lift autonomy above a ceiling. `DelegationLedger` grants windows
  into the trace and projects the **active set purely from the trace** (zero own store);
  `delegation_grant_ref` / `autonomy_session_ref` fill the P1.4 operator-contract placeholders.
- **F6.4 — AurelEU role-fluid persona switch** (`front_server/aureleu.py`, flag `AUREL_AURELEU`):
  `AurelEUDispatcher.resolve_persona(role, mandate)` maps to a communication mode and **compiles the
  governed identity prompt** via the existing P1.4 `identity_prompt_compiler` (which already enforces
  kernel > contract > persona > mode dominance and detects contradictions). A persona switch is an
  **explicit, traced `persona_switch` transition**. The conversation engine now accepts a per-turn
  `system` prompt; the proposal dispatcher hands it the compiled prompt when AurelEU is enabled, and
  the static `CHAT_SYSTEM` (F5) otherwise. Persona is **expression, not authority** — the compiled
  prompt itself carries "persona cannot grant permissions"; authority stays the mandate (F6.2).
  This is the live half of the F5 `claims_aureleu_dispatcher_live` seam (sealed in F6.10).

## Evidence

- `tests/test_p6f6_3_delegation.py` — **10**: ceiling ≠ A7; is_active window; covers respects
  ceiling + category; cite-or-deny (active grant allowed, outside window / above ceiling / no grant →
  drop-to-G0); A7 never covered; grant projects from trace + active set + contract ref (expires → "").
- `tests/test_p6f6_4_aureleu_persona.py` — **9**: role→mode (+ default + persona_ref wins); compiles
  a governed prompt (≠ CHAT_SYSTEM, carries the no-authority law, hash-bound); different roles →
  different prompts/hashes; invalid mode fails closed; switch traces **only on change**; persona
  carries no authority field; dispatcher uses the compiled prompt when enabled and the static
  CHAT_SYSTEM when off (byte-identical).
- ruff + mypy clean; F5 + F6 front regression green.

## Boundary (honest)

F6.3 is the delegation **primitive + projection + cite-or-deny**; wiring "violation → G0 +
notification" into the AurelEU dispatch path (checking the window before dispatching a sub-agent) is
**F6.5**. Role→mode is a fixed table; operator-tunable persona routing is later. AurelEU resolves
persona from the default `config/aurel/*.yaml` sources; per-mandate persona overlays land with the
mandate persona bundle (F6.5+).

## Next

- **F6.5** — Constitution ↔ dispatch wiring (AurelEU checks the delegation window + mandate scope
  before dispatching; violation → G0 + notification), tying F6.2 + F6.3 + F6.4.
- **F6.6–F6.7** — DN mechanisms (surface `dual_kernel` σ/merge-gate; challenger + tripwire + panic).
