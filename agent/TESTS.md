# Tests & Verification

## Canonical commands

From repository root, using the project venv (`.venv/bin/python`).

**Bare `python3`, `pytest`, `ruff`, and `mypy` are NOT authoritative.**
**System `/usr/bin/python3` is NOT authoritative.**
**Validation MUST run through the project venv or an equivalent activated environment.**

```bash
# Compile check
.venv/bin/python -m compileall src tests

# Test suite (full)
.venv/bin/python -m pytest -q --tb=line

# Lint (ruff)
.venv/bin/python -m ruff check src tests

# Type check (mypy)
.venv/bin/python -m mypy src/agentic_runtime

# Coverage (must measure src/agentic_runtime)
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
```

**Why venv is required:** The project uses a virtualenv at `.venv/`. Running
commands through `.venv/bin/python` ensures that all dev dependencies (pytest,
ruff, mypy, pytest-cov) are available, and that coverage instruments the
correct package path.

**Coverage target:** Coverage must measure `src/agentic_runtime` (the real
runtime source), must pass with `--cov-fail-under=75`, and must not exclude
large modules just to pass.

# Via CLI wrapper
python -m agentic_runtime.cli verify
```

## Lean validation doctrine (v5.1 Integration-First)

**Default for phase work:** focused pytest on the touched subsystem plus compileall/ruff/mypy when Python changes.

**Operator manual seal** (not required for docs-only tasks like P1.6.19):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

Run full pytest/coverage/Bandit only when:

- Runtime/security/sandbox/network/subprocess/secrets paths are touched
- Focused validation reveals a cross-system issue
- Operator explicitly requests full validation

Docs-only patches (agent reports/state) require `git status --short` verification only.

## P1.ENF-A Policy + Identity Enforcement Bridge Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_governance_enforcement_submit.py -q
.venv/bin/python -m pytest tests/test_identity_submit_context.py -q
.venv/bin/python -m pytest tests/test_entrypoint_governance_guard.py -q
.venv/bin/python -m pytest tests -q -k "runtime or policy or policy_cards or identity or repo_agent or aurel_shell"
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results after P1.ENF-A: compileall **PASS**; governance enforcement submit **11 passed**; identity submit context **7 passed**; entrypoint governance guard **6 passed**; runtime/policy/identity/repo_agent/aurel_shell regression subset **3229 passed, 3493 deselected**; ruff **PASS**; mypy **PASS** (328 source files); Bandit `-ll` **PASS**. Optional full pytest was interrupted after extended runtime with **4140 passed** and no failure output before interrupt; not claimed as full-suite PASS. Coverage was not run after the optional full-suite interruption.

P1.ENF-A is an explicit-config runtime submit enforcement bridge only. It does NOT implement P2.9-B, P2.9-C, P2.9-D, P2.10+, full Custos runtime, full permission matrix, Shell command router, product UI, identity CLI monolith refactor, Golden Thread B, sandbox backend rewrite, memory behavior rewrite, trace ledger rewrite, production LIVE, TRACE_VERIFIED, P2 completion, or Shell completion.

Report: `agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md`

## P1.ENF-A-OMNI-R1 Validation Truth / Core Integrity Repair Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_consent_fixture_determinism.py -q
.venv/bin/python -m pytest tests/test_trace_merkle_integrity.py -q
.venv/bin/python -m pytest tests/test_trace.py tests/test_trace_persistence_p06.py -q
.venv/bin/python -m pytest tests/test_governance_enforcement_submit.py tests/test_identity_submit_context.py tests/test_entrypoint_governance_guard.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m mypy --follow-imports=silent \
  --enable-error-code arg-type \
  --enable-error-code call-arg \
  --enable-error-code union-attr \
  src/agentic_runtime/runtime.py \
  src/agentic_runtime/trace.py \
  src/agentic_runtime/repo_agent.py \
  src/agentic_runtime/core_types.py \
  src/agentic_runtime/__init__.py
```

**Validation truth:** Baseline mypy (`src/agentic_runtime`) keeps repo-wide disabled error codes in `pyproject.toml` and is not a strict core wiring proof. The **core strict probe** above scopes to five runtime/security files with `arg-type`, `call-arg`, and `union-attr` enabled and `--follow-imports=silent` so transitive identity/shell/policy lattice debt is not misread as core wiring failure. Running the same five files without `--follow-imports=silent` still surfaces broad transitive type debt outside this repair scope — that result is **not** claimed as core probe PASS.

Results after P1.ENF-A-OMNI-R1: compileall **PASS**; consent fixture determinism **4 passed**; trace Merkle integrity **2 passed**; trace regression **12 passed**; P1.ENF-A regression **24 passed**; ruff **PASS**; baseline mypy **PASS** (328 source files); core strict probe **PASS** (5 source files, silent imports). Full suite and coverage **NOT RUN**. Bandit **NOT RUN**.

P1.ENF-A-OMNI-R1 is validation-truth repair only. It does NOT implement P1.ENF-B, P2.9-B, global mypy strictness, full type safety, TRACE_VERIFIED, LIVE, or product behavior.

Report: `agent/reports/P1_ENF_A_OMNI_R1_VALIDATION_TRUTH_CORE_INTEGRITY_REPAIR.md`

## P1.ENF-C Golden Thread B / P1.8–P2.9 Governance Continuity Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q
.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_entrypoint_governance_audit.py tests/test_repo_agent_entrypoint_audit.py -q
.venv/bin/python -m pytest tests/test_governance_enforcement_submit.py tests/test_identity_submit_context.py tests/test_entrypoint_governance_guard.py -q
.venv/bin/python -m pytest tests/test_trace_merkle_integrity.py tests/test_consent_fixture_determinism.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m mypy --follow-imports=silent \
  --enable-error-code arg-type \
  --enable-error-code call-arg \
  --enable-error-code union-attr \
  src/agentic_runtime/runtime.py \
  src/agentic_runtime/trace.py \
  src/agentic_runtime/repo_agent.py \
  src/agentic_runtime/core_types.py \
  src/agentic_runtime/__init__.py
```

Results after P1.ENF-C: compileall **PASS**; Golden Thread B **17 passed**; validation truth + drift gates **18 passed**; entrypoint audit **16 passed**; P1.ENF-A enforcement **24 passed**; trace/consent repair **6 passed**; ruff **PASS**; baseline mypy **PASS** (332 source files); core strict probe **PASS** (5 files, silent imports). Full suite, coverage, Bandit, and optional selector **NOT RUN**.

P1.ENF-C is a governance continuity harness only. It does NOT implement P1.ENF-F-B, P1.ENF-D1, P1.ENF-E, P2.9-B, Shell command router, product UI, LIVE, TRACE_VERIFIED, or all-evidence-complete claim.

Report: `agent/reports/P1_ENF_C_GOLDEN_THREAD_B_GOVERNANCE_CONTINUITY.md`

## P1.ENF-E Sandbox Safe Backend Gating / UnsafeLocalSandbox Hardening Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_sandbox_backend_gate.py -q
.venv/bin/python -m pytest tests/test_sandbox_safe_backend_submit.py -q
.venv/bin/python -m pytest tests/test_governance_enforcement_submit.py -q
.venv/bin/python -m pytest tests/test_identity_invariant_enforcement_submit.py tests/test_identity_submit_context.py -q
.venv/bin/python -m pytest tests/test_entrypoint_governance_guard.py -q
.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m mypy --follow-imports=silent \
  --enable-error-code arg-type \
  --enable-error-code call-arg \
  --enable-error-code union-attr \
  src/agentic_runtime/runtime.py \
  src/agentic_runtime/trace.py \
  src/agentic_runtime/repo_agent.py \
  src/agentic_runtime/core_types.py \
  src/agentic_runtime/__init__.py
```

Results after P1.ENF-E: compileall **PASS**; sandbox backend gate **9 passed**; sandbox safe backend submit **4 passed**; governance enforcement submit **11 passed**; identity invariant enforcement submit **9 passed**; identity submit context **7 passed**; entrypoint governance guard **6 passed**; validation truth + drift gates **18 passed**; Golden Thread B **17 passed**; ruff **PASS**; baseline mypy **PASS** (336 source files); core strict probe **PASS** (5 files, silent imports). Full suite, coverage, Bandit, and optional selector **NOT RUN**.

P1.ENF-E is sandbox backend safety classification and gating only. It does NOT implement full sandbox platform, container/Firecracker/seccomp/AppArmor, P2.REVIEW-A, P2.9-B, Shell command router, product UI, LIVE, TRACE_VERIFIED, SAFE_VERIFIED without proof, or P2 complete claim.

Report: `agent/reports/P1_ENF_E_SANDBOX_SAFE_BACKEND_GATING_UNSAFE_LOCAL_HARDENING.md`

## P1.ENF-D1 Identity Kernel Invariant Enforcement Deepening Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_identity_kernel_invariants.py -q
.venv/bin/python -m pytest tests/test_identity_invariant_enforcement_submit.py -q
.venv/bin/python -m pytest tests/test_identity_submit_context.py tests/test_governance_enforcement_submit.py -q
.venv/bin/python -m pytest tests/test_entrypoint_governance_guard.py -q
.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m mypy --follow-imports=silent \
  --enable-error-code arg-type \
  --enable-error-code call-arg \
  --enable-error-code union-attr \
  src/agentic_runtime/runtime.py \
  src/agentic_runtime/trace.py \
  src/agentic_runtime/repo_agent.py \
  src/agentic_runtime/core_types.py \
  src/agentic_runtime/__init__.py
```

Results after P1.ENF-D1: compileall **PASS**; identity kernel invariants **2 passed**; identity invariant enforcement submit **9 passed**; identity submit context **7 passed**; governance enforcement submit **11 passed**; entrypoint governance guard **6 passed**; validation truth + drift gates **18 passed**; Golden Thread B **17 passed**; ruff **PASS**; baseline mypy **PASS** (334 source files); core strict probe unchanged from prior baseline (5-file probe with pre-existing unrelated strict findings). Full suite, coverage, Bandit, and optional selector **NOT RUN**.

P1.ENF-D1 is selected Identity Kernel invariant enforcement only. It does NOT implement full IK enforcement, identity CLI refactor, auth/session subsystem, Custos runtime, sandbox hardening, P1.ENF-E, P2.REVIEW-A, P2.9-B, Shell command router, product UI, LIVE, TRACE_VERIFIED, or P2 complete claim.

Report: `agent/reports/P1_ENF_D1_IDENTITY_KERNEL_INVARIANT_ENFORCEMENT_DEEPENING.md`

## P1.ENF-F-B Roadmap v5.5 Canon Sync / Historical Docs Archive Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q
.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_entrypoint_governance_audit.py tests/test_repo_agent_entrypoint_audit.py -q
.venv/bin/python -m pytest tests/test_docs_canon_status.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m mypy --follow-imports=silent \
  --enable-error-code arg-type \
  --enable-error-code call-arg \
  --enable-error-code union-attr \
  src/agentic_runtime/runtime.py \
  src/agentic_runtime/trace.py \
  src/agentic_runtime/repo_agent.py \
  src/agentic_runtime/core_types.py \
  src/agentic_runtime/__init__.py
```

Results after P1.ENF-F-B: compileall **PASS**; Golden Thread B **17 passed**; validation truth + drift gates **18 passed**; entrypoint audit **16 passed**; docs canon status **9 passed**; ruff **PASS**; baseline mypy **PASS**; core strict probe **PASS** (5 files, silent imports). Full suite, coverage, Bandit, and optional selector **NOT RUN**.

P1.ENF-F-B is docs/canon sync only. It does NOT implement P1.ENF-D1, P1.ENF-E, P2.REVIEW-A, P2.9-B, Shell command router, product UI, ROADMAP renumbering/rewrite, historical evidence deletion, LIVE, TRACE_VERIFIED, or P2 complete claim.

Report: `agent/reports/P1_ENF_F_B_ROADMAP_V55_CANON_SYNC_HISTORICAL_DOCS_ARCHIVE.md`

## P1.ENF-F-A Tooling / Determinism / Shadow-Still-Active Drift Gates Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_validation_truth_gates.py -q
.venv/bin/python -m pytest tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_consent_fixture_determinism.py tests/test_trace_merkle_integrity.py -q
.venv/bin/python -m pytest tests/test_entrypoint_governance_audit.py tests/test_repo_agent_entrypoint_audit.py -q
.venv/bin/python -m pytest tests/test_governance_enforcement_submit.py tests/test_identity_submit_context.py tests/test_entrypoint_governance_guard.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m mypy --follow-imports=silent \
  --enable-error-code arg-type \
  --enable-error-code call-arg \
  --enable-error-code union-attr \
  src/agentic_runtime/runtime.py \
  src/agentic_runtime/trace.py \
  src/agentic_runtime/repo_agent.py \
  src/agentic_runtime/core_types.py \
  src/agentic_runtime/__init__.py
```

Results after P1.ENF-F-A: compileall **PASS**; validation truth gates **6 passed**; drift gates **12 passed**; P1.ENF-A-OMNI-R1 repair **6 passed**; P1.ENF-B audit **16 passed**; P1.ENF-A enforcement **24 passed**; ruff **PASS**; baseline mypy **PASS** (331 source files); core strict probe **PASS** (5 files, silent imports). Full suite, coverage, Bandit, and optional selector **NOT RUN**.

P1.ENF-F-A is a lightweight drift/validation gate layer only. It does NOT implement P1.ENF-C, P1.ENF-F-B, P1.ENF-D1, P1.ENF-E, P2.9-B, full CI, global mypy strictness, Shell command router, product UI, LIVE, TRACE_VERIFIED, or all-drift-impossible claim.

Report: `agent/reports/P1_ENF_F_A_TOOLING_DETERMINISM_SHADOW_DRIFT_GATES.md`

## P1.ENF-B Entrypoint Bypass Guard Expansion / Repo Agent Enforcement Audit Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_entrypoint_governance_audit.py -q
.venv/bin/python -m pytest tests/test_repo_agent_entrypoint_audit.py -q
.venv/bin/python -m pytest tests/test_entrypoint_governance_guard.py -q
.venv/bin/python -m pytest tests/test_governance_enforcement_submit.py tests/test_identity_submit_context.py -q
.venv/bin/python -m pytest tests/test_trace.py tests/test_trace_merkle_integrity.py tests/test_consent_fixture_determinism.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m mypy --follow-imports=silent \
  --enable-error-code arg-type \
  --enable-error-code call-arg \
  --enable-error-code union-attr \
  src/agentic_runtime/runtime.py \
  src/agentic_runtime/trace.py \
  src/agentic_runtime/repo_agent.py \
  src/agentic_runtime/core_types.py \
  src/agentic_runtime/__init__.py
```

Results after P1.ENF-B: compileall **PASS**; entrypoint governance audit **10 passed**; repo_agent entrypoint audit **6 passed**; entrypoint governance guard **6 passed**; P1.ENF-A regression **18 passed**; P1.ENF-A-OMNI-R1 repair **7 passed**; ruff **PASS**; baseline mypy **PASS** (329 source files); core strict probe **PASS** (5 files). Optional aurel_shell, full suite, and Bandit **NOT RUN**.

P1.ENF-B is entrypoint audit/guard expansion only. It does NOT implement P1.ENF-C, P2.9-B, Shell command router, product UI, repo_agent rewrite, identity CLI refactor, sandbox hardening, LIVE, TRACE_VERIFIED, or all-entrypoints-safe claim.

Report: `agent/reports/P1_ENF_B_ENTRYPOINT_BYPASS_GUARD_REPO_AGENT_ENFORCEMENT_AUDIT.md`

## P2.10-C Tauri Desktop Local Shell Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -c "from agentic_runtime.aurel_shell.web_shell_read_model import export_web_shell_read_model_fixture; from agentic_runtime.aurel_shell.desktop_shell_contract import export_desktop_shell_read_model_fixture; export_web_shell_read_model_fixture(); export_desktop_shell_read_model_fixture()"
.venv/bin/python -m pytest tests/test_p210c_desktop_shell_contract.py -q
.venv/bin/python -m pytest tests/test_p210c_desktop_capability_boundary.py -q
.venv/bin/python -m pytest tests/test_p210c_tauri_wrapper_truth.py -q
.venv/bin/python -m pytest tests/test_p210b_web_shell_read_model.py tests/test_p210b_web_shell_contract_binding.py -q
.venv/bin/python -m pytest tests/test_p210a_multi_client_foundation.py tests/test_shell_client_parity_matrix.py tests/test_shell_client_run_modes.py -q
.venv/bin/python -m pytest tests/test_shell_exit_final_seal.py tests/test_p29d_p210_entry_gate.py tests/test_p29d_final_tail_handoff.py -q
.venv/bin/python -m pytest tests/test_p2_command_palette_vslice.py tests/test_p2_command_preflight.py tests/test_p2_vertical_slice_review.py -q
.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime/aurel_shell/desktop_shell_contract.py src/agentic_runtime/aurel_shell/web_shell_read_model.py
cd web/shell && npm install && npm run typecheck && npm test && npm run build && npm run tauri:build
```

Results after P2.10-C: compileall **PASS**; P2.10-C focused **20 passed**; P2.10-B regression **18 passed**; P2.10-A regression **23 passed**; P2.9-D seal **15 passed**; P2 vertical slice **25 passed**; truth/drift **18 passed**; Golden Thread B **17 passed**; ruff **PASS**; mypy **PASS**; frontend typecheck **PASS**; vitest **11 passed**; build **PASS**; tauri build **PASS**. Full suite and coverage **NOT RUN**.

P2.10-C is a Tauri desktop local shell / desktop wrapper contract pack only. It does NOT implement P2.10-D/E, mobile app, CLI/TUI parity, arbitrary command execution, native file/secrets/shell/runtime/sandbox authority, Shell LIVE, production desktop app, full local app, or change P2.VSLICE-A preflight, command preflight, policy, identity, or sandbox behavior. Runnable desktop wrapper is DEV_FIXTURE — not Shell LIVE, not full desktop app, not native authority.

Report: `agent/reports/P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md`

## P2.10-B Local Web Shell Skeleton Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -c "from agentic_runtime.aurel_shell.web_shell_read_model import export_web_shell_read_model_fixture; export_web_shell_read_model_fixture()"
.venv/bin/python -m pytest tests/test_p210b_web_shell_read_model.py -q
.venv/bin/python -m pytest tests/test_p210b_web_shell_contract_binding.py -q
.venv/bin/python -m pytest tests/test_p210a_multi_client_foundation.py tests/test_shell_client_parity_matrix.py tests/test_shell_client_run_modes.py -q
.venv/bin/python -m pytest tests/test_shell_exit_final_seal.py tests/test_p29d_p210_entry_gate.py tests/test_p29d_final_tail_handoff.py -q
.venv/bin/python -m pytest tests/test_p2_command_palette_vslice.py tests/test_p2_command_preflight.py tests/test_p2_vertical_slice_review.py -q
.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime/aurel_shell/web_shell_read_model.py
cd web/shell && npm install && npm run typecheck && npm test && npm run build
```

