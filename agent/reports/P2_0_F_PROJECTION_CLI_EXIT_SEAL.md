# P2.0-F — Projection/API/CLI/Docs/Exit Seal Integration Tail

**Pack ID:** P2.0-F
**Section:** P2.0 — Seven-Surface Cognitive OS Lock
**Domain:** P2 — AurelShell Seven-Surface Cognitive OS Foundation
**Covered checkpoints:** P2.0.27–P2.0.30
**Status:** DONE — P2.0 SEALED_FOR_P2_CONTRACT_SCOPE
**Date:** 2026-06-29
**Next step:** OMNI review of P2.0 exit seal and P2.1 readiness boundary

---

## 1. Result Header

P2.0-F closes the P2.0 section by making the P2.0-A/B/C/D/E AurelShell contract
stack externally inspectable and sealable at **contract scope only**. It adds a
read-model projection, an API contract (not a server), an event contract (not an
emitted event/bus), a read-only CLI inspect binding, an explicit UNAVAILABLE TUI
binding, docs/state/report sync, and a scope-aware P2.0 exit seal. No product UI,
API server, HTTP route, event bus, runtime event, live CLI/TUI product, route
runtime, memory write, trace write, trace verification, runtime mutation, or P2.1
work was implemented.

## 2. Dispatch Gate Evidence

| Gate | Evidence |
|------|----------|
| P1.9.30-SEAL-CRITERIA-REPAIR accepted | yes — `SEALED_FOR_P1_CONTRACT_SCOPE` (`agent/reports/P1_9_30_SEAL_CRITERIA_REPAIR.md`) |
| Pre-P2 audit rerun decision | `READY_FOR_P2_REVIEW` (`agent/reports/P1_PRE_P2_FULL_AUDIT_AND_SEAL_RERUN.md`) |
| P2.0-A report / OMNI / git | present; OMNI accepted (recorded in B/C dependency evidence); final git clean; `ca08c91` |
| P2.0-B report / OMNI / git | present; OMNI accepted (recorded in C dependency evidence); final git clean; `8fe4a59` |
| P2.0-C report / OMNI / git | present; local OMNI marker missing (prior operator waiver pattern); final git clean; `3e22b04` |
| P2.0-D report / OMNI / git | present; local OMNI marker waived by operator (DEC-P20E-01); final git clean; `f897746` |
| P2.0-E report / OMNI / git | present; status DONE; **local OMNI marker missing — explicitly waived by operator for this P2.0-F dispatch (DEC-P20F-01)**; final git clean; `1f0f6a9` |
| Working tree clean at dispatch | yes (snapshot at session start was stale; preflight `git status --short` empty) |
| Premature P2.0-F files | none |

**Gate result:** PASS with explicit operator waiver for the missing local P2.0-E
OMNI acceptance marker. The operator answered "Waive marker, proceed" when asked.
The waiver is dependency evidence for this dispatch only; it is not recorded as a
false OMNI acceptance claim.

## 3. Roadmap Authority Chain

Aurel Roadmap v5.5 = canonical truth; P1 seal / pre-P2 audit = P2 permission gate;
P2.0-A registry, P2.0-B boundaries, P2.0-C continuity, P2.0-D truth/permission/
fixture, P2.0-E demo/snapshot/regression/readiness = dependency gates; Implementation
Pack Doctrine = grouping; CodeOps = validation/report/git; local `agent/ROADMAP.md` =
progress mirror only (not authority). Checkpoint names P2.0.27–P2.0.30 are
unchanged and not collapsed.

## 4. Execution Shape Used

P2.0 Integration Tail + Contract-Scope Seal Pack / Orchestrated Single Executor.
Seal-critical / contract-scope exit seal / readiness boundary. The selected shape
was obeyed; no split was needed; no different shape recommended.

## 5. Dependency on P2.0-A/B/C/D/E

- **P2.0-A registry reused:** `build_default_surface_registry`, `CANONICAL_SURFACE_ORDER` (seven surfaces) — no duplicate surface enum/registry created.
- **P2.0-B boundaries respected:** navigation/Logo→CRO/source-of-truth boundaries surface through the snapshot summary; not bypassed.
- **P2.0-C continuity respected:** floating/handoff/context carryover summaries surface through the snapshot; TraceRef is not TRACE_VERIFIED.
- **P2.0-D truth/permission/fixture respected:** truth-label, permission-matrix, unavailable-state, and fixture-disclosure summaries surface through the snapshot; DEV_FIXTURE is not LIVE; permission matrix is not authorization.
- **P2.0-E snapshot/readiness respected:** projection read model is built over `ShellStateSnapshot` (read-model only); `build_p2_0_e_operator_demo_snapshot_regression_result` is exercised as a dependency check.

