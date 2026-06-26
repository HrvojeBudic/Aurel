# CODEOPS-0A — Agent-Native Hybrid Control Protocol

**Date:** 2026-06-26  
**Status:** COMPLETE  
**Patch type:** DOCS_PROCESS — agent-native upstream control layer

---

## 1. Purpose

CODEOPS-0A installs Aurel CodeOps v1.6 as an upstream control protocol inside the existing `agent/` governance layer. It does not create `.aurel/codeops`, `ACTIVE_STATE.json`, duplicate evidence, duplicate validation, duplicate decision logs, runtime code, tests, hooks, scripts, branch registry, graph, metrics, or automation.

CodeOps standardizes how every Aurel P, patch, repair, review, integration and seal is shaped, executed, reported, reviewed and continued — without replacing the existing `agent/` tree.

---

## 2. Why CodeOps is agent-native

CodeOps lives entirely inside `agent/`:

- Protocol definition: `agent/CODEOPS.md`
- Templates: `agent/templates/`
- Evidence: existing `agent/reports/`, `agent/evidence/`, `agent/releases/`
- Task/roadmap/state/validation: existing `agent/ACTIVE_TASK.md`, `ROADMAP.md`, `STATE.md`, `TESTS.md`

There is no parallel `.aurel/codeops/` tree, no duplicate state JSON, and no second governance system. CodeOps is the discipline that makes the existing `agent/` tree execute better.

Canonical formula:

```
OMNI designs.
Hrvoje dispatches.
Agent executes.
agent/ records.
Git proves.
OMNI reviews.
```

---

## 3. Existing canon preserved

All existing `agent/` governance files preserved:

- `agent/AGENT.md` — minimally extended with CodeOps pointer section
- `agent/ACTIVE_TASK.md` — untouched
- `agent/ROADMAP.md` — untouched
- `agent/STATE.md` — untouched
- `agent/ARCHITECTURE.md` — untouched
- `agent/DECISIONS.md` — untouched
- `agent/TESTS.md` — untouched
- `agent/REPORTS.md` — one index entry added

No changes to `src/`, `tests/`, `docs/`, `.cursor/`, or `.claude/`.

---

## 4. Files added

| File | Purpose |
|---|---|
| `agent/CODEOPS.md` | Aurel CodeOps v1.6 protocol definition |
| `agent/templates/BRAINSTORM_TEMPLATE.md` | Pre-plan brainstorming template |
| `agent/templates/PLAN_TEMPLATE.md` | High-rigor plan template |
| `agent/templates/PROMPT_CONTRACT_TEMPLATE.md` | Copy/paste execution prompt template |
| `agent/templates/AGENT_REPORT_TEMPLATE.md` | Post-execution agent report template |
| `agent/templates/OMNI_REVIEW_TEMPLATE.md` | OMNI review checklist template |
| `agent/templates/REPAIR_TEMPLATE.md` | Minimal repair prompt template |
| `agent/templates/SEAL_TEMPLATE.md` | Exit seal checklist template |
| `agent/templates/ORCHESTRATED_PROMPT_TEMPLATE.md` | Single-executor phased work template |
| `agent/templates/PROMPT_PACK_TEMPLATE.md` | Multi-prompt orchestration template |
| `agent/templates/REVIEW_PROMPT_TEMPLATE.md` | External/adversarial review template |
| `agent/reports/CODEOPS_0A_AGENT_NATIVE_HYBRID_CONTROL_PROTOCOL.md` | This report |
| `AGENTS.md` | Root shim pointing to `agent/AGENT.md` and `agent/CODEOPS.md` |

---

## 5. Files updated

| File | Change |
|---|---|
| `agent/AGENT.md` | Added CodeOps section after "Before changing code" |
| `agent/REPORTS.md` | Added CODEOPS-0A report index entry |

---

## 6. What was deliberately not created

The following were **not** created per hard law:

