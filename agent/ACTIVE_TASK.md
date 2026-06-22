# Active Task: P1.6.2 — Behavioral Contract Schema (In Progress)

## Objective

Add the first formal Behavioral Contract Schema v1 on top of the existing Policy Card foundation (P1.6.0) and Policy Card Schema (P1.6.1). Create first-class, typed, frozen, validated, deterministic, hash-ready behavioral contract objects. Behavioral contracts define how a subject must behave — obligations, prohibitions, preconditions, postconditions, evidence requirements, and escalation rules. They are not runtime enforcement.

## Status

**In Progress** — 2026-06-22

Code is fully implemented. 96 new tests pass, all existing tests continue to pass with zero regressions.

## Scope

### In scope
- 24 enums: BehavioralContractStatus (5), BehavioralContractSubjectType (11), BehavioralContractScopeType (13), BehavioralContractObligationType (13), BehavioralContractProhibitionType (12), BehavioralContractPreconditionType (11), BehavioralContractPostconditionType (10), BehavioralContractEvidenceType (12), BehavioralContractEscalationTrigger (11), BehavioralContractEscalationAction (6)
- 15 frozen dataclasses: BehavioralContractIdentity, BehavioralContractSubject, BehavioralContractScope, BehavioralContractObligation, BehavioralContractProhibition, BehavioralContractPrecondition, BehavioralContractPostcondition, BehavioralContractEvidenceRequirement, BehavioralContractEscalationRule, BehavioralContractSource, BehavioralContractValidationIssue, BehavioralContractValidationResult, BehavioralContract
- Closed-world `load_behavioral_contract_from_dict()` + `validate_behavioral_contract()`
- Deterministic `behavioral_contract_to_canonical_dict()` + `serialize_behavioral_contract_canonical()`
- SHA-256 `compute_behavioral_contract_hash()`
- Centralized Behavioral Contract Schema v1 (`contract_schema.py`) with field classifications
- Error hierarchy: 6 new error classes in `errors.py`
- ~44 new public exports in `__init__.py`
- 96 comprehensive tests in `tests/test_behavioral_contract_schema_p162.py`

### Not in scope
- No runtime enforcement
- No policy runtime resolver / conflict detector / simulation
- No CLI / report generator
- No specific risk-tier policy cards (P1.6.3)
- No policy card reference resolution
- No P25 hardening
