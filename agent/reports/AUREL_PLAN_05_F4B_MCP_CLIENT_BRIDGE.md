# AUREL PLAN 05 — F4B: MCP Client Bridge (smjer B — Aurel zove VAN) — v4 (real, expanded)

_Cut: 2026-07-09, branch `feat/f4b-mcp-client-bridge` (from master @ post-F3+F4 merge)._
_v4: pravi, potpun MCP klijent usklađen s protokolom (lifecycle + capabilities + content blocks + pagination +_
_stdio & Streamable-HTTP transport + više servera). Funkcija prva; sigurnost proporcionalna, posuđena iz F2–F4._

## 0. Cilj

Aurel dobiva **pravu, protokolno-usklađenu MCP klijent sposobnost**: spoji se na vanjski MCP server (stdio ili
HTTP), odradi `initialize` handshake s pregovorom verzija i capabilitija, otkrije alate (`tools/list` s
paginacijom), pozove alat (`tools/call`) i ispravno parsira **content blokove** (text/image/resource), pa taj
rezultat — kao **tainted DATA** — provuče kroz ContextLoom u governed kontekst. Podržava **više servera** kroz
registry/config i upravlja njihovim životnim ciklusom.

**Sigurnost se ne gradi nanovo — nasljeđuje se:** output=`TaintedContent` (F3.0), svaki alat kroz `ToolContract`
+ `runtime.submit` (isti gate koji već štiti sve), outbound kroz `SecretRedactor` (F2). Novo je samo transport,
tainting na ulazu, i HIGH floor jer je izvor vanjski.

## 1. Invarijante (5)

1. **Additive & flag-gated** (`AUREL_MCP_CLIENT`, default OFF); byte-identical OFF.
2. **Output uvijek tainted** (F3.0); u kontekst samo kroz ContextLoom (DATA-fenced).
3. **No contract ⇒ no execution**; bridge=allowlist (prazan default); poziv kroz `runtime.submit`.
4. **HIGH external floor** po bridged alatu (server-anotacija ne spušta).
5. **Hard caps + secret-redakcija** na transportu (timeout+max-bytes; `redact_known` outbound).

## 2. Usklađenost s MCP protokolom (što "pravi" znači)

- **Lifecycle:** `initialize` (client→server, s `protocolVersion`, `capabilities`, `clientInfo`) → server odgovara
  svojim capabilitijima → klijent šalje `notifications/initialized` → operativna faza → `close`/shutdown.
- **Version negotiation:** klijent predlaže (npr. `2025-06-18`), prihvaća serverov ako se razlikuje, fail-closed ako nekompatibilan.
- **Capabilities:** klijent gejta pozive prema onome što server oglašava (`tools`, `resources`, `prompts`); nema poziva na necapable surface.
- **JSON-RPC 2.0 potpuno:** requesti (id-correlated), **notifikacije** (bez id: initialized/cancelled/progress), error objekti; id-generator + response-correlation.
- **tools/list paginacija:** `cursor` petlja dok `nextCursor` postoji.
- **tools/call rezultat:** `content: []` blokovi (`text`, `image`, `audio`, `resource`) + `isError` + opcionalni `structuredContent`.
- **Resources & prompts:** `resources/list` + `resources/read`, `prompts/list` + `prompts/get` — capability-gated (tools su primarni, resources/prompts real ali sekundarni).
- **Transporti:** **stdio** (subprocess, newline-delimited JSON, stderr=log) i **Streamable HTTP** (POST JSON-RPC, `Mcp-Session-Id` header, 202 za notifikacije; SSE-streaming odgovori parkirani u §6).

## 3. Dekompozicija (7 zapečaćenih slice-ova)

| Slice | Naslov | Novi moduli | Seal |
|---|---|---|---|
| **B0** | JSON-RPC 2.0 client core (req/notif/resp, id-korelacija, error) | `mcp_client/jsonrpc_client.py` | `test_p6f4b_0_jsonrpc_client.py` |
| **B1** | Transporti: stdio (subprocess) + Streamable-HTTP + caps + fake | `mcp_client/transport.py` | `test_p6f4b_1_transport.py` |
| **B2** | Content model: MCP content blokovi → tipizirani tainted | `mcp_client/content.py` | `test_p6f4b_2_content.py` |
| **B3** | Protokol klijent: lifecycle + capabilities + tools/resources/prompts | `mcp_client/client.py` | `test_p6f4b_3_client.py` |
| **B4** | Bridge: inputSchema→ToolContract, HIGH floor, allowlist, ToolSpec, submit | `mcp_client/bridge.py` | `test_p6f4b_4_bridge.py` |
| **B5** | Registry + config + connection manager (više servera, lifecycle) | `mcp_client/registry.py`, `config/live/mcp_servers.yaml` | `test_p6f4b_5_registry.py` |
| **B6** | ContextLoom sink + CLI + F4B exit seal | `mcp_client/loom_sink.py`, `f4b_seal.py`, `cli_modules/mcp_client_commands.py` | `test_p6f4b_6_f4b_exit_seal.py` |

### B0 — JSON-RPC client core
`JsonRpcClientCodec`: `build_request(method, params) -> (id, dict)`, `build_notification(method, params)`,
`correlate(response) -> (id, result|error)`, fail-closed validacija. Reuse error-konstanti iz `mcp_gateway/jsonrpc.py`.
Deterministički id (monotoni brojač, ne RNG). **Seal:** req/notif shape; error correlation; malformed fail-closed.

