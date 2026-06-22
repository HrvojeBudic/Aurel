# Non-Negotiable Invariants

Every finding and fix plan must preserve these invariants. Flag any finding that violates them as **Critical**.

## Core law

```text
Entity proposes. Runtime disposes.
```

The entity may propose `CommandEnvelope` actions. The runtime alone decides permission, execution, verification, trace, and memory.

## Authority separation

- **Capability ≠ permission ≠ authority** — three distinct concepts; never conflate.
- Tool visibility, tool access, manifest loading, and prompt rendering **do not grant execution rights**.
- Tool registration is not trust. Registry entries record state; trust is evaluated separately.
- Tool invocation draft is not execution. Drafts are proposals only.
- Manifest loading is not registry activation. Parsed manifests are not registered with Tool Bus.
- Identity is not policy. Persona is not authority. Communication mode is not permission.
- Operator remains final authority; Aurel cannot self-escalate autonomy.

## Fail closed

Invalid or unsafe input must be rejected, not silently accepted:

- Invalid plans, empty plans, unsupported plans
- Unsafe paths, traversal attempts, secret path access
- Missing prompt variables, forbidden prompt requests
- Bad manifests, blocking validation issues, unknown providers
- Unverifiable state, missing required fields
- Critical identity/persona invariant violations (fail_boot)

## Sandbox honesty

- `UnsafeLocalSandbox` is demo/trusted-only — never describe as production security boundary.
- Sandbox profile checks must **not** silently downgrade to weaker enforcement.
- Docker/Bubblewrap profiles must be honest about availability — no hidden fallback to unsafe mode.

## Trace and secrets

- Trace records must be honest — record fallback reasons, do not hide them.
- Prompt rendering must not persist raw prompt text by default.
- Secrets come from env only — never commit, log, or expose in trace/output.
- Real provider support must preserve `local_only` and secret-from-env boundaries.

## Test integrity

- Protected tests must **not** be weakened to satisfy `TestIntegrityVerifier`.
- Do not delete, skip, or mutate tests to make a fix pass without explicit user approval.
- Subprocess timeout test skips in restricted CI sandboxes are environment facts, not proof of behavior.

## Memory and praxis

- Trace is not memory.
- Praxis outputs are candidates with evidence — not canon or automatic truth.
- Memory promotion requires conservative gates — never auto-promote canon.
- Reflex eligibility checks document that runtime governance remains mandatory.

## Repository agent

- LLM/repository planning may propose work only.
- Patch and test execution must go through `AgenticRuntime.submit()` → Tool Bus → Approval → Sandbox → Verifier.
- The LLM never receives tool authority and never executes tools directly.

## Tool manifest boundary (P1.3.9 sealed)

- No bridge in P1.3: `ToolInvocationDraft` does not become `CommandEnvelope`.
- No `runtime.submit` or `ToolRuntime` calls from `tool_manifest/`.
- Lifecycle trace events are separate from P0.6 hash-chain ledger.
- Quarantine is isolation, not deletion — objects remain auditable.

## Clean design bar (for fix plans)

When proposing fixes:

1. Keep each gate responsible for one decision.
2. Return structured results — not prose or hidden booleans.
3. Prefer explicit enums and small dataclasses over loose dicts.
4. Keep fallbacks honest and traceable.
5. Add tests that encode the invariant, not only the happy path.
6. Leave documentation and reports consistent when behavior changes.
7. Use existing dataclasses, enums, schemas, validators before adding new shapes.
8. Avoid broad refactors unless explicitly scoped in the fix plan.

## Forbidden shortcuts

Never propose these as fixes:

- Weakening policy, sandbox, verifier, or trace checks
- Bypassing approval or HITL gates
- Granting execution rights via manifest or prompt changes alone
- Storing raw prompts or secrets in trace/memory
- Auto-promoting praxis candidates to canon
- Renaming core architecture terms (`Entity`, `Runtime`, `CommandEnvelope`, etc.)
