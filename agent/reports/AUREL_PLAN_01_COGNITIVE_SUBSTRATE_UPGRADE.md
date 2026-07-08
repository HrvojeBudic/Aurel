# AUREL UPGRADE MASTER PLAN — Cognitive Substrate Thickening Under Unweakened Governance

**Status:** DEFINITIVE PLAN (pre-build). Corrections from adversarial critique applied and reordered.
**Doctrine anchor:** "Entity proposes, runtime disposes." AurelTraceLog is the single canonical source of truth.
**Frontier:** P5 (AurelTrace) sealed; P6 (Durable Spine / Object Plane) next; P9 (Custos) enforcement later.
**Constraint:** Stdlib-only Python 3.11+, no runtime deps, deterministic/replayable, strictly additive-behind-flags.

---

## 1. Executive Summary

**Thesis.** Aurel's governance moat — the `CommandEnvelope -> Policy -> HITL -> Budget -> Snapshot -> Execute(sandbox) -> Verify -> Rollback -> Trace -> Memory` pipeline, the hash-chained AurelTraceLog, and its fail-closed / no-overclaim discipline — is already strong. Its *cognitive* substrate (memory sophistication, reasoning allocation, world models, external reach) is comparatively thin. This plan thickens cognition **without weakening a single governance invariant**: every new capability reduces to a `CommandEnvelope` through `AgenticRuntime.submit`, a governed `MemoryFabric.request_write`, or a read-only projection over the trace. Nothing becomes a second executor, a second source of truth, or a silent allow.

**Track A — Bi-temporal memory graph + memory-as-tools (P6 Durable Spine).** Upgrade the RAM-only 5-tier `MemoryFabric` into a bi-temporal (valid-time + transaction-time) knowledge graph with typed supersession edges, durable stdlib persistence anchored to trace ids, non-destructive belief revision (UPDATE/DELETE/FORGET), governed consolidation, and deterministic hybrid retrieval — every mutation flowing through the existing `request_write -> MemoryWritePolicy.evaluate_write -> _trace_memory` funnel. The candidate→verified→procedural→canon ladder is layered *on top of*, never around.

**Track B — Reasoning scheduler + per-entity thinking budget (P6.5.x).** A proposal-only scheduler on the entity/planning side that first repairs the honesty prerequisite (real `TokenUsage` into the ledger, killing the fictional flat 1200-token/0.01 USD estimate), then adds a per-entity `ThinkingBudget`, a difficulty/risk estimator, adaptive System-1/System-2 routing over the already-built-but-unused `ModelRouter.select_profile_for_task`, a heuristic PRM step verifier feeding a bounded LLM replan, and a hash-chained `ReasoningAllocationRecord`. It shapes only *what is requested*; `PlanValidator` and `runtime.submit` remain the sole gates.

**Track C — Simulation-gated action via lightweight world model (P6.4.x).** A "simulate-then-permit" admission gate that, for consequential writes, runs the candidate command in a disposable state twin (built from the existing `WorldLineForest.checkout` / `StateStore.materialize` primitive), scores the predicted post-state with the *same* state-based `StateVerifier`, and feeds the verdict to Policy/HITL as **evidence only, never authority**. Simulation output is a distinctly-labeled non-canonical `simulation_decision` trace event; predicted-vs-actual is stored as governed CANDIDATE calibration memory.

**Track D — MCP/A2A native adoption + self-correcting RAG (P7.x).** Adopt MCP (agent→tool) and A2A (agent→agent) as *wire shapes over stdlib transport*, never as execution authority — every remote MCP tool is bridged into `ToolRegistry` + `ToolContractRegistry` so no-contract-no-execution holds; every A2A request becomes a `CommandEnvelope`. A Self-RAG corrective-retrieval loop wraps `MemoryFabric.retrieve`. All external bytes are **tainted-by-provenance** and structurally barred from becoming instructions. The proprietary "OSP" protocol idea is **killed** — entity ontological state is a read-model projection over the trace.

---

## 2. Grounded Current-State Snapshot (BUILT vs CONTRACT-ONLY)

### BUILT and enforced (live in the spine)
- **Governed command pipeline.** `AgenticRuntime.submit` (`runtime.py`) is the single execution path: issuer check → tool contract input → budget precheck → policy.evaluate → HITL → sandbox-profile → `budget.charge_tool` + `charge_sandbox_execution` (`runtime.py:378-379`) → under `_write_lock` for writes (`_WRITE_TOOLS` = edit/write/patch/delete, `runtime.py:121,392`): `before_hash = state_hash()`; `snapshot()`; `dispatch()`; `after_hash`; `verify()`; rollback-on-fail; then hash-chained `StateTransitionRecord`.
- **State-based verification.** `StateVerifier.verify()` (`verifier.py`) re-reads/re-derives/re-runs real post-state; never trusts tool claims.
- **Snapshot/rollback + CAS.** `_WorkspaceBackend` copytree snapshot + byte rollback; `StateStore` content-addressed by `_tree_hash` == `sandbox.state_hash()`; `WorldLineForest.checkout(sandbox_factory=...)` materializes any recorded state into a fresh sandbox and proves the hash — **opt-in behind `retain_states`, which defaults `False` (`__init__.py:424`).**
- **Memory fabric.** `MemoryFabric` (`memory.py`) — 5 RAM tiers, `HashingEmbedder` (sha256 char-3gram, deterministic, stdlib), governed `request_write -> MemoryWritePolicy.evaluate_write -> _trace_memory -> append_memory_event` (`memory.py:70,215,237`). **`request_write` charges `budget.charge_memory_write()` directly and anchors ONLY a `MemoryGovernanceRecord` — it does NOT flow through `runtime.submit`, takes NO sandbox snapshot, and produces NO `StateTransitionRecord`.**
- **Memory governance.** `MemoryWritePolicy` (`memory_governance.py`) — agents cannot mint VERIFIED/PROCEDURAL/CANON; failed runs cannot create success memory; untrusted → CANDIDATE; promotion ladder gated (evidence → ≥2 distinct success traces → approval). Pure, I/O-free.
- **Budget.** `BudgetLedger` (`budget.py`) — hard multi-dimensional caps via `_check()`, trace-bound `BudgetDecisionRecord`. **`charge_llm` uses a flat `usd=0.01, estimated_tokens=1200` (`budget.py:101`) — token/cost accounting is fictional.**
- **Tool bus.** `ToolRuntime.dispatch -> ToolBus.execute` (`tools.py`) with fail-closed gates (`sandbox_policy.check_tool`, `tool_contracts.resolve_for_execution` + `ToolInputValidator`). 14 builtins. No-contract/no-registration → no execution.
- **Model plane.** `ModelRouter` (`model_router.py`) — provider failover, fail-closed local_only/remote/secret gating; `select_profile_for_task` / `profile_for_task` **built but unused by `entity.plan()`**. Anthropic/OpenAI providers **drop the API `usage` field** (`anthropic_provider.py:65-72`).
- **Skills.** `skills.py` — Voyager-style lifecycle, reflex reuse (zero-LLM path), drift demotion — precedent for governed self-improvement.
- **Praxis.** `praxis.py` — evidence-gated experience→CANDIDATE adapter (`submit_memory_candidate_to_governance`); proposal-only, **not invoked from the live loop**.

