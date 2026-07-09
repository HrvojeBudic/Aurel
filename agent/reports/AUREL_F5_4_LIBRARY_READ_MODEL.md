# AUREL F5.4 — Unified Library Read-Model

_2026-07-10, branch `feat/f5-front-v1`. One projection over memory + docs + export bundle._

## What shipped

`GET /read/library` returns one **read-only composition** of three trace-derived ingredients —
Library is a *projection name, not a new store*.

- **`front_server/library.py`** — `LibraryReadModel` composes:
  - `MemoryProjection.from_trace` → `memory_by_tier()` (current ids grouped by truth tier),
    `versions(id)` (supersession chain, `[]` for unknown ids), `provenance_chain(id)` (version
    chain + incident edges), `rejected()` (governance-denied writes, audit-kept).
  - `doc_registry` → `assets()` (canonical docs: repo-relative path + existence, read-only).
  - `TraceExportManifest` → `manifest()`, **injected** when the P5 export pipeline built one;
    otherwise an honest `{"status": "UNAVAILABLE", ...}` seam (never a fabricated manifest).
  - `min_truth_state()` → the **MIN** (weakest active tier) across current records — truth
    labels propagate as MIN, not MAX.
- **`front_server/read_models.py`** — `/read/library` registered; optional `?memory_id=` drills
  into one record's provenance chain.

## Evidence

- Seal `tests/test_p6f5_4_library_read_model.py` — **7 passed**: composes memory + docs +
  manifest (README asset exists; promoted record in `verified`, other in `candidate`; rejected
  audit present); Library == direct `MemoryProjection` (rejected + tier grouping identical);
  versions/provenance (`[id]` known, `[]` unknown, `relates_to` edge surfaced); MIN truth state
  = weakest tier (`candidate`); injected manifest ⇒ AVAILABLE; zero-write + deterministic;
  live via `/read/library` (empty memory ⇒ honest empty tiers, docs still listed,
  `claims_time_travel` False).
- ruff clean; mypy clean. Full F5 + front_server + conversation regression green (**59 passed**).

## Boundary (honest)

The **export manifest** is composed by the P5 trace-export pipeline (needs redaction/inclusion
decisions over P5-E material); the Library projects it only when injected, else declares it
UNAVAILABLE. **Time-travel / as-of replay is F8** — `CLAIMS_LIBRARY_TIME_TRAVEL` is hard-wired
`False`. Record **content** is only present when a durable store is supplied (else `None`, never
fabricated — inherited from `MemoryProjection`).

## Next

- **F5.5** — HQ.Command read-model (live run status + F5.2 approval inbox + budget burn +
  Watchtower seam) composed on this same registry.
- **F5.8** — React `LibraryExplorer` reading `/read/library`.
