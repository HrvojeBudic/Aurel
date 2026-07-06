# Governance Scale — G0–G5 (M6)

The governance scale is a **manually chosen** spectrum of autonomy, selected per
agent, per task, or per system, along one axis:

```
ABSOLUTE GOVERNED (G0)  ⟷  HERETIC (G5, free from all discretionary gates)
```

Each level is a *preset over knobs that already exist* — the `AutoApprover` risk
envelope, the `GovernanceEnforcementConfig` mode, the sandbox/attestation
requirement (M0), and the anchored-trace requirement (M2). No new enforcement
mechanism is introduced; the scale names coherent points and materializes them.

## The levels

| Level | HITL (human from) | Reversibility cap | Enforcement | Sandbox | Anchor | Trace |
|-------|-------------------|-------------------|-------------|---------|--------|-------|
| **G0** ABSOLUTE | ≥ R1 | R2 | fail-closed | required+attested | required | on |
| **G1** Supervised | ≥ R2 | R3 | fail-closed | required+attested | required | on |
| **G2** Trusted | ≥ R3 | R3 | fail-closed | required+attested | required | on |
| **G3** Autonomous-in-workspace | ≥ R4 | R4 | fail-closed | required+attested | required | on |
| **G4** Frontier | R5 only | R5 | advisory | required+attested | required | on |
| **G5** HERETIC | none | R5 | shadow (log-only) | not required | **required** | **on** |

Risk classes: R0 read-only · R1 safe-local · R2 reversible write · R3 external
effect · R4 sensitive/system · R5 irreversible/destructive.

## The constitutional floor (survives even HERETIC)

Two invariants hold at every level, G5 included:

1. **The hash-chained, externally anchored trace stays on.** A run that cannot
   prove what it did has left the world-line: no recovery (the M2 checkout is
   impossible), no post-hoc audit, drift undetectable by definition. Trace-off
   is therefore never a valid level — it is deletion of the system's ability to
   prove its own history, not a higher freedom.
2. **No self-escalation.** No component raises its own level; only an operator
   override receipt does.

**Tradeoff, resolved explicitly.** Keeping trace on in HERETIC costs a
philosophical purity ("not free from *everything*") and a sub-millisecond append
per submit, plus the possibility of secrets entering the trace (mitigated by the
existing redacted trace view). Turning it off costs sovereignty itself. We keep
the record. Because a local trace is forgeable by anyone with write access to the
trace directory (proven: a full re-forge passes internal verification), **G5 is
refused unless an external anchor and a green sandbox attestation are both
available** — until then G4 is the hard ceiling.

## Precedence

`effective = min(system_ceiling, agent_ceiling, task_request)` — the most
restrictive wins. A task may always lower itself. Raising a task above the agent
ceiling (never above the system ceiling) requires an **OverrideReceipt**: an
operator identity, a reason, a single-run scope, and a TTL, recorded in the
trace like any approval. The operator, and only the operator, extends trust.

## Config / enforce / audit

- **Config**: system default lives in `config/`; per-agent on the agent card /
  policy card; per-task in the submit envelope. `resolve_effective` computes the
  effective level and `runtime_kwargs_for` materializes it into `build_runtime`
  arguments.
- **Enforce**: the resolver is the only place that instantiates gate
  configuration. A permissive `AutoApprover(lambda r: True, allow_r5=True)`
  outside the resolver is the anti-pattern the CI guard forbids.
- **Audit**: `agentic-runtime governance audit <run_id> --declared Gn` infers,
  from the trace's approval receipts (`risk_class` + `decided_by`), the minimal
  level that would have permitted the observed behavior, and flags any run
  operating above its declaration — silent drift toward HERETIC.

## Failure modes guarded

- **Silent drift**: default enforcement is a function of level (G≤3 →
  fail-closed); the bare `GovernanceEnforcementConfig()` shadow-only default is
  confined to the resolver's G4/G5 path.
- **Understated level**: the drift audit compares inferred vs declared and exits
  non-zero on upward drift.
- **Probe lie**: a level requiring a hard sandbox will not resolve on a host
  where the M0 functional attestation fails.

## Next-gen evolution (design; implemented after M6)

- **Capability vector, not a scalar.** G-levels become named presets over a
  vector of independent dials (HITL, sandbox, tool scope, network, budget). An
  operator can derive a custom profile; the resolver and audit operate on the
  vector.
- **Earned autonomy.** A trust score from verified runs (verifier pass rate, a
  drift-free streak from the governance audit) lets the system *propose* a level
  increase — the increase itself still requires an operator override (no
  self-escalation, consistent with the P1.4 constitution).
- **Cryptographic identity.** A per-card key signing each `entry_hash` makes
  `issuer_card_id` provable across a trust boundary — the precondition for
  network deployment.
- **Remote attestation.** The M0 attestation record signed by a host key makes a
  node's G-level availability provable to a remote coordinator.
