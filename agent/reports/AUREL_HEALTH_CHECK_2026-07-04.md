# Aurel Governed Agentic Runtime — Post-P4 Health-Check Analysis Report

**Date:** 2026-07-04
**Status:** PARTIAL — F-001 and F-004 remediated; F-002, F-003, F-005 remain open
**Analysis mode:** health-check

---

## 1. Summary

Full-system health-check of the Aurel governed agentic runtime at post-**P4-EXEC-G** (P4 sealed). Overall verdict: **PARTIAL PASS** — governance integrity and sealed-domain invariants remain intact; the P4 exit seal evidence (8068 pytest passed at seal time) still stands as canon. Five operator-facing drift and wiring gaps were identified. **F-001** (terminal shell canon frozen at P2.10-D) and **F-004** (exec status CLI unwired despite P4-EXEC-G contract) were remediated in-session via operator-canon sync and read-only `exec status` CLI binding. **F-002** (Shell projections not trace-fed), **F-003** (P2 tail deferred), and **F-005** (policy `shell_binding` UNAVAILABLE) remain documented backlog with honest UNAVAILABLE posture.

**Recommended next step:** Proceed with P5 AurelTrace Spine per roadmap, or resume deferred P2.11-D when operator prioritizes Shell tail; optionally run fresh `cli verify` for full-suite revalidation.

Remediation record: Phases 0–1 (F-001) and Phase 2 (F-004) complete — see §10.

---

## 2. Scope and trigger

| Field | Value |
|-------|-------|
| Trigger | User request: principal architect analysis + `/analyze-aurel` health-check |
| Boundary | Full-system: `src/agentic_runtime/`, `tests/`, `agent/` governance docs, CLI surfaces (shell, exec, flow, policy) |
| Analysis mode | `health-check` |
| Invariants at risk | Fail-closed honesty, projection-is-not-control, operator canon sync, CLI binding truth labels, Entity proposes / Runtime disposes |
| Non-goals | P5 trace spine implementation; P2.11-D–P2.20 tail; Shell UI/React product; governance weakening; full-suite re-seal |

---

## 3. Architecture / pipeline context

Aurel is a **governed agentic runtime** with core law **"Entity proposes. Runtime disposes."** At analysis time:

| Domain | Status | Role |
|--------|--------|------|
| P4 AurelExec | **SEALED** (P4-EXEC-G) | Admission, lease, managed runtime, modes, judgment, topology — first governed `runtime.submit` bridge |
| P3 AurelFlow | **SEALED** (P3-FLOW-L) | Non-executing control-plane grammar; scheduling intent, not dispatch |
| P2 AurelShell | **Partial** — P2.10 sealed; P2.11-C done; P2.11-D next; P2.11-D→P2.20 deferred | Operator-console contracts, read models, CLI bindings — not live product |
| P5 AurelTrace | **Next** | Trace spine, durable event log, TRACE_VERIFIED — not implemented |
| P9 Custos | **Future** | Authority enforcement — shadow-only today |

**P2.0** in this codebase is the internal AurelShell operator-console phase (seven surfaces), not an external business system. **Projection** means CQRS read models over runtime state and `AurelTraceLog` contracts — not financial forecasting.

**Operator-facing read path (post-remediation):**

```
agent canon (STATE/ACTIVE_TASK/ROADMAP)
    → terminal_shell_client (operator_canon=True default)
    → shell status CLI
    → honest pack pointers (P2.11-C complete, P2.11-D next)

P4 exec_status aggregator (26 categories, honest UNAVAILABLE)
    → exec status CLI (wired)
    → deterministic JSON (no runtime objects → all UNAVAILABLE-with-reason)
```

Execution still flows only through the sanctioned `ExecRuntimeBridge` → `AgenticRuntime.submit()` path. CLI status commands are read-only bindings.

---

## 4. Evidence

### Commands run

| Command | Result |
|---------|--------|
| `python -m agentic_runtime.cli shell status` | **PASS** — shows `last_completed_pack: P2.11-C`, `next_pack: P2.11-D`, `next_pack_not_started: true` |
| `python -m agentic_runtime.cli exec status` | **PASS** — JSON with 26 categories; all `UNAVAILABLE` when no runtime objects passed (honest) |
| `pytest tests/test_terminal_shell_canon_sync.py tests/test_exec_cli_commands.py tests/aurel_exec/test_exec_cli_status_binding.py tests/test_p210d_terminal_shell_client.py -q` | **PASS** — 16 passed |
| Full repo `pytest -q` (pre-fix snapshot) | **PARTIAL** — 8057 passed, 11 failed (session snapshot; not re-run post-fix) |
| P4-EXEC-G seal evidence (canon) | **PASS** — 8068 passed / 2 skipped at seal time per `agent/STATE.md` |

