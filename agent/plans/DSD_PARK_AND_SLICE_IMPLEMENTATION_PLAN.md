# PLAN — DSD-PARK-01 Park & Slice (Dual-Track Hygiene + Safe Migration Resume)

**Status:** APPROVED FOR EXECUTION (operator-dispatched)  
**Date:** 2026-07-13  
**Owner:** Operator (Hrvoje) dispatches; Agent executes slices  
**Supersedes:** ad-hoc “953 uncommitted files on master” state — does **not** replace `MIGRATION_PLAN.md` (Task Pack 7 enterprise plan); this plan operationalizes it safely.

**Canonical formula:** OMNI designs → Hrvoje dispatches → Agent executes → `agent/` records → Git proves → OMNI reviews.

---

## 0. Current Canon Snapshot

| Field | Value |
|-------|-------|
| Active branch | `master` @ `130f061` (3 commits **ahead** of `origin/master`, unpushed) |
| Open feature branch | `feat/f8-time-plane` (1 commit: F8 plan only, not merged) |
| Dirty working tree | **953** items: 3 modified tracked + **950** untracked |
| LIVE runtime spine | `src/agentic_runtime/` (~606 `.py`, 8600+ tests green at last seal) |
| DSD scaffold | `src/dsd/` (~29 `.py`, S0 complete, S1 partial) |
| Broken packaging delta | `pyproject.toml` references `dsd.cli` / `dsd.demo` — **files do not exist** |
| Quarantine archive | `migration/quarantine/` (~643 files) — snapshot fork, not active code |
| Think-tank bulk | `OS/` (~195 files) — PDFs, extracts, agent specs — not runtime CI scope |
| Last DSD slice evidence | S0 treasury/entity: `tests/slices/test_S0_treasury_entity.py` (2/2 PASS per DEC-S0-01) |
| Active product track | F-series through F7 merged; **F8 next** on `agentic_runtime` |

**Canonical sources read for this plan:**
- [x] `agent/AGENT.md`, `agent/CODEOPS.md`, `agent/TESTS.md`
- [x] `MIGRATION_PLAN.md`, `DSD_CIVIC_FABRIC_CANON.md`, `DSD_CIVIC_FABRIC_PLAN.md`
- [x] `agent/reports/dsd-migration-reflector-phase0.md`
- [x] Git state (2026-07-13): branches, worktrees, dirty inventory

**Known blockers:**
1. Master working tree polluted — unsafe for F8 or DSD commits mixed together.
2. Uncommitted `pyproject.toml` would break `pip install -e .` if committed as-is.
3. Quarantine fork creates “two truths” confusion vs live `src/dsd/`.

---

## 1. Mission Summary

**Problem:** DSD hybrid migration (Task Pack 7) was started on `master` without git hygiene. ~950 untracked files (quarantine fork, OS think-tank, scaffold, canons) sit alongside 3 modified governance files. F8 product work cannot proceed safely on this tree.

**Goal:** Restore **dual-track** operation:
- **Track A (`master`):** clean, pushable, F8-ready — `agentic_runtime` unchanged except explicit F8 slices.
- **Track B (`feat/dsd-s0-s1`):** parked DSD migration — canon docs + S0/S1 code + slice tests only.

**Operator value:** Predictable git, no accidental loss of S0 work or migration canons, no broken install, clear resume point for DSD after F8.

**Smallest correct scope:** Hygiene + park + one sealed DSD branch commit — **not** full matrix rename, **not** quarantine import, **not** F8 implementation.

---

## 2. Roadmap Position

| Track | Current | Next |
|-------|---------|------|
| **A — Aurel runtime (F-series)** | F7 merged locally, unpushed | Push master → implement F8 on clean master |
| **B — DSD migration (Task Pack 7)** | S0 sealed (local), S1 partial, Phase 0 packaging incomplete | Park on `feat/dsd-s0-s1` → resume after F8 or explicit operator override |

**Parallel safety:** **NOT SAFE** on same branch/worktree. Sequential dual-track only.

---

## 3. Core Law (non-negotiable)

1. **Entity proposes, Runtime disposes** — do not rename core concepts (`CommandEnvelope`, `AgenticRuntime`, etc.) in Track A.
2. **Platform stays connected** — at every step both must hold:
   - `import agentic_runtime` + `python -m agentic_runtime.cli status` → OK
   - `import dsd` → OK (S0/S1 surface only until shims exist)
