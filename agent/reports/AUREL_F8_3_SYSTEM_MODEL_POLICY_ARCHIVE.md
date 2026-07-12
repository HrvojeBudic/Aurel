# F8.3 — System Model / Policy / Archive Seal Report

**Date:** 2026-07-13  
**Branch:** `feat/f8-time-plane`  
**Slice:** F8.3 — model-routing + policy browser + archive status  
**Flag:** `AUREL_SYSTEM` (shared with F8.2)

## Delivered

| Surface | Role |
|---------|------|
| `SystemReadModel.model_routing()` | ModelRouter profiles/providers/health + promotion gate evidence |
| `SystemReadModel.policy_browser()` | PolicyCardRegistry enumeration + `canonical_hash`, secrets masked |
| `SystemReadModel.archive_status()` | Persistent verify + integrity assessment + receipt backlog |
| `/read/system/{model_routing,policies,archive}` | Registered in read_models |

## Validation

```bash
.venv/bin/python -m pytest tests/test_p6f8_3_system_model_policy_archive.py -q   # 7 passed
.venv/bin/python -m pytest tests/test_p6f8_*.py -q                              # 28 passed
```

## Invariants held

- Read-only enumeration; `grants_authority: False` on policy browser and promotion gates
- Secrets masked (`<masked:sha[:8]>` fingerprint discipline)
- Archive honestly UNAVAILABLE for in-memory trace
- Flag OFF ⇒ UNAVAILABLE on all `/read/system/*`

## Next

F8.4 — Library time-travel (`LibraryReadModel.as_of`, flip `CLAIMS_LIBRARY_TIME_TRAVEL`).
