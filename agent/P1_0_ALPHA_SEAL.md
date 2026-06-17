# P1.0 — Runtime Alpha Seal

Alpha seal criteria formalize readiness for external users and CI promotion.

## Criteria

| ID | Check | Requirement |
|----|-------|-------------|
| A1 | Documentation | `README.md`, `agent/ARCHITECTURE.md`, `agent/STATE.md`, `agent/ROADMAP.md`, `agent/TESTS.md`, `docs/DEPLOYMENT.md` present |
| A2 | CI workflow | `.github/workflows/ci.yml` runs compile, ruff, mypy, pytest+coverage, alpha-seal |
| A3 | Compile | `python -m compileall src tests` exits 0 |
| A4 | Tests | `pytest -q` all pass (timeout tests skip in restricted subprocess environments) |
| A5 | Coverage | `agentic_runtime` ≥ 75% line coverage |
| A6 | Apply sandbox | `resolve_apply_sandbox_profile()` prefers bubblewrap → docker → restricted_local |
| A7 | Lint / types | `ruff check` and `mypy src/agentic_runtime` pass in CI |
| A8 | Zero runtime deps | `pyproject.toml` `dependencies = []` |

## Verification

```bash
pip install -e ".[dev]"
python -m agentic_runtime.cli alpha-seal
```

Fast check (docs + compile only):

```bash
python -m agentic_runtime.cli alpha-seal --skip-tests
```

JSON output:

```bash
python -m agentic_runtime.cli alpha-seal --json
```

## Exit codes

- `0` — all seal checks passed
- `1` — one or more checks failed

## Phase status

**P1.0 — PRE-SEAL** (2026-06-17): local `alpha-seal` succeeds on Python 3.12.3; release artifacts added in P1.0.1.

**P1.0 — PASS** when:

1. `alpha-seal` succeeds on a clean checkout with dev dependencies installed
2. GitHub Actions CI passes on Python 3.11 and 3.12
3. `agent/releases/`, `agent/evidence/p1.0/`, and seal report are present and consistent

See `agent/reports/P1.0_RUNTIME_ALPHA_SEAL_REPORT.md`.

## Out of scope for P1.0

- PyPI publish
- Multi-agent orchestration
- Network tools with governance
- OpenTelemetry observability

These remain on the roadmap after alpha.
