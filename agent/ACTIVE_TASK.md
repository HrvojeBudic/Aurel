# Active Task: P1.6.15 — Policy Violation Trace Hook

**Status:** ACTIVE

## Roadmap Position

- Last completed: P1.6.14 — Policy Resolution Trace Hook
- Current active: **P1.6.15 — Policy Violation Trace Hook**
- Next planned: P1.6.16 — Policy Test Harness

P1.6.15 records shadow policy violation evidence; it does NOT enforce policy decisions, write to the Ledger, activate approvals, block commands, or change runtime sandbox behavior.

## Objective

Introduce deterministic, hash-ready shadow violation evidence that records governance mismatch, drift, missing context, adapter errors, unresolved conflicts, or incomplete trace state — without changing runtime behavior.

## Scope

- `violation_trace.py` (new): violation taxonomy, envelope, classification, binding, canonical hash
- `resolution_result.py`: optional `violation_trace`, `violation_trace_hash`, `violation_trace_id`
- `resolver.py`: `_attach_violation_metadata()` after trace hook
- `runtime_projection.py`: violation metadata fields on `PolicyShadowProjection`
- `__init__.py`: minimal P1.6.15 exports

## Non-scope

- No Ledger write. No trace.py integration. No runtime.py changes.
- No enforcement. No command blocking. No approval activation. No sandbox changes.

## Tests

- `tests/test_policy_violation_trace_p1615.py` — pure violation object tests (32 tests)
- `tests/test_policy_resolution_violation_binding_p1615.py` — resolution binding tests (12 tests)
- `tests/test_policy_runtime_projection_violation_trace_p1615.py` — projection metadata tests (9 tests)

## Report

Full report: `agent/reports/P1.6.15_POLICY_VIOLATION_TRACE_HOOK_REPORT.md`
