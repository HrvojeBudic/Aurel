# Repository State

_Last updated: 2026-06-17_

## What works

- Full governed command pipeline: policy → HITL → budget → sandbox → verify → trace → memory
- Plan validation halts on empty/invalid/unsupported plans
- Persistent and in-memory trace ledgers with hash-chain verification
- Runtime state machine with structured `ExecutionOutcome`
- Budget enforcement with traced decisions
- Memory write governance with provenance and promotion gates
- Tool input/output contract enforcement (P0.10)
- End-to-end demo: fix calc bug, authority denial, HITL denial, test integrity, skill maturation
- Minimal CLI: `python -m agentic_runtime.cli {status,demo,verify}`
- P0.12 model provider layer:
  - deterministic mock provider by default
  - optional OpenAI / Anthropic / Ollama adapters
  - structured plan schema validation before `PlanValidator`
- P0.13 Tool Bus v1:
  - structured tool registry/spec/metadata/result/error concepts
  - builtin read/search/git-read/write/patch/execution tools
  - contract-bound input validation before handler execution
  - structured tool errors instead of uncaught exceptions
- P0.14 Repository Agent Loop:
  - bounded repository context builder
  - deterministic plan-first coding loop
  - patch/test execution through `AgenticRuntime.submit()` and Tool Bus tools
  - structured `CodeTaskReport` with bounded repair attempts
- P0.15 HITL / Approval Upgrade:
  - structured approval requests, decisions, receipts
  - risk classes R0–R5 with preview/confirmation rules
  - runtime trace receipts for approval outcomes
  - repo-agent dry-run approval summaries and CLI approval modes
- P0.16 Praxis Memory Seed:
  - `PraxisExperience` capture from runtime/repo/approval/test/verifier sources
  - governed memory/procedure/skill **candidates** (not verified truth)
  - conservative promotion gates and reflex eligibility checks
  - repo-agent `PraxisReport` and trace `PraxisEventRecord` events
  - CLI: `praxis-demo`, `memory-candidates`, `praxis-report`
- P0.17 Sandbox Hardening:
  - sandbox profiles (`no_exec_readonly`, `restricted_local`, `unsafe_local_demo`, docker, bubblewrap)
  - `SandboxPolicy` + `ProfiledSandbox` path/exec enforcement
  - structured `SandboxViolation` + trace records
  - runtime status diagnostics and repo-agent profile selection
  - CLI: `sandbox-status`, repo-task `--sandbox`
- P0.17.1 Pre-P0.20 Readiness Patch:
  - missing-file safety in repo context builder
  - `TestRunnerAdapter` uses `run_tests` for list commands
  - `AutoApprover` predicate cannot widen risk envelope
  - explicit repo auto-approval R0–R3 only
- P0.19 P0.20 Demo Harness:
  - `DemoScenario` / `DemoRepoFactory` / `DemoHarness` contracts
  - `buggy_calculator` controlled scenario (initial fail → patch → test)
  - plan-first verification, approval/sandbox/praxis/trace summaries
  - honest failure when initial tests pass unexpectedly or final tests fail
  - CLI: `demo-harness buggy_calculator`
- P0.20 First Real Coding Agent Demo (**PASS**):
  - governed loop proven end-to-end: objective → context → plan → approval preview
    → governed patch → tests → trace → sandbox summary → praxis report → evidence
  - `write_evidence` / `build_sandbox_summary` evidence adapters
  - CLI: `demo-harness ... --evidence-dir`
  - evidence artifacts under `agent/evidence/p0.20/`
  - seal tests `tests/test_p020_demo_seal.py`
- P0.21 LLM Planning Bridge for Repository Agent (**PASS**):
  - planner modes: `deterministic`, `llm`, `hybrid`, `dry_run`
  - `LLMRepoPlanner` calls ModelRouter/provider structured output for plans only
  - strict repository plan schema + `RepoPlanValidator` fail closed
  - hybrid fallback records fallback reason without bypassing governance
  - new `missing_validation` demo scenario and mock LLM planner coverage
  - CLI: `repo-task --planner ... --provider ...`, `demo-harness ... --planner ... --provider ...`
