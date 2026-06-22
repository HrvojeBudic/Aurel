# Active Task: P1.6.3 - Risk Tier Policy Card Model (Complete)

## Objective

Add the first specific typed policy card model: `RiskTierPolicyCard`. It defines Aurel risk-tier semantics for R0-R6, reversibility levels, oversight expectations, evidence expectations, and seed action-class mappings. It is declarative, closed-world, deterministic, and hash-ready.

## Status

**Complete** - 2026-06-22

P1.6.3 is implemented with 36 focused tests. P1.6.0-P1.6.3 focused tests pass together.

## Scope

### In scope

- `RiskTier` enum with R0-R6.
- `ReversibilityLevel`, `OversightLevel`, and `EvidenceExpectation` vocabularies.
- `RiskTierDefinition`, `RiskActionClass`, `RiskActionClassMapping`, and `RiskTierPolicyCard`.
- Risk Tier Policy Card Schema v1 (`risk_tier_schema.py`) with required, optional, forbidden, and canonical fields; dangerous metadata keys; default tier definitions; and default action-class mapping seeds.
- Closed-world `load_risk_tier_policy_card_from_dict()` and `validate_risk_tier_policy_card_dict()`.
- Structured `validate_risk_tier_policy_card()`.
- Deterministic `risk_tier_policy_card_to_canonical_dict()` and `serialize_risk_tier_policy_card_canonical()`.
- SHA-256 `compute_risk_tier_policy_card_hash()`.
- Safe `create_default_risk_tier_policy_card()`.
- Strict R5 and R6 safety validation.
- Public exports from `agentic_runtime.policy_cards`.

### Non-scope

- No policy runtime resolver.
- No automatic risk classifier.
- No runtime risk inference.
- No enforcement engine.
- No human oversight cards.
- No tool permission, sandbox, model routing, memory write, or execution enforcement.
- No policy conflict detector.
- No policy simulation mode.
- No policy violation trace hook.
- No CLI or report generator.
- No P25 hardening.

## Acceptance Criteria

- Default risk tier policy card validates successfully.
- R0, R1, R2, R3, R4, R5, and R6 are all required.
- Missing, duplicate, or unknown tiers fail validation.
- R5 requires trace, evidence, approval, explicit Operator confirmation, irreversible reversibility, and explicit Operator oversight.
- R6 is denied and non-permissive: no execution, external egress, memory write, or tool write.
- Reversible and compensatable remain distinct.
- Dangerous metadata keys fail validation; safe metadata is accepted.
- Unknown top-level and nested risk-tier fields fail closed.
- Generic `PolicyCard(kind="risk_tier")` compatibility is enforced.
- Canonical serialization and hash are deterministic.
- P1.6.0-P1.6.2 tests remain passing with the new P1.6.3 tests.

## Validation Commands

```bash
python3 -m compileall src tests
PYTHONPATH=src:. ./.venv/bin/pytest tests/test_policy_cards_p160.py tests/test_policy_cards_schema_p161.py tests/test_behavioral_contract_schema_p162.py tests/test_risk_tier_policy_cards_p163.py -q
PYTHONPATH=src:. ./.venv/bin/pytest -q
./.venv/bin/ruff check .
./.venv/bin/mypy .
PYTHONPATH=src:. python3 -m agentic_runtime status
```

## Next

P1.6.4 - Human Oversight Policy Card Model.
