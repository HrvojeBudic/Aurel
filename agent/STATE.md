# Repository State

_Last updated: 2026-06-23 (P1.6.8S - Repository Reality & Policy Card Stabilization Seal)_

## Current Roadmap Pointer

- Last completed: P1.6.8 — Prompt Policy Card Model
- Current stabilization: P1.6.8S — Repository Reality & Policy Card Stabilization Seal
- Next planned: P1.6.9 — Sandbox Policy Card Model
- Last verified against commit: pending final commit for P1.6.8S

## What works

- Full governed command pipeline: policy → HITL → budget → sandbox → verify → trace → memory
- ...
- P1.4.14 Operator Consent Binding: delta-bound consent with attestation binding, risk acknowledgement, 55 tests
- P1.4.15 Identity Governance Command Surface: unified CLI, `identity status`/`verify`, JSON envelope, 53 tests
- Plan validation halts on empty/invalid/unsupported plans
- Persistent and in-memory trace ledgers with hash-chain verification
- P1.5.10X canonical AurelTraceLog contracts
- P1.5.11A Golden Thread A
- P1.5.11B Capability Evidence ↔ Trace / Context Binding
- P1.5.12 Evaluation Case Extraction Seed: candidate EvaluationCase/RegressionCandidate from capability evidence, 42 extraction tests
- **P1.5.13 Verifier Normalization with Limitations**:
  - `src/agentic_runtime/contracts/verifier.py` upgraded with `VerifierKind` enum (6 kinds), `VerifierNormalizationReport`, and enhanced `VerifierResult` v2 with `verifier_kind`, `normalized_from`, `created_at`
  - `src/agentic_runtime/evaluation/verifier_normalization.py`: 6 stub verifier normalizers (deterministic, operator review, policy check, LLM judge stub, context adequacy, evidence integrity)
  - Golden Thread A now uses normalized `VerifierResult` via `EvidenceIntegrityVerifierStub`
  - Hard invariants enforced: non-empty limitations, evidence_refs for pass, source_trace_event_ref required, reason non-empty, confidence 0.0–1.0
  - 32 new normalization tests, all 802 core tests pass
  - No raw verifier output reaches capability evidence or evaluation cases
  - Next: P1.5.14 Evaluation Mirror Runtime Hook
