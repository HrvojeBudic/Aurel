# P4-EXEC-D — Execution Modes Registry / Tool / Model / Terminal Profiles (Lean Validation)

## 1. Result Header

**DONE — CLOSED_WORLD_MODE_REGISTRY / UNKNOWN_MODE_BLOCKED / NO_SILENT_FALLBACK / TOOL_ONLY_THROUGH_EXISTING_BRIDGE / MODEL_PROFILE_ONLY / TERMINAL_CODE_UNAVAILABLE / PROFILE_IS_NOT_PERMISSION / BRIDGE_PRESERVED / P4_EXEC_E_NEXT**

Date: 2026-07-03. Roadmap: Aurel Roadmap v5.5, P4.10–P4.13. Lean validation edition: focused D-pack tests + compileall + ruff on touched paths only (no full pytest, no regression globs, no full-project mypy — deliberate, per dispatch).

## 2. Pack Scope

P4-EXEC-D teaches the managed runtime which execution modes are allowed, profile-only, unavailable, or blocked: a closed-world `ExecutionModeRegistry` total over the `ExecutionMode` enum, a generic `ExecutionModeProfile` with explicit requirements, specialized `ToolExecutionProfile`/`ModelExecutionProfile`/`TerminalExecutionProfile`/`CodeExecutionProfile`, a deterministic `ModeCompatibilityDecision`, a narrow queue hook reusing the C `block_queue_entry` helper, a read-only `ModeProjection`, and four new fail-closed proofs (the B-era `NoDirectDispatchProof` is reused).

## 3. Canon / Preflight

Branch `master`, clean at start, HEAD `364760e` (P4-EXEC-C hash record). Canon read: ACTIVE_TASK (P4-EXEC-C complete, P4-EXEC-D next), ROADMAP pointer, STATE, ARCHITECTURE, DECISIONS, TESTS, REPORTS, all three P4-EXEC reports, full aurel_exec source. No canon conflicts.

## 4. P4-EXEC-C Prerequisite Confirmation

`agent/reports/P4_EXEC_C_WORKER_QUEUE_BUS_CHECKPOINT_RUNTIME_SHAPE.md` exists; commits `a6dc80b` + `364760e` in history. The C managed shape is consumed unchanged: `exec_queue.py`, `exec_worker.py`, `exec_messages.py`, `exec_checkpoint.py`, and `exec_runtime_bridge.py` all have **zero edits** in this pack — the mode hook (`enforce_mode_compatibility_before_claim`) lives in the new `exec_modes.py` and calls the existing `block_queue_entry` helper.

## 5. Operational Debt Guard Proof

