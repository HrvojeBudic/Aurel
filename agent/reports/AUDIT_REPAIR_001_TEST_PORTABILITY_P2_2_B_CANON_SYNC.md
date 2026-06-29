# AUDIT-REPAIR-001 — Test Portability + P2.2-B Canon Sync

**Repair ID:** AUDIT-REPAIR-001  
**Date:** 2026-06-29  
**Status:** REPAIR_DONE  
**Section context:** P2 — AurelShell; P2.2 — Per-Surface Local Navigation  
**Trigger:** Enterprise audit regression/stability blocker (F-001 repo-path drift)

---

## 1. Result Header

**Repair:** AUDIT-REPAIR-001 — Test Portability + P2.2-B Canon Sync  
**F-001 status:** FIXED — hardcoded `/home/hrvojeb/Desktop/GG` subprocess cwd removed  
**F-002 status:** CONFIRMED — P2.2-B canon already synced in commits `e9c25ad` / `4e1b57c`; validated post-repair  
**Full suite:** 6151 passed, 3 skipped (path-portability failures eliminated)  
**P2.2-C started:** No  
**Release-clean claimed:** No — release seal not in scope  
**LIVE claimed:** No  
**TRACE_VERIFIED claimed:** No  

## 2. Audit Findings Addressed

| ID | Severity | Action |
|----|----------|--------|
| F-001 | High | Fixed — portable repo-root discovery via `tests/repo_root.py` |
| F-002 | Medium | Confirmed — P2.2-B report/canon present; no fabrication required |
| F-003 | Backlog | Recorded — not implemented |
| F-004 | Backlog | Recorded — not implemented |
| F-005 | Backlog | Recorded — not implemented |

## 3. F-001 Hardcoded Path Evidence

**Before repair — active test occurrences:**

| File | Line | Pattern |
|------|------|---------|
| `tests/path_governance/test_p1_7_16_policy_context_bridge.py` | 929 | `cwd="/home/hrvojeb/Desktop/GG"` |
| `tests/path_governance/test_p1_7_17_projection_api_event_contract.py` | 677 | `cwd="/home/hrvojeb/Desktop/GG"` |
| `tests/test_capability_claim_boundary.py` | 405 | `cwd="/home/hrvojeb/Desktop/GG"` |

**Historical-only occurrences remaining:** `.claude/`, `agent/evidence/p0.20/`, `agent/reports/P1_PRE_P2_FULL_AUDIT_AND_SEAL_RERUN.md` (audit documentation).

**Prior failure mode:** `FileNotFoundError: [Errno 2] No such file or directory: '/home/hrvojeb/Desktop/GG'` when repository lives at `/home/hrvojeb/Desktop/Aurel`.

**Prior full-suite impact:** 12 failures (2 direct regression subprocess tests, 2 cascading P1.7.18/P1.7.20 regression tests, 8 capability-claim CLI subprocess tests).

## 4. F-001 Repair Details

Created `tests/repo_root.py` with `pyproject.toml` + `src/` discovery:

```python
def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in (current, *current.parents):
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    raise RuntimeError("Could not locate repository root")
```

Updated three test files to import `REPO_ROOT` and use `cwd=str(REPO_ROOT)`.

**Tests skipped/xfail/deleted/weakened:** None.

## 5. F-001 Validation Evidence

```bash
grep -R "/home/hrvojeb/Desktop/GG" -n tests src agent  # no active test/src occurrences
.venv/bin/python -m pytest tests/path_governance/test_p1_7_16_policy_context_bridge.py \
  tests/path_governance/test_p1_7_17_projection_api_event_contract.py \
  tests/test_capability_claim_boundary.py -q
# 143 passed in 160.69s
```

## 6. F-002 Canon Drift Evidence

**Audit trigger state (stale):** P2.2-B source untracked; ACTIVE_TASK/STATE described P2.2-A as latest.