Results after P2.10-B: compileall **PASS**; P2.10-B focused **18 passed**; P2.10-A regression **22 passed**; P2.9-D seal **15 passed**; P2 vertical slice **25 passed**; truth/drift **18 passed**; Golden Thread B **17 passed**; ruff **PASS**; mypy **PASS**; frontend typecheck **PASS**; vitest **6 passed**; build **PASS**. Full suite and coverage **NOT RUN**.

P2.10-B is a local web Shell skeleton / contract-bound read model pack only. It does NOT implement P2.10-C/D/E, Tauri desktop, mobile app, CLI/TUI parity, arbitrary command execution, Shell LIVE, production API server, full API/event bridge live, full local app, or change P2.VSLICE-A preflight, command preflight, policy, identity, or sandbox behavior. Runnable local web skeleton is DEV_FIXTURE — not Shell LIVE or full local app.

Report: `agent/reports/P2_10_B_LOCAL_WEB_SHELL_SKELETON.md`

## P2.10-A Multi-Client Shell Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_p210a_multi_client_foundation.py -q
.venv/bin/python -m pytest tests/test_shell_client_parity_matrix.py -q
.venv/bin/python -m pytest tests/test_shell_client_run_modes.py -q
.venv/bin/python -m pytest tests/test_shell_exit_final_seal.py tests/test_p29d_p210_entry_gate.py tests/test_p29d_final_tail_handoff.py -q
.venv/bin/python -m pytest tests/test_shell_exit_finalization.py tests/test_p29c_release_boundaries.py tests/test_p29c_finalization_evidence_bundle.py -q
.venv/bin/python -m pytest tests/test_shell_exit_readiness.py tests/test_shell_exit_validation_matrix.py tests/test_p29b_shell_exit_evidence_matrix.py -q
.venv/bin/python -m pytest tests/test_p2_command_palette_vslice.py -q
.venv/bin/python -m pytest tests/test_p2_command_preflight.py -q
.venv/bin/python -m pytest tests/test_p2_vertical_slice_review.py -q
.venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q
.venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results after P2.10-A: compileall **PASS**; P2.10-A focused **22 passed**; P2.9 seal regressions **140 passed**; ruff **PASS**; mypy **PASS** on new module. Full suite and coverage **NOT RUN**.

P2.10-A is a contract-only multi-client Shell foundation pack only. It does NOT implement P2.10-B/C/D, full web UI, Tauri desktop app, mobile app, arbitrary command execution, Shell LIVE, production API server, full API/event bridge live, runnable local app, or change P2.VSLICE-A preflight, command preflight, policy, identity, or sandbox behavior.

Report: `agent/reports/P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md`

## P2.9-A Shell Exit Seal Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_exit_seal_foundation.py -q
.venv/bin/python -m pytest tests/aurel_shell/test_shell_exit_seal_foundation_evidence_refs.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results after P2.9-A-R1 evidence-ref repair: compileall **PASS**; focused P2.9-A **16 passed**; evidence ref integrity **10 passed**; `tests/aurel_shell` **1004 passed**; ruff **PASS**; mypy **PASS** (324 source files).

P2.9-A is a contract-only Shell Exit Seal foundation pack only. It does NOT create completed Shell Exit Seal, release seal, product readiness, P2 completion, Shell completion, live Shell runtime, multi-client runtime, frontend/product UI, operator-testable product behavior, validation execution, trace verification, permission enforcement, Custos decisioning, truth-label enforcement, runtime dispatch, command execution, trace write, memory write, storage write, agent governance replacement, LIVE, TRACE_VERIFIED, release scope, or start P2.9-B, P2.9-C, P2.9-D, P2.10, P2.11, P2.12, or P2.13.

Report: `agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md`
Repair report: `agent/reports/P2_9_A_R1_SHELL_EXIT_SEAL_FOUNDATION_EVIDENCE_REF_REPAIR.md`

## P2.8-D Shell State / Reports / Docs Section Seal Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_state_section_seal.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.8-D **15 passed**; `tests/aurel_shell` **978 passed**; ruff **PASS**; mypy **PASS** (323 source files).

P2.8-D is a contract-only Shell State / Reports / Docs section seal pack only. It does NOT create live Shell state runtime, Shell state sync runtime, state reconciliation engine, repair/autofix action, refresh runtime, persistent state store, database persistence, storage write, trace write, memory write, docs write, reports write, report generator runtime, docs generator runtime, summary generator runtime, report publisher, docs publisher, agent/REPORTS.md replacement, agent/ governance replacement, docs source-of-truth, product UI, product behavior, CLI runner, TUI runtime, command execution, runtime dispatch, permission enforcement, Custos decisioning, approval runtime, release seal, LIVE, TRACE_VERIFIED, release scope, P2 complete, Shell complete, or start P2.9, P2.10, P2.11, P2.12, or P2.13.

Report: `agent/reports/P2_8_D_SHELL_STATE_REPORTS_DOCS_SECTION_SEAL.md`

## P2.8-C Docs Index / State Sync / Read-Only Summary Boundary Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_state_summary.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.8-C **14 passed**; `tests/aurel_shell` **963 passed**; ruff **PASS**; mypy **PASS** (322 source files).

P2.8-C is a contract-only read-only summary and sync descriptor boundary pack only. It does NOT create live Shell state runtime, Shell state sync runtime, state reconciliation engine, repair/autofix action, refresh runtime, persistent state store, database persistence, storage write, trace write, memory write, docs write, reports write, report generator runtime, docs generator runtime, summary generator runtime, report publisher, docs publisher, agent/REPORTS.md replacement, agent/ governance replacement, docs source-of-truth, product UI, product behavior, CLI runner, TUI runtime, command execution, runtime dispatch, permission enforcement, Custos decisioning, approval runtime, LIVE, TRACE_VERIFIED, release scope, or start P2.8-D, P2.9, P2.10, or P2.13.

Report: `agent/reports/P2_8_C_DOCS_INDEX_STATE_SYNC_READ_ONLY_SUMMARY.md`

## P2.8-B Shell State Read Models / Report Index Expansion Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_state_read_models.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.8-B **14 passed**; `tests/aurel_shell` **949 passed**; ruff **PASS**; mypy **PASS** (321 source files).

P2.8-B is a contract-only Shell state read models / report index expansion pack only. It does NOT create live Shell state runtime, Shell runtime, session state engine, query runtime, filter runtime, sort runtime, persistent state store, database persistence, storage write, trace write, memory write, report generator runtime, docs generator runtime, report publisher, docs publisher, agent/REPORTS.md replacement, agent/ governance replacement, docs source-of-truth, product UI, product behavior, CLI runner, TUI runtime, command execution, runtime dispatch, permission enforcement, Custos decisioning, approval runtime, LIVE, TRACE_VERIFIED, release scope, or start P2.8-C, P2.8-D, P2.9, P2.10, or P2.13.

Report: `agent/reports/P2_8_B_SHELL_STATE_READ_MODELS_REPORT_INDEX.md`

## P2.8-A Shell State / Reports / Docs Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_state_foundation.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.8-A **14 passed**; `tests/aurel_shell` **935 passed**; ruff **PASS**; mypy **PASS** (320 source files).

P2.8-A is a contract-only Shell state / reports / docs foundation pack only. It does NOT create live Shell state runtime, Shell runtime, session state engine, persistent state store, database persistence, storage write, trace write, memory write, report generator runtime, docs generator runtime, report publisher, docs publisher, agent/REPORTS.md replacement, agent/ governance replacement, docs source-of-truth, product UI, product behavior, CLI runner, TUI runtime, command execution, runtime dispatch, permission enforcement, Custos decisioning, approval runtime, LIVE, TRACE_VERIFIED, release scope, or start P2.8-B, P2.9, P2.10, or P2.13.

## P2.7-D Shell / CLI / TUI Binding Section Seal Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_binding_section_seal.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.7-D **15 passed**; `tests/aurel_shell` **921 passed**; ruff **PASS**; mypy **PASS** (319 source files).

P2.7-D is a contract-only Shell / CLI / TUI binding section seal pack only. It does NOT create CLI app/runner/entrypoint, TUI runtime/app, Shell runtime/execution runtime/state runtime, command parser/router/handler, command execution/invocation, output writer runtime, render runtime, operator confirmation runtime, approval runtime, HITL activation, authorization, permission enforcement/grant/denial, Custos/Mneme integration, tool invocation, workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, shell state mutation, surface switching, navigation mutation, API server, HTTP routes, live endpoint, event bus, trace/memory/storage writes, source-of-truth store, product UI, product behavior, release scope, Shell complete, P2 complete, LIVE, TRACE_VERIFIED, or start P2.8, P2.10, or P2.13.

Report: `agent/reports/P2_7_D_SHELL_CLI_TUI_BINDING_SECTION_SEAL.md`

## P2.7-C Shell Binding Preview / Selection / Operator Confirmation Boundary Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_binding_preview_selection.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.7-C **14 passed**; `tests/aurel_shell` **906 passed**; ruff **PASS**; mypy **PASS** (318 source files).

P2.7-C is a contract-only binding preview / selection / confirmation-boundary pack only. It does NOT create UI, product UI, CLI app/runner/entrypoint, TUI runtime/app, Shell runtime/execution runtime, command parser/router/handler, command execution/invocation, output writer runtime, render runtime, operator confirmation runtime, approval runtime, HITL approval activation, authorization, permission enforcement/grant/denial, Custos/Mneme integration, tool invocation, workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, surface switching, navigation mutation, API server, HTTP routes, live endpoint, event bus, trace/memory/storage writes, source-of-truth store, product behavior, release scope, LIVE, TRACE_VERIFIED, or start P2.7-D, P2.8, P2.10, or P2.13.

## P2.7-B Shell Binding Read Models / Command Surface Adapter Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_binding_read_models.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.7-B **14 passed**; `tests/aurel_shell` **892 passed**; ruff **PASS**; mypy **PASS** (317 source files).

P2.7-B is a contract-only binding read-model / command surface adapter pack only. It does NOT create command parser/router/handler, command execution/invocation, CLI app/runner/entrypoint, TUI runtime/app, Shell runtime/execution runtime, output writer runtime, render runtime, product UI, operator confirmation runtime, approval runtime, authorization, permission enforcement, Custos/Mneme integration, tool invocation, workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, surface switching, navigation mutation, API server, HTTP routes, live endpoint, event bus, trace/memory/storage writes, source-of-truth store, product behavior, release scope, LIVE, TRACE_VERIFIED, or start P2.7-C, P2.8, P2.10, or P2.13.

## P2.7-A Shell / CLI / TUI Binding Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_binding_foundation.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.7-A **13 passed**; `tests/aurel_shell` **878 passed**; ruff **PASS**; mypy **PASS** (316 source files).

P2.7-A is a contract-only binding foundation only. It does NOT create CLI app, CLI runner, CLI entrypoint, TUI runtime, TUI app, Shell runtime, Shell execution runtime, command parser/router/handler, command execution, tool invocation, workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, surface switching, API server, HTTP routes, live endpoint, event bus, trace write, memory write, storage write, permission enforcement, product UI, product behavior, release scope, LIVE, TRACE_VERIFIED, or start P2.7-B, P2.8, P2.10, or P2.13.

Report: `agent/reports/P2_7_A_SHELL_CLI_TUI_BINDING_FOUNDATION.md`

## P2.6-D Surface Projection / API / Event Bridge Section Seal Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_surface_projection_section_seal.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.6-D **15 passed**; `tests/aurel_shell` **865 passed**; ruff **PASS**; mypy **PASS** (315 source files).

P2.6-D is a contract-only section seal only. It does NOT create API server, HTTP routes, route handlers, live endpoints, live query execution, event bus, event dispatcher, subscriber runtime, websocket/SSE, live stream, runtime event emission, runtime bridge, runtime dispatch, API event bridge runtime, trace write, memory write, storage write, CLI/Shell/TUI binding, product behavior, release scope, LIVE, TRACE_VERIFIED, or start P2.7, P2.10, or P2.13. The discarded Attention / Notification / Inbox direction for P2.6 was not used.

Report: `agent/reports/P2_6_D_SURFACE_PROJECTION_API_EVENT_SECTION_SEAL.md`

## P2.6-C Event Envelope / Bridge Boundary / No-Runtime-Dispatch Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_surface_projection_events.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.6-C **22 passed**; `tests/aurel_shell` **850 passed**; ruff **PASS**; mypy **PASS** (314 source files).

P2.6-C is a contract-only projection event-envelope / bridge-boundary expansion only. It does NOT create event bus, event dispatcher, event subscriber runtime, subscription runtime, delivery runtime, delivery channel, websocket/SSE runtime, live stream, runtime event emission, runtime bridge, runtime dispatch, API event bridge runtime, trace write, memory write, storage write, projection UI, API server, HTTP routes, route handlers, live endpoint, live query execution, surface switching, route/command execution, command router/handler, workflow/tool dispatch, CLI/Shell/TUI binding, approval activation, authorization, permission enforcement, Custos/Mneme integration, runtime mutation, source-of-truth store, claim production LIVE, claim TRACE_VERIFIED, claim release scope, claim product behavior, or start P2.6-D, P2.7, P2.10, or P2.13. The discarded Attention / Notification / Inbox direction for P2.6 was not used.

Report: `agent/reports/P2_6_C_SURFACE_PROJECTION_EVENT_BRIDGE_BOUNDARY.md`

## P2.6-B Surface Projection Read Models / API Schema Expansion Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_surface_projection_schemas.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.6-B **24 passed**; `tests/aurel_shell` **828 passed**; ruff **PASS**; mypy **PASS** (313 source files).

P2.6-B is a contract-only projection schema/read-model expansion only. It does NOT create projection UI, API server, HTTP routes, route handlers, live endpoints, live query execution, database/storage query runtime, websocket/SSE runtime, event bus, event dispatch, runtime bridge, runtime dispatch, surface switching, route/command execution, command router/handler, workflow/tool dispatch, CLI/Shell/TUI binding, approval activation, authorization, permission enforcement, Custos/Mneme integration, memory/storage/trace writes, runtime mutation, source-of-truth store, claim production LIVE, claim TRACE_VERIFIED, claim release scope, claim product behavior, or start P2.6-C, P2.7, P2.10, or P2.13. The discarded Attention / Notification / Inbox direction for P2.6 was not used.

Report: `agent/reports/P2_6_B_SURFACE_PROJECTION_SCHEMA_EXPANSION.md`

## P2.6-A Surface Projection / API / Event Bridge Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_surface_projection_foundation.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.6-A **40 passed**; `tests/aurel_shell` **804 passed**; ruff **PASS**; mypy **PASS** (312 source files).

P2.6-A is a contract-only surface projection / API / event bridge foundation only. It does NOT create projection UI, API server, HTTP routes, route handlers, websocket/SSE runtime, event bus, event dispatch, runtime bridge, runtime dispatch, surface switching, route/command execution, command router/handler, workflow/tool dispatch, CLI/Shell/TUI binding, approval activation, authorization, permission enforcement, Custos/Mneme integration, memory/storage/trace writes, runtime mutation, source-of-truth store, claim production LIVE, claim TRACE_VERIFIED, claim release scope, claim product behavior, or start P2.6-B, P2.7, P2.10, or P2.13. The discarded Attention / Notification / Inbox direction for P2.6 was not used.

Report: `agent/reports/P2_6_A_SURFACE_PROJECTION_API_EVENT_FOUNDATION.md`

## P2.5-D Handoff Section Seal Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_cross_surface_handoff_section_projection.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.5-D **16 passed**; `tests/aurel_shell` **764 passed**; ruff **PASS**; mypy **PASS** (311 source files).

P2.5-D is contract/read-model section projection, read-only contract render binding, readiness audit, contract-scope demo, and section seal only. It does NOT create projection UI, cross-surface UI, preview UI, explanation panel UI, confirmation modal, operator confirmation UI, live Shell/TUI binding, API/event bridge, handoff execution, surface switching, route execution, approval activation, permission enforcement, Custos/Mneme integration, memory/storage/trace writes, runtime mutation, source-of-truth store, claim production LIVE, claim TRACE_VERIFIED, claim release scope, claim product behavior, or start P2.6, P2.7, P2.10, or P2.13.

Report: `agent/reports/P2_5_D_HANDOFF_SECTION_SEAL.md`

## P2.5-C Handoff Preview / Confirmation Boundary Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_cross_surface_handoff_preview.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.5-C **18 passed**; `tests/aurel_shell` **748 passed**; ruff **PASS**; mypy **PASS** (310 source files).

P2.5-C is contract/read-model handoff preview and confirmation boundary only. It does NOT render preview UI, explanation panel UI, confirmation modal, operator confirmation UI, record real operator consent, create consent state, create or activate approvals, authorize actions, enforce permissions, integrate Custos, integrate Mneme, execute handoff, switch surfaces, execute routes, create route handlers/runtime, execute commands, create command router/handler, invoke tools, dispatch workflows, create API server, create HTTP routes, create event bus, emit runtime events, mutate runtime, write memory/storage/trace, create source-of-truth store, claim production LIVE, claim TRACE_VERIFIED, claim release scope, claim product behavior, or start P2.5-D, P2.6, P2.7, P2.10, or P2.13.

Report: `agent/reports/P2_5_C_HANDOFF_PREVIEW_CONFIRMATION_BOUNDARY.md`

## P2.5-B Handoff Context / Continuity / Conflict / Availability Read Model Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_cross_surface_handoff_context.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.5-B **18 passed**; `tests/aurel_shell` **730 passed**; ruff **PASS**; mypy **PASS** (309 source files).

