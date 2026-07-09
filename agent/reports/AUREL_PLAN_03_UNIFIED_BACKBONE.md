# AUREL PLAN 03 — Jedinstvena kičma (sinteza P-serije + Kognicije + F-serije)

_Verzija: v1 (2026-07-09). Status: **STRATEŠKI PLAN / PRIJEDLOG** — ne poništava `agent/ROADMAP.md` v5.5 kao ACTIVE_CANON za numeriranje P-taskova; slaže postojeće smjerove u jednu kičmu i redoslijed. Autoritet ostaje: ROADMAP=P-numeracija, ovaj dokument=redoslijed i vezanje slojeva._

Sinteza: [[aurel-private-os-direction]] + [[dual-kernel-layer]] + `AUREL_PLAN_02_ADE_PLATFORM_ENFORCEMENT_I_LOOP.md` + `agent/ROADMAP.md` (v5.5).

---

## 1. Teza sinteze

Do sada su postojala tri plana koja su izgledala kao tri smjera. Nisu tri smjera — to su **tri sloja jednog sustava**:

| Sloj | Što je | Odakle dolazi | Uloga |
|------|--------|---------------|-------|
| **Substrat (governance)** | Kostur/gramatika: što je dopušteno, zapečaćeno, ugovorno istinito | **P-serija** (Aurel Roadmap v5.5, P0→P9) | Nikad LIVE bez PASS-a nad stvarnim dokazom |
| **Um (kognicija)** | Memorija, rasuđivanje, simulacija, vanjski doseg | **Tracks A/B/C/D + dual-kernel** (Upgrade Master Plan) | Zadeblja mišljenje bez slabljenja governancea |
| **Tijelo + lice (proizvod)** | Ono što operator stvarno koristi; vremenska crta isporuke | **F-serija** (Plan 02 v3, F0→F10, Aurel Front) | Privatni suvereni OS: 6 ekrana + AurelEU + Signal |

Ključni uvid koji F-plan već tvrdi i koji ova sinteza formalizira: **backend je zreo, sučelje ne postoji.** Zato **F-serija postaje kičma (driving timeline)**, a svaka F-faza na sebe vješa (a) governance substrat iz P-serije koji joj treba i (b) kognitivni rep koji aktivira. Jedna kičma, tri sloja po fazi.

## 2. Invarijante koje se ne pregovaraju ni u jednoj fazi

1. **No-collapse / poštenje** — ništa ne stigne u LIVE stanje bez PASS verdikta merge gatea nad *stvarnim* (ne tvrđenim) dokazom. `TRACE_VERIFIED` je samo odluka resolvera, nikad labela.
2. **Contract-before-live** — svaka sposobnost prvo živi kao `SEALED_CONTRACT_ONLY`, pa tek onda dobije izvršni put. P-pečati su dokaz zatvaranja ugovora, ne produkcijska spremnost.
3. **Jedna vrata** — UI (Signal/ekrani) → **AurelEU** → `runtime.submit`. Nula direktnih poziva iz sučelja. Signal ima nula vlastitog stanja.
4. **Enforcement default za samotnog operatora** — profil `standard` = G2. Operator je sam; enforcement defaulti su kritični, ne opcionalni.
5. **Ukamaćivanje, ne demo-efekt** — prioritet je dugoročno (memorija/kanon, refleksi, trace arhiv, track record), ne vizualni dojam.

## 3. Istinito trenutno stanje (2026-07-09, korigirano za doc-lag)

**Mergeano u `master`:**
- Dual-kernel (Custos/Praxis, Σ, merge gate, ledger) — `f0c02ad`.
- Track B (reasoning scheduler) i **Track A** (bi-temporalna memorija A0→A8 + `mem_*` dispatch spojen na `runtime.submit`).
- **F2** (provideri Qwen/Kimi + SecretStore + `aurel secrets` + redaction + `aurel drill model-swap`) — merge `800d88a` **danas**. (Napomena: `agent/ACTIVE_TASK.md` još kaže "F2 nije na masteru" — zaostaje za gitom; treba sync.)
- P-serija contract-only kroz **P5 SEALED** (AurelTrace Spine).

**Zapečaćeno contract-only (ne LIVE):** P2 (većina), P3, P4, P5.

**Otvoreno / nezapočeto:**
- Governance: **P6** (AurelData/Object Plane) sljedeći; P8 (Atlas router), P9 (Custos runtime) iza. P2 rep (P2.11-D→P2.20) odgođen. P1.ENF D1/E/REVIEW-A nezapočeti.
- Kognicija: Track C rep (C6→C9), Track D (MCP/A2A).
- Proizvod: F0/F1 djelomično; F3–F10 nezapočeti.