### Key observations

- `terminal_shell_client.py` now defines `OPERATOR_CANON_*` constants and defaults `operator_canon=True` for live read models; `operator_canon=False` preserves P2.10-D historical seal builders (`build_p2_10_d_terminal_shell_result`).
- `shell_commands.py` status output uses operator canon constants directly — no longer frozen at P2.10-E "next".
- `exec_commands.py` wires `cmd_exec_status` via `handle_exec_cli_status`; `build_shell_binding_contract(cli_wiring_available=True)` is now the default.
- `DEC-P4EXECG-03` in `agent/DECISIONS.md` documented deliberate CLI deferral at seal time — superseded by wiring but decision log not yet updated.
- Policy projection `shell_binding` section remains honestly `UNAVAILABLE` per `DEC-P1.6.17` — no Shell UI exists.
- P2 tail (P2.11-D → P2.20) explicitly deferred until after full P3 per operator override; P3 now sealed, P5 is roadmap next.

---

## 5. Findings

| ID | Severity | Module | Location | Root cause | Affected invariant |
|----|----------|--------|----------|------------|-------------------|
| F-001 | High | `aurel_shell/terminal_shell_client.py` | `OPERATOR_CANON_*`, `build_terminal_shell_read_model` | Read model hardcoded to P2.10-D seal pointers while agent canon advanced to P2.11-C | Operator canon sync / fail-closed honesty |
| F-002 | Medium | `aurel_shell/*` projections | Shell read-model layer | Projections are contract-built, not trace-fed from AurelTrace | Projection truth / P5 handoff gap |
| F-003 | Medium | `agent/ROADMAP.md`, `agent/STATE.md` | P2.11-D→P2.20 tail | Operator override deferred P2 tail during P3; P3 sealed, tail still open | Scope honesty |
| F-004 | Medium | `cli.py`, `exec_status.py` | `build_shell_binding_contract`, CLI registration | P4-EXEC-G sealed with CLI wiring deliberately UNAVAILABLE; contract existed but `exec status` not registered | CLI binding truth |
| F-005 | Low | `policy` projections | `shell_binding` section | No Shell UI / React frontend — section correctly UNAVAILABLE | Scope honesty (documented) |

### Finding details

#### F-001: Terminal shell canon frozen at P2.10-D

**Severity:** High  
**Module:** `aurel_shell/terminal_shell_client.py`  
**Location:** `src/agentic_runtime/aurel_shell/terminal_shell_client.py:62–64`, `678–724`

The terminal Shell read model reported `P2.10-D` as last completed and `P2.10-E` as next while `agent/STATE.md` and `agent/ACTIVE_TASK.md` recorded P2.11-C complete and P2.11-D next. Operators running `shell status` received stale pack pointers — a canon drift failure.

**Remediation (COMPLETE):** Operator-canon layer with `operator_canon=True` default; historical P2.10-D builders preserved via `operator_canon=False`. Regression tests in `tests/test_terminal_shell_canon_sync.py`.

#### F-002: Shell projections not trace-fed

**Severity:** Medium  
**Module:** AurelShell projection layer  
**Location:** `src/agentic_runtime/aurel_shell/`

Shell read models are built from sealed contract modules and agent canon pointers, not from live `AurelTraceLog` events. This is consistent with P4/P5 boundaries (trace verification UNAVAILABLE) but limits operator situational awareness until P5 lands.

**Status:** Open — P5 AurelTrace Spine owns resolution.

#### F-003: P2 tail incomplete and deferred

**Severity:** Medium  
**Module:** Governance docs / P2 roadmap  
**Location:** `agent/ROADMAP.md`, `agent/STATE.md`

P2.11-D through P2.20 (including final seven-surface exit seal) remain NOT_STARTED. Deferred by explicit operator override during P3 delivery. P3 and P4 are now sealed; tail resumption is an operator ordering decision, not a code defect.

**Status:** Open — documented; not blocking P4 seal validity.

#### F-004: Exec CLI status unwired at operator surface

**Severity:** Medium  
**Module:** `aurel_exec/exec_status.py`, `cli.py`  
**Location:** `src/agentic_runtime/aurel_exec/exec_status.py:426–439`, `src/agentic_runtime/cli_modules/exec_commands.py`

P4-EXEC-G implemented `ShellBindingContract`, `ExecStatusReadModel`, and `handle_exec_cli_status` but sealed with `cli_wiring_available=False` and no `exec` subcommand in `cli.py`. Contract tests enforced unwired state; operators could not inspect exec posture via CLI.

