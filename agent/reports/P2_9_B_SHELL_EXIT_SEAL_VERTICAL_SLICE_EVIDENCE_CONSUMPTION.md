# P2.9-B — Shell Exit Seal / Vertical Slice Evidence Consumption

**Date:** 2026-07-01  
**Pack:** P2.9-B  
**Status:** DONE — SHELL_EXIT_SEAL_EVIDENCE_BOUNDARY / P2_FOUNDATION_SEALED / NOT_SHELL_LIVE / NOT_P2_PRODUCT_COMPLETE

## 1. Result Header

P2.9-B consumes P2.REVIEW-A and P2.VSLICE-A evidence, seals P2.1–P2.9 as an honest Shell foundation with one operator-testable vertical slice (P2.VSLICE-A governed command preflight), produces a P2 section seal matrix with truth labels, documents remaining gaps, and hands off to P2.10+ or repair. This is an evidence seal, not a product completion claim. Shell LIVE, arbitrary command execution, full product UI, full command runtime, and safe sandbox are not claimed.

## 2. Scope

- P1.ENF-A/D1/E chain evidence consumption
- P2.REVIEW-A decision consumption
- P2.VSLICE-A vertical slice evidence consumption
- P2.1–P2.9 section seal matrix with truth labels
- P2.6 Surface Projection / API / Event Bridge correction verification
- First true vertical slice proof documentation
- State/report sync and validation recording

Not in scope: P2.VSLICE-A implementation changes, arbitrary command execution, product command runner, full Shell UI, full global command runtime, broad Shell rewrite, full API/event bridge buildout, full surface router, sandbox backend changes, identity/policy enforcement changes, P2.9-C/D, P2.10+ implementation, repo_agent rewrite, global mypy strictness, Shell LIVE, P2 product complete.

## 3. Git / Worktree Preflight

- Branch: `master`
- Initial status: clean
- Unrelated dirty files: none
- P2.9-C/P2.9-D/P2.10+ dirty/untracked files: none
- Shell/product dirty/untracked files: none
- Runtime/sandbox/identity/policy dirty/untracked files: none
- `.venv/bin/python`: present
- Preflight result: **PASS**

## 4. Prerequisite Evidence Gate

| Prerequisite | Status |
|--------------|--------|
| P1.ENF-A report | yes — `agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md` |
| P1.ENF-D1 report | yes — `agent/reports/P1_ENF_D1_IDENTITY_KERNEL_INVARIANT_ENFORCEMENT_DEEPENING.md` |
| P1.ENF-E report | yes — `agent/reports/P1_ENF_E_SANDBOX_SAFE_BACKEND_GATING_UNSAFE_LOCAL_HARDENING.md` |
| P2.REVIEW-A report | yes — `agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md` |
| P2.VSLICE-A report | yes — `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md` |
| P2.VSLICE-A indexed | yes — `agent/REPORTS.md` line 5 |
| P2.VSLICE-A validation evidence | yes — 16 focused tests + regressions per report |
| P2.VSLICE-A commit evidence | yes — `f59a586` (implementation), `ff77faf` (hash record) |
| P2.VSLICE-A final/current git clean | yes |
| P2.9-B was NOT DONE before pack | yes |
| P2.9-B already done unexpectedly | no |
| Gate result | **PASS** |

## 5. P1.ENF Chain Consumption

| Pack | Status | Truth label | Key evidence |
|------|--------|-------------|--------------|
| P1.ENF-A | DONE | ENFORCEMENT_BRIDGE (explicit config) | Policy resolver submit influence, identity submit context, entrypoint guard; `governance_enforcement.py` |
| P1.ENF-D1 | DONE | ENFORCEMENT_BRIDGE (selected invariants) | IK-002/005/006/007 invariant enforcement at submit/preflight; `identity_invariant_enforcement.py` |
| P1.ENF-E | DONE | SANDBOX_BACKEND_GATED | UNSAFE_LOCAL/DEV_FIXTURE truth; SAFE_VERIFIED **UNAVAILABLE** without proof; `sandbox_backend_gate.py` |

