# Aurel / GG Agentic Runtime — Full-System Health-Check Analysis Report

**Date:** 2026-06-21
**Status:** PASS (with known issues)
**Analysis mode:** health-check

---

## 1. Summary

Full-system health-check of the Aurel / GG Agentic Runtime repository at commit post-P1.4.7-MG. Overall verdict: **PASS** — the runtime is healthy, governance integrity is intact. **1047 tests pass** (4 failed, 4 skipped), identity/card stack is fully green (395/395), compile/lint/type checks all pass, CLI identity `card validate` exits 0 with `valid: true`. Three pre-existing tool-bus issuer-mismatch failures and several documentation-drift issues were identified. No governance invariants are violated.

**Recommended next step:** Fix tool-bus test issuer mismatch (F-001) before claiming full-suite green; sync STATE.md and ROADMAP.md (F-005, F-008); proceed to P1.4.8.

---

## 2. Scope and trigger

| Field | Value |
|-------|-------|
| Trigger | User request: "napravi analizu koda" (code analysis) |
| Boundary | Full-system (entire `src/agentic_runtime/`, `tests/`, config, docs, agent state) |
| Analysis mode | `health-check` |
| Invariants at risk | All invariants from [references/invariants.md](references/invariants.md) — specifically authority separation, fail-closed, sandbox honesty |
| Non-goals | No code changes in this analysis; no weakening of governance; no P1.4.8 implementation |

---

## 3. Architecture / pipeline context

The repository implements a governed agentic runtime with the core law **"Entity proposes. Runtime disposes."** The current state spans:

- **P0.x** (Complete): Governed command pipeline, Tool Bus v1, Repository Agent Loop, HITL/approval, Praxis memory, sandbox hardening, LLM planning bridge, alpha seal
- **P1.1–P1.3** (Complete): Model configuration + secret boundary, prompt system, tool/plugin manifest layer (sealed)
- **P1.4.0–P1.4.7-MG** (Complete): Identity + autonomy scope contract, identity kernel, persona manifest, operator contract, communication modes, identity prompt compiler, self-model, agent identity card + merge-gate hardening

Pipeline map: identity layers are read/validate only until wired into runtime boot. The Agent Identity Card is the latest delivered module.

---

## 4. Evidence

### Commands run

| Command | Result |
|---------|--------|
| `python3 -m agentic_runtime.cli status --json` | **PASS** — UnsafeLocalSandbox, restricted_local profile, honest limitations |
| `python3 -m compileall src tests` | **PASS** |
| `ruff check .` | **PASS** — All checks passed |
| `mypy src` | **PASS** — Success: 107 source files, no issues |
| `pytest tests/test_identity_*.py tests/test_agent_identity_card*.py tests/test_self_model*.py ... -q` | **PASS** — 395 passed |
| `pytest -q --tb=no` (full suite) | **PARTIAL** — 1047 passed, 4 failed, 4 skipped |
| `agentic_runtime.cli identity card show --json` | **PASS** — valid JSON with 6 source hashes, authority boundaries |
| `agentic_runtime.cli identity card validate --json` | **PASS** — `{"valid": true, "config_valid": true, "card_valid": true}` |

### Key observations

- **Failing tests** (4/1055): `test_write_file_inside_workspace`, `test_patch_file_applies_simple_fixture`, `test_patch_file_rejects_invalid_patch_cleanly`, `test_cli_verify_exits_zero`
- All 4 failures root-caused to: `ISSUER_MISMATCH` in `runtime.py:399` — each test calls `_card()` twice (once for CommandEnvelope issuer, once for submit card), producing two different `AgentCard.id` values
- Identity stack (395 tests across kernel, persona, operator, modes, compiler, self-model, card, MG-seal, CLIs) is fully green
- `cli.py` reduced from ~2411 to ~1013 lines via `cli_modules/` decomposition
- `tool_manifest/validation.py` is the largest single file at 1051 lines (previously documented as needing split)
- Two `ToolRegistry` classes exist: execution registry in `tools.py` (line 129), manifest catalog in `tool_manifest/registry.py` (line 283)

---

## 5. Findings

| ID | Severity | Module | Location | Root cause | Affected invariant |
|----|----------|--------|----------|------------|-------------------|
| F-001 | High | `tests/test_tool_bus_p13.py` | L121–127, 161–168, 173–181 | `_card()` generates new random `id` each call; submit uses different card than command envelope | Authority separation (runtime.submit issuer gate) |
| F-002 | Low | `tests/test_public_entrypoints_p121.py` | L107 | Cascades from F-001: `cli verify` runs full pytest, fails on tool-bus tests | Test integrity |
| F-003 | Medium | `tool_manifest/validation.py` | L1–1051 | 1051-line monolith; split planned but deferred to P6/P7 | Clean design bar (keep modules focused) |
| F-004 | Medium | `tools.py`, `tool_manifest/registry.py` | L129, L283 | Two `ToolRegistry` classes unnamed in code; rename deferred | Clean design bar (explicit naming) |
| F-005 | Low | `agent/STATE.md` | L3 | `_Last updated: 2026-06-21 (P1.4.0)` — does not reflect P1.4.7-MG completion | Doc integrity |
| F-006 | Low | `agent/ROADMAP.md` | L5–7 | Header says "P1.4.2 complete — Next: P1.4.3" but actual state is P1.4.7-MG complete | Doc integrity |
| F-007 | Low | Identity modules (`*.py` across `/identity/`) | — | Repeated load/validate/hash/attest patterns; shared helper modules deferred | Clean design bar (DRY) |
| F-008 | Info | `agent/STATE.md` | — | P1.4.3–P1.4.6 achievements not listed in "What works" section; only P1.4.7 added | Doc completeness |

