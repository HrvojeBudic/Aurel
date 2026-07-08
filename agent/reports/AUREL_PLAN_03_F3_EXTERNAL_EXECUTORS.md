# AUREL PLAN 03 — F3: Adapter za vanjske izvođače (External Executors)

_Cut: 2026-07-09, branch `feat/f3-external-executors` (from `master` @ post-F2 merge). Follows F2 (providers/secrets/redaction/drill)._

## 0. Što F3 je (iz `AUREL_PLAN_02` §4.F3 + `AUREL_MASTERPLAN_CONTINUATION` Track D)

> `aurel gate check` (Claude Code hookovi) → `mcp_gateway/` (Aurel kao MCP server, governed alati,
> lease iz `spine/tool_exec.py`). Vanjski agenti = AgentCard + budget + track record.
> **U Front rječniku: ovo je backend WorkOPS.Code ekrana** — "vanjski senior izvođač" radi u istom
> governed kanalu koji će UI prikazivati.

Dva smjera, jedan governed kanal:
- **A (primarni, F3 naglasak):** Aurel **kao MCP server / gate** — vanjski izvođač (Claude Code prvi)
  zove Aurelove governed alate. `aurel gate check` je hook-entry: predloženu (tool, args) akciju provuče
  kroz governance BEZ izvršenja i vrati allow/deny + razlog.
- **B (Track D1/D2, kasnije u F3):** Aurel **kao MCP client** — Aurel zove vanjske MCP alate; izlaz je
  `TaintedContent(source_kind=mcp_tool)`, svaki bridged tool dobiva HIGH external floor.

**Zajednički obavezni temelj oba smjera: taint & injection obrana (D0) — "FIRST, no deps".**

## 1. Invarijante (NC — non-negotiable, kroz sve F3 slice-ove)

1. **Additive & flag-gated.** Sve iza `AUREL_EXTERNAL_INGRESS` / `AUREL_MCP_GATEWAY`; flag OFF ⇒
   `runtime.submit` / postojeće staze **byte-identične**.
2. **Provenance forbids instruction.** External-origin sadržaj (`source_kind ∈ EXTERNAL_ORIGIN_KINDS`)
   **strukturno** ne može postati plan/instrukcija — nema konstruktora koji ga podigne. Jedini izvor
   instrukcija ostaje model-output kroz `PlanValidator`. Injection-detektor je **advisory** data-channel
   obrana, NIKAD gate.
3. **No contract / no lease ⇒ no execution.** Svaki izloženi/pozvani alat mora imati `ToolContract`
   (P1.3 manifest seal netaknut) + lease iz `spine/tool_exec.py`. Fail-closed.
4. **External annotations may only ESCALATE risk.** Server/annotation nikad ne spušta risk floor.
5. **Vanjski agent = AgentCard + budget + track record.** Least-privilege; ne može se sam elevirati;
   budget je hard envelope; track-record je governed (ne self-reported).
6. **Sve odluke u trace.** Nijedna gate-odluka / gateway-poziv nije nevidljiv.
7. **Deterministic & stdlib-only.** Bez `hash()`/RNG u odlukama; bez novih third-party ovisnosti.

## 2. Dekompozicija (sealed slice-ovi)

| Slice | Naslov | Novi moduli | NC fokus | Seal |
|---|---|---|---|---|
| **F3.0** | External ingress: taint & injection defense (D0) | `external_ingress/{taint,injection_detector,sanitization}.py` | NC-2 provenance-forbids-instruction; advisory detektor | `test_p6f3_0_external_ingress_taint.py` |
| **F3.1** | Gate-check foundation | `gate/gate_check.py`, `cli_modules/gate_commands.py` (`aurel gate check`) | read-only governance dry-run; allow/deny + razlog; no execute | `test_p6f3_1_gate_check.py` |
| **F3.2** | External-executor identity + budget + track record | `external_executor.py` (AgentCard izvedba + budget envelope + governed track-record ledger) | NC-5 least-privilege, budget hard-stop, track-record governed | `test_p6f3_2_external_executor.py` |
| **F3.3** | `mcp_gateway/` — Aurel kao MCP server | `mcp_gateway/{jsonrpc,server,tool_registry}.py` | NC-3 contract+lease, NC-6 traced, ulaz tainted `mcp_client` | `test_p6f3_3_mcp_gateway.py` |
| **F3.4** | (smjer B) MCP client bridge | `mcp/{jsonrpc,transport,client,bridge}.py` | NC-2 izlaz tainted, NC-4 HIGH floor, contract po bridged toolu | `test_p6f3_4_mcp_client_bridge.py` |
| **F3.5** | Projection + CLI + exit seal + report | `gate/gate_projection.py`, `cli_modules/*_cli.py`, `external_ingress/f3_seal.py` | derived seal, read-only projekcije | `test_p6f3_5_f3_exit_seal.py` |

Redoslijed je fiksan do F3.3; F3.4 (smjer B) je odvojiv i može se odgoditi. F3.0 nema ovisnosti i ide prva.

## 3. Flagovi

- `AUREL_EXTERNAL_INGRESS` — F3.0 definira; defined-not-gating dok se ne poveže u F3.1+ (kao A0→A3 obrazac).
- `AUREL_MCP_GATEWAY` — F3.3 definira; load-bearing na wiringu gatewaya.

## 4. Reuse (ne graditi nanovo)

- `spine/tool_exec.py` — `ToolExecLease` / `SpineToolExecSession.issue_lease` (lease scope za gateway).
- `core_types.AgentCard` / `AuthorityScope` — identitet vanjskog izvođača.
- `tool_contracts.py` — contract registry; gateway izlaže samo contract-bound alate.
- `memory_governance` provenance obrazac (`trust: untrusted → candidate`) — analogija za taint doktrinu.
- F2 `SecretRedactor` — redakcija u gateway/provider errorima.

## 5. Status

- [x] **F3.0** — external ingress taint & injection defense (ovaj slice).
- [ ] F3.1 … F3.5.
