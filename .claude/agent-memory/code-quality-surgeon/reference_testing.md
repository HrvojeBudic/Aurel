---
name: reference-testing
description: How to run the agentic_runtime test suite, the interpreter to use, and the stale-cache trap that masks failures
metadata:
  type: reference
---

Test suite for `agentic_runtime` (root `/home/hrvojeb/Desktop/GG`):

- No system `python`; use the project venv: `.venv/bin/python` (Python 3.12, pytest 9.1). System `python3` has no pytest.
- Run: `PYTHONPATH="src:." .venv/bin/python -m pytest -q -p no:cacheprovider`
- `pyproject.toml` sets `testpaths=["tests"]`, `pythonpath=["src","."]`. Full suite is ~2400+ tests and takes ~2.5 min.

**Stale-cache trap (important):** pytest's `.pytest_cache` and `tests/**/__pycache__` can mask real failures — a green "2406 passed" run was actually hiding ~43 failures in `tests/contracts/`, `tests/evaluation/`. Always clear caches before trusting a baseline:
`find . -path '*/tests/*' -name __pycache__ -prune -exec rm -rf {} +; rm -rf .pytest_cache`

**Scope note:** `tests/contracts/`, `tests/evaluation/`, `tests/golden_threads/` belong to the in-progress P1.5 evaluation subsystem (modules under `src/agentic_runtime/contracts/`, `evaluation/`, `golden_threads/`) and have test/source drift unrelated to the core runtime. The core runtime tests are the top-level `tests/test_*.py`.

`cli verify` subcommand shells out to a nested `pytest -q` from repo root, so it surfaces the P1.5 collection/assert failures that the scoped run hides. Test `tests/test_public_entrypoints_p121.py::test_cli_verify_exits_zero` depends on the WHOLE tree being green.
