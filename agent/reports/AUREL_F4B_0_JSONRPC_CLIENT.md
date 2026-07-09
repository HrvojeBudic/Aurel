# AUREL F4B / B0 — Client-side JSON-RPC 2.0 Codec

_2026-07-09, branch `feat/f4b-mcp-client-bridge`. First F4B slice._

## What shipped

New package `src/agentic_runtime/mcp_client/` (flag `AUREL_MCP_CLIENT`, default OFF) —
the mirror of the server-side `mcp_gateway/jsonrpc.py`, for Aurel *issuing* MCP calls.

- **`jsonrpc_client.py`** — `JsonRpcClientCodec`: `build_request` (monotonic ids, no RNG),
  `build_notification` (no id), `correlate` (validates the envelope, returns a `Response`
  with exactly one of result/error), `expect` (asserts id correlation). Fail-closed:
  a malformed / off-spec envelope raises `JsonRpcClientError` rather than being coerced
  into a fake result. Reuses the shared `JSONRPC_VERSION` / `JsonRpcError` from the gateway
  so both directions never drift.

## Evidence

- Seal `tests/test_p6f4b_0_jsonrpc_client.py` — **14 passed**: request shape + monotonic
  ids + optional params; notifications carry no id; correlate success/error; fail-closed on
  6 off-spec envelopes; `expect` id correlation; flag default OFF.
- ruff clean; mypy clean (2 files); compileall OK. Purely additive.

## Next

**B1 — transports.** `Transport` protocol + `StdioTransport` (subprocess, newline-JSON,
caps) + `HttpTransport` (urllib POST, `Mcp-Session-Id`, caps) + an injectable in-process
fake for deterministic seals. Seal `test_p6f4b_1_transport.py`.