## 4. Jedinstvena kičma — faze (S0–S6 + Horizont)

Svaka faza nosi tri sloja: **[Lice]** što operator dobije · **[Substrat]** koji P-task to podupire · **[Um]** koji Track se aktivira · **[Pečat]** kriterij završetka.

### S0 — Konsolidacija istine (~dani, ODMAH)
- **[Lice]** Ništa novo — čišćenje. **[Substrat]** Sync `ACTIVE_TASK.md`/`STATE.md`/`CANON_INDEX.md` da odražavaju F2-merge + Track A merge; potvrdi da je dual-kernel grana u masteru. **[Um]** M2 seal: coverage + bandit na masteru. **[Pečat]** Jedno kanonsko stanje bez drift-a; puni pytest zelen na HEAD-u.
- _Zašto prvo:_ tri plana su ostavila dokumentacijski dug; sinteza je bezvrijedna dok "istinito stanje" nije jedno.

### S1 — Suvereni temelj (F0 + F1 + F2✓)
- **[Lice]** Operator upisuje ključ za bilo koji provider; enforcement gradacija vidljiva. **[Substrat]** P1.ENF lanac (enforcement modovi, fail-closed submit), P9 Custos *sjeme*. **[Um]** — (bez novog). **[Pečat]** Provider zamjenjiv jednim retkom u `models.live.yaml`; profil `standard`=G2 aktivan po defaultu; F0 honesty + F1 gradacija dovršeni. **Status: F2 done; dovrši F0/F1.**

### S2 — Kognitivni loop na jedna vrata (F4 + Track C rep + Track D bridge)
- **[Lice]** Interaktivni loop + ContextLoom: intent → prijedlog → simulacija → izvršenje. **[Substrat]** `runtime.submit` enforcement (P1.ENF) + dual-kernel merge gate na izvršnom putu. **[Um]** **Track C rep C6** (shadow-wire sim-gate u `runtime.submit`) → **C7** (enforcing) → **C8** (counterfactual) → **C9** (projection); **Track D0** (taint) → **D1** (MCP bridge, governed vanjski doseg). **[Pečat]** "simulate-then-permit": intent → fork/simulacija → gate → execute, sve replayabilno; D4 (A2A) ostaje zadnji/parkiran.
- _Sinergija:_ Track C ("simuliraj pa dopusti") ≈ dual-kernel spekulativni fork — **ne graditi ispočetka, ujediniti.** Ovo je i popravak poznate budget/memory rupe materialize putanje.

### S3 — Aurel Front v1 (F5: Signal + WorkOPS + HQ jezgra)
- **[Lice]** Prvi pravi UI: Signal (plutajući chat), WorkOPS (izvršenje vidljivo), HQ.Command (approval). Prvi Rust (Tauri: keychain, tray, notifikacije). **[Substrat]** P2.6 Surface Projection + P2.7 Shell binding — ali sada trebaju **stvarni** minimalni binding (P2 rep P2.11-D→P2.20 *ili* F5-minimalni izvršni binding, operator bira opseg). **[Um]** Track A durable memorija = "Library" ujedinjena projekcija. **[Pečat]** _F5 seal:_ operator iz Signala zada intent → AurelEU predloži plan → approval u HQ.Command → izvršenje u WorkOPS → artefakt+odluka u Library — sve replayabilno, nula direktnih poziva iz UI-ja.

### S4 — Data plane + Business plane (P6 + F7 Corp)
- **[Lice]** Corp ekran: klijenti, dokumenti, računi, Evidence Vault, KPI. **[Substrat]** **P6 AurelData/Object Plane** (ObjectRef/DataRef/ArtifactRef, lifecycle, indeksiranje) — točno ono što F7 treba kao izvor istine poslovnog stanja. **[Um]** Track A durable memorija → poslovni track-record; Reflex Flywheel → Corp KPI. **[Pečat]** Corp ekran prikazuje stvarno poslovno stanje iz object planea, ne fixture; Output Passport receipts u Evidence Vaultu.

### S5 — Suvereni orkestrator + živi governance (F6 + P9 Custos runtime)
- **[Lice]** AurelEU (AUREL_CRO) kao role-fluid dispatcher + Constitution + DN mehanizmi; HQ.Board decision journal. **[Substrat]** **P9 Custos policy runtime** — stvarno izvršno provođenje politike na `runtime.submit`, ne više contract-only. **[Um]** identity kernel + persona manifesti + delegation spojeni kao *orkestrator* (danas skela). **[Pečat]** Policy odluke provođene na runtime-u nad stvarnim dokazom; "jedna vrata" zatvorena kroz AurelEU.

