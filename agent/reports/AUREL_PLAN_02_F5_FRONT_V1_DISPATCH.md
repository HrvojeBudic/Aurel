# AUREL PLAN 02 — F5 Front v1 Dispatch Plan (Signal + WorkOPS + HQ jezgra)

**Datum:** 2026-07-09
**Status:** LIVE dispatch plan — F5 razložen na samostalne slajseve (F5.0→F5.9)
**Izvor:** `AUREL_PLAN_02_ADE_PLATFORM_ENFORCEMENT_I_LOOP.md` §F5; doktrina iz `AUREL_MASTERPLAN_CONTINUATION.md` §5
**Ulazno stanje:** F4 zapečaćen (`AUREL_F4_4_EXIT_SEAL.md`); grana `feat/f4-cognition-contextloom`. Sljedeća grana: `feat/f5-front-v1`.
**Odluka operatera:** ravno na F5 (MCP client bridge ostaje odgođen UNAVAILABLE seam); puni dispatch plan.

---

## 0. Kako koristiti (svaka sesija)

- Svaki slajs (F5.x) je **samostalna dispatch jedinica**: novi/izmijenjeni fajlovi, flag,
  seal test, no-collapse invarijante i **paste-ready dispatch prompt**.
- Radi **jedan slajs odjednom**, redoslijedom §4. Nakon svakog: `ruff` + `mypy` na
  dodirnutim modulima, seal test slajsa, pa fokusirani regresijski rez; **puni suite**
  (`AGENTIC_SKIP_RECURSIVE_SMOKE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`,
  background) prije merge-a grane.
- **Zakon svakog slajsa** (§5): additive-behind-flags (default OFF ⇒ **byte-identičan** off
  put), entity-proposes/runtime-disposes, trace = jedini izvor istine, fail-closed,
  no-overclaim (booleani koji bi lagali su nekonstruktibilni), **"jedna vrata"** (UI nema
  drugi put do backenda osim POST /proposals).
- **North star** cijele faze je jedan test (§7): _operator iz Signala zada intent →
  AurelEU predloži plan → approval u HQ.Command → izvršenje vidljivo u WorkOPS → artefakt
  i odluka u Library — sve replayabilno, nula direktnih poziva iz UI-ja._

---

## 1. Utemeljeno stanje (ground truth, s file:line)

**Postoji (backend zreo):**
- `runtime.submit(cmd, card)` — jedini izvršni put (`runtime.py:202`); approval gate flow
  policy→approval→budget→sandbox→verify→trace (`runtime.py:309–375`).
- Approval **kontrakti** postoje: `ApprovalRequest` / `ApprovalDecision` / `ApprovalReceipt`,
  rizik R0–R5 (`approval.py:21–180`) — ali gate je **efemeran HITL callback**
  (`AutoApprover`/`DenyAllApprover`), **nema** perzistentnog inboxa ni projekcije.
- Read-modeli: `build_web_shell_read_model()` (`aurel_shell/web_shell_read_model.py:108–125`),
  7 surfacea + client status + truth labels + evidence refs; **statički JSON fixture**
  (`web/shell/public/*.json`), nije živ.
- Surface enum (closed-world, 7): `AUREL_CRO/HQ/CORP/HUB/IDE/SYSTEM/SETTINGS`
  (`aurel_shell/surface_registry.py:57–67`). `IDE`→WorkOPS alias. `LAB` **NE** ulazi u F5
  (gradi se u F9); ovdje ga ne diramo.
- Floating window kontrakt: `FloatingWindowKind = {SHELL_PROJECTION_CONTAINER, CONTEXT_VIEW,
  INSPECT_PANEL}` (`aurel_shell/floating_window.py:39–45`), "contract only, ne izvršava ništa"
  (`:116–122`). Nema `SIGNAL_CHAT`.
- Library sastojci (sva tri komponibilna, read-only iz tracea): `MemoryProjection.from_trace`
  (`memory_projection.py:37–160`), `doc_registry` path mapiranje (`doc_registry.py:41–132`),
  `TraceExportManifest` (`aurel_trace/trace_export.py:40–150`).
- ContextLoom (F4): `ContextBundle`/`context_ref` sha256 (`context_loom/loom.py:52–160`),
  `ContextItem` s provenance+taint (`context_loom/context_item.py:56–105`),
  `context_refs_from_replay` (`context_loom/context_trace.py:60–77`) — refovi prežive replay.
- React skeleton: `AppShell` (`web/shell/src/App.tsx:13–70`), `GlobalTopbar` surface selector
  (`components/GlobalTopbar.tsx:9–59`), `SurfacePanel` **stub** (`components/SurfacePanel.tsx`),
  contract-binding test (`contract-binding.test.ts`), DTO tipovi (`types.ts:79–87`).

**NE postoji (F5 gradi):**
1. **HTTP/SSE server** — jedini most UI↔`runtime.submit`. Danas: nikakav server, samo CLI.
2. **Žive projekcije** rebuildane iz tracea na zahtjev (danas: statički fixture).
3. **Perzistentni approval inbox** kao projekcija iz tracea + endpoint za odluku.
4. **Signal poruka kao proposal** (identity/role/mandate/room_id/context_refs) + `SIGNAL_CHAT`.
5. **Ujedinjeni `LibraryReadModel`** (memorija+docs+trace manifest u jedan read-model).
6. **Front UI sadržaj** (approval panel, Signal area, per-surface paneli, SSE klijent).

