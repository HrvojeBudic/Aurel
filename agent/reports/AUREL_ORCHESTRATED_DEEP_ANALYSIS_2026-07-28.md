# Aurel Orchestrated Deep Analysis — 2026-07-28

**Mode:** health-check + architecture + governance (analysis-only)  
**Orchestrator:** multi-agent (Architecture, Governance/Security, Runtime Integration, Test/Quality, Product/Canon)  
**Workspace:** `/home/hrvojebudic/Desktop/Aurel-master`  
**Non-goals:** no code fixes; no governance weakening proposed as shortcut  

## Scope

| Field | Value |
|-------|--------|
| Trigger | Operator request: analyze Aurel, list all problems, use specialized agents |
| Boundary | Full-system (kernel + domains + front + MCP + canon) |
| Analysis mode | `health-check` + architecture + security |
| Invariants at risk | Entity proposes/Runtime disposes; fail-closed; sandbox honesty; capability≠permission≠authority; secrets/trace honesty |

## Evidence baseline

| Command / probe | Outcome |
|-----------------|---------|
| `python3 -m compileall -q src` | exit 0 |
| `PYTHONPATH=src:. python3 -m agentic_runtime.cli status` | OK; sandbox=`UnsafeLocalSandbox` via `restricted_local`; `security_boundary=False`; mock provider |
| `build_runtime()` defaults | `AutoApprover`, `GovernanceEnforcementMode.SHADOW_ONLY`, inner `UnsafeLocalSandbox` |
| `.git` | **absent** (export/snapshot, not a live repo) |
| Scale | ~618 Python modules under package; ~650 `test_*.py`; ~330 agent reports |
| Full suite | not re-run (~30 min historical); deferred intentionally |

## Team findings (merged inventory)

### Critical

| ID | Title | Source agents |
|----|-------|---------------|
| **C-01** | Default sandbox is **not** a security boundary (`restricted_local` → `UnsafeLocalSandbox`) | G-001, status probe |
| **C-02** | Governance / Custos / identity / sandbox-backend gates default **SHADOW_ONLY** (non-blocking) | G-002, G-007, R-007 |
| **C-03** | Front HTTP door: **unauthenticated** mutation surface (localhost trust only) | G-003, G-016, G-018 |
| **C-04** | Canon continuity collapse: ACTIVE_TASK / STATE / ROADMAP / CANON_INDEX / REPORTS disagree | A-003, D-001, D-003–D-005 |
| **C-05** | No `.git` + wipe/recovery narrative → branch/merge/seal provenance **unprovable** in this tree | D-002, D-008 |
| **C-06** | Dual/triple trace SoT: ARCHITECTURE names `AurelTraceLog`; live kernel writes `trace.py` ledger | A-001 |

### High

| ID | Title | Source |
|----|-------|--------|
| **H-01** | `allow_network=False` does not stop network via `run_shell` under unsafe local | G-004 |
| **H-02** | Front CLI serve does **not** wire ConversationEngine / ApprovalInbox / AgentCard | R-001, R-003 |
| **H-03** | Front `corp_*` writes bypass `runtime.submit` | G-008 |
| **H-04** | Identity invariant “enforcement” is self-attested metadata flags | G-005 |
| **H-05** | MCP `allowed_tools` unused; pin not enforced on call path | G-009 |
| **H-06** | `network_fetch` runs on host process, not sandbox isolation | G-010 |
| **H-07** | Dual policy paths (P0 PolicyEngine always; Custos optional/shadow) | A-005 |
| **H-08** | DualKernelRuntime second public `submit` façade | A-007 |
| **H-09** | Sealed P2 Shell / P3 Flow / P4 Exec largely **not** product spine; Front built beside them | A-004, A-006, R-004–R-006 |
| **H-10** | Homonym types (`TraceEventRef`, `EvidenceRef`) across contracts vs aurel_trace | A-002 |
| **H-11** | README “production-shaped” + Beta classifier vs unsafe defaults / PRE-SEAL | D-006, D-007 |
| **H-12** | SEALED language easily misread as production readiness | D-010, T-005 |
| **H-13** | Product IA 6-screen vs Shell 7-surface taxonomy clash | D-009 |
| **H-14** | P1.0 limitations claim no network/delete tools; code registers them | G-020 |
| **H-15** | Full suite ~30 min; lean packs skip it; CI hang/timeout gaps | T-001, T-002 |
| **H-16** | Ruff/mypy heavily weakened; bandit not in CI | T-003, T-004, T-017 |

### Medium