### S6 — Time + System + Lab + Router (F8 + F9 + P8 Atlas)
- **[Lice]** System ekran (Chronos forenzika, SecretStore unos, tray), Lab ekran (Evaluation, Model Swap Drill, Simulation). **[Substrat]** **P8 Atlas** model router (multi-provider routing kao governance). **[Um]** Track B reasoning scheduler pogoni Lab eksperimente; Evaluation/verifier → Lab. **[Pečat]** Kauzalni graf UI; deterministički routing s honest failoverom; Lab reproducira drill-ove.

### Horizont (svjesno parkirano, "pripitomljene" verzije)
HUB ekran (FlowStudio canvas, Registry, SkillForge) = CORE-ali-poslije-F7 (F10). SCI-FI: Intelligence & World Model (engine #6), Media Generator, Fine-Tune, Business Simulator, multi-jurisdikcije — svi kao "governed feeds", ne autonomni. **Rust po okidačima:** sandbox supervisor, trace verify/archive binary, Signal WebSocket ako Python async postane usko grlo (mjeriti, ne pretpostavljati). Nikad u Rust: planner/loop, LLM orkestracija.

## 5. Mapa: engine ↔ substrat ↔ um ↔ faza (jedna tablica istine)

| Front engine | P-substrat | Kognicija | Isporuka |
|---|---|---|---|
| 1 Governance & Proposal | P1.ENF, P9 Custos | dual-kernel gate | S1, S5 |
| 2 Durable Spine / Library | P5 (sealed), P6 | Track A durable | S3, S4 |
| 3 Sovereign Orchestration (AurelEU) | identity kernel, P9 | delegation/persona | S5 |
| 4 Trace & Causal | P5 (sealed) | golden threads | S3/S6 (UI) |
| 5 Memory & Context | Track A | ContextLoom | S2, S3 |
| 6 Intelligence & World Model | — | governed feeds | Horizont |
| 7 Execution & Workflow | aurel_exec/flow (P4), spine | Track C sim-gate | S2 |
| 8 Evaluation & Verification | evaluation/verifier | Track B PRM | S6 (Lab) |
| 9 Security & Crypto | sandbox, SecretStore (F2) | — | S1 |
| 10 Analytics & Self-Improvement | budget, σ, praxis | Track B/reflex | S4 (KPI), S6 |

## 6. Redoslijed i zašto baš ovaj

```
S0 istina → S1 suvereni temelj → S2 kognitivni loop → S3 Front v1 →
S4 Data+Corp → S5 AurelEU+Custos → S6 Time+System+Lab+Router → Horizont
```

- **Kičma prvo, lice poslije:** S0–S2 dovršavaju izvršnu kičmu (loop + governance + kognicija na `runtime.submit`); S3+ grade UI na gotovoj kičmi. Poklapa se s F-planovim "F0–F4 kičma, F5–F9 Front".
- **Governance prati potrebu, ne apstrakciju:** P6 stiže kad ga treba F7 (Corp), P9 kad ga treba F6 (AurelEU), P8 kad ga treba Lab/router — a ne "svih P-faza redom u prazno".
- **Kognitivni repovi se aktiviraju gdje ih loop koristi:** Track C u S2 (simulate-then-permit), Track A u S3/S4 (Library/track-record), Track B u S6 (Lab), Track D postupno (D1 rano, D4 zadnji).

## 7. Neposredni sljedeći potezi (izvršno)

1. **S0-a:** sync `ACTIVE_TASK.md` + `STATE.md` + `CANON_INDEX.md` na F2-merged / Track-A-merged stvarnost; ukloni "F2 nije na masteru" drift.
2. **S0-b:** M2 seal — coverage + bandit + puni pytest na `master` HEAD; zabilježi baseline.
3. **S1:** dovrši F0 (honesty stabilizacija) + F1 (enforcement gradacija, profil `standard`=G2 default) na masteru.
4. **S2 start:** Track C **C6** — shadow-wire dual-kernel sim-gate u `runtime.submit` (flag-gated, byte-identical OFF), kao temelj F4 loopa.

---

_Kraj plana. Ovaj dokument je redoslijedni/vezni autoritet; P-numeracija ostaje u `agent/ROADMAP.md`. Ažurirati verziju pri svakom pomaku faze S0→S6._
