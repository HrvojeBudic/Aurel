# F8.1 — Irreversibility Gate Seal Report

**Date:** 2026-07-13  
**Branch:** `feat/f8-time-plane`  
**Slice:** F8.1 — fork-before-irreversible as HITL evidence  
**Flag:** `AUREL_CHRONOS_FORK_GATE` (default OFF)

## Delivered

| Module | Role |
|--------|------|
| `chronos/irreversibility.py` | `classify_irreversibility()` + `influence_is_escalation_only()` |
| `chronos/fork_gate.py` | `evaluate_fork_gate()` — ephemeral twin simulation (reuse dual_kernel merge gate) |
| `runtime.py` | Gate between mandate (F6.2) and approval (HITL); attaches evidence to approval context |

## Validation

```bash
.venv/bin/python -m pytest tests/test_p6f8_1_irreversibility.py -q   # 7 passed
.venv/bin/python -m pytest tests/test_p6f8_0_chronos.py -q           # 7 passed
```

## Invariants held

- Flag OFF ⇒ fork gate block skipped (byte-identical submit path)
- Irreversible + twin UNAVAILABLE ⇒ fail-closed before execution
- Fork verdict is **evidence only** (`is_escalation_only=True`); R5 denial still enforced by HITL
- Reversible writes skip fork simulation
- Praxis event `fork_gate_evidence` recorded (speculative, non-authoritative)

## Next

F8.2 — System surface skeleton + audit/usage read-models (`AUREL_SYSTEM`).
