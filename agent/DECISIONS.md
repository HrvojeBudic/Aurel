# Decisions Log

## 2026-06-22 - P1.6.3 Risk Tier Policy Card Model

### DEC-P163-01: RiskTierPolicyCard defines risk semantics, not runtime classification
**Decision:** `RiskTierPolicyCard` defines R0-R6 semantics, reversibility, oversight, evidence expectations, and action-class mapping seeds. It does not classify arbitrary runtime actions.
**Why:** Classification belongs to a later risk classifier/resolver layer.

### DEC-P163-02: Risk tiers are closed-world R0-R6
**Decision:** Required tiers are exactly R0, R1, R2, R3, R4, R5, and R6. Missing, duplicate, or unknown tiers fail validation.
**Why:** Future governance consumers need a deterministic and stable risk vocabulary.

### DEC-P163-03: R5 requires explicit Operator confirmation
**Decision:** R5 must require trace, evidence, approval, explicit Operator confirmation, irreversible reversibility, and explicit Operator oversight.
**Why:** Serious irreversible or externally consequential actions must not be made weak by policy-card data.

### DEC-P163-04: R6 is denied and non-permissive
**Decision:** R6 must use denied oversight and denied reversibility and cannot allow execution, external egress, memory write, or tool write.
**Why:** Forbidden actions must remain forbidden in the semantic model.

### DEC-P163-05: Reversible and compensatable are distinct
**Decision:** `reversible` and `compensatable` are separate `ReversibilityLevel` values.
**Why:** Actions such as sending email are not reversible even if later compensation is possible.

### DEC-P163-06: Risk tier cards cannot grant authority or bypass contracts
**Decision:** Risk tier cards cannot grant authority, bypass generic policy cards, or replace behavioral contracts. Dangerous metadata keys and authority-shaped fields are rejected.
**Why:** Metadata and declarative risk semantics must not become a shadow control plane.

### DEC-P163-07: Runtime resolver, classifier, and P25 hardening are deferred
**Decision:** P1.6.3 does not implement a runtime risk classifier, policy runtime resolver, conflict detector, simulation mode, trace hook, CLI, report generator, enforcement engine, human oversight cards, or P25 hardening.
**Why:** P1.6.3 is the semantic model layer only.

## 2026-06-22 — P1.6.2 Behavioral Contract Schema

### DEC-P162-01: Behavioral contracts do not grant authority
**Decision:** A behavioral contract may define obligations, prohibitions, preconditions, postconditions, evidence requirements, and escalation rules — but it must never grant authority or bypass policy cards.
**Why:** Authority is a separate runtime gate. Behavioral contracts define behavioral expectations, not permissions.

### DEC-P162-02: Behavioral contracts are closed-world validated
**Decision:** Unknown top-level fields and dangerous fields (authority_grant, bypass_policy, skip_trace, etc.) are rejected. Metadata must not contain dangerous keys (operator_not_required, authority, etc.).
**Why:** Prevents behavioral contracts from becoming shadow authority or control mechanisms.

### DEC-P162-03: Behavioral contracts use deterministic canonical serialization
**Decision:** `behavioral_contract_to_canonical_dict()` produces sorted-key deterministic dicts. `serialize_behavioral_contract_canonical()` produces compact JSON. Sub-objects within obligations/prohibitions etc. are sorted by their type enum value. `policy_card_refs` are sorted. Same logical contract → same hash.
**Why:** Enables future trace binding, attestation, and integrity verification.

### DEC-P162-04: Behavioral contracts can reference policy card IDs
**Decision:** `policy_card_refs` is a tuple of policy card identity strings. No reference resolution or validation in P1.6.2.
**Why:** Establishes the relationship model without premature enforcement.

### DEC-P162-05: Behavioral contract error hierarchy extends PolicyCardError
**Decision:** `BehavioralContractError` inherits from `PolicyCardError`. Six subclasses: `BehavioralContractError`, `BehavioralContractValidationError`, `BehavioralContractSerializationError`, `BehavioralContractHashError`, `BehavioralContractUnknownFieldError`, `BehavioralContractUnsafeFieldError`.
**Why:** Consistent error taxonomy across the policy_cards package.

### DEC-P162-06: P1.6.2 does not implement runtime enforcement
**Decision:** No runtime enforcement, no policy resolver, no conflict detector, no simulation, no CLI. P1.6.2 is schema, validation, canonicalization, and hash-readiness only.
**Why:** Clean foundation-first. Enforcement and resolution are separate concerns.

### DEC-P162-07: Behavioral contracts live in the policy_cards package
**Decision:** Both `contracts.py` and `contract_schema.py` live inside `src/agentic_runtime/policy_cards/`. They share the same error taxonomy, validation patterns, and serialization conventions.
**Why:** Behavioral contracts are governance objects of the same class as policy cards. They belong together.

### DEC-P162-08: Schema versioning is mandatory for behavioral contracts
**Decision:** `schema_version` is a required top-level field. Only `"1.0"` is supported. Missing/unsupported versions fail validation.
**Why:** Same versioning discipline as policy cards. Enables future migration.

## 2026-06-22 — P1.6.1 Policy Card Schema

### DEC-P161-01: Policy Card Schema v1 is explicit
**Decision:** Schema version, required/optional/forbidden/canonical fields, and field categories are centralized in `schema.py` as the single source of truth. Validation uses schema definitions, not scattered inline lists.
**Why:** Schema truth must be inspectable, exportable, and testable in one place.

### DEC-P161-02: schema_version is part of the policy card contract
**Decision:** `schema_version` is a required top-level field on every `PolicyCard`. Unsupported versions fail validation. Missing/empty versions are rejected. The loader does not auto-default.
**Why:** Explicit versioning enables future migration, compatibility checks, and prevents silent version divergence.