P2.5-B is contract/read-model handoff context and availability only. It does NOT transfer context, persist context, write memory, write storage, write trace, resolve conflicts, block runtime, create operator confirmation, create or activate approvals, enforce permissions, integrate Custos, integrate Mneme, create cross-surface UI, preview UI, explanation panel UI, drag/drop, handoff animation, switch surfaces, execute routes, create route handlers/runtime, execute commands, create command router/handler, invoke tools, dispatch workflows, create API server, create HTTP routes, create event bus, emit runtime events, mutate runtime, create source-of-truth store, claim production LIVE, claim TRACE_VERIFIED, claim release scope, claim product behavior, or start P2.5-C, P2.6, P2.7, P2.10, or P2.13.

Report: `agent/reports/P2_5_B_HANDOFF_CONTEXT_AVAILABILITY_READ_MODEL.md`

## P2.4-C Command Proposal / No-Execution Boundary Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_global_command_proposal.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.4-C **20 passed**; `tests/aurel_shell` **612 passed**; ruff **PASS**; mypy **PASS** (306 source files).

P2.4-C is contract/read-model command proposal only. It does NOT add command palette UI, selection UI, preview panel UI, confirmation modal, frontend UI, browser UI, Tauri app, desktop app, keyboard shortcut handling, keyboard listener, hotkey handler, command execution, command router, command handlers, tool invocation, workflow dispatch, approval activation, permission enforcement, Custos integration, surface runtime switch, route execution, route handlers, route runtime, API server, HTTP routes, event bus, runtime event emission, local/browser storage, memory writes, trace writes, runtime mutation, source-of-truth store, production LIVE, TRACE_VERIFIED, release scope, product behavior, P2.4-D, P2.5, P2.6, P2.7, P2.10, or P2.13 work.

Report: `agent/reports/P2_4_C_COMMAND_PROPOSAL_NO_EXECUTION.md`

## P2.4-D Command Palette Integration Tail / Projection / Binding / Docs / Section Seal Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_global_command_section_projection.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.4-D **16 passed**; `tests/aurel_shell` **628 passed**; ruff **PASS**; mypy **PASS** (307 source files).

P2.4-D is contract/read-model section projection, explicit UNAVAILABLE binding, readiness audit, contract-scope demo, and section seal only. It does NOT add command palette UI, selection UI, preview panel UI, confirmation modal, frontend UI, browser UI, Tauri app, desktop app, keyboard shortcut handling, keyboard listener, hotkey handler, live search, command execution, command router, command handlers, command invocation, tool invocation, workflow dispatch, approval activation, permission enforcement, Custos integration, surface runtime switch, route execution, route handlers, route runtime, API server, HTTP routes, event bus, runtime event emission, local/browser storage, memory writes, trace writes, runtime mutation, source-of-truth store, production LIVE, TRACE_VERIFIED, release scope, product behavior, P2.5, P2.6, P2.7, P2.10, or P2.13 work.

Report: `agent/reports/P2_4_D_COMMAND_PALETTE_SECTION_SEAL.md`

## P2.4-B Command Discovery Read Model Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_global_command_discovery.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.4-B **23 passed**; `tests/aurel_shell` **592 passed**; ruff **PASS**; mypy **PASS**.

P2.4-B is contract/read-model command discovery only. It does NOT add command palette UI, search UI, live search box, keyboard shortcut handling, keyboard listener, hotkey handler, fuzzy search UI, ML ranking, recommendation engine, command execution, command router, command handlers, tool invocation, workflow dispatch, approval activation, permission enforcement, Custos integration, surface runtime switch, route execution, route handlers, route runtime, API server, HTTP routes, event bus, runtime event emission, local/browser storage, memory writes, trace writes, runtime mutation, source-of-truth store, production LIVE, TRACE_VERIFIED, release scope, product behavior, P2.4-C, P2.5, P2.6, P2.7, P2.10, or P2.13 work.

## P2.4-A Command Palette / Global Commands Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_global_command_registry.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.4-A **16 passed**; `tests/aurel_shell` **569 passed**; ruff **PASS**; mypy **PASS** (304 source files).

P2.4-A is contract/read-model command foundation only. It does NOT add command palette UI, frontend UI, browser UI, Tauri app, desktop app, keyboard shortcut handling, keyboard listener, hotkey handler, fuzzy search, ranking engine, command execution, command router, command handlers, tool invocation, workflow dispatch, approval activation, permission enforcement, Custos integration, surface runtime switch, route execution, route handlers, route runtime, API server, HTTP routes, event bus, runtime event emission, local/browser storage, memory writes, trace writes, runtime mutation, source-of-truth store, production LIVE, TRACE_VERIFIED, release scope, product behavior, P2.4-B, P2.5, P2.6, P2.7, P2.10, or P2.13 work.

Report: `agent/reports/P2_4_A_COMMAND_PALETTE_GLOBAL_COMMANDS_FOUNDATION.md`

## P2.3-D Workspace Window Section Projection / Binding / Seal Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_workspace_window_section_projection.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.3-D **14 passed**; `tests/aurel_shell` **553 passed**; ruff **PASS**; mypy **PASS** (303 source files).

P2.3-D is contract/read-model section projection, read-only binding, docs/state/report sync, readiness audit, and contract-scope exit seal only. It does NOT add product UI, browser UI, Tauri app, frontend components, frontend window movement, surface runtime switch, route runtime, route execution, route handlers, command palette, drag/drop, docking UI, undocking UI, CSS/frontend layout, layout engine, real collision detection, conflict resolver runtime, automatic conflict resolution, permission enforcement, permission grant/denial, runtime blocking, Custos integration, API server, HTTP routes, event bus, runtime event emission, local/browser storage, memory writes, trace writes, runtime mutation, source-of-truth store, production LIVE, TRACE_VERIFIED, release scope, P2.4, P2.10, or P2.13 work.

Report: `agent/reports/P2_3_D_WORKSPACE_WINDOW_SECTION_SEAL.md`

## P2.3-C Cross-Surface Window Handoff / Conflict / Docking Semantics Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_workspace_window_cross_surface.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.3-C **15 passed**; `tests/aurel_shell` **539 passed**; ruff **PASS**; mypy **PASS** (302 source files).

P2.3-C is contract/read-model cross-surface window semantics only. It does NOT add product UI, browser UI, Tauri app, frontend components, frontend window movement, surface runtime switch, route runtime, route execution, route handlers, drag/drop, docking UI, undocking UI, CSS/frontend layout, layout engine, real collision detection, conflict resolver runtime, automatic conflict resolution, permission enforcement, permission grant/denial, runtime blocking, Custos integration, API server, HTTP routes, event bus, runtime event emission, local/browser storage, memory writes, trace writes, runtime mutation, source-of-truth store, production LIVE, TRACE_VERIFIED, release scope, P2.3-D, P2.10, or P2.13 work.

Report: `agent/reports/P2_3_C_WORKSPACE_WINDOW_CROSS_SURFACE.md`

## P2.3-B Floating Window Focus / Stack / Grouping / Restore Semantics Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_workspace_window_semantics.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.3-B **15 passed**; `tests/aurel_shell` **524 passed**; ruff **PASS**; mypy **PASS** (301 files).

P2.3-B is contract/read-model focus/stack/group/restore semantics only. It does NOT add product UI, browser UI, Tauri app, frontend components, browser focus, frontend activation, focus manager runtime, z-index runtime, CSS/frontend layout, layout engine, draggable/resizable windows, window manager runtime, keyboard shortcuts, command palette, route runtime, route execution, API server, HTTP routes, event bus, runtime event emission, local/browser storage, memory writes, trace writes, runtime mutation, permission enforcement, Custos integration, desktop workspace UI, frontend group UI, tabs UI, source-of-truth store, production LIVE, TRACE_VERIFIED, release scope, P2.3-C, P2.10, or P2.13 work.

Report: `agent/reports/P2_3_B_WORKSPACE_WINDOW_SEMANTICS.md`

## P2.3-A Floating Windows / Workspace State Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_workspace_state_foundation.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.3-A **12 passed**; `tests/aurel_shell` **509 passed**; ruff **PASS**; mypy **PASS** (300 files).

P2.3-A is contract/read-model workspace state foundation only. It does NOT add product UI, browser/Tauri app, draggable windows, window manager, CSS/layout/z-index runtime, frontend routes, live CLI/TUI product, route runtime, API server, HTTP route, event bus, runtime event emission, permission enforcement, Custos integration, memory writes, trace writes, local/browser storage, old `Workspace` top-level surface activation, production LIVE, TRACE_VERIFIED, release scope, P2.3-B, P2.10, or P2.13 work.

Report: `agent/reports/P2_3_A_WORKSPACE_STATE_FOUNDATION.md`

## AUDIT-REPAIR-001 Test Portability Validation (COMPLETE)

```bash
grep -R "/home/hrvojeb/Desktop/GG" -n tests src agent  # no active test occurrences
.venv/bin/python -m pytest tests/path_governance/test_p1_7_16_policy_context_bridge.py \
  tests/path_governance/test_p1_7_17_projection_api_event_contract.py \
  tests/test_capability_claim_boundary.py -q
.venv/bin/python -m pytest -q --tb=line
```

Results: targeted path/capability **143 passed**; full suite **6151 passed, 3 skipped**; compileall **PASS**; ruff **PASS**; mypy **PASS** (297 files).

Portable cwd via `tests/repo_root.py` (`pyproject.toml` + `src/` discovery). No tests skipped/xfail/weakened. F-003–F-005 remain backlog.

Report: `agent/reports/AUDIT_REPAIR_001_TEST_PORTABILITY_P2_2_B_CANON_SYNC.md`

## P2.2-D Local Navigation Integration Tail / Section Seal Validation (COMPLETE)

```bash
.venv/bin/python -m pytest tests/aurel_shell/test_shell_local_navigation_integration_tail.py -q
```

Results: compileall **PASS**; focused P2.2-D **18 passed**; AurelShell **497 passed**; ruff **PASS**; mypy **PASS** (299 files).

P2.2-D is contract/read-model integration tail / section seal only. It does NOT add product UI, frontend sidebar, global left nav, frontend routes, clients, live CLI/TUI product, route runtime, route handler, click handlers, keyboard shortcuts, command palette, floating windows, API server, HTTP route, event bus, runtime event emission, permission enforcement, Custos integration, memory writes, trace writes, local/browser storage, production LIVE, TRACE_VERIFIED, release scope, or P2.3 implementation.

Report: `agent/reports/P2_2_D_LOCAL_NAVIGATION_INTEGRATION_TAIL.md`

## P2.2-C Local Navigation Context / Surface-Specific Profiles Validation (COMPLETE)

```bash
.venv/bin/python -m pytest tests/aurel_shell/test_shell_local_navigation_context.py -q
```

Results: compileall **PASS**; focused P2.2-C **19 passed**; AurelShell **479 passed**; ruff **PASS**; mypy **PASS** (298 files).

P2.2-C is contract/read-model context/profile/restoration/degraded/context projection only. It does NOT add product UI, frontend sidebar, global left nav, frontend routes, clients, live CLI/TUI product, route runtime, route handler, click handlers, keyboard shortcuts, command palette, floating windows, API server, HTTP route, event bus, runtime event emission, permission enforcement, Custos integration, memory writes, trace writes, local/browser storage, production LIVE, TRACE_VERIFIED, release scope, P2.2-D, or P2.3 work.

Report: `agent/reports/P2_2_C_LOCAL_NAVIGATION_CONTEXT.md`

## P2.2-B Local Navigation Hierarchy / Interaction Constraints Validation (COMPLETE)

```bash
.venv/bin/python -m pytest tests/aurel_shell/test_shell_local_navigation_hierarchy.py -q
```

Results: compileall **PASS**; focused P2.2-B **20 passed**; AurelShell **460 passed**; ruff **PASS**; mypy **PASS** (297 files).

P2.2-B is contract/read-model hierarchy/ordering/selection/interaction projection only. It does NOT add product UI, frontend sidebar, global left nav, frontend routes, clients, live CLI/TUI product, route runtime, route handler, click handlers, keyboard shortcuts, command palette, floating windows, API server, HTTP route, event bus, runtime event emission, permission enforcement, Custos integration, memory writes, trace writes, production LIVE, TRACE_VERIFIED, release scope, P2.2-C, or P2.3 work.

Report: `agent/reports/P2_2_B_LOCAL_NAVIGATION_HIERARCHY.md`

