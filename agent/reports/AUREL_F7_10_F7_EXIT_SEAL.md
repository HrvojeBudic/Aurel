# AUREL F7.10 — Corp / Business Plane Derived Exit Seal

_2026-07-11, branch `feat/f7-corp`. F7 is sealed — derived, and it flips two F6 seams live._

## What shipped

The F7 phase closes with a **derived** exit seal, a klijent-nula north-star projection, and CLI.

- **`f7_seal.py`** — `build_f7_exit_seal()` derives `SEALED` **only** when every slice (F7.0–F7.10)
  has both an importable module and a present report; any missing module/report `BLOCK`s the seal.
  It records the two F6 seams **flipped to live** — `watchtower_alerts` (F7.3) and
  `full_approval_workbench` (F7.8) — and completes the Output Passport (F7.4). A fresh UNAVAILABLE
  registry parks LATER surfaces (forecasting, KPI builder, ROI, billing, compliance, auto-risk) and
  SCI-FI features (business simulator, value-risk studio, R&D-NLP). Overclaim guards for those are
  hard-wired False; the two flipped claims and Output Passport completion are True iff SEALED.
- **`f7_projection.py`** — `F7RunProjection` composes the portfolio tree, cost attribution, budget
  governance, Watchtower feed, Evidence-Vault Output Passport, Risk Register, and Reflex Flywheel KPIs
  into one replayable klijent-nula view.
- **CLI** — `aurel corp seal [--json]` (derived seal), `aurel corp status` (north-star projection),
  alongside `aurel corp vault` / `aurel corp export`.

## Evidence

- `tests/test_p6f7_10_f7_exit_seal.py` — **7 passed**: the derived seal is SEALED with all 11 slices
  PASSED; a missing report BLOCKs deterministically; the two F6 seams are flipped (claims live);
  SCI-FI overclaim guards are False; the klijent-nula north-star scenario runs end-to-end (in-scope
  run + cost + budget deny alert + approval receipt + governed risk + replayable projection).
- Lint ratchet OK (E501 1492 ≤ baseline); ruff + mypy clean; F7 suite green; `aurel corp seal`
  prints SEALED.

## The F7 phase (what is now closed)

The Business Plane backbone is closed: clients/jobs over mandates (klijent nula), per-mandate cost
attribution, budget governance, Watchtower alerts, Evidence Vault + Output Passport, CORP read-model,
agency wizard, Risk Register, approval workbench context, and Reflex Flywheel KPIs + React surface.

## Boundary (honest)

SEALED means the Business Plane backbone is closed — NOT that forecasting, a billing console, a
business simulator, or auto risk detection exist (LATER / SCI-FI). The runtime binds no skill library,
so reflex KPI is honestly UNAVAILABLE via the registry until richer wiring lands.

## Next

- Merge `feat/f7-corp` → master.
- **F8** — Library time-travel / as-of replay (carried forward in UNAVAILABLE registry).