The projection read model copies the P2.0-E shell state snapshot summaries rather
than recomputing a second source of truth.

## 6. Roadmap Coverage Matrix P2.0.27–P2.0.30

### P2.0.27 — DONE
Canonical name: Shell Projection/API/Event Contract
Evidence: `ShellProjectionContract`, `ShellProjectionPayload`, `ShellProjectionReadModel`, `ShellProjectionTruthBoundary`, `ShellAPIContract`/`ShellAPIEndpointContract`/`ShellAPIResponseContract`, `ShellEventContract`/`ShellEventPayloadContract` (`projection.py`, `api_contract.py`, `event_contract.py`).
Tests: `test_p2_0_27_*` projection/API/event builders, serialization, read-model-only, not-source-of-truth, no-mutation, API-not-server, no-HTTP-route, event-not-emitted, no-event-bus.
Truth label: PROJECTION_ONLY / READ_MODEL_ONLY / API_CONTRACT_ONLY / EVENT_CONTRACT_ONLY / NOT_LIVE.
Unavailable reason: API runtime + event runtime UNAVAILABLE (contract-only).
Limitations: no API server, HTTP route, event bus, or emitted runtime event.

### P2.0.28 — DONE
Canonical name: Shell/CLI/TUI Binding
Evidence: `ShellInspectCommandContract`, `ShellCLIBindingContract`, `ShellTUIBindingContract`, `ShellBindingUnavailableReason`, `ShellBindingTruthBoundary`, `handle_shell_cli_inspect` (`cli_binding.py`).
Tests: `test_p2_0_28_*` CLI read-only, no-execute, no-mutate, no-grant, no-workflow; TUI explicit UNAVAILABLE with reason + next action.
Truth label: CLI_INSPECT_CONTRACT_ONLY / TUI_UNAVAILABLE / CONTRACT_ONLY / NOT_LIVE.
Unavailable reason: TUI UNAVAILABLE — no TUI convention in this repo.
Limitations: no command execution, shell mutation, or live CLI/TUI product.

### P2.0.29 — DONE
Canonical name: Shell Docs/State/Reports Update
Evidence: `P20DocsStateReportUpdate`, `P20ReportIndexEntry`, `P20StateSyncSummary`, `build_p2_0_docs_state_report_update` (`exit_seal.py`); this report; `agent/REPORTS.md` index; `agent/ACTIVE_TASK.md`, `agent/STATE.md`, `agent/ROADMAP.md`, `agent/DECISIONS.md`, `agent/TESTS.md` updated.
Tests: `test_p2_0_29_*` docs update builds, does not override roadmap canon, does not fake proof/LIVE, records validation intent.
Truth label: DOCS_SYNC_ONLY / REPORT_EVIDENCE / NOT_LIVE.
Unavailable reason: n/a — docs sync only.
Limitations: docs are not proof; roadmap canon not overridden; no roadmap renumber.

### P2.0.30 — DONE
Canonical name: P2.0 Exit Seal + Live Integration Demo
Evidence: `P20ExitSeal`, `P20ExitSealScope`, `P20ExitSealChecklist`, `P20LiveIntegrationDemoResult`, `P20ExitSealDecision`, `P20ReadinessForP21Review`, `P20FProjectionCLIExitSealPackResult` (`exit_seal.py`).
Tests: `test_p2_0_30_*` exit seal builds; `P2_CONTRACT_SCOPE` seals with complete evidence; `PRODUCTION_LIVE_SCOPE`/`TRACE_VERIFIED_SCOPE` cannot seal without evidence; `RELEASE_SCOPE` cannot seal on fixtures only; no fake LIVE/TRACE_VERIFIED; live demo truth boundary explicit; `READY_FOR_P2_1_REVIEW` review-only; P2.1 not started.
Truth label: P2_CONTRACT_SCOPE / SEALED_FOR_P2_CONTRACT_SCOPE / NOT_LIVE / NOT_TRACE_VERIFIED / READINESS_REVIEW_ONLY.
Unavailable reason: production LIVE path + actual trace verification UNAVAILABLE.
Limitations: contract scope only; no production live/trace/release seal; P2.1 not started or authorized.

## 7. Projection/API/Event Contract Proof