## P2.2-A Per-Surface Local Navigation Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m pytest tests/aurel_shell/test_shell_local_navigation_foundation.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
```

Results: compileall **PASS**; focused P2.2-A **24 passed**; AurelShell **440 passed**; ruff **PASS**; mypy **PASS** (296 files).

P2.2-A is contract/read-model local navigation foundation only. It does NOT add product UI, frontend sidebar, global left nav, frontend routes, clients, live CLI/TUI product, route runtime, route handler, click handlers, keyboard shortcuts, command palette, floating windows, API server, HTTP route, event bus, runtime event emission, permission enforcement, Custos integration, memory writes, trace writes, production LIVE, TRACE_VERIFIED, release scope, P2.2-B, or P2.3 work.

## P2.1-D Topbar Integration Tail / Projection / Binding / Docs / Section Handoff Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_topbar_integration_tail.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.1-D **21 passed**; AurelShell **416 passed**; ruff **PASS**; mypy **PASS** (295 files).

P2.1-D is contract/read-model section closure only. It does NOT add product UI, frontend topbar, clients, live CLI/TUI product, route runtime, route handler, local navigation, command palette, API server, HTTP route, event bus, runtime event emission, permission enforcement, Custos integration, memory writes, trace writes, production LIVE, TRACE_VERIFIED, release scope, P2.2-A, or P2.2 work.

## P2.1-C Topbar Route Visibility / Interaction Constraints / Registry Refinement Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_topbar_route_visibility.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.1-C **52 passed**; AurelShell **395 passed**; ruff **PASS**; mypy **PASS** (294 files).

P2.1-C is contract/read-model route visibility and interaction constraint projection only. It does NOT add product UI, frontend topbar, clients, live CLI/TUI, route runtime, route handler, local navigation, command palette, floating workspace state, notification engine, approval queue, runtime event stream, permission enforcement, Custos integration, memory writes, trace writes, P2.1-D, or P2.2 work.

## P2.1-B Topbar Status Slots / Availability / Operator Context Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_topbar_status_slots.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.1-B **37 passed**; AurelShell **343 passed**; ruff **PASS**; mypy **PASS** (293 files).

P2.1-B is contract/read-model status projection only. It does NOT add product UI, frontend topbar, clients, live CLI/TUI, route runtime, local navigation, command palette, notification engine, approval queue, runtime event stream, auth/session backend, permission enforcement, Custos integration, memory writes, trace writes, P2.1-C, or P2.2 work.

## P2.1-A Global Topbar / Surface Registry Foundation Validation (COMPLETE)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_topbar_surface_registry.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P2.1-A **75 passed**; AurelShell **306 passed**; ruff **PASS**; mypy **PASS** (292 files).

P2.1-A is contract/read-model/topbar-registry only. It does NOT add product UI, frontend topbar, clients, live CLI/TUI, route runtime, local navigation, permission enforcement, Custos integration, memory writes, trace writes, or P2.1-B+ work.

## P2.0-F Projection / API / CLI / Docs / Exit Seal Validation (COMPLETE)

Focused validation (2026-06-29):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_shell_projection_cli_exit_seal.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Report: `agent/reports/P2_0_F_PROJECTION_CLI_EXIT_SEAL.md`

Results: compileall **PASS**; focused P2.0-F **43 passed**; AurelShell **231 passed**; ruff **PASS**; mypy **PASS** (291 files).

P2.0-F is contract/projection/read-model/exit-seal only. It does NOT add product UI, API server, HTTP routes, event bus, runtime event emission, live CLI/TUI product, route runtime, memory writes, trace writes, trace verification, runtime mutation, or P2.1 work. `P2_CONTRACT_SCOPE` seals separately from `PRODUCTION_LIVE_SCOPE`, `TRACE_VERIFIED_SCOPE`, and `RELEASE_SCOPE`. `READY_FOR_P2_1_REVIEW` is review-only.

## P2.0-E Operator Demo + Snapshot + Regression Validation (COMPLETE)

Focused validation (2026-06-29):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/aurel_shell/test_operator_demo_snapshot_regression.py -q
.venv/bin/python -m pytest tests/aurel_shell -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Report: `agent/reports/P2_0_E_OPERATOR_DEMO_SNAPSHOT_REGRESSION.md`

Results: compileall **PASS**; focused P2.0-E **33 passed**; AurelShell **188 passed**; ruff **PASS**; mypy **PASS** (286 files).

P2.0-E is contract/read-model/regression-harness only. It does NOT add product UI, web/desktop/mobile clients, CLI/TUI, route runtime, browser tests, live shell, source-of-truth store, permission enforcement, Custos integration, memory writes, trace writes, P2.0-F implementation, or P2.1 authorization.

## P1.7.20 Exit Seal + Live Integration Demo Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py tests/path_governance/test_p1_7_15_path_governance_test_harness.py tests/path_governance/test_p1_7_16_policy_context_bridge.py tests/path_governance/test_p1_7_17_projection_api_event_contract.py tests/path_governance/test_p1_7_18_path_governance_cli_tui_binding.py tests/path_governance/test_p1_7_20_exit_seal_live_integration_demo.py -q
.venv/bin/python -m pytest tests/path_governance/test_p1_7_19_docs_state_reports_sync.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Report: `agent/reports/P1.7.20_EXIT_SEAL_LIVE_INTEGRATION_DEMO.md`

Results: compileall **PASS**; focused P1.7.0–P1.7.20 **679 passed** (35 P1.7.20 focused); P1.7.19 docs sync **8 passed**; ruff **PASS**; mypy **PASS** (229 files).

Operator manual seal command (in-process demo):

```bash
.venv/bin/python -c "from agentic_runtime.path_governance import run_path_governance_exit_seal, render_path_governance_exit_seal_summary as s; r=run_path_governance_exit_seal(); print(s(r))"
```

Operator manual seal commands (optional, not run for P1.7.20):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

P1.7.20 seals Path Governance as evidence-only vertical slice; it does NOT add runtime enforcement, policy decisions, Ledger writes, global trace writes, source mutation, Shell UI, HTTP server, or sandbox changes.

## P1.7.19 Docs / State / Reports Update Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py tests/path_governance/test_p1_7_15_path_governance_test_harness.py tests/path_governance/test_p1_7_16_policy_context_bridge.py tests/path_governance/test_p1_7_17_projection_api_event_contract.py tests/path_governance/test_p1_7_18_path_governance_cli_tui_binding.py -q
.venv/bin/python -m pytest tests/path_governance/test_p1_7_19_docs_state_reports_sync.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Report: `agent/reports/P1.7.19_DOCS_STATE_REPORTS_UPDATE.md`

Results: compileall **PASS**; focused P1.7.0–P1.7.18 **636 passed**; P1.7.19 docs sync **8 passed**; total **644 passed**; ruff **PASS**; mypy **PASS** (228 files).

Operator manual seal commands (optional, not run for P1.7.19 docs-only task):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

P1.7.19 synchronizes Path Governance documentation, state, reports, and test index for the Integration-First roadmap; it does NOT add runtime behavior, policy enforcement, Ledger writes, global trace writes, source mutation, Shell UI, HTTP server, or sandbox changes.

## P1.7.18 Path Governance CLI/TUI Binding Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py tests/path_governance/test_p1_7_15_path_governance_test_harness.py tests/path_governance/test_p1_7_16_policy_context_bridge.py tests/path_governance/test_p1_7_17_projection_api_event_contract.py tests/path_governance/test_p1_7_18_path_governance_cli_tui_binding.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0–P1.7.18 **636 passed** (45 P1.7.18 focused); ruff **PASS**; mypy **PASS** (228 files).

Operator manual seal commands (optional, not run for P1.7.18):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.17 Path Governance Projection/API/Event Contract Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py tests/path_governance/test_p1_7_15_path_governance_test_harness.py tests/path_governance/test_p1_7_16_policy_context_bridge.py tests/path_governance/test_p1_7_17_projection_api_event_contract.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Report: `agent/reports/P1.7.17_PATH_GOVERNANCE_PROJECTION_API_EVENT_CONTRACT.md`

Results: compileall **PASS**; focused P1.7.0–P1.7.17 **591 passed** (38 P1.7.17 focused); ruff **PASS**; mypy **PASS**.

Operator manual seal commands (optional, not run for P1.7.17):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.16 Policy Context Bridge Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py tests/path_governance/test_p1_7_15_path_governance_test_harness.py tests/path_governance/test_p1_7_16_policy_context_bridge.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 + P1.7.9 + P1.7.10 + P1.7.11 + P1.7.12 + P1.7.13 + P1.7.14 + P1.7.15 + P1.7.16 **553 passed** (54 P1.7.16 focused); ruff **PASS**; mypy **PASS**.

Report: `agent/reports/P1.7.16_POLICY_CONTEXT_BRIDGE.md`

Operator manual seal commands (optional, not run for P1.7.16):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.15 Path Governance Test Harness Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py tests/path_governance/test_p1_7_15_path_governance_test_harness.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 + P1.7.9 + P1.7.10 + P1.7.11 + P1.7.12 + P1.7.13 + P1.7.14 + P1.7.15 **499 passed** (42 P1.7.15 focused); ruff **PASS**; mypy **PASS** (224 files).

Report: `agent/reports/P1.7.15_PATH_GOVERNANCE_TEST_HARNESS.md`

Operator manual seal commands (optional, not run for P1.7.15):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.14 Path Violation / Drift Trace Hook Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 + P1.7.9 + P1.7.10 + P1.7.11 + P1.7.12 + P1.7.13 + P1.7.14 **457 passed** (45 P1.7.14 focused); ruff **PASS**; mypy **PASS** (223 files).

Report: `agent/reports/P1.7.14_PATH_VIOLATION_DRIFT_TRACE_HOOK.md`

Operator manual seal commands (optional, not run for P1.7.14):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.13 Path Resolution Trace Hook Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 + P1.7.9 + P1.7.10 + P1.7.11 + P1.7.12 + P1.7.13 **412 passed** (41 P1.7.13 focused); ruff **PASS**; mypy **PASS** (222 files).

Report: `agent/reports/P1.7.13_PATH_RESOLUTION_TRACE_HOOK.md`

Operator manual seal commands (optional, not run for P1.7.13):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.12 Path/Source Conflict & Precedence Rules Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py tests/path_governance/test_p1_7_12_conflict_precedence.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 + P1.7.9 + P1.7.10 + P1.7.11 + P1.7.12 **371 passed** (36 P1.7.12 focused); ruff **PASS**; mypy **PASS** (221 files).

Report: `agent/reports/P1.7.12_PATH_SOURCE_CONFLICT_PRECEDENCE_RULES.md`

Operator manual seal commands (optional, not run for P1.7.12):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.11 Source Trust Resolver v0 / Shadow Mode Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 + P1.7.9 + P1.7.10 + P1.7.11 **335 passed** (40 P1.7.11 focused); ruff **PASS**; mypy **PASS** (220 files).

Report: `agent/reports/P1.7.11_SOURCE_TRUST_RESOLVER_SHADOW_MODE.md`

Operator manual seal commands (optional, not run for P1.7.11):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

Full pytest/coverage/Bandit remain manual unless runtime/security/sandbox/network/subprocess/secrets paths are touched or the operator requests full validation. P1.7.11 touched backend shadow trust resolver schema/helper, focused tests, and docs only; it did not touch runtime/security/sandbox/network/subprocess/secrets paths.

## P1.7.10 Path Governance Resolver v0 / Shadow Mode Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 + P1.7.9 + P1.7.10 **295 passed** (35 P1.7.10 focused); ruff **PASS**; mypy **PASS** (219 files).

Report: `agent/reports/P1.7.10_PATH_GOVERNANCE_RESOLVER_SHADOW_MODE.md`

Operator manual seal commands (optional, not run for P1.7.10):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

Full pytest/coverage/Bandit remain manual unless runtime/security/sandbox/network/subprocess/secrets paths are touched or the operator requests full validation. P1.7.10 touched backend shadow resolver schema/helper, focused tests, and docs only; it did not touch runtime/security/sandbox/network/subprocess/secrets paths.

## P1.7.9 Path/Source Risk Classification Model Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py tests/path_governance/test_p1_7_9_path_source_risk_classification.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 + P1.7.9 **260 passed** (41 P1.7.9 focused); ruff **PASS**; mypy **PASS** (218 files).

Report: `agent/reports/P1.7.9_PATH_SOURCE_RISK_CLASSIFICATION_MODEL.md`

Operator manual seal commands (optional, not run for P1.7.9):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.8 Source Provenance & Evidence Binding Seed Validation (COMPLETE)

Focused validation (2026-06-26):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 + P1.7.8 **219 passed** (33 P1.7.8 focused); ruff **PASS**; mypy **PASS** (217 files).

Report: `agent/reports/P1.7.8_SOURCE_PROVENANCE_EVIDENCE_BINDING_SEED.md`

Operator manual seal commands (optional, not run for P1.7.8):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.7 Untrusted Content Boundary Model Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py tests/path_governance/test_p1_7_7_untrusted_content_boundary.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 + P1.7.7 **186 passed** (33 P1.7.7 focused); ruff **PASS**; mypy **PASS** (216 files).

Report: `agent/reports/P1.7.7_UNTRUSTED_CONTENT_BOUNDARY_MODEL.md`

Operator manual seal commands (optional, not run for P1.7.7):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.6 Path Authority Scope Model Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py tests/path_governance/test_p1_7_6_path_authority_scope.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 + P1.7.6 **153 passed** (29 P1.7.6 focused); ruff **PASS**; mypy **PASS** (215 files).

Report: `agent/reports/P1.7.6_PATH_AUTHORITY_SCOPE_MODEL.md`

Operator manual seal commands (optional, not run for P1.7.6):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.7.5 Path Normalization & Escape Detection Contract Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 + P1.7.5 **124 passed** (30 P1.7.5 focused); ruff **PASS**; mypy **PASS** (214 files).

Report: `agent/reports/P1.7.5_PATH_NORMALIZATION_ESCAPE_DETECTION_CONTRACT.md`

Operator manual seal commands (optional, not run for P1.7.5):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
```

## P1.7.4 Trusted Root & Scope Registry Seed Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py tests/path_governance/test_p1_7_4_trusted_roots.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 + P1.7.4 **94 passed**; ruff **PASS**; mypy **PASS** (212 files).

Report: `agent/reports/P1.7.4_TRUSTED_ROOT_SCOPE_REGISTRY_SEED.md`

Operator manual seal commands (optional, not run for P1.7.4):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

Full pytest/coverage/Bandit remain manual unless runtime/security/sandbox/network/subprocess/secrets paths are touched or the operator requests full validation. P1.7.4 touched registry schema/test/docs only.

## P1.7.3 Source Trust Label Taxonomy Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py tests/path_governance/test_p1_7_3_source_trust_taxonomy.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 + P1.7.3 **70 passed**; ruff **PASS**; mypy **PASS** (211 files).

Report: `agent/reports/P1.7.3_SOURCE_TRUST_LABEL_TAXONOMY.md`

Operator manual seal commands (optional, not run for P1.7.3):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

Full pytest/coverage/Bandit remain manual unless runtime/security/sandbox/network/subprocess/secrets paths are touched or the operator requests full validation. P1.7.3 touched taxonomy schema/test/docs only.

## P1.7.2 Source Identity & SourceRef Schema Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py tests/path_governance/test_p1_7_2_source_identity.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 + P1.7.2 **46 passed**; ruff **PASS**; mypy **PASS** (210 files).

Report: `agent/reports/P1.7.2_SOURCE_IDENTITY_SOURCE_REF_SCHEMA.md`

Operator manual seal commands (optional, not run for P1.7.2):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

Full pytest/coverage/Bandit remain manual unless runtime/security/sandbox/network/subprocess/secrets paths are touched or the operator requests full validation. P1.7.2 touched schema/test/docs only.

## P1.7.1 Path Identity & Canonical Path Schema Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py tests/path_governance/test_p1_7_1_path_identity.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 + P1.7.1 **25 passed**; ruff **PASS**; mypy **PASS** (209 files).

Report: `agent/reports/P1.7.1_PATH_IDENTITY_CANONICAL_PATH_SCHEMA.md`

Operator manual seal commands (optional, not run for P1.7.1):

```bash
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

Full pytest/coverage/Bandit remain manual unless runtime/security/sandbox/network/subprocess/secrets paths are touched or the operator requests full validation. P1.7.1 touched schema/test/docs only.

## P1.7.0 Path Governance Foundation Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/path_governance/test_p1_7_0_foundation.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.7.0 **11 passed**; ruff **PASS**; mypy **PASS** (207 files).

Report: `agent/reports/P1.7.0_PATH_GOVERNANCE_SOURCE_TRUST_FOUNDATION.md`

Programmatic foundation status:

```bash
.venv/bin/python -c "
from agentic_runtime.path_governance import get_path_governance_foundation_status, stable_hash
s = get_path_governance_foundation_status()
print(s.task_id, s.posture.value, stable_hash(s))
"
```

## P1.6.20 Exit Seal Validation (COMPLETE)

Focused validation (2026-06-25):

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest \
  tests/test_policy_exit_seal_p1620.py \
  tests/test_policy_exit_seal_projection_p1620.py \
  tests/test_policy_exit_seal_cli_p1620.py -q
.venv/bin/python -m pytest \
  tests/test_policy_exit_seal_p1620.py \
  tests/test_policy_exit_seal_projection_p1620.py \
  tests/test_policy_exit_seal_cli_p1620.py \
  tests/test_policy_cli_binding_p1618.py \
  tests/test_policy_cli_projection_p1618.py \
  tests/test_policy_cli_harness_p1618.py \
  tests/test_policy_projection_contract_p1617.py \
  tests/test_policy_projection_sources_p1617.py \
  tests/test_policy_projection_integration_p1617.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

Results: compileall **PASS**; focused P1.6.20 **42 passed**; P1.6.17/18 regression **137 passed**; ruff **PASS**; mypy **PASS** (200 files).

Exit seal verdict: **PASS_WITH_WARNINGS**. Report: `agent/reports/P1.6.20_POLICY_EXIT_SEAL_LIVE_INTEGRATION_DEMO.md`

Programmatic seal:

```bash
.venv/bin/python -c "
from agentic_runtime.policy_cards import build_policy_exit_seal_report, policy_exit_seal_report_hash
r = build_policy_exit_seal_report()
print(r.verdict.value, policy_exit_seal_report_hash(r))
"
```

Operator manual seal (optional): full pytest, coverage ≥75%, Bandit `-ll`.

## P1.6.20 Exit Seal Validation Expectations (superseded by COMPLETE section above)

Live CLI verification (from P1.6.19 runbook):

```bash
.venv/bin/python -m agentic_runtime.cli policy status
.venv/bin/python -m agentic_runtime.cli policy projection --json
.venv/bin/python -m agentic_runtime.cli policy unavailable
.venv/bin/python -m agentic_runtime.cli policy harness list
.venv/bin/python -m agentic_runtime.cli policy harness run
```

## P1.6.19 Verification (Policy Docs/State/Reports Update)

Docs-only task — no Python source changes expected.

```bash
git status --short
```

Optional sanity check:

```bash
.venv/bin/python -m compileall src tests
```

P1.6.19 synchronizes the policy subsystem documentation, state, reports, and operator runbook for the Integration-First roadmap; it does NOT add policy enforcement, write to the Ledger, activate approvals, block commands, or change runtime sandbox behavior.

## P1.6.18 Verification (Policy CLI/TUI Binding)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_cli_binding_p1618.py tests/test_policy_cli_projection_p1618.py tests/test_policy_cli_harness_p1618.py -q
.venv/bin/python -m pytest tests/test_policy_cli_binding_p1618.py tests/test_policy_cli_projection_p1618.py tests/test_policy_cli_harness_p1618.py tests/test_policy_projection_contract_p1617.py tests/test_policy_projection_sources_p1617.py tests/test_policy_projection_integration_p1617.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

P1.6.18 binds the P1.6 policy projection contract to a minimal operator-facing CLI/TUI surface; it does NOT enforce policy decisions, write to the Ledger, activate approvals, block commands, or change runtime sandbox behavior.

## P1.6.12 Verification (Custos Shadow Runtime Projection & Submit Observability Hook)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_runtime_projection_p1612.py tests/test_runtime_custos_shadow_submit_p1612.py -q
.venv/bin/python -m pytest tests/test_policy_runtime_projection_p1612.py tests/test_runtime_custos_shadow_submit_p1612.py tests/test_policy_registry_binding_p1611.py tests/test_policy_resolver_p1610.py tests/test_snapshot_security_p1610h.py -q
.venv/bin/python -m pytest tests/test_policy_runtime_projection_p1612.py tests/test_runtime_custos_shadow_submit_p1612.py tests/test_policy_registry_binding_p1611.py tests/test_policy_resolver_p1610.py tests/test_sandbox_policy_cards_p169.py tests/test_prompt_policy_cards_p168.py tests/test_memory_write_policy_cards_p167.py tests/test_tool_permission_policy_cards_p166.py tests/test_data_residency_policy_cards_p165.py tests/test_human_oversight_policy_cards_p164.py tests/test_risk_tier_policy_cards_p163.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

P1.6.12 local results: compileall **PASS**; focused P1.6.12 suite **26 passed in 0.71s**; P1.6.10/P1.6.11/security regression **111 passed, 1 skipped in 0.84s**; P1.6 policy-card family regression **497 passed in 1.64s**; ruff **PASS**; mypy **PASS** (`Success: no issues found in 192 source files`); full pytest **3405 passed, 3 skipped in 260.24s**; coverage **3405 passed, 3 skipped in 283.29s**, total coverage **79.56%**, fail-under 75 passed; Bandit **FAILS on known deferred B310/B108 findings** in `http_utils.py`, `sandbox.py`, `tools.py`, and `verifier.py` (no new P1.6.12 finding).

## P1.6.13 Verification (Policy Conflict Algebra & Strictest-Wins Rules)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_conflict_algebra_p1613.py tests/test_policy_resolver_conflict_algebra_p1613.py -q
.venv/bin/python -m pytest tests/test_policy_conflict_algebra_p1613.py tests/test_policy_resolver_conflict_algebra_p1613.py tests/test_policy_runtime_projection_p1612.py tests/test_policy_registry_binding_p1611.py tests/test_policy_resolver_p1610.py tests/test_snapshot_security_p1610h.py -q
.venv/bin/python -m pytest tests/test_policy_conflict_algebra_p1613.py tests/test_policy_resolver_conflict_algebra_p1613.py tests/test_policy_runtime_projection_p1612.py tests/test_runtime_custos_shadow_submit_p1612.py tests/test_policy_registry_binding_p1611.py tests/test_policy_resolver_p1610.py tests/test_sandbox_policy_cards_p169.py tests/test_prompt_policy_cards_p168.py tests/test_memory_write_policy_cards_p167.py tests/test_tool_permission_policy_cards_p166.py tests/test_data_residency_policy_cards_p165.py tests/test_human_oversight_policy_cards_p164.py tests/test_risk_tier_policy_cards_p163.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

## P1.6.17 Verification (Policy Projection/API/Event Contract)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_projection_contract_p1617.py tests/test_policy_projection_sources_p1617.py tests/test_policy_projection_integration_p1617.py -q
.venv/bin/python -m pytest tests/test_policy_projection_contract_p1617.py tests/test_policy_projection_sources_p1617.py tests/test_policy_projection_integration_p1617.py tests/test_policy_test_harness_p1616.py tests/test_policy_test_harness_integration_p1616.py tests/test_policy_test_harness_determinism_p1616.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

P1.6.17 introduces the versioned policy projection/API/event contract required by the Integration-First roadmap; CLI binding was added in P1.6.18. P1.6.17 does NOT enforce policy decisions, write to the Ledger, activate approvals, block commands, or change runtime sandbox behavior.

## P1.6.16 Verification (Policy Test Harness)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_test_harness_p1616.py tests/test_policy_test_harness_integration_p1616.py tests/test_policy_test_harness_determinism_p1616.py -q
.venv/bin/python -m pytest tests/test_policy_test_harness_p1616.py tests/test_policy_test_harness_integration_p1616.py tests/test_policy_test_harness_determinism_p1616.py tests/test_policy_violation_trace_p1615.py tests/test_policy_runtime_projection_violation_trace_p1615.py tests/test_policy_resolution_violation_binding_p1615.py -q
.venv/bin/python -m pytest tests/test_policy_test_harness_p1616.py tests/test_policy_test_harness_integration_p1616.py tests/test_policy_test_harness_determinism_p1616.py tests/test_policy_violation_trace_p1615.py tests/test_policy_runtime_projection_violation_trace_p1615.py tests/test_policy_resolution_violation_binding_p1615.py tests/test_policy_resolution_trace_p1614.py tests/test_policy_resolver_trace_hook_p1614.py tests/test_policy_runtime_projection_trace_p1614.py tests/test_policy_conflict_algebra_p1613.py tests/test_policy_resolver_conflict_algebra_p1613.py tests/test_policy_runtime_projection_p1612.py tests/test_runtime_custos_shadow_submit_p1612.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
```

