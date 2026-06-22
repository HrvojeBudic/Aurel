# Pipeline Maps

Use these maps to trace bugs through the system and identify the owning module at each stage.

## Command pipeline

Full path from plan to observation:

```
Provider structured plan
  → Schema validation
  → PlanValidator                    [plan_validator.py]
  → CommandEnvelope                  [core_types.py]
  → Tool contract (input)            [tool_contracts.py, tools.py]
  → Budget precheck                  [budget.py]
  → Policy                           [policy.py]
  → Approval resolver                [approval.py]
  → HITL / approver                  [hitl.py]
  → Approval receipt trace           [trace.py]
  → Sandbox profile check            [sandbox_policy.py]
  → Budget charge                    [budget.py]
  → Sandbox snapshot (writes)        [sandbox.py]
  → Tool Bus execution               [tools.py]
  → Tool contract (output)           [tool_contracts.py]
  → State verifier                   [verifier.py]
  → Rollback (failed writes)         [sandbox.py]
  → Trace append                     [trace.py]
  → Governed memory update           [memory_governance.py, memory.py]
  → ObservationEnvelope + VerifierResult
```

Orchestration kernel: `runtime.py` (`AgenticRuntime.submit()`).

Entity-side planning: `entity.py` → proposes envelopes, does not dispose.

## Repository agent loop

Application-level loop — not a separate authority system:

```
RepoTaskRequest
  → RepoContextBuilder
  → CodeTaskPlanner / LLMRepoPlanner    [model_router.py, model_providers/]
  → RepoPlanValidator                   [repo_agent.py]
  → PatchExecutor                       [Runtime.submit → patch_file/write_file]
  → TestRunnerAdapter                   [Runtime.submit → run_tests/run_shell]
  → TestFailureAnalyzer
  → RepairLoop                          [bounded iterations]
  → CodeTaskReport
  → PraxisMetabolism                    [praxis.py]
```

All mutations and tests still pass through the command pipeline above.

## Tool manifest layer (declarative — P1.3)

Separate from executable Tool Bus:

```
Manifest file (JSON/YAML)
  → load_manifest_file                  [tool_manifest/loader.py]
  → validate (P1.3.1 rules)             [tool_manifest/validation.py]
  → quarantine decision                 [tool_manifest/quarantine.py]
  → register to catalog                 [tool_manifest/registry.py]
  → create invocation draft             [tool_manifest/invocation.py]
  → lifecycle event                     [tool_manifest/events.py]

  ✗ NO bridge to CommandEnvelope in P1.3
  ✗ NO runtime.submit or ToolRuntime dispatch
```

Future bridge (P6, not implemented):

```
ManifestToolCatalog → ToolInvocationDraft → Authority/Policy → CommandEnvelope → runtime.submit → ToolRuntime
```

## Identity layers (P1.4 — read/validate)

```
config/aurel/*.yaml
  → load + validate                     [identity/kernel*.py, persona*.py, etc.]
  → compute hash                        [identity/*_hash.py]
  → attest / safe summary               [identity/*_attestation.py, *_summary.py]
  → CLI                                 [cli.py identity subcommands]

  ✗ NOT wired into runtime boot yet (except read/validate CLI)
```

## Prompt system (P1.2)

```
prompts/**/*.yaml
  → PromptRegistry load + validate      [prompt_system.py]
  → variable check (fail closed)
  → render template
  → PromptTraceSummary (no raw prompt stored)
```

## Model configuration (P1.1)

```
agent/config/ or _default_config/
  → ModelConfigBundle load              [model_config.py]
  → provider selection                  [model_router.py]
  → secret resolution (env only)        [secrets.py]
  → structured plan from provider       [model_providers/]
```

## Debugging: where to look first

| Pipeline stage | Primary modules | Test patterns |
|----------------|-----------------|---------------|
| Plan rejected | `plan_validator.py`, provider schemas | `test_plan_*`, provider tests |
| Policy denied | `policy.py`, `approval.py` | `test_policy_*`, `test_approval_*` |
| Sandbox blocked | `sandbox_policy.py`, `sandbox.py`, `canonical_path.py` | `test_sandbox_*` |
| Tool failed | `tools.py`, `tool_contracts.py` | `test_tool_*` |
| Verify failed | `verifier.py` | `test_verifier_*`, integrity tests |
| Trace missing | `trace.py` | `test_trace_*` |
| Memory rejected | `memory_governance.py` | `test_memory_*` |
| Repo plan invalid | `repo_agent.py` (RepoPlanValidator) | `test_repo_*` |
| Manifest invalid | `tool_manifest/validation.py` | `test_tool_manifest_*` |
| Identity invalid | `identity/*_validation.py` | `test_identity_*`, `test_persona_*` |
| Prompt invalid | `prompt_system.py` | `test_prompt_*` |
