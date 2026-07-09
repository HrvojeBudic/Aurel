# AUREL F3.5 — Projection + CLI + F3 Exit Seal

_2026-07-09, branch `feat/f3-external-executors`. Final F3 slice — closes the external-executor phase._

## What shipped

- **`f3_seal.py`** — the **derived** F3 exit seal (never a self-assigned boolean).
  `build_f3_exit_seal` checks every substantive slice (F3.0→F3.3 + F3.5) for both an
  importable module AND a present report; a missing module or report BLOCKS that item
  and the whole seal. Deferred surfaces stay explicit in an `UnavailableSurface`
  registry — `mcp_transport`, `content_passthrough`, `mcp_client_bridge` (→ F4 /
  ContextLoom), `a2a_messaging` — each with a reason and a future owner. Overclaim
  guards `claims_transport_wired` / `claims_content_passthrough` /
  `claims_client_bridge_live` are computed and hard-wired False: SEALED means the
  **inbound governed-executor path** is closed, not that those surfaces exist.
- **`f3_projection.py`** — read-only read-models behind the Front WorkOPS.Code screen:
  `project_executor_standing` (trust, card/effective ceilings, track-record counts,
  recent outcomes) and `project_gateway_surface` (per exposed tool: its external floor +
  the executor's current reachability — `reachable` / `needs_approval` / `denied`).
  `classify_reachability` mirrors the gateway's step-3 floor/authority gate; the seal
  test cross-checks it against the gateway's actual verdicts so it cannot drift.
- **`cli_modules/f3_commands.py` + `cli.py`** — `aurel f3 seal [--json]` (exits 2 when
  not SEALED, so it can gate CI) and `aurel f3 surface [--trusted]` (projects a demo
  executor's reachable surface, no runtime built).

## Evidence

- Seal `tests/test_p6f3_5_f3_exit_seal.py` — derived status SEALED when all slices
  present / BLOCKED when a report or module is missing (hermetic tmp-dir); overclaim
  guards False; UNAVAILABLE registry explicit with owners; projection standing +
  surface; **no-drift** cross-check (projection reachability == gateway verdict for
  reachable / needs_approval / denied); real-repo seal is SEALED.
- ruff clean; mypy clean; compileall OK. Only existing file touched: `cli.py`
  (additive subparser + import).

## F3 phase — closed

Aurel now admits an external executor (a Claude Code session, another agent) into one
governed channel, inbound-only, security-first:

- **F3.0** taint & injection defense — external content is instruction-ineligible by
  provenance, not by scanning.
- **F3.1** `aurel gate check` — read-only contract+policy preflight, fidelity by reuse.
- **F3.2** identity + hard budget + governed track record — least-privilege, no
  self-elevation, trust derived and only ever restrictive.
- **F3.3** `mcp_gateway/` — Aurel as a governed MCP server; every `tools/call` tainted,
  allowlisted, floor-checked, preflighted, executed under a lease through real `submit`,
  and recorded.
- **F3.5** derived exit seal + read-only projections + CLI.

**Explicitly deferred (UNAVAILABLE, not overclaimed):** MCP transport loop; F2-redacted
content passthrough; direction B MCP client bridge (→ F4 ContextLoom, where tainted
external output has a governed consumer); A2A messaging.

## Next

**F4 — Kognicija: interaktivni loop + ContextLoom.** The natural home for direction B:
governed context assembly (provenance + taint + budget-aware compression + hash in
trace), where Aurel calling OUT to external MCP servers finally has a disciplined sink.
