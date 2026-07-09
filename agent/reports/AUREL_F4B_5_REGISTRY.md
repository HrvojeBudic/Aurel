# AUREL F4B / B5 — MCP Server Registry + Connection Manager

_2026-07-09, branch `feat/f4b-mcp-client-bridge`. Sixth F4B slice._

## What shipped

- **`config/live/mcp_servers.yaml`** — declares the external MCP servers Aurel may call.
  **Every server disabled by default** (nothing connects until the operator flips
  `enabled: true` + sets `AUREL_MCP_CLIENT`). Secrets never in the config — a stdio server
  names env vars via `env_passthrough`; the transport scrubs the rest.
- **`mcp_client/registry.py`** — `McpServerSpec` (stdio: command/args/env_passthrough;
  http: url) + `parse_server_spec` (fail-closed: transport ∈ {stdio,http}, stdio needs
  command, http needs url). `McpServerRegistry.load` reuses the stdlib `yaml_minimal` +
  `assert_no_raw_secrets_in_yaml` (F2), rejects duplicates. `McpConnectionManager` —
  `connect` (enabled-only; builds transport via an **injectable factory**, initializes an
  `McpClient`; idempotent), `disconnect`, `active`, `health`. Fail-closed on unknown /
  disabled server.

## Evidence

- Seal `tests/test_p6f4b_5_registry.py` — **6 passed**: the real config parses with all
  servers disabled; a tmp config toggles enabled; spec validation fail-closed (name /
  transport / stdio-command / http-url); missing config fails closed; manager connects an
  enabled server to an initialized client (fake transport, no subprocess), refuses
  disabled + unknown, is idempotent, and disconnect updates health.
- ruff clean; mypy clean (7 files); compileall OK. Additive (only new files + a new config).

## Next

**B6 — ContextLoom sink + CLI + F4B exit seal.** `loom_sink.py` (tool result → DATA-fenced
`ContextItem`, the one path external content enters context), `f4b_seal.py` (derived exit
seal over B0–B6 + UNAVAILABLE registry), `cli_modules/mcp_client_commands.py`
(`aurel mcp-client list-servers / seal / demo`). Seal `test_p6f4b_6_f4b_exit_seal.py`.
