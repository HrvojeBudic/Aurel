# Decisions Log

## 2026-06-17 — P1.0.1 Alpha Seal Integrity Patch

### PRE-SEAL until CI green on baseline commit
**Decision:** Release status is **PRE-SEAL**, not PASS, despite clean local verification on Python 3.12.3.
**Why:** No git baseline commit; GitHub Actions not executed; Python 3.11 not verified locally. Public PASS requires CI matrix green.

### Release artifacts required before PASS claim
**Decision:** Add `agent/releases/`, `agent/evidence/p1.0/`, and `agent/reports/P1.0_RUNTIME_ALPHA_SEAL_REPORT.md`.
**Why:** STATE/ROADMAP previously claimed PASS without manifests, evidence, or seal report.

### No runtime changes in P1.0.1
**Decision:** Documentation and evidence only; no new features, tests weakened, or seal criteria relaxed.
**Why:** Task scope is seal hygiene, not capability expansion.

### Document bubblewrap apply harness divergence
**Decision:** Record CLI `demo-harness --apply` (auto bwrap) harness failure when agent `final_status` ≠ `succeeded` despite independent `final_test` pass.
**Why:** Honest operator signal; pytest harness uses `restricted_local` by default and passes.

## 2026-06-17 — P1.0 Runtime Alpha Seal

### Timeout tests skip via sandbox probe, not bare subprocess
**Decision:** `requires_subprocess` in `conftest.py` probes `UnsafeLocalSandbox.run_shell` with a short sleep+timeout; skip when permission denied or timeout not enforced.
**Why:** Direct `subprocess.run` can succeed while nested sandbox execution fails in restricted CI environments.

### `--apply` auto-selects hard sandbox in CLI
**Decision:** `resolve_apply_sandbox_profile()` prefers bubblewrap → docker → restricted_local; CLI `--sandbox` defaults to `None` (auto) for apply paths.
**Why:** Production-shaped apply workflows should not silently use soft isolation when hard backends exist.

### Mypy/ruff scoped for alpha
**Decision:** Ruff ignores pre-existing F401/F541/F811/E402 project-wide; mypy disables selected error codes via `pyproject.toml`.
**Why:** P1.0 adds CI gates without forcing a full-repo lint migration; coverage threshold 75%.


### Demo HITL section uses MEDIUM card ceiling
**Decision:** In demo section 5, set `card2.authority.max_risk = RiskLevel.MEDIUM` so `run_shell` (HIGH) triggers `require_approval`, then `AutoApprover` denies it.
**Why:** Previous demo labeled "auto-denied" while policy returned `allow` and the sandbox actually executed `rm`. Output must match behavior.

### Status via dedicated module, not Kernel method
**Decision:** Add `status.py` with `runtime_status()` and `format_status()` rather than bloating `Kernel`.
**Why:** Minimal surface; CLI and tests can import without constructing entities.

### CLI scope: status / demo / verify only
**Decision:** No full command center. `verify` wraps `pytest -q` with `PYTHONPATH=src:.`.
**Why:** Task explicitly limits CLI scope; documents one canonical test path.

### pytest pythonpath includes repo root
**Decision:** Set `pythonpath = ["src", "."]` in `pyproject.toml`.
**Why:** Matches documented `PYTHONPATH=src:. pytest -q` without manual env in most cases.

### HITL denial messages clarified
**Decision:** HITL block path now includes tool name, risk level, and `HITL_DENIED` code.
**Why:** Failure paths should state why execution stopped without redesigning error handling.

### No test changes for sandbox timeout flake
**Decision:** Document env-dependent failure in `TESTS.md`; do not modify `test_sandbox_p03.py`.
**Why:** Test is correct; failure is CI sandbox restriction on nested subprocesses.

## 2026-06-17 — P0.12 Real LLM Adapter Layer

### Provider layer preserves `ModelRouter.complete()`
**Decision:** Add provider adapters behind the existing `complete(profile, system, user)` seam instead of rewriting entity planning.
**Why:** Keeps `AgenticEntity.plan()` and `PlanValidator` as the execution gate; providers only generate text/JSON plans.

### Stdlib HTTP clients only
**Decision:** Implement OpenAI, Anthropic, and Ollama adapters with `urllib`.
**Why:** Preserves zero runtime dependencies and keeps real providers optional.

### Legacy scripted plans remain supported
**Decision:** `MockModelClient` returns scripted responses unchanged.
**Why:** Existing tests intentionally exercise invalid/legacy plan shapes through `PlanValidator`.