- **Projection:** `build_shell_projection_contract()` → `ShellProjectionContract` bundling a `ShellProjectionPayload` whose `ShellProjectionReadModel` carries the A/B/C/D/E summaries (surface registry, navigation boundary, continuity, truth label, permission matrix, unavailable state, fixture disclosure, operator demo, client consistency, regression harness, readiness) sourced from the P2.0-E shell state snapshot. `is_read_model=true`, `is_source_of_truth=false`, `mutates_runtime=false`, `writes_memory=false`, `writes_trace=false`. Serializes via `serialize_shell_projection_payload`.
- **API contract:** `build_shell_api_contract()` → `ShellAPIContract` with `runtime_status=UNAVAILABLE_API_RUNTIME`, `is_api_server=false`, `creates_http_route=false`, `handles_network_request=false`, `mutates_runtime=false`, `authorizes_action=false`. Guarded by `assert_api_contract_is_not_server` and `assert_no_http_routes_created`.
- **Event contract:** `build_shell_event_contract()` → `ShellEventContract` with `runtime_status=UNAVAILABLE_EVENT_RUNTIME`, `is_runtime_event=false`, `event_emitted=false`, `event_bus_created=false`, `mutates_runtime=false`, `writes_trace=false`. Guarded by `assert_event_contract_is_not_emitted_runtime_event` and `assert_no_event_bus_created`.

## 8. CLI/TUI Binding Proof

- **CLI:** `build_shell_cli_binding_contract()` → `ShellCLIBindingContract` (`READ_ONLY_CONTRACT`) with `is_read_only=true`, `executes_action=false`, `mutates_runtime=false`, `grants_permission=false`, `starts_workflow=false`, `writes_memory=false`, `writes_trace=false`. `handle_shell_cli_inspect()` returns `read_only=true`, `authority_granted=false`, `executed=false`, `mutated_runtime=false`. Guarded by `assert_cli_inspect_is_read_only` and `assert_cli_does_not_execute`.
- **TUI:** `build_shell_tui_binding_contract()` → `ShellTUIBindingContract` with `binding_status=UNAVAILABLE`, explicit `unavailable_reason` and `next_action`, `truth_label=TUI_UNAVAILABLE`. Guarded by `assert_tui_status_explicit`. No live TUI product is created.

## 9. Docs/State/Reports Sync Proof

`build_p2_0_docs_state_report_update()` records: report path present on disk and
indexed in `agent/REPORTS.md`; `roadmap_canon_overridden=false`;
`validation_recorded=true`; state files updated (ACTIVE_TASK, STATE, ROADMAP,
DECISIONS, TESTS). Guarded by `assert_docs_do_not_override_roadmap_canon`. Docs are
explicitly not proof; evidence lives in code/tests/report/git.

## 10. P2.0 Exit Seal Decision

- **Seal decision:** `SEALED_FOR_P2_CONTRACT_SCOPE` (requested scope `P2_CONTRACT_SCOPE`).
- **Seal scopes & per-scope decisions:**
  - `P2_CONTRACT_SCOPE`: **SEALED**
  - `PRODUCTION_LIVE_SCOPE`: **PARTIAL** (cannot seal — no live path evidence)
  - `TRACE_VERIFIED_SCOPE`: **PARTIAL** (cannot seal — no trace verification evidence)
  - `RELEASE_SCOPE`: **PARTIAL** (cannot seal — dev fixtures only)
- Checklist: A–E dependency reports present, projection/API/event contract built,
  API/event runtime honest, production-LIVE + trace-verification + TUI explicitly
  UNAVAILABLE, CLI read-only inspect PASS, docs sync PASS, no fake
  LIVE/TRACE_VERIFIED/release-seal, P2.0.27–P2.0.30 coverage PASS.

## 11. Live Integration Demo Truth Boundary

`build_p2_0_live_integration_demo_result()` runs an in-process DEV_FIXTURE vertical
slice (projection build + read-only CLI inspect). `demo_status=DEV_FIXTURE_TESTED`,
`truth_label=NOT_LIVE`, `live_path_evidence=false`. The builder raises if asked for
`LIVE_TESTED`/`PRODUCTION_LIVE_TESTED`. Live path evidence: none. Unavailable
reason: `UNAVAILABLE_LIVE_PATH` + `UNAVAILABLE_TRACE_VERIFICATION`.

## 12. P2.1 Readiness Boundary

`build_p2_0_readiness_for_p2_1_review()` → `READY_FOR_P2_1_REVIEW`,
`is_review_only=true`, `starts_p2_1=false`, `authorizes_p2_1_coding=false`. Guarded
by `assert_p2_1_readiness_is_review_only` and `assert_p2_1_not_started`. P2.1 is not
started and not authorized for coding.

## 13. No API Server / Runtime / UI / Fake LIVE Proof