### DEC-P161-03: Unsupported schema versions fail validation
**Decision:** Only `"1.0"` is supported. Any other value, including `null`, `""`, `"999.0"`, or `"experimental"`, raises `PolicyCardUnknownFieldError`.
**Why:** Fail-closed on unknown versions prevents accidental acceptance of cards written for future schema changes.

### DEC-P161-04: Required, optional, forbidden, and canonical fields are centralized
**Decision:** All field classifications live in `schema.py` constants. `validation.py` imports them rather than maintaining its own copies.
**Why:** Prevents drift between validation logic and schema documentation. Single point of truth.

### DEC-P161-05: Metadata remains descriptive only — expanded dangerous key set
**Decision:** Dangerous metadata keys expanded from 21 (P1.6.0) to 31 (P1.6.1) to include `grant_authority`, `permission_grant`, `evidence_bypass`, `delegation_grant`, `secret_access`, `network_access`, `operator_not_required`, `unrestricted`.
**Why:** Metadata must not become a second policy language.

### DEC-P161-06: Runtime resolver fields are reserved but not accepted yet
**Decision:** `resolver`, `resolution`, `enforcement`, `priority`, `conditions`, `effects`, `actions` are listed as `POLICY_CARD_RUNTIME_FUTURE_FIELDS` and rejected in P1.6.1 input.
**Why:** Prevents premature use of fields whose semantics are not yet defined.

### DEC-P161-07: P1.6.1 does not implement runtime resolver or P25 hardening
**Decision:** Schema formalization only. No behavioral contracts, resolver, conflict detector, simulation, CLI, or P25 hardening.
**Why:** Task scope is explicitly schema formalization. Clean separation of concerns.

## 2026-06-22 — P1.6.0 Policy Card Foundation

### DEC-P160-01: Policy cards do not grant authority
**Decision:** A policy card may describe required authority, risk limits, oversight requirements, scope, and constraints, but it must never grant authority merely by existing.
**Why:** Authority is a separate runtime gate (policy engine, HITL, operator consent). Embedding authority grant in policy card definitions would bypass governance.

### DEC-P160-02: Unknown authority/safety fields fail closed
**Decision:** Any unknown top-level field in a policy card dict, and any field implying authority grant, permission bypass, or policy override, must fail validation — never silently ignored.
**Why:** Closed-world enforcement prevents shadow control planes and accidental authority expansion through malformed input.

### DEC-P160-03: Policy cards use deterministic canonical serialization
**Decision:** All policy cards produce deterministic canonical JSON (sorted keys, compact separators) for hashing and comparison. Same logical card → same serialization → same hash.
**Why:** Enables future trace binding, evidence binding, attestation, and cache deduplication.

### DEC-P160-04: Policy cards support canonical hash readiness
**Decision:** `compute_policy_card_hash()` returns a SHA-256 hex digest of the canonical serialized representation. This hash is stable and deterministic.
**Why:** Foundational for future attestation, trace binding, and policy integrity verification.

### DEC-P160-05: Raw source hash and canonical hash are separate
**Decision:** `PolicyCardSource.raw_source_hash` represents the hash of raw input bytes (pre-parsing). The canonical hash represents the typed, validated logical content. They are intentionally independent.
**Why:** Raw source may differ by whitespace, ordering, or encoding while representing the same logical policy. Canonical hash captures semantic meaning, not transport artifacts.

### DEC-P160-06: P1.6.0 does not implement runtime policy resolver
**Decision:** P1.6.0 provides the policy card data model, validation, serialization, and hashing — but no resolver, conflict detector, simulation engine, CLI, report generator, or enforcement.
**Why:** Clean foundation-first architecture. Enforcement (P1.6.12+) and hardening (P25) are separate concerns.

### DEC-P160-07: P25 hardening is not pulled forward
**Decision:** P1.6.0 stays narrow. P25 hardening (Custos integration, path governance, full enforcement, output passports) is not implemented prematurely.
**Why:** Task scope is explicitly P1.6.0 foundation only. Broader architecture must not be compromised by premature scope creep.

## 2026-06-21 — P1.5.0 Evaluation Mirror Foundation Gate + Roadmap v3.2 Alignment

### DEC-P150-01: P1.5 begins only after sealed P1.4.20
**Decision:** P1.5.0 implementation requires verified P1.4.20 exit seal (SEALED_WITH_LIMITATIONS).
**Why:** Evaluation foundation builds on governed identity; P1.4 must be sealed first.

### DEC-P150-02: P1.5 is Evaluation Mirror Foundation, not full P4
**Decision:** P1.5.0 provides domains, subjects, scopes, criteria, and run envelopes only — not scoring, benchmarks, or Hub evaluation.
**Why:** P4 is the full Evaluation Mirror; collapsing P1.5 into P4 would overclaim scope.

### DEC-P150-03: Roadmap v3.2 is a macro update, not a reset
**Decision:** P1–P2 remain stable; P3–P21 refined; P22–P24 added for Hub architecture; P25=v0.9, P30=v1.0.
**Why:** Preserve completed work while extending macro direction.

### DEC-P150-04: Aurel Core is distinct from Hub tools
**Decision:** A-Hub, S-Hub, L-Hub, IDE are independent tools with native LLM/runtime layers.
**Why:** Hub independence prevents Aurel from claiming Hub capabilities as its own.

### DEC-P150-05: HQ is Aurel-native; Hubs/IDE are independent surfaces
**Decision:** HQ is Aurel's command center; Hub tools can be used with or without Aurel coordination.
**Why:** Clear product boundary between sovereign core and independent tool surfaces.

### DEC-P150-06: Hub memory does not automatically become Aurel Core memory
**Decision:** Memory domains are separated; promotion requires explicit authorized handoff.
**Why:** Prevents silent memory contamination across tool boundaries.

