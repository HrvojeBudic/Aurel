# ADR-004: AurelTraceLog Source of Truth

Date: 2026-06-21

## Decision

AurelTraceLog is the canonical append-only hash-chained event source. Ledger, Evidence, RuntimeState, Evaluation, Mneme and Shell are projections over AurelTraceLog, not independent sources of truth.

If it is not represented in AurelTraceLog, it is not canonical.

## Context

Aurel now has evidence, evaluation, runtime, memory, ledger, replay and shell-adjacent surfaces. Those surfaces can produce useful derived records, but future phases need one canonical source for what happened so downstream records cannot become competing truths.

P1.5.10X adds a small contract seed before P1.5.11A. It defines canonical trace events, stable event references, projection bindings and chain verification without implementing the full workflow runtime.

## Problem

Without a single source of truth, Aurel can drift into inconsistent states:

- Ledger says one thing happened.
- Evaluation claims another result.
- Memory promotes a third interpretation.
- Shell or report projections carry stale or unauditable state.

That ambiguity makes replay, audit, evidence binding, output passports and future memory promotion unreliable.

## Alternatives Considered

1. Treat Ledger as canonical.
   Rejected because ledger entries are one projection of events, not the full event source for runtime, evaluation, shell, memory and report surfaces.

2. Treat each subsystem as independently canonical.
   Rejected because this preserves competing truths and makes cross-subsystem replay ambiguous.

3. Make trace_id content-addressed.
   Rejected because trace_id is a stable run or workflow identity. Content-addressing belongs on event_hash now and on replay or causal graph artifacts later.

4. Defer source-of-truth rules until full AurelFlow.
   Rejected because later evidence, memory and evaluation contracts need a binding target now.

## Final Rule

AurelTraceLog is the only canonical append-only hash-chained event source.

TraceEvent is immutable after append through the public API. Every TraceEvent has deterministic payload_hash and event_hash values. The first event in a trace uses `GENESIS` as previous_event_hash. Later events use the previous event_hash.

trace_id is stable identity and is not content-addressed. event_hash is content-addressed from canonical event content. Future causal_graph_hash and replay_report_hash may be content-addressed later.

Every serious future evidence, evaluation, memory, ledger, shell, report, output passport or replay record must be able to bind back to a canonical TraceEventRef.

## Consequences

- Projection records cannot claim canonical status.
- Ledger, Evidence, RuntimeState, Evaluation, Mneme, Shell and Reports are derived artifacts.
- Evidence and evaluation records that cannot bind to a TraceEventRef are not authoritative.
- Chain integrity can be verified through deterministic event hashes.
- Replay can later build causal graph and report hashes over canonical TraceEvents.

## Non-goals

P1.5.10X does not implement full AurelFlow, full AurelExec, workflow scheduling, approval pause, retry/recovery, real tool execution, real shell execution, real LLM execution, full Ledger migration, full Mneme memory lifecycle, Noesis, SoulIntegrityReport or Golden Thread A.

The patch only establishes canonical trace integrity and projection boundaries.
