# AUREL F3.2 — External-Executor Identity, Budget Envelope, Track Record

_2026-07-09, branch `feat/f3-external-executors`. Third F3 slice (after F3.0 taint, F3.1 gate-check)._

## What shipped

New pure-value module `src/agentic_runtime/external_executor.py` — an external
executor (a Claude Code session, another agent) is admitted to Aurel's governed
channel as **three bounded things, never a trusted peer**:

1. **Least-privilege identity.** `ExternalExecutorGrant` (operator-authorized ceiling;
   tightest defaults: no tools, read-only, LOW risk, no network/secrets) →
   `derive_external_card` produces an `AgentCard` **exactly the grant, never wider**
   (protected mutation always off). No self-elevation: the profile exposes no
   scope-widening method — more capability exists only by deriving from a *new* grant.
2. **Hard budget envelope.** `budget_envelope` clamps a `BudgetPolicy` **down** to the
   grant (`min` of platform default and grant). A grant can only tighten; an
   over-generous grant is clamped to the platform default — no executor raises its own
   ceiling.
3. **Governed track record.** `TrackRecordLedger` is append-only with immutable
   (`frozen`) entries; `record()` is the only writer, meant to be called by the runtime
   from real gate/verifier results — **the executor cannot write its own success**.
   `TrustLevel` (UNTRUSTED/PROBATION/TRUSTED) is **derived, never set**; a recent failure
   drops trust to UNTRUSTED. `effective_max_risk = min(card ceiling, trust ceiling)`:
   trust can only **restrict** (a low-trust executor is capped below its card until it
   earns a record) and **never widens** authority beyond the card.

`ExternalExecutorProfile` bundles identity + budget + ledger; `make_external_executor`
is the factory. Deterministic, stdlib-only, no runtime wiring.

## Evidence

- Seal `tests/test_p6f3_2_external_executor.py` — **12 passed**: tightest defaults;
  card == grant never wider; no self-elevation (widening needs a new grant); budget
  clamps over-generous grants to base and applies tight grants without exceeding base;
  track record append-only + immutable; no-record → UNTRUSTED; trust climbs with clean
  successes; a recent failure drops it; trust only restricts / never widens; profile
  effective ceiling uses trust; to_dict serializable.
- ruff clean; mypy clean (1 source file); compileall OK.
- **Purely additive** — no existing file modified.

## Next

**F3.3 — `mcp_gateway/` (Aurel as an MCP server).** Expose governed tools to external
clients over stdlib JSON-RPC 2.0; each exposed tool bound to a `ToolContract` + a lease
from `spine/tool_exec.py`; inbound calls enter as `make_tainted(..., MCP_CLIENT)` and run
through full `submit` under the executor's F3.2 profile (least-privilege card + hard
budget), with outcomes written to its track record. Seal `test_p6f3_3_mcp_gateway.py`.
This is where ALLOW becomes real execution (budget / sandbox / approval all apply).