### DEC-P150-07: Open-weight lanes are sovereign foundation; external APIs are escalation
**Decision:** Mistral/DeepSeek/GLM/Llama are foundation; Codex/GPT/Claude/Gemini/OpenRouter are optional escalation.
**Why:** Sovereign identity should not depend on external API availability.

### DEC-P150-08: P22–P24 must not pull execution before P1–P2 are stable
**Decision:** Finish P1.5–P1.9, lock P2.0, then proceed P3+. Do not start Hub implementation early.
**Why:** Foundation must be stable before Hub architecture patches.

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

## 2026-06-17 — P1.1 Model Configuration + Secret Boundary

### Centralized config in agent/config/
**Decision:** Add `providers.yaml`, `models.yaml`, `runtime.yaml` with stdlib YAML subset parser — no PyYAML dependency.
**Why:** Zero runtime dependencies preserved; explicit operator-facing configuration before prompt system and integrations.

### Secrets from environment only
**Decision:** `EnvSecretProvider` resolves secrets; YAML rejects raw `api_key`/`secret`/`token` fields; `SecretRedactor` scrubs outputs.
**Why:** Secret boundary must be explicit before LLM patch synthesis and external integrations.

### local_only blocks remote providers
**Decision:** `runtime.yaml` defaults `local_only: true`; validation rejects remote profiles; `ModelRouter` blocks remote at runtime.
**Why:** Safe default for local-first, governance-first runtime; remote usage is opt-in.

### ModelRouter backward compatible
**Decision:** `ModelRouter()` without config behaves as P0.12; config bundle is optional.
**Why:** Existing mock/offline tests and `AUREL_MODEL_PROVIDER` env selection must not break.


## 2026-06-18 — P1.2.1 Public Entry + Runtime Verification Patch

### Demo exits 0 with safe no-skill message when evidence gates not satisfied
**Decision:** Add guard `skills = kernel.skills.all(); if not skills: print(safe message)` instead of crashing on `skills[0]`.
**Why:** In safe/governed mode, no skill promotion is a valid outcome. The runtime must not crash or fake a skill. Human escalation is the correct governed path when evidence is insufficient for promotion.

### Sandbox CPU limit inherits profile max_timeout_seconds
**Decision:** `materialize_sandbox_backend` passes `cpu_seconds=int(profile.max_timeout_seconds)` to `UnsafeLocalSandbox`.
**Why:** The `restricted_local` profile declared `max_timeout_seconds=30.0` but `UnsafeLocalSandbox` defaulted `cpu_seconds=10`. The mismatch caused processes to be killed by rlimit before the profile's declared timeout, producing silent exit_code=-9 in slower environments.

### CLI alpha-seal smoke test uses --skip-tests to avoid nested pytest
**Decision:** `test_cli_alpha_seal_skip_tests_exits_zero` uses `alpha-seal --skip-tests` (docs/compile/sandbox checks only).
**Why:** Running `alpha-seal --skip-coverage` inside the test suite creates nested pytest, which may timeout or get OOM-killed. The `--skip-tests` form verifies the CLI entrypoint and most readiness checks without recursion.

## 2026-06-17 — P1.2 Prompt System Seed

### Prompt manifests are assets, not authority
**Decision:** Add prompt manifests under top-level `prompts/` and validate policy fields, but do not let prompts grant tools, writes, secrets, or policy changes.
**Why:** Prompts propose language; Runtime, Custos-style validators, policy, sandbox, and verifiers decide.

### Trace summaries store hashes and metadata by default
**Decision:** `PromptTraceSummary` records prompt identity, ownership, allowed profiles/tasks, hashes, variables used, and `raw_prompt_stored: false`; CLI render omits raw prompt previews.
**Why:** Operators need inspectable prompt provenance without storing raw prompts or secrets by default.

### P1.1 model profile validation is optional
**Decision:** `PromptRegistry` can validate `allowed_model_profiles` against `ModelConfigBundle`, while loading still works without config.
**Why:** Prompt assets should remain testable offline and must not require real API keys.

### Repo planner prompt integration stays fallback-safe
**Decision:** `LLMRepoPlanner` accepts an optional prompt registry for `repo_planner`; otherwise it keeps the existing hardcoded prompt behavior.
**Why:** P1.2 seeds the prompt system without changing execution behavior or broad-refactoring P0.21 planning.

## 2026-06-21 — P1.4.2 Persona Manifest v2.0

### Persona is an expression contract, not authority
**Decision:** Implement frozen typed persona manifest with invariant registry (PM-001–PM-007), validator, SHA-256 hash, and deterministic safe summary; config at `config/aurel/persona_manifest.yaml`.
**Why:** Persona must define expression/interaction behavior while proving it cannot grant permissions, override identity/policy, change autonomy, or canonize untrusted input.

### Safe summary is preparation, not the P1.4.5 compiler
**Decision:** `build_persona_safe_summary()` returns a deterministic object with no raw YAML and no permission/tool/autonomy language; the Identity Prompt Context Compiler is deferred to P1.4.5.
**Why:** Raw manifest must never be injected into prompts (PM-007); prompt context must be compiled from validated typed objects.

### Persona CLI uses the identity namespace
**Decision:** Expose `identity persona {show,validate,hash,attest,summary}` to match the existing `identity kernel` namespace rather than a new top-level `persona` command.
**Why:** Project-consistent CLI structure; persona is part of the identity layer.

## 2026-06-21 — P1.4.1 Identity Kernel v2.0

### Identity Kernel is a trust anchor, not persona or autonomy
**Decision:** Implement frozen typed kernel with invariant registry, validator, and SHA-256 hash; config at `config/aurel/identity_kernel.yaml`.
**Why:** P1.4.1 must be machine-readable, tamper-evident foundation for Self-Model, Identity Card, and seal tests without collapsing persona/autonomy layers.

### Attestation writes are explicit only
**Decision:** `write_identity_kernel_attestation()` and CLI `--write` only; no import-time or silent runtime mutation.
**Why:** Trust anchor changes must be auditable and operator-initiated.