**Zaključak:** backend je zreo, most i UI ne postoje. F5 = **most ("jedna vrata") + žive
projekcije + tri stupa Fronta (Signal / WorkOPS / HQ jezgra) na tome.**

---

## 2. Arhitektonska kičma: "jedna vrata" + transport odluka

Sve u F5 visi o jednom procesu — `front_server/`. Njegov je jedini zadatak preslikati
tri klase ruta na postojeći backend **bez ijednog drugog izvršnog puta**:

- `GET /read/{model}` — **čiste projekcije** (surfaces, hq/command, library, signal/history,
  approvals). Rebuildane iz tracea. Read-only.
- `POST /proposals` — **JEDINA vrata za mutaciju.** Svaki UI čin (Signal poruka, approve/deny,
  Board "convert", WorkOPS tool poziv) je `ProposalEnvelope` koji se reducira na
  `runtime.submit`. Nema drugog state-changing endpointa.
- `GET /ws` (HTTP→WebSocket upgrade) — bidirekcionalni Signal stream + approval push.
  **Read/push kanal, ne drugi izvršni put:** poruke koje stignu preko WS-a nose isti
  `ProposalEnvelope` i **reduciraju se na `POST /proposals` semantiku** (isti dispatcher);
  WS nikad ne zove podsustav direktno. "Jedna vrata" ostaje jedna.

**Transport odluka (WebSocket od v1 — operaterska odluka, 2026-07-09):**
Doktrina je **stdlib-only, bez runtime ovisnosti** — zato **bez** `websockets` paketa:
ručni RFC 6455 preko `socket`/`http.server` upgradea (handshake `Sec-WebSocket-Accept` =
base64(SHA1(key+GUID)), frame encode/decode + unmasking, ping/pong, close). To je jedan
diskretan modul (`front_server/websocket.py`) i dobiva **vlastiti slajs F5.0b** da se
handshake+framing pečate neovisno o "jedna vrata" HTTP temelju (F5.0a). Bidirekcionalno, ali
disciplina ista: dolazna WS poruka je `ProposalEnvelope` kroz isti dispatcher — nema drugog
izvršnog puta. **Honesty scope v1:** localhost-only, **bez TLS/wss** (Tauri učitava
`localhost`); overclaim guard `claims_remote_websocket = False` i `claims_wss_tls = False`
hard-wired dok se ne uvede Tauri-Rust transport (plan §6).

**Master flag:** `AUREL_FRONT_SERVER` (server se ne konstruira kad je OFF ⇒ byte-identičan
runtime). Sve F5 mogućnosti su iza njega ili iza pod-flagova; nijedan default put se ne mijenja.

---

## 3. Per-slajs dispatch specifikacije

> Legenda: **Files** = novo / izmijenjeno. **Flag** default OFF. **Seal** = pytest fajl.
> **NC** = no-collapse invarijante koje moraju vrijediti. Reuse postojećih zapisa u traceu;
> nove trace evente enkodiraj u summary (persistent replay flatta details).

### F5.0a — "Jedna vrata": HTTP server foundation (flag `AUREL_FRONT_SERVER`)

- **Files:** novo `front_server/__init__.py`, `front_server/server.py` (stdlib
  `ThreadingHTTPServer` + router), `front_server/routes.py` (deklarativna tablica ruta s
  `mutation: bool`), `front_server/proposal_dispatcher.py` (skeleton: prima `ProposalEnvelope`,
  reducira na `runtime.submit`). Edit: `cli.py` (`aurel front serve`, additive subparser).
- **NC:** čist stdlib (bez novih ovisnosti); **točno JEDNA** ruta ima `mutation=True`
  (`POST /proposals`) i ona se reducira na `runtime.submit`; sve ostalo read-only; server se
  **ne konstruira** kad je flag OFF (byte-identično); nijedan handler ne zove podsustav
  direktno mimo dispečera/projekcija.
- **Seal:** `test_p6f5_0a_one_door.py` — enumerira sve rute iz `routes.py`; tvrdi da postoji
  **točno jedna** mutation ruta; da flag-off ⇒ server nekonstruktibilan.
- **Dispatch prompt:** _"Na grani `feat/f5-front-v1` implementiraj F5.0a per dispatch spec u
  `AUREL_PLAN_02_F5_FRONT_V1_DISPATCH.md`. Novi `front_server/` (stdlib-only): ThreadingHTTPServer,
  deklarativna route tablica gdje je `POST /proposals` jedina `mutation=True` ruta koja se
  reducira na `runtime.submit`, proposal dispatcher skeleton. Flag `AUREL_FRONT_SERVER` default
  OFF ⇒ server se ne konstruira, runtime byte-identičan. `aurel front serve` CLI. Seal
  `test_p6f5_0a_one_door.py` dokazuje točno jednu mutation rutu i flag-off nekonstruktibilnost."_

### F5.0b — WebSocket transport (RFC 6455, stdlib) (flag `AUREL_FRONT_SERVER`)

- **Files:** novo `front_server/websocket.py` (ručni RFC 6455: handshake
  `Sec-WebSocket-Accept` = base64(SHA1(key + magic GUID)), frame encode/decode + client-mask
  unmasking, ping/pong, close handshake — sve preko stdlib `socket`/`hashlib`/`base64`, bez
  ovisnosti); edit `front_server/server.py` (`GET /ws` HTTP→WS upgrade), `front_server/routes.py`
  (`/ws` označen kao **non-mutation** push/stream kanal). Dolazna WS poruka → isti
  `proposal_dispatcher` (ne novi izvršni put).
