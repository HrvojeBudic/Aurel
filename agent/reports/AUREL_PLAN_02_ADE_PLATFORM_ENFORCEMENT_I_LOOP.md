# AUREL PLAN 02 v3 — Privatni suvereni OS + Aurel Front (6 ekrana, AurelEU, Signal)

**Status:** MASTER PLAN v3 (zamjenjuje v2). Nastavlja se na AUREL_PLAN_01 (kognitivni supstrat).
**Doktrina:** "Entity proposes, runtime disposes." Trace/Library je jedini izvor istine. Ništa ne slabi governance invarijante.
**Datum:** 2026-07-08
**Utemeljeno u:** hands-on validaciji koda + potpunoj probavi "Aurel Front" specifikacije (48 dokumenata: 6 ekrana × moduli, Core Engines, codex audit, scenariji).

**Changelog v2 → v3:**
- **Aurel Front postaje ciljno sučelje plana.** Svih 6 ekrana (HQ, Corp, HUB, Lab, WorkOPS, System) + AurelEU + Signal integrirani su u faze s gradijentom realnosti (CORE / LATER / SCI-FI po modulu).
- Front-ov `codex.txt` (interni pošteni audit) potvrđuje moje hands-on nalaze — njegove tri konkretne rupe dodane u F0 (unsafe web replay fallback, plan-driven spine pada na mock modelu, "SEALED" jezik uz nesigurne defaulte).
- Novi ekran **Lab** ulazi u shell kontrakt (surface enum danas ima samo HQ/CORP/HUB/IDE/SYSTEM/SETTINGS/AUREL_CRO); `IDE`→WorkOPS alias; `AUREL_CRO`→dom AurelEU-a.
- v2 sustavi (ContextLoom, Chronos, Heartbeat, Watchtower, Constitution, Reflex Flywheel…) mapirani su na Front module umjesto da žive paralelno.
- Misija nepromijenjena: **privatna arhitektura i infrastruktura koja vodi operatorove poslove** — ne proizvod za tržište, ne open-source za naplatu.

---

## 1. Misija (nepromijenjena) i što Front dodaje

Aurel je privatni suvereni OS: jedan operator (principal), više poslova, flota agenata pod ustavom. Sustav se ukamaćuje: memorija, dokazi, vještine, track record.

**Aurel Front je "tijelo" tog OS-a** — šest ekrana kroz koje operator vidi i vodi sve, plus dvije spojnice:
- **AurelEU** — suvereni "mozak": role-fluid entitet koji mijenja persone, dispečira pod-agente s ubrizganim pravilima, i kroz kojeg prolazi svaka komanda iz sučelja.
- **Signal** — univerzalni plutajući chat (resizable/minimizable, prisutan na svih 6 ekrana): **nula vlastitog stanja** (Library/trace su izvor istine), **ruta isključivo kroz AurelEU**, svaka poruka nosi identitet, ulogu, mandat i context_refs (Library hasheve).

Ključna arhitektonska odluka koju Front donosi i koju usvajamo kao zakon: **"jedna vrata"** — sučelje nikad ne zove podsustave direktno; sve komande su prijedlozi (proposals) kroz AurelEU → `runtime.submit`. Postojeći `aurel_shell` read-only zakoni ostaju; jedini command API su prijedlozi.

---

## 2. Utemeljeno stanje (kod + codex audit se slažu)

**Uvijek enforced:** submit pipeline (policy→approval→budget→sandbox→verify→rollback→hash-chained trace), budget kapovi, bubblewrap probe, cassette determinizam (dokazan bit-identičan replay), Track A governed memorija (flag), dual-kernel preflight (flag).

**OFF/shadow po defaultu:** identity invarijante, sandbox backend gate, policy cards enforcement, drift gates; G0–G5 skala je deklarativna.

**Token accounting:** `charge_llm(usage=...)` + `substantiated`/`estimate_only` postoji; Anthropic/OpenAI ekstrahiraju usage; **DeepSeek i Ollama ne** (rupa → F0).

**Planner:** heuristika (regex + demo uzorak) koja se pravi da planira → F0 poštenje.

**Front-codex dodatne rupe (potvrđene):** (a) `spine/webui` ima unsafe fallback za replay; (b) plan-driven spine pada s default mock modelom; (c) "SEALED" jezik uz `UnsafeLocalSandbox` default je overclaim dok F1 ne sleti.

