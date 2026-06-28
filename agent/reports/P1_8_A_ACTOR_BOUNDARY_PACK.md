# P1.8-A — Actor Boundary Pack

**Date:** 2026-06-27
**Task:** P1.8-A — P1.8.17-P1.8.22 Actor Boundary Pack
**Status:** COMPLETE
**Roadmap:** v5.5 actor-boundary remap over v5.1 Integration-First

## Summary

P1.8-A implements the operator-authorized remap from the local v5.1 P1.8.17 projection handoff to **P1.8-A — P1.8.17-P1.8.22 Actor Boundary Pack**.

The pack is deterministic, versioned, JSON-safe, side-effect-free, and contract-only. It defines actor/state/proposal boundaries for Aurel state actor, agent worker, CRO authority/state bridge, SYSTEM root, BusinessEnvironment, and tool/workflow/memory trigger proposals.

## Implementation

### Files created

- `src/agentic_runtime/delegation/actor_boundary.py`
- `tests/delegation/test_actor_boundary.py`
- `agent/reports/P1_8_A_ACTOR_BOUNDARY_PACK.md`

### Files modified

- `src/agentic_runtime/delegation/__init__.py`
- `agent/ACTIVE_TASK.md`
- `agent/ROADMAP.md`
- `agent/STATE.md`
- `agent/DECISIONS.md`
- `agent/REPORTS.md`

## Coverage Matrix

| Checkpoint | Contract | Evidence | Boundary |
|------------|----------|----------|----------|
| P1.8.17 | `AurelStateActorBoundary` | `aurel_state_actor_boundary_hash` | Aurel state actor can own state; agent worker cannot |
| P1.8.18 | `AgentWorkerBoundary` | `agent_worker_boundary_hash` | Agent is worker-only; no self-authorization or SYSTEM entry |
| P1.8.19 | `CROAuthorityStateBridge` | `cro_authority_state_bridge_hash` | CRO depends on operator/Custos/runtime/SYSTEM; no self-authorization or evolution activation |
| P1.8.20 | `SystemRootBoundaryReference` | `system_root_boundary_reference_hash` | SYSTEM root is operator-only; agent/tool/workflow entry unavailable |
| P1.8.21 | `BusinessEnvironmentActorBoundary` | `business_environment_actor_boundary_hash` | BusinessEnvironment can hold bounded state refs only; no permission grant or high-impact execution |
| P1.8.22 | `TriggerProposalBoundary` | `trigger_proposal_boundary_hash` | Tool/workflow/memory triggers are proposal-only; no permission, execution, or memory write |

## Data Contracts

- Enums: `DelegationActorBoundaryActorKind`, `DelegationActorBoundaryKind`, `DelegationAuthorityScope`, `DelegationActorStateRole`, `DelegationProposalOriginKind`, `DelegationBoundaryTruthLabel`, `DelegationBoundaryUnavailableReason`, `DelegationActorBoundaryStatus`
- Contracts: `AurelStateActorBoundary`, `AgentWorkerBoundary`, `CROAuthorityStateBridge`, `SystemRootBoundaryReference`, `BusinessEnvironmentActorBoundary`, `TriggerProposalBoundary`
- Read model/result: `DelegationActorBoundaryCheckpointRead`, `DelegationActorBoundaryReadModel`, `DelegationActorBoundaryPackResult`
- Builders: `build_default_delegation_actor_boundary_read_model()`, `build_p1_8_a_actor_boundary_pack_result()`, plus one builder per checkpoint contract
- Serialization: `serialize_delegation_actor_boundary_read_model()`, `serialize_delegation_actor_boundary_pack_result()`

## Truth Labels

- Checkpoint contracts: `CONTRACT_ONLY`
- Default read model/result source: `DEV_FIXTURE`
- No default `LIVE`
- No default `TRACE_VERIFIED`

## Side Effects

All `DelegationActorBoundarySideEffects` booleans are false:

```text
policy_decision_emitted = False
custos_decision_emitted = False
approval_created = False
permission_granted = False
execution_started = False
ledger_written = False
global_trace_written = False
memory_written = False
workflow_executed = False
tool_executed = False
system_boundary_mutated = False
runtime_mutated = False
```

## Explicit Unavailable Surfaces

- CLI/Shell/TUI binding is UNAVAILABLE; owned by P1.8.28 Delegation Shell/CLI/TUI Binding.
- Runtime enforcement is UNAVAILABLE; P1.8-A is contract-only and enforcement belongs to later runtime/policy layers.
- Policy/Custos decisioning, approval, permission grants, runtime execution, trace/Ledger writes, memory writes, tool/workflow execution, SYSTEM entry, Output Passport/P1.9, and TRACE_VERIFIED are unavailable.

## Deliberately Not Implemented

- Runtime enforcement
- Policy/Custos calls or decisions
- Approval, permission, or authority grants
- Execution, tool dispatch, workflow execution, or high-impact action execution
- Memory writes
- Ledger writes or global trace writes
- CLI/Shell/TUI binding
- SYSTEM mutation or runtime mutation
- P1.8-B behavior

## Validation

```bash
.venv/bin/python -m compileall src tests
# PASS

.venv/bin/python -m pytest tests/delegation/test_actor_boundary.py -q
# 17 passed

.venv/bin/python -m pytest tests -q -k "actor_boundary or delegation"
# 1028 passed, 4453 deselected

.venv/bin/python -m ruff check src tests
# All checks passed

.venv/bin/python -m mypy src/agentic_runtime
# Success: no issues found in 248 source files
```

## Compatibility Note

The broader delegation selector exposed a package-level export collision for `build_delegation_authority_ref`: P1.8.0 foundation and P1.8.4 authority binding both publish that historical name. `agentic_runtime.delegation.__init__` now dispatches the package-level name by call shape so both existing P1.8.0 and P1.8.4 tests pass without changing either underlying module.

## Remaining Risk

P1.8-A proves deterministic contract/read-model behavior only. It does not prove runtime enforcement, trace verification, Ledger finality, Shell/CLI/TUI binding, or P1.8-B behavior.

## Next Recommended Task

P1.8-B.