**Actual repo state at repair dispatch:** P2.2-B already committed on `master` (`e9c25ad`, `4e1b57c`). Canon files (`ACTIVE_TASK.md`, `STATE.md`, `ROADMAP.md`, `TESTS.md`, `REPORTS.md`) and `agent/reports/P2_2_B_LOCAL_NAVIGATION_HIERARCHY.md` already reflected P2.2-B DONE.

**Repair action:** Confirmed P2.2-B validation post F-001 fix; indexed this audit repair report; updated state pointers for full-suite green and audit-repair completion.

## 7. P2.2-B Validation Evidence

```bash
.venv/bin/python -m pytest tests/aurel_shell/test_shell_local_navigation_hierarchy.py -q
# 20 passed
.venv/bin/python -m pytest tests/aurel_shell -q
# 460 passed
```

P2.2-B overclaim check: PASS — no UI/sidebar/global left nav/route runtime/click handler/command palette/floating window claims in source or report.

## 8. P2.2-B Canon Sync Details

- P2.2-B status: **DONE** (unchanged — evidence from prior pack + revalidated)
- Next planned: **P2.2-C planning only** — not dispatched
- Report: `agent/reports/P2_2_B_LOCAL_NAVIGATION_HIERARCHY.md` (existing)

## 9. Files Created / Modified

**Created:**

- `tests/repo_root.py`
- `agent/reports/AUDIT_REPAIR_001_TEST_PORTABILITY_P2_2_B_CANON_SYNC.md`

**Modified:**

- `tests/path_governance/test_p1_7_16_policy_context_bridge.py`
- `tests/path_governance/test_p1_7_17_projection_api_event_contract.py`
- `tests/test_capability_claim_boundary.py`
- `agent/REPORTS.md`
- `agent/ACTIVE_TASK.md`
- `agent/STATE.md`
- `agent/TESTS.md`

## 10. Tests Run

| Command | Result |
|---------|--------|
| Targeted path/capability tests | 143 passed |
| P2.2-B focused | 20 passed |
| `tests/aurel_shell` | 460 passed |
| Full suite | 6151 passed, 3 skipped |
| compileall | PASS |
| ruff | PASS |
| mypy | PASS (297 files) |

## 11. Full Suite Result

```
6151 passed, 3 skipped in 1104.42s (0:18:24)
```

Path-portability failures: **0**  
Remaining non-path failures: **0**

## 12. Security Scan Status

Inherited from pre-repair audit baseline (not rerun in this repair):

- pip_audit: no known vulnerabilities
- bandit: 34 low, 0 medium, 0 high

## 13. What Was Deliberately Not Implemented

P2.2-C, P2.2.11+, P2.3+, UI/sidebar/global left nav, route runtime, click handlers, keyboard shortcuts, command palette, floating windows, API server, event bus, memory writes, trace writes, Custos enforcement, large module refactor, `__init__.py` export deflation, contract generation abstraction, release seal, TRACE_VERIFIED claim, LIVE claim.

## 14. F-003–F-005 Backlog

| ID | Finding | Disposition |
|----|---------|-------------|
| F-003 | Large module / export maintainability hotspot | Backlog — out of AUDIT-REPAIR-001 scope |
| F-004 | Broad package API surface smell | Backlog — out of AUDIT-REPAIR-001 scope |
| F-005 | Repetitive contract-pattern generation | Backlog — out of AUDIT-REPAIR-001 scope |

## 15. Remaining Risks

- Historical audit/evidence files still reference `/Desktop/GG` path (documentation only).
- Release gate remains separate from test portability; no release seal performed.
- F-003–F-005 maintainability concerns remain open for future packs.

## 16. Next Recommended Step

Proceed to P2.2-C planning/dispatch from clean full-suite baseline after OMNI review of this repair report. Do not start P2.2-C implementation without explicit dispatch.

## 17. Commit Hash

`5d133e0fd29c4094e7960c34801f3eaf3d6c4f54`

## 18. Final Git Status

Clean — all in-scope changes committed on `master`; no push performed.
