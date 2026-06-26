# ORCHESTRATED PROMPT — {{P_ID}} {{TITLE}}

Single executor, phased work. Operator selected tool/model at dispatch time.

---

## Mission

{{MISSION_SUMMARY}}

**Smallest correct scope:** {{SMALLEST_CORRECT_SCOPE}}

---

## Rules

- Do not create branches.
- Do not push.
- Do not rewrite history.
- Do not expand scope.
- Execute phases in order.
- Stop and report on blockers.

---

## Phase 1 — Read Canon

Read before any changes:

```
agent/AGENT.md
agent/CODEOPS.md
agent/ACTIVE_TASK.md
agent/ROADMAP.md
agent/STATE.md
agent/TESTS.md
agent/REPORTS.md
{{ADDITIONAL_CANON}}
```

Report conflicts before proceeding.

---

## Phase 2 — Inspect Repo

```bash
git branch --show-current
git status --short
{{ADDITIONAL_INSPECTION}}
```

Confirm no unrelated dirty files. Stop if found.

---

## Phase 3 — Local Plan

Confirm in writing (brief):

- Files to create/modify
- Integration-first slice
- Truth labels
- Validation commands from `agent/TESTS.md`
- Acceptance criteria

Do not expand beyond prompt scope.

---

## Phase 4 — Implement

Implement minimal correct patch.

Allowed files:

```
{{ALLOWED_FILES}}
```

Forbidden:

```
{{FORBIDDEN_FILES}}
```

---

## Phase 5 — Validate

```bash
{{VALIDATION_COMMANDS}}
```

Record exact output.

---

## Phase 6 — Update Existing Canon

Update only required files:

| File | Update |
|---|---|
| {{FILE}} | {{UPDATE}} |

Do not duplicate state surfaces.

---

## Phase 7 — Evidence

Create report if required: `agent/reports/{{REPORT_FILE}}`

Link from `agent/REPORTS.md`.

---

## Phase 8 — Commit

```bash
git add {{STAGED_FILES}}
git commit -m "{{COMMIT_MESSAGE}}"
```

Do not push.

---

## Phase 9 — Final Report

Return:

```
RESULT — {{P_ID}}

Summary:
Phases completed:
Files created:
Files modified:
Validation run:
Canon updated:
Commit hash:
Final git status:
Remaining risks:
Done / Not Done:
```
