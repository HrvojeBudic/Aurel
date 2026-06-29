# Decisions Log

## 2026-06-29 - P2.3-B Workspace Window Semantics Boundary

### DEC-P23B-01: Missing P2.3-A OMNI marker waived for P2.3-B dispatch only
**Decision:** The operator explicitly instructed this P2.3-B dispatch to ignore missing P2.3-A OMNI acceptance evidence and implement. P2.3-B records this as an operator waiver, not as false OMNI acceptance evidence. The waiver is scoped to this dispatch only and does not extend to later packs.
**Why:** P2.3-A implementation, report, commit hash (`1271881`), report-hash docs commit (`2e3f6d1`), clean git evidence, projection seed, side-effect proof, and DONE status are present locally, but no separate P2.3-A OMNI acceptance marker was found in repo state.

### DEC-P23B-02: P2.3-B is contract/read-model semantics only
**Decision:** P2.3-B defines focus intent, stack/layer order, group/collection, restore/resume, and workspace focus/stack projection semantics only. It does not create browser focus, frontend activation, focus manager runtime, z-index runtime, CSS/layout engine, draggable/resizable windows, storage, route runtime, API/event runtime, product behavior, memory/trace writes, runtime mutation, P2.3-C, P2.10, or P2.13.
**Why:** P2.3-B vocabulary sounds like real window-manager/product behavior. Keeping every contract side-effect false preserves the P2.3-A foundation boundary and prevents runtime overclaim.

## 2026-06-29 - P2.1-D Topbar Integration Tail / Section Seal Boundary

### DEC-P21D-01: P2.1 seals only at contract scope
**Decision:** P2.1-D may return `SEALED_FOR_P2_1_CONTRACT_SCOPE` only for the P2.1 Global Topbar / Surface Registry contract/read-model layer. The seal does not claim production `LIVE`, actual `TRACE_VERIFIED`, release scope, visual topbar implementation, route runtime, local navigation, API server, event bus, or runtime event emission.
**Why:** P2.1 closes the global topbar / surface registry contract surface. Product UI, route runtime, local navigation, trace verification, and release evidence belong to later sections and cannot be inferred from a contract-scope seal.

### DEC-P21D-02: P2.2 readiness is plan-only
**Decision:** `READY_FOR_P2_2_PLAN` means P2.2 planning/readiness only. It does not start P2.2, does not implement P2.2-A, and does not create per-surface local navigation.
**Why:** P2.1-D can hand off a coherent P2.1 section to the next planning gate without crossing into the P2.2 implementation boundary.

## 2026-06-29 - P2.0-F Projection / CLI / Exit Seal Boundary