| ID | Title | Source |
|----|-------|--------|
| **M-01** | Multiple tool registries (tools / tool_manifest / MCP gateway) without composition root | A-008 |
| **M-02** | mem_* dispatch bypasses normal sandbox/transition shape (flag-gated) | A-009, R-008–R-009 |
| **M-03** | Empty placeholders: autonomy / metacognition / compliance; heretic in attic | A-010, R-012 |
| **M-04** | Parallel approval systems (HITL vs Front inbox) | A-011 |
| **M-05** | Path governance package structurally shadow-only | G-017 |
| **M-06** | Entrypoint guard classifies, does not enforce | G-012 |
| **M-07** | Secret path protection = basename + file tools only; shell can `cat .env` | G-013 |
| **M-08** | SecretStore plaintext 0600; redaction exact-match gaps | G-014, G-015 |
| **M-09** | Mandate gate multi-flag often inert | G-011 |
| **M-10** | Dual-kernel/praxis construct UnsafeLocalSandbox for children | G-019 |
| **M-11** | Pre-built sandbox without profile → unsafe_local_demo network allowed | G-006 |
| **M-12** | AurelExec only `read_file` TOOL bridge | R-004, A-014 |
| **M-13** | AurelFlow never calls runtime.submit | R-005 |
| **M-14** | MCP client library-complete but default OFF / not in build_runtime | R-010 |
| **M-15** | Approval pending in-process only (not durable) | R-003 |
| **M-16** | Flag forest / optional composition | A-015 |
| **M-17** | Public API exports kernel sprawl; sealed domains hidden | A-012 |
| **M-18** | Manifest lifecycle “trace” orphaned from hash-chain SoT | A-013 |
| **M-19** | Seal tests overweight report presence vs behavior | T-005 |
| **M-20** | Skip surface environment-dependent; CI skips hard sandbox | T-006, T-018 |
| **M-21** | Nested pytest / collection subprocess cost | T-007, T-008 |
| **M-22** | No suite partitioning (slow markers unused) | T-009 |
| **M-23** | TestIntegrityVerifier thinly tested vs marketing | T-011 |
| **M-24** | TESTS.md is historical megadoc, not lean gatebook | T-015 |
| **M-25** | Report inflation (~330) + append-only ACTIVE_TASK/STATE/ROADMAP | D-011 |
| **M-26** | Pn vs Fn dual roadmap dialects unreconciled | D-013 |
| **M-27** | Git tools fail silently when no `.git` | T-013 |
| **M-28** | Coverage path docs vs CI inconsistency | T-014 |

### Low

| ID | Title | Source |
|----|-------|--------|
| **L-01** | SAFE_VERIFIED cannot be satisfied (honest but gates only work under enforce) | G-021 |
| **L-02** | G5 HERETIC disables fail-closed | G-022 |
| **L-03** | xfail unused; known gaps only as skips | T-019 |
| **L-04** | Validation-truth gates not wired as CI enforcement | T-020 |
| **L-05** | Conversation flag defined-not-gating | R-002 |
| **L-06** | Cassette-default overstated for Front | R-011 |

## What actually works (credit)

1. **P0 kernel pipeline is real:** `CommandEnvelope` → PolicyEngine → HITL interface → budget → sandbox dispatch → verifier → hash-chained `trace.py` transitions.  
2. **Sandbox honesty at type level:** `UnsafeLocalSandbox.is_security_boundary=False`; no silent bwrap→unsafe when hard mode requested.  
3. **Contract packs (P2–P5)** are often **honest about UNAVAILABLE** (side-effect booleans structurally false).  
4. **MCP bridge** (when wired) has HIGH floor + submit path; servers disabled by default.  
5. **compileall** clean on this tree; `cli status` runs.  

## Root problem (one sentence)

Aurel is a **deep, honest governance grammar and a real P0 disposal kernel**, overlaid by **contract-seal inflation**, **shadow-by-default enforcement**, **unsafe default isolation**, **stale multi-file canon**, and **product Front/MCP surfaces that exist as libraries more than as default-wired product**.

## Recommended fix order (no implementation)

1. **Canon single pointer** — one table for current task / sealed packs / next; archive megadocs.  
2. **Restore git integrity** — this export cannot prove seals/merges.  
3. **Default security posture** — document loudly; prefer hard sandbox + ENFORCE profiles for “governed” demos; fix shell network/secret holes.  
4. **One dispose path** — Front/corp mutations only through `runtime.submit`; wire Front CLI actuators or stop claiming live converse/act.  
5. **One SoT for trace types** — collapse AurelTraceLog claim vs operational ledger.  
6. **Test gate reform** — smoke vs nightly; pytest-timeout; bandit ratchet; reduce seal-as-report-presence.  
7. **Freeze or integrate** sealed Shell/Flow/Exec packs into product consumers.

## Explicitly not in scope of this analysis

- Implementing fixes  
- Running full 30-min pytest suite  
- Weakening policy/sandbox/verifier to “pass”  

---

*Ready for implementation — invoke targeted fix work or `debug-aurel` after operator prioritizes IDs above.*