- **P1.5.14 Evaluation Mirror Runtime Hook**:
  - `src/agentic_runtime/contracts/evaluation_runtime.py`: 5 new contracts (EvaluationTargetRef, EvaluationRequest, EvaluationRun, EvaluationEvent, EvaluationRunResult) + 5 enums
  - `src/agentic_runtime/evaluation/runtime_hook.py`: `run_evaluation()` runtime-callable hook
  - Golden Thread A extended with evaluation runtime integration; GoldenThreadAResult gains 5 new fields
  - Anti-promotion structural enforcement: no capability_promoted, memory_written, skill_created, reflex_created, policy_changed fields in any contract
  - 49 new tests (25 hook, 18 invariants, 6 golden thread), all 851 core tests pass
  - **P1.5.18 Evaluation ↔ Memory Candidate Bridge (COMPLETE)**:
  - Bridges evaluation/feedback/capability outputs to MemoryCandidate records
  - MemoryCandidate is candidate-only; NEVER committed, NEVER active recall, NEVER creates skills/reflexes/policies
  - 6 enums, 4 dataclasses with strict __post_init__ validation
  - 41 new tests (21 bridge, 8 derivation, 12 invariants)
  - Golden Thread A extended with memory candidate + bridge report fields
  - memory_committed is structurally always False
  - **P1.5.19 P1.5 Integrated Seal (COMPLETE)**:
  - Seals the entire P1.5 subsystem — proves coherence, trace-binding, evidence-binding, limitation-binding, candidate-safety, and non-promotional guarantees
  - 4 new contracts: P15IntegratedSealReport, GoldenThreadASealReport, ContractInvariantChecklist (18 invariants), ColdCacheVerificationReport
  - 1 seal runner: run_p15_integrated_seal()
  - 41 new tests: full seal, trace integrity, candidate boundaries, anti-overclaim, no-promotion, verification gate
  - Golden Thread A produces seal reports after P1.5.18 memory bridge
  - All 18 hard invariants pass; cold-cache verification required; no hidden promotions
  - P1.5 sealed — next is P1.6.0 Policy Cards & Behavioral Contracts
  - **P1.6.0 Policy Card Foundation (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/` — first-class policy card foundation module
  - 3 enums: `PolicyCardKind` (10 kinds), `PolicyCardStatus` (5 statuses), `PolicyCardScopeType` (10 scope types)
  - 8 frozen dataclasses: `PolicyCard`, `PolicyCardIdentity`, `PolicyCardScope`, `PolicyCardRiskBinding`, `PolicyCardAuthorityBinding`, `PolicyCardSource`, `PolicyCardValidationIssue`, `PolicyCardValidationResult`
  - Closed-world validation: unknown top-level fields fail, dangerous metadata keys fail
  - Deterministic canonical serialization (sorted keys, compact JSON)
  - SHA-256 canonical hash readiness
  - Error taxonomy: 6 error classes (`PolicyCardError`, `PolicyCardValidationError`, etc.)
  - `load_policy_card_from_dict()` dict loader
  - 59 tests; no runtime resolver, conflict detector, CLI, or P25 hardening
  - Policy cards are foundation only — no enforcement yet
  - **P1.6.1 Policy Card Schema (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/schema.py` — centralized schema v1 contract
  - `schema_version` added to `PolicyCard` (required, must be "1.0")
  - Centralized field classifications: required/optional/forbidden/canonical/control/governance/source/descriptive/identity/runtime-future
  - Expanded dangerous field set (25 top-level + 31 metadata keys from 18 + 21 in P1.6.0)
  - Deterministic `export_policy_card_schema()` and helpers
  - Validation refactored to use schema definitions (no scattered inline lists)
  - Runtime-future reserved fields rejected (resolver, enforcement, conditions, etc.)
  - 61 new tests (120 total policy card tests); no resolver/enforcement/CLI yet
  - **P1.6.2 Behavioral Contract Schema (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/contracts.py` — 24 enums + 15 frozen dataclasses for behavioral contracts
  - `src/agentic_runtime/policy_cards/contract_schema.py` — centralized Behavioral Contract Schema v1
  - BehavioralContract models: identity, subject, scope, obligations, prohibitions, preconditions, postconditions, evidence requirements, escalation rules
  - Behavioral contracts can reference policy card IDs via `policy_card_refs`
  - Closed-world validation, deterministic serialization, SHA-256 canonical hashing
  - Behavioral contract error hierarchy (6 classes) extending PolicyCardError
  - ~44 new public exports; 96 new tests
  - No runtime enforcement, no resolver, no CLI
  - **P1.6.3 Risk Tier Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/risk_tiers.py` - R0-R6 typed risk-tier model, validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/risk_tier_schema.py` - Risk Tier Policy Card Schema v1, required fields, dangerous metadata keys, default definitions, action-class mapping seeds
  - RiskTierPolicyCard exists and remains compatible with generic `PolicyCard(kind="risk_tier")`
  - Default R0-R6 tier definitions exist with reversibility, oversight, evidence expectations, and semantic default flags
  - R5 requires trace, evidence, approval, irreversible reversibility, and explicit Operator confirmation
  - R6 is denied/non-permissive and cannot allow execution, external egress, memory write, or tool write
  - Reversible and compensatable remain distinct
  - Closed-world dict loading rejects unknown top-level/nested fields and dangerous metadata
  - Deterministic canonical serialization and SHA-256 canonical hash are available
  - 36 new focused tests; P1.6.0-P1.6.3 focused suite passes
  - No runtime risk classifier, no policy resolver, and no runtime enforcement yet
  - **P1.6.4 Human Oversight Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/human_oversight.py` - 5 enums (HumanOversightLevel/Mode/Trigger/Action, OversightEvidenceType), 7 frozen dataclasses (ConfirmationRequirement, ReviewerRequirement, OversightEvidenceRequirement, RiskTierOversightMapping, HumanOversightEscalationRule, HumanOversightPolicyCard), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/human_oversight_schema.py` - Human Oversight Policy Card Schema v1, required/optional/forbidden/canonical fields, dangerous metadata keys, default R0-R6 oversight mappings, default escalation rules
  - HumanOversightPolicyCard exists and remains compatible with generic `PolicyCard(kind="human_oversight")`
  - Default R0-R6 oversight mappings exist: R0-R1 none, R2 notify_only, R3 review_recommended, R4 approval_required, R5 explicit_confirmation_required (with strong confirmation and reviewer requirements), R6 deny
  - R4 must be approval_required or stricter; R5 must be explicit_confirmation_required with strong confirmation requirement; R6 must be deny and not approvable
  - Closed-world dict loading rejects unknown top-level/nested fields and dangerous metadata (auto_approve, operator_not_required, bypass_policy, etc.)
  - Deterministic canonical serialization and SHA-256 canonical hash are available
  - 68 new focused tests; P1.6.0-P1.6.4 focused suite passes (320 tests)
  - No runtime approval engine, no policy resolver, no enforcement, no CLI/report yet
  - **P1.6.5 Data Residency Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/data_residency.py` - 6 enums (DataResidencyZone 7 values, DataClass 20 values, ProcessingLocation 7 values, RedactionRequirementType 9 values, StorageRequirementType 6 values, DataExposurePermission 8 values), 8 frozen dataclasses (RedactionRequirement, StorageRequirement, DataEgressRule, DataExposureRule, DataResidencyRule, DataResidencyPolicyCard, DataResidencyValidationIssue, DataResidencyValidationResult), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/data_residency_schema.py` - Data Residency Policy Card Schema v1, 10 required data classes, 6 strict local-only data classes, required/optional/forbidden/canonical field tuples, sub-object field tuples, dangerous metadata keys (17), schema export functions
  - DataResidencyPolicyCard exists and remains compatible with generic `PolicyCard(kind="data_residency")`
  - Strict safety rules enforced at card validation: local_only zero-outbound (no egress/external-model/API/web), credentials no-egress + encryption + audit required, sensitive_personal_data/memory_record/trace_record local-only + no-egress, forbidden zone non-permissive
  - Default factory produces 20 data class rules with strict defaults: all classes local-only except public; credentials/sensitive_personal_data with redaction/storage/encryption requirements
  - Closed-world dict loading rejects unknown fields and dangerous metadata keys (allow_secret_egress, bypass_residency, skip_encryption, etc.)
  - Deterministic canonical serialization (sorted key stable) and SHA-256 hash
  - 48 new focused tests; P1.6.0-P1.6.5 focused suite passes (368 tests)
  - No runtime egress enforcement, model routing, data classification, redaction/encryption execution, or conflict resolution yet
  - **P1.6.6 Tool Permission Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/tool_permissions.py` - 5 enums (ToolCategory 17 values, ToolPermissionType 26 values, ToolPermissionDecision 8 values, ToolScopeType 12 values, ToolMatchMode 5 values), 6 frozen dataclasses (ToolIdentityMatcher, ToolPermissionCondition, ToolPermissionRule, ToolPermissionPolicyCard, ToolPermissionValidationIssue, ToolPermissionValidationResult), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/tool_permission_schema.py` - Tool Permission Policy Card Schema v1, required/optional/forbidden/canonical field tuples, sub-object field tuples, dangerous metadata keys (17), dangerous/high-risk permission types, default deny categories, schema export functions
  - ToolPermissionPolicyCard exists and remains compatible with generic `PolicyCard(kind="tool_permission")`
  - Strict deny-by-default posture: default_decision must be deny, unknown categories must deny, credential access denied, shell command requires sandbox/approval, network/egress governed, execute/delete/config-write require governance
  - Data residency compatibility: protected data classes (credentials, operator_private, sensitive_personal_data, memory_record, trace_record, source_code) cannot be exposed through external tools
  - Default factory produces 18 rules: unknown deny, credential deny, shell sandbox, egress deny/governed, filesystem read/write/delete governed, memory read/write governed, model local-only, email explicit confirmation, artifact export governed, config write approved, network governed, browser governed, GitHub/database governed
  - Closed-world dict loading rejects unknown fields and dangerous metadata keys (allow_all_tools, bypass_tool_policy, shell_unrestricted, etc.)
  - Deterministic canonical serialization and SHA-256 hash
  - 38 new focused tests; P1.6.0-P1.6.6 focused suite passes (406 tests)
  - No Tool Gateway enforcement, registry resolver, sandbox execution, network blocking, filesystem/path enforcement, credential system, memory write enforcement, model routing, or runtime permission engine yet
  - **P1.6.7 Memory Write Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/memory_write.py` - 6 enums (MemoryZone 14 values, MemoryWriteType 18 values, MemoryWriteDecision 10 values, MemoryVerificationStatus 8 values, MemoryRetentionClass 6 values, MemoryWriteRequirementType 13 values), 5 frozen dataclasses (MemoryWriteRequirement, MemoryWriteRule, MemoryWritePolicyCard, MemoryWriteValidationIssue, MemoryWriteValidationResult), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/memory_write_schema.py` - Memory Write Policy Card Schema v1, required/optional/forbidden/canonical field tuples, sub-object field tuples, dangerous metadata keys (19), PROTECTED_MEMORY_ZONES, STRICT_MEMORY_DATA_CLASSES, DEFAULT_MEMORY_WRITE_RULES (14 rules), schema export functions
  - MemoryWritePolicyCard exists and remains compatible with generic `PolicyCard(kind="memory_write")`
  - Memory zone / write type / decision / verification status / retention class vocabulary exists
  - Conservative deny-by-default posture: default_decision must be deny/forbidden
  - No silent canonical memory writes: canon_memory cannot be plain allow and requires source/evidence/trace references + operator review + explicit confirmation + conflict check
  - Policy memory protection: policy_memory requires policy authority + source/evidence/trace + operator review or explicit confirmation
  - Verified skill memory requires evaluation result + verification + evidence/trace references
  - Skill candidate memory cannot be verified/canonized by default (candidate ≠ verified ≠ canon)
  - Operator profile protection: requires user consent or operator review + source/provenance, trace when durable
  - Credentials cannot become durable memory by default; sensitive_personal_data writes are strict (evidence + provenance + residency check + review)
  - Scratchpad ephemeral and working memory session-scoped writes permitted with low friction
  - Closed-world dict loading rejects unknown fields and dangerous metadata keys (auto_canonize, bypass_memory_policy, remember_everything, consent_not_required, store_credentials, etc.)
  - Deterministic canonical serialization (sorted key stable) and SHA-256 hash
  - 60 new focused tests; P1.6.0-P1.6.7 focused suite passes (466 tests)
  - No Mneme storage engine, memory writing, retrieval, ranking, consolidation, memory graph, canon promotion engine, skill promotion engine, Verification Court, operator consent workflow, memory conflict detector, policy runtime resolver, or runtime enforcement yet
  - **P1.6.8 Prompt Policy Card Model (COMPLETE)**:
  - `src/agentic_runtime/policy_cards/prompt_policy.py` - 7 enums (PromptSourceType 19 values, PromptTrustLevel 10 values, PromptRole 16 values, PromptPolicyDecision 10 values, PromptInjectionRisk 5 values, PromptInjectionPattern 15 values, PromptBoundaryRequirementType 14 values), 5 frozen dataclasses (PromptBoundaryRequirement, PromptInjectionSignal, PromptHandlingRule, PromptPolicyCard, PromptPolicyValidationIssue, PromptPolicyValidationResult), validation, loading, serialization, hashing, default factory
  - `src/agentic_runtime/policy_cards/prompt_policy_schema.py` - Prompt Policy Card Schema v1, required/optional/forbidden/canonical field tuples, sub-object field tuples, dangerous metadata keys (21), TRUSTED/UNTRUSTED/EXTERNAL/PROTECTED prompt source sets, DEFAULT_PROMPT_HANDLING_RULES (15 rules), schema export functions
  - PromptPolicyCard exists and remains compatible with generic `PolicyCard(kind="prompt")`
  - Prompt source / trust level / role / decision / injection-risk vocabulary exists
  - Strict deny-by-default posture: default_decision must be deny/forbidden
  - Core law enforced — untrusted content may inform but never command: unknown source cannot be trusted; external content (web/email/file/code/external_api/retrieved_document/tool_output/unknown) cannot be instruction authority; tool output is data/context, not command; retrieved memory is context, not automatic authority
  - Untrusted/external/tool-output/retrieved trust levels cannot request tools, write memory, modify policy, or modify identity
  - High/critical injection risk cannot pair with allow + instruction authority
  - Closed-world dict loading rejects unknown fields and dangerous metadata keys (bypass_prompt_policy, reveal_system_prompt, grant_tool_access, external_as_instruction, trust_unknown_source, etc.)
  - Deterministic canonical serialization (sorted key stable) and SHA-256 hash
  - 74 new focused tests; P1.6.0-P1.6.8 focused suite passes (540 tests)
  - No prompt compiler, prompt assembly engine, instruction-hierarchy runtime enforcement, prompt injection detector, jailbreak detector, tool-call runtime blocking, memory write enforcement, identity compiler change, policy resolver, or runtime enforcement yet
  - **P1.6.8S Repository Reality & Policy Card Stabilization Seal (COMPLETE)**:
  - Git/docs/test/lint reality reconciled after P1.6.8 and before P1.6.9
  - Legitimate P1.6.4-P1.6.8 policy-card source, test, and report artifacts identified for final staging
  - Bare-python CLI subprocess tests replaced with shared `tests/cli_helpers.py` helper using active interpreter and `PYTHONPATH=src:.`
  - Ruff, mypy, full pytest, and coverage validation pass locally
  - Accidental root pager/help artifact removed; `.composer/` left as unrelated local tool state
  - Deferred structural debt recorded for identity CLI splitting, shared policy-card base, mypy tightening, security scan gates, and slow-test marker hardening

## What works

- Full governed command pipeline: policy → HITL → budget → sandbox → verify → trace → memory
- ...
- P1.4.14 Operator Consent Binding: delta-bound consent with attestation binding, risk acknowledgement, 55 tests
- P1.4.15 Identity Governance Command Surface: unified CLI, `identity status`/`verify`, JSON envelope, 53 tests
- Plan validation halts on empty/invalid/unsupported plans
- Persistent and in-memory trace ledgers with hash-chain verification
- P1.5.10X canonical AurelTraceLog contracts:
  - `src/agentic_runtime/contracts/trace.py` defines append-only `AurelTraceLog`, immutable `TraceEvent`, `TraceEventRef`, `TraceBindingRef`, `TraceIntegrityReport`, stable canonical JSON hashing, and chain verification
  - `src/agentic_runtime/contracts/projections.py` defines projection records that cannot claim canonical status
  - AurelTraceLog is the only source of truth; Ledger/Evidence/Runtime/Evaluation/Mneme/Shell/Reports are projections
  - Future serious evidence/evaluation/memory/output records must bind back to canonical `TraceEventRef`
- P1.5.11A Golden Thread A:
  - `src/agentic_runtime/golden_threads/thread_a.py` runs deterministic Intent → Context → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → CapabilityEvidence path
  - `src/agentic_runtime/contracts/evidence.py` defines trace-bound `EvidenceRef`
  - `src/agentic_runtime/contracts/verifier.py` defines `VerifierResult` with pass/evidence/limitations invariants
  - `src/agentic_runtime/contracts/capability.py` defines verified capability evidence factory and validation
  - Verified capability evidence cannot exist without canonical trace, evidence, verifier pass, verifier limitations, and capability limitations
- P1.5.11B Capability Evidence ↔ Trace / Context Binding:
  - `src/agentic_runtime/contracts/context.py` defines `ContextBindingRef`, `ContextAdequacyStatus`, and `ContextAdequacyReport`
  - `CapabilityEvidenceRecord` now stores `source_event_hash`, context refs, context adequacy ref, and evidence strength
  - Golden Thread A now includes ContextBindingRef and ContextAdequacyReport
  - Verified capability evidence requires trace, source hash, evidence, verifier pass, limitations, evidence strength `strong|verified`, and safe/adequate context
  - Unsafe/insufficient context, weak evidence, projection-only sources, and trace-hash mismatch block verification
- P1.5.12 Evaluation Case Extraction Seed:
  - `src/agentic_runtime/contracts/evaluation_cases.py` defines `FailureMode`, `EvaluationCase`, `RegressionCandidate`, `EvaluationCaseExtractionReport`
  - `src/agentic_runtime/evaluation/extraction.py` implements extraction from `CapabilityEvidenceRecord` → `EvaluationCase`/`RegressionCandidate`
  - Golden Thread A now produces a candidate `EvaluationCase`; `GoldenThreadAResult` extended with extraction fields
  - Extraction routing: review > regression > positive
  - All extracted records are candidate/needs_review by default — nothing is auto-accepted
  - Impossible states (positive case without trace, without evidence, with mismatched hash, with accepted status, etc.) are blocked by invariant validation
  - 46 tests across extraction, golden thread integration, serialization, failure mode mapping, and candidate-only guards
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
- P1.1 Model Configuration + Secret Boundary (**PASS**):
  - centralized config: `agent/config/{providers,models,runtime}.yaml`
  - `model_config.py`, `secrets.py`, `yaml_minimal.py`
  - `ModelRouter` accepts `ModelConfigBundle`, profile/task selection, `local_only` enforcement
  - secrets from env only; `SecretRedactor` on errors/status; raw API keys rejected in YAML
  - CLI: `config validate`, `models list`, `providers status`
  - tests: `tests/test_model_config_p11.py` (21 tests)
- P1.2.1 Public Entry + Runtime Verification Patch (**PASS**):
  - `demo.py` crash fixed: safe no-skill outcome when evidence gates not satisfied, exits 0
  - sandbox CPU/timeout mismatch fixed: `materialize_sandbox_backend` passes `cpu_seconds` from profile
  - `model_router.py` ruff/mypy noise cleaned: `ModelResponse` module import, `rows` rename, 3 unused ignores removed
  - `tests/test_public_entrypoints_p121.py` added (8 smoke tests)
  - README quick-start updated to accurately describe demo outcome
  - `slow` marker registered in `pyproject.toml`
- P1.2 Prompt System Seed (**PASS**):
  - top-level prompt assets under `prompts/system/` and `prompts/packs/`
  - `prompt_system.py` with `PromptRegistry`, metadata/policy validation, simple template rendering, and trace-safe `PromptTraceSummary`
  - prompt manifests declare owner, version, allowed model profiles, task tags, schemas, forbidden requests, evals, policy, and template
  - P1.1 model profile validation is optional and enabled by prompt CLI default validation
  - raw prompt text is not stored by default; CLI render emits hashes and metadata only
  - `SecretRedactor` applied to prompt summaries and CLI output; raw secret-like prompt material is rejected
  - CLI: `prompts validate`, `prompts list`, `prompts show`, `prompts render`
  - tests: `tests/test_prompt_system_p12.py` (26 tests)
- P1.3 Tool / Plugin Manifest Seed (**SEALED** via P1.3.9):
  - declarative manifest layer under `src/agentic_runtime/tool_manifest/`
  - lifecycle: load → validate → quarantine → register → invocation draft → lifecycle event
  - built-in seed manifests (7 tools across 6 JSON files)
  - research-inspired metadata (AWM/JEPA/LaMo/simulation/learning readiness fields)
  - **not** wired to Tool Bus, `CommandEnvelope`, or `runtime.submit`
  - tests: `tests/test_tool_manifest_p130.py` … `tests/test_builtin_tool_manifests_p138.py`, `tests/test_p13_tool_manifest_layer_seal.py` (58 seal tests)
- P1.3.9 Tool Manifest Layer Seal (**SEALED** — 2026-06-21):
  - end-to-end lifecycle seal without execution
  - declarative-vs-executable boundary tests (manifest `ToolRegistry` ≠ `tools.py` `ToolRegistry`)
  - governance hotfix confirmation (prompt risk_tier, YAML, restricted_local honesty, run_shell R4)
  - report: `agent/reports/P1.3_TOOL_PLUGIN_MANIFEST_REPORT.md`
- P1.4.0 Identity + Autonomy Scope Contract (**PASS**):
  - constitutional docs under `docs/P1.4_*.md`
  - stub packages: `identity/`, `autonomy/`, `governance/`, `heretic/`, `metacognition/`, `compliance/` (placeholders only)
  - static scope constants: `identity/p14_scope.py`
  - **not** Identity Kernel, Autonomy Scale, Measured Autonomy Score, or Heretic Sandbox runtime
  - tests: `tests/test_p14_scope_contract_docs.py`
  - report: `agent/reports/P1.4.0_IDENTITY_AUTONOMY_SCOPE_CONTRACT_REPORT.md`
- P1.4.1 Identity Kernel v2.0 (**PASS**):
  - `config/aurel/identity_kernel.yaml` with IK-001–IK-008 invariant registry
  - loader, validator, SHA-256 hash, attestation builder
  - CLI: `identity kernel {show,validate,hash,attest}`
  - **not** Persona Manifest, Operator Contract, Autonomy Scale, or Identity Card
  - tests: `tests/test_identity_kernel*.py` (27 tests)
  - report: `agent/reports/P1.4.1_IDENTITY_KERNEL_REPORT.md`
- P1.4.2 Persona Manifest v2.0 (**PASS**):
  - `config/aurel/persona_manifest.yaml` expression contract with PM-001–PM-007 invariants
  - loader, validator, SHA-256 hash, attestation, deterministic safe summary
  - CLI: `identity persona {show,validate,hash,attest,summary}`
  - **not** Operator Contract, Communication Modes, Prompt Context Compiler, or Autonomy
  - tests: `tests/test_persona_manifest*.py` (36 tests)
  - report: `agent/reports/P1.4.2_PERSONA_MANIFEST_REPORT.md`
- P1.4.3 Operator Relationship Contract v2.0 (**PASS**):
  - `config/aurel/operator_contract.yaml` — principal/delegate authority, ORC-001–ORC-008 invariants
  - loader, validator, SHA-256 hash, authority anchor, prompt-safe summary
  - CLI: `identity operator {show,validate,hash,attest,summary}`
  - tests: `tests/test_operator_contract*.py` (57 tests)
  - report: `agent/reports/P1.4.3_OPERATOR_RELATIONSHIP_CONTRACT_REPORT.md`
- P1.4.4 Communication Modes v2.0 (**PASS**):
  - `config/aurel/communication_modes.yaml` — cognitive/output mode registry, CM-001–CM-008 invariants
  - loader, validator, SHA-256 hash, case-insensitive lookup, per-mode safe summaries
  - CLI: `identity modes {show,validate,hash,attest,summary}`
  - tests: `tests/test_communication_modes*.py` (34 tests)
  - report: `agent/reports/P1.4.4_COMMUNICATION_MODES_REPORT.md`
- P1.4.5 Identity Prompt Context Compiler v2.0 (**PASS**):
  - `config/aurel/identity_prompt_compiler.yaml` — compile identity sources into prompt context
  - dominance rules, contradiction detection, deterministic SHA-256 context hash
  - CLI: `identity context {show,validate,hash,compile,render}`
  - tests: `tests/test_identity_prompt_context*.py` (55 tests)
  - report: `agent/reports/P1.4.5_IDENTITY_PROMPT_CONTEXT_COMPILER_REPORT.md`
- P1.4.6 Self-Model v2.0 (**PASS**):
  - `config/aurel/self_model_policy.yaml` — honest runtime self-description
  - identity summary, authority boundaries, capability-honest inventory, known limitations
  - CLI: `identity self {show,validate,hash,build}`
  - tests: `tests/test_self_model*.py` (48 tests)
  - report: `agent/reports/P1.4.6_SELF_MODEL_REPORT.md`
- P1.4.18 Trust Evidence Linkage (**COMPLETE** ✓):
  - `src/agentic_runtime/identity/trust_evidence.py` — trust evidence linkage layer operational
  - `TrustEvidenceKind`, `TrustEvidenceStatus`, `TrustPosture`, `TrustEvidenceRef`, `TrustEvidenceRequirement`, `TrustEvidenceLink`, `TrustEvidenceBundle`, `TrustEvidenceLinkageReport`
  - categorical trust posture resolution working (no fake numeric trust score)
  - engine: `default_trust_evidence_requirements_for_lifecycle()`, `build_trust_evidence_bundle()`, `validate_trust_evidence_bundle()`, `resolve_trust_posture()`
  - 5 helper builders: `evidence_ref_from_source_attestation`, `from_test_battery_report`, `from_consent_record`, `from_authority_delta_report`, `from_lifecycle_decision`
  - CLI: `identity trust-evidence {requirements,build,validate,explain}`
  - tests: 57 new (34 core + 23 seal/CLI), 355 identity total
  - reports: `agent/reports/P1.4.18_TRUST_EVIDENCE_LINKAGE.md`
- P1.4.19 Identity Docs / Reports / State Update (**COMPLETE** ✓):
  - consolidation/audit gate before P1.4.20 exit seal; no new governance semantics
  - `src/agentic_runtime/identity/p14_seal_readiness.py` — read-only seal readiness helper
  - data models: `P14ModuleStatus`, `P14SealReadinessReport`
  - pre-built constants: `P14_CLI_GROUPS` (18 entries), `P14_INVARIANTS` (15), `P1419_INVARIANTS` (10), `P14_KNOWN_LIMITATIONS` (15), `P1420_SEAL_CHECKLIST` (22)
  - CLI: `identity seal-readiness --json`
  - tests: 29 new anti-overclaim + seal-readiness tests (`test_p1419_anti_overclaim.py`), 384 identity total
  - report: `agent/reports/P1.4.19_IDENTITY_DOCS_REPORTS_STATE_UPDATE.md`
  - P1.4.18 verified complete before implementation
  - **Current active module: P1.4.20**
  - **Next module: P1.5.0 — Evaluation Mirror Foundation**
- P1.4.20 P1.4 Identity & Autonomy Exit Seal (**COMPLETE** ✓, SEALED_WITH_LIMITATIONS):
  - `src/agentic_runtime/identity/p14_exit_seal.py` — final P1.4 boundary seal, validates, does not add governance
  - 56 seal checks across 5 categories: import/object, CLI, governance invariants, adversarial, docs consistency
  - CLI: `identity p14-seal run/list-checks/run-check --json` — read-only, no mutation, no authority grant, no consent grant
  - Tests: 28 new (`test_p14_exit_seal.py`), 412 identity total
  - Seal result: **SEALED_WITH_LIMITATIONS** — honest; P1.5/P1.6/P1.8/P6/P7 not yet implemented
  - 15 known limitations carried forward from P1.4.19
  - Report: `agent/reports/P1.4.20_P14_IDENTITY_AUTONOMY_EXIT_SEAL.md`
  - P1.4.19 verified complete before implementation
  - **P1.4 is sealed. P1.5.0 Evaluation Mirror Foundation Gate is next.**
- P1.5.0 Evaluation Mirror Foundation Gate + Roadmap v3.2 Alignment (**COMPLETE**):
  - **Current phase:** P1.5 — Evaluation Mirror & Verified Capability Evidence Foundation
  - **Macro roadmap version:** Aurel Roadmap v3.2 (based on v3.1 macro update — refined, not reset)
  - `src/agentic_runtime/evaluation/evaluation_foundation.py` — minimal evaluation foundation
  - data models: `EvaluationDomain`, `EvaluationSubjectType`, `EvaluationSubject`, `EvaluationScope`, `EvaluationCriterion`, `EvaluationRunEnvelope`, `EvaluationFoundationReport`
  - engine: `default_evaluation_scope_for_domain()`, `build_evaluation_subject()`, `build_evaluation_run_envelope()`, `validate_evaluation_run_envelope()`, `build_p150_foundation_report()`
  - CLI: `evaluation foundation status/scope --json` — read-only, does not verify capability
  - Core law: No capability claim may become VERIFIED without evaluation evidence
  - P1.5.0 is foundation gate, **not** full P4 Evaluation Mirror
  - Roadmap v3.2 alignment: Aurel Core vs Hub tools, HQ/A-Hub/S-Hub/L-Hub/IDE taxonomy, memory boundaries, open-weight model doctrine
  - **Execution discipline:** Do not jump to P22–P24. Finish P1.5–P1.9, then lock P2.0, then continue P3+.
  - P1.4.20 verified complete (SEALED_WITH_LIMITATIONS) before implementation
  - Historical P1.5.0 pointer superseded; later P1.5 modules advanced through P1.5.19 and current work is P1.6.8S.
- P1.5.10 Baseline Comparison Model + Sparse Comparison Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/baseline_comparison.py` — baseline comparison model
  - enums: `BaselineReferenceKind`, `BaselineStatus`, `ComparisonDimension`, `ComparisonSignal`, `ComparisonConfidence`
  - dataclasses: `BaselineReference`, `BaselineComparisonInput`, `BaselineComparisonDecision`, `BaselineComparisonPolicy`, `BaselineComparisonReport`
  - engine: `validate_baseline_reference()`, `validate_baseline_comparison_input()`, `compare_evaluation_results()`, `compare_adversarial_coverage()`, `compare_hygiene_refs()`, `resolve_baseline_comparison_decision()`, `build_p1510_baseline_comparison_report()`
  - CLI: `evaluation baseline status/examples --json` — read-only, does not run evaluations or verify capability
  - Core law: baseline comparison may detect improvement or degradation; comparison is not verification
  - Sparse comparison readiness: 8 sparse dimensions supported categorically; Sparse Context Compiler NOT implemented
  - 13 invariants (`P1510_INVARIANTS`) including 3 sparse-specific
  - P1.5.9 verified complete before implementation
- P1.5.10X Single Source of Truth + TraceLog Integrity Patch (**COMPLETE**):
  - `src/agentic_runtime/contracts/trace.py` — canonical trace contracts and append-only in-memory `AurelTraceLog`
  - `TraceEvent` includes hash-chain fields, payload hash, event hash, refs, policy/context/verifier refs, severity and status
  - `TraceEventRef`, `TraceBindingRef`, and `TraceIntegrityReport` provide future evidence/evaluation/memory/output binding and replay integrity primitives
  - `src/agentic_runtime/contracts/projections.py` — projection contract layer for ledger, runtime, evaluation, memory, shell, report and evidence projections
  - Core law: AurelTraceLog is the only source of truth; Ledger/Evidence/Runtime/Evaluation/Mneme/Shell/Reports are projections
  - No full AurelFlow, AurelExec, tool execution, shell execution, LLM execution, full Ledger rewrite, or full Mneme lifecycle introduced
  - ADR: `docs/adr/ADR-004-aurel-tracelog-source-of-truth.md`
  - Report: `docs/roadmap/P1.5.10X_TRACELOG_INTEGRITY_PATCH.md`
  - Next module: P1.5.11A — Golden Thread A Minimal Contract Harness
- P1.5.11A Golden Thread A Minimal Contract Harness (**COMPLETE**):
  - `src/agentic_runtime/golden_threads/thread_a.py` — deterministic vertical contract harness
  - stubs: `OperatorIntentStub`, `AurelContextStub`, `PolicyDecisionStub`, `LeaseStub`, `StubExecutionResult`
  - result: `GoldenThreadAResult`
  - contracts: `EvidenceRef`, `VerifierResult`, P1.5.11A `CapabilityEvidenceRecord`
  - canonical event: `TraceEventType.STUB_EXECUTION_COMPLETED` appended to `AurelTraceLog`
  - Golden Thread A path: Intent → Context → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → CapabilityEvidence
  - Core law: verified capability evidence requires canonical `TraceEventRef`, at least one `EvidenceRef`, linked `VerifierResult`, verifier status `pass`, non-empty verifier limitations, and non-empty capability limitations
  - No full AurelFlow, AurelExec, real tool/model/shell execution, full Ledger migration, or full Mneme lifecycle introduced
  - Report: `docs/roadmap/P1.5.11A_GOLDEN_THREAD_A_MINIMAL_CONTRACT_HARNESS.md`
  - Next module: P1.5.11B — Capability Evidence ↔ Trace / Context Binding
- P1.5.11B Capability Evidence ↔ Trace / Context Binding (**COMPLETE**):
  - `src/agentic_runtime/contracts/context.py` — context binding and adequacy contracts
  - `src/agentic_runtime/contracts/capability.py` — capability evidence v2 with source event hash, context binding, context adequacy ref, and evidence strength
  - `src/agentic_runtime/golden_threads/thread_a.py` — updated Golden Thread A path: Intent → ContextBindingRef → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → ContextAdequacyReport → CapabilityEvidenceRecord v2
  - Core law: verified capability evidence requires canonical trace, matching source_event_hash, EvidenceRef, VerifierResult pass, verifier limitations, capability limitations, evidence strength `strong|verified`, and no unsafe/insufficient context
  - Partial context requires explicit context limitation
  - Projection-only source cannot verify capability evidence
  - No full AurelBrain, AurelContextPacket, AurelFlow, AurelExec, tool/model/shell execution, full Ledger migration, full Mneme lifecycle, CapabilityClaimRegistry, or EvaluationCase extraction introduced
  - Report: `docs/roadmap/P1.5.11B_CAPABILITY_EVIDENCE_TRACE_CONTEXT_BINDING.md`
  - Historical next module was P1.5.12; current work is P1.6.8S and next planned feature is P1.6.9.
- P1.5.9 Adversarial Evaluation Cases + Sparse Trap Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/adversarial_cases.py` — adversarial case definitions and registry
  - enums: `AdversarialCaseType`, `AdversarialCaseStatus`, `AdversarialCaseSeverity`, `AdversarialAttackSurface`, `AdversarialExpectedOutcome`
  - dataclasses: `AdversarialEvaluationCase`, `AdversarialCaseRegistry`, `AdversarialCaseValidation`, `AdversarialCaseReport`
  - engine: `validate_adversarial_case()`, `register_adversarial_case()`, `validate_adversarial_case_registry()`, `resolve_adversarial_cases_for_subject()`, `list_adversarial_cases()`, `build_default_adversarial_case_set()`, `build_p159_adversarial_case_report()`
  - CLI: `evaluation adversarial status/examples --json` — read-only, does not execute cases or verify capability
  - Core law: Aurel cannot trust only positive/pass cases; adversarial cases are first-class evaluation fixtures
  - Sparse trap readiness: omission, lost-context, multi-hop, contradiction survival, needle-in-context, context budget pressure traps represented; Sparse Context Compiler NOT implemented
  - 17 invariants (`P159_INVARIANTS`) including 6 sparse-specific
  - P1.5.8 verified complete before implementation
- P1.5.8 Benchmark Hygiene Guard + Sparse Hygiene Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/benchmark_hygiene.py` — benchmark/context hygiene guard
  - enums: `BenchmarkHygieneStatus`, `BenchmarkHygieneRisk`, `BenchmarkContaminationType`, `BenchmarkFreshnessStatus`, `BenchmarkRepresentativeness`
  - dataclasses: `BenchmarkFixtureBoundary`, `BenchmarkHygieneAssessment`, `BenchmarkHygienePolicy`, `BenchmarkHygieneDecision`, `BenchmarkHygieneReport`
  - engine: `validate_benchmark_fixture_boundary()`, `classify_contamination_risk()`, `classify_freshness_status()`, `assess_benchmark_hygiene()`, `resolve_hygiene_decision()`, `apply_hygiene_to_evidence_binding()`
  - CLI: `evaluation hygiene status/examples --json` — read-only, does not run benchmarks or verify capability
  - Core law: benchmark-derived evidence cannot strongly support a claim unless hygiene is acceptable
  - Sparse hygiene readiness: context leakage, retrieval leakage, lost-context risk, contradiction omission, and multi-hop edge missing represented as hygiene risks; Sparse Context Compiler NOT implemented
  - 17 invariants (`P158_INVARIANTS`) including 6 sparse-specific
  - P1.5.7 verified complete before implementation
- P1.5.7 Evidence-to-Claim Binding + Sparse Binding Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evidence_claim_binding.py` — evidence-to-claim binding layer
  - enums: `ClaimBindingRelationship` (8 types), `ClaimBindingStatus` (9 statuses), `ClaimSupportLevel` (5 levels), `ClaimConflictLevel` (6 levels)
  - dataclasses: `EvidenceClaimBinding`, `EvidenceClaimBindingPolicy`, `EvidenceClaimBindingDecision`, `EvidenceClaimBindingReport`
  - engine: `bind_evidence_to_claim()`, `validate_evidence_claim_binding()`, `aggregate_evidence_claim_bindings()`, `build_p157_evidence_claim_binding_report()`
  - CLI: `evaluation binding status/examples --json` — read-only, does not verify capability
  - Core law: Evidence can affect a claim, does not automatically verify it; no VERIFIED status
  - Sparse binding readiness: sparse-context evidence binds to sparse-related claims; Sparse Context Compiler NOT implemented
  - 13 invariants (`P157_INVARIANTS`) including 3 sparse-specific
  - P1.5.6 verified complete before implementation
- P1.5.6 Result Classification Engine + Sparse Classification Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/result_classification.py` — result classification engine
  - enums: `EvaluationObservationType` (18 types), `EvaluationObservationStatus` (7 statuses)
  - dataclasses: `EvaluationObservation`, `CriterionClassificationInput`, `CriterionClassificationDecision`, `ResultClassificationInput`, `ResultClassificationDecision`, `ResultClassificationPolicy`, `ResultClassificationReport`
  - engine: `validate_evaluation_observation()`, `classify_criterion_observation()`, `criterion_decision_to_result()`, `classify_result_from_criterion_decisions()`, `result_classification_to_evaluation_result()`, `classify_result_from_observations()`, `build_p156_result_classification_report()`
  - CLI: `evaluation classify status/examples --json` — read-only, does not execute evaluation
  - Core law: Classification is not verification; classification does not execute evaluation, call LLMs/tools, verify capability, or bind evidence to claims
  - Sparse classification readiness: 7 sparse observation types classifiable; Sparse Context Compiler NOT implemented
  - Conversion to P1.5.1 EvaluationCriterionResult and EvaluationResult objects
  - 17 invariants (`P156_INVARIANTS`)
  - P1.5.5 verified complete before implementation
- P1.5.5 Evaluation Run Envelope + Sparse Run Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evaluation_run_envelope.py` — governed run envelope layer
  - enums: `EvaluationRunStatus`, `EvaluationRunIntent`, `EvaluationRunMode`, `EvaluationEvaluatorType`
  - dataclasses: `EvaluationRunEvidenceRequirement`, `GovernedEvaluationRunEnvelope`, `EvaluationRunEnvelopeValidation`, `EvaluationRunEnvelopeReport`
  - engine: `build_governed_evaluation_run_envelope()`, `validate_governed_evaluation_run_envelope()`, `resolve_run_readiness()`, `build_evidence_requirements_from_criteria()`, `build_p155_run_envelope_report()`
  - CLI: `evaluation runs status/examples --json` — read-only, does not execute evaluation
  - Core law: No governed evaluation execution without a valid run envelope; envelopes do not run evaluation
  - Sparse run metadata: 5 boolean fields derived from criteria; ASCL not implemented
  - 13 invariants (`P155_INVARIANTS`)
  - P1.5.4 verified complete before implementation
- P1.5.4 Evaluation Criteria Schema + Sparse Criteria Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evaluation_criteria_schema.py` — reusable criteria schema layer
  - enums: `EvaluationCriterionKind`, `EvaluationCriterionSeverity`, `EvaluationCriterionRequirementLevel`, `EvaluationCriterionEvidenceRequirement`
  - dataclasses: `EvaluationCriterionApplicability`, `EvaluationCriteriaSchemaItem`, `EvaluationCriteriaSchema`, `EvaluationCriteriaSchemaRegistry`, `EvaluationCriteriaSchemaResolution`, `EvaluationCriteriaSchemaReport`
  - engine: `validate_criteria_schema_item()`, `resolve_criteria_for_subject()`, `list_criteria_schemas()`, `build_default_criteria_schema_for_subject_type()`, `build_default_sparse_criteria_schema()`, `build_p154_criteria_schema_report()`
  - CLI: `evaluation criteria status/examples --json` — read-only, does not run evaluation
  - Core law: No criteria schema, no governed evaluation run; criteria do not verify capability
  - Sparse criteria: 8 sparse criterion kinds, 6-criteria default sparse schema; Sparse Context Compiler NOT implemented
  - 15 invariants (`P154_INVARIANTS`)
  - P1.5.3 verified complete before implementation
- P1.5.3 Evaluation Subject Registry + Sparse Cognition Readiness (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evaluation_subject_registry.py` — governed subject registry
  - enums: `EvaluationSubjectStatus`, `EvaluationSubjectOrigin`, `EvaluationSubjectCategory`
  - dataclasses: `EvaluationSubjectRegistryEntry`, `EvaluationSubjectRegistrationRequest`, `EvaluationSubjectRegistrationDecision`, `EvaluationSubjectRegistry`, `EvaluationSubjectRegistryReport`
  - engine: `register_evaluation_subject()`, `resolve_evaluation_subject()`, `list_evaluation_subjects()`, `validate_evaluation_subject_registry()`, `build_p153_subject_registry_report()`
  - CLI: `evaluation subjects status/examples --json` — read-only, does not run evaluation
  - Core law: No registered subject, no governed evaluation; registration is not verification
  - Sparse Cognition readiness: 9 future ASCL categories registerable; Sparse Context Compiler NOT implemented
  - Hub origins: A_HUB/S_HUB/L_HUB/IDE registrable as future-ready references; Hub runtimes NOT implemented
  - 16 invariants (`P153_INVARIANTS`)
  - P1.5.2 verified complete before implementation
- P1.5.2 Capability Evidence Record (**COMPLETE**):
  - `src/agentic_runtime/evaluation/capability_evidence.py` — evidence bridge layer
  - enums: `CapabilityEvidenceKind`, `CapabilityEvidenceStatus`, `CapabilityEvidenceStrength`
  - dataclasses: `CapabilityEvidenceRecord`, `CapabilityEvidenceRequirement`, `CapabilityEvidenceLink`, `CapabilityEvidenceRecordSet`, `CapabilityEvidenceRecordReport`
  - engine: `capability_evidence_from_evaluation_result()`, `capability_evidence_from_result_set()`, `validate_capability_evidence_record()`, `aggregate_capability_evidence_records()`, `build_capability_evidence_link()`, `build_p152_capability_evidence_report()`
  - CLI: `evaluation capability-evidence status/examples --json` — read-only, does not verify capability
  - Core law: USABLE is not VERIFIED; evidence records support future claim binding (P1.5.7)
  - 11 invariants (`P152_INVARIANTS`)
  - P1.5.1 verified complete before implementation
- P1.5.1 Evaluation Object Model (**COMPLETE**):
  - `src/agentic_runtime/evaluation/evaluation_objects.py` — stable evaluation result language
  - enums: `EvaluationResultStatus`, `EvaluationOutcome`, `EvaluationVerdict`, `EvaluationConfidenceClass`, `EvaluationEvidenceQuality`, `EvaluationFailureMode`
  - dataclasses: `EvaluationCriterionResult`, `EvaluationResult`, `EvaluationResultSet`, `EvaluationObjectModelReport`
  - engine: `validate_evaluation_criterion_result()`, `validate_evaluation_result()`, `resolve_evaluation_result_from_criteria()`, `aggregate_evaluation_results()`, `build_p151_object_model_report()`
  - CLI: `evaluation objects status/examples --json` — read-only, does not verify capability
  - Core law: PASS does not mean VERIFIED; no numeric capability score
  - 11 invariants (`P151_INVARIANTS`)
  - P1.5.0 verified complete before implementation

## Known limitations

- Default sandbox is `UnsafeLocalSandbox` — **not** a production security boundary
- Real providers are optional and unverified without API keys/local services
- Single-entity demo; no multi-agent orchestration
- HITL uses `AutoApprover` in demo (bounded predicate, defaults deny)
- Tool Bus does not make authority decisions; Runtime policy remains mandatory
- No network, delete, git commit, or git push tools are implemented
- Prompt manifests are governance metadata and language templates only; prompts do not grant tool authority
- Two `ToolRegistry` types exist: manifest catalog (`tool_manifest/registry.py`) vs executable Tool Bus registry (`tools.py`) — not merged in P1.3
- Tool manifest invocation drafts do not become `CommandEnvelope`; future bridge planned at P6 Governed Tool Bus Expansion
- P1.4.1–P1.4.19 identity trust surface is implemented (kernel through seal readiness) but **not wired into `AgenticRuntime.submit()`** — delta detection, consent binding, trust posture, and seal readiness are CLI/report signals only until a later patch explicitly adds runtime enforcement
- P1.4.0 placeholder packages (`autonomy/`, `governance/`, `heretic/`, `metacognition/`, `compliance/`) remain stubs; substantive logic lives under `identity/` for delivered patches
- Repository agent patch synthesis remains intentionally small/deterministic; LLM planning proposes structured plans only and is not a general autonomous coding agent
- Repository-agent context building reads bounded local files directly, while
  mutations and test execution go through Runtime/Tool Bus governance
- One pytest (`test_timeout_kills_long_running_command`) may fail in restricted CI sandboxes when nested `python3` subprocesses are blocked; passes in normal environments — **P1.0:** both timeout tests skip automatically via `requires_subprocess` when subprocess spawn is blocked
- CLI `demo-harness --apply` with auto bubblewrap may report harness `failed` while independent `final_test` passes; use `--sandbox restricted_local` for scenario-default smoke or see P1.0 seal report

## P1.4.19 Known Limitations Index

P1.4.19 catalogued 15 known limitations (`P14_KNOWN_LIMITATIONS`) for P1.4.20 exit seal verification:

1. Identity trust surface (kernel through seal readiness) not wired into `AgenticRuntime.submit()`
2. P1.4.0 placeholder packages (`autonomy/`, `governance/`, `heretic/`, `metacognition/`, `compliance/`) remain stubs
3. Authority delta detection / consent binding are CLI/report signals only
4. Trust evidence linkage is classification-only, not runtime enforcement
5. P1.4 seal-readiness is read-only; no authority, permission, or tool changes
6. No cryptographic signatures on attestations (SHA-256 only)
7. No tamper-proof storage for identity sources or attestations
8. Capability claims are evidence-gated but not runtime-enforced
9. Autonomy scale engine is action-scoped only, not wired to runtime
10. Measured autonomy score is measurement-only, not an execution gate
11. Lifecycle state machine is eligibility-only, not permission enforcement
12. Identity test battery is verification-only, not continuous monitoring
13. External doctrine assimilation is roadmap influence only, not implementation
14. Two `ToolRegistry` types remain separate (manifest catalog vs execution registry)
15. Default sandbox is `UnsafeLocalSandbox` — not a production security boundary

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
python -m agentic_runtime.cli config validate
python -m agentic_runtime.cli models list
python -m agentic_runtime.cli providers status
python -m agentic_runtime.cli prompts validate
python -m agentic_runtime.cli prompts list
python -m agentic_runtime.cli prompts show repo_planner
python -m agentic_runtime.cli prompts render repo_planner --var objective="test" --dry-run
python -m agentic_runtime.cli identity trust-evidence requirements --lifecycle-state ACTIVE --json
python -m agentic_runtime.cli identity trust-evidence build --lifecycle-state ACTIVE --json
python -m agentic_runtime.cli identity trust-evidence validate --json
python -m agentic_runtime.cli identity trust-evidence explain --json
python -m agentic_runtime.cli identity seal-readiness --json
python -m agentic_runtime.cli identity p14-seal run --json
python -m agentic_runtime.cli identity p14-seal list-checks --json
python -m agentic_runtime.cli identity p14-seal run-check import_objects --json
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



## P1.4.12 - Raw Source + Canonical Hash Attestation (2026-06-21)

- P1.4.12: hash-based source attestation - `source_attestation.py`, `source_bundle.py`, identity attestation CLI
- source model: `SourceKind`, `SourceValidationStatus`, `SourceHashPair`, `SourceAttestation`
- raw source hash is computed from unnormalized raw bytes/text; canonical typed hash is computed from deterministic typed JSON
- identity bundle now carries attestations for identity kernel, persona manifest, operator contract, communication modes, identity prompt compiler, self-model policy, and agent identity card config
- external doctrine records can produce full attestations without becoming implementation or capability evidence
- unknown governance/authority-shaped fields are rejected/attested instead of silently trusted
- CLI: `identity attestation {list,show,validate,verify-bundle,compare}`
- 41 focused identity tests; full suite was `1263 passed, 2 skipped` at P1.4.12 seal (now `1376 passed, 2 skipped` with P1.4.13/14)
- invariants `INV-P1412-01` through `INV-P1412-10`
- report: `agent/reports/P1.4.12_RAW_SOURCE_CANONICAL_HASH_ATTESTATION.md`

P1.4.12 provides hash-based source attestation. It does not provide cryptographic signatures, tamper-proof storage, trust scoring, or capability verification.

## P1.4.13 - Authority Delta Detector (2026-06-21)

- P1.4.13: semantic authority delta detection — `authority_delta.py`, CLI `identity authority-delta compare`
- domain model: `AuthorityDeltaType` (30 types), `AuthorityDeltaSeverity` (5 levels), `AuthorityDelta`, `AuthorityDeltaInput`, `AuthorityDeltaReport`
- authority surface extraction for operator_contract, agent_identity_card_config, self_model_policy, external_doctrine, capability_claims, source_attestation source kinds
- semantic delta classification for risk ceiling, human oversight, tool permissions, write scope, external effect, claim/capability/doctrine status escalation
- severity resolution (INFO/LOW/MEDIUM/HIGH/CRITICAL), consent/evidence requirement markers
- attestation reference linkage (old_attestation_id, new_attestation_id)
- conservative tool classification heuristic (external-effect, write, read-only tokens)
- CLI: `identity authority-delta compare --old/--new/--source-kind/--json`
- 58 tests (core, seal, CLI); full suite `1321 passed, 2 skipped`
- invariants `INV-P1413-01` through `INV-P1413-10`
- report: `agent/reports/P1.4.13_AUTHORITY_DELTA_DETECTOR.md`

P1.4.13 detects authority-relevant changes. It does not grant Operator consent, approve actions, or execute tools.

## P1.4.14 - Operator Consent Binding (2026-06-21)

- P1.4.14: delta-bound Operator consent — `operator_consent.py`, CLI `identity consent {request,grant,deny,revoke,show,validate}`
- domain model: `OperatorConsentStatus` (6 states), `OperatorConsentScope` (4 scopes), `OperatorConsentRequest`, `OperatorConsentRecord`, `ConsentBindingValidation`, `OperatorConsentDecision`
- `build_operator_consent_request()` from `AuthorityDeltaReport`, `grant_operator_consent()` with fail-closed risk acknowledgement, `deny_operator_consent()`, `revoke_operator_consent()`, `validate_operator_consent_binding()`
- binding rules: consent is bound to exact delta_ids and old/new attestation_ids, not global, not transferable, requires risk acknowledgement for HIGH/CRITICAL
- revoked/expired/denied consent is permanently invalid for binding validation
- scope behavior: SINGLE_DELTA, DELTA_REPORT, SOURCE_UPDATE, SESSION_LIMITED (unsupported)
- JSON serialization for all consent data models
- 55 tests (27 core, 14 seal, 10 CLI, 4 fixtures); full suite `1376 passed, 2 skipped`
- invariants `INV-P1414-01` through `INV-P1414-10`
- report: `agent/reports/P1.4.14_OPERATOR_CONSENT_BINDING.md`
- **Ready for P1.4.15** Principal / Delegate Model

P1.4.14 binds Operator consent to specific authority deltas. It does not execute changes, grant capabilities, or create global/permanent consent.

## P1.4.15 — Identity Governance Command Surface (2026-06-21)

- P1.4.15: unified identity CLI surface — `identity_cli_surface.py`, CLI `identity status` / `identity verify`
- Data models: `IdentityCliStatus` (OK/DEGRADED/BLOCKED/UNKNOWN), `IdentityCliEnvelope`, `IdentitySubsystemStatus`, `IdentityStatusReport`
- Standardized JSON envelope with `ok`/`command`/`status`/`errors`/`warnings`/`result`
- `build_identity_status_report()` — lightweight subsystem probes (read-only)
- `verify_identity_surface()` — non-destructive validator checks (read-only)
- Commands: `identity status --json`, `identity verify --json` with human-readable output
- All P1.4 subcommand groups (autonomy, claims, doctrine, attestation, authority-delta, consent) routed under one namespace
- Human-readable output exposes blockers and suggested next commands
- 53 tests (21 core/envelope, 23 routing, 9 seal); full suite `1429 passed, 2 skipped`
- invariants `INV-P1415-01` through `INV-P1415-10`
- report: `agent/reports/P1.4.15_IDENTITY_GOVERNANCE_COMMAND_SURFACE.md`
- **Ready for P1.4.16** Identity Test Battery

P1.4.15 implements a command surface, not an interactive agent terminal. It does not execute tools, grant consent, mutate identity sources, or create new authority.

## P1.4.11 — External Doctrine Assimilation Registry (2026-06-21)

- P1.4.11: source-hashed external doctrine registry — `external_doctrine.py`, `doctrine_registry.py`, `doctrine_mapping.py`, and `doctrine_claim_boundaries.py`
- seeded doctrine: `agentic_os_asymmetric_teardown`, `abos_design_principles_v1`, `aether_v0_2`
- each seeded doctrine has source hash, roadmap impact mapping, claim boundaries, risk notes, and Operator acceptance
- P1.4.10 integration: doctrine-derived overclaims are blocked/downgraded through the capability claim boundary engine
- CLI: `identity doctrine {list,show,validate,impact,claims}`
- 33 tests in `tests/test_external_doctrine_registry.py`, `tests/test_doctrine_cli.py`, `tests/test_doctrine_seal.py`
- invariants `INV-P1411-01` through `INV-P1411-10`
- report: `agent/reports/P1.4.11_EXTERNAL_DOCTRINE_ASSIMILATION_REGISTRY.md`
- **Ready for P1.4.12** Raw Source + Canonical Hash Attestation

P1.4.11 allows external doctrine to influence roadmap mapping. It does not allow doctrine to become implemented capability by declaration.

## P1.4.10 — Capability Claim Boundary Engine (2026-06-21)

- P1.4.10: evidence-gated capability claim evaluation — `capability_claims.py` with 14-claim static registry, anti-hype firewall, roadmap/implementation/verification boundary enforcement, global-autonomy blocking, safe rewrite engine that preserves truth, fail-closed on unknown claims or missing evidence
- CLI: `identity claims {evaluate,list,show,validate,rewrite}`
- 51 tests in `tests/test_capability_claim_boundary.py`
- 12 invariants `INV-P1410-01` through `INV-P1410-12`
- report: `agent/reports/P1.4.10_CAPABILITY_CLAIM_BOUNDARY_ENGINE.md`
- **Ready for P1.4.11** External Doctrine Assimilation Registry

## P1.4.7 / P1.4.7-MG — Agent Identity Card (2026-06-21)

- P1.4.7: machine-readable Agent Identity Card with six source-bound hashes, stable/runtime SHA-256, CLI `identity card {show,validate,hash,attest,taxonomy}`
- P1.4.7-MG merge gate: `self_model_policy_path` respected at final validation; `agent_identity_card` capability marked `implemented`; `IdentitySourceBundle` for single-load card path; identity CLI extracted to `cli_modules/`
- Canonical card hash snapshots updated after self-model inventory correction
- **Ready for P1.4.10** Capability Claim Boundary Engine (see P1.4.9 report for handoff)

## P1.4.9 — Measured Autonomy Score (2026-06-21)

- P1.4.9: evidence-backed measurement layer — `measure_autonomy_score()` from AutonomyDecision records, 9 measured autonomy classes, top blockers, confidence scoring
- `identity/autonomy_measurement.py` — domain types, engine, classification, JSONL persistence
- CLI: `identity autonomy measure` with `--json`, `--evaluate-and-record`
- 45 tests in `tests/test_measured_autonomy_score.py`
- 10 invariants `INV-P149-01` through `INV-P149-10`
- report: `agent/reports/P1.4.9_MEASURED_AUTONOMY_SCORE.md`
- **Ready for P1.4.10** Capability Claim Boundary Engine

## P1.4.8 — Autonomy Scale Engine (2026-06-21)

- P1.4.8: action-scoped autonomy decision engine — `resolve_autonomy_decision()` with A0–A7 scale, fail-closed validation, risk/reversibility/lifecycle escalation, capability honesty
- `identity/autonomy_scale_engine.py` — domain types, baseline matrix, resolver
- `identity/autonomy_scale_engine_validation.py` — fail-closed validation, invariant enforcement
- CLI: `identity autonomy evaluate` with `--json`, `--json` output
- 40 tests in `tests/test_autonomy_scale_engine.py`
- 10 invariants `INV-P148-01` through `INV-P148-10`
- report: `agent/reports/P1.4.8_AUTONOMY_SCALE_ENGINE.md`
- **Ready for P1.4.9** Measured Autonomy Score

## P1.4.16 — Identity Test Battery (2026-06-21)

- P1.4.16: full identity governance test battery — `identity_test_battery.py` (battery engine, models + engine) and `identity_test_battery_scenarios.py` (scenario runners)
- 26 test cases across 7 categories: kernel, persona, operator_contract, communication_modes, identity_context, self_model, identity_card
- Battery wraps all 26 cases into a single PASSED/FAILED/DEGRADED/SKIPPED status; each case individually scorable (OK/FAIL/SKIP)
- 10 invariants defined (INV-P1416-01 through INV-P1416-10), all passing
- New CLI under identity namespace: `identity test-battery {run,list,run-case}` with `--scenarios` toggle for adversarial cases
- Two-file split: battery engine (`identity_test_battery.py`) holds models + engine; scenario runners (`identity_test_battery_scenarios.py`) hold concrete scenarios with late imports to avoid circular imports
- New tests: `tests/identity/test_identity_test_battery.py` (18 core tests) and `tests/identity/test_identity_test_battery_seal.py` (13 integrated/seal tests) — 31 new tests
- Full test suite: **1460 passed, 2 skipped** (zero regressions from P1.4.15's 1429)
- Battery status: **PASSED (26/26)** — all kernel/persona/operator/modes/context/self_model/card categories green
- Adversarial scenarios included by default; CLI `--scenarios` toggleable
- report: `agent/reports/P1.4.16_IDENTITY_TEST_BATTERY.md`
- **Ready for P1.4.17** Continuity Capsule

P1.4.16 is a verification/test harness, not a new governance engine. It sits above P1.4.13-14-15 (authority delta, consent, command surface) and below P1.4.17, wrapping all prior identity layers into a single battery.

## P1.4.17 — Agent Lifecycle Eligibility State Machine (2026-06-21)

- P1.4.17: lifecycle eligibility state machine — `agent_lifecycle.py`, CLI `identity lifecycle {show,profile,validate-transition,transitions,recommend}`
- 8 lifecycle states: DRAFT, ACTIVE, SUSPENDED, RESTRICTED, MAINTENANCE, DEPRECATED, ARCHIVED, REVOKED
- 24 reason codes for state transitions (e.g. OPERATOR_INITIATED, CONSENT_EXPIRED, COMPLIANCE_VIOLATION, EOL_DECLARED)
- 9 lanes model — each lifecycle state maps to eligible/blocked lanes + required gates
- REVOKED is terminal — no transitions out; DRAFT→ACTIVE denied; SUSPENDED→ACTIVE denied
- RESTRICTED is reason-sensitive — restrictions depend on the transition reason, not a blanket block
- ACTIVE is gated — lane eligibility is explicit, not unlimited
- Lifecycle does NOT grant authority — it determines lane eligibility only; permission remains with Policy and HITL
- Recommendation engine reads governance signals (authority delta, consent, battery) but does not apply transitions
- 17 invariants: INV-P1417-01 through INV-P1417-17
- 60 new tests (38 core in test_agent_lifecycle.py, 22 seal/CLI in test_agent_lifecycle_seal.py)
- Full suite: 1520 passed, 2 skipped
- All validation/recommendation is read-only — no mutation of identity sources, no consent grants, no tool execution

P1.4.17 governs which lifecycle state an agent is in and which lanes it is eligible for. It does not execute tools, grant permissions, or decide authority — those remain with Policy, HITL, and the Operator Consent Binding.

## Package layout

```
src/agentic_runtime/   # runtime kernel
tests/                 # pytest suite
examples/demo.py       # thin wrapper around agentic_runtime.demo
agent/                 # agent operating docs (this folder)
```