- **NC:** stdlib-only (nema `websockets` paketa); `/ws` je **non-mutation** ruta — sve što
  stigne preko WS-a reducira se na `ProposalEnvelope`/dispatcher, WS nikad ne zove podsustav
  direktno; localhost-only, bez TLS; server-OFF ⇒ nema WS listenera.
- **Seal:** `test_p6f5_0b_websocket.py` — handshake računa točan `Sec-WebSocket-Accept` iz
  poznatog test-vektora (RFC 6455 primjer); masked frame round-trip (encode→decode==original);
  nemaskiran client frame ⇒ odbijen (protokol fail-closed). Overclaim:
  `claims_remote_websocket=False`, `claims_wss_tls=False`.
- **Dispatch prompt:** _"Implementiraj F5.0b: `front_server/websocket.py` ručni RFC 6455 u
  stdlibu (handshake Sec-WebSocket-Accept = base64(SHA1(key+GUID)), frame encode/decode +
  unmasking, ping/pong, close), `GET /ws` upgrade u serveru, `/ws` non-mutation push kanal,
  dolazna poruka→isti proposal_dispatcher. Localhost-only, bez TLS; `claims_remote_websocket`/
  `claims_wss_tls`=False. Seal `test_p6f5_0b_websocket.py`: točan accept-key iz RFC vektora,
  masked frame round-trip, nemaskiran client frame odbijen."_

### F5.1 — Žive projekcije iz tracea (flag `AUREL_FRONT_SERVER`)

- **Files:** novo `front_server/read_models.py` (adapter koji na `GET /read/{model}` vraća
  **živu** projekciju umjesto statičkog fixturea); edit `aurel_shell/web_shell_read_model.py`
  (`build_web_shell_read_model(trace=…)` prihvaća živi trace). Edit: skripta koja i dalje može
  emitirati `web/shell/public/*.json` kao dev fixture (fallback kad server OFF).
- **NC:** projekcije su **čiste** (nula mutacija, nula write-a u trace); rebuildane iz tracea;
  determinizam (isti trace ⇒ isti bytes); kad je server OFF, UI koristi statički fixture
  (dev), nikad lažni "live".
- **Seal:** `test_p6f5_1_live_read_models.py` — živa projekcija == replay-izvedena; dodavanje
  trace eventa deterministički mijenja projekciju; nijedan read endpoint ne piše.
- **Dispatch prompt:** _"Implementiraj F5.1: `front_server/read_models.py` servira žive
  projekcije iz tracea preko `build_web_shell_read_model(trace=…)`. Read-only, deterministično,
  server-OFF ⇒ statički fixture fallback (nikad lažni live). Seal `test_p6f5_1_live_read_models.py`
  dokazuje projekcija==replay i zero-write."_

### F5.2 — Proposal dispatch + perzistentni approval inbox (flag `AUREL_FRONT_SERVER`)

- **Files:** novo `front_server/proposal_envelope.py` (`ProposalEnvelope`: operator_identity,
  current_role, mandate_id, context_refs, intent), popuniti `proposal_dispatcher.py`
  (envelope→`CommandEnvelope`→`runtime.submit`); novo `approval_inbox.py`
  (`PendingApprovalProjection.from_trace` — čita approval evente, gradi listu pending);
  edit `runtime.py`/`approval.py` (approval gate seam koji pending čini **čitljivim** kao
  projekciju + odluka operatera je governed zapis). **Bez** izmjene default gate ponašanja
  kad je flag OFF.
- **NC:** approval odluka je **sama governed record** (ne efemerna); operator ne može
  odobriti izvan mandata (fail-closed); neriješen zahtjev ostaje **pending** (nema tihog
  auto-approvea u `standard`); AurelEU seam u F5 je **PARTIAL** — jedna default persona,
  role-fluid switching je F6 (`claims_aureleu_dispatcher_live=False`).
- **Seal:** `test_p6f5_2_proposal_approval.py` — proposal → pending vidljiv u inbox projekciji
  → approve → `runtime.submit` izvrši → trace pokazuje lanac; deny ⇒ BLOCKED transition;
  approval izvan mandata odbijen.
- **Dispatch prompt:** _"Implementiraj F5.2: `ProposalEnvelope` (identity/role/mandate_id/
  context_refs/intent) → dispatcher → `runtime.submit`. `PendingApprovalProjection.from_trace`
  daje živ approval inbox; odluka operatera je governed record, neriješeno ostaje pending
  (fail-closed). AurelEU je PARTIAL seam (jedna persona, F6 = pun dispatcher),
  `claims_aureleu_dispatcher_live=False`. Seal `test_p6f5_2_proposal_approval.py`: proposal→
  pending→approve→submit→trace lanac; deny⇒BLOCKED; izvan-mandata odbijen."_

### F5.3 — Signal kontrakt + `SIGNAL_CHAT` + history projekcija (flag `AUREL_FRONT_SIGNAL`)

- **Files:** novo `front_server/signal.py` (`SignalMessage`: operator_identity, current_role,
  mandate_id, room_id, context_refs — **konstruktor odbija** poruku bez identity/mandate/refs);
  edit `aurel_shell/floating_window.py` (+`SIGNAL_CHAT` kind, i dalje "ne izvršava ništa");
  history = `LibraryReadModel`/trace projekcija (nula vlastitog stanja). Signal poruka →
  `ProposalEnvelope` (F5.2).