3. **No fake LIVE** — DSD branch does not claim Phase 0 sealed until `dsd` CLI exists and smoke passes.
4. **Clean git is part of done** — master must reach `git status --short` empty before F8 coding.
5. **History cannot be reconstructed** — quarantine archived **before** deletion, not silently dropped.
6. **Do not weaken tests/governance** to make migration pass.

---

## 4. CodeOps Classification

| Field | Value |
|-------|-------|
| Task Pattern | Hygiene + branch park + docs/code slice |
| Execution Mode | **LEAN** (Track A push); **LEAN→ELEVATED** (Track B commit with slice tests) |
| Risk Tier | **MEDIUM** (packaging/import surface); **LOW** for archive-only steps |
| Parallel Safety | **SEQUENTIAL ONLY** |
| Validation Depth | Lean gates per slice; full suite only if `pyproject.toml` or runtime paths touched on master |
| Review Needed | OMNI review after Phase A (master clean) and after Phase C (DSD branch sealed) |

---

## 5. File Triage Matrix (authoritative)

### 5.1 COMMIT on `feat/dsd-s0-s1` (~55 files)

```
# Canon + plan (root)
MIGRATION_PLAN.md
DSD_FULL_RENAMING_MATRIX.md
DSD_CIVIC_FABRIC_CANON.md
DSD_CIVIC_FABRIC_PLAN.md
DSD_MEMORY_FABRIC_CANON.md
AUREL_CONTINUITY_CANON.md
DSD_AUREL_INTELLIGENCE_MEMORY_RENAMING_SYNTHESIS.md

# DSD code (S0/S1 scaffold only)
src/dsd/**/*.py
src/dsd/py.typed

# Slice tests
tests/slices/test_S0_treasury_entity.py
tests/slices/test_S1_ledger.py

# Migration tooling + evidence
scripts/dsd_scope_enforce.sh
scripts/dsd_slice_gate.sh
agent/reports/DSD_DEEP_CANON_SYNTHESIS_2026-07-12.md
agent/reports/dsd-migration-reflector-phase0.md
agent/reports/dsd-phase0-mechanic-formalist-2026-07-12.md
agent/reports/dsd-phase0-stresstester-grounder-tests.md
agent/reports/DSD_CITIZENSHIP_RENAMING_CLEANUP_PLAN.txt
agent/evidence/memory_continuity_S5.txt   # only if referenced by reports

# Governance (DSD-specific deltas only)
agent/DECISIONS.md          # DEC-S0-01 block
agent/ACTIVE_TASK.md        # S0 completion note — or move to report only (prefer report)
```

### 5.2 REVERT on master (do not commit broken packaging)

```
pyproject.toml  →  revert ALL uncommitted changes on master
                  (restore agentic-runtime name + scripts until dsd/cli.py exists)
```

**Track B may commit a *partial* pyproject delta later** in Phase 0 seal slice — see §8 Phase C2.

### 5.3 ARCHIVE then REMOVE from working tree

| Path | Action | Archive target |
|------|--------|----------------|
| `migration/quarantine/` | tarball + optional orphan branch | `~/Desktop/Aurel-archives/dsd-quarantine-2026-07-12.tar.gz` |
| `migration/` (after quarantine removed) | delete empty dirs or keep README only | — |
| `scratch/` | delete | none (ephemeral) |
| `implementer/` | delete or move to archive | optional tarball |
| `evidence/` (root, untracked) | review; keep only if seal artifacts | else archive |

**Orphan branch (optional, safer than delete):**
```bash
git checkout --orphan archive/dsd-quarantine-2026-07-12
# add migration/quarantine only, commit, push, return to master
```

### 5.4 EXCLUDE from Aurel runtime repo (never commit to master or dsd branch)

| Path | Reason |
|------|--------|
| `OS/` (~195) | Think-tank / PDF corpus — separate repo or external storage |
| `prototypes/` | Empty or out of scope |
| `src/dsd/**/__pycache__/` | gitignored |
| Empty scaffold dirs with only `__pycache__` | do not commit empty packages |

### 5.5 `.gitignore` additions (Phase A — master hygiene)

Add to `.gitignore` (minimal, explicit):

```gitignore
# DSD migration ephemeral / out-of-repo-scope (2026-07-13 park plan)
/migration/quarantine/
/scratch/
/implementer/
/OS/
/evidence/
```

**Note:** `src/dsd/` is **not** ignored — it lives on `feat/dsd-s0-s1`.

---

## 6. Implementation Plan

### Phase A — Stabilize master (Track A prep) ⏱ ~15 min

**Objective:** Clean master working tree; push F7 commits; master ready for F8.