### Provider-shaped outputs require schema validation
**Decision:** Structured provider responses are validated against `STRUCTURED_PLAN_SCHEMA`; schema failures become refusal plans and then halted planning.
**Why:** No provider output should become commands without schema validation plus `PlanValidator`.

## 2026-06-17 — P0.13 Tool Bus v1

### Tool Bus wraps the existing runtime dispatch seam
**Decision:** Implement `ToolBus`/`ToolRegistry` in `tools.py` and keep `ToolRuntime.dispatch(CommandEnvelope)` for runtime compatibility.
**Why:** Avoids a broad runtime rewrite while creating a stable controlled execution surface.

### Tool Bus validates only when contracts are bound
**Decision:** `ToolBus.execute()` validates through `ToolContractRegistry` when bound; `AgenticRuntime` still performs the authoritative pre-policy contract gate.
**Why:** Direct bus usage is safer, but Runtime remains the execution authority.

### No destructive delete/network/git-write tools
**Decision:** P0.13 adds read-only git status/diff and no network/delete/commit/push tools.
**Why:** The task explicitly excludes network and destructive repository operations.

### `patch_file` uses a conservative unified-diff subset
**Decision:** Implement a small single-file patch applier that rejects mismatched/invalid hunks cleanly.
**Why:** Keeps dependencies at zero and fails closed for ambiguous patches.

## 2026-06-17 — P0.14 Repository Agent Loop

### Repository loop lives outside `Entity`
**Decision:** Add `repo_agent.py` instead of rewriting `AgenticEntity`.
**Why:** P0.14 is an application-level coding loop; `Entity` still owns the canonical plan-to-command runtime path.

### Mutations and tests go through Runtime
**Decision:** `PatchExecutor` and `TestRunnerAdapter` call `AgenticRuntime.submit()` instead of invoking tool handlers directly.
**Why:** Policy, HITL, budget, sandbox, verifier, trace, and memory governance must remain the execution authority.

### Context reads are bounded local reads
**Decision:** `RepoContextBuilder` reads small, non-secret local files directly with size/path limits.
**Why:** Context building is pre-plan inspection; write and execution side effects are the governed boundary for this phase.

## 2026-06-17 — P0.15 HITL / Approval Upgrade

### Separate approval module
**Decision:** Add `approval.py` for contracts/policy/previews; keep approver implementations in `hitl.py`.
**Why:** Keeps runtime integration small while making the approval surface reusable by CLI and repo agent.

### Risk classes layered on existing RiskLevel
**Decision:** Introduce `ApprovalRiskClass` R0–R5 without renaming `RiskLevel`.
**Why:** Preserves policy compatibility while enabling finer approval behavior.

### All non-denied commands pass through resolver
**Decision:** `AgenticRuntime.submit()` resolves approval requirements even when policy returns `allow`.
**Why:** R2+ writes and executions need preview/approval even inside card risk ceilings.

### Auto-approved actions still traced
**Decision:** R0/R1 auto approvals append `ApprovalReceiptRecord` entries.
**Why:** Operator audit requires visibility into skipped manual steps, not silent execution.

## 2026-06-17 — P0.16 Praxis Memory Seed

### Separate Praxis module, not a learning system
**Decision:** Add `praxis.py` as a metabolism seed with in-memory candidate stores.
**Why:** Captures experience and produces governed candidates without vector DB, RAG, or auto-promotion.

### Praxis SkillCandidate aliased on export
**Decision:** Praxis `SkillCandidate` exports as `PraxisSkillCandidate`; `core_types.SkillCandidate` unchanged.
**Why:** Avoids collision with existing `skills.py` lifecycle types.

### Repo agent uses Praxis instead of ad-hoc memory JSON
**Decision:** `CodeTaskReport.praxis_report` replaces `_write_candidate_memory`.
**Why:** Centralizes evidence linking, promotion gates, and trace events.

### Reflex bridge is proposal-only
**Decision:** `bridge_skill_candidate_to_library()` returns a dict; no auto-registration.
**Why:** Reflexes must never bypass runtime governance.

## 2026-06-17 — P0.17 Sandbox Hardening

### Separate sandbox_policy module
**Decision:** Add `sandbox_policy.py` for profiles/policy; keep backends in `sandbox.py`.
**Why:** Separates capability contracts from backend implementations without rewriting backends.

### ProfiledSandbox wrapper
**Decision:** Enforce path/exec policy via `ProfiledSandbox` wrapper + runtime/tool-bus pre-checks.
**Why:** Defense in depth — violations are structured before handlers run.

### Honest Docker/Bubblewrap availability
**Decision:** Profiles raise `SandboxUnavailableError` when backends missing; no silent downgrade.
**Why:** Must not claim container isolation when only unsafe local is active.

