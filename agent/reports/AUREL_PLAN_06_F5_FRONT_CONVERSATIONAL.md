# AUREL PLAN 06 — F5 Front v1 (konsolidiran): Conversational + next-gen komunikacijski sustav

_Cut: 2026-07-09, from master @ post-F4B merge._
_Usvaja paralelni dispatch temelj `AUREL_PLAN_02_F5_FRONT_V1_DISPATCH.md` (jedna vrata, HTTP+WS,_
_projekcije, approval inbox, Library, exit seal) i dodaje razgovorni sloj + next-gen-ready contract + F5.N._

---

## 1. Cilj i doktrina

Po završetku F5 operater **priča s LLM-om kroz Signal i kroz WorkOPS chat — povezano, s kontekstom**,
a governed tool-akcija ostaje netaknuta. Razgovor NIJE zaobilazak governancea nego **treći governed
mod istih jednih vrata (`POST /proposals`):**

- **ANSWER** — LLM razgovorni odgovor (F2 router nad ContextLoom kontekstom); budget-charged, traced, bez tool-izvršenja.
- **PROPOSE** — model vrati validan plan → approval inbox → `runtime.submit` (north-star put, nepromijenjen).
- **ACT** — direktna governed tool-akcija (postojeći two-phase submit).

Odluka answer/propose je **strukturna** (`PlanValidator` valid ⇒ propose), ne heuristika koja bi lagala.

---

## 2. Utemeljeno stanje (reuse, ne graditi)

- **Most ne postoji** → gradi se `front_server/` (jedini UI↔backend put).
- **F4 ContextLoom** (`context_loom/`): `assemble`, `context_ref`, trace-binding, DATA-fence.
- **F4.3** (`entity_loom_loop.py`): `RouterPlanner`, `Planner` — PROPOSE grana.
- **F2** (`model_router.py`, `model_cassette.py`, `secrets.py`): `complete_with_usage`, cassette-default, live keys, redakcija.
- **`runtime.submit`** — jedini izvršni put; **budget** `precheck_llm`/`charge_llm`; **trace** `PraxisEventRecord`.
- **B2** (`reasoning/difficulty_estimator.py`), **A0** (`memory_bitemporal.py`), **truth** (`MemoryTruthState`),
  **P2.5 handoff** (`aurel_shell/cross_surface_handoff*.py`) — temelji za F5.N.

---

## 3. Arhitektura: "jedna vrata" + transport

- `GET /read/{model}` — čiste projekcije iz tracea (read-only).
- `POST /proposals` — **JEDINA mutacija.** Svaki UI čin = `ProposalEnvelope{kind: converse|act}` → dispatcher.
- `GET /ws` — WebSocket (RFC 6455, stdlib, localhost, bez TLS) — bidirekcionalni stream; dolazna poruka
  se reducira na isti dispatcher (nije drugi izvršni put).

**Master flag `AUREL_FRONT_SERVER`** (OFF ⇒ server se ne konstruira, runtime byte-identičan).

---

## 4. F5.C — Conversation Engine + **NEXT-GEN-READY CONTRACT**  ★ jezgra

`front_server/conversation.py`. Kontrakt se dizajnira da **od prvog dana nosi polja/šavove za sve
N1–N8**, prazno/default dok pripadni F5.N slice ne oživi — nula retrofita kasnije.

