# AUREL F4B / B3 — MCP Protocol Client

_2026-07-09, branch `feat/f4b-mcp-client-bridge`. Fourth F4B slice._

## What shipped

`mcp_client/client.py` — `McpClient`, the real MCP lifecycle over an injectable transport:

- **initialize** — sends `protocolVersion` (2025-06-18) + capabilities + clientInfo,
  reads the server reply (version negotiation, server capabilities), then sends
  `notifications/initialized`. Fails closed if the server returns no `protocolVersion`.
- **list_tools** — paginated (`cursor` → `nextCursor` loop); each tool's **description is
  tainted** `MCP_TOOL` (a description can carry injection too), and a `descriptor_hash` is
  computed for B4 rug-pull pinning.
- **call_tool** — outbound args **scrubbed of registered secrets** (`redact_known`,
  exact-match — legit args untouched), result parsed by B2 (`ToolCallResult`).
- **resources / prompts** — `list_resources` / `read_resource` / `list_prompts`, all
  **capability-gated**: a surface the server did not advertise fails closed.
- **fail-closed everywhere** — a JSON-RPC error, an off-spec reply, or a transport failure
  raises `McpCallError`; server notifications and stray responses are skipped during
  correlation.

## Evidence

- Seal `tests/test_p6f4b_3_client.py` — **7 passed** against an in-process fake server
  transport: handshake + initialized notification; paginated tools with tainted
  descriptions + pinnable hash; call result parsed; **outbound known secret scrubbed while
  a legit arg is untouched**; non-advertised capability fails closed; call-before-init
  fails closed; JSON-RPC error → `McpCallError`.
- ruff clean; mypy clean (5 files); compileall OK. Purely additive.

## Next

**B4 — bridge to governance.** `mcp_client/bridge.py`: `json_schema_to_contract` (inputSchema
→ `ToolContract`) with a HIGH external floor, an allowlist (empty default), a namespaced
`ToolSpec` (`mcp__<server>__<tool>`) whose executor calls `client.call_tool` and returns
tainted evidence, executed through `runtime.submit`. Seal `test_p6f4b_4_bridge.py`.
