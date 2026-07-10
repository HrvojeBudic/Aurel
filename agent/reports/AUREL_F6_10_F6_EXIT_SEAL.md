# AUREL F6.10 — AurelEU / Constitution / Mandate Derived Exit Seal

_2026-07-10, branch `feat/f6-aureleu`. F6 is sealed — derived, and it flips two F5 seams live._

## What shipped

The F6 phase closes with a **derived** exit seal, a north-star run projection, and CLI.

- **`f6_seal.py`** — `build_f6_exit_seal()` derives `SEALED` **only** when every slice (F6.0–F6.10)
  has both an importable module and a present report; any missing module/report `BLOCK`s the seal.
  It records the two F5 seams **flipped to live** — `aureleu_role_fluid_dispatcher` (F6.4/F6.5) and
  `mandate_resolution_enforcement` (F6.0–F6.2) — and a fresh UNAVAILABLE registry with the parked
  SCI-FI features: `multi_jurisdiction_sovereigns`, `zero_knowledge_federation`,
  `crypto_nonrepudiation_ledger` (P1.8/P2.2), plus carried-forward `full_approval_workbench` (F7),
  `watchtower_alerts` (F7), `library_time_travel` (F8), `wss_tls_remote_transport`. Five overclaim
  guards: the three SCI-FI claims hard-wired False; the two flipped claims True iff SEALED.
- **`f6_projection.py`** — `F6RunProjection` composes Signal history + the AurelEU governance state
  (mandates, delegations, persona switches, DN) + constitution violations into one replayable view.
- **CLI** — `aurel aureleu seal [--json]` (derived seal), `aurel aureleu status` (north-star
  projection), alongside `aurel aureleu panic`.

## Evidence

- `tests/test_p6f6_10_f6_exit_seal.py` — the derived seal is SEALED with all 11 slices PASSED; a
  missing report BLOCKs deterministically; the two F5 seams are flipped (claims live); the SCI-FI
  overclaim guards are False; the north-star scenario runs end-to-end (Signal under a mandate →
  AurelEU authorizes an in-scope dispatch and denies an out-of-scope one → replayable projection).
- ruff + mypy clean; full F5 + F6 regression green; `aurel aureleu seal` prints SEALED.

## The F6 phase (what is now closed)

Authority is a **mandate** (resolved, content-hashed, in every trace record, enforced fail-closed
in `runtime.submit`); autonomy is **delegated** by operator windows (cite-or-deny → G0); **AurelEU**
is the role-fluid dispatcher that compiles the governed identity prompt per (role, mandate) and
requires **both** a valid mandate and a cited delegation before any autonomous dispatch; the **DN**
safeguards (σ graduated autonomy, absolute verifier veto, challenger, tripwire, `aurel panic`) and
the **AUREL_CRO** surface + two-persona Board options round it out.

## Boundary (honest)

SEALED means the mandate + constitution + AurelEU + DN backbone is closed — NOT that
multi-jurisdiction sovereigns, a zero-knowledge federation, or a cryptographic non-repudiation
ledger exist (parked / P1.8 / P2.2). Runtime G0 **profile** switching on violation (vs. the recorded
`drop_to_g0` + notification) and the full approval workbench remain forward seams.

## Next

- Merge `feat/f6-aureleu` → master.
- **F7** — Corp screen: Business Plane (clients, receipts, Watchtower alerts).