```
@dataclass(frozen=True)
class ConversationTurn:              # operatorova poruka
    turn_id, room_id, operator_identity, role, mandate_id       # N5: mandate_id obavezan
    text
    context_refs: tuple[str,...]     # N1: priloženi ContextLoom refovi
    bitemporal_stamp: BiTemporalStamp  # N8: as-of audit od početka
    created_at

@dataclass(frozen=True)
class ConversationReply:             # LLM odgovor
    mode: ANSWER | PROPOSE | UNAVAILABLE
    text
    context_ref: str                 # N1: bundle hash (per-turn provenance)
    source_refs: tuple[str,...]      # N1: koji su itemi ušli (per-claim seam)
    truth_label: MemoryTruthState    # N2: MIN(context items); model NE diže
    profile_used: str                # N3/N7: koji je profil odabran
    usage_substantiated: bool        # F2 honest token accounting
    proposal: Optional[ProposalEnvelope]   # PROPOSE mod
    bitemporal_stamp: BiTemporalStamp      # N8

class ConversationEngine:
    def __init__(self, runtime, router, memory, *, profile_selector, redactor): ...
    def respond(self, turn) -> ConversationReply:
        1. record operator turn (governed, hash-chained, bitemporal-stamped)
        2. bundle = assemble_context(turn)   # room history + memory recall + turn.context_refs
                                             # budget-fit + compress; vanjsko DATA-fenced (F4)
        3. bind context_ref u trace
        4. profile = profile_selector(turn, bundle)   # N3 seam: default fiksni; N3 zamijeni estimatorom
        5. raw, model, usage = router.complete_with_usage(profile, SYS, bundle.to_prompt())
                                             # cassette default; budget-charged; no-key ⇒ UNAVAILABLE
        6. mode = PROPOSE if PlanValidator(raw).valid else ANSWER
        7. truth_label = MIN(item.truth_label for item in bundle.items)   # N2
        8. record reply s context_ref + truth_label + profile
        9. return ConversationReply(...)
```

- `profile_selector` je **seam**: default vraća fiksni `chat` profil; N3 ga zamijeni difficulty-estimatorom.
- `RoomHistoryProjection.from_trace(room_id)` — history isključivo iz tracea (nula vlastitog stanja).
- Flag `AUREL_FRONT_CONVERSATION` (OFF).
- **NC:** razgovor governed (budget+trace+ContextLoom); cassette determinizam; no-key ⇒ UNAVAILABLE (ne lažni);
  PROPOSE ide kroz F5.2 jedna vrata; truth_label MIN strukturno; history iz tracea; svaki turn bitemporalno oštampan.
- **Seal `test_p6f5_c_conversation.py`:** operator turn → ANSWER pod kasetom (deterministički), context_ref
  replay-safe; room history iz tracea; PROPOSE kad model vrati plan (→ProposalEnvelope, ne izvršenje);
  no-key+no-cassette ⇒ UNAVAILABLE; budget charged; vanjski context_ref DATA-fenced; truth_label==MIN; turn bitemporalno oštampan.

---

## 5. Puna F5 dekompozicija (svi slice-ovi)

Legenda: **★** kritični put za razgovor · flag default OFF · seal = pytest fajl.

### F5.0a — "Jedna vrata" HTTP server  ★  (flag `AUREL_FRONT_SERVER`)
Novo `front_server/{server,routes,proposal_dispatcher}.py` (stdlib `ThreadingHTTPServer` + deklarativna route
tablica gdje je **točno jedna** `mutation=True` ruta = `POST /proposals` → `runtime.submit`). `aurel front serve` CLI.
**NC:** stdlib-only; točno jedna mutation ruta; flag-OFF ⇒ server nekonstruktibilan; nijedan handler ne zove
podsustav mimo dispečera/projekcija. **Seal** `test_p6f5_0a_one_door.py` (enumeria rute, tvrdi jednu mutation rutu, flag-off nekonstruktibilnost).

### F5.0b — WebSocket transport (RFC 6455, stdlib)  ★  (flag `AUREL_FRONT_SERVER`)
Novo `front_server/websocket.py` (ručni handshake `Sec-WebSocket-Accept`=base64(SHA1(key+GUID)), frame
encode/decode + unmasking, ping/pong, close — stdlib `socket`/`hashlib`/`base64`); `GET /ws` upgrade; `/ws`
non-mutation push. Dolazna poruka → isti dispatcher. Localhost-only, bez TLS.
**NC:** stdlib-only; `/ws` non-mutation; server-OFF ⇒ nema WS. `claims_remote_websocket`/`claims_wss_tls`=False.
**Seal** `test_p6f5_0b_websocket.py` (točan accept-key iz RFC vektora; masked frame round-trip; nemaskiran client frame odbijen).

### F5.C — Conversation Engine + next-gen-ready contract  ★  (§4)  (flag `AUREL_FRONT_CONVERSATION`)

