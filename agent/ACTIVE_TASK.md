# Active Task: P1.6.8S — Repository Reality & Policy Card Stabilization Seal

**Status:** COMPLETE

## Roadmap Position

- Last completed: P1.6.8 — Prompt Policy Card Model
- Current stabilization: P1.6.8S — Repository Reality & Policy Card Stabilization Seal
- Next planned: P1.6.9 — Sandbox Policy Card Model
- Last verified against commit: 3f65647f356eccac8b057592f894c9294bd01f5c

## Objective

Seal repository reality after P1.6.8 and before P1.6.9. This patch aligns git state, policy-card implementation truth, CLI subprocess tests, linting, validation results, and agent documentation. It does not add Sandbox Policy Card behavior.

## Scope Completed

- Classified tracked, modified, and untracked repository state.
- Preserved legitimate P1.6.4-P1.6.8 source, test, and report artifacts for final staging.
- Removed the accidental root-level pager/help artifact named `ive identity, evaluation, contracts, and policy card infrastructure`.
- Verified P1.6.8 Prompt Policy Card implementation, schema, errors, exports, closed-world validation, canonical serialization, deterministic hash readiness, and tests.
- Added shared CLI subprocess helper `tests/cli_helpers.py`.
- Refactored autonomy and measured-autonomy CLI tests off bare `python3 -m agentic_runtime.cli`.
- Fixed all ruff findings in `src` and `tests`.
- Reconciled docs to show P1.6.8 complete, P1.6.8S as the stabilization seal, and P1.6.9 next.
- Added optional dev security tooling seeds (`bandit`, `pip-audit`) without making them hard gates.

## Validation

```bash
.venv/bin/python -m compileall src tests                                             # PASS
.venv/bin/python -m pytest tests/test_prompt_policy_cards_p168.py -q --tb=line       # PASS, 74 passed
.venv/bin/python -m pytest tests/test_policy_cards_p160.py tests/test_policy_cards_schema_p161.py tests/test_behavioral_contract_schema_p162.py tests/test_risk_tier_policy_cards_p163.py tests/test_human_oversight_policy_cards_p164.py tests/test_data_residency_policy_cards_p165.py tests/test_tool_permission_policy_cards_p166.py tests/test_memory_write_policy_cards_p167.py tests/test_prompt_policy_cards_p168.py -q --tb=line  # PASS, 540 passed
.venv/bin/python -m pytest tests/test_autonomy_scale_engine.py tests/test_measured_autonomy_score.py -q --tb=line  # PASS, 85 passed
.venv/bin/ruff check src tests                                                       # PASS
.venv/bin/mypy src/agentic_runtime                                                   # PASS
.venv/bin/python -m pytest -q --tb=line                                               # PASS, 3220 passed, 2 skipped
.venv/bin/python -m pytest --cov=src/agentic_runtime --cov-report=term-missing -q --tb=no  # PASS, 79.27% coverage, 3220 passed, 2 skipped
```

## Deferred Structural Debt

- `src/agentic_runtime/cli_modules/identity_commands.py` is large (3380 lines); split later during P1/P25 hardening.
- Typed policy card modules repeat serialization/validation/hash patterns; consider a shared typed policy-card base after P1.6.10 or during P25 governance hardening.
- `mypy` still disables several important error codes; tighten during P25/P29 hardening.
- Security scanning is optional only; promote `bandit` / `pip-audit` to hard gates in P28/P29 if the workflow is ready.
- Slow test marker discipline remains future P25/P30 test hardening work.

## Next

- P1.6.9 — Sandbox Policy Card Model