| Step | Command / action | Verify |
|------|------------------|--------|
| A1 | **Backup quarantine** before any delete: `tar -czf ~/Desktop/Aurel-archives/dsd-quarantine-2026-07-12.tar.gz -C /home/hrvojeb/Desktop/Aurel migration/quarantine` | tarball exists, size > 0 |
| A2 | Stash or copy DSD commit set aside (see §5.1) — agent uses `git stash push -u -m "dsd-park-wip"` **only** if not branching yet; prefer direct branch in A4 | files preserved |
| A3 | Revert `pyproject.toml` on master: `git checkout -- pyproject.toml` | `git diff pyproject.toml` empty |
| A4 | Update `.gitignore` per §5.5 | `git diff .gitignore` shows additions only |
| A5 | Remove ephemeral paths from working tree: `rm -rf migration/quarantine scratch implementer` (after A1 tarball) | paths gone |
| A6 | `git status --short` — expect **empty** or only `.gitignore` + intentional docs | **STOP if OS/ or src/dsd/ still dirty on master** |
| A7 | If `.gitignore` changed: commit on master: `chore: gitignore DSD ephemeral paths and quarantine archive` | one commit |
| A8 | Push master: `git push origin master` | remote matches local 130f061 lineage |
| A9 | Smoke: `.venv/bin/python -m agentic_runtime.cli status` | exit 0 |
| A10 | Record in `agent/reports/DSD_PARK_01_MASTER_HYGIENE.md` | report linked from REPORTS.md |

**Phase A exit criteria:**
- [ ] `git status --short` empty on master
- [ ] `origin/master` includes F7 env CAS-pointer fix (3 commits)
- [ ] Full agentic_runtime smoke OK
- [ ] Quarantine tarball verified

**STOP if:** push rejected, tests fail, or uncommitted DSD files accidentally committed to master.

---

### Phase B — Park DSD slice branch (Track B create) ⏱ ~20 min

**Objective:** Move valuable DSD work off master onto dedicated branch without quarantine/OS noise.

| Step | Command / action | Verify |
|------|------------------|--------|
| B1 | From clean master: `git checkout -b feat/dsd-s0-s1` | branch created |
| B2 | Restore DSD files (if stashed: `git stash pop`; else copy from backup/tarball of §5.1 list) | files present |
| B3 | Stage **only** §5.1 paths — use explicit `git add` list, never `git add .` | `git diff --cached --stat` ≤ ~60 files |
| B4 | **Do not stage** `pyproject.toml` CLI entries yet | no `dsd=` scripts without `dsd/cli.py` |
| B5 | Commit: `feat(dsd): park S0/S1 slice + migration canon (Task Pack 7)` | one commit |
| B6 | Run slice validation (§7 Track B commands) | all pass |
| B7 | Write `agent/reports/DSD_PARK_01_S0_S1_BRANCH.md`; link from REPORTS.md | report exists |
| B8 | `git checkout master` — master stays clean | master has no DSD code commit if operator prefers master without dsd until merge; **OR** leave branch unpushed until OMNI review |

**Branch policy (operator choice — default recommended):**

| Option | Behavior |
|--------|----------|
| **Recommended** | `feat/dsd-s0-s1` stays **local/unpushed** until F8 milestone or OMNI review |
| Alternative | Push branch for backup: `git push -u origin feat/dsd-s0-s1` |

**Phase B exit criteria:**
- [ ] Branch contains S0/S1 + canons + reports + scripts
- [ ] No quarantine, OS, scratch on branch
- [ ] Slice tests pass
- [ ] Master checked out and clean after return

---

### Phase C — Resume F8 on master (Track A) ⏱ ongoing

**Objective:** Product forward motion; zero DSD rename on master until explicit dispatch.

| Step | Action |
|------|--------|
| C1 | `git checkout master` |
| C2 | `git checkout feat/f8-time-plane` OR create fresh from master |
| C3 | Implement F8 per `feat/f8-time-plane` plan — **touch only `agentic_runtime` paths** |
| C4 | Commit F8 slices on feature branch; merge to master when sealed |
| C5 | Push master after each merged F8 slice |

**Hard boundary:** No `src/dsd/` edits on master during F8 unless operator explicitly overrides with a new dispatch.

---

### Phase D — DSD Phase 0 seal (Track B resume) ⏱ after F8 or parallel on branch

**Objective:** Complete Task Pack 7 exit criteria from `MIGRATION_PLAN.md` §7.

