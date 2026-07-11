# AUREL F7.0 — Corp domena: Client + Job registry + klijent nula

_2026-07-11, branch `feat/f7-corp`. First slice of the Business Plane — authority stays the mandate._

## What shipped

The Business Plane opens with its **domain**: a thin business layer over the mature F6 governance
machinery. A **job** (posao) is the business wrapper around one or more mandates; a **client** is the
party the work is for. Additive behind `AUREL_CORP` (default OFF ⇒ byte-identical F6 world — nothing in
the runtime imports `corp/` yet).

- **`corp/domain.py`** — `ClientRecord` (frozen: `client_id`, `name`, `notes`) and `JobRecord` (frozen:
  `job_id`, `client_id`, `mandate_ids: tuple`, `repos: tuple`, `status: JobStatus`, `title`). Both are
  content-hashed (`sha(canonical_json(...))`, `created_at` excluded — content identity, not timestamp),
  mirroring `Mandate`. A `JobRecord` is **un-constructible without a `client_id`** (`ValueError`) — you
  cannot mint a job that hides who it is for (structural no-overclaim, the F7 analogue of "a mandate is
  un-constructible without a scope"). `status` is a closed-world `JobStatus` enum
  (PROPOSED/ACTIVE/PAUSED/CLOSED) — no free-form strings. `.make()` helpers mint ids like `Mandate.make`.
  Flag helper `flag_enabled()` reads `AUREL_CORP`.
- **`corp/registry.py`** — `CorpRegistry.from_records(clients, jobs, *, mandate_registry=None)` resolves
  `client_id`/`job_id` to records (fail-closed ⇒ `None`, or `ClientNotFound`/`JobNotFound` on the
  `_or_raise` variants) and — the point of F7.0 — **validates references at build time, fail-closed**:
  every job's `client_id` must resolve to a known client, and when a `MandateRegistry` is given, every
  `mandate_id` a job references must resolve there too. A job pointing at a client or authority that does
  not exist is un-buildable (`CorpValidationError`). The registry holds the validated `MandateRegistry`
  reference (**reused, never copied**) so F7.1/F7.5 can walk job → mandate → scope. `jobs_for_client`,
  `client_ids`/`job_ids`, and `canonical_hash` are all deterministic (sorted).
- **`corp/default.py`** — **klijent nula** (the own repo as client zero): `client_zero()` +
  `client_zero_job()` (one job under the passthrough `DEFAULT_MANDATE_ID`), and
  `default_corp_registry()` which validates the seed against the mandate `default_registry` so the seed's
  mandate reference is **proven at build**, not assumed. Klijent nula is where every F7 slice is proven
  end-to-end before any real client.

## Evidence

- Seal `tests/test_p6f7_0_corp_domain.py` — **13 passed**: job requires non-empty `client_id`
  (no-overclaim) + closed-world status; client requires id+name; `.make` mints ids; content hash
  deterministic + content-addressed (created_at excluded); registry resolves + fails closed
  (`None`/`ClientNotFound`/`JobNotFound`); **build rejects unknown client reference** and **unknown
  mandate reference** (fail-closed); build skips mandate validation honestly when no registry is given;
  `jobs_for_client` deterministic; registry hash deterministic; klijent nula resolves + references real
  authority; flag defaults OFF.
- ruff clean; mypy clean (4 files). Regression `test_p6f6_0/1/2` (mandate — imported by `corp.default`)
  + F7.0 seal: **40 passed** (0 failed).

## Boundary (honest)

`corp/` is **data model + resolution only**. A job does **not** grant authority — authority stays the
mandate (F6), enforced fail-closed in `runtime.submit`. Client/Job records are business metadata;
`mandate_ids` are references into the existing `MandateRegistry`, never a copy. Nothing in the runtime
imports `corp/` yet, so the flag-OFF world is byte-identical F6. Cost attribution (F7.1), Watchtower
(F7.3), Evidence Vault (F7.4), and the CORP surface read-model (F7.5) build on this.

## Next

- **F7.1** — Cost attribution: additive `per_mandate` bucket in `budget.py` + `CostAttributionView`
  pivot (client → job → mandate) over the `mandate_id` F6.1 already carries in every trace record.
- Then F7.5 (portfolio map) closes the walking skeleton; F7.3 (Watchtower) flips the oldest F5 seam.