**Shell:** surface kontrakti postoje (closed-world enum u `aurel_shell/surface_registry.py:57`), floating window kontrakt postoji (`floating_window.py`, contract-only, "ne izvršava ništa"), cross-surface handoff sheme postoje (`cross_surface_handoff_context.py` s `hq`/`corp` id-jevima). **Front UI ne postoji — sve je contract-only.** React 19+Vite+Tauri skeleton u `web/shell` čeka spajanje.

**Spremnost backenda po podsustavu (sažetak agenata):** runtime 95%, aurel_flow 90%, trace 85%, policy_cards 85%, approval 90%, budget/Financial 85–90%, memorija/Library 80%, cassette/simulacija 85%, model router 75%, skills 40%, fine-tuning 0%, media generacija 0%, web scraping/Intelligence 0%.

---

## 3. Deset engine-a ≈ postojeći podsustavi (mapa istine)

Front-ova "Core Engines" lista se gotovo 1:1 mapira na postojeće:

| # | Front engine | Postojeće | Status |
|---|---|---|---|
| 1 | Governance & Proposal | `runtime.submit` + policy + policy_cards + approval | **ŽIVO** (enforcement gradacija → F1) |
| 2 | Durable Spine / Library | trace + Track A durable memorija + WorldLineForest + doc_registry | **ŽIVO djelomično** — "Library" = ujedinjena projekcija (→ F5) |
| 3 | Sovereign Orchestration (AurelEU) | identity kernel + persona manifesti + delegation/ + operator_contract | **PARCIJALNO** — postoji kao skela, nije spojeno kao orkestrator (→ F6) |
| 4 | Trace & Causal | `aurel_trace/` P5 (sealed) + golden threads | **ŽIVO**; kauzalni graf UI → F5/F8 |
| 5 | Memory & Context | Track A + ContextLoom (→ F4) | **ŽIVO / u planu** |
| 6 | Intelligence & World Model | — | **ODSUTNO** (→ horizont; skalirano na "governed feeds") |
| 7 | Execution & Workflow | aurel_exec + aurel_flow + spine + repo_agent | **ŽIVO** (flow nema UI) |
| 8 | Evaluation & Verification | evaluation/ + verifier + cassette | **PARCIJALNO** (→ F9 Lab) |
| 9 | Security & Crypto | sandbox + SecretStore (→ F2) | **PARCIJALNO**; HSM/zero-trust = SCI-FI za privatno |
| 10 | Analytics & Self-Improvement | budget + σ + praxis + skills | **PARCIJALNO** (→ F7 KPI, Reflex Flywheel) |

Zaključak koji plan slijedi: **backend je zreo, sučelje ne postoji.** Zato faze F0–F4 dovršavaju kičmu, a F5–F9 grade Front na njoj.

---

## 4. Faze

### F0 — Stabilizacija i poštenje (≈1–1.5 tjedan)

| # | Zadatak |
|---|---|
| 0.1 | Planner honesty: `_patches_for_request` bez pogotka → `valid=False` + refusal; `--planner demo-heuristic` alias. |
| 0.2 | Token usage: `_usage_from` u `deepseek_provider.py` (OpenAI-kompatibilan `usage`) i `ollama_provider.py` (`prompt_eval_count`/`eval_count`). |
| 0.3 | Reverse-dependency audit (`scripts/reverse_deps.py`) → attic za module s nula uvoznika (`heretic/` odmah; `golden_threads/` OSTAJE — evaluation ovisi). |
| 0.4 | **[novo iz codexa]** `spine/webui` — ukloniti unsafe replay fallback (fail-closed poruka umjesto tihog pada na unsafe). |
| 0.5 | **[novo iz codexa]** Plan-driven spine + mock: ili deterministic mock plan fixture ili pošteni `unavailable_reason`; test za oba. |
| 0.6 | Higijena: `demo.txt`, `demo_praxis.txt`; CI artefakt `aurel governance audit --json`. |

### F1 — Enforcement gradacija (≈1–2 tjedna) — *nepromijenjeno iz v2*

`enforcement_profiles.yaml` (dev=G4 / **standard=G2 default** / hardened=G0–G1); `build_runtime(profile=...)` stvarno primjenjuje; `aurel governance audit --fail-on-drift` kao CI bloker; demo pod standardom. Ovime prestaje codex-ov prigovor "SEALED uz nesigurne defaulte".

### F2 — Suverenitet: provideri + ključevi (≈1 tjedan) — *nepromijenjeno iz v2*