### F5.2 — Proposal dispatch + perzistentni approval inbox (`converse`+`act`)  ★  (flag `AUREL_FRONT_SERVER`)
Novo `proposal_envelope.py` (`ProposalEnvelope{kind, operator_identity, role, mandate_id, context_refs, intent}`),
`approval_inbox.py` (`PendingApprovalProjection.from_trace` — pari `ApprovalRequest`↔`ApprovalDecision`, nespareni=pending).
**Two-phase submit:** Faza A (`DeferredApprovalGate` → pending marker + BLOCKED/parked, ništa se ne izvrši);
Faza B (`POST /proposals/{id}/decide` → `PreDecidedApprovalGate` → re-submit iste komande; APPROVED dovrši, DENIED BLOCKED).
Dispatcher: `converse`→`ConversationEngine.respond`; `act`→two-phase submit.
**NC:** approval odluka = governed record; izvan mandata odbijen; neriješeno ostaje pending (nema tihog auto-approvea);
AurelEU PARTIAL (jedna persona, `claims_aureleu_dispatcher_live=False`). **Seal** `test_p6f5_2_proposal_approval.py`.

### F5.3 — Signal kontrakt + `SIGNAL_CHAT` + chat na F5.C  ★  (flag `AUREL_FRONT_SIGNAL`)
Novo `front_server/signal.py` (`SignalMessage` obavezni identity/role/mandate_id/room_id/context_refs —
konstruktor odbija bez njih) → `converse` proposal → `ConversationEngine`. `SIGNAL_CHAT` FloatingWindowKind
(contract-only). History = `RoomHistoryProjection` (nula vlastitog stanja). Reply streaman preko WS s context_ref.
**NC:** nula vlastitog stanja; svaka poruka nosi identity+role+mandate+refs (nekonstruktibilna bez); ruta samo kroz
dispatcher; context_refs = F4 hashevi. **Seal** `test_p6f5_3_signal_chat.py` (poruka→ANSWER reply u room history s context_ref; SignalMessage bez refs nekonstruktibilan; history iz tracea).

### F5.1 — Žive projekcije iz tracea  (flag `AUREL_FRONT_SERVER`)
Novo `front_server/read_models.py` (`GET /read/{model}` → živa projekcija umjesto statičkog fixturea preko
`build_web_shell_read_model(trace=…)`). Server-OFF ⇒ statički fixture dev-fallback (nikad lažni live).
**NC:** čiste projekcije (zero-write), deterministične. **Seal** `test_p6f5_1_live_read_models.py`.

### F5.4 — Library v1 ujedinjeni read-model  (flag `AUREL_FRONT_SERVER`)
Novo `library_read_model.py` (`LibraryReadModel` komponira `MemoryProjection.from_trace` + `doc_registry` +
`TraceExportManifest`; `assets/provenance_chain/versions/memory_by_tier/rejected`). Truth label = MIN. Time-travel = F8 UNAVAILABLE.
**Seal** `test_p6f5_4_library_read_model.py`.

### F5.5 — HQ.Command read-model  (flag `AUREL_FRONT_SERVER`)
Novo `front_server/hq_command.py` (živi run status + F5.2 approval inbox + budget burn + Watchtower alert **seam**
(F7, UNAVAILABLE)). Prediktivno UNAVAILABLE. **Seal** `test_p6f5_5_hq_command.py`.

### F5.7 — WorkOPS Chat na F5.C + Code  ★  (flag `AUREL_FRONT_WORKOPS`)
Novo `front_server/workops.py`: `WorkOpsChatReadModel` = `RoomHistoryProjection(room_id="workops:*")` + task
tracking + inline approval — **isti `ConversationEngine`, drugi room**. `WorkOpsCodeReadModel` = read-only file
browser projekcija + governed tool pozivi (proposals kroz F5.0) + F3 Claude Code sesije vidljive (F3 adapter seam).
**NC:** file browser read-only; tool pozivi = proposals; AI-editor = LATER UNAVAILABLE. **Seal** `test_p6f5_7_workops_chat.py`.

### F5.6 — Board v1 decision journal  (opcionalno, flag `AUREL_FRONT_BOARD`)
Novo `front_server/board.py` (`BoardDecision` governed record; `board_journal` projekcija; `convert_to_proposal`→
ProposalEnvelope kroz F5.0). Async; real-time = LATER. **Seal** `test_p6f5_6_board_journal.py`.

