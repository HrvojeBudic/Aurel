# Tests & Verification

## Canonical commands

From repository root:

```bash
# Compile check
python3 -m compileall src tests

# Test suite (preferred)
PYTHONPATH=src:. pytest -q

# Equivalent when pyproject pythonpath is active (editable install or pytest from root)
pytest -q

# Via CLI wrapper
python -m agentic_runtime.cli verify
```

## Demo smoke test

```bash
PYTHONPATH=src python -m agentic_runtime.cli demo
# or
python -m agentic_runtime.demo
```

## Status smoke test

```bash
PYTHONPATH=src python -m agentic_runtime.cli status
python -m agentic_runtime.cli status --json
```

## Environment notes

### `test_timeout_kills_long_running_command` / `test_run_shell_timeout_is_enforced`

Both tests spawn nested subprocesses. In **restricted CI sandboxes**
that block subprocess execution, they are **skipped** automatically via
`requires_subprocess` in `tests/conftest.py`.

Run outside the restricted sandbox to confirm timeout behavior:
```bash
pytest tests/test_sandbox_p03.py::test_timeout_kills_long_running_command -q
pytest tests/test_tool_bus_p13.py::test_run_shell_timeout_is_enforced -q
```

## Verifying P1.0

```bash
pip install -e ".[dev]"
python3 -m compileall src tests
ruff check src tests
mypy src/agentic_runtime
pytest -q --cov=agentic_runtime --cov-fail-under=75
python -m agentic_runtime.cli alpha-seal
```

Expected: alpha-seal exits 0; full suite 300 passed, 4 skipped (when subprocess blocked).

## Verifying P1.0.1 (seal integrity)

```bash
pip install -e ".[dev]"
python3 -m compileall src tests
ruff check src tests
mypy src/agentic_runtime
pytest -q --cov=agentic_runtime --cov-fail-under=75
python -m agentic_runtime.cli alpha-seal
python -m agentic_runtime.cli demo-harness buggy_calculator --apply --sandbox restricted_local
```

Release artifacts:

- `agent/releases/P1.0_*.md`
- `agent/evidence/p1.0/*.json`
- `agent/reports/P1.0_RUNTIME_ALPHA_SEAL_REPORT.md`

Status: **PRE-SEAL** until CI green on baseline commit (Python 3.11 + 3.12).

## Verifying P0.11

1. `python3 -m compileall src tests` — exit 0
2. `pytest -q` — 121+ passed (1 env flake possible)
3. `python -m agentic_runtime.cli status` — shows `unsafe_local` sandbox mode
4. `python -m agentic_runtime.cli demo` — section 5 shows `require_approval` + HITL DENIED
5. `/agent` docs present

## Verifying P0.12

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest -q
PYTHONPATH=src:. pytest tests/test_model_providers_p12.py -q
```

Expected offline provider result:

```text
9 passed, 2 skipped
```

The skipped tests are integration placeholders:

- OpenAI integration requires `OPENAI_API_KEY`
- Ollama integration requires `AUREL_RUN_OLLAMA_TESTS=1`

Normal test runs do not require API keys or network access.

## Verifying P0.13

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_tool_bus_p13.py -q
PYTHONPATH=src:. pytest tests/test_tool_contract_p10.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused Tool Bus result:

```text
18 passed
```

The Tool Bus tests cover registry behavior, contract-bound validation,
filesystem boundary failures, patching, execution tool structured outputs, and
runtime integration.

## Verifying P0.14

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_repo_agent_p14.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused Repository Agent Loop result:

```text
20 passed
```

The P0.14 tests cover bounded context construction, allowed-path handling,
large-file truncation, deterministic planning, Runtime/Tool Bus patch execution,
structured test execution, bounded repair attempts, and a tiny end-to-end
repository task fixture.

CLI smoke example:

```bash
python -m agentic_runtime.cli repo-task "replace 'old' with 'new' in src/file.py"
python -m agentic_runtime.cli repo-task "replace 'old' with 'new' in src/file.py" --apply
```

## Verifying P0.15

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_hitl_p15.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused HITL result:

```text
16 passed
```

CLI smoke examples:

```bash
python -m agentic_runtime.cli approve-demo --mode deny
python -m agentic_runtime.cli repo-task "replace 'x' with 'y' in src/a.py" --dry-run
```

## Verifying P0.16

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_praxis_p16.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused Praxis result:

```text
24 passed
```

CLI smoke examples:

```bash
python -m agentic_runtime.cli praxis-demo
python -m agentic_runtime.cli memory-candidates
python -m agentic_runtime.cli praxis-report
```

## Verifying P0.17

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_sandbox_p17.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused Sandbox Hardening result:

```text
25 passed
```

CLI smoke examples:

```bash
python -m agentic_runtime.cli sandbox-status
python -m agentic_runtime.cli sandbox-status --profile restricted_local --json
python -m agentic_runtime.cli repo-task "replace 'x' with 'y' in src/a.py" --dry-run --sandbox no_exec_readonly
```

## Verifying P0.17.1

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_p0171_readiness.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused readiness result:

```text
10 passed
```

## Verifying P0.19

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_demo_harness_p19.py -q
PYTHONPATH=src:. pytest -q
```

Harness smoke:

```bash
PYTHONPATH=src python -m agentic_runtime.cli demo-harness list
PYTHONPATH=src python -m agentic_runtime.cli demo-harness buggy_calculator
PYTHONPATH=src python -m agentic_runtime.cli demo-harness buggy_calculator --apply
```

Expected focused harness result:

```text
17 passed
```

## Verifying P0.20

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_p020_demo_seal.py -q
PYTHONPATH=src:. pytest -q
```

Run the demo and regenerate evidence through the public path:

```bash
PYTHONPATH=src python -m agentic_runtime.cli demo-harness buggy_calculator \
    --apply --repo-parent /tmp/p020_demo --evidence-dir agent/evidence/p0.20
```

Expected focused seal result:

```text
12 passed
```

Evidence artifacts are written under `agent/evidence/p0.20/` (8 files).

## Verifying P0.21

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_repo_planner_p021.py -q
PYTHONPATH=src:. pytest tests/test_repo_agent_p14.py -q
PYTHONPATH=src:. pytest tests/test_demo_harness_p19.py -q
PYTHONPATH=src:. pytest tests/test_p020_demo_seal.py -q
PYTHONPATH=src:. pytest -q
```

CLI smoke examples:

```bash
PYTHONPATH=src python -m agentic_runtime.cli demo-harness buggy_calculator --apply
PYTHONPATH=src python -m agentic_runtime.cli demo-harness missing_validation --planner hybrid --provider mock --apply
PYTHONPATH=src python -m agentic_runtime.cli repo-task "objective" --planner llm --provider mock
```

Expected focused P0.21 result: `18 passed`. Offline tests use `MockProvider`; API keys are not required.