- P1.0 Runtime Alpha Seal (**PRE-SEAL** — P1.0.1 integrity patch 2026-06-17):
  - GitHub Actions CI configured: compileall, ruff, mypy, pytest+coverage (≥75%), alpha-seal
  - `python -m agentic_runtime.cli alpha-seal` readiness checks (local PASS on Python 3.12.3)
  - `--apply` auto-selects hard sandbox: bubblewrap → docker → restricted_local
  - timeout subprocess tests skip in restricted CI sandboxes (`requires_subprocess`)
  - deployment guide: `docs/DEPLOYMENT.md`
  - dev tooling: pytest-cov, ruff, mypy
  - release docs: `agent/releases/P1.0_*.md`
  - P1.0 evidence: `agent/evidence/p1.0/`
  - seal report: `agent/reports/P1.0_RUNTIME_ALPHA_SEAL_REPORT.md`
  - **PASS** pending: baseline commit + CI green on Python 3.11/3.12

## Known limitations

- Default sandbox is `UnsafeLocalSandbox` — **not** a production security boundary
- Real providers are optional and unverified without API keys/local services
- Single-entity demo; no multi-agent orchestration
- HITL uses `AutoApprover` in demo (bounded predicate, defaults deny)
- Tool Bus does not make authority decisions; Runtime policy remains mandatory
- No network, delete, git commit, or git push tools are implemented
- Repository agent patch synthesis remains intentionally small/deterministic; LLM planning proposes structured plans only and is not a general autonomous coding agent
- Repository-agent context building reads bounded local files directly, while
  mutations and test execution go through Runtime/Tool Bus governance
- One pytest (`test_timeout_kills_long_running_command`) may fail in restricted CI sandboxes when nested `python3` subprocesses are blocked; passes in normal environments — **P1.0:** both timeout tests skip automatically via `requires_subprocess` when subprocess spawn is blocked
- CLI `demo-harness --apply` with auto bubblewrap may report harness `failed` while independent `final_test` passes; use `--sandbox restricted_local` for scenario-default smoke or see P1.0 seal report

## How to run

```bash
# from repo root, with dev deps installed
pip install -e ".[dev]"

python -m agentic_runtime.cli status
python -m agentic_runtime.cli demo
python -m agentic_runtime.cli verify
python -m agentic_runtime.cli repo-task "replace 'old' with 'new' in src/file.py"
python -m agentic_runtime.cli repo-task "replace 'old' with 'new' in src/file.py" --apply
python -m agentic_runtime.cli approve-demo --mode deny
python -m agentic_runtime.cli repo-task "objective" --dry-run --approval-mode deny
python -m agentic_runtime.cli praxis-demo
python -m agentic_runtime.cli memory-candidates
python -m agentic_runtime.cli praxis-report
python -m agentic_runtime.cli sandbox-status
python -m agentic_runtime.cli sandbox-status --profile restricted_local --json
python -m agentic_runtime.cli repo-task "objective" --sandbox restricted_local
python -m agentic_runtime.cli repo-task "objective" --dry-run --sandbox no_exec_readonly
python -m agentic_runtime.cli demo-harness buggy_calculator
python -m agentic_runtime.cli demo-harness buggy_calculator --apply
python -m agentic_runtime.cli demo-harness buggy_calculator --apply --evidence-dir agent/evidence/p0.20
python -m agentic_runtime.cli demo-harness missing_validation --planner hybrid --provider mock --apply
python -m agentic_runtime.cli demo-harness list
python -m agentic_runtime.cli alpha-seal
```

See `agent/releases/P1.0_ALPHA_MANIFEST.md` for seal status and required verification.

Provider selection:

```bash
AUREL_MODEL_PROVIDER=mock python -m agentic_runtime.cli demo
AUREL_MODEL_PROVIDER=openai OPENAI_API_KEY=... python -m agentic_runtime.cli demo
AUREL_MODEL_PROVIDER=anthropic ANTHROPIC_API_KEY=... python -m agentic_runtime.cli demo
AUREL_MODEL_PROVIDER=ollama AUREL_OLLAMA_MODEL=llama3.1 python -m agentic_runtime.cli demo
```

See `TESTS.md` for canonical compile and pytest commands.

## Package layout

```
src/agentic_runtime/   # runtime kernel
tests/                 # pytest suite
examples/demo.py       # thin wrapper around agentic_runtime.demo
agent/                 # agent operating docs (this folder)
```