Avoided: live model execution and any model API import (`model_router`/`model_providers` imports sweep-forbidden in D modules), terminal/shell/subprocess execution, code eval/script running (`eval(`/`exec(`/`os.system`/`open(` sweep-forbidden), filesystem mutation, network execution, new sandbox paths, tool platform expansion (allowed tools structurally capped at the bridge's `SUPPORTED_BRIDGE_TOOLS`), verifier/recovery engines, decorative profile hierarchies (one generic profile + four specialized ones, all frozen contracts).

Why model/terminal/code remain unavailable/profile-only: no router/budget/prompt/output-contract canon exists for models; no sandbox/operator/P9 authority canon exists for terminal; no verifier canon exists for code — the profiles carry those requirements as structurally mandatory (`requires_* = False` is unconstructible) so the future packs inherit an explicit checklist instead of an open door.

How P4-EXEC-E ambiguity was reduced: Exec-E's verifier/recovery decisions can consume per-mode requirements (`requires_verifier`, `requires_p5_proof`, `requires_p9_authority` on every profile), the blocked/unavailable reasons name their future owners, and the compatibility decision's `missing_requirements` gives failure classification a deterministic input.

## 6. Execution Mode Registry Proof

`ExecutionModeRegistry` is total over `ExecutionMode` by construction — a registry missing a mode or carrying a duplicate is unconstructible; `registry_is_closed_world`/`unknown_mode_blocked` locked True; `silent_fallback_allowed`/`grants_authority`/`executes` locked False; `default_mode` must be an available mode. Default classification: TOOL → AVAILABLE_FOR_EXISTING_BRIDGE; MODEL → PROFILE_ONLY; TERMINAL/CODE/CONVERSATION/COMPOSITE → UNAVAILABLE with reasons; UNAVAILABLE/ERROR posture markers → BLOCKED. Unknown raw strings → BLOCKED with the closed-world reason.

## 7. Tool Profile Proof

`ToolExecutionProfile`: `direct_dispatch_allowed` unconstructibly True; `runtime_bridge_required`/`mutating_tools_unavailable`/`requires_lease_scope_match` unconstructibly False; every allowed tool must be declared read-only AND within `SUPPORTED_BRIDGE_TOOLS` (both violations tested: `write_file` rejected as not read-only, `list_dir` rejected as exceeding the bridge path); empty tool list rejected. The default profile is exactly `("read_file",)` — the path B proved against the real kernel. LIVE label per dispatch truth posture: the profile binds real, tested backend logic to the real bridge path.

## 8. Model Profile Unavailable Proof

`ModelExecutionProfile`: `model_execution_available`/`model_call_allowed` unconstructibly True; all six future requirements (router/budget/policy/prompt-contract/output-contract/verifier) unconstructibly False; UNAVAILABLE label with mandatory reason. No model API import exists in D modules (sweep-tested). `NoModelCallProof` fail-closed.

## 9. Terminal Profile Unavailable Proof

`TerminalExecutionProfile`: `terminal_execution_available`/`subprocess_allowed`/`shell_allowed`/`network_allowed` unconstructibly True; sandbox/operator-approval/P9 requirements unconstructibly False. No subprocess/socket import in D modules (sweep-tested). `NoTerminalExecutionProof` fail-closed.

## 10. Code Profile Unavailable Proof

`CodeExecutionProfile`: `code_execution_available`/`eval_allowed`/`script_execution_allowed`/`filesystem_mutation_allowed`/`network_allowed` unconstructibly True; sandbox/verifier/P9 requirements unconstructibly False. No `eval(`/`exec(`/`open(`/`os.system` in D modules (sweep-tested). `NoCodeExecutionProof` fail-closed.

## 11. Mode Compatibility Proof

`decide_mode_compatibility` is a pure deterministic function (same inputs ⇒ same decision id): unknown string → BLOCKED; BLOCKED/UNAVAILABLE/PROFILE_ONLY/ERROR availability → blocked with explicit reason; TOOL → allowed only when the tool profile names the tool AND the lease scope matches mode/tool — mismatches produce named `missing_requirements`. The decision object is structurally honest: `allowed == blocked` is unconstructible, `fallback_mode` may not exist at all, `silent_fallback_used` locked False, and an allowed reason states "allowed is not runtime success". `require_mode_compatibility` raises fail-closed (UNSUPPORTED_EXECUTION_MODE); `enforce_mode_compatibility_before_claim` blocks the queue entry via the existing C helper and returns an allowed entry untouched.

## 12. Projection Proof

`ModeProjection` (read-only, frozen): registry classification (supported/profile-only/unavailable/blocked mode lists + per-family profile statuses), optional requested-mode decision view (`mode_available` claimable only for registry-supported modes; a non-available requested mode must carry a blocked reason), and 16 risky-claim booleans structurally False (fallback, direct dispatch, model call, terminal/shell/subprocess, code/eval/script, new sandbox, network, P5, P9, Shell/React/API).

## 13. No Direct Dispatch Proof

B-era `NoDirectDispatchProof` reused and re-asserted; `ToolExecutionProfile.direct_dispatch_allowed` unconstructibly True; D modules sweep-forbid `.dispatch(` and the tools-module import; `ExecRuntimeBridge` remains the only sanctioned kernel reference (unchanged this pack).

## 14. No Model Call Proof — §8; `NoModelCallProof` + import sweep.

## 15. No Terminal/Subprocess Proof — §9; `NoTerminalExecutionProof` + import sweep.

## 16. No Code/Eval/Script Proof — §10; `NoCodeExecutionProof` + source sweep.

## 17. No Silent Fallback Proof

`NoSilentFallbackProof` fail-closed; the decision contract makes fallback structurally unrepresentable (`fallback_mode` must be None, `silent_fallback_used` locked False); every blocked-mode test asserts blocked-with-reason rather than any redirection; the registry's `silent_fallback_allowed` locked False.

## 18. Roadmap Coverage Matrix

| Range | Status | Evidence |
|---|---|---|
| P4.10 Execution Modes Registry | DONE | `exec_modes.py`; test_exec_modes.py (8) |
| P4.11 Tool Execution Profile | DONE | `exec_mode_profiles.py`; test_exec_tool_profile.py (5) |
| P4.12 Model Execution Profile | DONE (PROFILE_ONLY) | test_exec_risky_mode_profiles.py |
| P4.13 Terminal / Code Execution Profile | DONE (UNAVAILABLE) | test_exec_risky_mode_profiles.py (5) |
| Compatibility + hook + projection | DONE | test_exec_mode_compatibility.py (7) + test_exec_mode_projection.py (6) |

## 19. P4.10 Status — DONE (see §6). Registry does not execute and grants no authority; no execute/run/submit/dispatch/authorize surface exists (tested).

## 20. P4.11 Status — DONE (see §7). Tool mode LIVE only for the existing safe read-only bridge path; mutating tools structurally unavailable with reason.

## 21. P4.12 Status — DONE as PROFILE_ONLY (see §8). Model profile exists; model execution/calls structurally unavailable; requirements checklist mandatory.

## 22. P4.13 Status — DONE as UNAVAILABLE (see §9–§10). Terminal and code profiles exist; every execution boolean structurally False; P9/operator/sandbox/verifier requirements mandatory.

## 23. Lean Tests / Validation

```
.venv/bin/python -m compileall src/agentic_runtime/aurel_exec tests/aurel_exec → PASS
.venv/bin/python -m pytest tests/aurel_exec/test_exec_modes.py
  tests/aurel_exec/test_exec_tool_profile.py
  tests/aurel_exec/test_exec_risky_mode_profiles.py
  tests/aurel_exec/test_exec_mode_compatibility.py
  tests/aurel_exec/test_exec_mode_projection.py -q → 31 passed
  (modes 8 · tool profile 5 · risky profiles 5 · compatibility 7 · projection 6)
.venv/bin/python -m ruff check src/agentic_runtime/aurel_exec tests/aurel_exec → All checks passed
git status --short → only in-scope changes; clean after commit
```

Deliberately not run (lean mandate): full pytest, full `tests/aurel_exec`, runtime/tool/sandbox/trace regression globs, full-project mypy. Shared-file changes were additive only (`__init__.py` exports, `exec_projection.py` new ModeProjection + one import); A/B/C compatibility is expected but not re-executed this run. Truth-label note: `ExecTruthLabel` was deliberately **not** widened with PROFILE_ONLY/BLOCKED members — that posture is carried by `ExecutionModeAvailability`, keeping the sealed A-pack label vocabulary and its exact-set test intact under lean validation (recorded in DECISIONS).

## 24. Files Created / Modified

Created: `src/agentic_runtime/aurel_exec/{exec_modes,exec_mode_profiles}.py`; `tests/aurel_exec/{test_exec_modes,test_exec_tool_profile,test_exec_risky_mode_profiles,test_exec_mode_compatibility,test_exec_mode_projection}.py`; this report.

Modified: `aurel_exec/{__init__,exec_projection}.py` (additive); `agent/{REPORTS,STATE,ACTIVE_TASK,ROADMAP,ARCHITECTURE,DECISIONS,TESTS}.md`.

Untouched: `exec_runtime_bridge.py`, `exec_queue.py`, `exec_worker.py`, `exec_messages.py`, `exec_checkpoint.py`, all A/B modules, all runtime/kernel sources, all web/frontend paths.

## 25. What Was Deliberately Not Implemented

Live model execution / model API calls; terminal/shell/subprocess execution; code eval/script execution; filesystem mutation; network execution; new sandbox execution; tool expansion beyond `read_file`; verifier/recovery engines (P4-EXEC-E); algedonic routing; topology/concurrency/backpressure; harness telemetry; P5 trace verification; P8 routing; P9 enforcement; Shell UI/React/API server.

## 26. Remaining Risks

- The registry is a value object; nothing yet pins "the" canonical registry instance at runtime — a registry authority/selection discipline belongs to a future pack (each instance is internally honest).
- The compatibility hook is opt-in (callers must invoke it before claim/run); wiring it as a mandatory step inside the managed helper was deferred to avoid touching C under lean validation — Exec-E should decide where the mandatory call sites live.
- PROFILE_ONLY/BLOCKED as availability-statuses-not-truth-labels is a documented mapping; if a future pack widens `ExecTruthLabel`, the A exact-set test must move with it in the same commit.
- `build_mode_projection` duck-types its registry/decision params (kept exec_projection import-light); typed signatures can land when the mode surface stabilizes.

## 27. Next Pack: P4-EXEC-E

Verifier / Failure Classification / Bounded Recovery / Algedonic Signals — attach verifier hooks and semantic guards to mode requirements, classify failures from bridge outcomes and causality messages, and add bounded recovery over the C checkpoint refs, keeping rollback execution gated on P9.

## 28. Commit Hash

`7229c6e` — `feat(aurel-exec): add execution mode registry` (17 files, +1776/−6).

## 29. Final Git Status

Clean after commit (`git status --short` empty); verified in the run that produced this report.
