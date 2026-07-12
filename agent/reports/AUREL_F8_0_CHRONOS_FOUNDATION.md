# F8.0 — Chronos Foundation Seal Report

**Date:** 2026-07-13  
**Branch:** `feat/f8-time-plane`  
**Slice:** F8.0 — replay / fork / diff engine + CLI  
**Flag:** `AUREL_CHRONOS` (default OFF)

## Delivered

| Module | Role |
|--------|------|
| `chronos/replay.py` | `ChronosReplay.from_run` — verify chain + CAS checkout audit |
| `chronos/fork.py` | `ChronosFork.fork_at` — worldline fork at transition index |
| `chronos/diff.py` | `ChronosDiff.compare` — deterministic transition signature diff |
| `chronos/__init__.py` | `flag_enabled()` + exports |
| `cli_modules/chronos_commands.py` | `aurel chronos replay|fork|diff` |
| `cli.py` | chronos subparser registration |

## Validation

```bash
.venv/bin/python -m pytest tests/test_p6f8_0_chronos.py -q   # 7 passed
.venv/bin/python -m compileall src/agentic_runtime/chronos
```

## Invariants held

- Read-only on parent run (fork mints child; replay/diff zero mutation)
- Flag OFF ⇒ CLI returns UNAVAILABLE JSON/text
- Unretained runs ⇒ `replayable=False` with explicit reason
- Tampered CAS state ⇒ `mismatch_at=0`
- Parent events unchanged after fork

## Truth labels

| Surface | Label |
|---------|-------|
| Chronos replay/fork/diff | LIVE when `AUREL_CHRONOS=1` |
| Irreversibility gate (F8.1) | UNAVAILABLE |
| System screen (F8.2+) | UNAVAILABLE |

## Next

F8.1 — `chronos/irreversibility.py` + `fork_gate.py` + runtime.submit hook (escalation-only evidence).