P1.6.16 introduces a deterministic policy test harness for shadow governance validation; it does NOT enforce policy decisions, write to the Ledger, activate approvals, block commands, or change runtime sandbox behavior.

## P1.6.15 Verification (Policy Violation Trace Hook)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_violation_trace_p1615.py tests/test_policy_runtime_projection_violation_trace_p1615.py tests/test_policy_resolution_violation_binding_p1615.py -q
.venv/bin/python -m pytest tests/test_policy_violation_trace_p1615.py tests/test_policy_runtime_projection_violation_trace_p1615.py tests/test_policy_resolution_violation_binding_p1615.py tests/test_policy_resolution_trace_p1614.py tests/test_policy_resolver_trace_hook_p1614.py tests/test_policy_runtime_projection_trace_p1614.py tests/test_policy_conflict_algebra_p1613.py tests/test_policy_resolver_conflict_algebra_p1613.py tests/test_policy_runtime_projection_p1612.py tests/test_runtime_custos_shadow_submit_p1612.py tests/test_policy_registry_binding_p1611.py tests/test_policy_resolver_p1610.py tests/test_snapshot_security_p1610h.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

P1.6.15 records shadow policy violation evidence; it does NOT enforce policy decisions, write to the Ledger, activate approvals, block commands, or change runtime sandbox behavior.

## P1.6.14 Verification (Policy Resolution Trace Hook)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_resolution_trace_p1614.py tests/test_policy_resolver_trace_hook_p1614.py tests/test_policy_runtime_projection_trace_p1614.py -q
.venv/bin/python -m pytest tests/test_policy_resolution_trace_p1614.py tests/test_policy_resolver_trace_hook_p1614.py tests/test_policy_runtime_projection_trace_p1614.py tests/test_policy_conflict_algebra_p1613.py tests/test_policy_resolver_conflict_algebra_p1613.py tests/test_policy_runtime_projection_p1612.py tests/test_runtime_custos_shadow_submit_p1612.py tests/test_policy_registry_binding_p1611.py tests/test_policy_resolver_p1610.py tests/test_snapshot_security_p1610h.py -q
.venv/bin/python -m pytest tests/test_policy_resolution_trace_p1614.py tests/test_policy_resolver_trace_hook_p1614.py tests/test_policy_runtime_projection_trace_p1614.py tests/test_policy_conflict_algebra_p1613.py tests/test_policy_resolver_conflict_algebra_p1613.py tests/test_policy_runtime_projection_p1612.py tests/test_runtime_custos_shadow_submit_p1612.py tests/test_policy_registry_binding_p1611.py tests/test_policy_resolver_p1610.py tests/test_sandbox_policy_cards_p169.py tests/test_prompt_policy_cards_p168.py tests/test_memory_write_policy_cards_p167.py tests/test_tool_permission_policy_cards_p166.py tests/test_data_residency_policy_cards_p165.py tests/test_human_oversight_policy_cards_p164.py tests/test_risk_tier_policy_cards_p163.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
.venv/bin/python -m bandit -r src/agentic_runtime -ll
```

P1.6.14 creates trace-compatible policy resolution evidence; it does NOT write to the Ledger, enforce policy decisions, activate approvals, block commands, or change runtime sandbox behavior.

P1.6.13 is shadow-only. No enforcement, no command blocking, no approval activation, no runtime sandbox changes.

P1.6.12 is observability-only. P0 runtime remains authoritative, and Custos shadow decisions are not enforcement decisions.

## P1.6.11 Verification (Policy Resolution Context & Registry Binding)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_registry_binding_p1611.py -q
.venv/bin/python -m pytest tests/test_policy_registry_binding_p1611.py tests/test_policy_resolver_p1610.py tests/test_sandbox_policy_cards_p169.py tests/test_prompt_policy_cards_p168.py tests/test_memory_write_policy_cards_p167.py tests/test_tool_permission_policy_cards_p166.py tests/test_data_residency_policy_cards_p165.py tests/test_human_oversight_policy_cards_p164.py tests/test_risk_tier_policy_cards_p163.py -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75
```

P1.6.11 focused coverage (`tests/test_policy_registry_binding_p1611.py`) covers registry construction, duplicate handling, family/scope lookup, deterministic applicability filtering, context binding, risk mapping, registry-to-resolver integration, shadow-only/non-enforcement guarantees, and public exports.

P1.6.11 local results: compileall **PASS**; focused P1.6.11 suite **22 passed in 0.21s**; P1.6.9/P1.6.10/P1.6.11 focused regression **471 passed in 0.93s**; ruff **PASS**; mypy **PASS** (`Success: no issues found in 191 source files`); full pytest **3379 passed, 3 skipped in 204.21s**; coverage **3379 passed, 3 skipped in 226.66s**, total coverage **79.40%**, fail-under 75 passed.

## P1.6.10 Verification (Custos v0 Policy Runtime Resolver — Shadow Mode)

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_policy_resolver_p1610.py -q
# resolver + all policy-card families
.venv/bin/python -m pytest tests/test_policy_resolver_p1610.py tests/test_sandbox_policy_cards_p169.py tests/test_prompt_policy_cards_p168.py tests/test_memory_write_policy_cards_p167.py tests/test_tool_permission_policy_cards_p166.py tests/test_data_residency_policy_cards_p165.py tests/test_human_oversight_policy_cards_p164.py tests/test_risk_tier_policy_cards_p163.py -q
.venv/bin/ruff check src/agentic_runtime/policy_cards/resolver.py src/agentic_runtime/policy_cards/resolution_context.py src/agentic_runtime/policy_cards/resolution_result.py tests/test_policy_resolver_p1610.py
```

P1.6.10 local results: compileall **PASS (exit 0)**; resolver focused suite
**51 passed**; resolver + P1.6.3–P1.6.9 policy-card suites **449 passed**; ruff on new
files **PASS**.

`tests/test_policy_resolver_p1610.py` (51 tests) covers nine blocks: (1) context
construction / canonical serialization / hash determinism / closed-world `from_dict`;
(2) no-card and no-applicable-card conservative behavior (never silent allow); (3) the
seven single-family adapters; (4) strictest-wins aggregation + deterministic ordering +
same-input-same-hash; (5) shadow mode (`enforcement_mode == SHADOW`, `WOULD_*` actions,
ENFORCE/SIMULATE fail-closed, resolver usable independently of the runtime);
(6) `ResolvedPolicySet` canonical serialization + hash + source ids/hashes + context
hash; (7) cross-family resolution and aggregation of violations/approvals/card-ids;
(8) public exports + error hierarchy + no circular import; (9) non-enforcement
guarantees (no enforcement surface; resolver does not import or call the runtime;
side-effect free).

Honesty note: full `pytest -q`, `--cov`, and `mypy src/agentic_runtime` were **not
re-run to completion in this session** (mypy was interrupted). The resolver is additive
(new modules + additive exports/errors); confirm the full suite, coverage ≥ 75%, and
`mypy src/agentic_runtime` before commit.

## P1.6.8S Verification

Last verified against commit: 3f65647f356eccac8b057592f894c9294bd01f5c

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/test_prompt_policy_cards_p168.py -q --tb=line
.venv/bin/python -m pytest tests/test_policy_cards_p160.py tests/test_policy_cards_schema_p161.py tests/test_behavioral_contract_schema_p162.py tests/test_risk_tier_policy_cards_p163.py tests/test_human_oversight_policy_cards_p164.py tests/test_data_residency_policy_cards_p165.py tests/test_tool_permission_policy_cards_p166.py tests/test_memory_write_policy_cards_p167.py tests/test_prompt_policy_cards_p168.py -q --tb=line
.venv/bin/python -m pytest tests/test_autonomy_scale_engine.py tests/test_measured_autonomy_score.py -q --tb=line
.venv/bin/ruff check src tests
.venv/bin/mypy src/agentic_runtime
.venv/bin/python -m pytest -q --tb=line
.venv/bin/python -m pytest --cov=src/agentic_runtime --cov-report=term-missing -q --tb=no
```

P1.6.8S local results: compileall **PASS**; P1.6.8 focused suite **74 passed**; P1.6.0-P1.6.8 focused policy-card suite **540 passed**; autonomy CLI subprocess suite **85 passed**; ruff **PASS**; mypy **PASS**; full pytest **3220 passed, 2 skipped**; coverage command **3220 passed, 2 skipped**, total coverage **79.27%**.

Bare `python3 -m agentic_runtime.cli` subprocess calls were removed from autonomy/measured-autonomy tests and centralized through `tests/cli_helpers.py`. Remaining `python3` uses in tests are sandbox/repo-agent payload commands, not CLI module subprocess imports.

## Optional Security Tooling

The dev extra seeds optional security tools only; these are not hard CI gates in P1.6.8S.

```bash
bandit -r src/agentic_runtime
pip-audit
```

## Verifying P1.6.0 + P1.6.1 + P1.6.2 + P1.6.3 Policy Cards & Behavioral Contracts

P1.6.0 establishes first-class policy card foundation objects. P1.6.1 adds centralized Policy Card Schema v1. P1.6.2 adds Behavioral Contract Schema v1 with 24 enums, 15 frozen dataclasses, and deterministic hashing. P1.6.3 adds Risk Tier Policy Card Model v1 with R0-R6 definitions, R5/R6 safety validation, action-class mapping seeds, and deterministic hashing.

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_policy_cards_p160.py tests/test_policy_cards_schema_p161.py tests/test_behavioral_contract_schema_p162.py tests/test_risk_tier_policy_cards_p163.py -q
ruff check src/agentic_runtime/policy_cards/
mypy src/agentic_runtime/policy_cards/
```

P1.6.0 test categories (59 tests):

- Valid card creation (minimal and full cards)
- Deterministic serialization (same card → same JSON → same hash)
- Closed-world unknown field rejection (arbitrary and dangerous)
- Dangerous metadata key rejection (authority, bypass, egress, sandbox, etc.)
- Invalid enum rejection (kind, status, scope_type)
- Missing required field rejection (identity, kind, status, scope, description)
- Source hash separation (raw ≠ canonical)

P1.6.1 test categories (61 tests):

- Schema version acceptance ("1.0" passes)
- Unsupported schema version rejection ("999.0", "0.0", "experimental", empty, null)
- Missing/empty/blank schema version rejection
- Required fields tuple present and non-empty
- Optional fields accepted (risk_binding, authority_binding, source, metadata)
- Forbidden fields rejected (authority_grant, policy_bypass, grant_authority, etc.)
- Unknown field rejection (random field, multiple unknowns)
- Dangerous metadata rejection (operator_not_required, evidence_bypass, delegation_grant, network_access)
- Safe metadata acceptance (owner_note, source_reference, review_hint)
- Schema export determinism (same output twice)
- Schema export content verification (all categories present)
- Canonical fields stable (same card → same hash)
- Schema version helpers (is_supported, validate_schema_version)
- Runtime-future field rejection (resolver, enforcement, conditions)
- Schema constants sanity (types, disjoint sets, JSON valid)

P1.6.3 test categories (36 tests):

- Default RiskTierPolicyCard validates and hashes
- Required R0-R6 tier coverage
- Invalid, missing, and duplicate tier rejection
- R5 explicit Operator confirmation, trace, evidence, and approval requirements
- R6 denied/non-permissive checks for execution, external egress, memory write, and tool write
- Reversibility and oversight consistency checks
- Action class mapping validation and invalid action-class rejection
- Generic PolicyCard compatibility with kind risk_tier
- Closed-world unknown top-level and nested definition field rejection
- Dangerous metadata rejection and safe metadata acceptance
- Deterministic serialization and hash stability
- Schema export determinism and schema version helpers
- Explicit assertion that no runtime resolver, classifier, simulation, trace hook, or enforcement API is implemented

P1.6.4 test categories (68 tests):

- Default HumanOversightPolicyCard validates and hashes
- Required R0-R6 oversight mappings
- Invalid, missing, and duplicate tier mapping rejection
- R4 requires approval_required or stricter (level and action)
- R5 requires explicit_confirmation_required (level, mode, action)
- R5 requires strong confirmation requirement fields (requires_explicit_confirmation, preview_required, evidence_required, operator_identity_required)
- R5 requires operator-required reviewer
- R6 must deny (level, mode, action)
- R6 cannot be approvable/confirmable
- Invalid oversight levels, modes, triggers, actions rejected
- Valid escalation rules accepted
- Dangerous metadata keys rejected (auto_approve, operator_not_required, etc.)
- Safe metadata accepted
- Generic PolicyCard compatibility with kind human_oversight
- Closed-world unknown top-level and nested field rejection
- Deterministic serialization and hash stability
- Schema export determinism and schema version helpers
- Explicit assertion that no runtime approval engine is implemented

P1.6.5 test categories (48 tests):

- Default DataResidencyPolicyCard validates with all 20 data classes
- Required data classes present (credentials, personal_data, sensitive_personal_data, etc.)
- All 20 data classes in default (including evaluation_record, tool_output, policy_record, etc.)
- Invalid data class / invalid zone rejected
- Missing required data class rejected
- Duplicate data class rejected
- local_only zero-outbound: no egress, no external model, no external API, no web search
- credentials no-egress, encryption required, audit trace required, no external model
- sensitive_personal_data must be local_only, no egress, no external model
- memory_record must be local_only, no egress
- trace_record must be local_only, no egress
- forbidden non-permissive: no egress, no external model
- Dangerous metadata keys rejected (allow_secret_egress, bypass_residency, etc.)
- Safe metadata accepted (owner_note, created_by, etc.)
- PolicyCard compatibility (kind="data_residency" required)
- Closed-world validation — unknown top-level and nested fields rejected
- Deterministic serialization — two default cards produce identical canonical JSON
- Hash stability — identical cards produce identical SHA-256 hashes; metadata changes produce different hashes
- Schema export determinism and schema version helpers
- Explicit assertion that no runtime enforcement methods exist

P1.6.6 test categories (38 tests):

- Default ToolPermissionPolicyCard validates with deny-by-default posture
- Default decision must be deny; permissive defaults rejected
- Unknown tool category denied
- Credential access denied by default
- External API/network egress not simple allow
- Shell command requires sandbox/approval/risk; sandboxed shell passes
- Execute/delete/config-write require governance
- Data residency compatibility — protected data classes rejected for external exposure
- Invalid tool category/permission type/permission decision rejected
- Broad allow-all matcher rejected
- Dangerous metadata keys rejected (allow_all_tools, bypass_tool_policy, shell_unrestricted, operator_not_required)
- Safe metadata accepted
- PolicyCard compatibility (kind="tool_permission" required)
- Closed-world validation — unknown top-level and nested fields rejected
- Deterministic serialization
- Hash stability
- Schema export deterministic
- No runtime enforcement methods on card
- Error hierarchy verified

P1.6.7 test categories (60 tests, `tests/test_memory_write_policy_cards_p167.py`):

- Default MemoryWritePolicyCard validates; default rules equal `DEFAULT_MEMORY_WRITE_RULES`
- Default decision must be deny; permissive defaults (allow, candidate_only, canonicalize_allowed) rejected
- No silent canonical write — canon_memory + allow rejected
- Canon memory requires source/evidence/trace references + operator review + explicit confirmation + conflict check; full requirements pass
- Policy memory protected — policy_memory + allow rejected; missing governance/review rejected
- Verified skill memory requires evaluation/verification/evidence/trace
- Skill candidate cannot be verified/canonized by default
- Operator profile protected — operator_profile + allow rejected; missing consent/review/provenance rejected
- Scratchpad ephemeral allowed; working memory session-scoped allowed
- Credentials cannot be durable memory — credentials in semantic/operator memory rejected
- Sensitive personal data strict — weak binding rejected; strict (evidence + provenance + residency check + review) passes
- Invalid memory zone rejected (global_brain, shadow_canon, unbounded_memory)
- Invalid memory write type rejected (auto_truth, secret_authority, self_upgrade)
- Invalid memory decision rejected (auto_canonize, always_remember, force_store)
- Invalid verification status / retention class rejected
- Dangerous metadata keys rejected (auto_canonize, bypass_memory_policy, remember_everything, consent_not_required, store_credentials)
- Safe metadata accepted (owner_note, created_by)
- PolicyCard compatibility (kind="memory_write" required)
- Closed-world validation — unknown/forbidden top-level and unknown nested rule fields rejected
- Deterministic serialization; canonical-dict round-trip preserves hash
- Hash stability; metadata changes produce different hashes
- Schema export deterministic; schema version helpers; protected-zone/strict-class constants
- No runtime enforcement methods on card; empty memory rules rejected; error hierarchy verified

P1.6.8 test categories (74 tests, `tests/test_prompt_policy_cards_p168.py`):

- Default PromptPolicyCard validates; default rules equal `DEFAULT_PROMPT_HANDLING_RULES`
- Default decision must be deny; permissive defaults (allow, context_only) rejected
- Unknown source cannot be trusted (trusted_system/trusted_developer/operator_authorized/repo_canonical/verified_template)
- External web content cannot be instruction authority
- Email content cannot be instruction authority
- Tool output cannot command (TOOL_OUTPUT_AS_INSTRUCTION)
- Retrieved memory cannot command
- Untrusted/external/tool-output/retrieved prompts cannot request tools
- Untrusted/external/tool-output/retrieved prompts cannot write memory
- Untrusted/external/tool-output/retrieved prompts cannot modify policy
- Untrusted/external/tool-output/retrieved prompts cannot modify identity
- High/critical injection risk (rule-level and signal-level) cannot pair with allow + instruction authority
- Trusted system/developer/operator classes validate under strict governance
- Invalid source type rejected (shadow_system, fake_operator, super_admin_prompt)
- Invalid trust level rejected (self_trusted, external_admin, auto_trusted)
- Invalid prompt role rejected (authority_grant, secret_exfiltration, policy_override)
- Invalid decision rejected (obey_always, ignore_policy, force_tool_call); invalid injection risk rejected
- Dangerous metadata keys rejected (bypass_prompt_policy, reveal_system_prompt, grant_tool_access, external_as_instruction, trust_unknown_source)
- Safe metadata accepted (owner_note, created_by)
- PolicyCard compatibility (kind="prompt" required)
- Closed-world validation — unknown/forbidden top-level and unknown nested rule fields rejected
- Deterministic serialization; canonical-dict round-trip preserves hash
- Hash stability; metadata changes produce different hashes
- Schema export deterministic; schema version helpers; source-category constants
- Boundary requirement loading; no runtime enforcement methods on card; empty prompt rules rejected; error hierarchy verified

## Verifying P1.5.10X

P1.5.10X establishes canonical AurelTraceLog integrity. AurelTraceLog is the only source of truth; Ledger, Evidence, RuntimeState, Evaluation, Mneme, Shell and Reports are projections over AurelTraceLog.

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/contracts -q
PYTHONPATH=src:. pytest tests/contracts tests/test_trace.py tests/test_trace_persistence_p06.py -q
PYTHONPATH=src:. pytest -q
ruff check .
mypy .
```

