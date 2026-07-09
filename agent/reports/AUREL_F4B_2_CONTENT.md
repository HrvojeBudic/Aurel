# AUREL F4B / B2 — MCP Tool-Result Content Model

_2026-07-09, branch `feat/f4b-mcp-client-bridge`. Third F4B slice._

## What shipped

`mcp_client/content.py` — parses an MCP `tools/call` result's typed content blocks into
provenance-labelled values.

- `ContentBlock` + `ContentKind` (text / image / audio / resource / resource_link /
  unknown). **Text** (and text resources) becomes `TaintedContent(MCP_TOOL)` —
  instruction-ineligible (F3.0), the only thing that reaches context. **Binary**
  (image / audio / blob resource) is reduced to a **bytes-free descriptor** (mime,
  encoded length, `data_ref` hash) — the raw base64 is dropped at the boundary and never
  rendered. An **unknown / hostile** block fails *open into UNKNOWN* (never raises).
- `ToolCallResult` (content + `isError` + `structuredContent`); `text()` renders a
  context-safe string (text inline, binary as descriptors); `parse_tool_result`
  fail-closes a malformed result to `isError=True`.

## Evidence

- Seal `tests/test_p6f4b_2_content.py` — **9 passed**: text tainted + ineligible; text
  resource; **image/blob are descriptors, raw base64 never in `render()` or `to_dict()`**;
  isError + structured captured; mixed text+binary keeps bytes out of sink text; unknown /
  non-dict blocks fail open to UNKNOWN; malformed result → error; deterministic.
- ruff clean; mypy clean (4 files); compileall OK. Purely additive.

## Next

**B3 — protocol client.** `mcp_client/client.py`: `McpClient` — initialize handshake
(version + capabilities negotiation, `notifications/initialized`), `list_tools` (pagination),
`call_tool` (→ `ToolCallResult`), capability-gated resources/prompts, outbound arg
redaction. Seal `test_p6f4b_3_client.py` (against an in-process fake transport).
