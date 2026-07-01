# P1.ENF-F-B — Roadmap v5.5 Canon Sync / Historical Docs Archive

**Date:** 2026-07-01  
**Pack:** P1.ENF-F-B  
**Status:** DONE — DOCS_CANON_SYNC / HISTORICAL_ARCHIVE / P2.9-B_NOT_DONE

## 1. Result Header

P1.ENF-F-B makes **Aurel Roadmap v5.5** the unambiguous active roadmap canon while preserving older roadmap/docs/reports as labeled historical evidence. Added `agent/CANON_INDEX.md`, active canon pointers in state/roadmap docs, index-level historical notices on v3.2 sections, Golden Thread B continuity binding, P2.6 correction guard, and focused docs/canon tests. No ROADMAP renumbering, no historical deletion, no P1.ENF-D1/P2.9-B implementation, no Shell LIVE claim.

## 2. Scope

- Identify active vs historical docs
- Add v5.5 active canon pointer
- Label historical/superseded docs via canon index
- Bind Golden Thread B as current continuity evidence
- Preserve P2.6 = Surface Projection / API / Event Bridge
- Sync reports/state/active task/tests
- Add docs/canon status tests

Not in scope: P1.ENF-D1, P1.ENF-E, P2.REVIEW-A, P2.9-B+, ROADMAP rewrite/renumbering, Shell router, product UI, historical deletion.

## 3. Git / Worktree Preflight

- Branch: `master`
- Initial status: clean
- Unrelated dirty files: none
- P1.ENF-D1 dirty/untracked files: none
- P1.ENF-E dirty/untracked files: none
- P2.REVIEW-A dirty/untracked files: none
- P2.9-B dirty/untracked files: none
- `.venv/bin/python`: present
- Preflight result: **PASS**

## 4. Prerequisite Evidence Gate

### P1.ENF-C

- Report found: yes
- Report path: `agent/reports/P1_ENF_C_GOLDEN_THREAD_B_GOVERNANCE_CONTINUITY.md`
- Indexed: yes (`agent/REPORTS.md`)
- Validation evidence: yes (17 Golden Thread B tests; recorded in report and `agent/TESTS.md`)
- Commit evidence: yes (`63a6c87` feat + `431987a` docs hash record)
- Final/current git clean: yes (clean before P1.ENF-F-B edits)
- Golden Thread B current continuity evidence: yes
- Gate result: **PASS**

### Prior ENF chain

- P1.ENF-A: report exists, indexed, validation recorded
- P1.ENF-A-OMNI-R1: report exists, indexed, commit `8bf05de`
- P1.ENF-B: report exists, indexed, commit `47ea128`
- P1.ENF-F-A: report exists, indexed, commit `d91d2e2`

- P2.9-B remains NOT DONE: yes
- P1.ENF-D1 / P1.ENF-E / P2.REVIEW-A not started: yes

## 5. Canon Discovery

### Docs inspected

- `agent/AGENT.md`, `agent/CODEOPS.md`, `agent/ACTIVE_TASK.md`, `agent/ROADMAP.md`, `agent/STATE.md`, `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`, `agent/TESTS.md`, `agent/REPORTS.md`

### Reports inspected

- All P1.ENF-* reports; representative P2.* and P1.* historical reports; `docs/roadmap/P1.5.*`

### Active canon candidates

- `agent/ROADMAP.md` (v5.5 header)
- `agent/STATE.md`
- `agent/CANON_INDEX.md` (created)
- `agent/CODEOPS.md`, `agent/AGENT.md`

### Historical/superseded docs found

- `agent/ROADMAP.md` v3.2 doctrine/system map sections
- `agent/ARCHITECTURE.md` v3.2 system architecture section
- `docs/roadmap/P1.5.*` sealed docs
- Many `agent/reports/P1.*` with v5.1 headers
- `agent/templates/PLAN_TEMPLATE.md` v5.1 header

### Drift-prone references

- ROADMAP "Current phase" mirrors still cite older next-task language in places (DRIFT_WARNING)
- v5.1 headers in historical reports (expected; labeled in CANON_INDEX)
- Legacy A-Hub/S-Hub/L-Hub/Forum/Archivium taxonomy in v3.2 sections (HISTORICAL_REFERENCE)

### P2.6 drift references

- Discarded Attention/Notification/Inbox direction documented in P2.6 reports and ROADMAP mirrors — not active canon

### LIVE / TRACE_VERIFIED references

- Historical reports contain boundary disclaimers (not active overclaims)
- Active STATE/CANON_INDEX/ACTIVE_TASK do not claim Shell LIVE

### Discovery matrix

Created in `agent/CANON_INDEX.md`.

## 6. Active Canon Pointer

- v5.5 active canon pointer added: yes
- Locations: `agent/ROADMAP.md` (Active roadmap canon section), `agent/CANON_INDEX.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`
- Golden Thread B continuity pointer: yes (`agent/CANON_INDEX.md`, `agent/STATE.md`)
- Current pack pointer: P1.ENF-F-B DONE
- Next planned pack pointer: P1.ENF-D1
- P2.9-B NOT DONE pointer: yes (STATE, CANON_INDEX, ACTIVE_TASK)
- Older docs historical notice: index-level in CANON_INDEX; block notices on v3.2 sections in ROADMAP and ARCHITECTURE

