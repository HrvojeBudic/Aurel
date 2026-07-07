# AUREL — Master-Plan Continuation & Dispatch Plan (Tracks A / B / C / D)

**Date:** 2026-07-07
**Status:** LIVE plan — pick up here next session
**Source master plan:** `~/Desktop/ui/AUREL UPGRADE MASTER PLAN.txt`
**This block sealed in `master`:** merge `f0c02ad` (report `agent/reports/AUREL_DUAL_KERNEL_TRACKB.md`); full suite 8535 passed / 11 skipped / 0 failed.

---

## 0. How to use this (next session)

- Each remaining phase below is a **self-contained dispatch unit**: it lists the
  new/edited files, the flag, the seal test, the no-collapse invariants, and a
  **paste-ready dispatch prompt**.
- Work **one phase at a time**, in the sequence of §4. After each phase: `ruff` +
  `mypy` on touched modules, the phase seal test, then a focused regression slice;
  run the **full suite** (`AGENTIC_SKIP_RECURSIVE_SMOKE=1 .venv/bin/python -m pytest
  -q -p no:cacheprovider`, ~30 min, background) before merging a track.
- **Cross-cutting law for every phase** (see §5): additive-behind-flags (default
  OFF ⇒ byte-identical), entity-proposes/runtime-disposes, trace = single source of
  truth, fail-closed, no-overclaim (booleans that would lie are unconstructible).
- Branch per track: `feat/track-a-memory`, `feat/track-c-simgate`, `feat/track-d-mcp`.

---

## 1. Current state (canonical in `master`)

**Done + sealed:**
- **Dual kernel** (`src/agentic_runtime/dual_kernel/`, flags `AUREL_DUAL_KERNEL`,
  `AUREL_DK_MATERIALIZE`): Σ vector, routing, constraints, merge gate (ABC C1–C4 +
  Book 12 ladder), NC firewall, Praxis, facade, decision ledger, CLI, CAS
  materialize-to-live. This already implements the **substance of Track C C1–C5**
  (disposable twin, StateVerifier scoring, speculative verdict, simulation_decision
  trace evidence).
- **Phase 0** (foundation): P0-S.1 truthful token accounting (`reasoning/`,
  `budget.charge_llm(usage)`, `model_router.complete_with_usage`, `entity.plan`
  live-wired), P0-S.2 `charge_reasoning`/`charge_simulation` + caps, P0-S.3
  `retain_states` gated default (`build_runtime(entity_class=…)`).
- **Track B COMPLETE** (`reasoning/`, flag `AUREL_REASONING_SCHEDULER`): B1 thinking
  budget, B2 difficulty estimator, B3 adaptive allocation in `entity.plan`, B4
  `reasoning_allocation` trace event, B5 PRM step verifier + bounded replan, B6
  workload projection + `reasoning` CLI.

**Key existing modules to build on (grounded):**
- Memory: `memory.py` (MemoryFabric, HashingEmbedder, `request_write` →
  `MemoryWritePolicy.evaluate_write` → `_trace_memory` → `append_memory_event`,
  `assemble_context`), `memory_governance.py`, `core_types.MemoryRecord` /
  `MemoryGovernanceRecord` / `MemoryTier` / `MemoryTruthState`.
- State: `state_store.py` (CAS: `put`/`materialize`/`has`), `worldline.py`
  (WorldLineForest fork/merge/checkout).
- Tools: `tools.py` (ToolRuntime/ToolBus), `tool_contracts.py`
  (ToolContractRegistry, `resolve_for_execution`, ToolInputValidator).
- Model/trace: `model_router.py`, `trace.py` (hash-chained; append_* methods;
  `PraxisEventRecord` is the reusable proposal-side event).
- Runtime: `runtime.py` (`AgenticRuntime.submit`, `_append_transition`,
  `_state_store`), `entity.py` (`plan`, reasoning binding).

---

## 2. Remaining work (all tracks)

