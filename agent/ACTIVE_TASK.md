# Active Task: P1.6.10 — Custos v0 Policy Runtime Resolver / Shadow Mode

**Status:** COMPLETE (shadow mode only)

## Roadmap Position

- Last completed: P1.6.9 — Sandbox Policy Card Model
- Current active: P1.6.10 — Custos v0 Policy Runtime Resolver / Shadow Mode
- Next planned: P1.6.11 — Policy Resolution Context & Registry Binding

## Objective

Take the first step from policy-card vocabulary toward policy adjudication. Implement
Custos v0: a deterministic, hash-ready policy runtime resolver that interprets the
P1.6.0–P1.6.9 policy cards into a single shadow-mode judgment — without enforcing
anything and without touching `AgenticRuntime.submit()`.

Core principle: **P1.6.10 interprets policy cards; it does not enforce them.** This
phase creates policy judgment without runtime punishment. "Entity proposes, runtime
disposes" — P1.6.10 does not yet dispose.

## Scope (completed)

- `policy_cards/resolution_context.py` — `EnforcementMode` (SHADOW + reserved ENFORCE/SIMULATE), `PolicyResolutionContext` (closed-world, deterministic canonical serialization + SHA-256 hash, `from_dict`/`to_canonical_dict`).
- `policy_cards/resolution_result.py` — `PolicyFamily`, `FamilyDecision` (ALLOW/WARN/REQUIRE_APPROVAL/DENY/NOT_APPLICABLE/ERROR), `ShadowAction` (WOULD_*), `PolicyFamilyDecision`, `ResolvedPolicySet` (deterministic canonical dict + hash, `would_allow/would_warn/would_require_approval/would_deny` predicates).
- `policy_cards/resolver.py` — seven family adapters (risk tier, human oversight, data residency, tool permission, memory write, prompt, sandbox), strictest-wins MVP aggregation, `resolve_policy_cards()`, `PolicyRuntimeResolver`, `aggregate_family_decisions()`.
- `policy_cards/errors.py` — 5 resolver errors (`PolicyResolutionError`, `PolicyResolutionValidationError`, `PolicyResolutionContextError`, `PolicyResolutionSerializationError`, `PolicyResolutionAdapterError`).
- `policy_cards/__init__.py` — public exports for all resolver types/functions.
- `tests/test_policy_resolver_p1610.py` — 51 tests.

## Non-scope (deliberately NOT implemented)

- No change to `AgenticRuntime.submit()`; no command is blocked, paused, or mutated.
- No active enforcement, no approval gating at runtime, no ENFORCE/SIMULATE behavior (fail-closed rejected).
- No full Policy Conflict Algebra; only strictest-wins MVP.
- No registry / filesystem discovery / database of cards (P1.6.11); loading is explicit.
- No Golden Thread B, no sandbox runtime behavior change, no Docker/Bubblewrap requirement, no runtime dependencies.
- No Model Routing / Business Process policy cards.

## Strictest-wins MVP

`DENY > REQUIRE_APPROVAL (= ERROR, conservative) > WARN > ALLOW > NOT_APPLICABLE`.
No applicable cards → conservative `WARN` (never silent ALLOW). Shadow map:
DENY→WOULD_DENY, REQUIRE_APPROVAL→WOULD_REQUIRE_APPROVAL, WARN→WOULD_WARN,
ALLOW→WOULD_ALLOW, NOT_APPLICABLE→WOULD_NOT_APPLY, ERROR→WOULD_ERROR (family) and
conservative REQUIRE_APPROVAL at the aggregate.

## Acceptance criteria — met

Context + result types exist; resolver accepts explicit cards; determines applicable
cards; emits per-family decisions; SHADOW only; WOULD_* semantics; strictest-wins;
conservative no-card behavior; reason codes + applicable card IDs + source hashes in
result; deterministic context/result serialization and hashes; no `submit()` change;
no enforcement.

## Validation

```bash
.venv/bin/python -m compileall src tests                                   # PASS
.venv/bin/python -m pytest tests/test_policy_resolver_p1610.py -q          # PASS, 51 passed
# all policy-card families + resolver
.venv/bin/python -m pytest tests/test_policy_resolver_p1610.py tests/test_sandbox_policy_cards_p169.py tests/test_prompt_policy_cards_p168.py tests/test_memory_write_policy_cards_p167.py tests/test_tool_permission_policy_cards_p166.py tests/test_data_residency_policy_cards_p165.py tests/test_human_oversight_policy_cards_p164.py tests/test_risk_tier_policy_cards_p163.py -q   # PASS, 449 passed
.venv/bin/ruff check src tests                                             # PASS (new files)
```

## Next

- P1.6.11 — Policy Resolution Context & Registry Binding
