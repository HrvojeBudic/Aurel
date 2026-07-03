# P4-EXEC-C — Worker / Queue / Bus / Checkpoint Runtime Shape (Lean Validation)

## 1. Result Header

**DONE — MANAGED_SHAPE_AROUND_PROVEN_BRIDGE / QUEUE_IS_NOT_SCHEDULER / ONE_LOCAL_SLOT_NOT_A_POOL / LOCAL_LOG_NOT_A_BUS / CHECKPOINT_REF_NOT_A_PERSISTENCE_ENGINE / ROLLBACK_REF_NOT_ROLLBACK_EXECUTION / RECOVERY_UNAVAILABLE / BRIDGE_REUSED_NO_SECOND_PATH / P4_EXEC_D_NEXT**

Date: 2026-07-03. Roadmap: Aurel Roadmap v5.5, P4.7–P4.9. Lean validation edition: focused C-pack tests + compileall + ruff on touched paths only; no full pytest, no broad regression globs, no full-project mypy (deliberate, per dispatch).

## 2. Pack Scope

P4-EXEC-C wraps the proven P4-EXEC-B submit in minimal local runtime management: `ExecQueueEntry` (admitted + leased jobs waiting for a local claim), one local in-process `WorkerSlot` + `QueueClaim` (P4.7), `ExecutionMessage`/`LocalExecutionMessageLog` for local causality (P4.8), `ExecutionCheckpointRef`/`ExecutionRollbackRef` boundaries (P4.9 DeltaBox-lite), the `run_claimed_queue_entry_once` managed helper reusing `ExecRuntimeBridge` as-is, `ManagedRuntimeResult`, `ManagedRuntimeProjection`, and five fail-closed boundary proofs.

## 3. Canon / Preflight

Branch `master`, clean at start, HEAD `a0f2a6d` (P4-EXEC-B hash record). Canon read: ACTIVE_TASK (P4-EXEC-B complete, P4-EXEC-C next), ROADMAP pointer, STATE, ARCHITECTURE, DECISIONS, TESTS, REPORTS, both P4-EXEC-A/B reports, full aurel_exec source and tests. No canon conflicts.

## 4. P4-EXEC-B Prerequisite Confirmation

`agent/reports/P4_EXEC_B_RUNTIME_SUBMIT_BRIDGE.md` exists; commits `57f39e2` + `a0f2a6d` in history. `ExecRuntimeBridge` was reused exactly as shipped — zero edits to `exec_runtime_bridge.py`, `exec_outcome.py`, `exec_trace_binding.py`, `exec_session.py`, `exec_job.py`, `exec_lease.py` in this pack. The managed helper calls `bridge.submit_once(...)` with the same signature B proved against the real kernel.

## 5. Operational Debt Guard Proof

Avoided: worker pool/registry, remote/distributed workers, async dispatcher (`asyncio`/`threading` absent from C modules, sweep-tested), distributed queue, event streaming, service bus, pub/sub, any transport (NATS/gRPC/WebSocket/HTTP), checkpoint persistence engine, rollback executor, recovery/retry engine, backpressure/concurrency, P3 scheduler duplication, P8 router, mode profiles, Shell/React/API. Four new modules + one projection class; the managed helper is one function orchestrating existing pieces.

Why minimal: every object either enqueues an admitted + leased job, claims it with the single local slot, records local causality, names a checkpoint boundary, records rollback as not-executed, reuses the bridge, or projects the shape.

How P4-EXEC-D/E ambiguity was reduced: Exec-D gets a managed substrate (queue entry → claim → managed run) to plug mode profiles into — the bridge's `SUPPORTED_BRIDGE_EXECUTION_MODES`/`SUPPORTED_BRIDGE_TOOLS` remain the single widening point. Exec-E gets exactly the attachment surfaces it needs: pre/post checkpoint refs with real stable hashes, a not-executed rollback ref naming P4-EXEC-E as owner, ERROR_RECORDED causality messages, and the no-retry rule marking where bounded recovery begins.

## 6. Managed Runtime Shape Proof

`run_claimed_queue_entry_once`: validates claim coherence (queue entry / worker slot / job / lease ids + CLAIMED states, fail-closed with zero kernel calls on any block) → records ATTEMPT_READY → creates the PRE_ATTEMPT checkpoint ref (stable hash over the real local job/lease/session/attempt view) → marks entry/claim/slot RUNNING → calls the existing `ExecRuntimeBridge.submit_once` once → records ATTEMPT_SUBMITTED + OUTCOME_RECORDED (+ ERROR_RECORDED on failure) → POST_ATTEMPT checkpoint ref over the outcome → not-executed rollback ref → completes/fails the queue entry → releases the slot → returns `ManagedRuntimeResult` (+ full `ManagedRuntimeExecution` bundle). Fake-kernel test asserts exactly one submit call; failure path preserves FileNotFoundError, marks the entry FAILED, and still releases the worker.

## 7. No Worker Platform Proof