| Step | Deliverable | Verify |
|------|-------------|--------|
| D1 | Create `src/dsd/cli.py` — thin shim delegating to `agentic_runtime.cli:main` | `dsd --help` works |
| D2 | Create `src/dsd/demo.py` — thin shim to `agentic_runtime.demo:main` | `dsd-demo` works |
| D3 | Update `pyproject.toml` on **feat/dsd-s0-s1 only**: dual scripts + include dsd* | `pip install -e .` OK |
| D4 | Add compat re-exports in `agentic_runtime/__init__.py` (optional thin) | legacy imports unchanged |
| D5 | Complete S1 ledger slice tests + any missing `records/` module wiring | slice tests green |
| D6 | Seal report: `agent/reports/DSD_PHASE0_PACKAGING_SEAL.md` | linked |
| D7 | OMNI review → merge `feat/dsd-s0-s1` → master **only after** F8 gate satisfied or operator orders merge |

**Phase 0 seal acceptance (from MIGRATION_PLAN.md):**
- [ ] `MIGRATION_PLAN.md` committed (on branch)
- [ ] `pip install -e .` + `import dsd` + `dsd --help` + `aurel --help`
- [ ] Slice + scaffold tests pass
- [ ] No logic duplication between trees (dsd shims only for CLI until institution slices)
- [ ] Clean git on branch

---

### Phase E — Institution slices (Track B long tail) ⏱ post Phase 0

Execute per `DSD_FULL_RENAMING_MATRIX.md` — **one institution per branch**:

```
feat/dsd-s2-charter      # policy → charter shims
feat/dsd-s3-citizenship  # identity → citizenship
feat/dsd-s4-council      # aurel_flow → council
...
```

Each slice:
1. Branch from latest `feat/dsd-*` or master after merge
2. Matrix section only — no cross-institution drive-by
3. Compat alias in `agentic_runtime` during transition
4. Focused pytest + `scripts/dsd_slice_gate.sh`
5. Report in `agent/reports/`
6. Merge when slice gate green + OMNI review

**Never:** mass-rename 600 files in one commit; import quarantine fork wholesale.

---

## 7. Validation Commands

### Track A — master hygiene (after Phase A)

```bash
cd /home/hrvojeb/Desktop/Aurel
git status --short                    # must be empty
.venv/bin/python -m compileall src/agentic_runtime tests
.venv/bin/python -m agentic_runtime.cli status
.venv/bin/python -m agentic_runtime.cli demo-harness buggy_calculator
# Optional before F8 merge: full verify (~30 min)
# .venv/bin/python -m agentic_runtime.cli verify
```

### Track B — DSD branch (after Phase B/D)

```bash
cd /home/hrvojeb/Desktop/Aurel
git checkout feat/dsd-s0-s1
.venv/bin/python -m compileall src/dsd tests/slices
.venv/bin/python -m pytest tests/slices/ -q --tb=line
.venv/bin/python -c "import dsd; from dsd import ResourceAccount, CognitiveSession, ExecutionKernel; print(dsd.__version__)"
# After D1-D3 only:
pip install -e .
dsd --help
aurel --help
bash scripts/dsd_slice_gate.sh        # if present and executable
.venv/bin/python -m ruff check src/dsd tests/slices
.venv/bin/python -m mypy src/dsd       # best-effort; record failures
```

### Pre-delete safety (Phase A1)

```bash
tar -tzf ~/Desktop/Aurel-archives/dsd-quarantine-2026-07-12.tar.gz | head
tar -tzf ~/Desktop/Aurel-archives/dsd-quarantine-2026-07-12.tar.gz | wc -l   # expect ~643 files
```

---

## 8. Git Workflow Summary

```
Timeline (recommended):

  [now]  master (dirty) ──Phase A──► master (clean) ──push──► origin/master
                │
                └──Phase B──► feat/dsd-s0-s1 (park commit, local)
                                      │
                                      └──Phase D──► Phase 0 seal (later)
                
  master ──Phase C──► feat/f8-time-plane ──merge──► master (F8)
                
  After F8: merge feat/dsd-s0-s1 ──► master (when OMNI approves)
```

