# F8.5 — Succession Drill + System Panel Seal Report

**Date:** 2026-07-13  
**Branch:** `feat/f8-time-plane`  
**Slice:** F8.5 — succession drill CLI + System React panel  
**Flags:** `AUREL_CHRONOS` (drill), `AUREL_SYSTEM` (System reads + panel)

## Delivered

| Surface | Role |
|---------|------|
| `succession_drill.run_succession_drill()` | export → restore → verify → replay on isolated copy |
| `aurel drill succession [--sample N] [--out PATH]` | CLI with honest discrepancy reporting |
| `SystemPanel.tsx` | Audit, usage, model routing, policies, archive via frontClient |
| `frontClient.system*` | Five `/read/system/*` builders |

## Validation

```bash
.venv/bin/python -m pytest tests/test_p6f8_5_succession_drill.py -q   # 7 passed
.venv/bin/python -m pytest tests/test_p6f8_*.py -q                              # 41 passed
cd web/shell && npm test -- system-surface.test.ts
```

## Invariants held

- Drill operates on isolated copy; live trace bytes unchanged
- Tamper on copy ⇒ discrepancy in replay (never silent PASS)
- React panel zero direct fetch/WebSocket; fixture mode honest
- System reads operator-only, zero-write

## Next

F8.6 — derived F8 exit seal + `aurel chronos seal/status`.
