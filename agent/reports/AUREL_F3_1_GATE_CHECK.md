# AUREL F3.1 — `aurel gate check` Governance Preflight for External Executors

_2026-07-09, branch `feat/f3-external-executors`. Second F3 slice (after F3.0 taint foundation)._

## What shipped

The governance preflight an external executor (a Claude Code session, another agent)
hits before its proposed action ever runs. New package `src/agentic_runtime/gate/`:

- **`gate/gate_check.py`** — `GateChecker` runs a proposed `(tool, args)` through the
  **exact same chain `runtime.submit` runs**, in the same order, over the **same
  evaluator objects**: contract registry → contract input validation → policy
  evaluation. It **never executes, charges budget, touches the sandbox, or appends to
  the trace**. `GateChecker.from_runtime(kernel_or_runtime)` binds to a live runtime's
  own `contracts` / `input_validator` / `policy`, so the gate cannot drift from the
  real decision (fidelity by reuse, not re-implementation).
- **`GateCheckDecision`** — frozen verdict with `phase` (contract_registry /
  contract_input / policy / admitted), `reasons`, re-scored `risk`, contract `code`,
  and — honestly — a distinct **`REQUIRE_APPROVAL`** verdict (policy admits only with
  HITL) that is *not* flattened into DENY. `preflight_only=True` is explicit: ALLOW
  means "no contract/policy objection", **not** final authorization.
- **`cli_modules/gate_commands.py` + `cli.py`** — `aurel gate check --proposal <json>`
  (or `--proposal-file`, `--card`/`--card-file`, `--executor`, `--json`). Exit codes:
  `0` ALLOW, `3` REQUIRE_APPROVAL, `2` DENY, `1` usage/parse error.

The proposed action enters as F3.0 `make_tainted(..., EXTERNAL_EXECUTOR)`: provenance-
external, **instruction-ineligible**, with an advisory injection scan attached. The
gate evaluates the proposal as a *request* — never executes it as an instruction — and
the scan is evidence only, it never changes the verdict.

## Evidence

- Seal `tests/test_p6f3_1_gate_check.py` — **10 passed**: four verdicts land at the
  right phase (unknown→registry, bad args→contract_input, no-authority read→policy DENY,
  trivial in-scope→admitted ALLOW) plus REQUIRE_APPROVAL surfaced honestly; read-only +
  idempotent (sandbox `state_hash` unchanged); proposal is external + instruction-
  ineligible; injection-in-rationale is advisory not gating; `GATE_ARG_KEYS` does not
  drift from `runtime._GOVERNANCE_SUBMIT_ARG_KEYS`.
- CLI smoke: ALLOW (exit 0), DENY unknown-tool (exit 2, `code=unknown_tool`),
  REQUIRE_APPROVAL run_tests (exit 3, honest reasons + external provenance in JSON).
- ruff clean; mypy clean (3 source files); compileall OK.
- Only existing file touched: `cli.py` (+16 lines, additive subparser + import).
  Representative CLI regressions green (`test_dual_kernel_cli`, `test_p6f2_secrets_cli`).

## Boundary (honest)

The gate is a **preflight over contract + policy only**. It deliberately does NOT run
the sandbox posture gate, budget precheck, or approval flow — those remain on the real
`submit` path at execution time. ALLOW is therefore "governance would admit", not
"authorized to run". Sandbox/budget/approval gating for actual external execution lands
in F3.3 (the MCP gateway), where the action runs through full `submit` under a lease.

## Next

**F3.2 — external-executor identity + budget + track record.** An external agent's
`AgentCard` derivation, a hard budget envelope, and a governed track-record ledger
(success/fail history feeding trust — never self-reported). Seal `test_p6f3_2_external_executor.py`.