| Track | Remaining phases | Size | Risk |
|-------|------------------|------|------|
| **A — Bi-temporal memory + memory-as-tools** | A0, A1a, A1b, A2, A3, A4, A5, A6, A7, A8a, A8b | Large | Med (memory funnel is governed already) |
| **C — Simulation-gated action** | C6 (shadow), C7 (enforcing), C8 (counterfactual), C9 (projection); optional C0–C4 formal contracts | Med | High (C6/C7 touch `runtime.submit` hot path) |
| **D — MCP/A2A + Self-RAG** | D0, D1, D2, D3, D5, D6, D4 | Large | High (largest external attack surface; A2A last) |
| **Misc** | materialize budget/memory mirror; coverage+bandit seal | Small | Low |

---

## 3. Per-phase dispatch specs

> Legend: **Files** = new / edited. **Flag** default OFF. **Seal** = pytest file.
> **NC** = no-collapse invariants that must hold. Reuse `PraxisEventRecord` for new
> trace events unless a dedicated record type is explicitly wanted (avoids
> trace-serialization surgery — note the persistent replay flattens praxis events
> and drops `details`, keeping only the `k=v` summary, so encode key fields there).

### Track A — Bi-temporal memory graph + memory-as-tools (flag `AUREL_DURABLE_MEMORY`)

**A0 — Bi-temporal stamps + as-of read model.**
Files: new `memory_bitemporal.py` (`BiTemporalStamp`: valid_from/to, transaction_from/to), `memory_asof.py` (`AsOfView`, `belief_history`); edit `core_types.MemoryRecord` add 6 optional default-open fields (superseded_by, revises, valid_/transaction_ ranges). NC: additive-only; open interval ⇒ current; governance/storage/retrieval untouched. **Honesty:** `to_dict()` gains keys ⇒ update MemoryRecord golden fixtures in the SAME commit (grep tests for MemoryRecord dict asserts first). Seal: `test_p6a0_bitemporal_seal.py` (fabric behavior byte-identical).

**A1a — Memory ops as governed tools.**
Files: new `memory_tools.py` (`mem_add/update/delete/search/link` handlers calling `fabric.request_write`/`promote`/`retrieve` — NEVER store directly); edit `tool_contracts.py` (contracts), `tools.py` (registration). NC: memory writes route through the EXISTING `request_write → _trace_memory` funnel and anchor a SINGLE `MemoryGovernanceRecord` — they do NOT flow through `runtime.submit`, take no sandbox snapshot, produce no StateTransitionRecord (do not claim HITL/double-anchor). Budget: exactly one charge site `charge_memory_write`; suppress `charge_sandbox_execution` for the `mem_*` class. `mem_search` read-only. Seal: `test_p6a1_memory_tools_governed.py` (agent `mem_add` CANON denied; one memory-write charge, zero sandbox-exec charge).

**A1b — MEMORY_WRITE risk floor.** Files: edit `tool_contracts.py`, `memory_governance.py` (SideEffect.MEMORY_WRITE floor + policy re-score). Seal: `test_p6a1b_mem_risk_floor.py`. Decoupled from A1a so it seals with the policy surface independently.

**A2 — Typed relation graph.** Files: new `memory_graph.py` (`MemoryEdge` bi-temporal, `MemoryGraphIndex`, `detect_supersession_chain`); edit `memory.py`, `memory_governance.py` (`evaluate_link`). NC: edges are governed writes; SUPERSEDES/CONTRADICTS evidence-gated; append-only. Seal: `test_p6a2_memory_graph.py` (SUPERSEDES requires evidence).

**A3 — DurableMemoryFabric.** Files: new `durable_memory.py` (overrides store/relocate/link; `load()`/`save()` re-verify `source_trace_ids` against the bound trace, quarantine unanchored), `memory_persistence.py` (`FileMemoryBackend` JSONL + `os.replace` atomic; `ExternalMemoryBackend` all-UNAVAILABLE unconstructible-available); edit `core_types` (`DurableMemoryGovernanceRecord`). NC: persistence is a projection over the trace; append-only versions; determinism preserved. Seal: `test_p6a3_durable_memory*.py` (missing anchor quarantined; ExternalBackend unconstructible-available).

**A4 — Belief revision.** Files: new `memory_revision.py` (`apply_update/retract/forget` → governed requests); edit `memory_tools.py`, `memory_governance.py`. NC: non-destructive; `mem_forget` marks retention only (never pops/deletes versions); FORGET forbidden on audit (rejected/canon/policy); as-of-past returns pre-revision belief. Seal: `test_p6a4_belief_revision.py`.

