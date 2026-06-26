# AUREL CODEOPS v1.6
## Agent-Native Hybrid Control Protocol

---

## 0. Identity

**Aurel CodeOps v1.6 — Agent-Native Hybrid Control Protocol**

Aurel CodeOps is the internal development protocol used to build Aurel.

- CodeOps is **not** Aurel runtime.
- CodeOps is **not** Aurel product architecture.
- CodeOps is **not** a new parallel governance tree.
- CodeOps is **not** a replacement for the existing `agent/` or `docs/` system.

CodeOps is the upstream and downstream control protocol that standardizes how every Aurel P, patch, repair, review, integration and seal is shaped, executed, reported, reviewed and continued.

**Canonical formula:**

```
OMNI designs.
Hrvoje dispatches.
Agent executes.
agent/ records.
Git proves.
OMNI reviews.
```

---

## 1. Core Purpose

CodeOps exists to make the existing `agent/` governance layer execute better — not to replace it.

It standardizes:

- How tasks are shaped before implementation
- How prompts become execution contracts
- How agents report evidence-backed outcomes
- How OMNI reviews and decides next steps
- How canon is preserved across patches

---

## 2. Core Doctrine

1. **agent-native** — all process lives inside `agent/`, not a parallel tree
2. **chat-controlled** — intake, brainstorm, plan, and prompt contract originate in ChatGPT / OMNI
3. **operator-dispatched** — Hrvoje selects tool and model at dispatch time
4. **model-neutral** — CodeOps does not route models
5. **canon-preserving** — existing `agent/` and `docs/` truth is never duplicated
6. **evidence-first** — claims require proof; confidence is not evidence
7. **branch-conservative** — `master`/`main` is durable git truth; no branch unless instructed
8. **integration-first** — vertical slices beat isolated backend-only patches
9. **review-driven** — every significant execution passes through OMNI review

---

## 3. Canonical Planes

### 3.1 Chat Control Plane

**Owner:** ChatGPT / OMNI (Hrvoje as sovereign operator)

Responsibilities:

- Intake and current canon snapshot
- Brainstorm
- Plan
- Prompt contract authoring
- Dispatch (operator selects tool/model)
- OMNI review and next-step decision

### 3.2 Agent Governance Plane

**Owner:** `agent/`

Responsibilities:

- Current task pointer (`ACTIVE_TASK.md`)
- Roadmap progress (`ROADMAP.md`)
- Runtime/product state (`STATE.md`)
- Architecture map (`ARCHITECTURE.md`)
- Product/runtime decisions (`DECISIONS.md`)
- Validation commands (`TESTS.md`)
- Report index (`REPORTS.md`)
- Patch evidence (`reports/`, `evidence/`, `releases/`)
- CodeOps protocol (`CODEOPS.md`)
- Templates (`templates/`)

### 3.3 Spec / ADR Plane

**Owner:** `docs/`

Responsibilities:

- Architectural decision records
- Historical design documents
- Roadmap specifications
- Long-form product/spec truth

`docs/` is not the live task pointer. It is the spec and historical design plane.

### 3.4 Execution / Evidence Plane

**Owner:** `src/`, `tests/`, git, validation, reports

Responsibilities:

- Implementation
- Tests
- Validation runs
- Git history as proof
- Structured evidence in `agent/reports/` and `agent/evidence/`

---

## 4. Canonical Folder Structure

```
agent/
├── AGENT.md              # Agent operating guide
├── CODEOPS.md            # This file — upstream control protocol
├── ACTIVE_TASK.md        # Current task pointer
├── ROADMAP.md            # Roadmap progress
├── STATE.md              # Runtime/product state
├── ARCHITECTURE.md       # Product architecture map
├── DECISIONS.md          # Product/runtime decisions
├── TESTS.md              # Validation command authority
├── REPORTS.md            # Report index
├── templates/            # Brainstorm/plan/prompt/report/review templates
├── reports/              # Patch evidence reports
├── evidence/             # Structured evidence
├── releases/             # Release/seal evidence
└── config/               # Agent configuration
```

CodeOps adds **discipline** to this tree. It does not create a second tree.

---

## 5. Files That Must Not Be Created Yet