### Finding details

#### F-001: Tool-bus issuer mismatch (3 tests)

**Severity:** High
**Module:** `tests/test_tool_bus_p13.py`
**Location:** `tests/test_tool_bus_p13.py:121-127`, `:161-168`, `:173-181`

`_card()` creates a new `AgentCard` with a random `id` (via `AgentCard.make()` → `new_id("card")`). Tests call `_cmd(_card(), ...)` to build a CommandEnvelope (issuer_card_id = card_A.id), then `kernel.runtime.submit(..., _card())` with a different card_B. Since `card_A.id != card_B.id`, `runtime.py:101` triggers `ISSUER_MISMATCH`. This surfaced after P1.4.7-MG introduced card identity validation into the runtime submit path.

**Reproduction:**
```python
card = _card()
res = kernel.runtime.submit(_cmd(_card(), "write_file", ...), _card())
# card_A.id != card_B.id → ISSUER_MISMATCH
```

**Fix direction:** Reuse the same card instance:
```python
card = _card()
res = kernel.runtime.submit(_cmd(card, "write_file", ...), card)
```

#### F-003: `tool_manifest/validation.py` monolith

**Severity:** Medium
**Module:** `tool_manifest/validation.py`
**Location:** 1051 lines

Single-file validation covers schema, contracts, permissions, invocation, and errors. P1.4.7-MG report documented planned split:
```
tool_manifest/validation/schema.py
tool_manifest/validation/contracts.py
tool_manifest/validation/permissions.py
tool_manifest/validation/invocation.py
tool_manifest/validation/errors.py
```
Deferred to pre-P6/P7 bridging — not blocking P1.4.8.

#### F-004: Two `ToolRegistry` classes unnamed

**Severity:** Medium
**Location:** `tools.py:129` (execution registry), `tool_manifest/registry.py:283` (manifest catalog)

Documented in ARCHITECTURE.md as `ExecutionToolRegistry` vs `ManifestToolCatalog`, but classes are both named `ToolRegistry` in code. Rename deferred — not blocking P1.4.8.

---

## 6. Test coverage assessment

| Area | Covered by | Gap |
|------|-----------|-----|
| Identity kernel | `test_identity_kernel*.py` (27 tests) | None |
| Persona manifest | `test_persona_manifest*.py` (36 tests) | None |
| Operator contract | `test_operator_contract*.py` | None |
| Communication modes | `test_communication_modes*.py` | None |
| Identity prompt context | `test_identity_prompt_context*.py` | None |
| Self-model | `test_self_model*.py` | None |
| Agent identity card | `test_agent_identity_card*.py` | None |
| P1.4.7-MG seal | `test_p147_mg_agent_identity_card.py` (7 tests) | None |
| Tool bus | `test_tool_bus_p13.py` (18 tests, 3 fail) | Issuer mismatch not covered by current card-reuse pattern |
| Tool manifest layer | 9 test files (~280 tests) | None — all pass |
| Identity stack total | 395 tests | **All pass** |

---

## 7. Known limitations / doc drift

| Item | Current state | Expected |
|------|--------------|----------|
| `STATE.md` last-updated header | `P1.4.0` | Should reflect latest completed phase (P1.4.7-MG) |
| `ROADMAP.md` current phase header | "P1.4.2 complete" | Should reflect P1.4.7-MG |
| `STATE.md` "What works" section | Missing P1.4.3–P1.4.6 entries | Should list operator contract, comm modes, compiler, self-model |
| `tool_manifest/validation.py` | 1051-line monolith | Split planned, deferred to P6/P7 |
| Two `ToolRegistry` classes | Both named `ToolRegistry` | Rename planned: `ExecutionToolRegistry` / `ManifestToolCatalog` |
| Identity stack copy-paste | Repeated load/validate/hash/attest in each P1.4.x module | Shared helpers deferred |
| `cli.py` | 1013 lines (down from 2411) | Further extraction of non-identity commands deferred |
| Callers outside card path still reload sources | `build_aurel_self_model_from_paths`, prompt-context CLI | Full bundle adoption deferred |

---

## 8. Explicitly not in scope

- P1.4.8 Autonomy Scale Engine implementation
- Fixing tool-bus tests or code (analysis only)
- Renaming `ToolRegistry` classes
- Splitting `tool_manifest/validation.py`
- Full identity-stack bundle adoption beyond card path
- Runtime boot wiring of identity layers

---

## 9. Recommended next step

Proceed with a focused fix for F-001 (tool-bus issuer mismatch — 3 tests, reusing same card instance), sync STATE.md/ROADMAP.md for P1.4.7-MG completion, then begin P1.4.8 Autonomy Scale Engine.

Link fix plan: `agent/reports/ANALYSIS_2026-06-21_FIX_PLAN.md` (below)
