# AUREL F3.3 — Aurel as a Governed MCP Server (`mcp_gateway/`)

_2026-07-09, branch `feat/f3-external-executors`. Fourth F3 slice — where a preflight becomes real execution._

## What shipped

New package `src/agentic_runtime/mcp_gateway/` — the single governed door through which
an external MCP client (a Claude Code session, another agent) reaches Aurel's tools.

- **`jsonrpc.py`** — minimal stdlib JSON-RPC 2.0 (request/response/error value types +
  a fail-closed `parse_request` with correct standard codes). No third-party dep.
- **`tool_registry.py`** — `GatewayToolRegistry`: the exposed-tool allowlist. Empty by
  default; a tool is offered only if explicitly `expose`-d AND contracted. Each exposed
  tool carries an **escalation-only external risk floor** — raised to at least MEDIUM
  (external origin is never trusted) and at least the contract's intrinsic floor; a
  caller/annotation floor can only push it higher. JSON-Schema derived from the contract.
- **`server.py`** — `McpGateway`. Every `tools/call` passes six gates in order:
  1. **Tainted** `MCP_CLIENT` (F3.0) — external-origin, instruction-ineligible.
  2. **Allowlisted** — not exposed ⇒ never listed, never runs.
  3. **Floor vs. authority/trust** (F3.2) — above the operator card ceiling ⇒ hard
     DENY; within the card but above the trust-earned ceiling ⇒ **REQUIRE_APPROVAL**
     (the bootstrap path: a fresh executor's calls need approval; approved runs build
     its track record, trust rises, friction drops).
  4. **Gate preflight** (F3.1) — contract + policy under the least-privilege card.
  5. **Lease-scoped real submit** — on ALLOW, `SpineToolExecSession` issues a lease
     bound to exactly this (tool, args) and calls the real `runtime.submit` kernel.
     **Budget / sandbox / approval all apply here** — this is where ALLOW becomes
     execution.
  6. **Recorded** — outcome (SUCCESS / FAILURE / DENIED / BLOCKED) written to the
     executor's F3.2 governed track record, feeding future trust.
- **`__init__.py`** — exports + flag `AUREL_MCP_GATEWAY` (defined-not-gating; the
  gateway is opt-in by construction, becomes load-bearing when a transport is stood up).

The JSON-RPC result carries governed **evidence** of the submit (exec id, before/after
state hashes, verifier_passed), not raw internal tool output — so the gateway never
leaks internal data by default. Full F2-redacted content passthrough is a later refinement.

## Evidence

- Seal `tests/test_p6f3_3_mcp_gateway.py` — **9 passed**: initialize / tools/list /
  unknown-method / malformed; escalation-only floor (TRIVIAL git_status floored to
  MEDIUM); unexposed ⇒ DENIED + no exec; floor > card ⇒ hard DENY; within-card-untrusted
  ⇒ REQUIRE_APPROVAL; out-of-scope tool ⇒ policy DENY; ALLOW+trusted ⇒ **real submit
  runs, evidence returned, SUCCESS recorded, inbound provenance MCP_CLIENT +
  instruction-ineligible**; flag default OFF.
- ruff clean; mypy clean (4 source files); compileall OK.
- **Purely additive** — no existing file modified. F3.0–F3.2 seals still green (30).

## Boundary (honest)

Transport is not wired — `McpGateway.handle(dict) -> dict` is the governed core; a real
stdio/HTTP JSON-RPC loop is a thin shell deferred to a follow-up (and gated by the
`AUREL_MCP_GATEWAY` flag going load-bearing). The result returns governed evidence, not
tool content passthrough (which needs F2 redaction first). Mutating tools still require a
hard-isolated sandbox at the lease gate (`SpineExecutionBlocked` → BLOCKED recorded).

## Next

**F3.4 (optional, direction B) — MCP client bridge** (Aurel calls OUT to external MCP
servers; output tainted, HIGH floor, contract per bridged tool), **or F3.5 — projection
+ CLI + F3 exit seal**. Operator decides ordering; F3.4 is separable and can be deferred.