- **NC:** Signal ima **nula vlastitog stanja** (history isključivo iz tracea); svaka poruka
  nosi identity+role+mandate+context_refs (nekonstruktibilna bez njih ⇒ no-overclaim);
  ruta **isključivo** kroz proposal dispatcher; poruka je proposal, nikad direktan poziv;
  `context_refs` su točno F4 ContextLoom hashevi.
- **Seal:** `test_p6f5_3_signal_contract.py` — `SignalMessage` bez mandate/refs nekonstruktibilan;
  history rekonstruiran čisto iz tracea; nema signal-lokalnog storea; `SIGNAL_CHAT` window
  ne izvršava ništa.
- **Dispatch prompt:** _"Implementiraj F5.3: `SignalMessage` s obveznim identity/role/mandate_id/
  room_id/context_refs (konstruktor odbija bez njih), `SIGNAL_CHAT` FloatingWindowKind
  (contract-only), history isključivo iz tracea (nula vlastitog stanja), poruka→ProposalEnvelope.
  context_refs = F4 ContextLoom hashevi. Seal `test_p6f5_3_signal_contract.py`."_

### F5.4 — Library v1 ujedinjeni read-model (flag `AUREL_FRONT_SERVER`)

- **Files:** novo `library_read_model.py` (`LibraryReadModel` komponira
  `MemoryProjection.from_trace` + `doc_registry` path mapiranje + `TraceExportManifest`;
  metode `assets()`, `provenance_chain(id)`, `versions(id)`, `memory_by_tier()`, `rejected()`);
  edit `front_server/read_models.py` (`GET /read/library`).
- **NC:** "Library" je **ime projekcije, ne novi store**; trace ostaje izvor istine; truth
  labeli se propagiraju kao **MIN** podložnih zapisa; nula write puta; time-travel je F8
  (ovdje UNAVAILABLE seam).
- **Seal:** `test_p6f5_4_library_read_model.py` — Library == trace-izvedeno; dodan memory event
  deterministički mijenja projekciju; truth label MIN dokazan; zero-write.
- **Dispatch prompt:** _"Implementiraj F5.4: `LibraryReadModel` komponira MemoryProjection +
  doc_registry + TraceExportManifest u jedan read-only read-model (assets/provenance/versions/
  memory_by_tier/rejected). Ime projekcije, ne store; truth label = MIN; time-travel = F8
  UNAVAILABLE. Seal `test_p6f5_4_library_read_model.py`."_

### F5.5 — HQ.Command read-model (flag `AUREL_FRONT_SERVER`)

- **Files:** novo `front_server/hq_command.py` (`HQCommandReadModel`: živi status runova +
  approval inbox (F5.2) + budget burn (`budget.py`) + Watchtower alert feed **seam**); edit
  `front_server/read_models.py` (`GET /read/hq/command`).
- **NC:** čista kompozicija živih projekcija; Watchtower je F7 ⇒ alert feed je **PARTIAL**
  seam (prazan/deklariran UNAVAILABLE, ne lažan); prediktivni dio deklariran UNAVAILABLE.
- **Seal:** `test_p6f5_5_hq_command.py` — read-model komponira status+pending+budget; alerti
  UNAVAILABLE seam eksplicitan; zero-write.
- **Dispatch prompt:** _"Implementiraj F5.5: `HQCommandReadModel` = živi run status + F5.2
  approval inbox + budget burn + Watchtower alert **seam** (F7, UNAVAILABLE). Prediktivno
  UNAVAILABLE. Seal `test_p6f5_5_hq_command.py`."_

### F5.6 — Board v1 decision journal (flag `AUREL_FRONT_BOARD`)

- **Files:** novo `front_server/board.py` (`BoardDecision` = governed record; `board_journal`
  projekcija iz tracea; `convert_to_proposal(decision)` emitira `ProposalEnvelope` kroz ista
  vrata). Edit `read_models.py` (`GET /read/board`).
- **NC:** Board odluka je **record, ne izvršenje**; "Convert to Proposal" ide kroz istu jednu
  vrata (F5.0); nema direktnog izvršenja; async (hrani tjedni review); real-time debata = LATER.
- **Seal:** `test_p6f5_6_board_journal.py` — convert-to-proposal se reducira na `runtime.submit`;
  Board je projekcija+proposal, bez drugog puta.
- **Dispatch prompt:** _"Implementiraj F5.6: `BoardDecision` governed record, `board_journal`
  projekcija, `convert_to_proposal`→ProposalEnvelope kroz F5.0 vrata. Async decision journal;
  real-time = LATER. Seal `test_p6f5_6_board_journal.py`."_

### F5.7 — WorkOPS surface: Chat + Code (flag `AUREL_FRONT_WORKOPS`)

- **Files:** novo `front_server/workops.py` (`WorkOpsChatReadModel` = perzistentna Library
  povijest + task tracking + tool-invocation s inline approval hookom (F5.2); `WorkOpsCodeReadModel`
  = read-only file browser projekcija + governed tool pozivi + F3-adapter Claude Code sesije
  vidljive). Edit `read_models.py`.
- **NC:** file browser **read-only** (nema write puta); terminal/tool pozivi su **governed
  proposals** kroz F5.0; AI-editor/kolaboracija = **LATER** (UNAVAILABLE); Claude Code sesije
  su F3 adapter (ako F3 nije sletio, deklariran UNAVAILABLE seam, ne lažan).
- **Seal:** `test_p6f5_7_workops.py` — WorkOPS tool poziv je proposal kroz jedna vrata; file
  browser nekonstruktibilno-write; AI-editor UNAVAILABLE eksplicitan.