Živi profili (planning=Claude→v4-pro failover; coding=v4-pro; review/challenger=v4-flash; summarization=v4-flash→ollama); SecretStore (env→os-keyring→tauri-keychain→file-0600, bez lažne kriptografije); centralna redakcija (trace/cassette/logovi) + sentinel seal; Model Swap Drill.

### F3 — Adapter: vanjski izvođači (≈1–2 tjedna) — *nepromijenjeno iz v2*

`aurel gate check` (Claude Code hookovi) → `mcp_gateway/` (Aurel kao MCP server, governed alati, lease iz `spine/tool_exec.py`). Vanjski agenti = AgentCard + budget + track record. **U Front rječniku: ovo je backend WorkOPS.Code ekrana** — "vanjski senior izvođač" radi u istom governed kanalu koji će UI prikazivati.

### F4 — Kognicija: interaktivni loop + ContextLoom (≈2–3 tjedna) — *nepromijenjeno iz v2, uz Front vezu*

ReAct loop (`entity_loop.py`) kroz `runtime.submit`; router po namjeni; cassette by default. **ContextLoom** = governed sastavljanje konteksta (provenance + taint + budget-aware kompresija + hash u trace). Front veza: Signalovi `context_refs` (Library hashevi uz svaku poruku) su točno ContextLoom reference — ista stvar, jedan mehanizam.

### F5 — Aurel Front v1: Signal + WorkOPS + HQ jezgra (≈6–9 tjedana)

Prva živa verzija sučelja. Stack: postojeći `web/shell` (React 19 + Vite + Tauri), Python backend izlaže read-modele (postojeći `aurel_shell` projekcijski sloj) + **jedan** command API: prijedlozi (proposals) — approve/deny, submit intent, secrets. WebSocket za Signal stream.

**5.1 Signal (spojnica svega):**
- Plutajući, resizable, minimizable overlay (postojeći `floating_window.py` kontrakt se proširuje s `SIGNAL_CHAT` kind — i dalje "ne izvršava ništa": poruke su prijedlozi).
- Nula vlastitog stanja: povijest/kontekst = Library projekcija; svaka poruka nosi `operator_identity`, `current_role`, `mandate` (vidi F6), `room_id`, `context_refs`.
- Ruta isključivo kroz AurelEU dispatcher (F6.3) → `runtime.submit`. UI nikad ne zove podsustave direktno.
- v1 sobe: operator↔AurelEU (glavna), po-poslu sobe (F7), agent-to-agent read-only digest. Real-time multi-party Board = LATER.

**5.2 WorkOPS (dnevna radna površina; `IDE` surface alias):**
- **Chat**: perzistentna povijest (Library), task tracking, tool invocation s inline approval widgetima. CORE — backend postoji, UI je posao.
- **Code**: terminal + read-only file browser + governed tool pozivi; Claude Code sesije kroz F3 adapter vidljive ovdje. AI-editor/kolaboracija = LATER.

**5.3 HQ jezgra:**
- **Command**: živi status runova + **approval inbox** (killer modul; `approval.py` postoji) + budget burn + alerti (Watchtower feed, F7.3). Prediktivno = LATER.
- **Library v1**: ujedinjeni explorer nad trace+memorija+artefakti (asset lista, provenance lanac, verzije, memory explorer po tierovima). Time-travel pregled = F8. **Odluka: "Library" je ime ujedinjene projekcije** — ne novi store; trace ostaje izvor istine (postojeći A7 memory projection + doc_registry + trace export se spajaju u jedan read-model).
- **Board v1**: async decision journal (odluke kao objekti s "Convert to Proposal" gumbom; hrani tjedni review). Real-time debata/AI moderacija = LATER.

**Seal F5:** operator iz Signala zada intent → AurelEU predloži plan → approval u HQ.Command → izvršenje vidljivo u WorkOPS → artefakt i odluka u Library — sve replayabilno, nula direktnih poziva iz UI-ja.

### F6 — AurelEU + Constitution + DN mehanizmi (≈2–3 tjedna)

AurelEU = Front ime za ono što v2 zove Constitution+persona+dispatcher, sada spojeno:

