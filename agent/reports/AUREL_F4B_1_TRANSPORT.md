# AUREL F4B / B1 — MCP Client Transports (stdio + Streamable HTTP)

_2026-07-09, branch `feat/f4b-mcp-client-bridge`. Second F4B slice._

## What shipped

`mcp_client/transport.py` — the `Transport` protocol (`send` / `receive` / `close`,
injectable) plus two **real, fail-closed, hard-capped** transports:

- **`StdioTransport`** — spawns a subprocess (`argv` list, **never a shell**) with a
  **default-deny scrubbed env** (`scrub_env`: only explicitly passed-through vars survive,
  plus a minimal PATH — secrets never reach the child unless named). Newline-delimited
  JSON-RPC on stdout via a bounded reader thread; stderr drained as diagnostics (never fed
  into the protocol). Per-message byte cap + receive timeout; dead process / oversize /
  malformed / EOF all raise `McpTransportError`.
- **`HttpTransport`** — stdlib `urllib` POST of one JSON-RPC message, persisting the
  `Mcp-Session-Id` header, honoring HTTP 202 (accepted notification, no body), **refusing
  every redirect** (`_NoRedirect`), byte-capped + timed out, http(s)-scheme-only.

## Evidence

- Seal `tests/test_p6f4b_1_transport.py` — **11 passed**, against **genuine** transports
  (no in-process fake): a python subprocess for stdio + a stdlib `http.server` on
  127.0.0.1 — deterministic, no external network. Covers: stdio round-trip; env scrubbed
  by default / passed-through when explicit; oversize + timeout fail-closed; `scrub_env`
  default-deny; HTTP round-trip + session-id persistence; 202 notification; redirect
  refusal; oversize fail-closed; non-http scheme rejected.
- ruff clean; mypy clean (3 files); compileall OK. Purely additive.

## Next

**B2 — content model.** `mcp_client/content.py`: MCP content blocks (text/image/audio/
resource) → typed, tainted structures; `ToolCallResult` (content + isError + structured);
`result_to_text` for the sink. Seal `test_p6f4b_2_content.py`.
