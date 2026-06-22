---
name: project-agentic-runtime
description: The agentic_runtime governed agent runtime — architecture, the central pipeline, and where the security boundary lives
metadata:
  type: project
---

`agentic_runtime` (pkg under `src/agentic_runtime/`, version 0.2.0): a governed agentic OS. Central law: "the entity proposes; the runtime disposes." Entities cannot act — they hand a `CommandEnvelope` to `AgenticRuntime.submit()`, which runs ONE governed pipeline (runtime.py): policy → HITL approval → budget → sandbox snapshot → tool exec → state verifier → rollback-on-fail → hash-chained trace → governed memory write.

**Why:** anti-reward-hacking + capability!=permission!=authority governance. Verification is state-based (re-reads real FS), never claim-based.

**How to apply:**
- `build_runtime()` / `Kernel` in `__init__.py` wire everything. `Kernel.spawn(card)` -> `AgenticEntity`.
- Security boundary is the sandbox (sandbox.py): `UnsafeLocalSandbox` is explicitly NOT a boundary (demo only, needs allow_unsafe); `Bubblewrap`/`Docker` are hard isolation. `ProfiledSandbox` (sandbox_policy.py) wraps a backend and enforces path/exec policy at the FS boundary.
- Path safety flows through `CanonicalPathResolver` everywhere (prevents `../` escapes). Policy + sandbox_policy + tools all canonicalize.
- Tool contracts (tool_contracts.py) gate input BEFORE policy/exec and output BEFORE verified-success. "No contract -> no execution."
- Core data types (CommandEnvelope, ObservationEnvelope, records) live in core_types.py.

The P1.5 evaluation subsystem (`contracts/`, `evaluation/`, `golden_threads/`) is a separate in-progress effort with its own tests; see [[reference-testing]].
