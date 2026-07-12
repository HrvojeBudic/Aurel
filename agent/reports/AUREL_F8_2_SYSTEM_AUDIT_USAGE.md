# F8.2 — System Surface: Audit + Usage Seal Report

**Date:** 2026-07-13  
**Branch:** `feat/f8-time-plane`  
**Slice:** F8.2 — System audit log + usage read-models  
**Flag:** `AUREL_SYSTEM` (default OFF)

## Delivered

| Module | Role |
|--------|------|
| `front_server/system_read_model.py` | `SystemReadModel.audit_log()` + `.usage()` |
| `front_server/read_models.py` | `GET /read/system/audit`, `/read/system/usage` |
| `aurel_shell/boundaries.py` | `build_system_read_model_projections()` |

## Validation

```bash
.venv/bin/python -m pytest tests/test_p6f8_2_system_audit_usage.py -q   # 7 passed
.venv/bin/python -m pytest tests/test_p6f8_*.py -q                      # 21 passed
```

## Invariants held

- Zero-write read-only projections
- Operator-only (`operator_only: True` on all responses)
- Flag OFF ⇒ `available: False`, `status: UNAVAILABLE`
- Empty filter ⇒ empty list (not UNAVAILABLE)
- Audit deterministic (kind/mandate/agent/time + pagination)
- Usage from live `budget.snapshot()` + policy remaining + optional corp budget rollup

## Next

F8.3 — model-routing + policy-browser + archive-status read-models.