Focused contract coverage:

- append-only `AurelTraceLog`
- immutable `TraceEvent` records
- deterministic payload and event hashing
- genesis and previous-event hash chain integrity
- chain verification failure reporting
- `TraceEventRef` and `TraceBindingRef`
- non-canonical projection records

## Verifying P1.5.11A

P1.5.11A proves Golden Thread A: Intent → Context → Policy → Lease → Stub Exec → Trace → Evidence → Verifier → CapabilityEvidence. Verified capability evidence requires canonical trace, evidence, verifier pass, verifier limitations, and capability limitations.

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/contracts/test_evidence_ref_invariants.py tests/contracts/test_verifier_result_invariants.py tests/contracts/test_capability_evidence_invariants.py tests/golden_threads/test_thread_a_governed_evidence.py -q
PYTHONPATH=src:. pytest tests/contracts tests/golden_threads -q
PYTHONPATH=src:. pytest -q
ruff check src/agentic_runtime/contracts src/agentic_runtime/golden_threads tests/contracts tests/golden_threads
mypy src/agentic_runtime/contracts src/agentic_runtime/golden_threads
```

Focused contract coverage:

- trace-bound `EvidenceRef`
- `VerifierResult` pass/evidence/limitations/confidence invariants
- verified `CapabilityEvidenceRecord` factory and validation
- direct verified construction blocked
- failed verifier cannot create verified capability evidence
- operator feedback stub cannot auto-promote capability evidence
- canonical `AurelTraceLog` event and hash-chain verification in Golden Thread A

## Verifying P1.5.11B

P1.5.11B upgrades capability evidence with trace/context binding. Verified capability evidence now requires canonical trace, matching source event hash, evidence refs, verifier pass, limitations, evidence strength `strong|verified`, and safe/adequate context.

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/contracts/test_capability_evidence_invariants.py tests/contracts/test_capability_context_binding.py tests/contracts/test_context_adequacy_report.py tests/contracts/test_evidence_strength_level.py tests/golden_threads/test_thread_a_governed_evidence.py -q
PYTHONPATH=src:. pytest tests/contracts tests/golden_threads -q
PYTHONPATH=src:. pytest -q
ruff check src/agentic_runtime/contracts src/agentic_runtime/golden_threads tests/contracts tests/golden_threads
mypy src/agentic_runtime/contracts src/agentic_runtime/golden_threads
```

Focused contract coverage:

- `ContextBindingRef`
- `ContextAdequacyReport`
- `EvidenceStrengthLevel`
- source_event_hash required and matched to `TraceEventRef.event_hash`
- unsafe/insufficient context blocks verification
- partial context requires context limitation
- adequacy score cannot override unsafe status
- weak/moderate/none evidence strength cannot verify capability
- projection-only sources cannot verify capability
- Golden Thread A includes context binding and context adequacy

## Verifying P1.5.13

P1.5.13 normalizes all verifier outputs through 6 stub verifier normalizers. Every VerifierResult now requires verifier_kind, limitations, reason, confidence in range, evidence_refs for pass status, and source_trace_event_ref. Golden Thread A uses normalized verifier results via EvidenceIntegrityVerifierStub.

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/evaluation/test_verifier_normalization.py tests/golden_threads/test_thread_a_verifier_normalization.py tests/contracts/test_verifier_result_invariants.py -v
PYTHONPATH=src:. pytest tests/evaluation/test_evaluation_case_extraction.py -v  # P1.5.12 still works
ruff check src/agentic_runtime/contracts/verifier.py src/agentic_runtime/evaluation/verifier_normalization.py src/agentic_runtime/golden_threads/thread_a.py
mypy src/agentic_runtime/contracts/verifier.py src/agentic_runtime/evaluation/verifier_normalization.py
```

Focused contract coverage:

- `VerifierKind` enum (6 kinds)
- `VerifierNormalizationReport` dataclass
- `VerifierResult` v2 with verifier_kind, normalized_from, created_at
- 6 stub verifier normalizers: deterministic, operator review, policy check, LLM judge stub, context adequacy, evidence integrity
- Invariant tests: non-empty limitations, evidence_refs for pass, reason non-empty, confidence 0.0–1.0, source_trace_event_ref required
- Golden Thread A test: normalized verifier result, normalization report, verifier_kind populated

**Next:** P1.5.14 — Evaluation Mirror Runtime Hook

## Verifying P1.5.14

P1.5.14 creates the first runtime-callable Evaluation Mirror boundary. 5 new contracts (EvaluationTargetRef, EvaluationRequest, EvaluationRun, EvaluationEvent, EvaluationRunResult) with strict validation, plus `run_evaluation()` runtime hook that validates targets against AurelTraceLog, emits evaluation trace events, and returns deterministic results. Golden Thread A calls the hook after P1.5.12 extraction and P1.5.13 normalization. Anti-promotion structure enforced across all contracts.

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/evaluation/test_evaluation_runtime_hook.py tests/evaluation/test_evaluation_runtime_invariants.py tests/golden_threads/test_thread_a_evaluation_runtime.py -v
ruff check src/agentic_runtime/contracts/evaluation_runtime.py src/agentic_runtime/evaluation/runtime_hook.py src/agentic_runtime/golden_threads/thread_a.py
mypy src/agentic_runtime/contracts/evaluation_runtime.py src/agentic_runtime/evaluation/runtime_hook.py src/agentic_runtime/golden_threads/thread_a.py
```

Focused test coverage:

- 25 runtime hook tests: happy path, target validation, terminal status, anti-promotion, multiple evaluation modes, event binding
- 18 invariant tests: contract validation (empty fields, mismatched hash, serialization, anti-promotion structure)
- 6 Golden Thread A tests: evaluation runtime result fields, P1.5.12/P1.5.13 still work, events in trace log

**Next:** To be specified by operator.

## Verifying P1.5.12