### CONTRACT-ONLY / NO-EXECUTION (sealed, structurally inert)
- `aurel_flow/*` (checkpoint/replay/reversible-state) — boundary booleans forced False by `_forbid_true`.
- `aurel_exec/*` — `ExecRuntimeBridge` submits only `read_file`; `exec_verification` forbids `verified=True` without evidence.
- `tool_manifest/*` (P1.3) — full declare→validate→quarantine→catalog→draft lifecycle, **no execution** (sealed by `test_p13_tool_manifest_layer_seal`).
- `policy_cards/memory_write.py` (P1.6.7) — 14-zone deny-by-default memory policy card, **does not enforce runtime memory**.
- `delegation/*` (P1.8) — reference-only identity mesh / chain; "ref exists ≠ resolved ≠ authorized".
- `metacognition/` — empty placeholder.

### ABSENT ENTIRELY (confirmed not on disk)
Bi-temporal/valid-time modeling; `durable_memory.py` / `DurableMemoryFabric`; typed memory graph; world-model / simulate-then-permit; MCP client/server or model tool-call loop; live A2A channel; Self-RAG loop; knowledge/intel ingestion plane.

---

## 3. Unified Build Order (dependency-ordered across all 4 tracks)

The critique's mandatory reordering is applied. **Three corrections are prerequisites to any build:** (1) fix the Track A memory-tool "double-anchor/HITL" overclaim — memory writes do not flow through `submit`; (2) make Track D external-content instruction-ineligibility **provenance-based, not scan-verdict-based**; (3) extract Track B's real-token-accounting into a **shared Phase 0 foundation** that lands before anything charges compute.

Legend: seal = independently sealable pytest file(s) proving the phase's invariants.