- **Dispatch prompt:** _"Implementiraj F5.7: WorkOPS Chat (Library povijest + task tracking +
  inline approval) i Code (read-only file browser + governed tool pozivi + F3 Claude Code
  sesije vidljive). File browser read-only, tool pozivi = proposals kroz F5.0, AI-editor =
  LATER UNAVAILABLE. Seal `test_p6f5_7_workops.py`."_

### F5.8 — React Front v1 wiring (`web/shell`) (flag: build-time, gated na server)

- **Files:** edit `web/shell/src/components/SurfacePanel.tsx` (per-surface sadržaj),
  novo `components/SignalPanel.tsx` (chat area + inline `context_ref` metadata),
  `components/ApprovalInbox.tsx`, `components/LibraryExplorer.tsx`, `components/BoardJournal.tsx`,
  `components/FloatingWindowRenderer.tsx` (uklj. `SIGNAL_CHAT`); novo `src/frontClient.ts`
  (HTTP + WebSocket klijent prema F5.0a/F5.0b serveru; native browser `WebSocket`, bez lib);
  edit `types.ts` (DTO za ProposalEnvelope/SignalMessage/approvals/library); edit
  contract-binding testove.
- **NC:** UI **nema** put do backenda osim F5.0 servera; sve mutacije preko `POST /proposals`;
  TS DTO se poklapaju s Python kontraktima (binding test); lint/build provjera da nema
  direktnog importa podsustava; server-OFF ⇒ static-fixture dev način (bez lažnog live).
- **Seal:** `web/shell` vitest contract-binding proširen (DTO paritet) + `test_p6f5_8_ui_one_door.py`
  (server-strana: UI čin ⇒ proposal; nijedan drugi endpoint mutira).
- **Dispatch prompt:** _"Implementiraj F5.8: proširi `SurfacePanel` per-surface; dodaj SignalPanel
  (context_ref inline), ApprovalInbox, LibraryExplorer, BoardJournal, FloatingWindowRenderer
  (SIGNAL_CHAT); `frontClient.ts` HTTP+SSE prema F5.0. Sve mutacije preko POST /proposals; DTO
  paritet u binding testu; server-OFF⇒static fixture. Seali: vitest binding + `test_p6f5_8_ui_one_door.py`."_

### F5.9 — Front v1 exit seal + CLI + projekcija (flag: n/a, seal je derived)

- **Files:** novo `front_seal.py` (**derived** exit seal: svaki F5.0→F5.8 slajs importabilan
  AND report prisutan; UNAVAILABLE registry: `wss_tls_remote_transport`,
  `aureleu_role_fluid_dispatcher`, `watchtower_alerts`, `workops_ai_editor`, `library_time_travel`
  — svaki s razlogom i vlasnikom; overclaim guardovi hard-wired False); novo `front_projection.py` (read-only projekcija punog
  Signal→approval→exec→Library runa); edit `cli_modules/f5_commands.py` + `cli.py`
  (`aurel front seal [--json]`, `aurel front serve`, `aurel front demo`).
- **NC:** seal je **izveden**, nikad self-assigned boolean; missing modul/report ⇒ BLOCKED;
  odgođene površine ostaju eksplicitne u UNAVAILABLE registru.
- **Seal:** `test_p6f5_9_front_exit_seal.py` — **north star scenarij** (§7) end-to-end kao
  automatiziran test; derived SEALED kad su svi prisutni, BLOCKED na bilo kojem missing;
  overclaim guardovi False; nula direktnih UI poziva dokazana.
- **Dispatch prompt:** _"Implementiraj F5.9: `front_seal.py` derived exit seal (svi slajsevi
  importabilni + reporti prisutni; UNAVAILABLE registry s vlasnicima; overclaim guardovi False),
  `front_projection.py`, `aurel front seal/serve/demo`. Seal `test_p6f5_9_front_exit_seal.py`
  vozi §7 north-star scenarij end-to-end i dokazuje nula direktnih UI poziva."_

---

## 4. Preporučeni redoslijed (walking skeleton prvo)

1. **Walking skeleton (jedan intent kroz cijeli seal put):** F5.0a → F5.0b → F5.2 → F5.3(min)
   → dovoljno za: Signal poruka → proposal → pending approval → approve → submit → vidljivo.
   Ovo je najmanji rez koji dokazuje "jedna vrata" žive. (F5.0b se može i odgoditi iza F5.2 ako
   se skeleton prvo vozi HTTP pollom, ali WS je operaterska v1 odluka pa ide rano.)
2. **Projekcijski sloj:** F5.1 → F5.4 → F5.5. Sve read-only, jeftino, paralelizabilno.
3. **Stupovi:** F5.6 (Board) → F5.7 (WorkOPS).
4. **UI:** F5.8 (React) — thicken tek kad su read-modeli živi.
5. **Pečat:** F5.9 derived exit seal + `agent/reports/AUREL_F5_*` report; puni suite; merge
   `feat/f5-front-v1` → `master` (CODEOPS, mirror `AUREL_F4_4_EXIT_SEAL.md`).

Kritičan put je F5.0→F5.2 (most). Sve ostalo visi o njima; ako most nije čist, ostalo je UI boja.

---

## 5. Cross-cutting invarijante (svaki slajs mora držati)

- **Entity proposes, runtime disposes.** Svaka mogućnost se reducira na `ProposalEnvelope` →
  `runtime.submit`, governed `request_write`, ili read-only projekciju. Nema drugog izvršioca.