### F5.8 — React Front v1 wiring (`web/shell`)  (build-time, gated na server)
Edit `SurfacePanel.tsx`; novo `SignalPanel.tsx` (chat area + inline context_ref chip + PROPOSE→approval CTA),
`WorkOpsChatPanel.tsx`, `ApprovalInbox.tsx`, `LibraryExplorer.tsx`, `FloatingWindowRenderer.tsx` (`SIGNAL_CHAT`);
novo `frontClient.ts` (`sendMessage(room,text,refs)`→`POST /proposals{converse}`; native `WebSocket` stream).
DTO paritet u binding testu.
**NC:** UI nema put mimo F5.0 servera; sve mutacije kroz `POST /proposals`; server-OFF ⇒ static fixture.
**Seal** vitest binding + `test_p6f5_8_ui_one_door.py`.

### F5.9 — Front v1 derived exit seal + CLI  (seal je derived)
Novo `front_seal.py` (derived: svaki F5.0→F5.8 + F5.C importabilan AND report prisutan; missing ⇒ BLOCKED;
UNAVAILABLE registry — vidi §8; overclaim guardovi hard-False), `front_projection.py` (read-only projekcija punog
runa), `cli_modules/f5_commands.py` (`aurel front seal/serve/demo`).
**North-star test** = **živ LLM razgovor** (§7). **Seal** `test_p6f5_9_front_exit_seal.py`.

---

## 6. F5.N — NEXT-GEN komunikacijski sloj (feature slice-ovi, POSLIJE skeletona)

Kontrakt (§4) već nosi šavove; F5.N su **same značajke**, svaka vlastiti flag + seal, prioritet po vrijednosti.
Nijedan ne mijenja jedna-vrata doktrinu.

| N | Značajka | Šav (već u F5.C) | Što F5.N gradi | Temelj | Seal |
|---|---|---|---|---|---|
| **N1**★ | **Provenance-native** — po-tvrdnji `context_ref` chip; klik→izvor; tvrdnja bez ref-a = crvena zastavica | `reply.source_refs` | span→ref mapiranje + UI chip + Library rezolucija | F4 + F5.4 | `test_p6f5_n1_provenance.py` |
| **N3**★ | **Effort-aware** — B2 difficulty bira profil (jeftino pitanje→jeftin model); vidiš prije slanja + override | `profile_selector` seam | estimator wiring + preview + override | B2 + F2 profili | `test_p6f5_n3_effort.py` |
| **N4**★ | **Streaming** — token-by-token preko WS; cassette streama deterministički; no-key⇒UNAVAILABLE | reply inkrementalan | router `complete_streaming` seam + WS `reply_delta` | F5.0b + F2 | `test_p6f5_n4_streaming.py` |
| **N2** | **Truth-labeled** — odgovor nosi MIN truth label; model ne diže | `reply.truth_label` | UI značka + kalibracija prikaza | `MemoryTruthState` | `test_p6f5_n2_truth.py` |
| **N5** | **Room = governed kanal s mandatom** — PROPOSE gated na sobin mandat | `mandate_id` obavezan | mandat enforcement (→ F6 puni) | AuthorityScope + F6 | `test_p6f5_n5_room_mandate.py` |
| **N6** | **Cross-surface handoff** — razgovor Signal↔WorkOPS bez gubitka konteksta | history=trace-projekcija po room_id | P2.5 handoff kompozicija + preview | P2.5 (sealed) | `test_p6f5_n6_handoff.py` |
| **N7** | **Challenger turn** — isti kontekst, drugi (jeftin) profil pobija/potvrđuje; u Board journal | `profile_selector` seam | drugi respond() + Board zapis | F2 challenger + F5.6 | `test_p6f5_n7_challenger.py` |
| **N8** | **Bitemporal audit** — replay sobe "kako je izgledala u T"; halucinacija forenzički debuggabilna | `turn.bitemporal_stamp` | as-of replay view + context_ref set@T | A0 + as-of replay | `test_p6f5_n8_bitemporal.py` |

**Redoslijed F5.N:** N1 → N3 → N4 (must: provenance + štednja + streaming), pa N2 → N5 → N6 → N7 → N8 inkrementalno.

---

## 7. North star (F5.9 test) — definicija uspjeha

**Grana A (razgovor, primarni cilj):** operater u Signalu pošalje poruku → `ConversationEngine` sastavi
ContextLoom kontekst → LLM (cassette) **ANSWER reply s `context_ref`** → vidljivo u room history → replayabilno.
Isto kroz WorkOPS chat (drugi room, isti engine).