| Phase ID | Track | Goal | New modules | Depends on | Seal / evidence |
|---|---|---|---|---|---|
| **P0-S.1** | Shared/B | Real `TokenUsage` into ledger; kill flat 1200/0.01 estimate; `estimate_only`/`substantiated` honesty flags; distinct thinking-vs-output aggregates | `reasoning/token_accounting.py`; edits to `model_providers/base.py`,`anthropic_provider.py`,`openai_provider.py`,`budget.py` | — | `test_p650_real_token_usage.py`; `test_p650_seal.py` (usage=None ⇒ estimate_only, substantiated unconstructible-True) |
| **P0-S.2** | Shared/B+C | Shared budget seam: `charge_reasoning()` + `charge_simulation()` + caps (`max_thinking_tokens`,`max_thinking_calls`,`max_simulation_execs`) all through `_check()` | edits to `budget.py` | P0-S.1 | `test_p651_thinking_budget.py::test_charge_*_overspend_raises_and_traces_deny` |
| **P0-S.3** | Shared/P6 | Default `retain_states=ON` for a declared gated entity-class set (not globally); genesis + verified post-state commit live in factory | edits to `__init__.py`,`runtime.py` | — | `test_retain_states_gated_default.py` (off for ungated ⇒ byte-identical) |
| **A0** | A | Bi-temporal stamps on `MemoryRecord`/`MemoryGovernanceRecord` + as-of read model; **honest note: `to_dict()` gains keys, behavior byte-identical** | `memory_bitemporal.py`,`memory_asof.py`; edits `core_types.py` | — | `test_p6a0_bitemporal_seal.py` (fabric behavior identical; golden fixtures updated same commit) |
| **A1a** | A | Memory ops as governed tools — contracts + registration only; **route to existing `request_write` (single `MemoryGovernanceRecord` anchor); NO submit-pipeline claim** | `memory_tools.py`; edits `tool_contracts.py`,`tools.py` | A0, P0-S.2 | `test_p6a1_memory_tools_governed.py` (agent mem_add CANON denied; **single memory-write charge, zero sandbox-exec charge**) |
| **A1b** | A | `SideEffect.MEMORY_WRITE` risk-floor + policy re-score tuning (with policy team) | edits `tool_contracts.py`,`memory_governance.py` | A1a | `test_p6a1b_mem_risk_floor.py` |
| **A2** | A | Typed relation graph + evidence-gated supersession edges via `mem_link` | `memory_graph.py`; edits `memory.py`,`memory_governance.py` | A0, A1a | `test_p6a2_memory_graph.py` (SUPERSEDES requires evidence) |
| **A3** | A | `DurableMemoryFabric` stdlib persistence anchored to trace ids; reload re-verifies anchors, quarantines unanchored; external backend UNAVAILABLE | `durable_memory.py`,`memory_persistence.py`; edits `core_types.py` | A0, A2 | `test_p6a3_durable_memory*.py` (missing anchor quarantined; ExternalBackend unconstructible-available) |
| **B1** | B | Per-entity `ThinkingBudget` on `AgentCard` (deny-by-default → reflex) | `reasoning/thinking_budget.py`; edits `core_types.py` | P0-S.2 | `test_p651_thinking_budget.py` |
| **B2** | B | Deterministic difficulty/risk estimator (fail-closed → higher band) | `reasoning/difficulty_estimator.py`,`reasoning/difficulty_types.py` | B1 | `test_p652_difficulty.py` |
| **B3** | B | Adaptive System-1/2 router binding in `entity.plan()`; blocked-remote escalation fails closed | `reasoning/reasoning_scheduler.py`,`reasoning/reasoning_types.py`; edits `entity.py` | B2 | `test_p653_adaptive_router.py` |
| **B4** | B | Hash-chained `ReasoningAllocationRecord` trace event | edits `core_types.py`,`trace.py`,`reasoning_scheduler.py` | B3 | `test_p654_alloc_record.py` |
| **A4** | A | Belief-revision UPDATE/DELETE/FORGET as non-destructive bi-temporal supersession | `memory_revision.py`; edits `memory_tools.py`,`memory_governance.py` | A2, A3 | `test_p6a4_belief_revision.py` (FORGET forbidden on audit) |
| **A5** | A | SUMMARIZE/LINK consolidation as governed CANDIDATE writes | `memory_consolidation.py`; edits `memory_tools.py`,`praxis.py` | A2, A4, P0-S.1 | `test_p6a5_consolidation.py` (summarize ⇒ CANDIDATE only) |
| **A6** | A | Hybrid retrieval (vector+keyword+graph+temporal) + deterministic RRF; neural embedder UNAVAILABLE. **Couples to B2 memory-sparsity feature — co-update if `assemble_context` changes** | `memory_retrieval.py`,`memory_embedder.py`; edits `memory.py` | A3, A4 | `test_p6a6_hybrid_retrieval*.py` (cross-process determinism) |
| **B5** | B | Heuristic PRM step verifier + bounded LLM replan; model-judge UNAVAILABLE | `reasoning/step_verifier.py`,`reasoning/step_verifier_types.py`; edits `entity.py` | B4 | `test_p655_step_verifier.py`; `test_p655_seal.py` (PRM never recorded as verified truth) |
| **C0** | C | World-model contracts + structural no-overclaim proofs (verdict.is_authority forbidden-True) | `simgate/sim_contracts.py`,`simgate/sim_proofs.py`,`simgate/__init__.py` | — | `test_p640_sim_contracts_seal.py` |
| **C4** | C | Bounds engine (blast-radius/invariant checks), pure I/O-free logic, deny-by-default | `simgate/sim_bounds.py` | C0 | `test_p644_sim_bounds.py` |
| **C5** | C | Speculative `simulation_decision` trace append seam (non-canonical, distinct event) | `simgate/sim_records.py`; edits `trace.py` | C0 | `test_p645_sim_trace_binding.py` (not a StateTransitionRecord) |
| **C1** | C | World Model Registry seam (fail-closed resolve; visibility ≠ permission) | `simgate/world_model_registry.py`,`simgate/world_model_base.py` | C0 | `test_p641_world_model_registry_seal.py` |
| **C2** | C | Disposable state-twin over `WorldLineForest`/`StateStore`; fail-closed if base state unretained | `simgate/sim_twin.py` | C1, P0-S.3 | `test_p642_sim_twin.py` |
| **C3** | C | Simulation runner in twin scored by `StateVerifier`; **non-deterministic tools forced INCONCLUSIVE**; budget-charged | `simgate/sim_runner.py` | C2, P0-S.2 | `test_p643_sim_runner.py` (no live mutation; nondeterministic ⇒ no predicted hash) |
| **C6** | C | Gate wiring into `submit`, **default-off, SHADOW-only first** (zero behavior change) | `simgate/sim_gate.py`; edits `runtime.py` | C2,C3,C4,C5 | `test_p646_sim_gate_shadow.py` (gate-off byte-identical) |
| **A7** | A | Library / Memory Explorer projection + read-only CLI (vertical slice) | `memory_projection.py`; edits `cli.py` | A3, A6 | `test_p6a7_memory_explorer*.py` (CLI read-only) |
| **A8a** | A | Durable factory reconstruction + fail-closed in-RAM fallback | edits `__init__.py` | A5, A6, A7 | `test_p6a8_live_promotion.py::test_durable_unavailable_fails_closed_in_ram` |
| **A8b** | A | Live promotion driver + Praxis/eval candidate submission in loop | edits `runtime.py`,`evaluation/memory_candidate_bridge.py` | A8a | `test_p6a8_live_promotion.py` (two successes ⇒ procedural; failed run no promotion) |
| **C7** | C | Enforcing mode: verdict as evidence → `_simulation_blocked` / HITL escalate; influence escalation-only | edits `runtime.py`; `simgate/sim_policy_influence.py` | C6, A4/A5 | `test_p647_sim_gate_enforcing.py` (influence cannot permit) |
| **C8** | C | Counterfactual memory: governed CANDIDATE predicted-vs-actual for calibration; determinism_class tag | `simgate/sim_counterfactual.py`; edits `runtime.py` | C7, C5, A4 | `test_p648_sim_counterfactual.py` (nondeterministic excluded from calibration) |
| **C9** | C | Sim-gate projection + read-only CLI + seal (vertical slice) | `simgate/sim_projection.py`,`cli_modules/sim_gate_cli.py`,`simgate/sim_seal.py` | C6,C7,C8 | `test_p649_sim_gate_seal.py` |
| **B6** | B | HQ.Command Workload Balancer projection + read-only CLI (vertical slice) | `reasoning/workload_projection.py`; edits `cli.py`; `docs/REASONING_SCHEDULER.md` | B5 | `test_p656_workload_projection.py`; `test_p656_seal.py` |
| **D0** | D | Taint & injection-defense primitives; **instruction-ineligibility by provenance (source_kind), not scan verdict** | `external_ingress/*`,`contracts/external_ingress_v1.py` | — | `test_taint_structural_proof.py` (external-origin ⇒ never instruction); `test_injection_detector_signatures.py` |
| **D1** | D | MCP client adapter as governed Tool Bus bridge; **annotations may only ESCALATE risk**; HIGH external floor unconditional | `mcp/*`,`contracts/mcp_bridge_v1.py`; edits `tools.py`,`tool_contracts.py` | D0 | `test_bridge_registers_contract.py`; `test_mcp_output_is_tainted.py`; `test_annotation_cannot_lower_floor.py` |
| **D3** | D | Self-RAG corrective retrieval over `MemoryFabric`; external evidence ⇒ CANDIDATE only | `self_rag/*`,`contracts/self_rag_v1.py` | D0, A3 (durable candidates) | `test_corrective_reretrieval.py`; `test_external_candidate_not_canon.py` |
| **D2** | D | MCP tool-use plan steps; `PlanValidator` cross-checks live registry | `model_providers/mcp_plan_schema.py`,`plan_validator_mcp.py` | D1 | `test_plan_mcp_step_requires_registered_tool.py` |
| **D5** | D | Entity ontological state as trace projection (**kills OSP**) | `projections/entity_ontology.py`,`contracts/entity_ontology_v1.py` | D3 | `test_entity_ontology_is_pure_projection.py`; `test_no_osp_protocol.py` |
| **D6** | D | HQ.Intelligence ingestion tools (scrape/extract/monitor) + read-only CLI (vertical slice) | `tools_intel.py`,`cli_modules/mcp_a2a_intel_cli.py` | D1,D3,D5 | `test_scrape_output_is_candidate_only.py`; `test_mcp_a2a_intel_cli_readonly.py` |
| **D4** | D | A2A inbound channel — **DEAD LAST, off-by-default**, gated behind D0 seal + authority-non-expansion proof | `a2a/*`,`contracts/a2a_v1.py` | D0, D5 | `test_unresolved_sender_blocked.py`; `test_a2a_body_injection_blocked.py`; `test_a2a_authority_non_expansion.py` |

