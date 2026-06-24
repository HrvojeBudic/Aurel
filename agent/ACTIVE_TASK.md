# Active Task: P1.6.14 — Policy Resolution Trace Hook

**Status:** ACTIVE

## Roadmap Position

- Last completed: P1.6.13 — Policy Conflict Algebra & Strictest-Wins Rules
- Current active: **P1.6.14 — Policy Resolution Trace Hook**
- Next planned: P1.6.15 — Policy Violation Trace Hook

P1.6.14 creates trace-compatible policy resolution evidence; it does NOT write to the Ledger, enforce policy decisions, activate approvals, block commands, or change runtime sandbox behavior.

## Objective

Introduce a formal trace-compatible evidence envelope for Custos policy resolution, strictest-wins conflict algebra, and runtime shadow projection. The system produces deterministic trace-compatible metadata with hashes and identifiers, making policy resolution audit-ready without writing to the real Ledger and without changing runtime behavior.

## Scope

- `resolution_trace.py` (new): `PolicyResolutionTraceEvent`, `PolicyResolutionTraceEnvelope`, `PolicyResolutionEvidenceRef`, `PolicyTraceBinding`, builder functions, canonical dict/hash
- `resolution_result.py`: optional `resolution_trace`, `resolution_trace_hash`, `resolution_trace_id` fields on `ResolvedPolicySet`
- `resolver.py`: `_attach_trace_metadata()` builds trace envelope from resolution + conflict metadata
- `runtime_projection.py`: `resolution_trace_id`, `resolution_trace_hash` fields on `PolicyShadowProjection`
- `__init__.py`: ~8 new public exports

## Non-scope

- No Ledger write. No trace.py integration. No AurelTrace integration.
- No enforcement. No command blocking. No approval activation. No sandbox changes.
- No runtime.py changes. No AgenticRuntime.submit() changes.

## Tests

- `tests/test_policy_resolution_trace_p1614.py` — pure trace object tests (32 tests)
- `tests/test_policy_resolver_trace_hook_p1614.py` — resolver integration tests (14 tests)
- `tests/test_policy_runtime_projection_trace_p1614.py` — projection trace metadata tests (9 tests)

## Report

Full report: `agent/reports/P1.6.14_POLICY_RESOLUTION_TRACE_HOOK_REPORT.md`