- `.aurel/codeops/` directory
- `ACTIVE_STATE.json`
- `DECISION_LOG.md` (duplicate of `agent/DECISIONS.md`)
- `EVIDENCE_PACK.md` (duplicate of `agent/evidence/`)
- `VALIDATION.md` (duplicate of `agent/TESTS.md`)
- `ROUTER.md` as model-router
- `BRANCH_REGISTRY.yaml`
- `graph/`, `metrics/`, `hooks/`, `scripts/` as CodeOps automation
- Runtime code changes in `src/`
- Test changes in `tests/`
- Docs changes in `docs/`
- `CLAUDE.md`

---

## 7. Source-of-truth preservation

Source-of-truth table from `agent/CODEOPS.md` preserves all existing canon locations. CodeOps adds only:

- `agent/CODEOPS.md` — upstream process protocol
- `agent/templates/` — formatting templates

No duplicate state, validation, evidence, or decision surfaces were introduced.

---

## 8. Templates added

Ten model-neutral, copy/paste-friendly templates in `agent/templates/`:

1. BRAINSTORM_TEMPLATE.md
2. PLAN_TEMPLATE.md
3. PROMPT_CONTRACT_TEMPLATE.md
4. AGENT_REPORT_TEMPLATE.md
5. OMNI_REVIEW_TEMPLATE.md
6. REPAIR_TEMPLATE.md
7. SEAL_TEMPLATE.md
8. ORCHESTRATED_PROMPT_TEMPLATE.md
9. PROMPT_PACK_TEMPLATE.md
10. REVIEW_PROMPT_TEMPLATE.md

All templates omit model routing and tool recommendations per CodeOps hard law #4.

---

## 9. Validation run

Exact commands run:

```bash
git diff --check
git status --short
test -f agent/CODEOPS.md
test -f agent/templates/BRAINSTORM_TEMPLATE.md
test -f agent/templates/PLAN_TEMPLATE.md
test -f agent/templates/PROMPT_CONTRACT_TEMPLATE.md
test -f agent/templates/AGENT_REPORT_TEMPLATE.md
test -f agent/templates/OMNI_REVIEW_TEMPLATE.md
test -f agent/templates/REPAIR_TEMPLATE.md
test -f agent/templates/SEAL_TEMPLATE.md
test -f agent/templates/ORCHESTRATED_PROMPT_TEMPLATE.md
test -f agent/templates/PROMPT_PACK_TEMPLATE.md
test -f agent/templates/REVIEW_PROMPT_TEMPLATE.md
test -f agent/reports/CODEOPS_0A_AGENT_NATIVE_HYBRID_CONTROL_PROTOCOL.md
test ! -d .aurel/codeops
git diff --name-only | grep -E '^(src/|tests/|docs/)' && echo "FORBIDDEN_CHANGE" || true
```

Results recorded at commit time in final response.

pytest, ruff, mypy, coverage, bandit: **not run** (docs/process patch only).

---

## 10. Remaining risks

- Templates are v1.6 initial drafts; real P tasks may reveal section gaps requiring template refinement in a future CodeOps patch.
- CODEOPS-0B (Preflight Teeth) is not yet implemented — preflight enforcement remains manual via prompt contracts.
- No automated hook validates CodeOps compliance; discipline relies on prompt contracts and OMNI review.
- Root `AGENTS.md` shim is new; some tools may need time to discover it vs `agent/AGENT.md`.

---

## 11. Next recommended CodeOps step

**CODEOPS-0B — Preflight Teeth** (future only, not implemented)

Planned scope: automated preflight checks before agent execution (git cleanliness, canon snapshot, forbidden tree detection). Requires explicit future task authorization.

Subsequent future items:

- CODEOPS-0C — Report-Backed Active Task Projection
- CODEOPS-0D — Parallel Work Protocol

---

**Final law:** CodeOps is not a new tree. CodeOps is the discipline that makes the existing `agent/` tree execute better.