### Critical invariants use fail_boot
**Decision:** All IK-001–IK-008 invariants are critical, immutable, and `violation_action: fail_boot`.
**Why:** Identity law violations must fail closed before any later P1.4 runtime integration.

## 2026-06-21 — P1.4.0 Identity + Autonomy Scope Contract

### Identity is not policy; persona is not authority
**Decision:** P1.4 constitutional docs and stub package docstrings encode separation: identity/persona/mode describe presentation and self-model; `policy.py`, approval, and Tool Bus decide execution.
**Why:** Prevents prompt-injected or self-declared identity from granting tool permissions or bypassing governance.

### Autonomy is Operator-selected; no self-escalation
**Decision:** Document and test that Aurel may request higher autonomy but cannot activate it; measured autonomy deferred to P1.4.9/P1.4.12.
**Why:** Local-first sovereign agent under one Operator requires explicit autonomy elevation, not agent self-grant.

### Heretic mode is cognitive freedom, bounded by constitutional floor
**Decision:** Heretic stub and constitution define red-team/cognitive latitude without default side effects, canon rewrite, or tool self-grant.
**Why:** Maximum cognitive freedom must not become uncontrolled execution escape.

### P1.4.0 is docs-first; stubs only
**Decision:** Six packages plus `p14_scope.py` constants; no Identity Kernel, Autonomy Scale, fake memory/world model, or policy engine in P1.4.0.
**Why:** Scope contract must align roadmap before incremental P1.4.x implementation.

### Capability honesty before P1.5 evidence
**Decision:** Distinguish planned / implemented / verified / unavailable; forward-hook P1.5–P1.9 without claiming those features are active.
**Why:** Agent trust requires honest capability surfaces before Evaluation Mirror exists.

## 2026-06-21 — P1.3.9 Tool Manifest Layer Seal

### Two ToolRegistry types remain separate
**Decision:** Keep `tool_manifest/registry.py` `ToolRegistry` (manifest catalog) separate from `tools.py` `ToolRegistry` (executable handler registry). Document as ManifestToolCatalog vs ExecutionToolRegistry in docs only — no public rename in P1.3.9.
**Why:** Merging would collapse declarative capability metadata into execution authority.

### No draft→CommandEnvelope bridge in P1.3
**Decision:** P1.3.9 documents but does not implement `ToolInvocationDraft` → `CommandEnvelope` → `runtime.submit` bridging. Future bridge planned at P6 Governed Tool Bus Expansion.
**Why:** Authority/command layer must exist before executable bridging; P1.3 is declarative only.

### GOV-HOTFIX invariants confirmed at seal
**Decision:** P1.3.9 seal references canonical tests for prompt risk_tier fail-closed, YAML no silent truncation, restricted_local honest diagnostics, and run_shell R4 — without weakening HITL or sandbox tests.
**Why:** Governance integrity must survive alongside manifest layer hardening.

## 2026-06-21 — P1.4.7-MG Agent Identity Card Merge Gate Hardening

### Self-model policy must thread through card validation
**Decision:** `build_agent_identity_card()` requires an explicit `self_model_policy`; no silent default reload inside the builder. `build_agent_identity_card_with_default_policy()` is the only explicit default-policy wrapper.
**Why:** `--self-model-policy-path` must affect the final validation gate, not only self-model construction.

### Capability inventory is canonical in `capability_inventory.py`
**Decision:** Self-model capability status derives from `CAPABILITY_INVENTORY`; validation `PLANNED_CAPABILITY_IDS` / `IMPLEMENTED_CAPABILITY_IDS` import from this module. P1.4.7 Agent Identity Card is `implemented`.
**Why:** Capability honesty — Aurel must not under-report implemented P1.4.7 work.

### IdentitySourceBundle for card path
**Decision:** Introduce `IdentitySourceBundle` for single-load identity sources on the P1.4.7 card build path; defer full-stack bundle adoption for prompt-context CLI and `build_aurel_self_model_from_paths`.
**Why:** Reduce TOCTOU/reload drift without blocking P1.4.8 on a full identity refactor.

### CLI decomposition via `cli_modules/`
**Decision:** Extract identity CLI handlers to `cli_modules/identity_commands.py`; keep `cli.py` as composition root. `repo_root()` in `cli_modules/common.py` uses `parents[3]` (one level deeper than `cli.py`).
**Why:** Prevent monolithic CLI growth; P1.4.x patches should not all touch one 2400-line file.

### CLI config dir uses library default
**Decision:** Expose `model_config.default_config_dir()`; CLI `config_dir()` delegates to it.
**Why:** CLI and library must resolve the same default config directory.

## 2026-06-21 — P1.4.8 Autonomy Scale Engine

### Autonomy is action-scoped, never global
**Decision:** `resolve_autonomy_decision()` takes a single `AutonomyRequest` and returns a single `AutonomyDecision`. No aggregate/global/scored autonomy.
**Why:** P1.4.8 delivers per-action decision logic; P1.4.9 adds measured/aggregate scoring. Collapsing both into one layer would conflate gating with measurement.

### A7 means denied, not highest autonomy
**Decision:** `AutonomyLevel.A7_DENIED` has numeric rank `-1` internally and `is_denied()` returns True only for A7. Invariant INV-P148-02 rejects `allowed=True` with A7.
**Why:** The numeric ordering A0→A6 is for lifecycle ceiling checks only. A7 must never be misinterpreted as "more autonomous than A6."

### Fail-closed on unknowns
**Decision:** Missing risk tier, missing reversibility tier, and UNKNOWN action category all produce A7_DENIED decisions. Invalid enum values in requests raise `AutonomyValidationError`. Semantic denials (e.g. planned capability) produce A7_DENIED with blockers.
**Why:** AUTONOMY-03 in the trust constitution demands that "any ambiguity in authority, action scope, or evidence provenance is resolved in the Operator's favor (deny/require-approval)."