- **Jedna vrata.** UI nema put do backenda osim `POST /proposals`. Read je čista projekcija.
  Seal to dokazuje strukturno (točno jedna mutation ruta), ne heuristikom.
- **Trace = jedini izvor istine.** Svaka mutacija → hash-chained record. Projekcije (read-modeli,
  Library, inbox, Board journal) su projekcije nad traceom; nikad novi store.
- **Fail-closed.** Nepoznato/neriješeno/bez mandata/bez ključa ⇒ DENY / escalate / pošteni
  UNAVAILABLE|PARTIAL|BLOCKED. Neriješen approval ostaje pending, nema tihog auto-approvea.
- **No-overclaim (strukturno).** Booleani koji bi lagali su nekonstruktibilni: `SignalMessage`
  bez mandate/refs, `claims_websocket_transport`, `claims_aureleu_dispatcher_live`,
  `claims_watchtower_live`, `claims_workops_ai_editor`. Truth labeli propagiraju kao MIN.
- **Additive-behind-flags.** `AUREL_FRONT_SERVER`/`_SIGNAL`/`_BOARD`/`_WORKOPS` default OFF;
  off put byte-identičan (dokaz: flag-off test + puni suite).
- **Stdlib-only, deterministički.** `http.server`+SSE, bez runtime ovisnosti; projekcije
  determinističke (sortirane po `(…, id)`, nikad `hash()`); nula RNG.

---

## 6. Odgođeni seamovi / UNAVAILABLE registry (nose se naprijed)

| Seam | Status u F5 | Vlasnik / kada |
|---|---|---|
| WebSocket transport | **ŽIVO v1** (localhost ws, stdlib RFC 6455) | F5.0b |
| wss/TLS + remote WebSocket | UNAVAILABLE (v1 = localhost, bez TLS) | Tauri-Rust, po mjerenju (plan §6) |
| AurelEU role-fluid dispatcher | PARTIAL (jedna persona) | **F6** |
| Mandati (puna rezolucija/enforcement) | PARTIAL (`mandate_id` polje obavezno, sadržaj default) | **F6** |
| Watchtower alert feed | PARTIAL seam (prazan) | **F7** |
| WorkOPS AI-editor / kolaboracija | UNAVAILABLE (LATER) | poslije F7 |
| Library time-travel | UNAVAILABLE | **F8** |
| Claude Code sesije u WorkOPS.Code | ovisi o F3 adapteru | **F3** |
| Real-time multi-party Board | UNAVAILABLE (LATER) | po potrebi |
| MCP client bridge (direction-B) | UNAVAILABLE (svjesno odgođen) | poslije F5 |

---

## 7. Front v1 exit seal — north star scenarij (F5.9 test)

Automatizirani end-to-end test koji je definicija uspjeha F5:

1. Operator iz **Signala** zada intent (`SignalMessage` s identity+role+mandate_id+context_refs).
2. Poruka → `ProposalEnvelope` → dispatcher → AurelEU (PARTIAL) predloži plan → `runtime.submit`.
3. Policy zahtijeva approval → **pending u HQ.Command inbox projekciji**.
4. Operator approve kroz `POST /proposals` (approval odluka = governed record).
5. `runtime.submit` izvrši → izvršenje **vidljivo u WorkOPS** read-modelu.
6. Artefakt + Board odluka **u Library** (ujedinjena projekcija).
7. Cijeli lanac **replayabilan** iz tracea; **nula direktnih poziva iz UI-ja** (dokazano:
   točno jedna mutation ruta, sve ostalo projekcija).

Sve pod `standard` profilom (F1), bez ključa u artefaktima (F2 redakcija), WebSocket
(localhost, stdlib RFC 6455) transport, overclaim guardovi False (`claims_remote_websocket`,
`claims_wss_tls`, `claims_aureleu_dispatcher_live` = False).

---

---

## 8. Dubinska razrada — F5.2 Approval inbox (killer modul)

**Postojeći temelj (grounded):** `approval.py` već ima cijeli kontrakt — `ApprovalRiskClass`
R0–R5 (`:21–27`), `ApprovalRequest` (request_id, command, decision, risk_class, action_summary,
side_effect_type, preview, affected_paths, required_capabilities, policy_verdict,
confirmation_level, strong_warning; `:64–118`), `ApprovalDecision` (outcome, reason, decided_by,
constraints; `:121–138`), `ApprovalReceipt.from_decision` (trace_id, expires_at; `:141–174`),
i `ApprovalPolicy.resolve` koja mapira rizik→requirement (`:195–318`). **Preview i args su već
redigirani** (`_sanitize_args`/`_sanitize_text`, `:494–509`). Ono što fali: gate je **sinkroni
HITL callback** u `runtime.submit` (`runtime.py:309–375`), pa nema perzistentnog inboxa.

**Ključni dizajn — two-phase submit (async approval bez suspenzije pipelinea):**
`runtime.submit` je sinkroni; ne parkiramo ga u sredini. Umjesto toga:

1. **Faza A (propose):** `POST /proposals` → dispatcher zove `runtime.submit` s
   **`DeferredApprovalGate`** koji na `request()` **ne blokira**: appenda `ApprovalRequest` u
   trace kao pending marker i vrati `ApprovalDecision(outcome=DEFERRED)` (outcome **već postoji**,
   `:40`). Komanda završi kao **BLOCKED/parked** transition (fail-closed), ništa se ne izvrši.
