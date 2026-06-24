# Active Task: P1.6.12 — Custos Shadow Runtime Projection & Submit Observability Hook

**Status:** ACTIVE

## Roadmap Position

- Last completed: P1.6.11 — Policy Resolution Context & Registry Binding
- Current active: **P1.6.12 — Custos Shadow Runtime Projection & Submit Observability Hook**
- Next planned: P1.6.13 — Policy Enforcement Adapter Hardening

P1.6.12 adds an observability-only bridge from `AgenticRuntime.submit()` to the Custos policy-card resolver. The P0 runtime remains authoritative for policy, approval, sandbox, budget, verifier, rollback, trace, and memory behavior. Custos shadow decisions are attached only as deterministic observation metadata.

## Objective

When explicitly enabled and supplied with an explicit `PolicyCardRegistry`, submit results may include:

```text
ObservationEnvelope.artifacts["policy_shadow_projection"]
```

The payload compares the runtime's effective P0 posture with the Custos `WOULD_*` shadow result and records alignment or mismatch codes. It is included before the state transition append, so it participates in the observation hash used by the trace record.

## Scope

- `RuntimePolicySnapshot` summarizes the authoritative runtime posture.
- `PolicyShadowProjection` records a deterministic, hash-ready comparison payload.
- `AgenticRuntime` and `build_runtime()` accept default-disabled shadow projection options.
- No registry means no projection, even if the flag is true.
- Flag false means no projection work.
- Resolver/projection failures degrade to observable `SHADOW_ERROR` metadata and never alter submit behavior.
- Projection hash excludes only the hash field itself.

## Non-scope

- No Custos runtime enforcement.
- No command blocking from policy cards.
- No approval activation from policy cards.
- No sandbox runtime bridge from sandbox policy cards.
- No default policy-card creation in runtime.
- No file discovery, database registry, or global policy state.
- Fail-closed apply, `run_shell` string rejection, and Bandit B310/B108 fixes are deferred.

## Tests

- `tests/test_policy_runtime_projection_p1612.py`
- `tests/test_runtime_custos_shadow_submit_p1612.py`

## Report

Full report: `agent/reports/P1.6.12_CUSTOS_SHADOW_RUNTIME_PROJECTION_REPORT.md`