### Baseline autonomy per action category
**Decision:** `BASELINE_BY_ACTION_CATEGORY` maps each `ActionCategory` to a fixed `AutonomyLevel`. Risk, reversibility, lifecycle, and capability checks escalate from this baseline.
**Why:** Predictable, deterministic mapping. No learned or self-tuned autonomy.

### Authority scope gating is lenient by default
**Decision:** `_check_authority_scope()` allows ANSWER and SUGGEST without checks. Beyond SUGGEST, it consults `execution_authority.allow_any` on the operator contract. If absent, access is allowed (operators should configure strict fields).
**Why:** Avoids blocking legitimate actions from agents that haven't yet configured explicit authority scopes. P1.5/P6 will add tighter permission models.

### Lifecycle state defaults to full access when absent
**Decision:** If an agent identity card has no `lifecycle_state` field, the resolver skips lifecycle gating rather than denying all actions beyond A1.
**Why:** Not all agents have lifecycle configurations. Introducing hard denial for unconfigured agents would break backward compatibility.

## 2026-06-21 — P1.4.9 Measured Autonomy Score

### Measurement is derived from decisions, never declared
**Decision:** `measure_autonomy_score()` takes `Sequence[AutonomyDecisionRecord]` and computes statistics. No manual autonomy class assignment is possible. INV-P149-01 enforced via seal tests.
**Why:** Agent trust requires that autonomy claims are evidence-backed, not self-declared.

### No global autonomy percentage
**Decision:** `MeasuredAutonomyScore` has no `global_score`, `autonomy_percentage`, or `aggregate` field. The most aggregated output is `MeasuredAutonomyClass`, which is a qualitative class, not a numeric percentage.
**Why:** A single autonomy percentage is misleading — it collapses very different autonomy levels and risk profiles into one number.

### Highest verified level requires 100% block-free decisions at that level
**Decision:** `_compute_highest_verified()` only counts a level as verified if ALL allowed decisions at that level have zero blockers. A single blocked decision at a level invalidates verification.
**Why:** Conservative evidence posture — partial verification is not verification.

### A7 is excluded from AUTONOMY_LEVEL_ORDER
**Decision:** `AUTONOMY_LEVEL_ORDER` is `(A0, A1, A2, A3, A4, A5, A6)` — A7 is never ranked. `_level_rank(A7) = -1`. Seal tests enforce that A7 never appears in highest_verified_level.
**Why:** Denial is not autonomy. Including A7 in ordering would allow statistical artifacts to suggest higher autonomy from denial counts.

### JSONL persistence is transitional, not canonical
**Decision:** `append_autonomy_decision_record` and `load_autonomy_decision_records` store/load JSONL at `agent/state/autonomy_decisions.jsonl`. Invalid lines are silently skipped.
**Why:** No database introduced. The project's existing Ledger or trace store should eventually subsume this. JSONL is a lightweight, audit-friendly intermediary.

## 2026-06-21 — P1.4.10 Capability Claim Boundary Engine

### Anti-hype firewall: claims evaluated against evidence, not roadmap
**Decision:** Every capability claim must cite evidence sources (tests, seal reports, CI, operator attestation). Roadmap status alone cannot satisfy verification-level evidence requirements.
**Why:** Prevents "we plan to implement X" from being claimed as "X is working" in agent self-description, identity card, or prompts.

### Roadmap ≠ Implementation
**Decision:** Roadmap entries are not valid evidence for verification-level claims. Claims referencing only roadmap status are downgraded or rejected.
**Why:** Agent trust requires that Aurel never confuses intention with capability.

### Implementation ≠ Verification
**Decision:** Module/class/file existence does not prove a capability works. Claims referencing only code existence (no tests, no seal, no CI green) are rejected at the verification boundary.
**Why:** An empty stub or broken module must not be claimable as a verified capability.

### Verification ≠ Production Readiness
**Decision:** Verified capabilities (tests pass, CI green) still need production seals (deployment evidence, stress tests, operator sign-off) to reach full maturity. Claims distinguish `verified` from `production_ready`.
**Why:** Passed tests in a dev environment do not mean production-grade reliability.

### Global autonomy blocked
**Decision:** "Aurel is autonomous" and similar global-agency claims are FORBIDDEN with no safe rewrite path. Only action-scoped autonomy claims are allowed.
**Why:** Global autonomy claims violate the trust constitution; autonomy is always contextual and operator-granted, not innate.

### Safe rewrite must preserve truth
**Decision:** `rewrite_claim()` produces a safer, evidence-aligned version that never introduces marketing spin, overpromise, or capability inflation. If no safe rewrite is possible, the claim is rejected outright.
**Why:** Autonomy boundaries must constrain even "helpful" rewording; a dangerous claim must not be softened into a still-dangerous claim.

### Static registry: 14 pre-registered claims
**Decision:** Claims are pre-registered with evidence requirements in `capability_claims.py`. No dynamic claim registration at runtime.
**Why:** Auditability and deterministic evaluation; prevents prompt-injected or hallucinated claims from entering the evaluation path.

### Fail-closed: unknown claims or missing evidence → FORBIDDEN
**Decision:** Claims not in the registry, or claims with insufficient evidence for the requested level, produce FORBIDDEN status. No default-allow.
**Why:** Trust boundary must be fail-closed; Aurel must never claim capabilities it cannot prove.

### P1.4.11 handoff: External Doctrine Assimilation Registry
**Decision:** P1.4.10 establishes the evaluation framework (evidence gates, anti-hype firewall, fail-closed) that P1.4.11 will extend to external doctrinal sources (legal, regulatory, ethical frameworks).
**Why:** Internal capability honesty must precede external doctrine assimilation.