### DEC-P20F-01: Missing P2.0-E OMNI marker waived for P2.0-F dispatch only
**Decision:** The operator explicitly waived the missing local P2.0-E OMNI acceptance marker for the P2.0-F implementation dispatch. P2.0-F records this as an operator waiver, not as false OMNI acceptance evidence. The waiver is scoped to this dispatch only and does not extend to later packs.
**Why:** P2.0-E implementation, report, commit hash (`1f0f6a9`), clean git evidence, and DONE status are present locally, but no separate P2.0-E OMNI acceptance marker exists in repo state (the established convention records acceptance inline in the next pack's dependency evidence). The operator confirmed "Waive marker, proceed" so the dispatch unblocks without rewriting evidence history.

### DEC-P20F-02: P2.0 seals only at contract scope
**Decision:** P2.0-F may return `SEALED_FOR_P2_CONTRACT_SCOPE` only when the P2.0-A/B/C/D/E report chain, P2.0.27-P2.0.30 coverage, projection/API/event contract, read-only CLI inspect with explicit TUI/LIVE/trace unavailable boundaries, docs sync, and fake-truth guards all pass. `PRODUCTION_LIVE_SCOPE`, `TRACE_VERIFIED_SCOPE`, and `RELEASE_SCOPE` cannot seal without actual live-path, trace-verification, and release evidence respectively. The seal claims no production `LIVE`, actual `TRACE_VERIFIED`, `EXIT_SEALED`, or release readiness.
**Why:** P2.0 is a contract/projection layer over the seven-surface cognitive OS lock. Production live runtime, trace verification, and release belong to later layers; the contract-scope seal must remain honest about what is unavailable.

### DEC-P20F-03: P2.1 readiness is review-only and not coding authorization
**Decision:** `READY_FOR_P2_1_REVIEW` derived from `SEALED_FOR_P2_CONTRACT_SCOPE` means OMNI review/brainstorm/planning only. It never means `READY_FOR_P2_1_CODING`, does not start P2.1, and does not authorize P2.1 implementation work.
**Why:** Exit seal at contract scope prepares review, not execution. P2.1 coding requires a separate accepted dispatch after OMNI review.

## 2026-06-29 - P2.0-E Operator Waiver Boundary

### DEC-P20E-01: Missing P2.0-D OMNI marker waived for P2.0-E dispatch only
**Decision:** The operator explicitly waived the missing local P2.0-D OMNI acceptance marker for the P2.0-E implementation dispatch. P2.0-E reports this as an operator waiver, not as false OMNI acceptance evidence.
**Why:** P2.0-D implementation, report, commit hash, clean git evidence, and validation evidence are present locally, but the exact OMNI acceptance marker was not found in repo state. The waiver unblocks this dispatch without rewriting evidence history.

## 2026-06-28 - P1.9.30 Seal Criteria Repair

### DEC-P1930-01: P1.9.30 seals P1 contract scope only
**Decision:** P1.9.30 may return `SEALED` only with qualification `SEALED_FOR_P1_CONTRACT_SCOPE` when the P1.9-A/B/C/D report chain, P1.9.0-P1.9.30 coverage, projection/API/event contract, read-only CLI/operator-testable dev fixture path, docs sync, unavailable LIVE/trace disclosures, and fake truth guards pass. This seal does not claim production `LIVE`, actual `TRACE_VERIFIED`, `EXIT_SEALED`, release readiness, or P2 coding readiness.
**Why:** Actual trace verification belongs to a later AurelTrace truth layer, and production live runtime is not implemented in P1.9. Output Passport can seal its P1 contract/projection/operator-testable layer only if unavailable production-live and trace-verification states remain explicit and non-operational.

### DEC-P1930-02: P2 readiness is review-only and audit-gated
**Decision:** `SEALED_FOR_P1_CONTRACT_SCOPE` may derive `READY_FOR_P2_REVIEW`, meaning review, brainstorm, or planning only after the follow-up pre-P2 audit accepts the criteria repair. It never means `READY_FOR_P2_CODING` and does not authorize P2 implementation work.
**Why:** Criteria repair is not the full pre-P2 validation sweep. P2 coding requires a separate accepted pre-P2 audit decision.

## 2026-06-28 — P1.8-B Proposal / Permission / Execution / Operator Review Pack

### DEC-P18B-01: Action boundary pack is contract-only
**Decision:** P1.8-B adds deterministic contracts, transition-collapse guards, and a compact read model for P1.8.23-P1.8.26 only. It does not implement runtime permission enforcement, policy/Custos decisions, approvals, execution dispatch, proof verification, trace/Ledger writes, memory writes, tool/workflow execution, SYSTEM mutation, Shell/CLI/TUI binding, or P1.8-C behavior.
**Why:** Proposal, permission, execution, proof, and operator review must remain separate semantic states before later runtime/projection surfaces can consume them.

### DEC-P18B-02: Operator decision state does not auto-execute
**Decision:** `OperatorDelegationDecisionBinding` records explicit operator review states. Pending review blocks final claims; approved state permits only contract-state continuation and never dispatches execution; rejected/stopped states block continuation.
**Why:** Operator review is a state boundary, not an implicit approval workflow or execution trigger.

## 2026-06-27 — P1.8-A Actor Boundary Pack

### DEC-P18A-01: Operator-authorized v5.5 remap
**Decision:** The local v5.1 pointer from P1.8.16 to P1.8.17 Projection/API/Event Contract is superseded for this run by the operator-authorized v5.5 remap: **P1.8.16 -> P1.8-A -> P1.8-B**. P1.8-A covers P1.8.17-P1.8.22 as the Actor Boundary Pack.
**Why:** The actor boundary pack must be canonized before projection/API/event binding so agents, tools, workflows, BusinessEnvironment, CRO, and SYSTEM root boundaries cannot be overclaimed by later surfaces.

### DEC-P18A-02: Actor boundary pack is contract-only
**Decision:** P1.8-A adds pure deterministic contracts and a compact read model only. It does not implement runtime enforcement, policy/Custos decisions, approvals, permission grants, execution, trace/Ledger writes, memory writes, tool/workflow execution, SYSTEM mutation, Shell/CLI/TUI binding, or P1.8-B behavior.
**Why:** Actor boundary contracts must separate declared authority from active authority. Enforcement belongs to later runtime/policy layers.

### DEC-P18A-03: Package-level authority builder compatibility
**Decision:** `agentic_runtime.delegation.build_delegation_authority_ref` now preserves both historical call styles: P1.8.0 foundation calls `(authority_kind, authority_basis)` and P1.8.4 authority-binding calls `(delegation_ref_id, authority_kind, authority_basis)`.
**Why:** The broad delegation validation selector exercises both package-level APIs. The compatibility wrapper keeps existing P1.8.0 and P1.8.4 tests passing without changing either underlying module.

## 2026-06-26 — P1.7.19 Docs / State / Reports Update

### DEC-P1719-01: Truth-sync only; no runtime behavior
**Decision:** P1.7.19 updates agent documentation, state canon, reports index, architecture pointer, and P1.7.20 readiness checklist only. No path governance backend, CLI, resolver, policy bridge, enforcement, Ledger, approval, or sandbox changes.
**Why:** P1.7.19 is a governance truth gate before exit seal, not a feature phase.

### DEC-P1719-02: P1.7 pre-seal; P1.7.20 next
**Decision:** P1.7 section is **pre-seal** after P1.7.19. Next planned task is **P1.7.20 — Exit Seal + Live Integration Demo**. Do not mark P1.7 fully sealed until P1.7.20 completes.
**Why:** Integration-First law requires exit seal proof, not docs-only completion, to seal a section.

## 2026-06-25 — P1.6.20 P1.6 Exit Seal + Live Integration Demo

### DEC-P1620-01: P1.6 sealed as Integration-First vertical slice
**Decision:** P1.6.20 adds `policy_cards/exit_seal.py` — read-only exit seal with 20 checks, deterministic report hash, verdict `PASS_WITH_WARNINGS`. P1.6 section complete.
**Why:** Integration-First law requires proof, not feature expansion, before advancing to P1.7.

### DEC-P1620-02: No enforcement in exit seal
**Decision:** Exit seal module does not import runtime, call submit, write Ledger, activate approvals, or mutate sandbox. Seal artifacts contain no raw secrets or command bodies.
**Why:** Exit seal that overclaims capability is governance theater.

### DEC-P1620-03: P1.7.0 next
**Decision:** Next planned task is **P1.7.0 — Path Governance & Source Trust Foundation**. P1.6 Policy Cards & Behavioral Contracts is sealed.
**Why:** P1.6 vertical slice is complete; path governance is the next Integration-First section.

## 2026-06-25 — P1.6.19 Policy Docs/State/Reports Update

### DEC-P1619-01: Truth-sync only; no runtime behavior
**Decision:** P1.6.19 updates agent documentation, state canon, reports index, operator runbook, and P1.6.20 checklist only. No policy backend, CLI, enforcement, Ledger, approval, or sandbox changes.
**Why:** P1.6.19 is a governance truth gate before exit seal, not a feature phase.

### DEC-P1619-02: Roadmap v5.1 naming correction canonized
**Decision:** P1.6.17 is **Policy Projection/API/Event Contract** (not "Policy CLI Surface"). P1.6.18 is **Policy CLI/TUI Binding** (not "Projection Contract"). P1.6.19 is docs/state/reports update. P1.6.20 is exit seal + live integration demo.
**Why:** Integration-First roadmap separates contract definition from operator surface binding; stale names are governance bugs.

### DEC-P1619-03: Operator runbook in agent canon
**Decision:** Operator inspection commands and source-label doctrine live in `agent/reports/P1.6.19_*` and synced `agent/*.md` files. CLI consumes projection contract; docs do not duplicate backend logic.
**Why:** Backend remains source of truth; documentation is projection over verified capability.

## 2026-06-25 - P1.6.18 Policy CLI/TUI Binding

### DEC-P1618-01: CLI consumes projection contract; no parallel logic
**Decision:** P1.6.18 adds `cli_modules/policy_commands.py` that calls `build_policy_projection_contract(cli_binding_available=True)` and `policy_projection_to_json_safe_dict()`. No duplicated projection builders or fake LIVE state.
**Why:** Integration-First law requires CLI to bind to P1.6.17 contract, not scrape internals.

### DEC-P1618-02: Shell binding remains UNAVAILABLE
**Decision:** Only CLI binding is implemented. `shell_binding` section stays `UNAVAILABLE` with honest reason until Shell UI exists.
**Why:** P1.6.18 is CLI binding, not full Shell UI.

### DEC-P1618-03: Built-in harness registry for CLI list/run
**Decision:** `policy_harness_registry.py` exposes built-in scenario matrix for CLI harness commands; comparator logic stays in P1.6.16 `test_harness.py`.
**Why:** P1.6.16 lacked a public suite registry; CLI needs honest list/run without duplicating harness engine.

## 2026-06-25 - P1.6.17 Policy Projection/API/Event Contract

### DEC-P1617-01: Projection contract only; CLI deferred to P1.6.18
**Decision:** P1.6.17 implements `projection_contract.py` as a read-only projection/API/event contract. CLI and Shell bindings are represented as `UNAVAILABLE` with honest reasons. No CLI commands added.
**Why:** Integration-First roadmap separates contract definition (P1.6.17) from operator surface binding (P1.6.18).

### DEC-P1617-02: Source labels are mandatory for capability state
**Decision:** Every `PolicyProjectionSection` declares a `PolicyProjectionSourceLabel`. `UNAVAILABLE` requires reason; `ERROR` requires safe error; `TRACE_VERIFIED` only when evidence hash present.
**Why:** No unlabelled mock data as operational truth; backend remains source of truth.

### DEC-P1617-03: Order-insensitive canonical hashing
**Decision:** `policy_projection_hash()` keys sections by `section_id`, sorts capabilities/reasons/errors before SHA-256.
**Why:** Stable hashes for CLI/TUI consumption and future event-stream compatibility.

## 2026-06-25 - P1.6.16 Policy Test Harness

### DEC-P1616-01: Harness validates shadow governance, does not enforce
**Decision:** `test_harness.py` defines scenario cases, runs Custos shadow stack, compares expected vs actual, and emits hashed reports — but does NOT enforce policy, write Ledger, activate approvals, block commands, or change sandbox/runtime behavior.
**Why:** P1.6.16 formalizes testability of shadow governance without crossing the enforcement boundary.

### DEC-P1616-02: Deterministic hashes with order-insensitive collections
**Decision:** Case, result, and report hashes sort tags, conflict types, violation types, reason codes, and results by `case_id` before SHA-256 canonicalization.
**Why:** Reproducible governance scenario verification requires stable hashes across shuffled inputs.

### DEC-P1616-03: Reuse resolver attach hooks for family-decision scenarios
**Decision:** Family-decision harness path calls existing `_attach_conflict_metadata`, `_attach_trace_metadata`, `_attach_violation_metadata` after `aggregate_family_decisions` — no parallel resolver.
**Why:** Single source of truth for shadow metadata attachment; avoids duplicated strictest-wins or violation logic.

### DEC-P1616-04: Metadata sanitization in harness reports
**Decision:** `_sanitize_metadata()` strips sensitive keys and command-body fields from harness case/report payloads.
**Why:** Governance test artifacts must be JSON-safe and audit-ready without leaking secrets or raw commands.

## 2026-06-25 - P1.6.15 Policy Violation Trace Hook

### DEC-P1615-01: Violation evidence, not enforcement
**Decision:** `violation_trace.py` produces shadow violation evidence with `shadow_only=true` and `enforced=false` but does NOT write to Ledger, block commands, activate approvals, or change sandbox/runtime authorization.
**Why:** Violation candidates are audit evidence; shadow mismatch is not proof runtime was wrong.

### DEC-P1615-02: Violation ID is deterministic SHA-256 hash
**Decision:** `violation_trace_id` equals `policy_violation_hash()` over canonical dict (excludes hash field from body).
**Why:** Aligns with P1.6.14 trace and all Custos hash conventions.

### DEC-P1615-03: Optional violation fields on ResolvedPolicySet and PolicyShadowProjection
**Decision:** `violation_trace*` optional on `ResolvedPolicySet`; projection carries violation metadata fields with empty defaults.
**Why:** Backwards compatibility; violation metadata enriches existing shadow artifacts.

### DEC-P1615-04: Priority-based violation classification
**Decision:** `classify_policy_violation()` uses violation-type priority so structural gaps (missing context, adapter error, incomplete trace) are not overwritten by alignment-only signals.
**Why:** Conservative governance evidence must surface structural failures before mismatch taxonomy.

### DEC-P1615-05: Metadata sanitization strips secrets and command bodies
**Decision:** `_sanitize_violation_metadata()` rejects sensitive keys and command-body fields before canonicalization.
**Why:** Violation evidence must be metadata-safe and audit-ready without leaking raw secrets or commands.

## 2026-06-24 - P1.6.14 Policy Resolution Trace Hook

### DEC-P1614-01: Trace-compatible evidence, not Ledger integration
**Decision:** `resolution_trace.py` produces trace-compatible metadata (PolicyResolutionTraceEvent, PolicyResolutionTraceEnvelope) with deterministic hashes and identifiers but does NOT write to `trace.py`/`AurelTraceLog`, import `AgenticRuntime`, or trigger real Ledger operations.
**Why:** P1.6.14 creates audit-ready evidence without compromising the architectural boundary. Full Ledger integration is deferred.

### DEC-P1614-02: Trace ID is deterministic SHA-256 hash of canonical content
**Decision:** `trace_id` is derived from `policy_trace_hash()` (SHA-256 over canonical dict). No external randomness, no wall-clock uniqueness.
**Why:** Determinism enables reproducible trace verification; aligns with all existing Custos hash conventions.

### DEC-P1614-03: Optional trace fields on ResolvedPolicySet (None by default)
**Decision:** `resolution_trace`, `resolution_trace_hash`, `resolution_trace_id` are `None` by default on `ResolvedPolicySet`.
**Why:** Full backwards compatibility; existing tests and consumers work without modification.

### DEC-P1614-04: Trace metadata derived from existing resolution + conflict metadata
**Decision:** `_attach_trace_metadata()` builds the trace event from the `ResolvedPolicySet` fields and `conflict_resolution` dict, not from raw adapter output.
**Why:** Single source of truth; trace reflects the final resolved state, not intermediate values.

### DEC-P1614-05: Runtime projection carries trace identifiers
**Decision:** `PolicyShadowProjection` now carries `resolution_trace_id` and `resolution_trace_hash` as optional string fields, propagated from `ResolvedPolicySet` in `project_policy_resolution_against_runtime()`.
**Why:** Connects shadow projection to trace evidence without changing `AgenticRuntime.submit()` behavior.

## 2026-06-24 - P1.6.13 Policy Conflict Algebra & Strictest-Wins Rules

### DEC-P1613-01: Error is highest rank (5) — conservative for conflict purposes
**Decision:** `PolicyDecisionRank.ERROR` has the highest numeric value (5), distinct from the existing `FamilyDecision.ERROR` value (3). When an adapter produces an error, that decision is the strictest in any conflict resolution.
**Why:** Conservative conflict algebra must treat adapter failures as the most severe outcome to avoid accidentally allowing operations that failed to evaluate.

### DEC-P1613-02: Empty input → NOT_APPLICABLE with NO_APPLICABLE_POLICY
**Decision:** When `resolve_policy_conflicts_strictest_wins()` receives an empty `family_decisions` tuple, it returns `NOT_APPLICABLE` rank with `NO_APPLICABLE_POLICY` strategy, not a generic WARN.
**Why:** An empty policy set means no families decided anything. Warning would imply there's something to warn about when there simply isn't any applicable policy.

### DEC-P1613-03: Conflict fields on ResolvedPolicySet are optional (None by default)
**Decision:** `conflict_resolution: dict | None = None` and `conflict_hash: str | None = None` on `ResolvedPolicySet`.
**Why:** Full backwards compatibility — existing consumers and tests that construct `ResolvedPolicySet` directly continue to work without modification.

### DEC-P1613-04: Conflict hash is deterministic SHA-256 over canonical conflict dict
**Decision:** `PolicyConflictResolution.compute_hash()` produces a SHA-256 hash over `json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))`.
**Why:** Same pattern as all other Custos hashes; deterministic, JSON-safe, verifiable.

### DEC-P1613-05: No enforcement, no runtime imports, no side effects
**Decision:** `conflict_algebra.py` imports only from `policy_cards` via `TYPE_CHECKING` and never imports or references `AgenticRuntime`, `submit()`, sandbox, approval, or any enforcement machinery. All functions are pure.
**Why:** P1.6.13 formalizes conflict — it does NOT enforce. This is the cardinal architectural law.

### DEC-P1613-06: Specificity is tie-break only after strictness rank
**Decision:** `compute_specificity_score()` scores 0-5 per dimension based on metadata presence. A highly specific ALLOW must never override a general DENY or REQUIRE_APPROVAL.
**Why:** Specificity resolves ties between decisions at the same strictness rank. It is not a mechanism to override stricter decisions with specific-but-lenient ones.

### DEC-P1613-07: Family names normalized via .value for str, Enum compatibility
**Decision:** `_family_name_from_fd()` extracts family names using `.value` on enum members instead of `str()`, which in Python 3.12+ returns the repr for `str, Enum` mixed classes.
**Why:** Ensures family names serialize as plain strings (`"risk_tier"`) rather than enum reprs (`"PolicyFamily.RISK_TIER"`) in all canonical representations.

## 2026-06-23 - P1.6.11 Policy Resolution Context & Registry Binding

### DEC-P1611-01: Registry is explicit, deterministic, and in-memory
**Decision:** `PolicyCardRegistry` accepts explicit typed card instances/lists, deduplicates identical duplicate IDs, rejects duplicate IDs with different canonical hashes, and exposes stable canonical dict/hash output. It does not discover files or use a database.
**Why:** P1.6.11 binds known policy-card storage/lists to resolution without creating hidden policy sources or nondeterministic discovery.

### DEC-P1611-02: Context binding is closed-world and runtime-free
**Decision:** Runtime-like metadata is normalized through `build_policy_resolution_context()` and `context_from_*_like()` helpers. Dict inputs reject unknown fields, list/set-like fields are sorted, metadata is JSON-safe, and no runtime class import is required.
**Why:** P1.6.12 needs a stable projection surface, but P1.6.11 must not modify or invoke runtime behavior.

### DEC-P1611-03: Risk mapping is a conservative seed, not full enum unification
**Decision:** Known runtime, approval, policy-card, and identity risk values map explicitly into `RiskTier`. Unknown present values map conservatively to R5 with an explicit reason code; invalid value types fail closed.
**Why:** The Composer review identified risk-vocabulary drift, but full risk architecture migration is out of scope.

### DEC-P1611-04: Applicability filtering selects lawbook candidates, not outcomes
**Decision:** Registry applicability uses deterministic family/scope/context signals and transparent reason codes. Insufficient context skips cards; no applicable cards still resolves conservatively through Custos.
**Why:** P1.6.11 finds and binds relevant cards. The resolver remains responsible for judgment, and enforcement remains deferred.

### DEC-P1611-05: Registry integration remains SHADOW-only
**Decision:** `resolve_policy_cards_from_registry()` and `PolicyRuntimeResolver.resolve_from_registry()` feed applicable registry cards into the existing resolver. They produce `ResolvedPolicySet` with `WOULD_*` outcomes and do not touch `AgenticRuntime.submit()`.
**Why:** P1.6.11 prepares the deterministic context/lawbook bridge for P1.6.12 without implementing runtime enforcement.


## 2026-06-23 - P1.6.10 Custos v0 Policy Runtime Resolver / Shadow Mode

### DEC-P1610-01: Shadow mode only; submit() untouched
**Decision:** The resolver runs SHADOW only and never modifies, calls, or imports
`AgenticRuntime.submit()`. It produces a judgment (`ResolvedPolicySet`) but enforces
nothing. ENFORCE/SIMULATE are reserved enum names rejected fail-closed.
**Why:** P1.6.10 must create policy judgment without runtime punishment. "Entity
proposes, runtime disposes" — P1.6.10 does not yet dispose.

### DEC-P1610-02: Resolver lives in `policy_cards/`, not a new package
**Decision:** Place `resolution_context.py`, `resolution_result.py`, `resolver.py`
inside `src/agentic_runtime/policy_cards/` rather than a separate `policy_resolver/`.
**Why:** Every card family already lives there and the resolver is a pure consumer of
those modules; co-location avoids an import-graph split with zero benefit.

### DEC-P1610-03: Strictest-wins MVP, conservative defaults
**Decision:** Aggregate with `DENY > REQUIRE_APPROVAL (= ERROR) > WARN > ALLOW >
NOT_APPLICABLE`. No applicable cards → conservative `WARN` (never silent ALLOW).
Adapter ERROR is never swallowed: it escalates to REQUIRE_APPROVAL with an explicit
`ADAPTER_ERROR_CONSERVATIVE` reason.
**Why:** Fail toward caution; full Policy Conflict Algebra is a later phase.

### DEC-P1610-04: Deterministic, timestamp-free artifacts
**Decision:** `resolution_id` and both canonical hashes derive purely from
`context_hash` + sorted card source hashes; no timestamps or random UUIDs enter any
canonical hash. List fields are sorted in canonical form.
**Why:** Matches the policy-card determinism convention; same input/cards → same hash.

### DEC-P1610-05: Explicit card loading; no registry in P1.6.10
**Decision:** The resolver accepts an explicit list of card instances and detects
duplicate card IDs (ambiguity) fail-closed. No filesystem discovery or registry.
**Why:** Keeps P1.6.10 deterministic and leaves registry binding intact for P1.6.11
(no roadmap rewording needed).

## 2026-06-23 - P1.6.8S Repository Reality & Policy Card Stabilization Seal

### DEC-P168S-01: Repository truth must match documentation truth
**Decision:** P1.6.8S treats tracked files, tests, lint, validation commands, and agent docs as part of governance truth. A policy-card phase is not sealed if its files remain untracked or its docs overclaim validation.
**Why:** Aurel cannot claim governed, sealed, traceable behavior while repository state and documentation disagree.

### DEC-P168S-02: CLI subprocess tests must use the active interpreter
**Decision:** CLI subprocess tests should use a shared helper that invokes `sys.executable -m agentic_runtime.cli` from the repository root with `PYTHONPATH=src:.`.
**Why:** Bare `python3 -m agentic_runtime.cli` can select the wrong interpreter and fail imports even when the runtime is valid in the active environment.

### DEC-P168S-03: P1.6.8S does not implement P1.6.9
**Decision:** Sandbox Policy Card behavior remains out of scope. P1.6.8S only stabilizes repository reality after Prompt Policy Card Model completion.
**Why:** Interstitial seals should reduce drift without smuggling in the next feature phase.

### DEC-P168S-04: Structural debt is recorded, not refactored
**Decision:** The large identity CLI command module, duplicated policy-card boilerplate, broad mypy disables, optional-only security scans, and slow-test marker discipline are documented as deferred debt.
**Why:** Broad refactors would increase risk in a stabilization patch and should happen in dedicated hardening phases.

## 2026-06-23 - P1.6.4 Human Oversight Policy Card Model

### DEC-P164-01: HumanOversightPolicyCard defines oversight semantics, not approval execution
**Decision:** `HumanOversightPolicyCard` defines oversight levels, approval/confirmation expectations, R0-R6 oversight mappings, escalation seeds, and evidence requirements. It does not approve actions, pause workflows, or execute approval behavior.
**Why:** Oversight semantics and approval runtime are separate concerns. The runtime resolver, approval workbench, and enforcement belong to later tasks.

### DEC-P164-02: Human oversight cards cannot grant authority
**Decision:** Human oversight cards cannot grant authority, bypass risk tier policy, or bypass behavioral contracts. Dangerous metadata keys like `auto_approve`, `operator_not_required`, `skip_approval`, and `bypass_policy` are rejected.
**Why:** Metadata and declarative oversight semantics must not become a shadow control plane.

### DEC-P164-03: approval_required and explicit_confirmation_required are distinct
**Decision:** `HumanOversightLevel.APPROVAL_REQUIRED` and `HumanOversightLevel.EXPLICIT_CONFIRMATION_REQUIRED` are separate levels. R5 must use `explicit_confirmation_required`, not `approval_required`.
**Why:** R5 represents serious/irreversible actions requiring explicit Operator confirmation, not just approval. Collapsing these would weaken the safety model.

### DEC-P164-04: R4 requires approval or stricter
**Decision:** R4 must have `oversight_level = approval_required` or stricter and `action = request_approval` or stricter. `none`, `notify_only`, and `review_recommended` are rejected for R4.
**Why:** High-impact compensatable actions require human approval as a floor.

### DEC-P164-05: R5 requires explicit Operator confirmation with strong requirements
**Decision:** R5 must have `oversight_level = explicit_confirmation_required`, `oversight_mode = explicit_confirmation`, `action = request_explicit_confirmation`, plus `confirmation_requirement` with `requires_explicit_confirmation`, `preview_required`, `evidence_required`, `operator_identity_required` all true, and `reviewer_requirement` with `operator_required` true.
**Why:** Serious irreversible actions must not be made weak. Every confirmation safety flag must be enforced at the semantic level.

### DEC-P164-06: R6 is denied and not approvable
**Decision:** R6 must have `oversight_level = deny`, `oversight_mode = deny`, `action = deny_action`. Any approvable level (approval_required, explicit_confirmation_required, etc.) is rejected for R6.
**Why:** Denied/forbidden actions must remain denied in the semantic model. No oversight card should make R6 contingently executable.

### DEC-P164-07: Runtime approval engine is not implemented in P1.6.4
**Decision:** P1.6.4 does not implement a runtime approval engine, policy resolver, enforcement engine, Approval Workbench UI, governance board workflow, or P25 hardening.
**Why:** P1.6.4 is the semantic model layer only. Approval execution and enforcement are separate concerns.

### DEC-P164-08: Human oversight cards use container pattern with generic PolicyCard
**Decision:** `HumanOversightPolicyCard` contains a generic `PolicyCard` with `kind="human_oversight"`, matching the `RiskTierPolicyCard` pattern. No inheritance from `PolicyCard`.
**Why:** Consistent with P1.6.3 design. The generic PolicyCard provides identity/status/scope foundations; the typed card adds domain-specific semantics.

## 2026-06-23 - P1.6.5 Data Residency Policy Card Model

### DEC-P165-01: DataResidencyPolicyCard defines data locality semantics, not runtime egress enforcement
**Decision:** `DataResidencyPolicyCard` defines residency zones, data classes, processing locations, egress/exposure/redaction/storage rules. It does not enforce egress, route models, classify data, perform redaction, or encrypt at runtime.
**Why:** Data locality semantics and runtime egress enforcement are separate concerns. The runtime egress guard, model router, classification engine, and redaction/encryption executors belong to later tasks.

### DEC-P165-02: local_only means zero outbound by definition
**Decision:** Any data class with `residency_zone = local_only` cannot allow egress, external model access, external API access, or web search. Only `local_device` and `local_network` processing locations are permitted.
**Why:** `local_only` must be strict from the start. Permitting any external path under `local_only` would make the zone meaningless.

### DEC-P165-03: credentials must never externalize by default
**Decision:** The default credentials rule requires `local_only` zone, `egress_allowed = False`, `requires_encryption = True`, `requires_audit_trace = True`, and forbids external model/api/web exposure.
**Why:** Credentials are the most sensitive data class. Any externalization path is dangerous.

### DEC-P165-04: sensitive_personal_data, memory_record, trace_record are strict local_only
**Decision:** These three data classes are forced `local_only` with no egress by default. Any attempt to set a different zone or allow egress fails validation.
**Why:** These classes represent the highest personal/sensitive boundary. Externalization must be explicitly opted into, not default.

### DEC-P165-05: 20 data classes provide comprehensive coverage
**Decision:** 20 distinct `DataClass` enum values cover public through identity records, with 10 required classes that must always be present in any valid card.
**Why:** Fine-grained classification enables future consumers (egress guard, model router, memory policy, trace policy) to make precise decisions per data type.

### DEC-P165-06: Forbidden zone is fully non-permissive
**Decision:** `residency_zone = forbidden` cannot allow egress, external model, external API, web search, or any processing location other than `forbidden`. Any permissive setting on a forbidden rule fails validation.
**Why:** Forbidden means forbidden. No loopholes.

### DEC-P165-07: Runtime egress guard is not implemented in P1.6.5
**Decision:** P1.6.5 does not implement a runtime egress guard, model router, classification engine, redaction executor, encryption executor, or conflict resolver.
**Why:** P1.6.5 is the semantic model layer only. Egress enforcement and execution are separate concerns.

### DEC-P165-08: Data residency cards use container pattern with generic PolicyCard
**Decision:** `DataResidencyPolicyCard` contains a generic `PolicyCard` with `kind="data_residency"`, matching the `RiskTierPolicyCard` and `HumanOversightPolicyCard` patterns. No inheritance from `PolicyCard`.
**Why:** Consistent with P1.6.3/P1.6.4 design. The generic PolicyCard provides identity/status/scope foundations; the typed card adds domain-specific semantics.

## 2026-06-23 - P1.6.8 Prompt Policy Card Model

### DEC-P168-01: PromptPolicyCard defines prompt trust/authority semantics, not runtime prompt enforcement
**Decision:** `PromptPolicyCard` defines prompt sources, trust levels, roles, handling decisions, injection-risk vocabulary, and boundary requirements. It does not compile prompts, assemble context, enforce instruction hierarchy, detect prompt injection/jailbreaks, or block tools/memory at runtime.
**Why:** Prompt-handling semantics and runtime prompt machinery are separate concerns. The Prompt Compiler, injection detector, and policy resolver belong to later tasks.

### DEC-P168-02: Prompt policy cards cannot grant authority or compile prompts
**Decision:** A prompt policy card never grants authority merely by existing and never compiles or assembles a prompt. `allow` means "may enter prompt assembly under policy," not "obey."
**Why:** Consistent with the policy-card law — policy is a governed object, not a control-plane actor. Prompt authority is never inferred from text content alone.

### DEC-P168-03: Default prompt posture is strict / deny-by-default
**Decision:** `default_decision` must be `deny` (or `forbidden`). Permissive defaults (allow, context_only, etc.) fail validation.
**Why:** The instruction hierarchy and untrusted-content boundary must hold by default. No unknown prompt source can become trusted.

### DEC-P168-04: Untrusted content may inform but never command
**Decision:** Unknown sources cannot carry trusted trust levels. External content (web/email/file/code/external_api/retrieved_document/tool_output/unknown) cannot be instruction authority. Tool output is data/context, not command. Retrieved memory is context, not automatic authority.
**Why:** This is the core Aurel prompt law — protection against prompt injection, authority spoofing, and instruction-hierarchy collapse.

### DEC-P168-05: Untrusted content cannot request tools, write memory, or modify policy/identity
**Decision:** For trust levels external_untrusted, tool_output_untrusted, unknown_untrusted, and retrieved_context, any of allowed_to_request_tools / allowed_to_write_memory / allowed_to_modify_policy / allowed_to_modify_identity set to true fails validation.
**Why:** Tool escalation, memory poisoning, policy override, and identity drift are existential prompt-injection risks.

### DEC-P168-06: Injection-risk vocabulary is policy-only, not a detector
**Decision:** `PromptInjectionRisk` and `PromptInjectionPattern` define vocabulary and validation semantics only. High/critical effective injection risk cannot pair with allow + instruction authority, but no runtime detection is implemented.
**Why:** P1.6.8 defines injection-risk policy language; the detector is a future task.

### DEC-P168-07: Prompt compiler, injection detector, resolver, and P25/P29 hardening are not implemented in P1.6.8
**Decision:** P1.6.8 does not implement a prompt compiler, prompt assembly engine, instruction-hierarchy enforcer, prompt injection detector, jailbreak detector, tool-call runtime blocking, memory write enforcement, identity compiler change, policy runtime resolver, policy conflict detector, simulation mode, trace hook, CLI, report generator, or P25/P29 hardening.
**Why:** P1.6.8 is the semantic model layer only. Enforcement and detection are separate concerns.

### DEC-P168-08: Prompt policy cards use container pattern with generic PolicyCard
**Decision:** `PromptPolicyCard` contains a generic `PolicyCard` with `kind="prompt"`, matching all previous typed policy card patterns. No inheritance from `PolicyCard`. Risk tiers/oversight are referenced as strings to avoid cross-module coupling.
**Why:** Consistent with P1.6.3–P1.6.7 design. The generic PolicyCard provides identity/status/scope foundations; the typed card adds domain-specific semantics.

## 2026-06-23 - P1.6.7 Memory Write Policy Card Model

### DEC-P167-01: MemoryWritePolicyCard defines memory write semantics, not memory storage
**Decision:** `MemoryWritePolicyCard` defines memory zones, write types, decisions, verification statuses, retention classes, and write requirements. It does not store, write, retrieve, rank, consolidate, graph, promote, canonize, or enforce memory at runtime, and it does not implement Mneme.
**Why:** Memory write semantics and runtime memory storage are separate concerns. Mneme, the Evaluation Mirror, the Verification Court, Praxis, and the policy runtime resolver belong to later tasks.

### DEC-P167-02: Memory write cards cannot grant authority or write memory by themselves
**Decision:** A memory write card never grants authority merely by existing and never performs a memory write. It only describes the policy a future resolver/Mneme will evaluate.
**Why:** Consistent with the policy-card law — policy is a governed object, not a control-plane actor.

### DEC-P167-03: Default memory posture is conservative / deny-by-default
**Decision:** `default_decision` must be `deny` (or `forbidden`). Permissive defaults (allow, candidate_only, canonicalize_allowed, requires_evidence-only, ephemeral_only) fail validation.
**Why:** Raw experience does not become capability directly. No silent durable memory.

### DEC-P167-04: Candidate memory is not verified memory; verified memory is not canon
**Decision:** `skill_candidate_memory` cannot carry `verified`/`canonized` status by default. `verified_skill_memory` requires evaluation result + verification + evidence/trace references. `canon_memory` requires its own highest-scrutiny gates separate from verification.
**Why:** The maturation ladder (Trace → Evaluation → Candidate → Verification → Skill → Specialist → Reflex; and verified → canon) must not be skipped.

### DEC-P167-05: No silent canonical or policy memory writes
**Decision:** `canon_memory` cannot be plain `allow`; it requires source/evidence/trace references plus operator review, explicit confirmation, and conflict check. `policy_memory` cannot be plain `allow`; it requires policy authority + source/evidence/trace + operator review or explicit confirmation. Both require evidence/provenance/trace binding.
**Why:** Canon pollution and policy-memory drift are existential governance risks.

### DEC-P167-06: Operator profile memory is protected; credentials cannot become durable memory
**Decision:** `operator_profile` writes require user consent or operator review plus source/provenance (and trace when durable). `credentials` may never appear in a rule's `allowed_data_classes`. `sensitive_personal_data` durable writes require evidence + provenance + residency check + review.
**Why:** Operator-profile pollution and sensitive-data memory leakage must be impossible by default; consent workflow is deferred but its requirement is encoded now.

### DEC-P167-07: Runtime Mneme write enforcement, resolver, and P25/P29 hardening are not implemented in P1.6.7
**Decision:** P1.6.7 does not implement a memory storage/retrieval/consolidation engine, memory graph, canon/skill promotion engine, Verification Court, operator consent workflow, memory conflict detector, policy runtime resolver, policy conflict detector, simulation mode, trace hook, CLI, report generator, or P25/P29 hardening.
**Why:** P1.6.7 is the semantic model layer only. Enforcement and execution are separate concerns.

### DEC-P167-08: Memory write cards use container pattern with generic PolicyCard
**Decision:** `MemoryWritePolicyCard` contains a generic `PolicyCard` with `kind="memory_write"`, matching all previous typed policy card patterns. No inheritance from `PolicyCard`. Risk tiers and data classes are referenced as strings to avoid cross-module coupling.
**Why:** Consistent with P1.6.3–P1.6.6 design. The generic PolicyCard provides identity/status/scope foundations; the typed card adds domain-specific semantics.

## 2026-06-23 - P1.6.6 Tool Permission Policy Card Model

### DEC-P166-01: ToolPermissionPolicyCard defines permission semantics, not runtime Tool Gateway enforcement
**Decision:** `ToolPermissionPolicyCard` defines tool categories, permission types, decisions, matchers, and safety rules. It does not enforce permissions, execute tools, resolve tool registries, or run sandboxes at runtime.
**Why:** Tool permission semantics and runtime enforcement are separate concerns. The Tool Gateway, registry resolver, and sandbox executor belong to later tasks.

### DEC-P166-02: Default posture is deny-by-default / least privilege
**Decision:** Default decision must be `deny`. Any other default (allow, conditional) fails validation. Unknown tool categories must deny.
**Why:** Least privilege must be the default. Permission must be explicitly granted through permission rules.

### DEC-P166-03: Credential access denied by default, cannot be overridden by metadata
**Decision:** `credential_access` must be deny by default. Any rule with `credential_access` and a non-deny decision fails validation. Metadata keys like `credential_access_allowed` are dangerous and rejected.
**Why:** Credentials are the most sensitive capability. No tool permission card should externalize credentials.

### DEC-P166-04: Shell command requires sandbox/approval/risk constraints
**Decision:** Shell command cannot be simple allow. Valid decisions require sandbox_required, approval_required, explicit_confirmation_required, or conditional with risk_ceiling and sandbox_required=True.
**Why:** Unrestricted shell access is the most dangerous tool capability.

### DEC-P166-05: Network/external egress is denied or strongly governed by default
**Decision:** Network and external_egress permission types cannot be simple allow. Must use deny, approval_required, or conditional with constraints.
**Why:** External egress moves data outside the trust boundary. Must be explicitly governed.

### DEC-P166-06: Protected data classes cannot be exposed through external tools
**Decision:** Rules allowing external/network/model/browser access must not include credentials, operator_private, sensitive_personal_data, memory_record, trace_record, or source_code in allowed_data_classes, and must include them in forbidden_data_classes.
**Why:** Data residency semantics (P1.6.5) and tool permission semantics must agree on the safety boundary.

### DEC-P166-07: Runtime Tool Gateway is not implemented in P1.6.6
**Decision:** P1.6.6 does not implement a Tool Gateway, registry resolver, sandbox executor, network blocker, filesystem enforcer, credential system, memory write enforcer, or model router.
**Why:** P1.6.6 is the semantic model layer only. Enforcement and execution are separate concerns.

### DEC-P166-08: Tool permission cards use container pattern with generic PolicyCard
**Decision:** `ToolPermissionPolicyCard` contains a generic `PolicyCard` with `kind="tool_permission"`, matching all previous typed policy card patterns. No inheritance from `PolicyCard`.
**Why:** Consistent with P1.6.3/P1.6.4/P1.6.5 design. The generic PolicyCard provides identity/status/scope foundations; the typed card adds domain-specific semantics.

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

## 2026-06-23 - P1.6.10H Runtime Security, Coverage & Governance Truth Hotfix

### DEC-P1610H-01: Snapshot path traversal fix via CanonicalPathResolver

`_WorkspaceBackend.read_snapshot_file` previously used a raw `os.path.join(src, rel)`
for resolution, bypassing the `CanonicalPathResolver` already used by `read_file`,
`write_file`, and `delete_file`. The fix routes snapshot reads through a fresh
`CanonicalPathResolver` rooted at the snapshot source directory, rejecting parent
traversal (`../`), absolute paths, and symlink escapes. The resolver is lightweight
and already battle-tested on the other FS ops — no new dependency, no broad refactor.

### DEC-P1610H-02: Unsafe backend honesty via allow_unsafe gate in materialize_sandbox_backend

`materialize_sandbox_backend` previously instantiated `UnsafeLocalSandbox` directly
for non-Docker/non-Bubblewrap profiles, bypassing the `create_sandbox(allow_unsafe=True)`
safety gate. The fix routes non-hard backends through `create_sandbox(SandboxMode.UNSAFE_LOCAL,
root=root, allow_unsafe=True, ...)`. This makes the safety trade-off explicit and honest —
`restricted_local` still uses `UnsafeLocalSandbox` (not hard isolated) but now declares
`allow_unsafe=True` at the factory level. No behavior change; truth-only fix.

### DEC-P1610H-03: Canonical venv commands

All validation commands now reference `.venv/bin/python`. Bare `python3`, `pytest`,
`ruff`, and `mypy` are explicitly documented as non-authoritative. This prevents
environment confusion between the system Python and the project venv.

### DEC-P1610H-04: Coverage path correction

Coverage must measure `src/agentic_runtime` (the real runtime source under the `src/`
layout), not the `agentic_runtime` package namespace. The canonical command is:
`.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75`

### DEC-P1610H-05: Sandbox layer disambiguation

Four distinct sandbox layers are now documented: runtime sandbox policy (P0 enforced),
sandbox backend (execution abstraction), sandbox policy card (P1.6.9 semantic model),
and Custos v0 resolver (P1.6.10 shadow-only). The key truth: P1.6.9 cards and P1.6.10
resolver do not yet enforce runtime behavior. Runtime enforcement still flows through
the P0 runtime policy and sandbox layers.