**A5 — Consolidation.** Files: new `memory_consolidation.py` (deterministic clustering → CANDIDATE + SUMMARIZES edges); edit `memory_tools.py`, `praxis.py`. NC: never auto-canonizes; summarize ⇒ CANDIDATE only; provenance preserved. Seal: `test_p6a5_consolidation.py`.

**A6 — Hybrid retrieval.** Files: new `memory_retrieval.py` (vector cosine + stdlib BM25-lite + graph expansion + as-of filter + deterministic RRF sorted by `(score, memory_id)`), `memory_embedder.py` (`NeuralEmbedderSeam` UNAVAILABLE — `embed()` raises). Edit `memory.py`. **Cross-lock:** if `assemble_context` signature/behavior changes, co-update Track B's B2 memory-sparsity feature (`difficulty_estimator`). Seal: `test_p6a6_hybrid_retrieval*.py` (cross-process determinism).

**A7 — Memory Explorer projection + CLI.** Files: new `memory_projection.py` (rebuilt only from trace memory-governance events + durable store); edit `cli.py` (`memory explore/history/graph/rejected`, read-only). Mirror the `reasoning`/`dual-kernel` CLI pattern. Seal: `test_p6a7_memory_explorer*.py`.

**A8a — Durable factory + fail-closed fallback.** Files: edit `__init__.py` (`build_runtime` reconstructs durable fabric; fails closed to in-RAM). Seal: `test_p6a8_live_promotion.py::test_durable_unavailable_fails_closed_in_ram`.

**A8b — Live promotion driver.** Files: edit `runtime.py` (`_record_command_memory` submits Praxis/eval candidates), `evaluation/memory_candidate_bridge.py`. NC: promotion monotonicity; two successes ⇒ procedural; failed run ⇒ no promotion. Seal: `test_p6a8_live_promotion.py`.

### Track C — Simulation-gated action (remaining; flag `AUREL_SIM_GATE`)

> C1–C5 substance already exists in the dual kernel. These wire it into the
> canonical `runtime.submit` path as EVIDENCE (never authority), shadow first.

**C6 — Gate wiring, SHADOW-only, default-off.** Files: new `simgate/sim_gate.py`; edit `runtime.py` (flags after budget charge, before the `with _write_lock: snapshot()` block). NC: gate-off ⇒ **byte-identical** pipeline; shadow ⇒ emits `simulation_decision` evidence + projection artifact, **never blocks**. Reuse the dual-kernel merge-gate to produce the verdict; charge via `charge_simulation`. Seal: `test_p646_sim_gate_shadow.py` (gate-off byte-identical).

**C7 — Enforcing mode.** Files: edit `runtime.py` (`_simulation_blocked` mirroring `_sandbox_blocked`), new `simgate/sim_policy_influence.py`. NC: influence **escalation-only** (`influence_is_escalation_only` forbid-False) — can deny / require-approval / raise-risk, NEVER permit or lower risk; UNAVAILABLE twin on a write ⇒ fail closed; blocked-by-sim still emits a canonical BLOCKED transition cross-linked to the speculative record. Seal: `test_p647_sim_gate_enforcing.py` (influence cannot permit).

**C8 — Counterfactual calibration memory.** Files: new `simgate/sim_counterfactual.py`; edit `runtime.py`. NC: `prediction_hit` from two real `_tree_hash`es → governed CANDIDATE via `request_write` (never auto-VERIFIED/CANON); failed runs cannot mint success calibration; `determinism_class` tag excludes non-deterministic tool classes. Seal: `test_p648_sim_counterfactual.py`.

**C9 — Projection + CLI + seal.** Files: new `simgate/sim_projection.py`, `cli_modules/sim_gate_cli.py` (read-only), `simgate/sim_seal.py`. Seal: `test_p649_sim_gate_seal.py`.

*(Optional formalization C0–C4: dedicated `simgate/sim_contracts.py` + `_forbid_true/_forbid_false` proofs, world-model registry, explicit `sim_bounds.py`. Only if a distinct sim-gate surface separate from the dual kernel is wanted.)*