- Policy truth: policy resolver can influence submit under `ENFORCE_FAIL_CLOSED`; default compatible without explicit config
- Identity truth: selected IK invariants enforced at submit/preflight under explicit config; not full IK enforcement
- Sandbox truth: `UnsafeLocalSandbox` is UNSAFE_LOCAL/dev-only; SAFE_VERIFIED unavailable; no safe sandbox overclaim

## 6. P2.REVIEW-A Consumption

- Report found: yes
- Chosen first vertical slice: **P2.VSLICE-A — Governed Command Palette / Global Command Preflight Slice**
- Fallback slice: **P2.VSLICE-A-FALLBACK — Global Topbar / Surface Registry Truth Slice** (not used; preflight path implemented)
- Evidence gaps at review time: CLI/TUI binding, governed preflight envelope, operator-testability — addressed by P2.VSLICE-A
- P2.9-B criteria from review: all met by P2.VSLICE-A evidence
- Consumed: **yes**

## 7. P2.VSLICE-A Consumption

| Capability | Verified | Evidence |
|------------|----------|----------|
| Global command registry | yes | `command_availability.py` — `build_p2_vslice_a_command_registry()` |
| Seed commands | yes | 7 seed commands including unavailable `shell.command.execute` |
| Command contracts | yes | `GlobalCommandContract`, version `p2_vslice_a_global_command_contract.v1` |
| Availability projection | yes | `project_command_availability()` with honest truth states |
| Command intent | yes | `CommandIntent` in `command_preflight.py` |
| Preflight decision | yes | `CommandPreflightDecision`; `executes_command=False` enforced |
| Preflight executed commands | **no** | Side-effect proof and tests confirm no execution |
| Policy summary | yes | `evaluate_policy_resolver_submit_influence` consumed |
| Identity summary | yes | `evaluate_identity_invariant_enforcement` consumed |
| Sandbox summary | yes | `evaluate_sandbox_backend_gate` with `UnsafeLocalSandbox` consumed |
| Evidence refs | yes | Report paths in gate summaries and pack result |
| Focused tests | yes | 10 + 6 = 16 passed |
| Remaining gaps | CLI/TUI binding UNAVAILABLE; command execution UNAVAILABLE; SAFE_VERIFIED UNAVAILABLE |

- Truth label: **PREFLIGHT_ONLY** / **READ_ONLY** where applicable
- TRACE_VERIFIED: not claimed (no operator trace path for Shell commands)
- Shell LIVE: not claimed

## 8. P2 Section Seal Matrix