**Grana B (governed akcija):** operater zada intent → PROPOSE plan → **pending u HQ.Command inbox** → approve kroz
`POST /proposals` (governed record) → `runtime.submit` izvrši → **vidljivo u WorkOPS** → artefakt + odluka **u
Library** → cijeli lanac replayabilan, **nula direktnih UI poziva** (točno jedna mutation ruta).

Sve pod `standard` (F1), bez ključa u artefaktima (F2 redakcija), WebSocket (localhost, stdlib), overclaim guardovi False.

---

## 8. Redoslijed izgradnje (walking skeleton = živ razgovor prvi)

1. **F5.0a → F5.0b** — most (HTTP + WS).
2. **F5.C** — conversation engine (s next-gen-ready kontraktom).
3. **F5.3(min)** — Signal poruka → F5.C → reply.  **▶ Milestone 1: pričam s LLM-om kroz Signal.**
4. **F5.2** — approval inbox + `converse`/`act` dispatch.
5. **F5.7** — WorkOPS chat na isti engine.  **▶ Milestone 2: pričam s LLM-om kroz WorkOPS.**
6. **F5.1 / F5.4 / F5.5** — žive projekcije, Library, HQ.Command.
7. **F5.8** — React chat UI (Signal + WorkOPS).
8. **F5.N** — N1 → N3 → N4 (pa ostatak).
9. **F5.9** — derived exit seal + CLI; puni suite; merge `feat/f5-front-v1` → master.

Kritični put za cilj: **F5.0 → F5.C → F5.3 → F5.7.**

---

## 9. Cross-cutting invarijante (svaki slice drži)
- **Entity proposes, runtime disposes** — sve na `ProposalEnvelope` → `runtime.submit` / governed write / read projekcija.
- **Jedna vrata** — UI nema put mimo `POST /proposals`; seal dokazuje strukturno (točno jedna mutation ruta).
- **Trace = jedini izvor istine** — projekcije nad traceom, nikad novi store.
- **Razgovor je governed** — svaki LLM okret budget-charged + traced + ContextLoom-kontekstiran.
- **Cassette-by-default determinizam** — seali bez ključa; živi model opt-in.
- **Fail-closed / no-overclaim** — lažljivi booleani nekonstruktibilni; truth labeli propagiraju MIN.
- **Additive-behind-flags, stdlib-only, deterministički** (sort po `(…, id)`, bez `hash()`/RNG).

---

## 10. Honesty / UNAVAILABLE registry
`claims_live_model` (False bez ključa) · `claims_streaming_live` (False dok provider streaming nije spojen) ·
`claims_conversation_persisted` (history = trace-projekcija) · `claims_challenger_multiagent` (False; N7=jedan async
second-opinion) · `claims_remote_websocket`/`claims_wss_tls` (False; localhost) · `claims_aureleu_dispatcher_live`
(False; F6) · `claims_watchtower_live` (False; F7) · `claims_workops_ai_editor` (False; LATER) ·
`claims_library_time_travel` (False; F8). Reply.mode=UNAVAILABLE kad ne može pošteno odgovoriti.

---

## 11. Konfiguracija za živi LLM (operater, po završetku F5)
- **Bez ključa:** razgovor na **kaseti** (deterministički dev/demo).
- **Živi LLM:** `aurel secrets set anthropic` (ili deepseek/qwen/kimi, F2) → `models.yaml` `chat`/`planning` profil →
  živi model, budget-charged, redigiran. Bez ključa i bez kasete → pošteni UNAVAILABLE.

## 12. Flagovi
`AUREL_FRONT_SERVER` · `AUREL_FRONT_CONVERSATION` · `AUREL_FRONT_SIGNAL` · `AUREL_FRONT_WORKOPS` ·
`AUREL_FRONT_BOARD` · po jedan `AUREL_FRONT_N1…N8` — svi default OFF; off put byte-identičan.

## 13. Status
- [ ] Skeleton: F5.0a → F5.0b → **F5.C** → F5.3 → F5.2 → F5.7
- [ ] Projekcije: F5.1 / F5.4 / F5.5 · UI: F5.8 · (opc. F5.6)
- [ ] Next-gen: F5.N (N1 → N3 → N4 → …)
- [ ] Pečat: F5.9 exit seal + merge
