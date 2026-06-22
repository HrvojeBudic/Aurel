---
name: analyze-aurel
description: Performs deep multi-phase analysis of Aurel (governed agentic runtime) — architecture, modules, invariants, bugs, test gaps, and governance risks — and produces structured audit reports and phased fix plans. Use when the user asks to analyze Aurel deeply, audit architecture, investigate bugs or errors, review modules, assess runtime health, or craft a fix plan before implementation.
---

# Analyze Aurel

## Overview

Use this skill for **deep investigation and fix planning** before code changes. It produces two artifacts:

1. **Analysis Report** — precise audit with evidence, findings, and severity
2. **Fix Plan** — phased, minimal-scope plan with acceptance criteria

For tactical implementation after the plan is approved, hand off to `debug-aurel`.

## When to Use

| Scenario | Analysis mode |
|----------|---------------|
| Failing test, runtime error, unexpected behavior | `bug` |
| Module boundaries, coupling, ownership questions | `architecture` |
| Single-module or phase (P1.x) review | `module-audit` |
| Baseline health, regression sweep, pre-release | `health-check` |
| Review a proposed patch before applying | `pre-patch-review` |

## Workflow Checklist

Copy and track progress:

```
Analysis Progress:
- [ ] Phase 1 — Orient
- [ ] Phase 2 — Scope
- [ ] Phase 3 — Evidence
- [ ] Phase 4 — Module scan
- [ ] Phase 5 — Invariant audit
- [ ] Phase 6 — Deliverables (report + plan)
```

---

## Phase 1 — Orient

Read in order **before any code changes**:

1. `agent/ACTIVE_TASK.md` — current objective and acceptance criteria
2. `agent/STATE.md` — what works today and known limits
3. `agent/ARCHITECTURE.md` — module map and execution pipelines
4. `agent/TESTS.md` — canonical compile and test commands
5. `agent/ROADMAP.md` — phase context (e.g. P1.4.x)
6. `agent/DECISIONS.md` — prior non-obvious choices

When scope crosses modules or ownership is unclear, read [references/module-ownership.md](references/module-ownership.md).

---

## Phase 2 — Scope

State these fields explicitly at the start of your analysis:

| Field | What to record |
|-------|----------------|
| **Trigger** | User symptom, failing test, architecture question, or audit request |
| **Boundary** | Single module, pipeline stage, phase (P1.x), or full-system |
| **Invariants at risk** | From [references/invariants.md](references/invariants.md) |
| **Analysis mode** | `bug` / `architecture` / `module-audit` / `health-check` / `pre-patch-review` |
| **Non-goals** | What will NOT be changed (e.g. no governance weakening) |

If scope is ambiguous, ask one focused question before proceeding.

---

## Phase 3 — Evidence

Run diagnostics **before theorizing**. Record every command and its outcome.

### Baseline health

```bash
python -m agentic_runtime.cli status [--json]
python3 -m compileall src tests
```

### Targeted tests

Map failure to module via [references/pipeline-map.md](references/pipeline-map.md), then:

```bash
PYTHONPATH=src:. pytest tests/<relevant>.py -q
```

### Full suite (cross-cutting issues)

```bash
PYTHONPATH=src:. pytest -q
python -m agentic_runtime.cli verify
```

### Release surface (public APIs, config, shared contracts)

```bash
ruff check src tests
mypy src/agentic_runtime
python -m agentic_runtime.cli alpha-seal
```

### Source inspection

Also inspect when relevant:

- Failing trace records and structured result objects
- Source under `src/agentic_runtime/`
- Matching tests under `tests/`
- Phase specs under `docs/` (e.g. P1.4.x specs)
- Config under `config/aurel/` for identity/persona layers

**Rule:** Reproduce or pinpoint the exact failure/missing behavior before proposing fixes.

---

## Phase 4 — Module Scan

Walk the pipeline from [references/pipeline-map.md](references/pipeline-map.md). For each stage in scope, record:

- **Owner module** (from module-ownership map)
- **Inputs / outputs / structured result types**
- **Failure modes observed or inferred**
- **Test coverage** (file names, gaps)
- **Coupling risks** (hidden dependencies, cross-module leaks)

### Bug routing heuristics

| Symptom | Route to |
|---------|----------|
| Path traversal, symlink, allowlist, root boundary | `canonical_path.py`, `sandbox.py`, `sandbox_policy.py` |
| Denied or over-permissive actions | `policy.py`, `approval.py`, `hitl.py`, sandbox profile |
| Malformed or invalid plans | Provider schemas, `plan_validator.py`, `RepoPlanValidator` |
| Missing or misleading audit output | `trace.py`, structured result objects |
| Test mutation or verification bypass | `verifier.py`, protected-file tests |
| Prompt issues | `prompt_system.py`, manifest validation, redacted summaries |
| Tool manifest issues | `tool_manifest/` models, validation, loader, registry, fixtures |
| Repo-agent failures | context builder → planner → plan validator → patch executor → test adapter → repair loop |
| Identity/persona issues | `identity/` loaders, validators, `config/aurel/` |

---

## Phase 5 — Invariant Audit

Cross-check every finding against [references/invariants.md](references/invariants.md).

Classify each finding:

| Severity | Meaning |
|----------|---------|
| **Critical** | Governance breach, security boundary, or data integrity |
| **High** | Incorrect behavior in production path |
| **Medium** | Correctness edge case, missing validation, doc drift |
| **Low** | Style, minor coupling, non-blocking tech debt |

Assign a unique finding ID (e.g. `F-001`) for traceability in the report and plan.

---

## Phase 6 — Deliverables

Produce **two artifacts**. Use templates in `references/`.

### A. Analysis Report

Follow [references/report-template.md](references/report-template.md). Modeled on existing phase reports in `agent/reports/` (e.g. P1.4.1).

Required sections: Summary, Scope, Architecture context, Evidence, Findings table, Test coverage, Known limitations, Explicitly not in scope.

### B. Fix Plan

Follow [references/plan-template.md](references/plan-template.md).

Required sections: Objective, Constraints, Root cause hypothesis, Phased approach, File change map, Test strategy, Risk register, Acceptance criteria, Agent doc updates.

### Handoff rules

- **Analysis-only requests:** Do not implement fixes. End with: *Ready for implementation — invoke debug-aurel or proceed with Phase 0.*
- **Analysis + fix requests:** Complete the report and plan first, then switch to `debug-aurel` for implementation.
- Save reports under `agent/reports/` when the analysis completes a phase or significant audit.

---

## Output Quality Bar

- Every finding has: ID, severity, module, file:line reference, root cause, affected invariant
- Every plan phase has: objective, files, tests, pass/fail acceptance criteria
- Evidence section lists commands run and outcomes (including skips)
- No governance weakening proposed as a shortcut
- Explanations are concrete enough for another engineer to audit

## Additional Resources

- Module ownership: [references/module-ownership.md](references/module-ownership.md)
- Invariants: [references/invariants.md](references/invariants.md)
- Pipeline map: [references/pipeline-map.md](references/pipeline-map.md)
- Report template: [references/report-template.md](references/report-template.md)
- Plan template: [references/plan-template.md](references/plan-template.md)
- Worked example: [examples/sample-analysis.md](examples/sample-analysis.md)

## What This Skill Does NOT Do

- Replace `debug-aurel` for tactical fixes
- Auto-commit or auto-push
- Weaken tests, policy, sandbox, verifier, or trace to pass
- Broad refactors unless the fix plan explicitly scopes them