One `create_local_worker_slot()` producing one IN_PROCESS_LOCAL slot; `is_worker_pool` unconstructibly True; no pool_size/spawn/scale surface (tested); non-local `WorkerKind`s constructible only with status UNAVAILABLE and structurally unable to claim; `NoWorkerPoolProof` (single_local_worker_slot_only locked True) + `NoRemoteWorkerProof` fail-closed.

## 8. No Transport Bus Proof

`LocalExecutionMessageLog` is an immutable local tuple log (append returns a new log — the old one is untouched, tested); `is_transport_bus`/`publishes_network_events`/`pubsub_available`/`has_subscribers` unconstructibly True; no publish/subscribe/route/emit/broadcast surface (tested); messages carry `is_network_event`/`routes`/`executes` locked False; C modules import no asyncio/threading/socket (sweep-tested); `NoTransportBusProof` fail-closed.

## 9. No Checkpoint Persistence / Rollback Execution Proof

A checkpoint ref claiming availability without a real stable hash is unconstructible (CHECKPOINT_INVALID); `is_persistence_engine`/`executes_rollback` locked False; no persist/save/store/restore surface. `ExecutionRollbackRef.rollback_executed` and `rollback_available` are unconstructibly True in this pack with the unavailable reason naming P4-EXEC-E under P9 authority; `NoRollbackExecutionProof` + `NoRecoveryEngineProof` fail-closed.

## 10. Roadmap Coverage Matrix

| Range | Status | Evidence |
|---|---|---|
| P4.7 Worker Slot / Queue Claim | DONE | `exec_queue.py` + `exec_worker.py`; 12 tests |
| P4.8 Execution Bus / Local Message Kernel | DONE | `exec_messages.py`; 6 tests |
| P4.9 Checkpoint / Rollback / DeltaBox-lite | DONE | `exec_checkpoint.py`; 6 tests |
| Managed shape + projection | DONE | `exec_worker.py` helper + `ManagedRuntimeProjection`; 6 tests |

## 11. P4.7 In-Process Worker Slot / Queue Claim — DONE

`ExecQueueEntry` (8-state closed-world `ExecQueueState` with a deterministic transition map; only LEASED/SESSION_BOUND jobs with their own bound, currently valid lease can enter; CLAIMED entries must reference their slot; `schedules_workflows`/`executes`/`dispatches_remotely` locked False). `WorkerSlot`/`WorkerKind`/`WorkerSlotStatus` as in §7. `claim_queue_entry` is deterministic and fail-closed: non-local kind → WORKER_KIND_UNAVAILABLE; busy slot or non-PENDING entry → DOUBLE_CLAIM_BLOCKED; foreign lease → CLAIM_MISMATCH; expired/revoked lease → LEASE_EXPIRED/LEASE_REVOKED. `release_worker_slot`/`fail_worker_slot` close claims with reasons. Truth labels inherit the job's (DEV_FIXTURE in tests); a claim is not execution (`is_execution` locked False).

## 12. P4.8 Execution Bus / Local Message Kernel — DONE

13-kind closed-world `ExecutionMessageKind` (exact set tested); deterministic message ids; immutable log with append/list/filter-by job/session/attempt/queue-entry helpers. Local causality before any distributed bus — the "execution bus" of this pack is honestly a local read-model log, and every bus-shaped claim is unconstructible.

## 13. P4.9 Checkpoint / Rollback / DeltaBox-lite — DONE

Pre/post attempt checkpoint refs over real local state views (deterministic `stable_hash`; same source ⇒ same hash/id); `ExecutionCheckpointKind` closed-world (PRE_ATTEMPT/POST_ATTEMPT/SESSION_SNAPSHOT/OUTCOME_SNAPSHOT/UNAVAILABLE/ERROR); rollback refs bound to checkpoint boundaries with execution structurally impossible. These are the named boundaries P4-EXEC-E recovery and P5 verification attach to later.

## 14. ExecQueueEntry Proof — see §11; tests `test_exec_queue.py` (6).

## 15. WorkerSlot Proof — see §7/§11; tests `test_exec_worker_slot.py` (6).

## 16. QueueClaim Proof — double claim blocked both ways (busy slot, claimed entry); lease guards; release/fail deterministic; tests in `test_exec_worker_slot.py`.

## 17. LocalExecutionMessageLog Proof — see §8; tests `test_exec_messages.py` (6).

## 18. ExecutionCheckpointRef Proof — see §9/§13; tests `test_exec_checkpoint_refs.py` (6).

## 19. ExecutionRollbackRef Proof — rollback_executed/rollback_available unconstructibly True; reason + P4-EXEC-E owner mandatory; tests in `test_exec_checkpoint_refs.py`.

## 20. Managed Runtime Path Proof

Operator-testable path proven in `test_exec_managed_runtime_shape.py`: admitted + leased job → queue entry → local claim → ATTEMPT_READY/CHECKPOINT_BOUND messages → pre checkpoint → existing bridge (1 kernel call, counted) → outcome → post checkpoint → rollback ref → worker release → `ManagedRuntimeResult` with the exact ordered message-id chain. Blocked shapes (released claim, foreign claim) raise before any kernel call with `submit_calls == []`.

