# P3-FLOW-H — Governed Autonomy Levels / Scope Envelopes Pack

## 1. Result

DONE. AurelFlow gained governed autonomy grammar — closed-world levels,
operator-selected modes, scope envelopes, a total deterministic resolver,
gates, safety candidates, drift/violation signals, override candidates, and
a read-only projection — with no self-upgrade, no authority, no execution,
no proof, and no UI control. Date: 2026-07-02. Standing operator override
remains in force ("override - start p3-Flow-A now, p2.11D-p2.20 will
contiune after full p3"); P2 is NOT sealed.

Required claims, all held structurally and by test: autonomy level is not
authority; scope envelope is not permission; gate decision is not execution;
operator override candidate is not Custos authorization; React projection is
not runtime control; P4/P5/P9 remain unavailable; persistence remains
unavailable and out of scope; runtime.submit remains not wired; no LIVE
claim; no TRACE_VERIFIED claim.

## 2. Scope

P3.16 governed autonomy, CodeOps Standard proportionality: 4 focused source
modules, 7 behavior-first test files (64 tests), short report. No P3.17+,
no P4/P5/P9, no execution/dispatch/persistence/React/API.

## 3. Preflight / Canon

Branch master, clean at `980bbed` (G hash record) → `4867489` (G
implementation). Canon read; ACTIVE_TASK/ROADMAP both named P3-FLOW-H next.
P3-FLOW-G prerequisite confirmed: all 5 G modules + 89 G tests present.
Naming conflict found and resolved: `FlowAutonomyLevel` (P3-FLOW-C
visibility projection in `flow_wiring.py`) and `AutonomyLevel`
(identity package) already exist, so H's closed-world enum is
`GovernedAutonomyLevel` (see DECISIONS: DEC-P3FLOWH-01).

## 4. Files Changed

Created: `src/agentic_runtime/aurel_flow/flow_autonomy.py` (levels, mode,
total resolver, action boundary), `flow_autonomy_scope.py` (scope
envelopes), `flow_autonomy_gates.py` (gate ladder, safety candidates,
violations, operator override), `flow_autonomy_projection.py` (read-only
projection); 7 test files; this report.
Modified: `aurel_flow/__init__.py` (53 new exports; 866 total, verified no
duplicates and all resolving), plus canon (REPORTS/STATE/ACTIVE_TASK/
ROADMAP/ARCHITECTURE/DECISIONS/TESTS).

## 5. Implemented Behavior

- `GovernedAutonomyLevel` (12 closed-world members; A9 heretic live mode
  locked unavailable; tier order A0–A8 with A9/UNAVAILABLE/ERROR
  deliberately untiered).
- `OperatorSelectedAutonomyMode` with explicit `AutonomyModeSource`;
  `self_selected`/`self_upgrade_allowed` structurally False; an
  operator-selected mode without a named operator fails closed.
- `AutonomyScopeEnvelope` + `AutonomyScopeLimit` over 16 closed-world
  dimensions; `covers()` behavior; duplicate dimensions fail closed; every
  external-capability boolean (memory/policy/identity/network/tool/sandbox/
  external side effects) structurally False.
- `resolve_permission_state()` — total deterministic resolver (section 6).
- `resolve_action_boundary()` — thin wrapper deriving read-only/
  candidate-only booleans from the resolution.
- `evaluate_autonomy_gate()` — deterministic ladder: budget+storm →
  FREEZE_AUTONOMY; storm → DOWNGRADE_AUTONOMY; no-progress →
  REQUIRE_OPERATOR_REVIEW; budget alone → HOLD; high-risk external → BLOCK;
  external → REQUIRE_AUTHORITY (future P4+P9); irreversible without
  reversibility or checkpoint-missing → REQUIRE_CHECKPOINT (P3-FLOW-F
  discipline); irreversible → REQUIRE_PROOF (future P5); high risk →
  REQUIRE_VERIFIER; else ALLOW_CANDIDATE.
- `AutonomySafetyCandidate` (downgrade/freeze/resume/escalation, candidates
  only): a downgrade must move to a strictly lower tier — an upward
  "downgrade" is unconstructible; freeze is not execution stop; resume is
  not permission; escalation is not approval.
- `AutonomyViolationSignal` + `detect_self_upgrade_violation()`: a
  non-operator request for a higher (or untiered) level produces a
  SELF_UPGRADE_ATTEMPTED violation requiring review + freeze candidate;
  operator requests are not violations; a self-upgrade violation cannot be
  constructed unmarked.
- `OperatorAutonomyOverrideCandidate`: raising autonomy structurally
  requires `future_p9_required=True`; not authority, not permission.
- `GovernedAutonomyProjection`: read-only summary of mode/scope/gates/
  violations plus a live resolver posture summary (every decision class
  resolved at the mode's level); all UI-authority booleans structurally
  False; run-lineage validated.

## 6. Total Resolver Design

Rules + hard overrides, no manual Cartesian table and no partial lookup.
Precedence: (1) ERROR input → ERROR; (2) UNAVAILABLE input → UNAVAILABLE;
(3) side-effect classes → FORBIDDEN_IN_P3 with future P4+P9 at every level;
(4) REQUEST_PROOF → REQUIRES_P5_PROOF; (5) REQUEST_AUTHORITY →
REQUIRES_P9_AUTHORITY; (6) A9 → UNAVAILABLE (locked); (7)
REQUEST_EXECUTION → REQUIRES_P4_EXECUTION with operator review; (8)
REQUEST_PERMISSION → REQUIRES_OPERATOR_REVIEW with future P9; (9) tier
ladder — read-only classes ALLOWED_READ_ONLY, MARK_INTERNAL_READ_MODEL
ALLOWED_INTERNAL_PROJECTION_ONLY, candidate classes ALLOWED_CANDIDATE_ONLY
at/above a per-class minimum tier (suggest≥A1, prepare≥A2, internal
advance≥A3, auto internal transition≥A4) else REQUIRES_OPERATOR_REVIEW.
Unknown raw level/class strings → FORBIDDEN_IN_P3 with operator review,
never ALLOWED_*. Monotonicity: once a class is allowed at a tier it stays
allowed at every higher tier (proven by property test); documented
exception: A9 is outside the ladder by design.

## 7. Seed Fixtures

12 parametrized seed pairs pin the dispatch's exemplars (A0+OBSERVE →
ALLOWED_READ_ONLY; A0+SUGGEST → REQUIRES_OPERATOR_REVIEW; A1+SUGGEST →
ALLOWED_CANDIDATE_ONLY; A2+PREPARE_PLAN → ALLOWED_CANDIDATE_ONLY;
A2+REQUEST_EXECUTION → REQUIRES_P4_EXECUTION with operator review;
A5+EXTERNAL_SIDE_EFFECT / A6+TOOL_EXECUTION / A8+ROLLBACK_EXECUTION /
A4+MEMORY_WRITE → FORBIDDEN_IN_P3 future-bound; A9+side-effect →
FORBIDDEN_IN_P3; any+REQUEST_PROOF → REQUIRES_P5_PROOF; any+
REQUEST_AUTHORITY → REQUIRES_P9_AUTHORITY). Seeds are fixtures, not the
implementation.

## 8. Property / Invariant Tests

All 300 known (12 levels × 25 classes) pairs iterated: totality; no
authority/permission/execution/proof/trace/submit leak; side-effect classes
never ALLOWED_* (and future-bound P4+P9 outside the ERROR/UNAVAILABLE level
overrides); REQUEST_PROOF/AUTHORITY future-bound at every non-override
level including locked A9; A9 never ALLOWED_*; no UNAVAILABLE/ERROR leakage
for tiered pairs outside hard-override classes; monotonicity over the tier
ladder; unknown raw inputs fail closed.

## 9. Behavior Tests

64 tests across 7 files (6 levels + 22 scope/matrix + 11 gates + 8
drift/violation + 5 projection + 6 no-authority + 6 no-execution), every
file input→output behavioral — gate ladder decisions, self-upgrade
detection, downgrade tier enforcement, projection resolver-summary
coverage, and fail-closed construction attempts.

## 10. Boundary Proof

Structurally unconstructible as True (raises FORBIDDEN_BOUNDARY_CLAIM):
`self_selected`, `self_upgrade_allowed`, `authority_granted`,
`permission_granted`, `execution_available`, `live_execution_available`,
`proof_available`, `trace_verified`, `runtime_submit_wired`,
`scope_authorizes_action`, `mode_changed`, `execution_stopped`,
`approval_granted`, `frontend_mutation_allowed`,
`ui_autonomy_toggle_authority`, `ui_override_authority`,
`ui_execution_allowed`, `api_server_implemented`, `frontend_implemented`.
`future_p4/p5/p9_required` are set True wherever execution/proof/authority
would be required later, and a raising override cannot be constructed with
`future_p9_required=False`. AST + regex boundary tests prove no
subprocess/network/persistence/submit/React machinery in the H modules.

## 11. Lint / Type Suppression Audit

Zero new suppressions. The scan
(`# type: ignore|# noqa|pyright: ignore|pylint: disable|cast(Any|typing.Any`)
over `flow_autonomy*.py` and `test_p3_flow_h_*.py` returned no matches, and
the H no-execution boundary test forbids `# type: ignore`/`# noqa` in the H
modules permanently. ruff/mypy pass without any suppression.

## 12. Validation

`compileall src tests` PASS; H tests 64 passed; shared-module regression
(G reliability control 13 + G budget/guards 14 + G no-execution 7 + F
no-execution 7 + A no-execution 6 = 47) passed — run because `__init__.py`
is shared and the F/A/G boundary tests glob-scan the whole package
including the new H modules; ruff "All checks passed!"; mypy "Success: no
issues found in 394 source files"; suppression scan clean; broader A–F
regression not re-run (no earlier-pack module was modified — only
`__init__.py` additions, covered by the export-resolution check and the
regression subset above).

## 13. What Was Deliberately Not Implemented

P3.17+ scheduling/topology/harness/seal; P4 AurelExec; P5 AurelTrace; P9
Custos; runtime.submit bridge; any autonomous execution, dispatch, queue
insertion, or worker allocation; tool/LLM/subprocess/network/sandbox
execution; Trace/Ledger/memory/policy/identity writes; React components,
frontend routes, AurelShell UI, API server, REST/WebSocket; actual mode
changes (all safety responses are candidates only).

## 14. Persistence Status

UNAVAILABLE and out of scope. No FlowRunStore, database, event store, or
durable snapshot exists; autonomy modes/scopes/violations are in-memory
contracts. Durable autonomy state is a future P4/P5/P6 handoff risk only.

## 15. Next Pack Handoff

P3-FLOW-I — Workflow-Atomic Scheduling Intent / Resource Prediction.
Scheduling intent should consume `GovernedAutonomyLevel`,
`AutonomyScopeEnvelope` (TIME/COST/LATENCY scopes), and the gate/guard
signals rather than inventing parallel bounds. Risks: gate inputs are
caller-declared (P4 must feed real signals); the tier ladder's per-class
minimum tiers are v1 policy (new tables need a v2, never mutation);
P3-FLOW-K should measure resolver/gate quality.

## 16. Commit / Final Git Status

Implementation commit: `f1080cf` — `feat(flow): add P3-FLOW-H governed
autonomy scope` (20 files, +2863/−5); hash recorded in the follow-up
`docs(agent): record P3-FLOW-H commit hash` commit, per pack convention.
Final git status clean on master; no branch, no push, no history rewrite.