**Phase grouping (linearized, no cycles):**
- **Phase 0 (shared foundation):** P0-S.1 → P0-S.2 → P0-S.3.
- **Phase 1 (memory spine):** A0 → A1a → A1b → A2 → A3.
- **Phase 2 (parallel once Phase 0+1 exist):** B1→B2→B3→B4 concurrent with A4→A5→A6; couple B2↔A6 in lockstep on `assemble_context`.
- **Phase 3 (simulation):** C0/C4/C5 (contract-only, anytime) → C1→C2→C3→C6 (shadow) → A7→A8a→A8b → C7→C8→C9; B5, B6 land here.
- **Phase 4 (external protocols, largest attack surface, last):** D0 → D1/D3 → D2/D5/D6 → **D4 (A2A) last, off-by-default**.

---

## 4. Per-Track Detail

### Track A — Bi-temporal memory graph + memory-as-tools
**Target Aurel phase:** P6.A0–P6.A8 (P6 Durable Spine / Object Plane; depends on P5 sealed).

- **A0 — Bi-temporal stamps + as-of read model.** Modules: `memory_bitemporal.py` (`BiTemporalStamp`, `valid_at`/`known_at`/`asof`), `memory_asof.py` (`AsOfView`, `belief_history`); 6 optional default-open fields on `MemoryRecord` (`valid_from/to`, `transaction_from/to`, `superseded_by`, `revises`). Contracts: `BiTemporalStamp v1`, `AsOfView` closed-world filter. Invariants: additive-only; open interval ⇒ current (never ambiguous False); governance/storage/retrieval untouched. **Honesty:** `to_dict()` *gains keys* — golden fixtures updated in the same commit; the byte-identity claim is about fabric *behavior*, not dict shape. Tests: `test_p6a0_bitemporal_stamps.py`, `test_p6a0_bitemporal_seal.py`.
- **A1a — Memory ops as governed tools (contracts + registration).** Modules: `memory_tools.py` (`mem_add/update/delete/search/link` handlers that call `fabric.request_write/promote/retrieve`, never store directly), contracts in `tool_contracts.py`, registration in `tools.py`. **Corrected invariant (was an overclaim):** memory writes route through the *existing* `request_write -> _trace_memory` funnel and anchor a **single `MemoryGovernanceRecord`**. They do **NOT** flow through `runtime.submit`, take **no** sandbox snapshot, and produce **no** `StateTransitionRecord`; there is **no** HITL/double-anchor claim. This is already governed and fail-closed. **Budget:** exactly one charge site — `charge_memory_write` — and `charge_sandbox_execution` is suppressed for the `mem_*` tool class (seal test: single mem_add ⇒ memory-write once, sandbox-exec zero). `mem_search` is read-only. Tests: `test_p6a1_memory_tools_governed.py`.
- **A1b — Risk-floor tuning.** `SideEffect.MEMORY_WRITE` floor + policy re-score, decoupled from A1a so the governance-surface change seals independently with the policy team.
- **A2 — Typed relation graph.** `memory_graph.py` (`MemoryEdge` bi-temporal, `MemoryGraphIndex`, `detect_supersession_chain`); `evaluate_link` in `memory_governance.py`. Invariants: edges are governed writes; SUPERSEDES/CONTRADICTS evidence-gated; append-only; `MemoryTier`/`MemoryTruthState` dual maps untouched.
- **A3 — DurableMemoryFabric.** `durable_memory.py` (overrides `_store/_relocate/link_records`; `load()`/`save()` re-verify `source_trace_ids` against bound trace, quarantine unanchored), `memory_persistence.py` (`FileMemoryBackend` JSONL + `os.replace` atomic, one version per `(memory_id, transaction_from)`; `ExternalMemoryBackend` all-UNAVAILABLE), `DurableMemoryGovernanceRecord`. Invariants: persistence is a projection over the trace; append-only versions; crash-safe; determinism preserved.
- **A4 — Belief revision.** `memory_revision.py` (`apply_update/retract/forget` → governed requests); `mem_forget` marks retention only, never pops `by_id` or deletes versions; `evaluate_retention` forbids FORGET on audit (rejected/canon/policy). Non-destructive; as-of-past returns pre-revision belief.
- **A5 — Consolidation.** `memory_consolidation.py` (deterministic clustering → CANDIDATE + SUMMARIZES edges); routes Praxis multi-record experiences through `mem_summarize`. Never auto-canonizes; provenance preserved.
- **A6 — Hybrid retrieval.** `memory_retrieval.py` (vector cosine + stdlib BM25-lite + graph expansion + as-of filter + deterministic RRF sorted by `(score, memory_id)`); `memory_embedder.py` `NeuralEmbedderSeam` UNAVAILABLE. **Cross-track lockstep:** if `assemble_context` signature/behavior changes, Track B's B2 memory-sparsity feature co-updates.
- **A7 — Memory Explorer projection + CLI.** `memory_projection.py` (rebuilt only from trace memory-governance events + durable store); `aurel memory explore/history/graph/rejected` read-only. Projection-over-trace; no mutation from CLI.
- **A8a / A8b — Live wiring (split).** A8a: durable factory reconstruction with fail-closed in-RAM fallback. A8b: `_record_command_memory` submits Praxis/eval candidates and drives evidence-gated promotions. Promotion monotonicity preserved; cross-run learning durable-and-honest.