### B1 — transporti
- `Transport` protokol: `send(dict)`, `receive() -> dict`, `close()`; **injektabilan** (seals → in-process fake).
- `StdioTransport`: subprocess (`argv` lista, nikad shell; `env`, `cwd`), reader thread, newline-JSON framing,
  stderr drenaža (log, ne truje protokol), caps (`timeout_s`, `max_response_bytes`), lifecycle terminate/kill, fail-closed `McpTransportError`.
- `HttpTransport`: stdlib `urllib`, POST JSON-RPC, `Mcp-Session-Id` header perzistira, 202→no-body za notifikacije,
  isti caps, bez redirecta.
- **Seal:** fake determinizam; stdio framing (split po \n, ignore stderr); caps enforce; http header/202; fail-closed.

### B2 — content model
`content.py`: `TextContent`/`ImageContent`/`AudioContent`/`EmbeddedResource` (frozen), `parse_content_block(dict)`,
`ToolCallResult(content: tuple, is_error: bool, structured: dict|None)`. **Svaki tekstualni blok → `make_tailed`** …
ispravak: `make_tainted(MCP_TOOL)`; ne-tekst (image/audio) nosi ref+mime, ne sirove bajtove u kontekst.
`result_to_text(result) -> str` za sink. **Seal:** parsira sve tipove blokova; text tainted+ineligible; isError poštovan; nepoznat blok fail-closed (ne baci).

### B3 — protokol klijent
`McpClient(transport, server_name, redactor, client_info)`:
`initialize()` (version+capabilities negotiation, šalje `initialized`), `list_tools()` (paginacija), `call_tool(name,args)`
(→ `ToolCallResult`), `list_resources()`/`read_resource(uri)`, `list_prompts()`/`get_prompt(name,args)` (capability-gated),
`ping()`, `close()`. Outbound args → `redact_known` prije slanja. Opisi alata i sami tainted. Fail-closed na error/necapable.
**Seal:** handshake+initialized; version negotiation; capability gate (necapable→odbij); paginacija; tainted output; redakcija; error poštenje.

### B4 — bridge u governance
`McpBridge(client, contract_registry)`: `bridge_tool(tool_descriptor)` (allowlist, prazno default).
`json_schema_to_contract(inputSchema) -> ToolContract` (JSON-Schema tipovi → `ArgSpec`, required, enum) s
**floor=max(HIGH, intrinsic)**. Registrira `ToolSpec` (`mcp__<server>__<tool>`) čiji executor: `redact→call_tool→
ToolCallResult→tainted evidence` (hash+provenance, sirovo → B6 sink). Ne-bridgean alat ne postoji za runtime.
Poziv kroz `runtime.submit` → network authority gate vrijedi. **Seal:** schema→contract (tipovi/required/enum);
floor escalation-only; namespaced tool ime; no-bridge⇒no-exec; kroz submit gejtan.

### B5 — registry + config + manager
`config/live/mcp_servers.yaml`: lista servera (`name`, `transport: stdio|http`, `command/args/env` ili `url`, `enabled`, `allowed_tools`).
`McpServerRegistry.load(path)` → `McpServerSpec`. `McpConnectionManager`: `connect(name)` (spawn transport + `McpClient.initialize`),
`disconnect`, `health`, bounded reconnect (1 pokušaj, fail-closed). Nema živog spawna u sealu (config-shape + fake).
**Seal:** config parse; server-spec validacija; manager lifecycle nad fake; disabled server ⇒ ne spaja; fail-closed na loš config.

### B6 — sink + CLI + seal
`loom_sink.py`: `sink_tool_result(result, server_name) -> ContextItem(MCP_TOOL)` (DATA-fenced; image/audio → ref, ne bajtovi).
`f4b_seal.py`: derived exit seal (B0→B6 modul+report) + UNAVAILABLE registar (živi server, SSE-streaming, D2 plan-steps, A2A, §6 hardening).
CLI `aurel mcp-client {list-servers, connect, list-tools, call, bridge, sink-demo, seal}` — read-only demo nad fake serverom.
**Seal:** sink→bundle external+fenced; image→ref ne bajtovi; derived SEALED/BLOCKED; real-repo SEALED; CLI demo end-to-end nad fake.

## 4. Reuse
F3.0 taint · F3.3 jsonrpc konstante · F2 `SecretRedactor` · F4 ContextLoom (sink+fence) · `ToolContract`/`ToolSpec` ·
`policy` network gate + `runtime.submit` · F2 `ProviderConfigLoader` obrazac za yaml.

## 5. Procjena
B0→…→B6, svaki: ruff+mypy+compileall+seal, ciljani `git add`. Stdlib-only (urllib/subprocess/threading). ~7 commita, ~13 fajlova, ~60 seal testova.

## 6. Parkirano (UNAVAILABLE, opt-in poslije)
Živi vanjski server (operator pali flag+config) · **SSE-streaming HTTP odgovori** · sigurnosni hardening (SSRF/egress guard,
tool-pinning/rug-pull, per-server secret grant, unicode/ANSI de-smuggling, fence-nonce, MCP fuzz drill) · **D2** (MCP alati kao
LLM-plan koraci, `STRUCTURED_PLAN_SCHEMA` v2) · **A2A** (zadnje) · retry/reconnect poool.

## 7. Status
- [ ] B0 … B6.