## 7. Historical Docs / Archive Labeling

- Index-level labeling used: yes (`agent/CANON_INDEX.md`)
- Individual doc labels added: v3.2 block notices in ROADMAP.md and ARCHITECTURE.md only
- Historical docs deleted: **no**

| Label | Examples |
|-------|----------|
| HISTORICAL_ARCHIVE | `docs/roadmap/P1.5.*`, pre-ENF P1 reports |
| HISTORICAL_REFERENCE | v3.2 doctrine, Golden Thread A, P2 contract reports |
| SUPERSEDED_BY_V5_5 | v5.1 report headers, docs/roadmap P1.5 docs |
| DRIFT_WARNING | ROADMAP progress mirrors, PLAN_TEMPLATE v5.1 header |
| DO_NOT_USE_AS_CURRENT_TASK_SOURCE | All labeled historical entries in CANON_INDEX |

## 8. Golden Thread B Binding

- P1.ENF-C report referenced: yes
- Golden Thread B described as current continuity: yes
- P1.8–P2.9-A chain referenced: yes
- P1.ENF repair/audit/gate chain referenced: yes
- Shell live behavior claimed: **no**
- P2.9-B marked NOT DONE: yes

## 9. P2 Section Correction Guard

- P2.6 Surface Projection / API / Event Bridge preserved: yes
- Wrong P2.6 active-canon references: none in active canon docs
- P2.9-B remains NOT DONE: yes
- P2.9-C/D/P2.10+ remain not started: yes

## 10. Reports / State Sync

- `agent/REPORTS.md` updated: yes
- `agent/STATE.md` updated: yes
- `agent/ACTIVE_TASK.md` updated: yes
- `agent/ROADMAP.md` updated: yes (canon header + v3.2 notice only)
- `agent/ARCHITECTURE.md` updated: yes (v3.2 notice only)
- `agent/DECISIONS.md` updated: yes
- `agent/TESTS.md` updated: yes
- `agent/CANON_INDEX.md` created: yes

## 11. Tests / Checks Added or Run

- `tests/test_docs_canon_status.py` created: yes (9 tests)
- Docs tests run: yes
- Grep checks run: yes (recorded below)
- Positive active-canon check: PASS
- P2.6 correct-meaning check: PASS
- P2.6 wrong-meaning check: no active-canon violations (historical discard notes only)
- LIVE / TRACE_VERIFIED review: active docs clean; historical boundary language classified

## 12. Validation Run

| Check | Result |
|-------|--------|
| compileall | PASS |
| Golden Thread B regression | 17 passed |
| validation truth / drift gates | 18 passed |
| entrypoint audit regression | 16 passed |
| docs canon status tests | 9 passed |
| ruff | PASS |
| baseline mypy | PASS |
| core strict probe | PASS (5 files, silent imports) |
| git status after validation | clean (expected post-commit) |

**Not run:** full suite, coverage, Bandit, optional selector

## 13. No-Scope-Expansion Proof

| Item | Implemented |
|------|-------------|
| P1.ENF-D1 | no |
| P1.ENF-E | no |
| P2.REVIEW-A | no |
| P2.9-B | no |
| P2.9-C/D/P2.10+ started | no |
| Shell command router | no |
| Product UI | no |
| P2 vertical slice | no |
| ROADMAP rewritten | no |
| Roadmap numbering changed | no |
| Historical evidence deleted | no |

## 14. Files Created / Modified

**Created:**

- `agent/CANON_INDEX.md`
- `agent/reports/P1_ENF_F_B_ROADMAP_V55_CANON_SYNC_HISTORICAL_DOCS_ARCHIVE.md`
- `tests/test_docs_canon_status.py`

**Modified:**

- `agent/ROADMAP.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`
- `agent/REPORTS.md`
- `agent/ARCHITECTURE.md`
- `agent/DECISIONS.md`
- `agent/TESTS.md`

## 15. What Was Deliberately Not Implemented

- P1.ENF-D1 identity kernel invariant enforcement
- P1.ENF-E sandbox safe backend gating
- P2.REVIEW-A first true P2 vertical slice decision
- P2.9-B rerun
- P2 true vertical slice
- Shell command router
- Product UI
- ROADMAP rewrite / renumbering
- Historical evidence deletion
- Full docs site rewrite
- Sandbox backend hardening
- Identity CLI refactor
- repo_agent rewrite

## 16. Remaining Risks / Limitations

- **Old roadmap docs:** v3.2/v5.1 material remains in body text of ROADMAP mirrors — labeled, not rewritten
- **Old reports:** v5.1 headers preserved; CANON_INDEX is routing authority
- **ROADMAP drift:** "Current phase" mirrors may lag ENF next-task; STATE/CANON_INDEX win
- **P2 contract-only lattice:** P2 remains contract-only; P2.9-B NOT DONE
- **UnsafeLocalSandbox:** unchanged
- **Identity invariant enforcement:** future P1.ENF-D1
- **Full suite/coverage:** not run this pack

## 17. Next Recommended Step

**P1.ENF-D1 — Identity Kernel Invariant Enforcement Deepening**

Alternative operator path: **P2.9-B** Shell Exit Seal Readiness rerun.

## 18. Commit Hash

_(recorded after commit)_

## 19. Final Git Status

_(recorded after commit)_