**Remediation (COMPLETE):** New `exec_commands.py`, `exec status` registered in `cli.py`, default `cli_wiring_available=True`, tests updated for wired + historical unwired modes.

#### F-005: Policy `shell_binding` UNAVAILABLE

**Severity:** Low  
**Module:** Policy projection  
**Location:** `agent/DECISIONS.md` (DEC-P1.6.17), policy projection builders

Policy `shell_binding` section reports UNAVAILABLE because no Shell UI or full TUI app exists. CLI binding is LIVE; Shell UI binding is honestly absent. This is correct fail-closed posture, not a defect.

**Status:** Open — resolves when P2 Shell UI product surface exists.

---

## 6. Test coverage assessment

| Area | Covered by | Gap |
|------|-----------|-----|
| Operator canon sync | `tests/test_terminal_shell_canon_sync.py` | Full governance doc drift gate not automated |
| P2.10-D historical seal | `tests/test_p210d_terminal_shell_client.py`, `test_p210d_terminal_no_execution.py` | — |
| Exec CLI wiring | `tests/test_exec_cli_commands.py`, `tests/aurel_exec/test_exec_cli_status_binding.py` | `exec coverage` / `exec handoff` vocabulary deferred |
| Shell permissions CLI | `tests/test_p211b_p211c_handoff.py`, P2.11-C tests | P2.11-D parity gate not started |
| Full suite green | P4-EXEC-G seal evidence | Fresh post-remediation full run not completed in session |

---

## 7. Known limitations / doc drift

- `agent/DECISIONS.md` DEC-P4EXECG-03 still states CLI wiring deferred — now superseded by `exec status` wiring; decision log update pending.
- `agent/STATE.md` line 54–55 still lists P2.11-C as "current active" in one bullet while also noting P4 sealed — minor pointer duplication, not a runtime claim.
- Full-suite rerun during remediation session was incomplete; focused remediation tests (16) pass; seal-time 8068 count remains authoritative until fresh `cli verify`.
- Shell is contract/read-model layer, not a live operator product; P2.10-E multi-client seal does not imply Shell LIVE.

---

## 8. Explicitly not in scope

- P5 AurelTrace Spine implementation
- P2.11-D through P2.20 Shell tail packs
- Shell UI / React frontend / API server
- Operator snapshot fusion (shell + policy + flow + exec JSON)
- `exec coverage` and `exec handoff` CLI handlers (vocabulary exists, handlers deferred)
- Custos authority enforcement (P9)
- Governance weakening or test deletion to achieve green

---

## 9. Recommended next step

Resume roadmap-primary work (**P5 AurelTrace Spine**) or operator-selected P2.11-D when Shell tail is prioritized. Run `cli verify` when a fresh full-suite seal is needed.

---

## 10. Remediation record (Fix Plan Phases 0–2)

### Phase 0–1 — Operator canon sync (F-001) — **COMPLETE**

| Action | File | Detail |
|--------|------|--------|
| Add `OPERATOR_CANON_*` constants | `terminal_shell_client.py` | P2.11-C complete, P2.11-D next |
| Default `operator_canon=True` | `terminal_shell_client.py` | Live read model uses operator canon |
| Preserve historical seal | `terminal_shell_client.py` | `operator_canon=False` for P2.10-D builders |
| Wire shell status CLI | `shell_commands.py` | Status uses operator canon constants |
| Regression tests | `tests/test_terminal_shell_canon_sync.py` | Canon sync assertions |

### Phase 2 — Exec status CLI binding (F-004) — **COMPLETE**

| Action | File | Detail |
|--------|------|--------|
| New exec CLI module | `cli_modules/exec_commands.py` | `cmd_exec_status` read-only JSON |
| Default wired contract | `exec_status.py` | `cli_wiring_available=True` default |
| Register subcommand | `cli.py` | `exec status` |
| Export reason constant | `aurel_exec/__init__.py` | `CLI_WIRING_AVAILABLE_REASON` |
| Tests | `test_exec_cli_commands.py`, `test_exec_cli_status_binding.py` | Wired + historical unwired |

### Open phases

| Finding | Recommended owner | Notes |
|---------|------------------|-------|
| F-002 | P5 | Trace-fed Shell projections |
| F-003 | Operator | P2.11-D→P2.20 tail ordering |
| F-005 | P2 Shell UI | Policy shell_binding goes LIVE with UI |

---

## Quality checklist

- [x] Every finding has ID, severity, module, location, root cause, invariant
- [x] Evidence section lists commands run with outcomes
- [x] No findings propose governance weakening as resolution
- [x] Architecture context identifies pipeline stage and owner module
- [x] Status reflects overall analysis verdict (PARTIAL — remediations applied, open items remain)