The following are **forbidden** unless a future CodeOps task explicitly authorizes them:

```
.aurel/codeops/
ACTIVE_STATE.json
DECISION_LOG.md          # duplicate of agent/DECISIONS.md
EVIDENCE_PACK.md         # duplicate of agent/evidence/
VALIDATION.md            # duplicate of agent/TESTS.md
ROUTER.md                # as model-router
BRANCH_REGISTRY.yaml
graph/
metrics/
hooks/
scripts/                 # as CodeOps automation layer
```

Do not create parallel state, validation, evidence, or decision surfaces.

---

## 6. Source-of-Truth Rules

| Need | Canonical Source |
|---|---|
| Current task / next task | `agent/ACTIVE_TASK.md` |
| Roadmap progress | `agent/ROADMAP.md` |
| Runtime/product state | `agent/STATE.md` |
| Product architecture | `agent/ARCHITECTURE.md` |
| Product/runtime decisions | `agent/DECISIONS.md` |
| Validation commands | `agent/TESTS.md` |
| Report index | `agent/REPORTS.md` |
| Patch evidence | `agent/reports/` |
| Structured evidence | `agent/evidence/` |
| Release/seal evidence | `agent/releases/` |
| Upstream CodeOps process | `agent/CODEOPS.md` |
| Brainstorm/plan/prompt/report/review templates | `agent/templates/` |

---

## 7. Conflict Resolution

When sources disagree, resolve in this order:

1. Explicit operator instruction
2. Current prompt contract for current execution
3. `agent/ACTIVE_TASK.md` for current task pointer
4. `agent/ROADMAP.md` for roadmap/progress
5. `agent/STATE.md` for product/runtime state
6. `agent/TESTS.md` for validation commands
7. `agent/DECISIONS.md` for product/runtime decisions
8. `docs/ADR` or sealed docs for architectural history
9. `agent/CODEOPS.md` for process discipline
10. `agent/templates/` for formatting

If conflict is serious:

```
STOP.
Report conflict.
Ask operator for decision.
```

---

## 8. Hard Laws

1. Every P starts in ChatGPT: Intake → Brainstorm → Plan → Prompt Contract.
2. Hrvoje is sovereign operator.
3. Hrvoje selects the tool/model at dispatch time.
4. CodeOps does not route models.
5. Prompt is an execution contract.
6. Agent executes the contract, not vibes.
7. Existing `agent/` canon must be preserved.
8. Existing `docs/` canon must be preserved.
9. No duplicate state surface.
10. No duplicate decision log.
11. No duplicate evidence format.
12. No duplicate validation authority.
13. `master`/`main` is durable git truth.
14. No new branch unless explicitly instructed.
15. No push from implementation prompts.
16. No history rewrite.
17. Stop on unrelated dirty files.
18. No fake done.
19. No fake live.
20. BLUEPRINT / future systems are not active automation.
21. DEV_FIXTURE, MOCK, SIMULATED, UNAVAILABLE, LIVE and TRACE_VERIFIED must be clearly separated.
22. `agent/TESTS.md` is validation command authority.
23. Product/runtime decisions go to `agent/DECISIONS.md`.
24. Aurel P patch reports go to `agent/reports/`.
25. Report links go to `agent/REPORTS.md`.
26. Evidence over confidence.
27. Validation must match risk.
28. Critical path requires elevated validation.
29. Every report declares remaining risk.
30. Clean git is part of done.
31. If CodeOps adds ceremony without better execution, remove it.

---

## 9. Full CodeOps Lifecycle

### 9.1 Intake / Current Canon Snapshot

Read canonical sources before any brainstorm or plan:

- `agent/ACTIVE_TASK.md`
- `agent/ROADMAP.md`
- `agent/STATE.md`
- `agent/TESTS.md`
- `agent/REPORTS.md`
- Latest `agent/reports/`
- `agent/ARCHITECTURE.md` if architecture-sensitive
- `agent/DECISIONS.md` if decision-sensitive
- `docs/adr/` if ADR-sensitive

Do not plan against imagined state.

### 9.2 Brainstorm

Shape the task before creating a Plan.

