# COPY/PASTE PROMPT — {{P_ID}} {{TITLE}}

You are implementing **{{P_ID}} — {{TITLE}}** in the Aurel / GG Governed Agentic Runtime repository.

---

## 0. Git / Worktree Discipline

Run first:

```bash
git branch --show-current
git status --short
```

Rules:

- Work on current `master`/`main` only.
- **No branch.**
- **No push.**
- Do not rewrite history.
- Do not amend previous commits.
- Do not delete `.venv`.
- Do not silently switch to system Python.
- Do not stage unrelated files.
- Final git status must be clean except pre-existing unrelated untracked packaging artifacts if they existed before the task and are explicitly reported.

If unrelated dirty or untracked files exist (other than known pre-existing zip artifacts):

```
STOP.
Report them.
Do not continue.
```

---

## 1. Read Existing Repo Canon

Before editing, inspect:

```
agent/AGENT.md
agent/CODEOPS.md
agent/ACTIVE_TASK.md
agent/ROADMAP.md
agent/STATE.md
agent/ARCHITECTURE.md
agent/DECISIONS.md
agent/TESTS.md
agent/REPORTS.md
{{ADDITIONAL_CANON_FILES}}
```

Do not update all `agent/` files blindly.
Use `agent/TESTS.md` as validation command authority.

---

## 2. Current Task

**Task ID:** {{P_ID}}

**Title:** {{TITLE}}

**Mission:** {{MISSION_SUMMARY}}

---

## 3. Roadmap Version

AUREL Roadmap v5.1 — Integration-First Roadmap

---

## 4. Current Roadmap Position

Last completed: {{LAST_COMPLETED}}

Current: {{P_ID}} — {{TITLE}}

Next expected: {{NEXT_TASK}}

---

## 5. Integration-First Law

| Layer | Required in this task |
|---|---|
| Backend capability | {{YES_NO_OR_UNAVAILABLE}} |
| Versioned contract/schema | {{YES_NO_OR_UNAVAILABLE}} |
| Projection/API/Event/read model | {{YES_NO_OR_UNAVAILABLE}} |
| CLI/Shell/TUI binding | {{YES_NO_OR_UNAVAILABLE}} |
| Trace/evidence/report binding | {{YES_NO_OR_UNAVAILABLE}} |
| Operator-testable path | {{LIVE_SIMULATED_DEV_FIXTURE_OR_UNAVAILABLE}} |

Truth labels (use honestly):

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

## 6. CodeOps Classification

| Field | Value |
|---|---|
| Task Pattern | {{PATTERN}} |
| Execution Mode | {{MODE}} |
| Risk Tier | {{RISK_TIER}} |
| Validation Depth | {{VALIDATION_DEPTH}} |

Operator selected tool/model at dispatch time.
Do not perform model routing.

---

## 7. Core Law

- CodeOps is not a new tree; `agent/` is governance source of truth.
- Prompt is an execution contract; execute the contract, not vibes.
- No duplicate state, validation, evidence, or decision surfaces.
- Evidence over confidence.
- Clean git is part of done.

---

## 8. Mission

{{DETAILED_MISSION}}

**Smallest correct scope:** {{SMALLEST_CORRECT_SCOPE}}

**What this must prove:** {{PROOF_REQUIRED}}

---

## 9. Hard Boundaries

Do not:

- {{BOUNDARY_1}}
- {{BOUNDARY_2}}
- {{BOUNDARY_3}}
- Fake LIVE or TRACE_VERIFIED
- Weaken tests/governance to pass
- Create branch unless explicitly instructed
- Push
- Duplicate agent/ state surfaces
- Touch forbidden paths: {{FORBIDDEN_PATHS}}

---

## 10. Affected Layers

| Layer | Change |
|---|---|
| src/ | {{YES_NO_DETAILS}} |
| tests/ | {{YES_NO_DETAILS}} |
| agent/ | {{YES_NO_DETAILS}} |
| docs/ | {{YES_NO_DETAILS}} |

---

## 11. Baseline Assumption

{{BASELINE_ASSUMPTION}}

If baseline is wrong, STOP and report before implementing.

---

## 12. Operating Model — Internal Engineering Passes

1. Read canon
2. Inspect repo
3. Implement minimal correct patch
4. Add/update tests if required
5. Validate per `agent/TESTS.md`
6. Update existing canon (minimal)
7. Create report if required
8. Commit
9. Final report

---

## 13. Vertical Integration Loop

For each layer touched, verify:

- [ ] Backend logic exists and is correct
- [ ] Contract/schema is versioned if applicable
- [ ] Projection/read path exists if applicable
- [ ] CLI/binding exists if applicable
- [ ] Evidence/report linked if applicable
- [ ] Operator can test or UNAVAILABLE is declared with reason

---

## 14. Implementation Requirements

### Create

{{FILES_TO_CREATE}}

### Modify

{{FILES_TO_MODIFY}}

### Core objects / contracts

{{CORE_OBJECTS}}

---

## 15. Research-Inspired Ideas To Integrate Now

{{RESEARCH_IDEAS_OR_NONE}}

Only integrate if in scope. Do not expand scope for research ideas.

---

## 16. Tests

{{TEST_REQUIREMENTS}}

Run tests documented in `agent/TESTS.md`.

---

## 17. Docs / State / Report Updates

| File | Update |
|---|---|
| agent/ACTIVE_TASK.md | {{UPDATE}} |
| agent/ROADMAP.md | {{UPDATE}} |
| agent/STATE.md | {{UPDATE}} |
| agent/DECISIONS.md | {{UPDATE}} |
| agent/reports/ | {{REPORT_FILE}} |
| agent/REPORTS.md | Link report |

Do not update files not listed unless required and reported.

---

## 18. Validation Strategy

Mandatory:

```bash
{{VALIDATION_COMMAND_1}}
{{VALIDATION_COMMAND_2}}
```

Scope checks:

```bash
{{SCOPE_CHECK_1}}
```

Record exact commands run in final report.

---

## 19. Acceptance Criteria

- [ ] {{AC_1}}
- [ ] {{AC_2}}
- [ ] {{AC_3}}
- [ ] Validation run and recorded
- [ ] Canon updated minimally
- [ ] Report created if required
- [ ] Commit created
- [ ] Final git status clean

---

## 20. Stop Conditions

Stop and report if:

- Unrelated dirty files
- Canon conflict
- Scope requires forbidden paths
- Validation fails unrecoverably in scope
- Branch or push would be required

---

## 21. Commit Requirement

Stage only in-scope files.

```bash
git add {{STAGED_FILES}}
git commit -m "{{COMMIT_MESSAGE}}"
```

Do not push.

---

## 22. Final Response Format

Return:

```
RESULT — {{P_ID}}

Summary:
Files created:
Files modified:
Existing canon preserved:
Tests added/updated:
Validation run:
Validation not run:
Commit hash:
Commit message:
Final git status:
Remaining risks:
Next recommended task:
Done / Not Done:
```

---

## 23. Final Reminder

Operator selected tool/model at dispatch time.
Do not perform model routing.

Execute the contract. Report honestly. Do not fake done.