P1.5.12 introduces EvaluationCase and RegressionCandidate extraction from trace-bound CapabilityEvidenceRecord. Golden Thread A now produces a candidate EvaluationCase. Extracted evaluation/regression records remain candidate-only.

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/evaluation/test_evaluation_case_extraction.py tests/golden_threads/test_thread_a_extracts_evaluation_case.py tests/golden_threads/test_thread_a_governed_evidence.py -v
PYTHONPATH=src:. pytest tests/contracts tests/golden_threads -q
ruff check src/agentic_runtime/contracts/evaluation_cases.py src/agentic_runtime/evaluation/extraction.py src/agentic_runtime/golden_threads/thread_a.py
mypy src/agentic_runtime/contracts/evaluation_cases.py src/agentic_runtime/evaluation/extraction.py
```

Focused contract coverage:

- `FailureMode`, `EvaluationCaseKind`, `EvaluationCaseStatus`, `ExtractionStatus`
- `EvaluationCase` with invariant validation (positive/regression/review kinds)
- `RegressionCandidate` with invariant validation
- `EvaluationCaseExtractionReport` with auditable status
- Extraction routing: review > regression > positive
- Positive case requires VERIFIED capability, PASS verifier, trace, matching hash, evidence, limitations, safe context
- Regression candidate from failed/unsafe/weak/unverifiable outcomes
- Review case from needs_review/inconclusive/partial context outcomes
- Candidate-only: nothing auto-accepted, no memory/skill/reflex/capability promotion
- Golden Thread A end-to-end still passes
- 46 tests across extraction, golden thread, serialization, and candidate-only guards

## Demo smoke test

```bash
PYTHONPATH=src python -m agentic_runtime.cli demo
# or
python -m agentic_runtime.demo
```

## Status smoke test

```bash
PYTHONPATH=src python -m agentic_runtime.cli status
python -m agentic_runtime.cli status --json
```

## Environment notes

### `test_timeout_kills_long_running_command` / `test_run_shell_timeout_is_enforced`

Both tests spawn nested subprocesses. In **restricted CI sandboxes**
that block subprocess execution, they are **skipped** automatically via
`requires_subprocess` in `tests/conftest.py`.

Run outside the restricted sandbox to confirm timeout behavior:
```bash
pytest tests/test_sandbox_p03.py::test_timeout_kills_long_running_command -q
pytest tests/test_tool_bus_p13.py::test_run_shell_timeout_is_enforced -q
```

## Verifying P1.0

```bash
pip install -e ".[dev]"
python3 -m compileall src tests
ruff check src tests
mypy src/agentic_runtime
pytest -q --cov=agentic_runtime --cov-fail-under=75
python -m agentic_runtime.cli alpha-seal
```

Expected: alpha-seal exits 0; full suite 300 passed, 4 skipped (when subprocess blocked).

## Verifying P1.0.1 (seal integrity)

```bash
pip install -e ".[dev]"
python3 -m compileall src tests
ruff check src tests
mypy src/agentic_runtime
pytest -q --cov=agentic_runtime --cov-fail-under=75
python -m agentic_runtime.cli alpha-seal
python -m agentic_runtime.cli demo-harness buggy_calculator --apply --sandbox restricted_local
```

Release artifacts:

- `agent/releases/P1.0_*.md`
- `agent/evidence/p1.0/*.json`
- `agent/reports/P1.0_RUNTIME_ALPHA_SEAL_REPORT.md`

Status: **PRE-SEAL** until CI green on baseline commit (Python 3.11 + 3.12).

## Verifying P0.11

1. `python3 -m compileall src tests` — exit 0
2. `pytest -q` — 121+ passed (1 env flake possible)
3. `python -m agentic_runtime.cli status` — shows `unsafe_local` sandbox mode
4. `python -m agentic_runtime.cli demo` — section 5 shows `require_approval` + HITL DENIED
5. `/agent` docs present

## Verifying P0.12

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest -q
PYTHONPATH=src:. pytest tests/test_model_providers_p12.py -q
```

Expected offline provider result:

```text
9 passed, 2 skipped
```

The skipped tests are integration placeholders:

- OpenAI integration requires `OPENAI_API_KEY`
- Ollama integration requires `AUREL_RUN_OLLAMA_TESTS=1`

Normal test runs do not require API keys or network access.

## Verifying P0.13

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_tool_bus_p13.py -q
PYTHONPATH=src:. pytest tests/test_tool_contract_p10.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused Tool Bus result:

```text
18 passed
```

The Tool Bus tests cover registry behavior, contract-bound validation,
filesystem boundary failures, patching, execution tool structured outputs, and
runtime integration.

## Verifying P0.14

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_repo_agent_p14.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused Repository Agent Loop result:

```text
20 passed
```

The P0.14 tests cover bounded context construction, allowed-path handling,
large-file truncation, deterministic planning, Runtime/Tool Bus patch execution,
structured test execution, bounded repair attempts, and a tiny end-to-end
repository task fixture.

CLI smoke example:

```bash
python -m agentic_runtime.cli repo-task "replace 'old' with 'new' in src/file.py"
python -m agentic_runtime.cli repo-task "replace 'old' with 'new' in src/file.py" --apply
```

## Verifying P0.15

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_hitl_p15.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused HITL result:

```text
16 passed
```

CLI smoke examples:

```bash
python -m agentic_runtime.cli approve-demo --mode deny
python -m agentic_runtime.cli repo-task "replace 'x' with 'y' in src/a.py" --dry-run
```

## Verifying P0.16

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_praxis_p16.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused Praxis result:

```text
24 passed
```

CLI smoke examples:

```bash
python -m agentic_runtime.cli praxis-demo
python -m agentic_runtime.cli memory-candidates
python -m agentic_runtime.cli praxis-report
```

## Verifying P0.17

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_sandbox_p17.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused Sandbox Hardening result:

```text
25 passed
```

CLI smoke examples:

```bash
python -m agentic_runtime.cli sandbox-status
python -m agentic_runtime.cli sandbox-status --profile restricted_local --json
python -m agentic_runtime.cli repo-task "replace 'x' with 'y' in src/a.py" --dry-run --sandbox no_exec_readonly
```

## Verifying P0.17.1

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_p0171_readiness.py -q
PYTHONPATH=src:. pytest -q
```

Expected focused readiness result:

```text
10 passed
```

## Verifying P0.19

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_demo_harness_p19.py -q
PYTHONPATH=src:. pytest -q
```

Harness smoke:

```bash
PYTHONPATH=src python -m agentic_runtime.cli demo-harness list
PYTHONPATH=src python -m agentic_runtime.cli demo-harness buggy_calculator
PYTHONPATH=src python -m agentic_runtime.cli demo-harness buggy_calculator --apply
```

Expected focused harness result:

```text
17 passed
```

## Verifying P0.20

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_p020_demo_seal.py -q
PYTHONPATH=src:. pytest -q
```

Run the demo and regenerate evidence through the public path:

```bash
PYTHONPATH=src python -m agentic_runtime.cli demo-harness buggy_calculator \
    --apply --repo-parent /tmp/p020_demo --evidence-dir agent/evidence/p0.20
```

Expected focused seal result:

```text
12 passed
```

Evidence artifacts are written under `agent/evidence/p0.20/` (8 files).

## Verifying P0.21

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_repo_planner_p021.py -q
PYTHONPATH=src:. pytest tests/test_repo_agent_p14.py -q
PYTHONPATH=src:. pytest tests/test_demo_harness_p19.py -q
PYTHONPATH=src:. pytest tests/test_p020_demo_seal.py -q
PYTHONPATH=src:. pytest -q
```

CLI smoke examples:

```bash
PYTHONPATH=src python -m agentic_runtime.cli demo-harness buggy_calculator --apply
PYTHONPATH=src python -m agentic_runtime.cli demo-harness missing_validation --planner hybrid --provider mock --apply
PYTHONPATH=src python -m agentic_runtime.cli repo-task "objective" --planner llm --provider mock
```

Expected focused P0.21 result: `18 passed`. Offline tests use `MockProvider`; API keys are not required.

## Verifying P1.1

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_model_config_p11.py -q
PYTHONPATH=src:. pytest tests/test_model_providers_p12.py -q
PYTHONPATH=src:. pytest tests/test_repo_planner_p021.py -q
PYTHONPATH=src:. pytest -q
```

CLI smoke examples:

```bash
python -m agentic_runtime.cli config validate
python -m agentic_runtime.cli models list
python -m agentic_runtime.cli providers status
```

Expected focused P1.1 result: `21 passed`. Config defaults use mock provider; no API keys required.

Report: `agent/reports/P1.1_MODEL_CONFIGURATION_SECRET_BOUNDARY_REPORT.md`


## Verifying P1.2

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_prompt_system_p12.py -q
PYTHONPATH=src:. pytest tests/test_model_config_p11.py -q
PYTHONPATH=src:. pytest tests/test_repo_planner_p021.py -q
PYTHONPATH=src:. pytest -q
PYTHONPATH=src:. python -m agentic_runtime.cli prompts validate
PYTHONPATH=src:. python -m agentic_runtime.cli prompts list
PYTHONPATH=src:. python -m agentic_runtime.cli prompts show repo_planner
PYTHONPATH=src:. python -m agentic_runtime.cli prompts render repo_planner --var objective="test" --dry-run
PYTHONPATH=src:. python -m agentic_runtime.cli alpha-seal --skip-coverage
```

Expected focused P1.2 result: `26 passed`. Prompt tests and CLI smoke use mock/local config and require no API keys.

## Verifying P1.2.1

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_public_entrypoints_p121.py -v
PYTHONPATH=src:. pytest tests/test_prompt_system_p12.py tests/test_model_config_p11.py -q
PYTHONPATH=src:. pytest tests/test_repo_planner_p021.py tests/test_demo_harness_p19.py -q
PYTHONPATH=src:. pytest -q
PYTHONPATH=src:. python -m agentic_runtime.demo
PYTHONPATH=src:. python examples/demo.py
PYTHONPATH=src:. python -m agentic_runtime.cli verify
PYTHONPATH=src:. python -m agentic_runtime.cli alpha-seal --skip-coverage
ruff check src tests
mypy src/agentic_runtime --ignore-missing-imports
```

Expected public entrypoint results:
- `python -m agentic_runtime.demo` exits 0, prints safe no-skill message (evidence gates not satisfied)
- `examples/demo.py` exits 0, same output
- `cli verify` exits 0 (runs full pytest suite)
- `cli alpha-seal --skip-coverage` exits 0 (runs pytest + compileall + docs)
- Focused smoke tests: `8 passed`
- ruff: clean; mypy: no errors in model_router.py

## Verifying P1.3

```bash
PYTHONPATH=src:. pytest tests/test_tool_manifest_p130.py -q
PYTHONPATH=src:. pytest tests/test_tool_manifest_validation_p131.py -q
PYTHONPATH=src:. pytest tests/test_tool_manifest_loader_p132.py -q
PYTHONPATH=src:. pytest tests/test_tool_registry_p133.py -q
PYTHONPATH=src:. pytest tests/test_tool_quarantine_p134.py -q
PYTHONPATH=src:. pytest tests/test_tool_invocation_draft_p135.py -q
PYTHONPATH=src:. pytest tests/test_tool_lifecycle_events_p136.py -q
PYTHONPATH=src:. pytest tests/test_tool_research_metadata_p137.py -q
PYTHONPATH=src:. pytest tests/test_builtin_tool_manifests_p138.py -q
```

Expected: all P1.3 unit/integration tests pass (~280 tests across phase files).

## Verifying P1.3.9 seal

```bash
PYTHONPATH=src:. pytest tests/test_p13_tool_manifest_layer_seal.py -q
```

Expected: `58 passed`.

Governance hotfix cross-references (canonical tests, also smoke-checked in seal file):

- Prompt risk_tier: `tests/test_prompt_system_p12.py`
- YAML no truncation / fail loud: `tests/test_model_config_p11.py`
- restricted_local honesty: `tests/test_sandbox_p17.py`
- run_shell R4: `tests/test_hitl_p15.py::test_policy_r4_warning_for_run_shell`
- run_shell contract: `tests/test_tool_contract_p10.py`

## Verifying P1.4.0

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_p14_scope_contract_docs.py -q
ruff check src tests
mypy src/agentic_runtime
```

Expected: doc existence tests pass; `P14_PATCHES` contains P1.4.0–P1.4.20; required constitutional phrases present in `docs/P1.4_*.md`.

Constitutional docs:

- `docs/P1.4_IDENTITY_AUTONOMY_SCOPE_CONTRACT.md`
- `docs/P1.4_AGENT_TRUST_CONSTITUTION.md`
- `docs/P1.4_RESEARCH_ALIGNMENT_NOTES.md`

## Verifying P1.4.1

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_identity_kernel.py tests/test_identity_kernel_hash.py tests/test_identity_kernel_cli.py -q
python -m agentic_runtime.cli identity kernel validate
python -m agentic_runtime.cli identity kernel show --json
ruff check src tests
mypy src/agentic_runtime
```

Expected: 27 identity kernel tests pass; CLI validate exits 0; show JSON includes 64-char `kernel_hash`.

## Verifying P1.4.2

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_persona_manifest.py tests/test_persona_manifest_hash.py tests/test_persona_manifest_cli.py -q
python -m agentic_runtime.cli identity persona validate
python -m agentic_runtime.cli identity persona show --json
python -m agentic_runtime.cli identity persona summary --json
ruff check src tests
mypy src/agentic_runtime
```

Expected: 36 persona manifest tests pass; CLI validate exits 0; show JSON includes 64-char `persona_hash`; summary JSON includes authority boundaries and capability honesty rules with no raw YAML.

## Verifying P1.4.7-MG (Agent Identity Card merge gate)

```bash
python3 -m compileall src tests
PYTHONPATH=src:. pytest tests/test_p147_mg_agent_identity_card.py \
  tests/test_agent_identity_card.py tests/test_agent_identity_card_hash.py \
  tests/test_agent_identity_card_cli.py tests/test_self_model.py -q
python3 -m agentic_runtime.cli identity card validate --json
python3 -m agentic_runtime.cli identity card show --json
ruff check .
mypy src
```

Expected: MG seal tests pass; `agent_identity_card` capability is `implemented` / `P1.4.7`; custom `self_model_policy_path` affects final card validation; CLI default config dir matches `default_config_dir()`; card CLI validate/show exit 0.

## Verifying P1.4.8 (Autonomy Scale Engine)

```bash
# Seal / unit / CLI autonomy tests
PYTHONPATH=src:. python3 -m pytest tests/test_autonomy_scale_engine.py -q
# Expected: 40 passed

# CLI smoke
python3 -m agentic_runtime.cli identity autonomy evaluate \
  --action-category answer --action-name test \
  --risk-tier R1_LOW --reversibility-tier R1_FULLY_REVERSIBLE --json
# Expected: A0_ANSWER_ONLY, allowed=true

python3 -m agentic_runtime.cli identity autonomy evaluate \
  --action-category unknown --action-name test \
  --risk-tier R1_LOW --reversibility-tier R1_FULLY_REVERSIBLE --json
# Expected: A7_DENIED, allowed=false, blocker=unknown_action_category

python3 -m agentic_runtime.cli identity autonomy evaluate \
  --action-category high_risk --action-name risky_op \
  --risk-tier R3_HIGH --reversibility-tier R1_FULLY_REVERSIBLE --json
# Expected: A6_APPROVAL_GATED_HIGH_RISK, requires_human_approval=true
```

Expected: 40 autonomy tests pass; A0–A7 correctly mapped per action category; unknown/ambiguous values fail closed; A7 = denied, not highest autonomy; no global autonomy score; planned capabilities cannot authorize.

## Verifying P1.4.9 (Measured Autonomy Score)

```bash
# Unit / seal / classification / CLI / persistence tests
PYTHONPATH=src:. python3 -m pytest tests/test_measured_autonomy_score.py -q
# Expected: 45 passed

# CLI measurement
python3 -m agentic_runtime.cli identity autonomy measure --minimum-decisions 0 --json
# Expected: INSUFFICIENT_EVIDENCE class

python3 -m agentic_runtime.cli identity autonomy measure \
  --evaluate-and-record --action-category answer \
  --action-name test --risk-tier R1_LOW \
  --reversibility-tier R1_FULLY_REVERSIBLE --minimum-decisions 1 --json
# Expected: score with total_decisions=1

python3 -m agentic_runtime.cli identity autonomy measure --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'global_score' not in d['score']; assert d['score']['autonomy_class'] in ('INSUFFICIENT_EVIDENCE','DENIED_OR_UNTRUSTED')"
# Expected: no global autonomy percentage, valid class
```

Expected: 45 tests pass; INSUFFICIENT_EVIDENCE when below minimum; A7 never ranked as highest verified; planned/roadmap capabilities not counted; no global autonomy percentage; JSON output is stable; measurement doesn't change permissions or execute tools.

## Verifying P1.4.10 (Capability Claim Boundary Engine)

```bash
# Unit / seal / registry / engine / CLI / boundary tests
PYTHONPATH=src:. python3 -m pytest tests/test_capability_claim_boundary.py -q
# Expected: 51 passed

# CLI evaluate
python3 -m agentic_runtime.cli identity claims evaluate \
  --claim "Aurel can read files" --json
# Expected: evidence-gated evaluation, DENIED without sufficient evidence

# CLI list
python3 -m agentic_runtime.cli identity claims list
# Expected: 14 pre-registered claims listed

# CLI show
python3 -m agentic_runtime.cli identity claims show --claim-id CC-001 --json
# Expected: claim details with evidence requirements

# CLI validate (all registry claims)
python3 -m agentic_runtime.cli identity claims validate
# Expected: all 14 claims pass registry validation

# CLI rewrite
python3 -m agentic_runtime.cli identity claims rewrite \
  --claim "Aurel is autonomous" --json
# Expected: FORBIDDEN — global autonomy not allowed; safe rewrite preserves truth
```

Expected: 51 tests pass; anti-hype firewall blocks roadmap-as-evidence; global autonomy claims are FORBIDDEN; safe rewrites never introduce marketing spin; fail-closed on unknown claims and missing evidence.

## Verifying P1.4.11 (External Doctrine Assimilation Registry)

```bash
# Unit / mapping / CLI / seal tests
PYTHONPATH=src:. python3 -m pytest   tests/test_external_doctrine_registry.py   tests/test_doctrine_cli.py   tests/test_doctrine_seal.py -q
# Expected: 33 passed

# CLI smoke
python3 -m agentic_runtime.cli identity doctrine --help
python3 -m agentic_runtime.cli identity doctrine validate
python3 -m agentic_runtime.cli identity doctrine list --json
python3 -m agentic_runtime.cli identity doctrine show agentic_os_asymmetric_teardown --json
python3 -m agentic_runtime.cli identity doctrine impact agentic_os_asymmetric_teardown --json
```

Expected: 3 seeded doctrine inputs validate; every seed has source hash, roadmap mapping, claim boundaries, and risk notes; roadmap influence is not implementation; rejected doctrine cannot create roadmap impact; implemented status requires capability evidence; doctrine claim boundaries route through P1.4.10.


## Verifying P1.4.12

```bash
.venv/bin/python -m compileall src tests
PYTHONPATH=src:. .venv/bin/python -m pytest tests/identity -q
PYTHONPATH=src:. .venv/bin/python -m pytest -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity attestation --help
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity attestation validate --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity attestation list --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity attestation show operator_contract --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity attestation verify-bundle --json
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
```

Expected P1.4.13 local result: compileall passed; focused identity suite `58 passed` (core + seal + CLI); ruff passed; mypy passed (117 source files with no issues). Full suite `1321 passed, 2 skipped`.

### P1.4.13 Authority Delta Detector

**Solo:**
```bash
PYTHONPATH=src:. pytest tests/identity/test_authority_delta.py tests/identity/test_authority_delta_seal.py tests/identity/test_authority_delta_cli.py -v
# Expected: 58 passed (27 core + 14 seal + 9 CLI + 8 helpers)
```

**CLI smoke:**
```bash
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity authority-delta --help
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity authority-delta compare \
  --old tests/fixtures/authority_delta/operator_contract_low_risk.yaml \
  --new tests/fixtures/authority_delta/operator_contract_high_risk.yaml \
  --source-kind operator_contract --json
# Expected: safe_to_auto_accept=false, requires_operator_consent=true, highest_severity=CRITICAL, 25 deltas, 0 UNKNOWN_AUTHORITY_CHANGE
```

**Core test categories:**
- Risk ceiling detection (increase/decrease/critical)
- Authority scope expansion/reduction
- Tool permission / write scope / external effect detection
- Human oversight weakening/strengthening
- Claim/doctrine/capability status escalation
- Delta report JSON serialization
- Attestation reference linkage
- Severity ordering and summary helpers

**Seal invariants:**
- INV-P1413-01 through INV-P1413-10 (all pass)

### P1.4.14 Operator Consent Binding

**Solo:**
```bash
PYTHONPATH=src:. pytest tests/identity/test_operator_consent.py tests/identity/test_operator_consent_seal.py tests/identity/test_operator_consent_cli.py -v
# Expected: 55 passed (27 core + 14 seal + 10 CLI + 4 fixtures)
```

**CLI smoke:**
```bash
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity consent --help
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity consent request \
  --delta-report tests/fixtures/consent/delta_report.json --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity consent grant \
  --request tests/fixtures/consent/consent_request.json --operator-id op1 --ack-risk --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity consent validate \
  --record tests/fixtures/consent/consent_record.json \
  --delta-report tests/fixtures/consent/delta_report.json --json
```

**Expected P1.4.15 local result:** compileall passed; focused identity suite `53 passed`; ruff passed; mypy passed. Full suite `1429 passed, 2 skipped`.

**Core test categories:**
- Consent request building from delta report
- Grant consent (with/without risk acknowledgement, HIGH/CRITICAL enforcement)
- Deny consent
- Revoke consent (only granted records)
- Validate consent binding (accept matching, reject attestation/delta/scope mismatch)
- Expiry validation
- Scope enforcement (SINGLE_DELTA, DELTA_REPORT, SOURCE_UPDATE, SESSION_LIMITED unsupported)
- Consent not transferable, not global, not capability verification
- JSON serialization stability

**Seal invariants:**
- INV-P1414-01 through INV-P1414-10 (all pass)

### P1.4.15 Identity Governance Command Surface

**Solo:**
```bash
PYTHONPATH=src:. pytest tests/identity/test_identity_cli_surface.py tests/identity/test_identity_cli_routing.py tests/identity/test_identity_cli_seal.py -v
# Expected: 53 passed (21 core/envelope + 23 routing + 9 seal)
```

**CLI smoke:**
```bash
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity --help
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity verify --json
```

**Expected P1.4.15 local result:** compileall passed; focused identity suite `53 passed`; ruff passed; mypy passed. Full suite `1429 passed, 2 skipped`.

**Core test categories:**
- Envelope: ok/command/status/errors/warnings/result contract, deterministic serialization
- Status: subsystem probing, read-only, human-readable output with blockers
- Verify: non-destructive validator checks, no side effects
- Routing: all 10 subcommand groups accessible under identity namespace
- Read-only: status/verify output stable, no consent artifacts, no source mutation

**Seal invariants:**
- INV-P1415-01 through INV-P1415-10 (all pass)

### P1.4.16 Identity Test Battery

**Solo:**
```bash
PYTHONPATH=src:. pytest tests/identity/test_identity_test_battery.py tests/identity/test_identity_test_battery_seal.py -v
# Expected: 31 passed (18 core + 13 seal)
```

**CLI smoke:**
```bash
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity test-battery --help
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity test-battery list
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity test-battery run --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity test-battery run-case kernel-001 --json
```

**Expected P1.4.16 local result:** compileall passed; focused battery suite `31 passed`; ruff passed; mypy passed. Full suite `1460 passed, 2 skipped`.

**Core test categories:**
- Battery engine: case model, scoring (OK/FAIL/SKIP), aggregate status (PASSED/FAILED/DEGRADED/SKIPPED)
- 7 scenario categories: kernel, persona, operator_contract, communication_modes, identity_context, self_model, identity_card
- 26 test cases total, each independently scorable
- Adversarial scenarios included by default, CLI toggleable via `--scenarios`
- Late imports in scenario runner dispatch to avoid circular imports
- Two-file architecture: battery engine (`identity_test_battery.py`) + scenario runners (`identity_test_battery_scenarios.py`)

**Test file summary:**
- `tests/identity/test_identity_test_battery.py` — 18 core tests (engine, scoring, aggregation, CLI)
- `tests/identity/test_identity_test_battery_seal.py` — 13 integrated/seal tests (full battery run, adversarial, CLI integration)
- Full suite: **1460 passed, 2 skipped** (zero regressions)

**Seal invariants:**
- INV-P1416-01 through INV-P1416-10 (all pass)

### P1.4.19 Identity Docs / Reports / State Update

**Solo:**
```bash
PYTHONPATH=src:. pytest tests/identity/test_p1419_anti_overclaim.py -v
# Expected: 29 passed (8 anti-overclaim + 6 seal readiness + 2 CLI + 7 invariant/checklist coverage + 6 module index completeness)
```

**CLI smoke:**
```bash
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity seal-readiness --json
```

**Expected P1.4.19 local result:** compileall passed; focused anti-overclaim suite `29 passed`; ruff passed; mypy passed. Full identity suite `384 passed`.

**Core test categories:**
- Doc existence (all agent/*.md files present)
- Anti-overclaim (8 tests): no new governance semantics, no autonomy overclaim, no production readiness claim, no ABOS/AETHER implementation claim, no authority grant, no state mutation, no P1.4.20 replacement, no capability expansion
- Seal readiness (6 tests): P14SealReadinessReport construction, module status, CLI group index, invariant index, limitation index, checklist coverage
- CLI (2 tests): `identity seal-readiness --json` output shape, exit codes
- Invariant/checklist coverage (7 tests): 15 P14_INVARIANTS exit, 10 P1419_INVARIANTS exit, 22 P1420_SEAL_CHECKLIST items exit, all invariants satisfied
- Module index completeness: 18 CLI groups, identity module inventory

**Test file summary:**
- `tests/identity/test_p1419_anti_overclaim.py` — 29 tests total
- Identity suite total: **384 passed** (zero regressions from P1.4.18's 355)
- P1.4.19 adds no new governance semantics, overclaims, or authority

**Seal invariants:**
- P14_INVARIANTS (15): P1.4.0–P1.4.20 scope contract invariants (all pass)
- P1419_INVARIANTS (10): consolidation/audit-specific invariants (all pass)
- P1420_SEAL_CHECKLIST (22): exit seal readiness checklist items (all covered)

### P1.4.18 Trust Evidence Linkage

**Solo:**
```bash
PYTHONPATH=src:. pytest tests/identity/test_trust_evidence.py tests/identity/test_trust_evidence_seal.py -v
# Expected: 57 passed (34 core + 23 seal/CLI)
```

**CLI smoke:**
```bash
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity trust-evidence --help
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity trust-evidence requirements --lifecycle-state ACTIVE --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity trust-evidence build --lifecycle-state ACTIVE --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity trust-evidence validate --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity trust-evidence explain --json
```

**Expected P1.4.18 local result:** compileall passed; focused trust evidence suite `57 passed` (34 core + 23 seal/CLI); ruff passed; mypy passed. Full identity suite `355 passed`.

**Core test categories:**
- TrustEvidenceKind, TrustEvidenceStatus, TrustPosture, TrustEvidenceRef domain model construction and serialization
- TrustEvidenceRequirement resolution from lifecycle state
- TrustEvidenceBundle build with 5 helper builders (source attestation, test battery, consent, authority delta, lifecycle)
- TrustEvidenceBundle validation (structural integrity, reference consistency)
- TrustEvidenceLinkageReport generation with posture explanation
- Categorical posture resolution (no numeric score)
- Human-readable and JSON formatters
- CLI: `identity trust-evidence requirements/build/validate/explain`

**Test file summary:**
- `tests/identity/test_trust_evidence.py` — 34 core tests (domain, requirements, bundle build, validation, posture resolution, serialization)
- `tests/identity/test_trust_evidence_seal.py` — 23 seal/CLI tests
- Identity suite total: **355 passed** (zero regressions)

**Seal invariants:**
- INV-P1418-01 through INV-P1418-10 (all pass)

### P1.4.17 Agent Lifecycle Eligibility State Machine

**Solo:**
```bash
PYTHONPATH=src:. pytest tests/identity/test_agent_lifecycle.py tests/identity/test_agent_lifecycle_seal.py -v
# Expected: 60 passed (38 core + 22 seal/CLI)
```

**CLI smoke:**
```bash
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity lifecycle --help
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity lifecycle show --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity lifecycle profile --state ACTIVE --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity lifecycle validate-transition --from DRAFT --to ACTIVE --reason OPERATOR_INITIATED --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity lifecycle transitions --state ACTIVE --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity lifecycle recommend --json
```

**Expected P1.4.17 local result:** compileall passed; focused lifecycle suite `60 passed`; ruff passed; mypy passed. Full suite `1520 passed, 2 skipped`.

**Core test categories:**
- Lifecycle state transitions: DRAFT, ACTIVE, SUSPENDED, RESTRICTED, MAINTENANCE, DEPRECATED, ARCHIVED, REVOKED
- 24 reason codes for state changes
- 9-lane eligibility model (eligible/blocked lanes + required gates)
- Terminal REVOKED: no transitions out
- DRAFT→ACTIVE denied, SUSPENDED→ACTIVE denied
- RESTRICTED is reason-sensitive
- Recommendation engine: read-only, reads governance signals, does not apply
- Lifecycle does not grant authority — lane eligibility only

**Test file summary:**
- `tests/identity/test_agent_lifecycle.py` — 38 core tests (states, transitions, lanes, invariants)
- `tests/identity/test_agent_lifecycle_seal.py` — 22 seal/CLI tests
- Full suite: **1520 passed, 2 skipped** (zero regressions from P1.4.16's 1460)

**Seal invariants:**
- INV-P1417-01 through INV-P1417-17 (all pass)

### P1.4.20 P1.4 Identity & Autonomy Exit Seal

**Solo:**
```bash
PYTHONPATH=src:. pytest tests/identity/test_p14_exit_seal.py -v
# Expected: 28 passed (core + governance + adversarial + CLI + docs)
```

**CLI smoke:**
```bash
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity p14-seal --help
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity p14-seal run --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity p14-seal list-checks --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli identity p14-seal run-check import_objects --json
```

**Expected P1.4.20 local result:** compileall passed; focused exit seal suite `28 passed`; ruff passed; mypy passed. Identity total **412 passed**.

**Core test categories:**
- Import/object seal checks — all P1.4 identity modules load and export correct objects
- CLI seal checks — `identity p14-seal run/list-checks/run-check` commands accessible and functional
- Governance invariant checks — all P1.4 invariants (P14_INVARIANTS, P1419_INVARIANTS) verified
- Adversarial checks — edge cases, boundary violations, invalid inputs tested
- Docs consistency checks — agent/*.md and docs/*.md synchronized with code
- Seal is read-only — no mutation, no authority grant, no consent grant
- Seal result: SEALED_WITH_LIMITATIONS — honest; P1.5/P1.6/P1.8/P6/P7 not yet implemented

**Test file summary:**
- `tests/identity/test_p14_exit_seal.py` — 28 tests total (core + governance + adversarial + CLI + docs)
- Identity suite total: **412 passed** (from P1.4.19's 384 + 28 new)

**Seal result:** SEALED_WITH_LIMITATIONS — 15 known limitations carried forward from P1.4.19.
P1.4 is sealed. P1.5.0 Evaluation Mirror Foundation Gate is next.

### P1.5.0 Evaluation Mirror Foundation Gate + Roadmap v3.2 Alignment

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/ -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation foundation status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation foundation scope --domain AUREL_CORE --json
```

**Expected P1.5.0 local result:** compileall passed; evaluation suite `33+ passed`; ruff passed; mypy passed. Identity total **412 passed** (no regressions).

**P1.5 Evaluation Mirror foundation tests:**
- evaluation object model is closed-world (EvaluationDomain, EvaluationSubjectType enums)
- evaluation subjects are typed and evidence-ref-bound
- evaluation criteria are explicit (required, evidence_required)
- evaluation run envelopes are evidence-bound
- evaluation run envelope does not verify capability by itself
- claim verification requires evaluation evidence later (P1.5.1+)
- roadmap docs aligned with v3.2
- docs do not reset P1–P2
- docs do not prematurely start P22–P24

**Test file summary:**
- `tests/evaluation/test_evaluation_foundation.py` — 16 core tests
- `tests/evaluation/test_p150_roadmap_alignment.py` — 10 roadmap alignment tests
- `tests/evaluation/test_p150_scope_guards.py` — 7 anti-scope-creep tests

**Core test categories:**
- Core evaluation (16): domain/subject closed-world, scope defaults, envelope build/validate, serialization, foundation report
- Roadmap alignment (10): P1.5.0 current, P1.5.1 next, P1–P2 stable, HQ/A-Hub/S-Hub/L-Hub/IDE, architecture doctrines, v3.2 not reset
- Anti-scope-creep (7): no full P4 claim, no P22–P24 early start, no Hub runtime, no Model-of-Models/Work, no LoRA, envelope does not verify capability

**Next:** P1.5.8 — Benchmark Hygiene Guard.

### P1.5.8 Benchmark Hygiene Guard + Sparse Hygiene Readiness

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_benchmark_hygiene.py tests/evaluation/test_benchmark_fixture_boundary.py tests/evaluation/test_benchmark_hygiene_decision.py tests/evaluation/test_benchmark_hygiene_binding_downgrade.py tests/evaluation/test_benchmark_hygiene_serialization.py tests/evaluation/test_p158_sparse_hygiene_readiness.py tests/evaluation/test_p158_scope_guards.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation hygiene status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation hygiene examples --json
```

**Expected P1.5.8 local result:** focused hygiene suite **66 passed**; evaluation suite **529 passed**; identity suite **412 passed**; canonical full suite with `PYTHONPATH=src:.` **2163 passed, 2 skipped**.

**Test file summary:**
- `tests/evaluation/test_benchmark_hygiene.py` — core enums, policy, assessment status tests
- `tests/evaluation/test_benchmark_fixture_boundary.py` — boundary validation and contamination classification tests
- `tests/evaluation/test_benchmark_hygiene_decision.py` — decision support caps and blockers
- `tests/evaluation/test_benchmark_hygiene_binding_downgrade.py` — binding downgrade/preservation tests
- `tests/evaluation/test_benchmark_hygiene_serialization.py` — JSON serialization tests
- `tests/evaluation/test_p158_sparse_hygiene_readiness.py` — sparse hygiene risk readiness tests
- `tests/evaluation/test_p158_scope_guards.py` — anti-scope-creep tests

**Next:** P1.5.9 — Adversarial Evaluation Cases.

### P1.5.9 Adversarial Evaluation Cases + Sparse Trap Readiness

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_adversarial_cases.py tests/evaluation/test_adversarial_case_registry.py tests/evaluation/test_adversarial_case_resolution.py tests/evaluation/test_adversarial_case_serialization.py tests/evaluation/test_p159_sparse_adversarial_cases.py tests/evaluation/test_p159_scope_guards.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation adversarial status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation adversarial examples --json
```

**Expected P1.5.9 local result:** focused adversarial suite **76 passed**; evaluation suite **605 passed**; identity suite **412 passed**; canonical full suite with `PYTHONPATH=src:.` **2239 passed, 2 skipped**.

**Test file summary:**
- `tests/evaluation/test_adversarial_cases.py` — core enums, validation, trap semantics, serialization
- `tests/evaluation/test_adversarial_case_registry.py` — registration, listing, registry validation
- `tests/evaluation/test_adversarial_case_resolution.py` — subject/domain/criteria resolution
- `tests/evaluation/test_adversarial_case_serialization.py` — JSON serialization
- `tests/evaluation/test_p159_sparse_adversarial_cases.py` — default set + sparse readiness
- `tests/evaluation/test_p159_scope_guards.py` — anti-scope-creep tests

**Next:** P1.5.10 — Baseline Comparison Model.

### P1.5.10 Baseline Comparison Model + Sparse Comparison Readiness

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_baseline_comparison.py tests/evaluation/test_baseline_reference.py tests/evaluation/test_baseline_comparison_policy.py tests/evaluation/test_baseline_comparison_serialization.py tests/evaluation/test_p1510_sparse_baseline_comparison.py tests/evaluation/test_p1510_scope_guards.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation baseline status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation baseline examples --json
```

**Expected P1.5.10 local result:** focused baseline suite **69 passed**; evaluation suite **674 passed**; identity suite **412 passed**; canonical full suite with `PYTHONPATH=src:.` **2308 passed, 2 skipped**.

**Test file summary:**
- `tests/evaluation/test_baseline_comparison.py` — result/adversarial/hygiene comparison and resolver tests
- `tests/evaluation/test_baseline_reference.py` — baseline reference validation tests
- `tests/evaluation/test_baseline_comparison_policy.py` — policy and input validation tests
- `tests/evaluation/test_baseline_comparison_serialization.py` — JSON serialization tests
- `tests/evaluation/test_p1510_sparse_baseline_comparison.py` — sparse dimension readiness tests
- `tests/evaluation/test_p1510_scope_guards.py` — anti-scope-creep tests

**Historical note:** P1.5.12 and P1.5.13 were later completed; current work is P1.6.8S and next planned feature is P1.6.9.

### P1.5.7 Evidence-to-Claim Binding

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_evidence_claim_binding*.py tests/evaluation/test_p157_*.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation binding status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation binding examples --json
```

**Expected P1.5.7 local result:** evaluation suite **463 passed**.

**Test file summary:**
- `tests/evaluation/test_evidence_claim_binding.py` — 31 core binding + validation + serialization tests
- `tests/evaluation/test_evidence_claim_binding_policy.py` — 7 policy tests
- `tests/evaluation/test_evidence_claim_binding_aggregation.py` — 11 aggregation tests
- `tests/evaluation/test_evidence_claim_binding_serialization.py` — 7 serialization tests
- `tests/evaluation/test_p157_sparse_binding_readiness.py` — 8 sparse binding readiness tests
- `tests/evaluation/test_p157_scope_guards.py` — 12 anti-scope-creep tests

**Next:** P1.5.8 — Benchmark Hygiene Guard.

### P1.5.6 Result Classification Engine

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_result_classification*.py tests/evaluation/test_criterion_classification*.py tests/evaluation/test_p156_*.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation classify status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation classify examples --json
```

**Expected P1.5.6 local result:** evaluation suite **387 passed**; full suite **2013 passed, 2 skipped** (8 pre-existing CLI failures unrelated).

**Test file summary:**
- `tests/evaluation/test_result_classification.py` — 29 core classification + validation + result aggregation + criterion tests
- `tests/evaluation/test_criterion_classification.py` — 8 standalone criterion classification tests
- `tests/evaluation/test_result_classification_to_evaluation_result.py` — 8 conversion tests
- `tests/evaluation/test_result_classification_serialization.py` — 7 serialization tests
- `tests/evaluation/test_p156_sparse_classification_readiness.py` — 12 sparse classification readiness tests
- `tests/evaluation/test_p156_scope_guards.py` — 10 anti-scope-creep tests

**Next:** P1.5.7 — Evidence-to-Claim Binding.

### P1.5.5 Evaluation Run Envelope

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_evaluation_run_envelope*.py tests/evaluation/test_p155_*.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation runs status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation runs examples --json
```

**Expected P1.5.5 local result:** evaluation suite **313 passed**; identity **412 passed** (no regressions).

**Test file summary:**
- `tests/evaluation/test_evaluation_run_envelope.py` — 15 core object + evidence + envelope builder tests
- `tests/evaluation/test_evaluation_run_envelope_validation.py` — 12 validation tests
- `tests/evaluation/test_evaluation_run_evidence_requirements.py` — 4 evidence derivation tests
- `tests/evaluation/test_evaluation_run_envelope_serialization.py` — 7 serialization tests
- `tests/evaluation/test_p155_sparse_run_readiness.py` — 6 sparse run readiness tests
- `tests/evaluation/test_p155_scope_guards.py` — 10 anti-scope-creep tests

**Next:** P1.5.6 — Result Classification Engine.

### P1.5.4 Evaluation Criteria Schema

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_evaluation_criteria*.py tests/evaluation/test_p154_*.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation criteria status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation criteria examples --json
```

**Expected P1.5.4 local result:** evaluation suite **259 passed**; identity **412 passed** (no regressions).

**Test file summary:**
- `tests/evaluation/test_evaluation_criteria_schema.py` — 22 core object + validation tests
- `tests/evaluation/test_evaluation_criteria_resolution.py` — 10 criteria resolution tests
- `tests/evaluation/test_evaluation_criteria_serialization.py` — 10 serialization tests
- `tests/evaluation/test_p154_sparse_criteria_readiness.py` — 13 sparse criteria readiness tests
- `tests/evaluation/test_p154_scope_guards.py` — 9 anti-scope-creep tests

**Next:** P1.5.6 — Result Classification Engine.

### P1.5.3 Evaluation Subject Registry

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_evaluation_subject_registry*.py tests/evaluation/test_p153_*.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation subjects status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation subjects examples --json
```

**Expected P1.5.3 local result:** evaluation suite **195 passed**; identity **412 passed** (no regressions).

**Test file summary:**
- `tests/evaluation/test_evaluation_subject_registry.py` — 15 core object + validation tests
- `tests/evaluation/test_evaluation_subject_registration.py` — 15 registration decision tests
- `tests/evaluation/test_evaluation_subject_registry_serialization.py` — 17 serialization + resolve/list/registry validation tests
- `tests/evaluation/test_p153_sparse_cognition_readiness.py` — 16 sparse cognition readiness tests
- `tests/evaluation/test_p153_scope_guards.py` — 12 anti-scope-creep tests

**Next:** P1.5.4 — Evaluation Criteria Schema.

### P1.5.2 Capability Evidence Record

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_capability_evidence*.py tests/evaluation/test_p152_scope_guards.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation capability-evidence status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation capability-evidence examples --json
```

**Expected P1.5.2 local result:** evaluation suite **120 passed**; identity **412 passed** (no regressions).

**Test file summary:**
- `tests/evaluation/test_capability_evidence.py` — 11 core object tests
- `tests/evaluation/test_capability_evidence_mapping.py` — 10 mapping tests
- `tests/evaluation/test_capability_evidence_aggregation.py` — 10 aggregation tests
- `tests/evaluation/test_capability_evidence_serialization.py` — 10 serialization/link tests
- `tests/evaluation/test_p152_scope_guards.py` — 5 anti-scope-creep tests

**Next:** P1.5.4 — Evaluation Criteria Schema.

### P1.5.1 Evaluation Object Model

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/evaluation/test_evaluation_objects.py tests/evaluation/test_evaluation_object_resolution.py tests/evaluation/test_evaluation_object_serialization.py tests/evaluation/test_p151_scope_guards.py -q
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation objects status --json
PYTHONPATH=src:. .venv/bin/python -m agentic_runtime.cli evaluation objects examples --json
```

**Expected P1.5.1 local result:** compileall passed; object model suite `40+ passed`; ruff passed; mypy passed. Evaluation total **74+ passed**. Identity total **412 passed** (no regressions).

**P1.5.1 object model tests:**
- closed-world enums (status, outcome, verdict, confidence, evidence quality, failure mode)
- criterion result validation (SUPPORTED requires evidence, BLOCKED requires blockers, FAILED requires failure modes)
- evaluation result validation (COMPLETED requires criteria, ERROR requires error failure mode)
- resolution rules (no criteria → insufficient, all passed → supported, blocked → blocked, conflicted → conflicted, required failure → rejected)
- categorical aggregation (blocked dominates, conflicted blocks supported, no numeric scoring)
- PASS does not imply VERIFIED; result object does not verify capability

**Test file summary:**
- `tests/evaluation/test_evaluation_objects.py` — 19 core object tests
- `tests/evaluation/test_evaluation_object_resolution.py` — 14 resolution/aggregation tests
- `tests/evaluation/test_evaluation_object_serialization.py` — 4 serialization tests
- `tests/evaluation/test_p151_scope_guards.py` — 5 anti-scope-creep tests
- `tests/evaluation/test_p15_integrated_seal.py` — 22 integrated seal tests (full seal, trace integrity, candidate boundary, anti-overclaim, seal contract validation, serialization)
- `tests/evaluation/test_p15_integrated_invariants.py` — 17 invariant tests (no-promotion, verification gate, structural safety)

**P1.5 is sealed. Next: P1.6.0 Policy Cards & Behavioral Contracts.**

### P1.9.30 Seal Criteria Repair

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/output_passport/test_passport_exit_seal_criteria_repair.py -q
.venv/bin/python -m pytest tests/output_passport/test_passport_exit_seal_repair.py -q
.venv/bin/python -m pytest tests/output_passport -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m pytest tests -q -k "output_passport or passport"
```

Report: `agent/reports/P1_9_30_SEAL_CRITERIA_REPAIR.md`

**Expected P1.9.30 criteria repair local result:** focused criteria repair **11 passed**; focused seal repair **15 passed**; output_passport **147 passed**; optional passport selector **153 passed, 5541 deselected**; compileall **PASS**; ruff **PASS**; mypy **PASS** (265 files).

**Seal result:** `SEALED` with qualification `SEALED_FOR_P1_CONTRACT_SCOPE` only. Production `LIVE` remains `UNAVAILABLE_LIVE_PATH`; actual `TRACE_VERIFIED` remains `UNAVAILABLE_TRACE_VERIFICATION`; P2 coding remains gated pending follow-up pre-P2 audit.

### P1.9.30 Exit Seal Focused Repair

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/output_passport/test_passport_exit_seal_repair.py -q
.venv/bin/python -m pytest tests/output_passport -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/agentic_runtime
.venv/bin/python -m pytest tests -q -k "output_passport or passport"
```

Report: `agent/reports/P1_9_30_SEAL_REPAIR.md`

**Expected P1.9.30 repair local result:** focused repair **15 passed**; output_passport **136 passed**; optional passport selector **142 passed**; compileall **PASS**; ruff **PASS**; mypy **PASS** (265 files).

**Seal result:** PARTIAL — production `LIVE_TESTED` path and actual `TRACE_VERIFIED` proof remain unavailable. P2 remains `NOT_READY_FOR_P2`.

### P1.9-B Output Passport Read Model / Test Harness / Binding Pack

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests/output_passport/test_passport_read_model_binding_pack.py -q
.venv/bin/python -m pytest tests/output_passport/ -q
.venv/bin/python -m pytest tests -q -k "output_passport or passport"
.venv/bin/python -m ruff check src/agentic_runtime/output_passport tests/output_passport
.venv/bin/python -m mypy src/agentic_runtime
```

Report: `agent/reports/P1_9_B_READ_MODEL_TEST_HARNESS_BINDING_PACK.md`

**Expected P1.9-B local result:** compileall **PASS**; focused P1.9-B **38 passed**; total output passport **71 passed**; broader passport selector **77 passed**; ruff **PASS**; mypy **PASS** (256 files).

**Next:** P1.9-C — Truth Boundary / Failure / Readiness Pack.

### P1.9-A Output Passport Identity / Attribution / Hash Pack

```bash
.venv/bin/python -m pytest tests/output_passport/test_passport_identity_attribution_hash.py -q
```

Report: `agent/reports/P1_9_A_PASSPORT_IDENTITY_ATTRIBUTION_HASH_PACK.md`

**Expected P1.9-A local result:** focused P1.9-A **33 passed**.
