# AUREL MAP 02 — "Sovereign Soul Framework" ↦ Dual-Kernel Governance

**Status:** ANALYSIS / MAPPING (no build). Companion to `AUREL_PLAN_01_COGNITIVE_SUBSTRATE_UPGRADE.md`.
**Subject:** an externally-proposed 5-layer AI-safety design ("Sovereign Soul Framework" / "Aksios Sentinel").
**Question answered:** *Is it integrable into Aurel, and what — if anything — is genuinely new?*
**Verdict:** 4 of 5 layers already exist on `feat/dual-kernel-sigma-merge-gate`, in a **stronger** form (deterministic, hash-chained, CI-anchored to DSD no-collapse laws). One layer — an adversarial "devil's advocate" pass — is genuinely additive and is specified separately in §4.

**Doctrine anchor (unchanged):** *Entity proposes, runtime disposes.* The AurelTraceLog + dual-kernel ledger are the single canonical source of truth. Every mapping below preserves: no second executor, fail-closed, no-overclaim, monotone governance, additive-behind-flags.

---

## 1. The proposal in one paragraph

The source text argues that an agent can be "jailbroken" because it is ontologically shallow — every instruction is equal if written convincingly — and that the only durable defense is **architecture, not a better system prompt**. It proposes five immovable layers (defense-in-depth + immune system): (1) a **Sacred Core** of immutable values placed outside prompt reach; (2) a **Superego Guardian** that intercepts every plan before execution; (3) an **Adversarial Trinity** (Defender + Devil's Advocate + Judge) that simulates the worst-case jailbreak in real time; (4) a **Consequence Simulator** that looks 3–5 steps ahead before acting; (5) an **External Kill-Switch + Audit Oracle** (immutable log + human override).

The intuition is sound. The prescribed *implementation* (a "Creed Vector" with cosine similarity > 0.97, a proprietary blockchain ledger, mystical framing) conflicts with Aurel's determinism/no-overclaim doctrine and is addressed in §3.

---

## 2. Layer-by-layer mapping to existing modules

### Layer 1 — Sacred Core (immutable values outside prompt reach)

**Proposed:** values as an embedding vector + constitutional rules + cryptographic hash; unchangeable by prompt because it lives outside context.

**Aurel equivalent — BUILT, stronger:** Aurel encodes "immovable values" as **real predicates and a monotone state vector**, not a fuzzy embedding.

| Proposal element | Aurel realization | Location |
|---|---|---|
| Immutable constitution | `cannot_disable_constitutional_floor`; operator is final authority; self-escalation impossible; config + trace outside agent write-authority | `docs/P1.4_AGENT_TRUST_CONSTITUTION.md` |
| "Values prioritized above any instruction" | Hard invariants — real Boolean predicates over Σ + command; a single failure forces a synchronous block | `dual_kernel/constraints.py` — `NoSecretsEgress`, `ProtectedTestIntegrity`, `WithinAuthorityRisk`, `ConstraintSet.hard_violations()` |
| "Cannot be lowered by a prompt" | `GovernanceStateVector` (Σ) is **monotone** — risk/sensitivity/capability never weaken across a task; you cannot talk Σ down | `dual_kernel/sigma.py` — `GovernanceStateVector.update()`, `_rank()` |
| Cryptographic anchoring | Every governance decision is hash-chained (see Layer 5) | `dual_kernel/ledger.py` |

**Why this is stronger than a Creed Vector:** a cosine-similarity gate is (a) non-deterministic → breaks replay fidelity, and (b) *spoofable* by sufficiently persuasive text — precisely the attack it claims to stop. A Boolean predicate over authority (`WithinAuthorityRisk`) cannot be "persuaded."

### Layer 2 — Superego Guardian (intercept every plan before execution)

**Proposed:** a separate agent that intercepts each inner-agent plan and returns `APPROVED / VETO / CLARIFY` before anything runs.

**Aurel equivalent — BUILT:** this is the entire **Custos control-plane + merge gate**. Nothing reaches live state without passing it.

| Proposal element | Aurel realization | Location |
|---|---|---|
| Guardian is a *separate plane* | Custos (governance plane) is distinct from Praxis (execution plane) | `dual_kernel/sigma.py` (Custos), `dual_kernel/praxis.py` (Praxis) |
| Intercepts every plan | `DualKernelRuntime.submit()` routes every command by measured autonomy before execution | `dual_kernel/kernel.py:84` — `submit()` |
| `VETO` | `AdmitDecision.blocked=True` when `identity_confidence < CONFIDENCE_HARD_FLOOR` (0.30); GOVERNED route discards a fork on a non-mergeable verdict | `dual_kernel/routing.py`; `dual_kernel/kernel.py:104-111` |
| `APPROVED` | Only `PASS` / `PASS_WITH_WARNING` are mergeable; every other verdict blocks | `dual_kernel/merge_gate.py:77` — `_MERGEABLE` |
| `CLARIFY` | `NEEDS_MORE_EVIDENCE` / `NEEDS_AUTHORITY_REVIEW` / `REVIEW_REQUIRED` rungs of the verdict ladder | `dual_kernel/merge_gate.py:30-44` — `MergeVerdict` |

**Note on the proposed Superego prompt** ("Ti si moja nepomična Srž… cosine > 0.97… nikad ne pregovaraš"): Aurel deliberately does **not** implement the guardian as an LLM prompt, because a prompt-based guardian shares the shallowness the design is trying to escape. The guardian is code (`MergeGate.evaluate`) whose checks are bound to canon laws and verified in CI.

### Layer 3 — Adversarial Trinity (Defender + Devil's Advocate + Judge)

**Proposed:** three parallel agents; the Devil's Advocate simulates the worst-case jailbreak in real time; if it succeeds, the action is refused.

**Aurel equivalent — PARTIAL / the one genuine gap.** Aurel has the *Judge* (`MergeGate`) and the *Defender* (hard invariants + policy), but **no explicit Devil's Advocate** that actively tries to construct the worst-case abuse of a proposed plan. The closest built primitive is the Track B PRM step-verifier + bounded replan, and even that is `model_judge_available = False` (structurally UNAVAILABLE) today.

→ This is the subject of the standalone build spec in §4.

### Layer 4 — Consequence Simulator (look ahead before acting)

**Proposed:** before each action, simulate 3–5 steps and ask "is this consistent with my Core?"; prevents gradual grooming.

**Aurel equivalent — BUILT (single-step) + PLANNED (multi-step world model):** Aurel already executes consequential commands in a **disposable fork** and judges the *real verified post-state* before it can touch live state.

| Proposal element | Aurel realization | Location |
|---|---|---|
| Simulate before permitting | `_preflight()` copies live workspace, runs the command in an ephemeral sandbox, gates the result; `_execute_materialize()` executes once in a CoW fork and merges only on PASS | `dual_kernel/kernel.py:142-252` |
| Score the predicted state | `MergeContext.verifier_result` comes from the **real** `StateVerifier` over the forked post-state — not a tool's self-claim | `dual_kernel/merge_gate.py:183` — `state_verification` blocker |
| "Consistent with Core?" | C1–C4 compositionality: write-paths ⊆ authority, assumptions discharged, governance consistent, recovery independent | `dual_kernel/merge_gate.py:137-168` |
| Multi-step lookahead / world model | PLANNED — Track C "simulate-then-permit" (disposable state twin, evidence-only, never authority) | `AUREL_PLAN_01`, Track C (C0–C9) |
| Anti-"gradual grooming" | Monotone Σ (§Layer 1) means cumulative risk cannot be reset by incremental innocuous steps — the grooming attack the text names is structurally blunted | `dual_kernel/sigma.py` |

**Doctrinal guardrail:** simulation output is **evidence, never authority** (`SimulationVerdict.is_authority` is structurally False in the plan). The text's framing "the simulator decides" would violate no-overclaim; in Aurel it can only *escalate* (add a blocker), never permit.

### Layer 5 — External Kill-Switch + Audit Oracle (immutable log + human override)

**Proposed:** human override + logs that cannot be deleted + an external verifier (a second account); optionally a private blockchain / Filecoin.

**Aurel equivalent — BUILT:** a tamper-evident, hash-chained decision ledger with an independent verify path, plus HITL as the human override.

| Proposal element | Aurel realization | Location |
|---|---|---|
| Immutable audit log | `DualKernelLedger` — append-only, GENESIS→…→head chain; `entry_hash = sha(prev_hash, payload_hash)` | `dual_kernel/ledger.py` — `DualKernelEvent.compute_entry_hash()` |
| "Logs that cannot be deleted" | Tamper detection: `verify()` recomputes every `entry_hash` and confirms the `prev_hash` chain; returns break sequence on any edit | `dual_kernel/ledger.py` — `verify()` |
| External verifier ("second account") | `dual-kernel verify-ledger <path>` run from an independent process/CI over the persisted JSONL | `cli_modules/dual_kernel_commands.py` — `cmd_dual_kernel_verify_ledger()` |
| Human override / kill-switch | HITL approval gate + operator-final-authority constitution; `AutoApprover` is only the *speculative* preflight approver, never the live gate | `dual_kernel/kernel.py:287` note; `docs/P1.4_AGENT_TRUST_CONSTITUTION.md` |
| Read-only operator surface | `dual-kernel status / bindings / show` | `cli_modules/dual_kernel_commands.py` |

**On blockchain/Filecoin:** explicitly out of scope. Aurel's doctrine is *stdlib-only, trace is the single source of truth*. A hash-chained append-only ledger already provides tamper-evidence without an external chain, a runtime dependency, or a second source of truth.

---

## 3. What NOT to port (and why)

Copying the proposal literally would **weaken** Aurel. Rejected elements:

1. **"Creed Vector" + cosine similarity > 0.97.** Non-deterministic (breaks replay) and spoofable by persuasive text. Aurel uses Boolean predicates over authority + a monotone Σ instead. Only `HashingEmbedder` (sha256) is a real embedder in the system; a neural/semantic gate is a declared UNAVAILABLE seam.
2. **Prompt-based Superego** ("Ti si Aksios… nikad ne pregovaraš"). A guardian implemented as an LLM prompt inherits the shallowness the framework claims to fix. Aurel's guardian is code bound to canon laws and CI-verified.
3. **Blockchain / Filecoin ledger.** Redundant given the hash-chained trace; violates stdlib-only + single-source-of-truth.
4. **Mystical framing** ("soul", "blood oath", "what you would die for"). No operational content; not representable as a predicate or a trace record.
5. **The closing prompt** of the source text ("tell me your deepest values, without a filter") is multi-turn persuasion scaffolding — ironically, the exact attack class Layer 2 exists to refuse. It has no engineering function and is disregarded.

---

## 4. The one genuine addition — Adversarial Trinity (build spec)

Everything above already exists. The Devil's Advocate does not. Below is a doctrine-clean specification to add it as an **evidence-only, escalation-only** blocker in the merge gate.

### 4.1 Principle

A new gate check `red_team_ok` that runs an adversarial pass over a proposed command **before** it can merge. The pass tries to construct the worst-case abuse/jailbreak realization of the command. Its verdict is **evidence, never authority**: it can only *add a blocker* (escalate to a review/fail rung), never permit an action or lower risk. This mirrors exactly how C1–C4 already behave (`MergeGate._c*` → append blocker).

### 4.2 Where it plugs in

- **Data model:** add `red_team_ok: bool = True` and `red_team_findings: tuple[str, ...] = ()` to `MergeContext` (`dual_kernel/merge_gate.py:80`). Default `True` keeps the flag-off path byte-identical.
- **Check:** in `MergeGate.evaluate()` (`merge_gate.py:171`), after the C1–C4 block:
  ```python
  if not ctx.red_team_ok:
      blockers.append("adversarial_review")
  ```
- **Gate id:** add `"adversarial_review"` to `GATE_IDS` (`merge_gate.py:63`) so `validate_coverage()` forces a canon binding to exist — fail-fast at construction otherwise.
- **NC binding:** add one row to `nc_merge_bindings.json` binding `adversarial_review` → an appropriate DSD no-collapse law (candidate: an NC-01H persuasion/authority-collapse law) with `verdict_on_fail = "review_required"` (soft) or `"needs_authority_review"` (hard). Reviewed with whoever owns canon.

### 4.3 Who produces `red_team_ok`

Deny-by-default and fail-closed:

- **Phase 1 (deterministic, ships first):** a pure, I/O-free `AdversarialProbe` in `dual_kernel/adversarial.py` — stdlib signature checks over the command + Σ (e.g. authority-expansion attempt, protected-path deletion framed as refactor, secrets/net reach not granted by the card, monotonicity-reset patterns). No model, deterministic, replayable. This is the analogue of the injection-detector-as-data-channel-defense from Track D.
- **Phase 2 (optional, gated):** an LLM "Devil's Advocate" that *proposes* worst-case exploits, surfaced as **evidence only** and charged through `charge_reasoning` (depends on `AUREL_PLAN_01` P0-S.1/P0-S.2). Structurally `model_judge_available`-style False until the budget/no-overclaim seams land — i.e. it can never be recorded as verified truth, only as a blocker signal.

### 4.4 Invariants (must hold)

1. **Escalation-only.** `red_team_ok=False` can only *add* a blocker. There is no code path where the adversarial pass permits, un-blocks, or lowers a risk rank. (Same shape as `sim_policy_influence.influence_is_escalation_only`.)
2. **Evidence, not authority.** Findings are recorded in the ledger (`blockers` + `nc_laws`), never as a `StateTransitionRecord` or a verified truth.
3. **Fail-closed.** Probe error / model UNAVAILABLE ⇒ treat as `red_team_ok=False` on consequential writes (block), not silent pass.
4. **Additive-behind-flag.** Default `True`; the ephemeral path stays byte-identical when the probe is not wired. Sealed by a new `test_p_adversarial_review_seal.py` (gate-off ⇒ byte-identical; probe finding ⇒ single `adversarial_review` blocker, zero live mutation).

### 4.5 Smallest sealable PR

`feat(dual-kernel): adversarial_review blocker — deterministic red-team probe (evidence-only, escalation-only)`

- `dual_kernel/merge_gate.py` — `MergeContext` fields + one blocker check + `GATE_IDS` entry.
- `dual_kernel/nc_merge_bindings.json` — one canon binding for `adversarial_review`.
- `dual_kernel/adversarial.py` — deterministic `AdversarialProbe` (Phase 1 only).
- `tests/test_p_adversarial_review_seal.py` — coverage + escalation-only + byte-identity seals.

No dependency on the four cognitive tracks; ships independently on the current branch. The Phase-2 LLM Devil's Advocate is a later, budget-gated follow-up.

---

## 5. One-line conclusion

Aurel is not an agent that needs a soul bolted on — it is *already* the "entity proposes, runtime disposes" architecture the proposal gropes toward, with 4 of 5 layers built as provable code rather than persuasive prose. The single worthwhile graft is a deterministic, evidence-only **adversarial_review** blocker (§4); the rest of the proposal is either already present in stronger form or actively contra-indicated by the no-overclaim / determinism doctrine.