No API server, no HTTP routes, no event bus, no runtime events emitted, no UI, no
web/desktop/mobile client, no live CLI/TUI product, no route runtime created. No
`LIVE` or `TRACE_VERIFIED` truth label is claimed; `assert_seal_honest` rejects
forbidden operational labels and fake-truth detection.

## 14. Truth Label / Seal Scope Proof

Default labels: CONTRACT_ONLY, READ_MODEL_ONLY, PROJECTION_ONLY, API_CONTRACT_ONLY,
EVENT_CONTRACT_ONLY, CLI_INSPECT_CONTRACT_ONLY, TUI_UNAVAILABLE, DOCS_SYNC_ONLY,
P2_CONTRACT_SCOPE, SEALED_FOR_P2_CONTRACT_SCOPE, READINESS_REVIEW_ONLY, NOT_LIVE,
NOT_TRACE_VERIFIED. `FORBIDDEN_P2_0_F_TRUTH_LABELS` blocks LIVE, TRACE_VERIFIED,
API_SERVER_LIVE, HTTP_ROUTE_CREATED, EVENT_EMITTED, EVENT_BUS_CREATED,
CLI_PRODUCT_LIVE, TUI_PRODUCT_LIVE, PRODUCTION_LIVE_SEALED, TRACE_VERIFIED_SEALED,
RELEASE_SEALED, P2_1_STARTED, etc.

## 15. Side-Effect / No-Authority Proof

`P20FSideEffectProof` — all 23 fields false: api_server_created, http_routes_created,
event_bus_created, runtime_events_emitted, ui_created, web_client_created,
desktop_client_created, mobile_client_created, live_cli_product_created,
live_tui_product_created, shell_runtime_mutated, permission_enforcement_created,
custos_integration_created, tool_executed, workflow_started, business_action_executed,
memory_written, runtime_mutated, trace_written, trace_verification_created,
global_trace_written, ledger_written, p2_1_started.

## 16. Surface Taxonomy Drift Status

SURFACE_TAXONOMY_DRIFT: **YES (inherited)** — `detect_surface_taxonomy_drift()`
reports legacy A-Hub/S-Hub/L-Hub docs noted since P2.0-A. P2.0-F uses only the
canonical seven-surface registry (Aurel CRO / HQ / CORP / HUB / IDE / SYSTEM /
Settings) and does not activate any old taxonomy.

## 17. Files Created / Modified

**Created (code):**
- `src/agentic_runtime/aurel_shell/projection.py`
- `src/agentic_runtime/aurel_shell/api_contract.py`
- `src/agentic_runtime/aurel_shell/event_contract.py`
- `src/agentic_runtime/aurel_shell/cli_binding.py`
- `src/agentic_runtime/aurel_shell/exit_seal.py`

**Created (tests):**
- `tests/aurel_shell/test_shell_projection_cli_exit_seal.py`

**Created (report):**
- `agent/reports/P2_0_F_PROJECTION_CLI_EXIT_SEAL.md`

**Modified:**
- `src/agentic_runtime/aurel_shell/__init__.py` (exports only)
- `agent/REPORTS.md`, `agent/ACTIVE_TASK.md`, `agent/STATE.md`, `agent/ROADMAP.md`, `agent/DECISIONS.md`, `agent/TESTS.md`

## 18. Tests Added / Updated

`tests/aurel_shell/test_shell_projection_cli_exit_seal.py` — dispatch/dependency,
P2.0.27 projection/API/event, P2.0.28 CLI/TUI, P2.0.29 docs sync, P2.0.30 exit seal /
live demo / P2.1 readiness, and pack result + side-effect proof.

## 19. Validation Run

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_projection_cli_exit_seal.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.0-F **43 passed**; AurelShell **231 passed**;
ruff **PASS**; mypy **PASS** (291 files).

## 20. What Was Deliberately Not Implemented

Product UI; API server; HTTP routes; event bus; runtime event emission; live CLI/TUI
product; route runtime; source-of-truth store; permission enforcement; Custos
integration; memory writes; trace writes; trace verification; runtime mutation;
production live seal; trace-verified seal; release seal; P2.1 work.

## 21. Limitations

Contract/projection/read-model/exit-seal scope only. The seal is honest about
unavailable production LIVE, trace verification, and release scopes. `READY_FOR_P2_1_REVIEW`
is review-only and does not authorize P2.1 coding.

## 22. Next Recommended Step

OMNI review of the P2.0 exit seal and the P2.1 readiness boundary. P2.1 is not
started and not authorized.

## 23. Commit Hash

Recorded in the final operator response after commit.

## 24. Final Git Status

Recorded in the final operator response after commit (expected clean).
