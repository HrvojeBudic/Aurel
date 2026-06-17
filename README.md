# Agentic Runtime — Agent 3.0 reference implementation

A production-shaped, runnable reference runtime for **governed agency**: the entity
proposes, the runtime disposes. Python 3.11+ stdlib only (no runtime dependencies).

## Quick start

```bash
pip install -e ".[dev]"   # optional: pytest for tests
python -m agentic_runtime.demo
python examples/demo.py
```

## Layout

```
pyproject.toml
src/agentic_runtime/     # package source
tests/                   # pytest suite
examples/                # runnable examples
```

## The one law

> An entity may not act. It may only emit a `CommandEnvelope`. The runtime
> decides whether it is permitted, safe, and how it executes, observes,
> verifies, traces, and remembers.

## Pipeline (every command)

```
CommandEnvelope
  → Policy        capability ≠ permission ≠ authority; canonical paths; risk re-score
  → HITL          if risk exceeds the card's ceiling
  → Budget        charge; hard limits trip a halt
  → Snapshot      before_state_hash (+ rollback point for writes)
  → Execute       tool runs ONLY inside the sandbox
  → Verify        against REAL post-state + test integrity
  → Rollback      if a write fails verification
  → Trace         hash-chained StateTransitionRecord
  → Memory        episodic + ephemeral update
  → return        ObservationEnvelope + VerifierResult
```

## P0 security hardening

| Control | Module |
|---------|--------|
| Canonical path resolution (no `..`, absolute, symlink escape) | `canonical_path.py` |
| Shared resolver in Policy + Sandbox | `policy.py`, `sandbox.py` |
| `UnsafeLocalSandbox` (explicitly not production-safe) | `sandbox.py` |
| `SafeSandbox` boundary (Docker, Bubblewrap) | `sandbox.py` |
| `run_tests` ≥ MEDIUM without hard isolation | `policy.py` |
| `TestIntegrityVerifier` (protected tests cannot be weakened) | `verifier.py` |
| Empty/invalid plans HALT | `entity.py` |
| Deterministic `hashlib` embedder | `memory.py` |

## Sandbox tiers

- **`UnsafeLocalSandbox`** — best-effort POSIX jail. Subprocesses may escape. Dev/demo only.
- **`DockerSandbox` / `BubblewrapSandbox`** — implement `SafeSandbox` (`is_hard_isolated=True`).

## Tests

```bash
python -m compileall src
pytest
python -m agentic_runtime.cli verify
python -m agentic_runtime.cli alpha-seal   # P1.0 readiness
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for production sandbox setup.

## Modules

| Module | Responsibility |
|--------|----------------|
| `canonical_path.py` | CanonicalPathResolver — single path truth |
| `core_types.py` | Vocabulary: Intent, CommandEnvelope, AgentCard, … |
| `policy.py` | Three-gate policy engine + risk re-scoring |
| `sandbox.py` | Workspace jail, snapshots, rollback, Safe/Unsafe tiers |
| `tools.py` | Side-effecting tool surface |
| `verifier.py` | State verifiers + TestIntegrityVerifier |
| `trace.py` | Hash-chained ledger |
| `memory.py` | 5-tier memory fabric |
| `skills.py` | Skill compilation + drift-checked reflex |
| `runtime.py` | Governed command pipeline kernel |
| `entity.py` | Cognitive organism (plan/execute/verify loops) |