| section_id | section_title | status | truth_label | evidence_refs | operator_testable_path | remaining_gaps | handoff_target |
|------------|---------------|--------|-------------|---------------|------------------------|----------------|----------------|
| P2.1 | Global Topbar / Surface Registry | SEALED_FOR_P2_1_CONTRACT_SCOPE | CONTRACT_ONLY | P2_1_A–D reports, `topbar_*` modules | no — contract/read-model only | No live surface switcher, no UI | P2.10+ |
| P2.2 | Per-Surface Local Navigation | SEALED_FOR_P2_2_CONTRACT_SCOPE | CONTRACT_ONLY | P2_2_A–D reports, `local_nav_*` modules | no | No sidebar UI, no route runtime | P2.10+ |
| P2.3 | Floating Windows / Workspace State | SEALED_FOR_CONTRACT_SCOPE | CONTRACT_ONLY | P2_3_A–D reports, `workspace_*` modules | no | Window semantics read-model only | P2.10+ |
| P2.4 | Command Palette / Global Commands | SEALED_CONTRACT_SCOPE + VSLICE | CONTRACT_ONLY + **PREFLIGHT_ONLY** (slice) | P2_4_A–D reports + P2_VSLICE_A report, `command_*` modules | **yes** — pytest read-model via `run_p2_vslice_a_operator_path()` | No command execution, no palette UI, CLI/TUI gap | P2.10+ |
| P2.5 | Cross-Surface Handoff | SEALED_CONTRACT_SCOPE | CONTRACT_ONLY | P2_5_A–D reports, `cross_surface_handoff_*` | no | Handoff contracts only; no E2E UI | P2.10+ |
| P2.6 | Surface Projection / API / Event Bridge | SEALED_CONTRACT_ONLY | CONTRACT_ONLY | P2_6_A–D reports, `surface_projection_*` | no | No API server, event bus, live bridge | P2.10+ |
| P2.7 | Shell / CLI / TUI Binding | SEALED_CONTRACT_ONLY | CONTRACT_ONLY | P2_7_A–D reports, `shell_binding_*` | no | Binding descriptors only; TUI UNAVAILABLE | P2.10+ |
| P2.8 | Shell State / Reports / Docs | SEALED_CONTRACT_ONLY | CONTRACT_ONLY | P2_8_A–D reports, `shell_state_*` | no | Read models only; not live Shell state | P2.10+ |
| P2.9-A | Shell Exit Seal Foundation | DONE | CONTRACT_ONLY | P2_9_A report, `shell_exit_seal_foundation.py` | no | Foundation gate only; not validation execution | P2.9-B |
| P2.9-A-R1 | Evidence Ref Repair | DONE | TRACE_VERIFIED (scoped ref integrity) | P2_9_A_R1 report | no | Ref integrity repair only | P2.9-B |
| P2.9-B | Shell Exit Seal / Vertical Slice Evidence Consumption | **DONE** | **EVIDENCE_SEAL** | this report | no — seal is documentation/evidence boundary | Does not claim Shell LIVE or product complete | P2.10+ |

## 9. Shell Truth Labels

| Label | Applied where | Notes |
|-------|---------------|-------|
| CONTRACT_ONLY | P2.1–P2.3, P2.5–P2.9-A | Section contracts/read-models; no live runtime |
| PREFLIGHT_ONLY | P2.VSLICE-A / P2.4 slice | Governed preflight decision; not execution |
| READ_ONLY | Registry/inspect paths | List/inspect commands; no mutation |
| UNAVAILABLE | CLI/TUI binding, command execution, SAFE_VERIFIED sandbox | Honest gaps documented |
| DEV_FIXTURE | Demo/snapshot paths (P2.0-E) | Not production LIVE |
| SIMULATED | Shadow governance modes | Advisory/shadow only unless ENFORCE_FAIL_CLOSED |
| NOT_DONE | P2.9-C, P2.9-D, P2.10+ | Future work |
| LIVE | **not used** for P2 seal | No operator-testable live Shell product |
| TRACE_VERIFIED | P2.9-A-R1 ref integrity only (scoped) | No Shell command trace verification |

## 10. First True Vertical Slice Proof

- Slice: **P2.VSLICE-A — Governed Command Palette / Global Command Preflight Slice**
- Operator-testable path: `pytest tests/test_p2_command_palette_vslice.py tests/test_p2_command_preflight.py` — `run_p2_vslice_a_operator_path()` exercises list → inspect → preflight
- Truth label: **PREFLIGHT_ONLY**
- Evidence refs: `agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md`, `src/agentic_runtime/p2_command_palette_vslice.py`, `command_projection.py`, `command_preflight.py`, `command_availability.py`
- Validation evidence: 16 focused tests passed; regressions passed (see §15)
- Preflight-only: **yes** — `executes_command=False`, `command_execution_implemented=False`, `preflight_only=True` in pack result
- Execution claim: **no**
- LIVE claim: **no**

## 11. P2.6 Canon Correction Check