| Item | Policy |
|------|--------|
| Branch creation | **Explicitly instructed** by this plan (feat/dsd-s0-s1, archive/* optional) |
| Push master | **Yes** after Phase A (operator requested sync) |
| Push feat/dsd-s0-s1 | Optional after Phase B; recommended after Phase D seal |
| Commit granularity | Phase A: 1 (.gitignore). Phase B: 1 (park). Phase D: 1–2 (CLI + pyproject) |
| Never commit | quarantine, OS/, scratch/, broken pyproject CLI refs |

---

## 9. Acceptance Criteria (whole plan)

### Phase A — Master hygiene
- [ ] Quarantine archived to tarball (verified listing)
- [ ] master `git status` clean
- [ ] `pyproject.toml` reverted on master (no broken dsd CLI refs)
- [ ] `.gitignore` updated
- [ ] `origin/master` pushed with 3 F7 commits
- [ ] `agentic_runtime.cli status` passes
- [ ] Report `DSD_PARK_01_MASTER_HYGIENE.md` written

### Phase B — Park branch
- [ ] `feat/dsd-s0-s1` exists with §5.1 files only
- [ ] `tests/slices/` pass (2 files)
- [ ] master clean after checkout back
- [ ] Report `DSD_PARK_01_S0_S1_BRANCH.md` written

### Phase C — F8 (separate dispatch)
- [ ] F8 work only on feature branch, not mixed with DSD
- [ ] master remains integration spine for `agentic_runtime`

### Phase D — Phase 0 seal (future dispatch)
- [ ] `dsd/cli.py` + `dsd/demo.py` exist
- [ ] `pip install -e .` succeeds
- [ ] Dual CLI smoke passes
- [ ] Phase 0 seal report written

---

## 10. Stop Conditions

**HALT and report to operator if:**

1. `git push origin master` fails (auth, conflict) — do not force-push.
2. After revert, `agentic_runtime.cli demo` or `status` fails.
3. Staging `git add .` would include `OS/` or `migration/quarantine/`.
4. Slice tests fail on `feat/dsd-s0-s1` and fix requires touching `agentic_runtime` core logic.
5. Tarball creation fails or archive is empty — **do not delete quarantine**.
6. Unrelated dirty files appear mid-slice — stop, do not commit.
7. Operator has not confirmed quarantine backup before A5 delete step.

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Lose S0 work by mass delete | Park branch B before any delete; tarball quarantine |
| Break `pip install -e .` | Revert pyproject on master; CLI shims before packaging commit |
| F8 blocked by DSD noise | Phase A clean master first |
| Two-truth confusion (quarantine vs src/dsd) | Never import from quarantine; archive + gitignore |
| OS/ PDFs bloat repo | Permanent exclude; separate think-tank repo |
| Premature DSD merge breaks 8600 tests | Merge only after Phase 0 seal + elevated gate |
| Lost migration canons | Commit on feat/dsd-s0-s1 in Phase B |

---

## 12. What NOT To Do

- ❌ Delete all 953 files without backup
- ❌ Commit everything in one mega-commit
- ❌ Continue DSD rename on master alongside F8
- ❌ Import `migration/quarantine/` into `src/dsd/`
- ❌ Commit `pyproject.toml` dsd scripts before `dsd/cli.py` exists
- ❌ Rename `CommandEnvelope`, `AgenticRuntime`, etc. on Track A
- ❌ Weaken tests or governance for migration convenience
- ❌ Force-push master

---

## 13. Dispatch Sequence (copy/paste for operator)

**Dispatch 1 — Phase A (hygiene + push):**
> Execute Phase A of `agent/plans/DSD_PARK_AND_SLICE_IMPLEMENTATION_PLAN.md`. Backup quarantine tarball first. Revert pyproject on master. Update gitignore. Remove quarantine/scratch/implementer. Commit gitignore if needed. Push master. Smoke status. Write hygiene report.

**Dispatch 2 — Phase B (park branch):**
> Execute Phase B of same plan. Create `feat/dsd-s0-s1`. Commit §5.1 files only. Run slice tests. Write branch report. Return to clean master.

**Dispatch 3 — Phase C (F8):**
> On clean master, continue F8 on `feat/f8-time-plane`. No DSD file touches.

**Dispatch 4 — Phase D (later):**
> On `feat/dsd-s0-s1`, implement dsd CLI/demo shims + pyproject Phase 0 seal per plan §Phase D.

---

## 14. Related Documents

| Document | Role |
|----------|------|
| `MIGRATION_PLAN.md` | Enterprise hybrid rename strategy (Task Pack 7) |
| `DSD_FULL_RENAMING_MATRIX.md` | Mechanical rename source of truth (Phase E) |
| `DSD_CIVIC_FABRIC_PLAN.md` | S0–S6 sovereign continuity sequence |
| `agent/reports/dsd-migration-reflector-phase0.md` | Phase 0 meta-audit |
| `agent/templates/PROMPT_CONTRACT_TEMPLATE.md` | Next: per-phase prompt contracts |

---

**Plan ready for operator dispatch.**  
Next step: operator approves Phase A execution, or requests Prompt Contract for a specific phase.
