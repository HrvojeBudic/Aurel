# AUREL F4B / B4 — Bridge External MCP Tools into Governance

_2026-07-09, branch `feat/f4b-mcp-client-bridge`. Fifth F4B slice — the integration point._

## What shipped

`mcp_client/bridge.py` — a discovered MCP tool becomes a governable Aurel tool only by
being **explicitly bridged** (allowlist, empty default):

- `json_schema_to_contract` — maps the server's JSON-Schema `inputSchema` to a
  `ToolContract` (`ArgSpec` types + required) with an **unconditional HIGH external floor**
  (`EXTERNAL_API_CALL` + `NETWORK_REQUEST` side effects). A malicious server annotation
  cannot lower it — escalation-only, proven even on a benign-looking schema.
- `McpBridge(client, runtime, sink=)` — `bridge_tool` registers the contract, a namespaced
  `ToolSpec` (`mcp__<server>__<tool>`) whose handler calls `client.call_tool` and returns
  **leak-safe evidence** (`ToolCallResult.to_dict` — hashes/provenance, **never raw external
  text**; the raw content flows to context only via the sink), and syncs the policy
  engine's registered-tools set. Descriptor hash pinned (`verify_pin`) so a rug-pull is
  detectable (T7).

## Evidence — governance proven end-to-end

- Seal `tests/test_p6f4b_4_bridge.py` — **8 passed**: schema→contract types/required + HIGH
  floor (unconditional); bridge registers contract+spec under `mcp__srv__echo`; handler
  executes the client and its observation is **leak-safe** (raw external text absent);
  **through `runtime.submit`**: with an auto-approver the HIGH tool runs end-to-end
  (`client.call_tool` really invoked); **defence in depth** — the default deny-all approver
  auto-denies a HIGH external call even for an authorized card; a low-ceiling card yields
  `REQUIRE_APPROVAL`; an un-bridged tool does not exist for the runtime; `verify_pin`
  detects a rug-pull.
- ruff clean; mypy clean (6 files); compileall OK. Additive.

## Next

**B5 — server registry + config + connection manager.** `mcp_client/registry.py` +
`config/live/mcp_servers.yaml`: declare servers (stdio/http), lifecycle (connect / health /
disconnect), disabled-server gating. Seal `test_p6f4b_5_registry.py`.