- P2.6 is Surface Projection / API / Event Bridge: **yes** — confirmed in ROADMAP.md, P2.6-A report ("Discarded Attention/Notification/Inbox direction not used"), P2.REVIEW-A report
- Attention/Notification/Inbox drift found: **no active drift** — historical P2.1-B "attention" slots are display-contract only, explicitly not notification engine
- Correction applied: not needed; canon preserved

## 12. What Is Sealed

- P2.1–P2.9 honest Shell foundation with contract lattice and one operator-testable vertical slice
- First true vertical slice: P2.VSLICE-A governed command preflight (preflight-only)
- Evidence boundary: P2.9-B seal is evidence/truth consumption, not product release
- Truth matrix: section seal matrix (§8) with honest labels
- P2.10+ handoff: documented gaps and recommended next step

## 13. What Is Not Sealed

- Full Shell LIVE
- Full product UI
- Arbitrary command execution
- Full command runtime
- Full API/event bridge (live server/bus)
- Full surface router
- Safe sandbox (SAFE_VERIFIED unavailable without proof)
- P2.10+ (not started)
- P2 product complete

## 14. P2.10+ Handoff

Recommended next: **P2.10+** per roadmap, or **P2.9-C** only if seal gaps require repair.

Priority gaps for P2.10+:

1. CLI/TUI read-only binding for command list/preflight inspect
2. Command execution engine (if ever in scope — currently UNAVAILABLE by design)
3. Live Shell product UI / surface switcher
4. Full API/event bridge runtime
5. SAFE_VERIFIED sandbox backend (requires proof infrastructure)

P2.9-C/D remain NOT READY until operator directs.

## 15. Tests / Validation

| Check | Result |
|-------|--------|
| compileall | **PASS** |
| P2 command palette vertical slice tests | **10 passed** |
| P2 command preflight tests | **6 passed** |
| P2 vertical slice review regression | **9 passed** |
| sandbox backend gate regression | **13 passed** |
| sandbox safe backend submit regression | **PASS** (included in 13) |
| identity invariant enforcement regression | **16 passed** |
| identity submit context regression | included in 16 |
| governance enforcement submit regression | **11 passed** |
| entrypoint governance guard regression | **6 passed** |
| validation truth / drift gate regression | **18 passed** |
| Golden Thread B regression | **17 passed** |
| baseline mypy | **PASS** (341 source files) |
| ruff | **PASS** |
| git status after validation | clean |

Validation not run: full suite, coverage (not required for P2.9-B seal scope).

## 16. No-Scope-Expansion Proof

| Forbidden change | Made |
|------------------|------|
| P2.VSLICE-A implementation changed | no |
| Arbitrary command execution implemented | no |
| Product command runner implemented | no |
| Full Shell UI implemented | no |
| Broad Shell rewrite | no |
| Full API/event bridge buildout | no |
| Full surface router | no |
| Sandbox backend changed | no |
| Identity/policy enforcement changed | no |
| P2.9-C/P2.9-D/P2.10+ started | no |
| repo_agent rewritten | no |
| Global mypy strictness enabled | no |
| Shell LIVE claimed | no |
| P2 full product completion claimed | no |

## 17. Files Created / Modified

Created:

- `agent/reports/P2_9_B_SHELL_EXIT_SEAL_VERTICAL_SLICE_EVIDENCE_CONSUMPTION.md`

Modified:

- `agent/REPORTS.md`
- `agent/STATE.md`
- `agent/ACTIVE_TASK.md`

## 18. Remaining Risks / Limitations

- Contract-only sections dominate P2.1–P2.3, P2.5–P2.8 — no live Shell product
- Command execution unavailable by design — preflight is not execution
- Safe sandbox (SAFE_VERIFIED) unavailable without proof
- Shell product UI not implemented
- CLI/TUI binding gap — pytest read-model path used for operator testability
- Full test suite and coverage not run in this seal pack
- P2.10+ not started

## 19. Commit Hash

`9082da7`

## 20. Final Git Status

Clean on `master` after commit `9082da7`.