### Track D — MCP/A2A native + Self-RAG (flag per surface; A2A dead-last, default-off)

**D0 — Taint & injection defense (FIRST, no deps).** Files: new `external_ingress/taint.py` (`TaintedContent` + `source_kind` + `TaintLabel`), `injection_detector.py` (deterministic stdlib signatures), `sanitization.py` (`SanitizationCrossing`), `contracts/external_ingress_v1.py`. **Doctrine (structural, not heuristic):** instruction-eligibility is forbidden by PROVENANCE — no constructor turns external-origin content (`source_kind ∈ {mcp_tool, a2a_message, network_fetch, scrape}`) into a plan/instruction, regardless of a "clean" scan; the only instruction source is model output through PlanValidator. Detector is data-channel defense-in-depth. Quarantined content retained. Seal: `test_taint_structural_proof.py`, `test_injection_detector_signatures.py`.

**D1 — MCP client bridge.** Files: new `mcp/jsonrpc.py` (stdlib JSON-RPC 2.0), `mcp/transport.py` (subprocess stdio in-sandbox / urllib http, timeouts + byte caps), `mcp/client.py` (output wrapped `TaintedContent(source_kind=mcp_tool)`), `mcp/bridge.py` (each MCP tool → `ToolSpec` + `ToolContract`); edit `tools.py`, `tool_contracts.py`, `contracts/mcp_bridge_v1.py`. NC: server annotations may only ESCALATE risk — every bridged tool gets an unconditional HIGH external/network floor; a malicious `side_effect=read` annotation on a writing tool cannot lower the floor. No-contract/no-registration ⇒ no execution (P1.3 manifest seal untouched). Seals: `test_bridge_registers_contract.py`, `test_mcp_output_is_tainted.py`, `test_annotation_cannot_lower_floor.py`.

**D2 — MCP plan steps.** Files: new `model_providers/mcp_plan_schema.py` (STRUCTURED_PLAN_SCHEMA v2, backward-compatible), `plan_validator_mcp.py`. NC: unregistered MCP tool reference fails closed at validation; model only proposes. Seal: `test_plan_mcp_step_requires_registered_tool.py`.

**D3 — Self-RAG corrective retrieval.** Files: new `self_rag/retrieval_critic.py` (deterministic relevance/support/sufficiency), `query_rewrite.py`, `loop.py` (bounded rounds, budget-charged, PARTIAL/UNAVAILABLE when weak — never fabricated), `candidate_ingest.py` (external evidence ⇒ CANDIDATE via `request_write` only); `contracts/self_rag_v1.py`. Depends on **A3** for durable candidates (RAM-only until then, declared UNAVAILABLE seam). Seals: `test_corrective_reretrieval.py`, `test_external_candidate_not_canon.py`.

**D5 — Entity ontology projection (kills "OSP").** Files: new `projections/entity_ontology.py` (folds StateTransitionRecord + MemoryGovernanceRecord + delegation refs + budget/verifier records into `EntityOntologyView`), `contracts/entity_ontology_v1.py`. NC: projection-only; no new source of truth; no wire protocol; truth label = MIN of underlying records. Seals: `test_entity_ontology_is_pure_projection.py`, `test_no_osp_protocol.py`.

**D6 — Intel ingestion tools + CLI.** Files: new `tools_intel.py` (scrape/extract/monitor, network_fetch discipline, output tainted → Self-RAG CANDIDATE), `cli_modules/mcp_a2a_intel_cli.py` (read-only). Seals: `test_scrape_output_is_candidate_only.py`, `test_mcp_a2a_intel_cli_readonly.py`.

**D4 — A2A inbound (DEAD LAST, off-by-default).** Files: new `a2a/message.py` (body tainted), `a2a/inbound.py` (resolve mesh ref → injection scan → authorized-only CommandEnvelope to `runtime.submit`), `board_dispatch.py`, `contracts/a2a_v1.py`. Gated behind D0 sealed AND an explicit **authority-non-expansion proof** (A2A never widens capability beyond pre-existing delegation grants). Resolved-but-unauthorized ⇒ BLOCKED + non-repudiation record + zero sandbox entry. Seals: `test_unresolved_sender_blocked.py`, `test_a2a_body_injection_blocked.py`, `test_a2a_authority_non_expansion.py`.