### Repo agent defaults to restricted_local
**Decision:** Apply uses `restricted_local`; dry-run uses `no_exec_readonly`.
**Why:** Writes/exec require explicit profile capability; planning is read-only.

## 2026-06-17 — P0.17.1 Pre-P0.20 Readiness Patch

### AutoApprover predicate narrows only
**Decision:** `allowed = base_allowed and predicate(req)` — predicate never widens risk envelope.
**Why:** `lambda r: True` must not bypass `allow_r4=False` / `allow_r5=False`.

### TestRunnerAdapter uses run_tests for list commands
**Decision:** Pytest-style `test_command` lists go through `run_tests`, not `run_shell`.
**Why:** `run_shell` contract expects `cmd: list[str]` or `command: str`, not a list in `command`.

### Repo context skips missing candidate files
**Decision:** Only include `pyproject.toml` / `README.md` when they exist on disk.
**Why:** `_summarize_file` must not crash on `path.stat()` for missing paths.

## 2026-06-17 — P0.19 P0.20 Demo Harness

### Harness uses RepositoryAgentLoop, not entity demo
**Decision:** P0.19 harness routes through `RepositoryAgentLoop` + Tool Bus, not `demo.py` entity path.
**Why:** P0.20 must prove the governed repo-agent loop end-to-end.

### Independent test verification
**Decision:** Harness runs subprocess tests before and after agent loop; fails honestly on mismatch.
**Why:** No fake success — final status requires independent `run_tests()` pass when `apply=True`.

### Clear bytecode cache between phases
**Decision:** Remove `__pycache__` / `.pytest_cache` after initial failing pytest before agent apply.
**Why:** Stale `.pyc` from initial run caused flaky agent test results after patch.

### sys.executable for scenario test commands
**Decision:** `buggy_calculator` uses `{sys.executable} -m pytest -q`, not bare `python3`.
**Why:** Subprocess tests must use the active interpreter (venv) where pytest is installed.

### RepositoryAgentLoop persists kernel after run
**Decision:** `self.kernel = kernel` assigned during `run()` for trace summary access.
**Why:** Demo harness needs `trace.replay()` without refactoring `run()` return type.

## 2026-06-17 — P0.20 First Real Coding Agent Demo

### Evidence generated from existing report fields, not new instrumentation
**Decision:** `write_evidence` serializes the existing `DemoRunReport` + `CodeTaskReport` fields and computes the diff from scenario source vs final repo content.
**Why:** Smallest adapter; no broad refactor. Diff is honest (real before/after), not faked.

### Sandbox summary derived from public profile template
**Decision:** `build_sandbox_summary` calls `get_sandbox_profile(...)` to report network/secrets/exec flags.
**Why:** Honest, single source of truth for sandbox capabilities; avoids duplicating policy constants.

### Evidence sanitization
**Decision:** Repo path reduced to a repo id (basename) in `demo_run_report.json`; test outputs truncated; praxis summaries inherit secret redaction.
**Why:** Evidence must not leak absolute host paths or secrets.

### PASS criteria enforced honestly
**Decision:** `final_status="succeeded"` requires an independent post-patch test pass; harness returns `harness_failed` if the initial test unexpectedly passes.
**Why:** No fake success — PASS is only claimed when the governed loop genuinely fixed the bug.


## 2026-06-17 — P0.21 LLM Planning Bridge

### Repository LLM plans use a separate schema
**Decision:** Add `REPO_PLAN_SCHEMA` / `RepoPlanValidator` instead of reusing the P0.12 command-plan schema.
**Why:** Repository planning should describe files, risks, tests, and assumptions; it must not produce executable tool commands.

### LLM planning is proposal-only
**Decision:** `LLMRepoPlanner` converts validated JSON into `RepoTaskPlan`; patch/test execution remains unchanged through `RepositoryAgentLoop`, Runtime, Tool Bus, Approval, Sandbox, Verifier, Trace, and Praxis.
**Why:** Preserves “Entity proposes. Runtime disposes.” and avoids vendor tool-calling.

### Hybrid fallback records the failed LLM reason
**Decision:** `hybrid` mode falls back to deterministic planning only after an invalid/unavailable LLM plan and records `fallback_reason` / `planning_errors`.
**Why:** Keeps offline robustness without hiding provider/schema failures.

### Patch synthesis remains deterministic
**Decision:** LLM plans do not include patches; existing deterministic patch synthesis is reused and minimally extended for the `missing_validation` demo.
**Why:** The LLM should not execute tools or smuggle unvalidated code changes into the execution path.