2. **Faza B (decide):** `POST /proposals/{request_id}/decide` s operaterskom
   `ApprovalDecision` → dispatcher **ponovno submitta ISTU komandu** s `PreDecidedApprovalGate`
   koji vrati operaterovu odluku. APPROVED ⇒ pipeline dovrši; DENIED ⇒ BLOCKED transition
   cross-linkan na pending request.

**`PendingApprovalProjection.from_trace` (`approval_inbox.py`):** čita approval evente,
**pari** `ApprovalRequest` s njegovom `ApprovalDecision`; **nespareni = pending**. Deterministički
sortiran po `(created_at, request_id)`. Status po zapisu: `pending | approved | denied | expired`.

**Mandate-bound approval (fail-closed):** operaterov `decided_by` mora odgovarati
`operator_identity` iz `ProposalEnvelope`; `approved_scope` (iz `affected_paths`) koji **prelazi**
mandatni doseg je odbijen — `ApprovalDecision` izvan mandata je nekonstruktibilan/rejected.
(Puna mandatna rezolucija je F6; u F5 default single-operator mandat + doseg-check seam.)

**Rizik → inbox ponašanje (iz `ApprovalPolicy.resolve`):**
- **R0/R1** → `auto_allow=True`: **nema** inbox unosa (izvrši se), ali traceano.
- **R2–R4** → `required=True`: **inbox unos**, čeka operatera; preview obavezan.
- **R5** → `deny_r5_by_default=True` ⇒ `auto_deny=True`: prikazan u inboxu kao **auto-denied**;
  operator ga ne može tiho odobriti — override traži eksplicitni `confirmation_level=2`
  (two-step), inače ostaje denied. Nikad tihi allow.

**TTL/expiry (fail-closed):** pending unos dobiva TTL; istekli ⇒ tretiran kao **DENIED**, nikad
tihi allow. Projekcija označi `expired`. `ApprovalReceipt.expires_at` (`:152`) je nosač.

**Batch odluke:** dozvoljene kao **sugar nad N pojedinačnih** `ApprovalDecision` zapisa — svaki
traceano, svaki prolazi svoj risk floor. **Nema** "approve all" koji preskače per-request rizik.

**DTO za React (`ApprovalInboxItemDTO`):** `{request_id, command_id, risk_class, action_summary,
side_effect_type, affected_paths[], required_capabilities[], preview:{summary, diff_summary,
warnings[], reversibility}, confirmation_level, strong_warning, created_at, status, mandate_id}`
— sve iz već-redigiranih `to_dict()`, **nula sirovih tajni**.

**Seal proširenja (`test_p6f5_2_proposal_approval.py`):** two-phase propose→pending→decide→submit
lanac u traceu; DEFERRED parkira bez izvršenja; R5 auto-denied nije tiho odobriv; izvan-mandata
decision odbijen; expired⇒denied; batch = N zapisa; inbox DTO bez tajni.

---

## 9. Dubinska razrada — F5.3 Signal kontrakt (nula vlastitog stanja)

**Postojeći temelj (grounded):** `context_refs` su točno F4 ContextLoom hashevi —
`context_assembly_summary` stavlja `context_ref=…` u **summary** (`context_trace.py:26–32`) pa
prežive replay; `context_refs_from_replay(replay)` ih rekonstruira **samo iz summarya**
(`:60–76`). `ContextItem.to_dict()` daje provenance **bez sirovog sadržaja** (`context_item.py:76–85`),
`instruction_eligible=False` za external-origin (`:72–74`) — Signal poruke koje referenciraju
scraped/MCP sadržaj nose ga kao **data-only**, nikad kao instrukciju.

**`SignalMessage` (frozen dataclass, `front_server/signal.py`):**
`{message_id, room_id, operator_identity, current_role, mandate_id, context_refs: tuple[str,...],
intent_text, created_at}`. **`__post_init__` odbija** praznu `operator_identity` / `mandate_id`
/ `context_refs` → **nekonstruktibilna** "autenticirana poruka" bez identiteta/mandata/konteksta
(no-overclaim, strukturno). `intent_text` je operator-origin (`SourceKind.OPERATOR`,
instruction-eligible); referencirani vanjski sadržaj ostaje data-only preko `context_refs`.

**Nula vlastitog stanja:** **nema** Signal storea. Poruka → `ProposalEnvelope` (polja se 1:1
mapiraju: operator_identity, current_role, mandate_id, context_refs, intent) → dispatcher →
`runtime.submit`; traceano. **History = projekcija:** trace se filtrira po signal-message
eventima + `room_id`; `context_refs_from_replay` vrati refove. UI dohvаti povijest sobe iz
`GET /read/signal/history?room={id}` — čista projekcija, nikad lokalni DB.

**context_refs inline (leak-safe):** za svaku poruku UI zove `GET /read/context/{ref}` →
`ContextBundle.to_dict()` metadata: `{items, source_kind mix, has_external, dropped, compressed,
per-item: source_kind/label/instruction_eligible/content_hash/est_tokens}` — **nikad sirovi
sadržaj** (doktrina `context_trace.py:8–9`). Badge pokazuje "N stavki, K vanjskih (fenced),
compressed/dropped" uz svaku poruku.

**Sobe v1 (`room_id` tag, ne store):** operator↔AurelEU (glavna), po-poslu sobe (F7 tag),
agent-to-agent **read-only digest**. Real-time multi-party = LATER.