## 2026-06-21 — P1.4.11 External Doctrine Assimilation Registry

### Doctrine is roadmap influence, not capability evidence
**Decision:** External doctrine records can map to existing roadmap modules and future work, but they cannot grant capability, override canon, or authorize implementation claims.
**Why:** P1.4.10 already established that roadmap and evidence are separate. P1.4.11 keeps external material inside that boundary.

### Source hash required for every doctrine input
**Decision:** Every registered doctrine input requires a SHA-256 source identity hash. Registry validation fails closed when the hash is missing or malformed.
**Why:** P1.4.12 will build stronger raw source and canonical hash attestation; P1.4.11 must not accept unauditable doctrine.

### Doctrine maps into existing P-number roadmap slots
**Decision:** Doctrine mappings must reference existing-style P-number roadmap modules. External doctrine cannot introduce replacement numbering.
**Why:** External architecture or business material may shape requirements, but it cannot rewrite Aurel's canonical roadmap by declaration.

### Doctrine claim boundaries route through P1.4.10
**Decision:** Doctrine-derived overclaims such as production Agentic OS, ABOS deployment, and AETHER multimodal intelligence are evaluated through the P1.4.10 claim boundary engine and blocked or downgraded.
**Why:** Doctrine must not bypass the evidence-gated anti-hype firewall.


## 2026-06-21 - P1.4.12 Raw Source + Canonical Hash Attestation

### Raw hash and canonical hash stay separate
**Decision:** Store `raw_source_hash` and `canonical_typed_hash` as distinct fields in `SourceHashPair` and `SourceAttestation`.
**Why:** Raw source integrity and canonical typed meaning answer different questions. Hashing only the typed object can hide unknown authority or safety fields in the raw source.

### Attestation is not trust or capability
**Decision:** Source attestations explicitly include non-goals for truth, trust, capability, cryptographic signing, and tamper-proof storage.
**Why:** A hash can prove same-content integrity for a seen input, not truth, safety, source trust, or implemented capability.

### Identity bundle owns identity source attestations
**Decision:** Extend `IdentitySourceBundle` with attestations for all seven identity sources instead of creating a competing bundle.
**Why:** P1.4.7-MG already introduced the single-load identity source surface; P1.4.12 adds integrity metadata to that path.

### Governance-shaped unknown fields fail closed
**Decision:** Unknown authority, safety, governance, policy, capability, secret, and override-shaped fields are recorded as rejected unknown fields and produce `REJECTED_UNKNOWN_FIELDS` for attestation.
**Why:** Identity/governance config must not silently ignore fields that look like authority or safety changes.

### Doctrine attestation does not become evidence of implementation
**Decision:** External doctrine records can produce `external_doctrine` source attestations, but those attestations remain integrity evidence only.
**Why:** P1.4.11 doctrine can influence roadmap mapping; it cannot grant capability or authorize implementation claims.

## 2026-06-21 - P1.4.13 Authority Delta Detector

### Authority delta detection is not consent
**Decision:** P1.4.13 detects dangerous/relevant authority deltas and marks them for Operator consent; it does not grant consent, approve changes, or execute tools.
**Why:** A detection-signal-only layer is safer and simpler. P1.4.14 will bind Operator consent to those deltas. Mixing detection and consent in the same module would create ambiguous authority.

### Valid source does not imply safe change
**Decision:** An attested, validated source can still represent a dangerous authority expansion. The delta detector treats validation status separately from authority impact.
**Why:** Hashing proves same-content integrity; it does not prove the content preserves the same authority, safety, or oversight posture.

### Conservative tool classification with documented heuristics
**Decision:** Classify tools as external-effect, write, or internal/read-only using conservative string heuristics rather than absent metadata.
**Why:** Rich tool metadata does not yet exist (P1.3/Tool Manifest, P6 Governed Tool Bus). A conservative seed heuristic with explicit limitation documentation is better than pretending all tools are equal.

### Authority delta reports use attestation refs when available
**Decision:** `AuthorityDeltaReport` and individual `AuthorityDelta` records carry `old_attestation_id` and `new_attestation_id` from P1.4.12 `SourceAttestation` objects when provided.
**Why:** P1.4.14 and later attestation-based consent workflows need to know exactly which attested sources produced which deltas.

### Severity ordering uses explicit table, not enum comparison
**Decision:** Compare severity levels using `SEVERITY_ORDER.index()` rather than relying on Python enum ordering (`>` or `<`).
**Why:** Python enum comparison is fragile and can depend on definition order. An explicit immutable order tuple is stable and transparent.

## 2026-06-21 - P1.4.14 Operator Consent Binding

### Consent is not global
**Decision:** Consent binds to exact delta IDs, source kind, and old/new attestation IDs. It does not cover any other authority delta, even the same field with different values.
**Why:** Global consent would make the delta detection in P1.4.13 meaningless. Fine-grained consent preserves the Operator's gatekeeping role over each specific authority change.

### Consent is not permanent by default
**Decision:** Consent records carry an `expires_at` field and expire independently of status. Expired consent is invalid for binding validation regardless of grant/revoke status.
**Why:** Authority deltas can accumulate over time; consent from six months ago should not implicitly authorize today's different source state.

### Consent fails closed
**Decision:** `grant_operator_consent()` raises `ConsentValidationError` when preconditions aren't met (missing operator_id, empty deltas, missing risk acknowledgement for HIGH/CRITICAL). Denied and revoked records are permanently invalid.
**Why:** A consent system that silently succeeds in degraded states is worse than no consent system at all.

### Risk acknowledgement required for HIGH/CRITICAL
**Decision:** Grants and validations both require `risk_acknowledged=True` when highest severity is HIGH or CRITICAL. The request model exposes `requires_explicit_risk_acknowledgement` to signal this upfront.
**Why:** The Operator must consciously acknowledge they are approving authority expansions or oversight weakening before consent becomes valid. Silent risk acceptance undermines the governance boundary.