1. **Constitution delegacije** (v2 dizajn nepromijenjen): strojno čitljivi delegacijski prozori u `operator_contract.yaml`; svaka autonomna akcija citira delegaciju; prekršaj → G0 + notifikacija.
2. **Mandati (Front: "legislation as runtime object", pripitomljeno):** mandat = verzionirani snop policy cards + persona + memory-zone pravila koji **putuje s dispečiranim agentom**. Za privatnu upotrebu mandati su per-posao i per-klijent (npr. "mandat: klijent X, samo repo Y, budget Z, EU-data pravila") — ne multi-suverene jurisdikcije (SCI-FI, parkirana). Implementacija: `policy_cards/` bundle + AgentCard vezanje; `mandate_id` u svakom trace zapisu.
3. **AurelEU dispatcher:** role-fluid entitet (persona switch = eksplicitna, trace-ana tranzicija; `identity_prompt_compiler` puni system promptove) koji prima Signal poruke, pretvara ih u prijedloge, dispečira pod-agente s mandatima. Živi na `AUREL_CRO` surfaceu.
4. **DN mehanizmi** (v2 tablica vrijedi): challenger pass (v4-flash), anti-stagnation tripwire, graduated autonomy (σ track record), ponderirani merge verdikt (verifier veto apsolutan), `aurel panic`. Dvo-personalno planiranje = generator opcija za poslovne odluke, prikazan u Boardu.

### F7 — Corp ekran: Business Plane (≈4–5 tjedana)

Front Corp = v2 "firma-u-kernelu", sada s konkretnim modulima i gradijentom:

**CORE (v1):** Agency.Portfolio Map (stablo poslova→agenti→workflowi, status overlay); Agency wizard (predlošci okruženja s mandatima, "what-if" impact report prije kreiranja); Operations.Task Runtime (živi feed); Operations.Evidence Vault (trace pretraga + export receipta — Output Passport dovršen ovdje); Financial.Cost Attribution + Budget Governance (`budget.py` je 85–90% spreman, treba UI); Risk Register v1 (ručni unos + heatmap, auto-detekcija preko drift_gates LATER).
**LATER:** KPI builder, forecasting, ROI analiza, billing konzola (za privatnu upotrebu dovoljan je cost-per-klijent izvještaj), Compliance gap analiza.
**SCI-FI (parkirano):** Business Simulator (discrete-event engine), Studio Value&Risk simulacije, R&D Knowledge Transfer NLP.

**Watchtower** (v2): read-only nadzornik → puni HQ.Command alerte i eskalira operatoru. **Reflex Flywheel**: KPI "reflex hit rate" i "trošak po zadatku kroz vrijeme" na Corp dashboardu. **Klijent nula** (vlastiti repo) vozi se end-to-end prije bilo kojeg pravog klijenta.

### F8 — Time Plane: Chronos + System ekran (≈2–3 tjedna)

- **Chronos** (v2): `aurel chronos replay/fork/diff` — u Frontu se pojavljuje kao **Lab.Simulation "time-travel debugging"** i **System.Forensics & Replay**. Ista jezgra, dvije projekcije.
- **Proba za nepovratno:** ništa nepovratno (mail, plaćanje, deploy, objava) bez forka; simulacijski verdikt = evidence za HITL, nikad ovlast.
- **System ekran v1 (CORE):** Model & Routing viewer (+ promotion gates vezani na Lab evaluacije), Policy card browser, Audit log pretraga, Usage/kvote dashboardi, Data Archive status (backup/retention). Policy editor, threat detection, HSM = LATER/SCI-FI.
- **Succession drill** (v2): kvartalno; restore na čist stroj → verify → replay uzorka. Ustav + kanon + trace = firma.

### F9 — Lab ekran (≈3–4 tjedna, nakon F5; dijelovi ranije jer su jeftini)

Novi surface u closed-world enumu (`AurelSurfaceKind.LAB`).

**CORE:** Evaluation Harness UI (postojeći `evaluation/` + `flow_harness_evaluation.py`; pokretanje suiteova, rezultati, usporedbe — ovdje žive i Model Swap Drill izvještaji iz F2); Simulation Sandbox (cassette scenariji, batch izvršavanje, Chronos fork/diff UI).
**LATER:** Dataset Manager (katalog + verzioniranje kaseta/trace korpusa — prirodni prvi "dataset" su vlastite kasete); LoRA Lab (samo preko managed API-ja ako se ukaže potreba; lokalni trening tek s hardverom).
**SCI-FI (parkirano):** Fine-Tune Console (GPU infra), sintetički podaci, adversarialna generacija scenarija.

### Horizont (svjesno parkirano, s pripitomljenim verzijama)