**`SIGNAL_CHAT` FloatingWindowKind (`floating_window.py:39–45`):** dodaj enum vrijednost;
descriptor **ostaje contract-only** — `mutates_runtime=False`, `executes_actions=False`,
`is_live_ui=False` (postojeći `assert_floating_window_does_not_execute/mutate/…` `:158–199`
i dalje vrijede). Živi chat je React (F5.8); **window je projekcijski kontejner**, sadržaj dolazi
iz read-modela, akcije su proposals. Time floating_window zakon ostaje nenarušen.

**AurelEU seam (PARTIAL):** F5 ruta ide kroz thin dispatcher (jedna default persona);
role-fluid persona switch je F6 (`claims_aureleu_dispatcher_live=False`). `current_role` polje
postoji i traceano, ali switching mehanika dolazi u F6.

**Seal proširenja (`test_p6f5_3_signal_contract.py`):** `SignalMessage` bez identity/mandate/refs
nekonstruktibilan; history rekonstruiran **čisto** iz tracea (nula lokalnog storea); `context_refs`
prežive replay (reuse `context_refs_from_replay`); `GET /read/context/{ref}` ne vraća sirovi
sadržaj; `SIGNAL_CHAT` descriptor ne izvršava/mutira; poruka→proposal, nikad direktan poziv.

---

## 10. Dubinska razrada — F5.8 React UI sloj (jedna vrata, DTO paritet)

**Postojeći temelj (grounded):** `types.ts` je **Python-owned DTO mirror**
(`WebShellReadModelDTO` + surface/client/evidence/no-overclaim DTO-i, `:1–77`); `App.tsx`
`AppShell` renderira data-driven SurfaceSelector (iz `in_surface_selector`/`in_topbar_right`) +
**SurfacePanel stub** + EvidenceRefsPanel + NoOverclaimPanel; `contract-binding.test.ts` tvrdi
DTO oblik; `TruthLabelBadge` postoji. Sve se hrani iz **statičkog** `public/web-shell-read-model.json`.

**`frontClient.ts` — JEDINA točka pristupa backendu:**
- `GET /read/*` (fetch) — projekcije; `POST /proposals` + `POST /proposals/{id}/decide` — mutacije;
  `WebSocket('/ws')` (native, bez lib) — Signal stream + approval push.
- **Enforcement:** nijedan drugi fajl ne smije importati `fetch`/`WebSocket` direktno — lint
  pravilo (`no-restricted-globals`/custom) + server-strani seal. Sve mutacije prolaze
  `frontClient.propose(envelope)`.

**Novi DTO-i (mirror Python `to_dict()`):** `ProposalEnvelopeDTO`, `SignalMessageDTO`,
`ApprovalInboxItemDTO` (§8), `ContextRefSummaryDTO`, `LibraryEntryDTO`, `BoardDecisionDTO`,
`HQCommandDTO`. Svaki zrcali jednu Python dataclass; **DTO paritet strategija:** Python na buildu
emitira `contract_manifest.json` (polja+tipovi po DTO-u); vitest binding test tvrdi da se
`types.ts` interfaces poklapaju s manifestom → hvata drift (proširenje postojećeg
`contract-binding.test.ts` obrasca).

**Komponente (SurfacePanel dispatch po `surface_id`):**
- `HQCommandPanel` → **ApprovalInbox** (lista pending, R0–R5 badge, preview diff/warnings,
  approve/deny gumbi → `POST /proposals/{id}/decide`) + live status + budget burn + Watchtower seam.
- `SignalPanel` → chat area, message list iz `GET /read/signal/history`, **ContextRefBadge** po
  poruci (§9), compose box → `frontClient.propose`. Renderira se i kao `SIGNAL_CHAT` floating window.
- `LibraryExplorer` (F5.4 read-model), `BoardJournal` (F5.6, "Convert to Proposal" gumb →
  propose), `WorkOpsPanel` (F5.7 Chat/Code).
- `FloatingWindowRenderer` — renderira descriptore (`SIGNAL_CHAT` / `CONTEXT_VIEW` / `INSPECT_PANEL`);
  descriptor ostaje contract-only, renderer čita read-modele.

**Server-OFF fixture način (pošteno):** `frontClient` detektira da nema servera → fallback na
statički `public/*.json` **i onemogući sve proposal akcije**, prikaže "read-only fixture mode".
**Nikad** ne lažira uspješan submit offline — nema lažnog "success".

**Truth label svugdje:** reuse `TruthLabelBadge`; svaki živi podatak nosi `ShellTruthLabel`;
`LIVE` **samo** kad stvarno iz žive trace projekcije, inače `READ_ONLY`/`DEV_FIXTURE`/`UNAVAILABLE`
— nema lažnog `LIVE`.

**Seal (`test_p6f5_8_ui_one_door.py` + vitest):** binding test dokazuje DTO paritet s
`contract_manifest.json`; server-strani seal dokazuje da UI čin ⇒ proposal i da **nijedan drugi
endpoint** ne mutira; lint dokazuje nula direktnih `fetch`/`WebSocket` izvan `frontClient.ts`;
server-OFF ⇒ akcije onemogućene (nema lažnog submita).

---

**One-line pickup:** _"Čitaj `agent/reports/AUREL_PLAN_02_F5_FRONT_V1_DISPATCH.md`; kreni F5.0a
('jedna vrata' HTTP temelj) na grani `feat/f5-front-v1` per §3, walking-skeleton redoslijedom §4;
detaljne razrade killer-modula u §8 (approval inbox), §9 (Signal), §10 (React)."_
