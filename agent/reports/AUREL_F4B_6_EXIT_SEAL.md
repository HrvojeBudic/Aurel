# AUREL F4B / B6 — ContextLoom Sink + CLI + F4B Exit Seal

_2026-07-09, branch `feat/f4b-mcp-client-bridge`. Final F4B slice — closes the MCP client bridge phase._

## What shipped

- **`mcp_client/loom_sink.py`** — `sink_tool_result(result, server_name) -> ContextItem`:
  the **one path** external MCP output enters context — as a `SourceKind.MCP_TOOL`
  ContextLoom item, instruction-ineligible and DATA-fenced on render. Binary is already
  bytes-free (B2).
- **`mcp_client/fake_server.py`** — an in-process, deterministic fake MCP server transport
  (no network) carrying a **hostile** tool description + output (an injection string), so
  the demo/seals visibly show the taint/fence discipline holding.
- **`mcp_client/f4b_seal.py`** — the **derived** F4B exit seal (B0→B6 module + report;
  missing ⇒ BLOCKED). UNAVAILABLE registry: live-server connection (operator opt-in), SSE
  streaming, the parked security hardening, D2 plan-steps, A2A. Overclaim guards
  (`claims_live_server`, `claims_security_hardening`) hard-False.
- **`cli_modules/mcp_client_commands.py` + `cli.py`** — `aurel mcp-client list-servers`
  (all disabled), `aurel mcp-client seal` (exit 2 if not SEALED), `aurel mcp-client demo`
  (full connect→list→call→sink against the fake server; shows hostile description/output
  stay instruction-ineligible and fenced).

## Evidence

- Seal `tests/test_p6f4b_6_f4b_exit_seal.py` — derived SEALED / BLOCKED (hermetic tmp);
  overclaim guards False; UNAVAILABLE explicit; **end-to-end demo** (fake server → the
  hostile injection in both the tool description and output is instruction-ineligible and
  DATA-fenced in the assembled bundle); real-repo SEALED.
- ruff clean; mypy clean; compileall OK. Only existing file touched: `cli.py` (additive).

## F4B phase — closed

Aurel can now call OUT to an external MCP server and use the result under governance:
B0 JSON-RPC client → B1 transports (stdio + HTTP, real, capped, scrubbed) → B2 content
model (tainted text, bytes-free binary) → B3 protocol client (lifecycle, capabilities,
fail-closed) → B4 bridge (HIGH floor, contract + submit, leak-safe) → B5 registry/config
(disabled by default) → B6 ContextLoom sink + CLI + exit seal.

**Security is inherited, not rebuilt:** external output is `TaintedContent` (never
instruction), every bridged tool carries a `ToolContract` and runs through `runtime.submit`
(HIGH floor → approval), outbound args are F2-redacted. **Deferred (UNAVAILABLE):**
live-server connection (operator opt-in), SSE streaming, the parked hardening
(SSRF/egress guard, pin enforcement, per-server grant, unicode de-smuggling, fence-nonce,
fuzz drill), D2, A2A.

## Next

Merge F4B → master when ready; then the operator can enable a real server in
`config/live/mcp_servers.yaml`. Or pick up F5 (Front) / the parked hardening.