### SESSION_LIMITED scope is unsupported
**Decision:** SESSION_LIMITED exists as an enum value but `validate_operator_consent_binding` rejects it with `scope_not_supported`.
**Why:** The runtime does not currently have a session model. Adding scope semantics prematurely would create scope violations that can't be enforced.

### Consent does not grant capability
**Decision:** A valid consent record says "the Operator accepted this exact delta". It does NOT mark any capability as implemented, verified, or production-eligible.
**Why:** Capability verification is a separate concern (P1.4.10, P1.4.11). Mixing consent with capability status would create ambiguous trust signals.

## 2026-06-21 - P1.4.15 Identity Governance Command Surface

### P1.4.15 is a command surface, not an interactive agent
**Decision:** P1.4.15 exposes a stable CLI for identity governance inspection (`status`, `verify`) and routes subcommands to existing modules — it does NOT build an interactive terminal agent, Codex-like coding loop, or TUI.
**Why:** The command surface provides machine-readable JSON endpoints and human-readable summaries for automation, CI, and tests. Interactive shell/TUI layers (P2, P8) are separate concerns that need session management, workspace context, and richer UX.

### Standardized JSON envelope for all identity commands
**Decision:** Every identity command that supports `--json` outputs `{ok, command, status, errors, warnings, result}`. `ok` is true only when `status == OK` and errors is empty.
**Why:** Heterogeneous JSON shapes across commands would break automation. A stable envelope allows scripts and CI to check `ok` and `errors` uniformly regardless of the specific subcommand.

### Status and verify are read-only by construction
**Decision:** `identity status` and `identity verify` use import-based subsystem probes only. They do not import modules that mutate state, do not write files, and do not execute tools.
**Why:** An operator inspecting governance health should never alter the system. Read-only semantics are proven by test: repeated calls produce identical output and side-effect-free behavior.

### Subsystem status uses import checks, not runtime probing
**Decision:** Subsystem status is determined by lightweight `__import__()` calls rather than loading full configuration, parsing YAML, or making runtime calls.
**Why:** Configuration file paths, YAML validity, and runtime state are environment-dependent. Import checks are the simplest signal that works in all environments (CI, headless, local) without configuration coupling.

### Identity consent is signal-only until runtime wiring
**Decision:** P1.4.13 authority delta detection and P1.4.14 operator consent binding remain CLI/report signals. They do not gate `AgenticRuntime.submit()` until a later patch (P1.4.15+) explicitly wires enforcement.
**Why:** Detection and consent binding are complete primitives; mixing them into the runtime pipeline without a designed bridge would create ambiguous authority boundaries.

## 2026-06-21 — P1.4.16 Identity Test Battery

### Two-file split: battery engine and scenario runners
**Decision:** Battery engine (`identity_test_battery.py`) contains models (case, score, status) and the engine (run, aggregate). Scenario runners (`identity_test_battery_scenarios.py`) contain concrete scenario definitions with per-category runner functions.
**Why:** Separates the battery framework from the domain-specific scenarios. The engine is reusable; scenarios can grow independently without touching the core scoring logic. Late imports in scenario dispatchers avoid circular dependencies between identity modules.

### Late imports in scenario runner dispatch
**Decision:** Each scenario runner function imports its target module (e.g., `identity.kernel`, `identity.persona_manifest`) at call time rather than at module top level.
**Why:** The battery sits above all identity layers and must not create import-time coupling between identity modules that may reference each other. Late imports allow the battery to import scenario runners without immediately pulling in the entire identity stack.

### CLI battery wraps all 26 cases into single aggregate status
**Decision:** `identity test-battery run` runs all 26 cases and aggregates into PASSED (all OK), FAILED (any FAIL), DEGRADED (blend of OK + SKIP, no FAIL), or SKIPPED (all SKIP). Individual case results are reported in JSON output.
**Why:** A single aggregate status provides a clear go/no-go signal for CI, seal checks, and operator health inspection without requiring manual inspection of 26 individual results.

### Adversarial scenarios included by default, CLI toggleable
**Decision:** The full battery includes adversarial scenarios (edge cases, boundary violations, invalid inputs) by default. CLI `--scenarios` flag allows toggling adversarial cases on/off.
**Why:** Adversarial coverage is part of the trust boundary — a battery that skips adversarial cases would provide false confidence. The toggle exists for fast sanity checks in development, but the default is comprehensive.

## 2026-06-21 — P1.4.17 Agent Lifecycle Eligibility State Machine

### Lanes model instead of boolean flags
**Decision:** Each lifecycle state maps to 9 lanes (eligible/blocked + required gates) rather than a flat set of boolean permission flags.
**Why:** A lane model captures structured eligibility — which agentic capabilities are available in which state — without conflating lifecycle with permission. Boolean flags would collapse structural context into oversimplified on/off switches.

### RESTRICTED is reason-sensitive, not dead
**Decision:** The RESTRICTED state applies restrictions based on the transition reason code (e.g. COMPLIANCE_VIOLATION, CONSENT_EXPIRED), not a blanket maximum-security block.
**Why:** A blanket-restricted state would be operationally equivalent to REVOKED. Reason-sensitive restrictions allow fine-grained lane blocking (e.g. block writes but allow reads) without terminating the agent's existence.

### ACTIVE is gated, not unlimited
**Decision:** The ACTIVE state has explicit lane eligibility declarations; it does not imply unlimited access to all lanes.
**Why:** "Active" must not be misinterpreted as "all capabilities allowed." Lane eligibility in ACTIVE is still constrained — Policy and HITL remain the permission authorities.

### Recommendation engine reads governance signals, does not apply
**Decision:** `recommend_transition()` reads authority delta reports, consent records, and battery status as inputs, but only outputs a recommendation — it never applies a transition or mutates state.
**Why:** Lifecycle transitions are Operator-initiated. An automated recommendation is a governance signal, not an autonomous state change. The Operator remains the final transition authority.

