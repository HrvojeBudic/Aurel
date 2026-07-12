# F8.4 — Library Time-Travel Seal Report

**Date:** 2026-07-13  
**Branch:** `feat/f8-time-plane`  
**Slice:** F8.4 — Library as-of via `memory_asof`  
**Flag:** `AUREL_SYSTEM` (shared with F8.2/F8.3)

## Delivered

| Surface | Role |
|---------|------|
| `LibraryReadModel.as_of(valid_time, transaction_time)` | Bitemporal library projection via `AsOfView.from_fabric` |
| `MemoryProjection.from_as_of_records()` | Record-set → tier-grouped read snapshot |
| `claims_library_time_travel()` | Derived seam flip (`True` iff `AUREL_SYSTEM`) |
| `/read/library?as_of=T` | Live read with optional `valid_time` / `transaction_time` |

## Validation

```bash
.venv/bin/python -m pytest tests/test_p6f8_4_library_time_travel.py -q
.venv/bin/python -m pytest tests/test_p6f8_*.py -q
.venv/bin/python -m pytest tests/test_p6f5_4_library_read_model.py -q
```

## Invariants held

- As-of is pure projection (clock-free bitemporal semantics from A0)
- Empty / missing `as_of` ⇒ current library (byte-identical to pre-F8.4 shape)
- Flag OFF ⇒ `claims_time_travel` False; `/read/library?as_of=` returns UNAVAILABLE
- No fabricated history — only records matching the as-of interval

## Next

F8.5 — Succession drill CLI + System React panel.