Template: `agent/templates/BRAINSTORM_TEMPLATE.md`

Brainstorm chooses direction, reduces scope, exposes risk, and prepares the Plan. Brainstorm is not implementation.

### 9.3 Plan

High-rigor plan with integration-first slice, truth labels, acceptance criteria, and validation strategy.

Template: `agent/templates/PLAN_TEMPLATE.md`

### 9.4 Prompt Contract

Copy/paste execution contract for the dispatched agent.

Template: `agent/templates/PROMPT_CONTRACT_TEMPLATE.md`

The prompt is the contract. The agent executes the contract, not vibes.

### 9.5 Dispatch

Hrvoje selects tool and model at dispatch time. CodeOps does not route models.

### 9.6 Agent Execution

Agent reads canon, implements within scope, validates, updates existing canon, creates evidence.

### 9.7 Agent Report

Structured report of what was done, what was proven, and what remains.

Template: `agent/templates/AGENT_REPORT_TEMPLATE.md`

Do not claim DONE unless implementation, validation, canon updates, report, commit, and git state support that claim.

### 9.8 OMNI Review

OMNI reviews agent report against prompt contract and canon.

Template: `agent/templates/OMNI_REVIEW_TEMPLATE.md`

Primary decision must be exactly one of:

```
CONTINUE
REPAIR
REVIEW
INTEGRATE
SEAL
STOP
```

### 9.9 Repair / Review / Integrate / Seal / Continue / Stop

Based on OMNI verdict:

- **CONTINUE** — proceed to next task or next brainstorm
- **REPAIR** — minimal fix using `agent/templates/REPAIR_TEMPLATE.md`
- **REVIEW** — external/adversarial review using `agent/templates/REVIEW_PROMPT_TEMPLATE.md`
- **INTEGRATE** — merge parallel work or prompt-pack outputs
- **SEAL** — exit seal using `agent/templates/SEAL_TEMPLATE.md`
- **STOP** — halt due to conflict, blocker, or operator decision

Then return to next brainstorm.

---

## 10. Execution Modes

| Mode | Description |
|---|---|
| **DOCS_ONLY** | Process/docs patch; no runtime changes |
| **LEAN** | Minimal targeted patch with focused validation |
| **ELEVATED** | Critical path; full validation suite required |
| **FULL_SEAL** | Exit seal with integration demo and evidence layer |

Operator and plan select mode based on risk tier and task pattern.

---

## 11. Task Patterns

| Pattern | Description |
|---|---|
| **P_PATCH** | Standard Aurel P numbered patch |
| **REPAIR** | Minimal fix for known failure |
| **SPIKE** | Time-boxed exploration; may defer |
| **INTEGRATION** | Vertical slice across layers |
| **SEAL** | Section exit seal with evidence |
| **DOCS_PROCESS** | Governance/process/docs only |
| **PROMPT_PACK** | Multiple coordinated prompts |
| **ORCHESTRATED** | Single executor, phased work |

Templates for multi-prompt work:

- `agent/templates/PROMPT_PACK_TEMPLATE.md`
- `agent/templates/ORCHESTRATED_PROMPT_TEMPLATE.md`

---

## 12. Integration-First Law

Every significant patch should declare an integration-first slice:

| Layer | Question |
|---|---|
| Backend capability | Does backend logic exist? |
| Versioned contract/schema | Is there a versioned contract? |
| Projection/API/Event/read model | Is there a read path? |
| CLI/Shell/TUI binding | Is there operator-facing binding? |
| Trace/evidence/report binding | Is evidence linked? |
| Operator-testable path | Can operator verify? |

Truth labels must be honest:

```
LIVE
TRACE_VERIFIED
SIMULATED
DEV_FIXTURE
UNAVAILABLE
ERROR
```

Do not fake LIVE. Do not fake TRACE_VERIFIED.

---

## 13. Branching Doctrine

- Work on `master`/`main` unless explicitly instructed otherwise
- No branch creation from implementation prompts
- No push from implementation prompts
- No history rewrite
- Clean git is part of done
- Stop on unrelated dirty files

---

## 14. Validation Doctrine