**UNAVAILABLE seams (Track A):** `ExternalMemoryBackend` (future object-plane / external durable store) — success booleans unconstructible; `NeuralEmbedderSeam` (future stronger embedder) — `embed()` raises; graph/version compaction retention-class policy — deferred (FORGET is retention-only, never erases audit).

---

### Track B — Reasoning scheduler + per-entity thinking budget
**Target Aurel phase:** P6.5.x, after P5 seal, parallel with P6 Durable Spine.

- **P0-S.1 (shared) — Truthful token accounting.** `TokenUsage.reasoning_tokens`; `ModelRequest.reasoning_effort` (request-only, providers may ignore); populate `ModelResponse.usage` from real Anthropic/OpenAI payloads; **usage absent ⇒ `usage=None`, charge stamped `estimate_only=True`, never synthesize a number.** `charge_llm(usage=...)` overload charges real prompt+completion to `estimated_tokens` and reasoning to a distinct `thinking_tokens` aggregate. `reasoning/token_accounting.py` `TokenAccountingView.substantiated` unconstructible-True without a usage-bearing response.
- **P0-S.2 (shared) — Budget seams.** `charge_reasoning()`, `charge_simulation()`, caps `max_thinking_tokens`/`max_thinking_calls`/`max_reasoning_passes_per_run`/`max_simulation_execs`, all through `_check()` → `BudgetExceeded` + `BudgetDecisionRecord`.
- **B1 — ThinkingBudget.** `reasoning/thinking_budget.py` (effort_ceiling reflex<low<medium<high, allowed_profile_tiers, max passes/tokens/calls); `AgentCard.thinking_budget` conservative default. Deny-by-default: unknown effort → reflex; missing budget → conservative, never unlimited. `clamp()` returns provably ≤ ceiling.
- **B2 — Difficulty estimator.** `reasoning/difficulty_estimator.py` deterministic features (risk, constraints, goal length, reflex-availability via real `skills.find_reflex` probe, memory-context sparsity, write-verbs) → band. Fail-closed: ambiguous input biases *higher*. Advisory only; emits no command.
- **B3 — Adaptive router binding.** `reasoning/reasoning_scheduler.py` chooses profile via `router.select_profile_for_task` + effort, clamped by ThinkingBudget, charges `charge_reasoning` before the call. Fail-closed escalation: blocked remote → surface `refusal_json`, never silent downgrade-then-claim-System-2. `PlanValidator` still sole gate.
- **B4 — ReasoningAllocationRecord.** `core_types.py` record (mirrors `BudgetDecisionRecord`) + `trace.append_reasoning_allocation`. Canonical-in-trace; safe category summaries only (no raw CoT); refusals recorded not dropped.
- **B5 — PRM step verifier.** `reasoning/step_verifier.py` deterministic per-step scoring → `should_escalate` → bounded LLM replan (charged, capped by `max_reasoning_passes`), re-run through `PlanValidator`. `model_judge_available` structurally False; PRM verdict never recorded as verified truth (StateVerifier remains sole truth source).
- **B6 — Workload Balancer projection + CLI.** `reasoning/workload_projection.py` pure fold over `ReasoningAllocationRecord` + `BudgetDecisionRecord`; propagates `estimate_only`/`substantiated`. Read-only; grants no allocation/execution.

**UNAVAILABLE seams (Track B):** model-judge PRM verifier (`forbid_true` guard, awaits router/budget/contract canon); learned allocation policy / self-model in empty `metacognition/` (P7+); provider-native `reasoning_effort` honoring beyond passthrough.

---

### Track C — Simulation-gated action via lightweight world model
**Target Aurel phase:** P6.4.x, after P6 Durable Spine primitives.