## 21. Projection Proof

`ManagedRuntimeProjection` (read-only, `read_only` locked True): queue/worker/claim state, local messages, checkpoint refs, rollback refs, truth labels, unavailable reasons; 18 platform-shaped availability booleans structurally False (scheduler, pool, remote/distributed, transport/publish/pubsub, persistence engine, rollback available/executed, recovery/retry/concurrency, P5, P9, Shell/React/API); `single_local_worker_slot_only` locked True; `checkpoint_ref_available=True` without actual refs unconstructible. The B-era `ExecProjection` is unchanged; its `worker_queue_available=False` now means "no worker/queue *platform*" — the local shape is projected by `ManagedRuntimeProjection` (recorded in DECISIONS).

## 22. No Remote/Distributed Worker Proof — see §7; kinds structurally UNAVAILABLE and claim-incapable; proof object fail-closed.

## 23. No Recovery Engine Proof — no retry anywhere (B's no-resubmit rule still guards the attempt); `NoRecoveryEngineProof` fail-closed naming P4-EXEC-E; managed helper contains no retry/repair branch — a failed run releases the worker and preserves the failure.

## 24. Lean Tests / Validation

```
.venv/bin/python -m compileall src/agentic_runtime/aurel_exec tests/aurel_exec → PASS
.venv/bin/python -m pytest tests/aurel_exec/test_exec_queue.py
  tests/aurel_exec/test_exec_worker_slot.py tests/aurel_exec/test_exec_messages.py
  tests/aurel_exec/test_exec_checkpoint_refs.py
  tests/aurel_exec/test_exec_managed_runtime_shape.py -q → 30 passed
  (queue 6 · worker slot 6 · messages 6 · checkpoint refs 6 · managed shape 6)
.venv/bin/python -m ruff check src/agentic_runtime/aurel_exec tests/aurel_exec → All checks passed
git status --short → only in-scope changes; clean after commit
```

Deliberately not run (lean mandate): full pytest, the full `tests/aurel_exec` suite, runtime/tool/sandbox/trace regression globs, full-project mypy. Changes to shared files were additive only (`exec_errors.py` new codes, `exec_projection.py` new class + imports, `__init__.py` new exports); A/B test compatibility is expected but was not re-executed in this run — honest note, not a verified claim.

## 25. Files Created / Modified

Created: `src/agentic_runtime/aurel_exec/{exec_queue,exec_worker,exec_messages,exec_checkpoint}.py`; `tests/aurel_exec/{test_exec_queue,test_exec_worker_slot,test_exec_messages,test_exec_checkpoint_refs,test_exec_managed_runtime_shape}.py`; this report.

Modified: `aurel_exec/{__init__,exec_errors,exec_projection}.py`; `agent/{REPORTS,STATE,ACTIVE_TASK,ROADMAP,ARCHITECTURE,DECISIONS,TESTS}.md`.

Untouched: `exec_runtime_bridge.py`, `exec_outcome.py`, `exec_trace_binding.py`, `exec_session.py`, `exec_job.py`, `exec_lease.py`, `exec_admission.py`, `exec_types.py`, all runtime/kernel sources, all web/frontend paths.

## 26. What Was Deliberately Not Implemented

Worker pool; remote/distributed workers; async dispatcher; distributed queue; network/event/service bus; pub/sub; NATS/gRPC/WebSocket/HTTP transport; checkpoint persistence engine; rollback execution; recovery/retry engine; backpressure/concurrency; P4.10+ execution modes; verifier hooks; algedonic signals; harness telemetry; P5 trace verification; P8 routing; P9 enforcement; Shell UI/React/API server; database/event store; service mesh.

## 27. Remaining Risks

- Queue/slot/claim objects are immutable snapshots the caller must thread; a stateful runtime shell (who owns "the" slot instance over time) is Exec-D+ work.
- Checkpoint hashes cover local read-model views, not sandbox state — a real state snapshot discipline (P3-FLOW-F canon) must be bound in before rollback execution ever arrives.
- `ManagedRuntimeProjection.worker_slot_state`/`claim_state` are string values (duck-typed builder); Exec-D may want typed fields when the shape stabilizes.
- The semantic split between `ExecProjection.worker_queue_available=False` (platform) and the local shape projection must be kept documented to avoid misreading.
- Lean validation skipped the A/B suites this run; the next non-lean pack should re-run the full aurel_exec suite.

## 28. Next Pack: P4-EXEC-D

Execution Modes Registry / Tool / Model / Terminal Profiles — widen the bridge's single supported path into a registry of governed mode profiles on top of the managed queue/claim/message/checkpoint substrate, keeping unsupported profiles structurally UNAVAILABLE until each is proven.

## 29. Commit Hash

`a6dc80b` — `feat(aurel-exec): add managed runtime queue and checkpoint shape` (20 files, +2343/−6).

## 30. Final Git Status

Clean after commit (`git status --short` empty); verified in the run that produced this report.