- `agent/TESTS.md` is validation command authority
- Validation depth must match risk tier
- DOCS_ONLY patches: `git diff --check`, file existence, scope checks
- LEAN patches: focused pytest subset
- ELEVATED/FULL_SEAL: full suite per `TESTS.md`
- Do not weaken tests to pass
- Report exact commands run in agent report

---

## 15. Existing Canon Update Rules

When updating existing canon:

- Update only files relevant to the task
- Do not rewrite entire files unless required
- Do not duplicate state into new files
- Product/runtime decisions → `agent/DECISIONS.md`
- Patch evidence → `agent/reports/` + link in `agent/REPORTS.md`
- Task completion → update `agent/ACTIVE_TASK.md` and `agent/ROADMAP.md` as appropriate
- Runtime state changes → `agent/STATE.md`
- Do not create parallel decision logs, validation files, or evidence formats

---

## 16. Report Doctrine

Every significant patch produces a report in `agent/reports/`.

Reports must include:

- Purpose
- What was implemented
- What was deliberately not implemented
- Validation commands run
- Truth labels used
- Remaining risks
- Next recommended task

Link all reports from `agent/REPORTS.md`.

Do not claim DONE without evidence.

---

## 17. Prompt Integrity

A prompt contract must:

- Declare git/worktree discipline
- Point to canonical sources
- Define mission, boundaries, and non-goals
- Specify affected layers
- Include validation strategy
- Include acceptance criteria
- Include stop conditions
- State: operator selected tool/model at dispatch time; do not perform model routing

Agents must execute the contract as written. Scope deviations must be reported.

---

## 18. Standard Templates

| Template | Purpose |
|---|---|
| `templates/BRAINSTORM_TEMPLATE.md` | Pre-plan brainstorming |
| `templates/PLAN_TEMPLATE.md` | High-rigor plan |
| `templates/PROMPT_CONTRACT_TEMPLATE.md` | Copy/paste execution prompt |
| `templates/AGENT_REPORT_TEMPLATE.md` | Post-execution agent report |
| `templates/OMNI_REVIEW_TEMPLATE.md` | OMNI review checklist |
| `templates/REPAIR_TEMPLATE.md` | Minimal repair prompt |
| `templates/SEAL_TEMPLATE.md` | Exit seal checklist |
| `templates/ORCHESTRATED_PROMPT_TEMPLATE.md` | Single-executor phased work |
| `templates/PROMPT_PACK_TEMPLATE.md` | Multi-prompt orchestration |
| `templates/REVIEW_PROMPT_TEMPLATE.md` | External/adversarial review |

All templates are copy/paste friendly and model-neutral.

---

## 19. Standard OMNI Outputs

OMNI produces one of:

| Output | When |
|---|---|
| Brainstorm verdict | After brainstorm |
| Plan approval | After plan review |
| Prompt contract | Ready for dispatch |
| OMNI review verdict | After agent report |
| Repair prompt | On REPAIR decision |
| Seal verdict | On SEAL decision |
| Next task recommendation | On CONTINUE |

Primary post-execution decision is exactly one of: CONTINUE, REPAIR, REVIEW, INTEGRATE, SEAL, STOP.

---

## 20. CodeOps Build Roadmap

| ID | Title | Status |
|---|---|---|
| **CODEOPS-0A** | Agent-Native Upstream Control Layer | **COMPLETE** (this patch) |
| **CODEOPS-0B** | Preflight Teeth | Future only |
| **CODEOPS-0C** | Report-Backed Active Task Projection | Future only |
| **CODEOPS-0D** | Parallel Work Protocol | Future only |

CODEOPS-0B and beyond are planned future work. Do not implement unless explicitly tasked.

---

## 21. Final Definition

**CodeOps is not a new tree.**

**CodeOps is the discipline that makes the existing `agent/` tree execute better.**

```
Intake / Current Canon Snapshot
→ Brainstorm
→ Plan
→ Prompt Contract
→ Dispatch
→ Agent Execution
→ Agent Report
→ OMNI Review
→ Repair / Review / Integrate / Seal / Continue / Stop
→ Next Brainstorm
```

```
OMNI designs.
Hrvoje dispatches.
Agent executes.
agent/ records.
Git proves.
OMNI reviews.
```