- **C0 — Contracts + proofs.** `simgate/sim_contracts.py` (`SimulationRequest`, `WorldModelPrediction`, `SimulationBoundsCheck`, `SimulationVerdict`), `simgate/sim_proofs.py` (`_forbid_true`/`_forbid_false`). Invariants: `SimulationVerdict.is_authority` structurally False; `requires_real_execution`/`is_speculative` forced; a non-PREDICTED prediction cannot carry `predicted_after_state_hash`.
- **C1 — World Model Registry.** `world_model_registry.py` (`resolve` → RESOLVED / NO_MODEL / ENTITY_CLASS_UNKNOWN, fail-closed), `world_model_base.py` (`WorldModel` Protocol: predict+healthcheck only; `NullWorldModel` → INCONCLUSIVE). Visibility ≠ permission.
- **C2 — Disposable twin.** `sim_twin.py` materializes base state via `StateStore.materialize` into a fresh sandbox, asserts `state_hash == base_state_hash`, fails closed TWIN_UNAVAILABLE if base not retained. **Depends on P0-S.3 (retain_states gated-on).** Never the live workspace, never host-level.
- **C3 — Simulation runner.** `sim_runner.py` runs candidate in twin, scores with `StateVerifier`, budget-charged via `charge_simulation`. **Corrected invariant:** tools whose `ToolContract` declares non-deterministic side effects (run_shell/run_tests/network_fetch) are **structurally forced to `prediction_status=INCONCLUSIVE` in `__post_init__`** — no `predicted_after_state_hash` for them (a second random sample is not a prediction). Only deterministic filesystem-effect tools carry a predicted hash. Prediction never recorded as verified truth.
- **C4 — Bounds engine.** `sim_bounds.py` pure I/O-free (blast-radius ceiling, protected-path deletion, canonical-path constraints, side-effect floor). Deny-by-default for INCONCLUSIVE/UNAVAILABLE on writes. Evidence, not authority.
- **C5 — Trace seam.** `sim_records.py` `SimulationDecisionRecord` (`event_type='simulation_decision'`, `is_speculative=True` structural) + `trace.append_simulation_event` hash-chained. Never a `StateTransitionRecord`.
- **C6 — Gate wiring, SHADOW-only, default-off.** `sim_gate.py` + `runtime.py` flags after budget charge, before the `with lock: snapshot()` block. Gate-off ⇒ byte-identical pipeline; shadow ⇒ emits `simulation_projection` artifact + trace event, never blocks.
- **C7 — Enforcing mode.** `_simulation_blocked` (mirrors `_sandbox_blocked`) + `sim_policy_influence.py`. Influence **escalation-only** (`influence_is_escalation_only` forbid-False) — can deny/require-approval/raise-risk, never permit or lower risk. UNAVAILABLE twin on a write ⇒ fail closed. Blocked-by-sim still emits a canonical BLOCKED transition cross-linked to the speculative record.
- **C8 — Counterfactual memory.** `sim_counterfactual.py` computes `prediction_hit` from two real `_tree_hash`es, submits governed CANDIDATE via `request_write` (never auto-VERIFIED/CANON). Failed runs cannot mint success calibration memory. `determinism_class` tag excludes non-deterministic classes from calibration.
- **C9 — Projection + CLI + seal.** `sim_projection.py`, `cli_modules/sim_gate_cli.py` (read-only), `sim_seal.py`.

**UNAVAILABLE seams (Track C):** CoW/incremental twin snapshots (current whole-tree copytree is the cost bottleneck); rich per-domain world models beyond twin-dispatch/identity predictor; external-side-effect prediction (network/shell stay INCONCLUSIVE by design); automatic model calibration/update from counterfactual memory (separate governed act); re-homing the gate into `aurel_exec.ExecRuntimeBridge` as a P4 admission decision.

---

### Track D — MCP/A2A native + self-correcting RAG
**Target Aurel phase:** P7.x, after P6 Durable Spine.

- **D0 — Taint & injection defense.** `external_ingress/taint.py` (`TaintedContent` + `source_kind` + `TaintLabel`), `injection_detector.py` (deterministic stdlib signatures), `sanitization.py` (`SanitizationCrossing`), `contracts/external_ingress_v1.py`. **Corrected doctrine (was a heuristic-as-structural overclaim):** instruction-eligibility is forbidden **by provenance, not by scan verdict.** There is **no constructor anywhere** that turns external-origin content (`source_kind` ∈ {mcp_tool, a2a_message, network_fetch, scrape}) into a plan/instruction, regardless of a "clean" scan. The only instruction source is model output through `PlanValidator`. The detector is defense-in-depth for the **data** channel; a `SANITIZED` label makes content usable as *data*, never as instruction. Quarantined content retained (audit), never dropped.
- **D1 — MCP client bridge.** `mcp/jsonrpc.py` (stdlib JSON-RPC 2.0), `mcp/transport.py` (subprocess stdio in-sandbox / urllib http, timeouts + byte caps), `mcp/client.py` (output wrapped as `TaintedContent(source_kind=mcp_tool)`), `mcp/bridge.py` (each MCP tool → `ToolSpec` + `ToolContract`). **Corrected doctrine:** server-supplied annotations may only **ESCALATE** risk — every bridged MCP tool gets a HIGH external/network floor unconditionally; a malicious `side_effect=read` annotation on a writing tool cannot lower the floor (seal test). No-contract/no-registration ⇒ no execution; manifest P1.3 seal untouched (this is a new layer).
- **D2 — MCP plan steps.** `mcp_plan_schema.py` (STRUCTURED_PLAN_SCHEMA v2, backward-compatible), `plan_validator_mcp.py` cross-checks the live registry; unregistered MCP tool reference fails closed at validation. Model still only proposes.
- **D3 — Self-RAG.** `self_rag/retrieval_critic.py` (deterministic relevance/support/sufficiency), `query_rewrite.py`, `loop.py` (bounded rounds, budget-charged, PARTIAL/UNAVAILABLE when weak — never fabricated), `candidate_ingest.py` (external evidence ⇒ CANDIDATE via `request_write` only). **Depends on A3** for durable candidates (RAM-only until then, declared UNAVAILABLE seam).
- **D5 — Entity ontology projection (kills OSP).** `projections/entity_ontology.py` folds `StateTransitionRecord` + `MemoryGovernanceRecord` + delegation refs + budget/verifier records into `EntityOntologyView`. Projection-only, no new source of truth, no wire protocol; truth label = MIN of underlying records.
- **D6 — Intel ingestion tools + CLI.** `tools_intel.py` (scrape/extract/monitor, network_fetch discipline, output tainted → Self-RAG CANDIDATE), `cli_modules/mcp_a2a_intel_cli.py` (read-only). Vertical slice complete.
- **D4 — A2A inbound (DEAD LAST, off-by-default).** `a2a/message.py` (body tainted), `a2a/inbound.py` (resolve mesh ref → injection scan → authorized-only `CommandEnvelope` to `runtime.submit`), `board_dispatch.py`, `contracts/a2a_v1.py`. **Gated behind D0 sealed AND an explicit authority-non-expansion proof** (A2A can never widen capability beyond pre-existing delegation grants). Resolved-but-unauthorized ⇒ BLOCKED + non-repudiation record + zero sandbox entry. Off-by-default like Track C's gate.