### Terminal REVOKED is hard-fail-closed
**Decision:** REVOKED has zero eligible lanes, zero outgoing transitions, and is irreversible. Any attempt to transition out of REVOKED fails closed with no fallback.
**Why:** Revocation must be a one-way terminal state. A soft REVOKED with escape hatches would undermine the trust boundary — a revoked agent must never re-enter any active lane.

## 2026-06-21 — P1.4.18 Trust Evidence Linkage

### Trust posture is strictly categorical, never numeric
**Decision:** `resolve_trust_posture()` returns a `TrustPosture` enum value (UNTRUSTED, MINIMAL, LOW, MODERATE, SUBSTANTIAL, HIGH, BLOCKED). There is no numeric trust score, percentage, or aggregate rating.
**Why:** A single numeric trust score collapses multi-dimensional evidence (kernel hash, test battery, consent records, authority deltas, lifecycle state) into a misleading single number. Categorical posture forces operators to read the linked evidence rather than trust a number.

### Evidence linkage is not truth validation
**Decision:** `TrustEvidenceLinkageReport` links evidence references and classifies posture — it does not validate whether the evidence is true, correct, or trustworthy. Source attestation hashes prove integrity, not truth.
**Why:** P1.4.12 established that hash-based attestation is not truth. P1.4.18 respects this boundary: linkage explains what evidence exists and how it was assembled, not whether that evidence is correct.

### Trust evidence bundle validation is read-only
**Decision:** `validate_trust_evidence_bundle()` checks structural integrity and reference consistency. It does not grant authority, execute tools, mutate lifecycle state, calculate numeric scores, or validate truth of evidence.
**Why:** Trust posture is a governance signal, not a permission gate. P1.4.18 intentionally stops at classification and explanation — authority decisions remain with Policy, HITL, and the Operator Consent Binding.

## 2026-06-21 — P1.4.19 Identity Docs / Reports / State Update

### P1.4.19 is consolidation, not new governance
**Decision:** P1.4.19 adds no new governance semantics. It provides structured P1.4 inventory (18 CLI groups, 15 invariants, 15 known limitations, 22-item P1.4.20 exit seal checklist) via `p14_seal_readiness.py` and `identity seal-readiness --json`. It does not add new identity modules, grant authority, overclaim autonomy, claim production readiness, claim ABOS/AETHER implementation, or mutate state.
**Why:** P1.4.19 is an audit/consolidation gate before the P1.4.20 exit seal. It ensures all P1.4 work is catalogued, indexed, and ready for final verification without introducing new governance surfaces that would themselves need verification.

### P1.4.19 prepares P1.4.20 and does not replace it
**Decision:** P1.4.19's seal-readiness report identifies what is complete and what must be verified in P1.4.20. It does not perform the exit seal itself. P1.4.20 performs the final exit seal verification using P1.4.19's indexes as canonical reference.
**Why:** The consolidation gate must not become the seal gate. P1.4.19 documents readiness; P1.4.20 verifies it. Separating these stages prevents premature sealing.

### P1.4 module/cli/invariant/limitation/checklist indexes are canonical for P1.4.20 verification
**Decision:** `P14_CLI_GROUPS` (18 entries), `P14_INVARIANTS` (15), `P1419_INVARIANTS` (10), `P14_KNOWN_LIMITATIONS` (15), and `P1420_SEAL_CHECKLIST` (22) are the canonical reference indexes that P1.4.20 will use for exit seal verification.
**Why:** A single source of truth for what exists in P1.4 prevents drift between documentation, tests, and seal criteria. P1.4.20's verification can trust these indexes as authoritative without needing to re-discover the module map.

## 2026-06-21 — P1.4.20 P1.4 Identity & Autonomy Exit Seal

### P1.4.20 is the final boundary seal for P1.4 — validates, does not add governance
**Decision:** P1.4.20 is a pure verification layer. It runs 56 seal checks across 5 categories (import/object, CLI, governance invariants, adversarial, docs consistency) and produces a seal result. It does not add new identity modules, governance semantics, authority grants, consent grants, or tool execution.
**Why:** A boundary seal must verify, not extend. If P1.4.20 added governance, it would create a recursive seal problem — who seals the seal? The seal is honest about what P1.4 has and hasn't achieved.

### SEALED_WITH_LIMITATIONS is the honest outcome
**Decision:** The seal result is `SEALED_WITH_LIMITATIONS`, not `SEALED`. Limitations are explicit: P1.5/P1.6/P1.8/P6/P7 are not yet implemented, 15 known limitations from P1.4.19 carry forward. Sealing P1.4 with full pass would be dishonest.
**Why:** Agent trust requires honesty about limitations. Claiming a full seal when known gaps exist would undermine the entire trust constitution. SEALED_WITH_LIMITATIONS tells the Operator exactly what P1.4 covers and what it doesn't.

### Seal CLI is read-only — no mutation, no authority grant, no consent grant
**Decision:** `identity p14-seal run/list-checks/run-check` are read-only commands. They inspect the system, run verification checks, and report results. They do not mutate identity sources, write attestations, grant consent, execute tools, or change runtime state.
**Why:** The seal is a diagnostic signal, not an action gate. Seal CLI must never become a backdoor for authority or consent. Read-only by construction is enforced by tests: repeated calls produce identical output.

### Next phase is P1.5.0 Evaluation Mirror Foundation
**Decision:** P1.4 is sealed. P1.5.0 Evaluation Mirror Foundation is the next phase, per the P1.4 scope contract forward hooks.
**Why:** P1.5 introduces reflection and evaluation infrastructure that builds on the sealed P1.4 foundation. Sequencing is explicit: the identity trust surface must be sealed before Aurel can evaluate itself.