| Front ideja | Pripitomljena privatna verzija | Kada |
|---|---|---|
| HQ.Intelligence (scraping/monitoring engine) | **Governed feeds**: RSS/API pull kroz `network_fetch` s provenance+taint (ContextLoom); sinteza kroz postojeći loop | poslije F7 |
| Media Generator | **Document Forge**: izvještaji/ponude/računi iz predložaka + Library podataka (receipts već u F7) | poslije F7 |
| Board real-time multi-party + AI moderacija | async decision journal (F5) + challenger digest | po potrebi |
| Multi-jurisdikcijski suvereni (AurelGer/AurelUS), zero-knowledge federacija | mandati po poslu/klijentu (F6) | SCI-FI |
| Multi-year emergence, ustavni amandmani samo-evolucijom | tjedni review + promotion ladder (postojeće) | SCI-FI |
| Mobile dispatch s punim stanjem | Signal web pristup s approval inboxom (read+approve) | poslije F5 |

---

## 5. Sustavi ↔ Front moduli (jedna mapa, bez dupliranja)

| v2/v3 sustav | Front dom |
|---|---|
| ContextLoom | Signal `context_refs` + Library |
| Chronos | Lab.Simulation + System.Forensics |
| Heartbeat | HUB.Automation Composer (backend mu je raspored; UI LATER u HUB-u) |
| Watchtower | HQ.Command alerti |
| Constitution + mandati | AurelEU (AUREL_CRO) + Corp.Agency |
| Reflex Flywheel | Corp KPI + HUB.SkillForge (LATER) |
| Model Swap Drill | Lab.Evaluation |
| Challenger / dvo-personalno | dual-kernel → HQ.Board digest |
| Output Passport receipts | Corp.Evidence Vault |
| SecretStore | System (Tauri keychain unos) |
| Tjedni review | HQ.Board decision journal |

HUB ekran (FlowStudio vizualni canvas, Registry Browser, SkillForge UX) je **CORE-ali-poslije-F7**: `aurel_flow`/`doc_registry`/`skills.py` backend postoji (40–90%), no operatoru prije trebaju WorkOPS/HQ/Corp. Redoslijed ekrana: **WorkOPS+HQ (F5) → Corp (F7) → System (F8) → Lab (F9) → HUB (F10)**.

---

## 6. Rust (nepromijenjeno iz v2, jedna dopuna)

Tauri (F5) = prvi Rust (keychain, tray, notifikacije). Kasnije po okidačima: sandbox supervisor, trace verify/archive binary. **Dopuna:** Signal WebSocket transport može kasnije u Tauri-Rust sloj ako Python async postane usko grlo — mjeriti, ne pretpostavljati. Nikad: planner/loop, LLM orkestracija.

---

## 7. Vremenska crta i kriteriji uspjeha

| Tjedni | Faza | Izlaz |
|---|---|---|
| 1–2 | F0 | poštenje: planner, usage, webui fallback, spine+mock |
| 2–4 | F1 | `standard` enforced default, CI drift bloker |
| 4–5 | F2 | živi provideri, SecretStore, redakcija, drill |
| 5–7 | F3 | Claude Code kroz gate/MCP |
| 7–10 | F4 | interaktivni loop + ContextLoom |
| 10–18 | F5 | **Front v1: Signal + WorkOPS + HQ.Command/Library/Board** |
| 16–19 | F6 | AurelEU dispatcher + mandati + DN mehanizmi |
| 19–24 | F7 | Corp v1 + klijent nula + receipts + Watchtower |
| 24–27 | F8 | Chronos + System v1 + succession drill |
| 27–31 | F9 | Lab v1 (evaluation + simulation UI) |
| 31+ | F10 | HUB v1 (FlowStudio, Registry, Automation UI) |

**Definicija uspjeha (≈7 mjeseci) = Front-ov "Powerful Example" scenarij, pripitomljen:** operator u Signalu zada poslovni zadatak → AurelEU (pod mandatom) dispečira agente → izvršenje u WorkOPS-u uz Lab simulaciju rizičnog koraka → approval u HQ.Command → isporuka u Corp s receiptom → sve replayabilno u System.Forensics — na stvarnom poslu (klijent nula), pod `standard` profilom, bez ijednog direktnog poziva iz UI-ja, bez ključa u artefaktima.

**Rizici:** F5 je najveći zalogaj (6–9 tjedana UI posla — držati se točno nabrojenih modula; sve ostalo je LATER); Signal disciplina ("jedna vrata") se lako erodira pod pritiskom rokova — čuva je seal test da UI nema drugi put do backenda; SCI-FI moduli (Intelligence, Media, Fine-Tune, Business Simulator) su najveći magnet za skretanje — parkirani su s pripitomljenim verzijama i ne ulaze prije F10.