**UNAVAILABLE seams (Track D):** durable cross-run RAG learning (until A3); MCP server-side hosting; native provider function-calling that executes (kept as plan proposals only); external tool attestation beyond quarantine.

---

## 5. Cross-Cutting Invariants (every phase must hold)

1. **Entity proposes, runtime disposes.** Every new capability reduces to a `CommandEnvelope` through `AgenticRuntime.submit`, a governed `MemoryFabric.request_write`, or a read-only projection. No second executor is introduced (respects the `aurel_exec` single-executor law and the `tool_manifest` P1.3 no-execution seal).
2. **Trace is the single source of truth.** Every mutation emits a hash-chained record into the AurelTraceLog (`StateTransitionRecord` / `MemoryGovernanceRecord` / `BudgetDecisionRecord` / new `ReasoningAllocationRecord` / new speculative `simulation_decision` / non-repudiation records). Durable stores, projections, and read-models are projections over the trace; if it is not in the trace it is not canonical. Speculative simulation records are distinctly labeled and never canonical transitions.
3. **Fail-closed / no silent fallback.** Unknown inputs, unresolved refs, unbuildable twins, absent usage, weak retrievals, and blocked remote escalations DENY, escalate, or report honest UNAVAILABLE/PARTIAL/BLOCKED — never a silent allow or a fabricated value.
4. **No-overclaim (structural, not heuristic).** Booleans that would lie are unconstructible: `SimulationVerdict.is_authority`, `TokenAccountingView.substantiated`, `ExternalMemoryBackend` success, `NeuralEmbedderSeam.embed`, `model_judge_available`, external-origin `→ instruction`. Truth labels (TRACE_BOUND < TRACE_INTEGRITY_VERIFIED < TRACE_VERIFIED) gate and propagate as MINs.
5. **Governance is layered on, never around.** `MemoryWritePolicy` gates all writes; the candidate→verified→procedural→canon ladder is untouched; agents cannot mint VERIFIED/PROCEDURAL/CANON; failed runs cannot create success memory; risk floors only escalate.
6. **Budget honesty is load-bearing.** No phase charges compute before P0-S.1 lands; every compute charge routes through `_check()`; overspend raises `BudgetExceeded`; estimated figures are flagged `estimate_only` and never presented as measured.
7. **Determinism / stdlib-only.** `HashingEmbedder` (sha256) stays the only real embedder; all fusion/reranking/detectors/critics are deterministic (sorted by `(score, id)`, never Python `hash()`); persistence reuses `state_store` atomic-rename crash-safety; JSON-RPC/A2A ride stdlib transport. Replay fidelity preserved; no runtime deps.
8. **No hidden chain-of-thought.** Only safe category summaries are stored (honoring `flow_pause_hooks` HIDDEN_COT boundary); raw reasoning is never captured into trace records.
9. **Additive-behind-flags.** Every gate/backend defaults off (or gated to declared entity classes); the ephemeral write path stays byte-for-byte unchanged when disabled (M0/M1 discipline).

---

## 6. Risks & Mitigations (critique folded in)

