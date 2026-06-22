# Sample Analysis — Sandbox Path Violation

Worked example showing scope → evidence → module scan → findings → fix plan. Hypothetical scenario for output quality reference.

---

## Phase 2 — Scope

| Field | Value |
|-------|-------|
| Trigger | `test_sandbox_rejects_path_outside_workspace` fails — write allowed outside workspace root |
| Boundary | Sandbox profile enforcement (`sandbox_policy.py`, `ProfiledSandbox`) |
| Invariants at risk | Sandbox boundary, fail closed, no silent downgrade |
| Analysis mode | `bug` |
| Non-goals | No weakening of sandbox checks; no switch to unsafe_local_demo |

---

## Phase 3 — Evidence

```bash
python -m agentic_runtime.cli status --json
# sandbox_profile: restricted_local, backend: ProfiledSandbox

PYTHONPATH=src:. pytest tests/test_sandbox_p17.py::test_sandbox_rejects_path_outside_workspace -q
# FAILED — write to /tmp/evil.txt was not blocked

python3 -m compileall src tests
# PASS
```

Key observation: `SandboxPolicy.evaluate_path()` returns `allowed=True` for paths resolved relative to parent directory when workspace root check uses string prefix instead of canonical path comparison.

Location: `src/agentic_runtime/sandbox_policy.py:142`

---

## Phase 4 — Module Scan

| Stage | Module | Finding |
|-------|--------|---------|
| Sandbox profile check | `sandbox_policy.py` | Path prefix check bypassed via `../` traversal |
| Path truth | `canonical_path.py` | `resolve_canonical()` not called before prefix check |
| Tool Bus execution | `tools.py` | Not reached — policy gate should block earlier |
| Tests | `tests/test_sandbox_p17.py` | Test exists but uses simple relative path, not traversal variant |

Coupling risk: `ProfiledSandbox` delegates to `SandboxPolicy` — fix must stay in policy layer, not sandbox backend.

---

## Phase 5 — Findings

| ID | Severity | Module | Location | Root cause | Affected invariant |
|----|----------|--------|----------|------------|-------------------|
| F-001 | Critical | `sandbox_policy.py` | `:142` | Prefix check without canonical resolution allows traversal escape | Sandbox boundary |
| F-002 | Medium | `tests/test_sandbox_p17.py` | — | Missing traversal variant test case | Test coverage |

---

## Deliverable A — Analysis Report (abbreviated)

**Status:** FAIL — sandbox boundary bypass via path traversal

**Summary:** `SandboxPolicy.evaluate_path()` uses string prefix matching without canonical path resolution, allowing writes outside the workspace root via `../` sequences. One Critical finding (F-001), one Medium coverage gap (F-002). Fix belongs in `sandbox_policy.py` with canonical path integration.

**Recommended next step:** Proceed to fix plan Phase 0.

---

## Deliverable B — Fix Plan (abbreviated)

### Objective

Block path traversal in `SandboxPolicy.evaluate_path()` using canonical path resolution before workspace root check.

### Constraints

- Sandbox boundary must hold for all path variants including `../`, symlinks, and absolute paths
- No silent downgrade to unsafe mode
- Fail closed on unresolvable paths

### Phase 0 — Reproduce

Add `test_sandbox_rejects_traversal_escape` in `tests/test_sandbox_p17.py`:

```python
def test_sandbox_rejects_traversal_escape(profiled_sandbox):
    result = profiled_sandbox.check_write("../../../etc/passwd")
    assert not result.allowed
```

**Acceptance:** Test fails before fix.

### Phase 1 — Minimal fix

Modify `src/agentic_runtime/sandbox_policy.py`:

- Call `resolve_canonical(path, workspace_root)` before prefix check
- Return `allowed=False` when resolved path is outside workspace root or resolution fails

**Acceptance:** F-001 resolved, Phase 0 test passes, existing sandbox tests pass.

### Phase 2 — Validation

```bash
PYTHONPATH=src:. pytest tests/test_sandbox_p17.py -q
PYTHONPATH=src:. pytest -q
```

### Acceptance criteria

- [ ] F-001 resolved — traversal paths blocked
- [ ] F-002 resolved — traversal test added
- [ ] All sandbox tests pass
- [ ] Full suite passes
- [ ] No governance invariants violated

---

> Ready for implementation — invoke `debug-aurel` or proceed with Phase 0.
