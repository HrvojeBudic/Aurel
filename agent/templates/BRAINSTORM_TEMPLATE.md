# BRAINSTORM TEMPLATE — {{P_ID}} {{TITLE}}

## 0. Brainstorm Purpose

This Brainstorm exists to shape the task before creating a Plan.

It must answer:

- What are we really trying to build?
- What is already true in the repo?
- What are the viable approaches?
- What is the smallest correct path?
- What must not be done?
- What is the correct CodeOps execution shape?

Brainstorm is not implementation.

Brainstorm chooses direction, reduces scope, exposes risk, and prepares the Plan.

---

# 1. Current Canon Snapshot

Active roadmap:
Current roadmap section:
Last completed task:
Current expected task:
Relevant latest report:
Known repo state:
Known validation baseline:
Known blockers:

Canonical repo sources:
- agent/ACTIVE_TASK.md
- agent/ROADMAP.md
- agent/STATE.md
- agent/TESTS.md
- agent/REPORTS.md
- latest agent/reports/
- agent/ARCHITECTURE.md if architecture-sensitive
- agent/DECISIONS.md if decision-sensitive
- docs/adr/ if ADR-sensitive
- docs/roadmap/ if roadmap-spec-sensitive

Canon truth rule:
Do not brainstorm against imagined state.
If canon is unknown, mark assumptions clearly.
If canon conflicts with user instruction, surface the conflict.

---

# 2. Mission Problem

## What is the actual problem?

{{MISSION_PROBLEM}}

## Why now?

{{WHY_THIS_TASK_NOW}}

## What capability or proof should exist after this task?

{{EXPECTED_CAPABILITY_OR_PROOF}}

## What is the operator-visible value?

{{OPERATOR_VALUE}}

---

# 3. Roadmap Position

Roadmap version: AUREL Roadmap v5.1 — Integration-First Roadmap

Completed:
{{COMPLETED_TASKS}}

Current:
{{P_ID}} — {{TITLE}}

Next expected:
{{NEXT_TASK}}, unless active roadmap says otherwise.

Rule:
If active roadmap disagrees, preserve active roadmap truth and report conflict.
Do not invent a next task.

---

# 4. Integration-First Pressure Check

| Layer | Expected in this task |
|---|---|
| Backend capability | {{YES_NO_OR_UNAVAILABLE}} |
| Versioned contract/schema | {{YES_NO_OR_UNAVAILABLE}} |
| Projection/API/Event/read model | {{YES_NO_OR_UNAVAILABLE}} |
| CLI/Shell/TUI binding | {{YES_NO_OR_UNAVAILABLE_WITH_REASON}} |
| Trace/evidence/report binding | {{YES_NO_OR_UNAVAILABLE}} |
| Operator-testable path | {{LIVE_SIMULATED_DEV_FIXTURE_OR_UNAVAILABLE}} |

Truth labels involved:
LIVE:
TRACE_VERIFIED:
SIMULATED:
DEV_FIXTURE:
UNAVAILABLE:
ERROR:

Risk of fake vertical slice:
{{RISK_OF_FAKE_SLICE_OR_OVERCLAIM}}

---

# 5. Strategic Options

## Option A — Minimal Patch

Description:
What it changes:
What it proves:
Pros:
Cons:
Risk:
Validation needed:

## Option B — Task Pack

Description:
Grouped tasks:
What it changes:
What it proves:
Pros:
Cons:
Risk:
Validation needed:

## Option C — Vertical Slice / Integration Patch

Description:
Slice path:
Backend:
Contract:
Projection/API/Event:
CLI/Shell/TUI:
Trace/evidence/report:
Operator-testable path:
Pros:
Cons:
Risk:
Validation needed:

## Option D — RCA Repair

Description:
Failure:
Suspected root cause:
Minimal repair:
Regression proof:
Risk:
Validation needed:

## Option E — Spike / Defer

Description:
Why not implement now:
What to learn:
Promotion condition:
Reject/defer condition:
Risk:
Validation/report needed:

---

# 6. Recommended Direction

Chosen option:
{{RECOMMENDED_OPTION}}

Why this is the best path:
{{WHY_THIS_OPTION}}

Smallest correct scope:
{{SMALLEST_CORRECT_SCOPE}}

What this does not solve:
{{LIMITATIONS}}

---

# 7. CodeOps Classification Draft

| Field | Draft |
|---|---|
| Task Pattern | {{PATTERN}} |
| Execution Mode | {{MODE}} |
| Risk Tier | {{LOW_MEDIUM_HIGH_CRITICAL}} |
| Parallel Safety | {{SAFE_NOT_SAFE_SEQUENTIAL_ONLY}} |
| Validation Depth | {{DOCS_ONLY_LEAN_ELEVATED_FULL_SEAL}} |
| Review Needed | {{OMNI_REVIEW_ADVERSARIAL_INTEGRATION_SEAL_NONE}} |
| Dispatch Note | Operator selects tool/model at dispatch time. |

---

# 8. Main Risks

## Technical risks

- {{TECH_RISK_1}}
- {{TECH_RISK_2}}

## Governance / truth risks

- {{GOVERNANCE_RISK_1}}
- {{GOVERNANCE_RISK_2}}

## Scope creep risks

- {{SCOPE_RISK_1}}
- {{SCOPE_RISK_2}}

## Git / validation risks

- {{GIT_OR_VALIDATION_RISK_1}}
- {{GIT_OR_VALIDATION_RISK_2}}

---

# 9. What Not To Do

This task must not become:

- {{NON_GOAL_1}}
- {{NON_GOAL_2}}
- {{NON_GOAL_3}}

Hard boundaries:

Do not fake LIVE.
Do not fake TRACE_VERIFIED.
Do not weaken tests/governance to pass.
Do not create new branch unless explicitly instructed.
Do not duplicate agent/ state, validation, report or decision canon.
Do not implement future roadmap tasks inside this task.

Task-specific hard boundaries:

{{TASK_SPECIFIC_HARD_BOUNDARIES}}

---

# 10. Required Proof / Evidence Shape

The eventual Plan/Prompt should require proof of:

- implementation exists
- tests exist
- focused validation ran
- relevant agent/ canon updated
- report created if required
- truth labels are honest
- unavailable states include reasons
- no forbidden side effects
- commit created if required
- final git status clean

Task-specific proof:

{{TASK_SPECIFIC_PROOF}}

---

# 11. Decision Needed

Before Plan, operator must confirm:

{{DECISION_NEEDED}}

Default decision candidates:

- Proceed to Plan with recommended direction.
- Revise scope before Plan.
- Split into Prompt Pack.
- Turn into Repair.
- Defer / Spike.
- Stop due to canon conflict.

---

# 12. Brainstorm Verdict

Verdict:
Recommended next step:
Plan readiness:
Known assumptions:
Known blockers:

Decision:

CONTINUE_TO_PLAN / REVISE_BRAINSTORM / SPLIT / REPAIR / SPIKE / STOP
