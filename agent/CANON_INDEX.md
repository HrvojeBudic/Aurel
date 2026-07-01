# Aurel Docs / Canon Status Index

_Last updated: 2026-07-01 (P1.ENF-F-B)_

## Active canon pointer

| Field | Value |
|-------|-------|
| **Active roadmap canon** | Aurel Roadmap v5.5 |
| **Active roadmap file** | `agent/ROADMAP.md` |
| **Current state** | `agent/STATE.md` |
| **Current continuity evidence** | Golden Thread B (`src/agentic_runtime/golden_thread_b.py`, `P1.ENF-C`) |
| **Last completed pack** | P1.ENF-F-B |
| **Next planned pack** | P1.ENF-D1 — Identity Kernel Invariant Enforcement Deepening |
| **P2.9-B** | NOT DONE |
| **P1.ENF-D1 / P1.ENF-E / P2.REVIEW-A** | NOT STARTED |

Golden Thread B is continuity evidence for P1.8–P2.9-A + P1.ENF repair/audit/gate chain. It is **not** Shell live behavior and does **not** make P2.9-B done.

## Status taxonomy

| Label | Meaning |
|-------|---------|
| `ACTIVE_CANON` | Current roadmap/canon authority |
| `CURRENT_STATE` | Current build state and next-task pointer |
| `CURRENT_CONTINUITY_EVIDENCE` | Golden Thread B / current evidence chain |
| `CURRENT_COMPLETED_REPORT` | Completed report for a finished pack |
| `HISTORICAL_ARCHIVE` | Preserved old doc; not active task source |
| `HISTORICAL_REFERENCE` | Useful background; not current canon |
| `SUPERSEDED_BY_V5_5` | Older roadmap material replaced by v5.5 active canon |
| `VISION_SEED` | Concept source; does not override roadmap |
| `SALVAGE_MODULE` | Old useful idea integrated or parked |
| `DRIFT_WARNING` | Known doc mismatch; visible but non-blocking |
| `DO_NOT_USE_AS_CURRENT_TASK_SOURCE` | Explicit guard for stale docs |

## Discovery matrix

| Path | Title / role | Detected version | Status | Active canon | Historical | Notes |
|------|--------------|------------------|--------|--------------|------------|-------|
| `agent/ROADMAP.md` | Aurel Roadmap | v5.5 | ACTIVE_CANON | yes | no | Primary roadmap authority; do not renumber/reorder items |
| `agent/STATE.md` | Repository State | v5.5 | CURRENT_STATE | yes | no | Build state + next-task pointer |
| `agent/ACTIVE_TASK.md` | Active Task | v5.5 | CURRENT_STATE | yes | no | Operator-facing current/next task |
| `agent/REPORTS.md` | Reports Index | — | CURRENT_STATE | yes | no | Report discovery index |
| `agent/TESTS.md` | Validation commands | v5.5 | CURRENT_STATE | yes | no | Canonical validation authority |
| `agent/CANON_INDEX.md` | This index | v5.5 | ACTIVE_CANON | yes | no | Doc status / canon pointer |
| `agent/ARCHITECTURE.md` | Architecture map | mixed | CURRENT_STATE + HISTORICAL_REFERENCE | partial | partial | v3.2 section is historical reference; module map is current |
| `agent/DECISIONS.md` | Decisions log | — | CURRENT_STATE | yes | no | Append-only decision record |
| `agent/CODEOPS.md` | CodeOps protocol | — | ACTIVE_CANON | yes | no | Development protocol |
| `agent/AGENT.md` | Agent operating guide | — | ACTIVE_CANON | yes | no | Agent entry guide |
| `src/agentic_runtime/golden_thread_b.py` | Golden Thread B harness | P1.ENF-C | CURRENT_CONTINUITY_EVIDENCE | no | no | Continuity evidence; not Shell live |
| `src/agentic_runtime/golden_threads/thread_a.py` | Golden Thread A harness | P1.5.11A | HISTORICAL_REFERENCE | no | yes | Preserved; superseded for continuity routing by Thread B |
| `agent/reports/P1_ENF_*` | P1.ENF pack reports | v5.5 ENF | CURRENT_COMPLETED_REPORT | no | no | P1.ENF-A through P1.ENF-F-B evidence chain |
| `agent/reports/P2_*` | P2 Shell contract reports | v5.5 P2 | HISTORICAL_REFERENCE + CURRENT_COMPLETED_REPORT | no | partial | Contract-only evidence; P2.9-B NOT DONE |
| `agent/reports/P1.*` (pre-ENF) | P1 section reports | v5.1 / v3.2 refs | HISTORICAL_ARCHIVE | no | yes | Preserved evidence; header may cite v5.1 |
| `docs/roadmap/P1.5.*` | P1.5 sealed roadmap docs | v3.2 / P1.5 | HISTORICAL_ARCHIVE | no | yes | SUPERSEDED_BY_V5_5 for task routing |
| `agent/templates/PLAN_TEMPLATE.md` | Plan template | v5.1 header | DRIFT_WARNING | no | yes | Template header cites v5.1; use v5.5 for active planning |
| `agent/ROADMAP.md` § v3.2 doctrine | Macro v3.2 structure | v3.2 | HISTORICAL_REFERENCE | no | yes | Preserved macro map; not current task authority |
| `agent/ROADMAP.md` § Current phase mirrors | Progress mirrors | mixed | DRIFT_WARNING | partial | partial | Some mirrors lag ENF chain; STATE/CANON_INDEX win for next-task |
| `agent/ARCHITECTURE.md` § v3.2 | System architecture v3.2 | v3.2 | HISTORICAL_REFERENCE | no | yes | Hub taxonomy reference; seven-surface Shell canon in P2.0+ |

## P2.6 correction guard

**Active canon:** P2.6 = Surface Projection / API / Event Bridge.

**Discarded (not active canon):** P2.6 = Attention / Notification / Inbox.

Evidence: P2.6-A through P2.6-D reports and `agent/ROADMAP.md` progress mirrors explicitly discard the Attention/Inbox direction.

## Historical docs — do not delete

Older roadmap/report eras remain preserved:

- v3.x roadmap material (`agent/ROADMAP.md` v3.2 sections, `docs/roadmap/`, P1.5 reports)
- v5.0 / v5.1 Integration-First material (many `agent/reports/P1.*` headers)
- v5.4 / v5.5 transition material (P1.8 remap notes in ROADMAP)
- P2 contract reports (P2.0–P2.9-A)
- P1.ENF repair/audit/gate reports
- Golden Thread A historical continuity

**Rule:** Label stale docs; do not delete historical evidence. Do not treat labeled historical docs as current task authority.

## Completed ENF evidence chain

```
P1.ENF-A → P1.ENF-A-OMNI-R1 → P1.ENF-B → P1.ENF-F-A → P1.ENF-C → P1.ENF-F-B (this pack)
```

## Next planned chain

```
P1.ENF-D1 → P1.ENF-E → P2.REVIEW-A → P2.9-B rerun
```

P2.9-B remains **NOT DONE**. P2.9-C/D/P2.10+ remain **NOT READY / NOT STARTED**.
