# AUREL F6.6–F6.7 — DN Mechanisms (graduated autonomy, merge veto, challenger, tripwire, panic)

_2026-07-10, branch `feat/f6-aureleu`. Surfacing the dual-kernel + the negotiation safeguards._

## What shipped

- **F6.6 — graduated autonomy + weighted merge verdict** (`front_server/dn.py`, reuse flag
  `AUREL_DUAL_KERNEL`): read-only surfacing of the existing `dual_kernel`. `graduated_autonomy(card)`
  exposes the σ autonomy index (0–10, higher = less freedom); `evaluate_merge(ctx)` runs the
  `MergeGate` and reports the weighted verdict — with the **verifier veto absolute**: a failed
  `verifier_result` is always a blocker and can never be mergeable, whatever the other signals say.
  `GET /read/aureleu/dn` declares availability honestly (UNAVAILABLE when the dual kernel is off).
- **F6.7 — challenger + tripwire + panic** (`dn/`): `ChallengerPass` runs an **advisory**
  second-opinion over a risky proposal through the F2 router (a provider failure is an honest
  UNAVAILABLE dissent, never a fabricated endorsement; it never executes). `check_stagnation(trace)`
  is the anti-stagnation tripwire — a run of identical non-terminal transitions with no progress
  trips it **fail-closed**. `panic(runtime, reason)` is the `aurel panic` kill-switch: a governed
  `aurel_panic` record + drop-to-G0, **never silent**; wired as `aurel aureleu panic [--reason]`.

## Evidence

- `tests/test_p6f6_6_dn_autonomy_merge.py` — **7**: bounded autonomy index; index varies with
  authority; passing verifier ⇒ mergeable; **failed verifier veto is absolute** (not mergeable,
  `state_verification` blocker); deterministic verdict; DN read-model availability + live registry.
- `tests/test_p6f6_7_dn_challenger_panic.py` — **7**: challenger surfaces advisory dissent; router
  failure ⇒ UNAVAILABLE (never a fake OK); challenger doesn't execute; tripwire fires on stagnation
  and stays quiet on progress; panic records a governed halt (→ G0) and is never silent.
- ruff + mypy clean; full F6 suite (F6.0–F6.7) green (**66**); `aurel aureleu panic` verified.

## Boundary (honest)

F6.6 is **read-only surfacing** — the σ-governor and merge-gate already live in `dual_kernel/`
(flag `AUREL_DUAL_KERNEL`); F6.6 changes no default path. `aurel panic` records the governed halt
signal; actually suspending a running daemon is a LATER concern (the daemon isn't built) — today
panic is the replayable signal everything downstream must honor. The challenger is advisory input
to a proposal, not an automatic gate.

## Next

- **F6.8** — two-persona planning → Board option generator (extends F5.6).
- **F6.9** — AUREL_CRO surface (AurelEU home) + read models + React.
- **F6.10** — derived F6 exit seal (flips the F5 aureleu/mandate seams to SEALED) + CLI + merge.