### Misc

**M1 — Materialize budget/memory mirror.** Close the documented gap: the
`_execute_materialize` path executes in a child runtime whose budget/memory don't
reflect on the parent (only `charge_simulation` + the faithful transition do).
Option: after materialize, replay the child's tool/sandbox budget deltas + memory
candidates into the parent via governed charges/`request_write`. Files: edit
`dual_kernel/kernel.py`. Seal: `test_dual_kernel_materialize_budget_mirror.py`.

**M2 — Coverage + Bandit seal.** Run `--cov=src/agentic_runtime --cov-fail-under=75`
and `bandit -r src` once; record numbers in a report (last coverage 89.21%).

---

## 4. Recommended sequencing

1. **Track A** (unblocks Self-RAG durability): A0 → A1a → A1b → A2 → A3 → A4 → A5 → A6 → A7 → A8a → A8b. (A0's fixture update is the only tricky bit.)
2. **Track C remainder** (parallelizable with A after A3): C6 (shadow) → C7 (enforcing) → C8 → C9. Touches `runtime.submit` — shadow-first, byte-identical off.
3. **Misc M1** any time after C7.
4. **Track D** (last, largest attack surface): D0 → D1 → D2/D3/D5 → D6 → **D4 (A2A) dead last**.
5. **M2** coverage/bandit seal before any external release.
6. Merge each track to `master` with a full-suite seal + `agent/reports/` report (CODEOPS), mirroring `AUREL_DUAL_KERNEL_TRACKB.md`.

---

## 5. Cross-cutting invariants (every phase must hold)

- **Entity proposes, runtime disposes.** Every new capability reduces to a
  `CommandEnvelope` through `AgenticRuntime.submit`, a governed
  `MemoryFabric.request_write`, or a read-only projection. No second executor.
- **Trace = single source of truth.** Every mutation → a hash-chained record.
  Durable stores/projections are projections over the trace. Speculative/PRM/sim
  records are distinctly labeled, never canonical transitions or verified truth.
- **Fail-closed / no silent fallback.** Unknown/unresolved/unbuildable/absent ⇒
  DENY / escalate / honest UNAVAILABLE|PARTIAL|BLOCKED — never a silent allow or a
  fabricated value.
- **No-overclaim (structural).** Lying booleans are unconstructible
  (`substantiated`, `model_judge_available`, `ExternalMemoryBackend` success,
  `NeuralEmbedderSeam.embed`, external-origin→instruction). Truth labels propagate
  as MINs.
- **Governance layered on, never around.** `MemoryWritePolicy` gates all writes;
  agents cannot mint VERIFIED/PROCEDURAL/CANON; failed runs cannot create success
  memory; risk floors only escalate.
- **Additive-behind-flags.** Every flag defaults OFF; disabled path byte-identical
  (prove with a dedicated flag-off test + the full suite).
- **Stdlib-only, deterministic.** `HashingEmbedder` stays the only real embedder;
  all fusion/critics deterministic (sorted by `(score, id)`, never `hash()`);
  persistence reuses `state_store` atomic-rename; no runtime deps.

---

## 6. Deferred seams / known gaps (carry forward)

- Materialize path budget/memory mirror (M1).
- Track C formal C0–C4 contracts (only if a distinct sim-gate surface is wanted).
- Dedicated `ReasoningAllocationRecord` / `SimulationDecisionRecord` types (currently
  reuse `PraxisEventRecord`; the persistent replay drops `details` — encode fields
  in the summary or add a real record + serializer if richer disk projection needed).
- DeepSeek/Ollama `usage` population (P0-S.1 did Anthropic/OpenAI only).
- Router→entity live-usage threading is done for planning; other charge sites still
  estimate_only.
- `max_thinking_tokens`/`max_thinking_calls` are enforced but not yet driven from
  the ThinkingBudget per-entity values end-to-end.

---

**One-line pickup for next session:** *"Read `agent/reports/AUREL_MASTERPLAN_CONTINUATION.md`; start Track A phase A0 per its dispatch spec on branch `feat/track-a-memory`."*