| Risk | Severity | Mitigation |
|---|---|---|
| **A1 double-anchor/HITL overclaim** — memory writes do not flow through `submit`; no `StateTransitionRecord` | High | **Corrected in plan.** Keep memory on `request_write -> _trace_memory` (single `MemoryGovernanceRecord`); drop all submit-pipeline/double-anchor/HITL claims; state the funnel honestly. |
| **Budget double-charge** on mem tools (tool dispatch + memory-write) | Medium | Exactly one charge site: `charge_memory_write`; suppress `charge_sandbox_execution` for `mem_*` class; seal test (memory-write once, sandbox-exec zero). |
| **Flat 1200-token estimate is a shared silent overclaim** across all four tracks | High | **P0-S.1 promoted to shared foundation, lands globally first.** Every compute-charging phase `dependsOn` it. |
| **Track C twin needs `retain_states` (defaults False)** | High | P0-S.3 defaults `retain_states=ON` for declared gated entity classes only; ungated path byte-identical; twin fails closed TWIN_UNAVAILABLE otherwise. |
| **`charge_simulation` missing** (C3 depends on B) | High | Added to shared P0-S.2 before C3; landing C's runner before it is a no-overclaim violation. |
| **Non-deterministic tool "prediction"** poisons calibration | Medium | Structurally force `INCONCLUSIVE` for nondeterministic side-effect classes in `sim_runner.__post_init__`; `determinism_class` tag excludes them from calibration. |
| **Injection detector false negatives** presented as structural impossibility | High | **Corrected:** instruction-ineligibility is provenance-based (`source_kind` external ⇒ never instruction); detector is data-channel defense-in-depth only, never an instruction gate. |
| **Attacker-supplied MCP annotations** set risk floor | Medium | Annotations may only escalate; unconditional HIGH external floor; seal test that `side_effect=read` cannot lower a writing tool's floor. |
| **A2A inbound = largest new attack surface** (remote-triggered submits) | Medium | D4 dead last, off-by-default, gated behind D0 seal + authority-non-expansion proof + D5 projection for audit; unauthorized ⇒ BLOCKED + non-repudiation + zero sandbox entry. |
| **`to_dict()` shape drift** breaks golden fixtures | Low | Honest invariant: behavior byte-identical, `to_dict` *gains keys*; grep + update all `MemoryRecord` golden fixtures in the A0 commit. |
| **B2↔A6 lockstep** on `assemble_context` | Low | Explicit cross-track coupling; co-update the memory-sparsity feature if the signature changes. |
| **Graph/version unbounded growth** | Medium | FORGET is retention-only (never erases audit); a separate governed compaction/retention-class policy is a deferred UNAVAILABLE seam. |
| **Twin cost O(tree) per write** when enforcing | Medium | Gate default-off; scope enforcing to declared high-risk classes; CoW/incremental snapshot left UNAVAILABLE. |

---

## 7. Explicitly OUT OF SCOPE / Anti-Hype

- **No proprietary wire protocol.** MCP/A2A are adopted as JSON shapes over stdlib transport. The "OSP" ontological-state protocol is **killed** and replaced by a trace projection. No new source of truth is introduced anywhere.
- **No model scaling / no neural embeddings / no external vector DB.** `HashingEmbedder` (sha256) remains the only real embedder; `NeuralEmbedderSeam` is UNAVAILABLE. Stronger models are a *routing* choice within existing fail-closed provider gating, not a new dependency.
- **No benchmark suite / no capability leaderboards.** Evidence is seal tests + trace reproducibility, not eval scores. Prediction fidelity is honestly bounded (filesystem effects only; network/shell INCONCLUSIVE by design).
- **No auto-canonization.** Nothing retrieved, scraped, summarized, or simulated becomes CANON without the approval gate. Consolidation, Self-RAG, and counterfactual memory produce CANDIDATES only.
- **No auto-model-update.** Counterfactual calibration data is stored as governed evidence; any world-model update is a separate governed act (Praxis discipline: produces candidates, nothing auto-promotes).
- **No native provider function-calling that executes.** Model tool-use remains *proposals* validated by `PlanValidator`.
- **No hidden reasoning capture.** Extended-thinking is a request parameter and a budget aggregate, not a CoT store.
- **No governance weakening for speed.** Hard-isolation backends are never silently downgraded; risk floors only escalate; the ephemeral path is byte-identical when flags are off.

---

## 8. First Concrete PR — Smallest Sealable Slice

**PR title:** `P0-S.1: truthful token/cost accounting (kill the flat 1200-token estimate)`

This is the honesty keystone the entire plan rests on, has **no dependencies**, touches the smallest surface, and unblocks every compute-charging phase in all four tracks.

**Scope (modules):**
- `src/agentic_runtime/model_providers/base.py` — add `TokenUsage.reasoning_tokens` (default 0); add `ModelRequest.reasoning_effort: str = "auto"` (request-only, no execution semantics).
- `src/agentic_runtime/model_providers/anthropic_provider.py` — populate `ModelResponse.usage` from the real API `usage` payload (`input_tokens`/`output_tokens`, thinking tokens when present); **usage absent ⇒ `usage=None`, never synthesize.**
- `src/agentic_runtime/model_providers/openai_provider.py` — same; map `completion_tokens_details.reasoning_tokens` when present, else 0.
- `src/agentic_runtime/budget.py` — `charge_llm(usage: TokenUsage | None = None, usd: float | None = None)`: real tokens → `estimated_tokens`, reasoning → distinct `thinking_tokens` aggregate; `usage=None` keeps the legacy estimate but stamps `estimate_only=True`; add `thinking_tokens`/`output_tokens` to `snapshot()`. All charges still route through `_check()`.
- `src/agentic_runtime/reasoning/__init__.py` — package root (docstring: proposal-only, allocation ≠ authority).
- `src/agentic_runtime/reasoning/token_accounting.py` — `TokenAccountingView` read-model splitting a snapshot into thinking/output/prompt with `estimate_only`; `substantiated` unconstructible-True without a usage-bearing `ModelResponse`.

**Tests (seal):**
- `tests/test_p650_real_token_usage.py::test_anthropic_usage_populates_ledger_not_flat_estimate`
- `tests/test_p650_real_token_usage.py::test_missing_usage_marks_estimate_only_and_substantiated_false`
- `tests/test_p650_real_token_usage.py::test_reasoning_tokens_charged_distinct_from_output_tokens`
- `tests/test_p650_real_token_usage.py::test_thinking_token_overspend_raises_BudgetExceeded_via_check`
- `tests/test_p650_seal.py::test_reasoning_effort_field_grants_no_execution_power`

**Why this first:** it is fully additive (mock provider still returns deterministic/None usage, so the existing ~8434-test suite stays green), it converts the largest existing silent overclaim (fictional flat cost) into an honest, substantiated-or-flagged figure, and every subsequent phase that charges reasoning, simulation, or retrieval compute can then `dependsOn` a ledger that tells the truth. Ship this, then P0-S.2 (`charge_reasoning`/`charge_simulation` seams) and P0-S.3 (`retain_states` gated-on), before opening the Track A memory spine.
