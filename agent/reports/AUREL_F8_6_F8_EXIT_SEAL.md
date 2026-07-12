# F8.6 — F8 Time Plane Derived Exit Seal Report

**Date:** 2026-07-13  
**Branch:** `feat/f8-time-plane`  
**Slice:** F8.6 — derived exit seal + north-star projection + CLI  
**Flags:** `AUREL_CHRONOS`, `AUREL_CHRONOS_FORK_GATE`, `AUREL_SYSTEM` (all default OFF)

## Delivered

| Surface | Role |
|---------|------|
| `f8_seal.build_f8_exit_seal()` | Derived checklist F8.0→F8.6; flips `library_time_travel` seam |
| `f8_projection.F8RunProjection` | North-star §7: replay + System forensics + Library as-of claim |
| `aurel chronos seal` | Prints SEALED/BLOCKED from module+report presence |
| `aurel chronos status` | JSON projection of Time Plane run |

## Validation

```bash
.venv/bin/python -m pytest tests/test_p6f8_6_f8_exit_seal.py -q   # 7 passed
.venv/bin/python -m pytest tests/test_p6f8_*.py -q                              # 48 passed
AUREL_CHRONOS=1 aurel chronos seal
```

## Invariants held

- Seal derived from slice module + report presence (never self-assigned)
- Missing report ⇒ BLOCKED; flip claims False when BLOCKED
- SCI-FI / LATER guardovi hard-wired False
- `library_time_travel` live iff SEALED (F8.4 flip proven)
- North-star §7: retained run replays; System reads live; succession drill passes

## Phase complete

F8 Time Plane **SEALED** on `feat/f8-time-plane`. Next: full suite + merge → master.
