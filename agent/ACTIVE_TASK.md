# Active Task: P1.6.13 — Policy Conflict Algebra & Strictest-Wins Rules

**Status:** ACTIVE

## Roadmap Position

- Last completed: P1.6.12 — Custos Shadow Runtime Projection & Submit Observability Hook
- Current active: **P1.6.13 — Policy Conflict Algebra & Strictest-Wins Rules**
- Next planned: P1.6.14 — Policy Enforcement Adapter Hardening

P1.6.13 introduces deterministic conflict algebra within the Custos shadow policy decision system. It normalizes policy family decisions into formal ranks, classifies conflicts between them, and determines the "strictest valid outcome" according to defined rules. All conflict evidence is preserved and explained deterministically. No enforcement or runtime behavior changes are introduced.

## Objective

When the Custos resolver produces multiple family decisions, P1.6.13 formalizes:

- **Normalization**: maps every `FamilyDecision`/`ShadowAction` to a `PolicyDecisionRank` (ERROR > DENY > REQUIRE_APPROVAL > WARN > ALLOW > NOT_APPLICABLE)
- **Conflict classification**: detects and taxonomizes rank, family, risk, approval, sandbox, data, tool, prompt, memory, adapter error, and context conflicts via 14 `PolicyConflictType` values
- **Strictest-wins resolution**: determines the winning outcome via deterministic rules (strictness → specificity → family_order → lexical), preserving all evidence
- **Deterministic canonical hashing**: SHA-256 over canonical conflict resolution dict

The integration attaches `conflict_resolution` and `conflict_hash` metadata to `ResolvedPolicySet` as optional backwards-compatible fields. The resolver calls into `conflict_algebra` after `aggregate_family_decisions()` produces the initial family decisions.

## Scope

- `conflict_algebra.py` (new): 6 enums, 6 frozen dataclasses, normalization helpers, strictest-wins resolution, conflict classification, specificity scoring, canonical hashing (~560 lines)
- `resolution_result.py`: optional `conflict_resolution`/`conflict_hash` fields on `ResolvedPolicySet` (default `None` — backwards compatible)
- `resolver.py`: calls `resolve_policy_conflicts_strictest_wins()` after `aggregate_family_decisions()`, attaches metadata via `_attach_conflict_metadata()`
- `__init__.py`: ~14 new public exports

## Non-scope

- No Custos runtime enforcement
- No command blocking from policy cards
- No approval activation from policy cards
- No sandbox behavior changes
- No runtime authorization modifications
- No enforcement imports in conflict_algebra.py

## Tests

- `tests/test_policy_conflict_algebra_p1613.py` — 73 pure-module tests
- `tests/test_policy_resolver_conflict_algebra_p1613.py` — resolver integration tests

## Report

Full report: `agent/reports/P1.6.13_POLICY_CONFLICT_ALGEBRA_STRICTEST_WINS_REPORT.md`
