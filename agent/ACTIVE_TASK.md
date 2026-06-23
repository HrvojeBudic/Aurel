# Active Task: P1.6.11 — Policy Resolution Context & Registry Binding

**Status:** ACTIVE

## Roadmap Position

- Last completed: P1.6.10H — Runtime Security, Coverage & Governance Truth Hotfix
- Current active: **P1.6.11 — Policy Resolution Context & Registry Binding**
- Next planned: P1.6.12 — Policy Enforcement Adapter / Shadow Runtime Projection

P1.6.11 teaches Custos how to assemble the correct policy lawbook and resolution context before judgment. It binds explicit policy-card lists to deterministic registry selection, runtime-like metadata to `PolicyResolutionContext`, conservative risk-vocabulary mapping, and the existing Custos v0 resolver.

## Objective

Policy cards plus runtime-like request metadata now flow through:

```text
explicit policy cards
  -> PolicyCardRegistry
  -> deterministic PolicyResolutionContext
  -> applicable cards
  -> Custos v0 resolver
  -> ResolvedPolicySet in SHADOW mode
```

The output remains `WOULD_*`. P1.6.11 does not enforce resolver outcomes through `AgenticRuntime.submit()`.

## Scope

### Registry binding

- `PolicyCardRegistry` is an explicit in-memory registry.
- It accepts typed card instances/lists only.
- It provides deterministic card ordering, duplicate ID handling, family/scope lookup, source hash collection, canonical dict, and canonical hash.
- It does not discover files, query a database, or auto-load arbitrary cards.

### Applicability filtering

- Registry applicability is deterministic and transparent via `PolicyCardApplicability` reason codes.
- Family and scope signals select cards conservatively.
- Insufficient context is skipped with explicit reasons; the resolver remains conservative for no applicable cards.

### Context binding

- `build_policy_resolution_context()` and `context_from_*_like()` helpers convert plain runtime-like metadata into `PolicyResolutionContext`.
- Dict inputs are closed-world.
- List/set-like fields are sorted deterministically.
- Metadata is validated as JSON-safe and non-authoritative.

### Risk mapping seed

- `risk_mapping.py` maps known runtime, approval, policy-card, and identity risk strings into P1.6 `RiskTier` values.
- Unknown present risk values map conservatively to R5 with explicit reason codes.
- Unsupported value types fail closed.

### Resolver integration

- `resolve_policy_cards_from_registry()` and `PolicyRuntimeResolver.resolve_from_registry()` feed registry-selected applicable cards into the existing Custos v0 resolver.
- Resolver output remains SHADOW-only.

## Non-scope (deliberately NOT implemented)

- No runtime policy-card enforcement.
- No `AgenticRuntime.submit()` behavior change.
- No command blocking.
- No approval activation.
- No sandbox runtime bridge.
- No database registry.
- No broad filesystem discovery.
- No full Policy Conflict Algebra.
- No full risk enum unification.
- No Golden Thread B.

## Tests

- `tests/test_policy_registry_binding_p1611.py` — registry construction, duplicate handling, family/scope lookup, applicability filtering, context binding, risk mapping, resolver integration, shadow-only non-enforcement, and public exports.

## Report

Full report: `agent/reports/P1.6.11_POLICY_RESOLUTION_CONTEXT_REGISTRY_BINDING_REPORT.md`
