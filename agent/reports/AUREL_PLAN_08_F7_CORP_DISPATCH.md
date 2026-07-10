# AUREL PLAN 08 — F7 Corp ekran: Business Plane (dispatch plan)

**Datum:** 2026-07-11
**Status:** LIVE dispatch plan — F7 razložen na samostalne slajseve (F7.0→F7.10)
**Izvor:** `AUREL_PLAN_02_ADE_PLATFORM_ENFORCEMENT_I_LOOP.md` §F7 (linije 141–149); F6 exit seal forward seamovi (`AUREL_F6_10_F6_EXIT_SEAL.md`)
**Ulazno stanje:** F6 zapečaćen i mergean u `master` (`f0789e4`). Sljedeća grana: `feat/f7-corp`.
**Ključni nalaz istraživanja:** F7 je ~60 % **projekcija/kompozicija postojeće mašinerije** (budget ledger,
trace + `mandate_id` u svim zapisima od F6.1, P5 receipts, mandate registry, CORP surface već u closed-world
enumu) + ~40 % novo (Client/Job domena, Watchtower pravila, Evidence Vault pretraga/export, Risk Register,
wizard). Nije greenfield — Business Plane je uglavnom **read-model sloj nad onim što F6 već trace-a**.

---

## 0. Kako koristiti (svaka sesija)

- Svaki slajs (F7.x) je **samostalna dispatch jedinica**: novi/izmijenjeni fajlovi, flag, seal test,
  no-collapse invarijante i paste-ready dispatch prompt.
- Radi **jedan slajs odjednom**, redoslijedom §4. Nakon svakog: `ruff` + `mypy` na dodirnutim modulima,
  seal test slajsa, fokusirani regres; **puni suite** (`AGENTIC_SKIP_RECURSIVE_SMOKE=1 .venv/bin/python -m
  pytest -q -p no:cacheprovider`, background) prije merge-a grane.
- **Zakon svakog slajsa** (§5): additive-behind-flags (default OFF ⇒ **byte-identičan** F6 svijet),
  **Watchtower = vidljivost, nikad ovlast** (read-only nadzornik), Corp domena **ne dodjeljuje ovlast**
  (ovlast ostaje mandat, F6), trace = jedini izvor istine, jedna vrata (Corp UI predlaže kroz
  `POST /proposals`, nikad ne izvršava), no-overclaim (alert bez izvora nekonstruktibilan, KPI bez
  podataka = UNAVAILABLE, `verified` samo iz stvarne P5 verifikacije).
- **North star** cijele faze (§7): operator kroz Agency wizard kreira okruženje **klijenta nula** (vlastiti
  repo) s mandatom → what-if impact report → proposal → approval → posao živi u Portfolio mapi → izvršenje
  pod mandatom → trošak pripisan klijentu → out-of-scope pokušaj ⇒ DENY ⇒ **Watchtower alert u HQ.Command**
  → receipt bundle iz Evidence Vaulta (Output Passport) → KPI iz stvarnih podataka — sve replayabilno.
- **Paralelni meta-task:** Canon V1 / governance reorg (brainstorm 2026-07-10) je zaseban kolosijek — F7 o
  njemu **ne ovisi**; reporti idu po postojećoj konvenciji (`agent/reports/AUREL_F7_*.md`), reorg ih kasnije
  bucketira.

---

## 1. Utemeljeno stanje (ground truth, s file:line)

**Postoji (zrelo, F7 spaja):**
- **CORP surface već postoji u closed-world enumu:** `aurel_shell/surface_registry.py:57–66`
  (`AurelSurfaceKind.CORP`), truth owner `BUSINESS_ENVIRONMENT_STATE` + relacije
  `business_environment_projection`/`corp_read_model` u `aurel_shell/boundaries.py:56–74`. **Surface je
  deklariran, read-model ne postoji — F7 ga puni.**
- **Jedna vrata + read-model registry:** `front_server/routes.py:28–33` (točno jedna mutation ruta
  `POST /proposals`), `front_server/read_models.py:96–107` (`_REGISTRY` s 10 buildera: signal/workops/
  approvals/library/hq/board/aureleu/dn — **nema corp modela**), `front_server/proposal_dispatcher.py`
  (converse / act / decide semantike), `frontClient.ts:35–110` (live/fixture mode, `propose()` jedina mutacija).
- **`mandate_id` je u SVIM trace zapisima (F6.1):** `core_types.py` — `BudgetDecisionRecord` (:418),
  `ApprovalReceiptRecord` (:624), `MemoryGovernanceRecord` (:488), `PraxisEventRecord` (:696), svi
  hash-chained. **Ovo je kralježnica cost attributiona i Evidence Vaulta — već postoji.**
- **`MandateScope` već nosi poslovnu dimenziju:** `mandate/mandate.py:36–42` — `client_id: str` i
  `budget_cents: float` polja postoje; `MandateRegistry.resolve/ids` (`mandate/registry.py:23–56`);
  enforcement gate `mandate/enforcement.py:55–88` + hook u `runtime.py:315–325` (mandate block ⇒ standardna
  BLOCKED tranzicija s reason — **nema dediciranog `MandateCheckRecord`**; Watchtower čita BLOCKED+reason).
- **Budget ledger 85–90 % spreman:** `budget.py` — `per_run`/`per_command`/`per_step`/`per_agent` bucketi,
  `estimated_cost_cents`, substantiated vs. estimate-only charges, `snapshot()`. **Fali `per_mandate`
  bucket i client pivot — F7.1.**
- **Receipts + verifikacija (P5):** `trace.py:728–757` (receipt.json: run_id, event_count,
  final_chain_hash, checkpoints, anchor), verify fail-closed `trace.py:520–545`; `aurel_trace` P5-TRACE-B
  `TraceVerificationReceipt` (`verified` **samo** izveden iz PASS verifikacije, nikad upgrade);
  `cli_modules/trace_commands.py` (read-only query/verify), `cli_modules/output_passport.py` (CLI binding).
  **Fali pretraga/filter po mandate_id/klijentu i batch export — F7.4.**
- **Watchtower seam, deklariran i čeka:** `front_server/hq_command.py:74–77` (`watchtower()` vraća
  `UNAVAILABLE, owner F7, alerts: []`), `CLAIMS_WATCHTOWER_LIVE = False` hard-wired;
  `front_seal.py:73–74` + `f6_seal.py:83–85` registriraju seam s vlasnikom F7.
- **Approval workbench seam:** `f6_seal.py:80–82` (`full_approval_workbench`, F7). F5.2 inbox već daje:
  two-phase submit (`approval_inbox.py:43–94`), immutable audit iz tracea (`:96–105`), pending in-process.
  **Fali kontekst (mandat/budget/rizik uz pending stavku) i povijest/filtriranje — F7.8.**
- **Reflex mašinerija za KPI:** `skills.py` (`CapabilityState.REFLEX`, `find_reflex` + environment
  signature drift demotion), `praxis.py:654–839` (`PromotionEvaluator.check_reflex_eligibility`,
  `reflex_checks` audit), `entity.py:93–103` (REFLEX hit = preskočen LLM poziv). **Fali agregacija u KPI.**
- **Risk temelj:** `core_types.py:58–63` (`RiskLevel` 5 razina), reflex drift-gate uzorak. **Fali Risk
  Register objekt + heatmap — F7.7.**
- **Seal + CLI uzorak:** `f6_seal.py:186–212` (derived seal: modul importabilan AND report prisutan;
  overclaim guardovi kao propertyji), `cli_modules/f5_commands.py:45–63` (`cmd_aureleu_seal` uzorak),
  registracija u `cli.py:522–524, 989`. Flag uzorak: `AUREL_<PODSUSTAV>`, helper `flag_enabled()`.
- **Constitution violations u traceu:** praxis eventi koje `f6_projection.py:35` već parsira
  (`mandate_id|reason` u summaryju) — Watchtower ih čita kao izvor.

**NE postoji (F7 gradi):**
1. **Corp domena** — `Client`/`Job` objekti + registry (danas postoji samo `MandateScope.client_id` string).
2. **`per_mandate`/per-client cost attribution** — ledger ne pivotira po mandatu; nema cost-per-klijent.
3. **Budget governance view** — alokacija vs. potrošnja po klijentu/poslu (predictive/ETA ostaje LATER).
4. **Watchtower alert builder** — deterministička pravila nad traceom/ledgerom koja pune HQ.Command.
5. **Evidence Vault** — trace pretraga (mandate/klijent/kind/vrijeme) + receipt bundle export.
6. **Corp read model + `/read/corp/*`** — portfolio stablo, živi feed, KPI.
7. **Agency wizard** — predlošci okruženja s mandatima + what-if impact report (dry-run enforcementa).
8. **Risk Register v1** — governed ručni unos + heatmap.
9. **CorpPanel.tsx** — React surface za CORP.

**Zaključak:** trace već nosi sve poslovne činjenice (mandate_id svugdje, budget odluke, approvale,
violations); budget ledger već broji. F7 = Corp domena (klijent/posao) + projekcijski sloj koji te
činjenice pivotira po klijentu/poslu + Watchtower koji ih nadzire — sve read-only osim kreiranja
okruženja kroz jedna vrata.

---

## 2. Arhitektonska kičma: Corp je projekcija nad mandatom, ne novi izvor ovlasti

Business Plane ne uvodi novi izvršni put ni novu ovlast — **posao (Job) je poslovni omotač oko mandata**:

- **Domena (novo, malo):** `corp/` paket — `ClientRecord` + `JobRecord` (frozen, hashirani, registry po
  uzoru na `mandate/`). Job → mandati preko `mandate_ids` (referenca u postojeći `MandateRegistry`);
  klijent ↔ mandat već vezan preko `MandateScope.client_id`. **Klijent nula** = vlastiti repo, seedan
  kao default (kao `mandate/default.py`).
- **Attribution (pivot):** postojeći charge siteovi u ledgeru dobivaju opcionalni `mandate_id` (additive,
  default `""` ⇒ byte-identično); `CostAttributionView` pivotira ledger + registry → cost po
  mandatu/poslu/klijentu; trace `BudgetDecisionRecord.mandate_id` je audit cross-check.
- **Nadzor (Watchtower):** čisti derivator alerta nad traceom + ledger snapshotom; puni postojeći
  `hq_command.watchtower()` seam. Vidljivost, nikad ovlast — ne blokira, ne izvršava, samo eskalira
  operatoru.
- **Dokazi (Evidence Vault):** pretraga po `mandate_id`/klijentu nad trace zapisima + receipt bundle
  export (reuse P5 receipts) — Output Passport dovršen ovdje.
- **Kreiranje (jedina mutacija):** Agency wizard generira prijedlog (template → mandat draft + job) koji
  ide kroz `POST /proposals` → approval → governed zapis. UI nikad ne kreira direktno.

**Master flag:** `AUREL_CORP` (default OFF ⇒ nema corp read-modela, ledger bucket se ne puni, byte-identičan
F6 svijet). Pod-flag: `AUREL_WATCHTOWER` (alert builder + HQ flip). Reuse: `AUREL_FRONT_SERVER` (rute),
`AUREL_MANDATE` (scope istina), `AUREL_FRONT_BOARD`/`AUREL_AURELEU` netaknuti.

**Zakon F6 se ne krši:** mandat ostaje jedini nositelj ovlasti; Corp objekti su poslovni metapodaci i
projekcije. Nijedan Corp zapis ne može proširiti `card.authority` niti zaobići mandate gate.

---

## 3. Per-slajs dispatch specifikacije

> Legenda: **Files** = novo / izmijenjeno. **Flag** default OFF. **Seal** = pytest fajl. **NC** = no-collapse.

### F7.0 — Corp domena: Client + Job registry + klijent nula (flag `AUREL_CORP`)
- **Files:** novo `corp/__init__.py` (flag helper po uzoru na `mandate/`), `corp/domain.py` (`ClientRecord`
  frozen: `client_id`, `name`, `notes`; `JobRecord` frozen: `job_id`, `client_id`, `mandate_ids: tuple`,
  `repos: tuple`, `status`; **JobRecord nekonstruktibilan bez `client_id`**; `content_hash` = sha256
  kanonskog JSON-a), `corp/registry.py` (`CorpRegistry.from_records`, `resolve_client/resolve_job`,
  deterministički sortiran; pri buildu validira da svaki `mandate_ids` element postoji u danom
  `MandateRegistry` — fail-closed), `corp/default.py` (**KLIJENT_NULA** = vlastiti repo + default mandat).
- **NC:** registry je governed konfiguracija, ne izvršenje; job bez klijenta nekonstruktibilan
  (no-overclaim); mandat veza je **referenca**, ne kopija; isti sadržaj ⇒ isti hash; nepoznat
  `mandate_id` u jobu ⇒ fail-closed pri buildu.
- **Seal:** `test_p6f7_0_corp_domain.py` — client/job hashirani; job bez klijenta ne postoji; nepoznata
  mandate referenca ⇒ fail-closed; klijent nula resolvira; deterministički poredak.
- **Dispatch prompt:** _"Implementiraj F7.0: `corp/domain.py` (`ClientRecord`/`JobRecord` frozen+hashed,
  job nekonstruktibilan bez client_id), `corp/registry.py` (resolve, validacija mandate referenci
  fail-closed), `corp/default.py` (klijent nula = vlastiti repo). Flag `AUREL_CORP`. Seal
  `test_p6f7_0_corp_domain.py`."_

### F7.1 — Cost attribution: per-mandate bucket + client pivot (flag `AUREL_CORP`)
- **Files:** edit `budget.py` — additivni `per_mandate: dict[str, dict]` bucket; postojeći charge
  potpisi dobivaju opcionalni `mandate_id: str = ""` (default ⇒ bucket se ne puni, byte-identično);
  edit `runtime.py` — na postojećim charge pozivima proslijedi `getattr(card, "mandate_id", "")`;
  novo `corp/cost.py` (`CostAttributionView.from_ledger(ledger, corp_registry, mandate_registry)` →
  rollup {klijent → posao → mandat → {cost_cents, tool_calls, llm_calls, substantiated vs. estimate}};
  cross-check helper nad trace `BudgetDecisionRecord.mandate_id`).
- **NC:** **nula novih verdikata** — attribution je izvještaj, ne enforcement; nijedan postojeći charge
  ne mijenja ponašanje (default `""` ⇒ ledger byte-identičan, dokaži flag-off testom); bez ledgera ⇒
  `UNAVAILABLE` s razlogom (F5.5 disciplina); substantiated/estimate-only razlika se prenosi pošteno.
- **Seal:** `test_p6f7_1_cost_attribution.py` — run pod mandatom M ⇒ trošak u `per_mandate[M]` i u
  client rollupu; default mandate_id ⇒ bucket prazan + snapshot byte-identičan; bez ledgera UNAVAILABLE.
- **Dispatch prompt:** _"Implementiraj F7.1: additive `per_mandate` bucket u `budget.py` (opcionalni
  `mandate_id=''` na charge potpisima, runtime prosljeđuje card.mandate_id), `corp/cost.py`
  (`CostAttributionView` pivot klijent→posao→mandat). Default prazan ⇒ byte-identično. Seal
  `test_p6f7_1_cost_attribution.py`."_

### F7.2 — Budget governance: alokacija vs. potrošnja po klijentu/poslu (flag `AUREL_CORP`)
- **Files:** novo `corp/budget_governance.py` (`ClientBudgetView`: alokacija = `MandateScope.budget_cents`
  po aktivnim mandatima posla (ili eksplicitna alokacija na JobRecordu), spent = F7.1 `per_mandate`,
  remaining = alokacija − spent; deny-count iz trace `BudgetDecisionRecord` verdict=deny po mandatu).
- **NC:** governance view je **izvještaj** — stvarni enforcement ostaje postojeći budget gate + mandate
  gate (F6.2 već enforcea `budget_cents`); forecasting/burn-ETA **ostaje UNAVAILABLE seam** (LATER,
  `hq_command.predictive()` se NE dira); alokacija bez mandata ⇒ UNAVAILABLE s razlogom, nikad izmišljena.
- **Seal:** `test_p6f7_2_budget_governance.py` — alokacija iz mandata; spent iz F7.1; remaining točan;
  deny-count iz tracea; predictive i dalje UNAVAILABLE.
- **Dispatch prompt:** _"Implementiraj F7.2: `corp/budget_governance.py` (`ClientBudgetView` — alokacija
  iz MandateScope.budget_cents, spent iz per_mandate, deny-count iz BudgetDecisionRecorda). Izvještaj,
  ne enforcement; predictive seam netaknut. Seal `test_p6f7_2_budget_governance.py`."_

### F7.3 — Watchtower: alert derivacija + HQ.Command flip (flag `AUREL_WATCHTOWER`)
- **Files:** novo `corp/watchtower.py` (`WatchtowerAlert` frozen: `alert_id`, `severity`, `kind`,
  `message`, `source_ref` — **nekonstruktibilan bez `source_ref`** (trace entry id/hash ili ledger
  metrika); `derive_alerts(trace, ledger, registries)` deterministička pravila: (1) budget deny —
  `BudgetDecisionRecord.verdict == "deny"`; (2) budget prag — ledger used/limit ≥ 0.8 po metrici;
  (3) mandate block — BLOCKED tranzicija s mandate reason (`runtime.py:319–325` put); (4) constitution
  violation — praxis eventi (parsing uzorak `f6_projection.py:35`); (5) pending approval — stavke iz
  approval audita bez odluke; sortirano deterministički po (severity, alert_id)); edit
  `front_server/hq_command.py:74–77` — `watchtower()` vraća live alerte kad je flag ON;
  `CLAIMS_WATCHTOWER_LIVE` postaje **izveden** (True samo flag ON + builder vezan), inače postojeći
  UNAVAILABLE stub byte-identičan.
- **NC:** Watchtower je **read-only nadzornik** — nikad ne blokira, ne izvršava, ne mijenja verdikt;
  svaki alert cita izvor (fabricirani alert nekonstruktibilan); flag OFF ⇒ F5.5 stub byte-identičan;
  pravila deterministička (bez `hash()`, bez vremena osim iz zapisa); **flipa** seam `watchtower_alerts`.
- **Seal:** `test_p6f7_3_watchtower.py` — budget deny ⇒ alert s source_ref; mandate BLOCKED ⇒ alert;
  violation ⇒ alert; alert bez izvora nekonstruktibilan; flag-off ⇒ UNAVAILABLE stub identičan;
  HQ.Command surfacea alerte kad je ON.
- **Dispatch prompt:** _"Implementiraj F7.3: `corp/watchtower.py` (`WatchtowerAlert` nekonstruktibilan
  bez source_ref; `derive_alerts` pravila: budget deny/prag, mandate BLOCKED, constitution violation,
  pending approval), flip `hq_command.watchtower()` + izveden CLAIMS_WATCHTOWER_LIVE iza
  `AUREL_WATCHTOWER`. Read-only, deterministički. Seal `test_p6f7_3_watchtower.py`."_

### F7.4 — Operations.Evidence Vault: trace pretraga + receipt export (flag `AUREL_CORP`)
- **Files:** novo `corp/evidence_vault.py` (`EvidenceVaultQuery`: filter po `mandate_id`, `client_id`
  (preko mandate→client mape iz registryja), `kind`, `run_id`; deterministički sortirani rezultati s
  entry_hash referencama; `export_receipt_bundle(run_id | job_id)` → JSON bundle: receipt
  (`trace.py:728–757`) + chain head + filtrirani zapisi + `TraceVerificationReceipt` iz `aurel_trace`
  kad verifikacija PASS — **`verified` isključivo izveden iz stvarne P5 verifikacije**); CLI u
  `cli_modules/f7_commands.py`: `aurel corp vault [--mandate|--client|--run] [--json]`,
  `aurel corp export --job J [--out PATH]` (read-only nad traceom; export piše bundle fajl).
- **NC:** pretraga i export su **read-only nad traceom** (nula mutacija tracea); `verified` nikad
  upgrade s FAIL/PARTIAL (P5-TRACE-B zakon); bundle nosi chain hash pa je tamper vidljiv; prazan
  rezultat = prazan (ne UNAVAILABLE); **ovime je Output Passport dovršen** — receipt po poslu s
  integritetom.
- **Seal:** `test_p6f7_4_evidence_vault.py` — filter po mandate_id vraća točno mandatove zapise; client
  filter preko registryja; bundle sadrži receipt + chain head; verified samo uz PASS; tamper ⇒ verify
  fail-closed; trace netaknut.
- **Dispatch prompt:** _"Implementiraj F7.4: `corp/evidence_vault.py` (query po mandate/client/kind/run,
  `export_receipt_bundle` reuse trace receipt + aurel_trace TraceVerificationReceipt, verified samo iz
  PASS), CLI `aurel corp vault/export`. Read-only, Output Passport dovršen. Seal
  `test_p6f7_4_evidence_vault.py`."_

### F7.5 — Portfolio mapa + Task Runtime živi feed (`/read/corp/*`) (flag `AUREL_CORP`)
- **Files:** novo `front_server/corp_read_model.py` (`CorpReadModel`: **portfolio stablo** klijent →
  posao → mandati → runovi sa status overlayem (run status uzorak iz `hq_command.py` — zadnja tranzicija
  po runu, run→posao preko mandate_id u zapisima) + cost sažetak (F7.1) + alert count (F7.3) + budget
  governance (F7.2); **runtime feed** — kronološki živi feed tranzicija/approvala/budget odluka
  filtriran po poslu); edit `front_server/read_models.py:96–107` — registriraj `corp/portfolio` i
  `corp/runtime`.
- **NC:** čista projekcija, zero-write; run bez mandata ide u "unassigned" (pošteno, ne izmišlja se
  veza); dijelovi bez izvora ⇒ UNAVAILABLE s razlogom (bez ledgera ⇒ cost UNAVAILABLE); truth labeli
  propagiraju kao MIN.
- **Seal:** `test_p6f7_5_corp_read_model.py` — stablo klijent nula → posao → run vidljivo; status
  overlay = zadnja tranzicija; runtime feed kronološki i filtriran; unassigned pošten; zero-write;
  `/read/corp/portfolio` živ.
- **Dispatch prompt:** _"Implementiraj F7.5: `front_server/corp_read_model.py` (portfolio stablo
  klijent→posao→mandat→run + status overlay + cost + alerts; runtime feed po poslu), registracija
  `corp/portfolio` + `corp/runtime` u read_models. Zero-write, unassigned pošten. Seal
  `test_p6f7_5_corp_read_model.py`."_

### F7.6 — Agency wizard: predlošci okruženja + what-if impact report (flag `AUREL_CORP`)
- **Files:** novo `corp/wizard.py` (`EnvironmentTemplate` frozen: client draft + job draft + mandat
  draft (`MandateScope`: repos/paths/budget/zone rules) + `persona_ref`; `what_if(template,
  sample_actions) → ImpactReport` — dry-run kroz **postojeći** `evaluate_mandate_scope_check`
  (`mandate/enforcement.py:55–88`) nad probnim akcijama: što bi mandat blokirao/propustio;
  `to_proposal(template)` → proposal payload (kind `act`) za jedna vrata); wire u
  `proposal_dispatcher` samo kao **payload generator** (dispatcher se ne mijenja strukturno).
- **NC:** wizard **ništa ne kreira direktno** — kreiranje okruženja je proposal kroz `POST /proposals` →
  approval → governed zapis; what-if je čista evaluacija bez izvršenja (**evidence, ne authority** —
  simulacijski verdikt nikad ne odobrava); ImpactReport advisory; template bez scope-a nekonstruktibilan
  (nasljeđuje Mandate no-overclaim).
- **Seal:** `test_p6f7_6_agency_wizard.py` — what-if točno predviđa DENY/pass za probne akcije (isti
  rezultat kao stvarni gate); to_proposal reducira na jedna vrata; nula direktnog kreiranja; template
  bez scope-a ne postoji.
- **Dispatch prompt:** _"Implementiraj F7.6: `corp/wizard.py` (`EnvironmentTemplate`, `what_if` dry-run
  kroz evaluate_mandate_scope_check = evidence ne authority, `to_proposal` kroz jedna vrata). Nula
  direktnog kreiranja. Seal `test_p6f7_6_agency_wizard.py`."_

### F7.7 — Risk Register v1: governed unos + heatmap (flag `AUREL_CORP`)
- **Files:** novo `corp/risk_register.py` (`RiskEntry` frozen: `risk_id`, `job_id`/`client_id`,
  `description`, `likelihood` 1–5, `impact` 1–5, `tier` (reuse `RiskLevel`, `core_types.py:58–63`),
  `mitigation`, `status`, `source="operator"`; unos kroz jedna vrata — proposal `act` → governed praxis
  zapis u trace (reuse `PraxisEventRecord` s `mandate_id`, polja u summaryju po F6 konvenciji);
  `RiskHeatmapView` — likelihood×impact matrica iz trace projekcije).
- **NC:** unos je **governed trace zapis**, ne efemerni store (heatmap = projekcija, preživi replay);
  auto-detekcija (drift_gates) je **LATER** — `auto_risk_detection` overclaim guard False; heatmap
  deterministična; brisanje = status change zapis, nikad pop.
- **Seal:** `test_p6f7_7_risk_register.py` — unos kroz jedna vrata ⇒ trace zapis; heatmap iz projekcije;
  replay vraća registar; auto-detekcija guard False; status change umjesto brisanja.
- **Dispatch prompt:** _"Implementiraj F7.7: `corp/risk_register.py` (`RiskEntry` governed kroz jedna
  vrata → praxis zapis, `RiskHeatmapView` projekcija likelihood×impact, reuse RiskLevel). Auto-detekcija
  LATER (guard False). Seal `test_p6f7_7_risk_register.py`."_

### F7.8 — Approval workbench refinement (flag `AUREL_CORP`; flipa `full_approval_workbench`)
- **Files:** novo `front_server/workbench.py` (`ApprovalWorkbenchReadModel`: pending stavke (F5.2 inbox)
  obogaćene **kontekstom** — mandat sažetak (scope: paths/tools/risk/budget), klijent/posao (F7.0),
  budget stanje mandata (F7.1/F7.2), risk unosi posla (F7.7), povijest odluka po alatu (pivot
  `audit_from_trace`, `approval_inbox.py:96–105`); deterministička filtracija/sortiranje po
  risk/starosti); edit `read_models.py` — registriraj `corp/workbench`.
- **NC:** obogaćivanje je **read-only kompozicija** — odluka i dalje ide isključivo kroz postojeći
  two-phase `decide` (F5.2 se ne dira, nema novog puta odluke); pending ostaje pošteno operativno stanje
  (`pending_source` disciplina iz F5.5); kontekst bez izvora ⇒ UNAVAILABLE, ne izmišljen; **flipa**
  `full_approval_workbench` seam.
- **Seal:** `test_p6f7_8_approval_workbench.py` — pending stavka nosi mandat+klijent+budget+risk
  kontekst; povijest po alatu iz audita; odluka i dalje samo kroz decide; bez konteksta UNAVAILABLE.
- **Dispatch prompt:** _"Implementiraj F7.8: `front_server/workbench.py` (`ApprovalWorkbenchReadModel` —
  pending + mandat/klijent/budget/risk kontekst + povijest odluka; read-only kompozicija, odluka ostaje
  F5.2 decide), registracija `corp/workbench`. Flipa full_approval_workbench. Seal
  `test_p6f7_8_approval_workbench.py`."_

### F7.9 — Reflex Flywheel KPI + CORP React surface (flag `AUREL_CORP`)
- **Files:** novo `corp/kpi.py` (`ReflexFlywheelView`: **reflex hit rate** = REFLEX hitovi / ukupno
  planiranja (izvor: praxis reflex eventi + skills registry, `skills.py`/`praxis.py:654–839`); **cost
  per task kroz vrijeme** = per_run cost (F7.1) grupiran po tasku i started_at bucketima; oba
  **UNAVAILABLE kad nema podataka** — nikad 0 % koji laže); novo
  `web/shell/src/components/front/CorpPanel.tsx` (portfolio stablo, cost/budget, alerts, risk heatmap,
  KPI, vault pretraga; wire u `FrontSurface` za `CORP`), edit `frontClient.ts` (corp read builderi);
  registriraj `corp/kpi` u read_models.
- **NC:** KPI nikad fabriciran (prazno ⇒ UNAVAILABLE s razlogom); React panel zero direktnih poziva —
  sve kroz `frontClient` `/read/*` + `propose()`; server OFF ⇒ fixture mode (F5.8 disciplina);
  truth labeli u UI-ju vidljivi.
- **Seal:** `test_p6f7_9_corp_kpi_surface.py` (+vitest) — hit rate iz stvarnih praxis eventa; cost per
  task iz ledgera; prazno UNAVAILABLE; `/read/corp/kpi` živ; UI čin ⇒ proposal; nula direktnih poziva.
- **Dispatch prompt:** _"Implementiraj F7.9: `corp/kpi.py` (reflex hit rate + cost per task kroz
  vrijeme, UNAVAILABLE bez podataka), `CorpPanel.tsx` (portfolio/cost/alerts/risk/KPI/vault) +
  frontClient corp readovi + fixture mode. Zero direktnih poziva. Seal `test_p6f7_9_corp_kpi_surface.py`
  + vitest."_

### F7.10 — Klijent nula E2E + derived exit seal + CLI + merge (seal je izveden)
- **Files:** novo `f7_seal.py` (**derived** po uzoru `f6_seal.py:186–212`: svaki F7.0→F7.9 slajs
  importabilan AND report prisutan; **flipa** seamove `watchtower_alerts` i `full_approval_workbench` na
  live (True iff SEALED); novi UNAVAILABLE registry: `kpi_builder`, `forecasting_burn_eta`,
  `roi_analysis`, `billing_console` (dovoljan je cost-per-klijent izvještaj), `compliance_gap_analysis`,
  `auto_risk_detection` (drift_gates LATER), `business_simulator` (SCI-FI), `value_risk_studio` (SCI-FI),
  `rnd_knowledge_transfer_nlp` (SCI-FI), `hq_intelligence_governed_feeds` (poslije F7),
  `document_forge` (poslije F7), carried: `library_time_travel` (F8), `wss_tls_remote_transport`
  (Tauri-Rust); overclaim guardovi: SCI-FI hard-wired False, flipovi True iff SEALED),
  `f7_projection.py` (`F7RunProjection` — north-star run §7), CLI `aurel corp seal/status` u
  `cli_modules/f7_commands.py` (+ `vault`/`export` iz F7.4), registracija u `cli.py`.
- **NC:** seal je **izveden**, nikad self-assigned; missing modul/report ⇒ BLOCKED deterministički;
  flipovi dokazani (Watchtower živ u HQ, workbench živ); odgođeno eksplicitno; klijent nula E2E prolazi
  **prije** merge-a.
- **Seal:** `test_p6f7_10_f7_exit_seal.py` — north-star §7 end-to-end; SEALED kad je sve prisutno;
  BLOCKED na missing; flipovi True; SCI-FI guardovi False; `aurel corp seal` ispisuje SEALED.
- **Dispatch prompt:** _"Implementiraj F7.10: `f7_seal.py` derived (svi slajsevi + reporti; flipa
  watchtower_alerts + full_approval_workbench; UNAVAILABLE registry za LATER/SCI-FI),
  `f7_projection.py` (north-star), CLI `aurel corp seal/status`. Seal `test_p6f7_10_f7_exit_seal.py`
  vozi §7. Potom puni suite + merge `feat/f7-corp` → master."_

---

## 4. Preporučeni redoslijed (walking skeleton prvo)

1. **Corp okostnica:** F7.0 → F7.1 → F7.5 — najmanji rez koji dokazuje Business Plane: klijent nula
   postoji, trošak mu se pripisuje, portfolio stablo je vidljivo. Sve ostalo visi o ovome.
2. **Nadzor:** F7.3 (Watchtower — flipa najstariji F5 seam) → F7.2 (budget governance).
3. **Dokazi:** F7.4 (Evidence Vault + Output Passport dovršen).
4. **Operater:** F7.6 (wizard) → F7.7 (Risk Register) → F7.8 (workbench).
5. **Front:** F7.9 (KPI + CorpPanel React).
6. **Pečat:** F7.10 — klijent nula E2E, derived exit seal, report, puni suite, merge → master.

Kritičan put je F7.0→F7.1→F7.5 (Corp okostnica) i F7.3 (Watchtower flip).

---

## 5. Cross-cutting invarijante (svaki slajs mora držati)

- **Corp ne dodjeljuje ovlast.** Ovlast ostaje mandat (F6), enforcean fail-closed u `runtime.submit`.
  Client/Job/Risk zapisi su poslovni metapodaci; nijedan ne širi `card.authority` niti zaobilazi gate.
- **Watchtower = vidljivost, nikad ovlast.** Read-only nadzornik: derivira i eskalira, nikad ne blokira,
  ne izvršava, ne mijenja verdikt. Alert bez izvora (source_ref) je nekonstruktibilan.
- **Jedna vrata.** Jedina Corp mutacija je kreiranje okruženja / risk unos kroz `POST /proposals` →
  approval → `runtime.submit`. UI i CLI su read-only projekcije + prijedlozi.
- **Trace = jedini izvor istine.** Attribution/portfolio/heatmap/KPI su projekcije nad traceom (+
  pošteni ledger snapshot za živi burn, F5.5 disciplina); replay ih vraća.
- **Additive-behind-flags.** `AUREL_CORP`/`AUREL_WATCHTOWER` default OFF; off-put byte-identičan F6
  svijetu (ledger bucket se ne puni, HQ stub netaknut). Dokaz: flag-off test + puni suite.
- **No-overclaim (strukturno).** KPI bez podataka = UNAVAILABLE (ne lažna nula); `verified` samo iz P5
  PASS verifikacije; what-if verdikt = evidence, ne authority; JobRecord bez klijenta i alert bez izvora
  nekonstruktibilni; SCI-FI guardovi hard-wired False.
- **Klijent nula prije pravog klijenta.** Cijeli F7 se dokazuje na vlastitom repou end-to-end (§7) prije
  ijednog stvarnog klijenta.
- **Stdlib-only, deterministički.** Pravila i sortiranja deterministička (sorted by `(key, id)`, nikad
  `hash()`); vrijeme samo iz zapisa; bez novih runtime ovisnosti.

---

## 6. Odgođeni seamovi / UNAVAILABLE registry (F7)

| Seam | Status u F7 | Vlasnik / kada |
|---|---|---|
| Watchtower alert feed (F5.5/N seam) | **ŽIVO** (flipa se) | F7.3 |
| Puni approval workbench | **ŽIVO** (flipa se) | F7.8 |
| Output Passport (receipts po poslu) | **DOVRŠEN** | F7.4 |
| Forecasting / burn ETA (`hq_command.predictive`) | UNAVAILABLE | LATER |
| KPI builder (custom KPI-jevi) | UNAVAILABLE | LATER |
| ROI analiza / billing konzola | UNAVAILABLE (cost-per-klijent dovoljan) | LATER |
| Compliance gap analiza | UNAVAILABLE | LATER |
| Auto risk detekcija (drift_gates) | UNAVAILABLE (ručni unos živ) | LATER |
| HQ.Intelligence governed feeds | UNAVAILABLE | poslije F7 |
| Document Forge (izvještaji/ponude iz predložaka) | UNAVAILABLE | poslije F7 |
| Business Simulator / Value&Risk Studio / R&D NLP | UNAVAILABLE (SCI-FI, parkirano) | — |
| Library time-travel | UNAVAILABLE (carried) | F8 |
| WorkOPS Code / AI-editor | UNAVAILABLE (carried) | poslije F7 |
| wss/TLS remote transport | UNAVAILABLE (carried) | Tauri-Rust |

---

## 7. F7 exit seal — north-star scenarij (F7.10 test)

Automatizirani end-to-end koji je definicija uspjeha F7 (**klijent nula**, vlastiti repo):

1. Operator kroz **Agency wizard** sastavi okruženje klijenta nula: predložak {klijent, posao, mandat
   `M_k0` = vlastiti repo, paths, budget, zone rules} → `what_if` impact report točno predvidi koje bi
   probne akcije prošle/pale.
2. Kreiranje ide kroz **jedna vrata**: proposal → approval u HQ.Command → governed zapis; posao se
   pojavi u **Portfolio mapi** (klijent nula → posao → mandat).
3. Intent pod mandatom `M_k0` (Signal/WorkOPS) → AurelEU resolvira (F6) → izvršenje; run vidljiv u
   **Task Runtime feedu** posla sa status overlayem.
4. Trošak runa pripisan: `per_mandate[M_k0]` → posao → klijent nula u **Cost Attribution**; budget
   governance pokazuje alokaciju vs. potrošnju.
5. Pod-agent pokuša write **izvan** mandata ⇒ F6.2 DENY (BLOCKED) ⇒ **Watchtower alert** s source_ref u
   HQ.Command; budget prag prijeđen ⇒ budget alert.
6. **Evidence Vault**: pretraga po `M_k0` vraća cijeli lanac; `export_receipt_bundle` daje Output
   Passport s chain hashom; tamper ⇒ verifikacija fail-closed.
7. **Risk Register** unos za posao (kroz jedna vrata) vidljiv u heatmapi; **workbench** pokazuje pending
   approval s mandat/budget/risk kontekstom.
8. **KPI**: reflex hit rate + cost per task izračunati iz stvarnih podataka (a prazan sustav ih pošteno
   deklarira UNAVAILABLE).
9. Cijeli lanac **replayabilan**; nula direktnih poziva iz UI-ja; flag OFF ⇒ byte-identičan F6 svijet;
   overclaim guardovi (simulator/billing/forecasting) False.

---

## 8. Dubinska razrada — Watchtower (killer modul #1)

**Postojeći temelj (grounded):** `hq_command.py:74–77` — `watchtower()` UNAVAILABLE stub s
`CLAIMS_WATCHTOWER_LIVE = False`; seam registriran u `front_seal.py:73–74` i `f6_seal.py:83–85` s
vlasnikom F7. Svi izvori alerta već postoje u traceu: `BudgetDecisionRecord` (verdict + used/limit +
mandate_id), BLOCKED tranzicije s mandate reason (`runtime.py:319–325`), constitution violation praxis
eventi (parsing uzorak `f6_projection.py:35`), approval audit (`approval_inbox.py:96–105`). **Fali samo
derivator.**

**`WatchtowerAlert` (frozen, `corp/watchtower.py`):** `{alert_id, severity: INFO|WARN|CRITICAL, kind:
BUDGET_DENY|BUDGET_THRESHOLD|MANDATE_BLOCK|CONSTITUTION_VIOLATION|APPROVAL_PENDING, message, source_ref,
mandate_id, client_id}`. `__post_init__` odbija prazan `source_ref` — alert koji ne može citirati izvor
ne postoji (no-overclaim). `alert_id` deterministički iz (kind, source_ref).

**`derive_alerts(trace, ledger, corp_registry, mandate_registry)`:** jedan prolaz po replayu + jedan
ledger snapshot; pravila su čiste funkcije zapis → Optional[alert]; rezultat sortiran po
`(severity_rank, alert_id)`. Client se resolvira mandate_id → `MandateScope.client_id` → CorpRegistry.
Bez ledgera ⇒ budget-prag pravila se preskaču (ne izmišljaju), s napomenom u viewu.

**HQ flip:** `hq_command.watchtower()` kad je `AUREL_WATCHTOWER` ON i builder vezan vraća
`{status: "LIVE", alerts: [...], source: "trace+ledger"}`; `claims_watchtower_alerts` postaje izveden.
OFF ⇒ postojeći stub, byte-identičan (F5.5 seal ostaje zelen).

**Zašto je ovo killer:** prvi modul koji operatoru **aktivno** donosi governance signale (dosad je sve
bilo pull projekcija), a struktura (derivator + source_ref disciplina) je temelj za buduće governed
feedove (HQ.Intelligence, poslije F7) — isti uzorak, drugi izvori.

---

## 9. Dubinska razrada — Cost Attribution + Evidence Vault (killer modul #2)

**Postojeći temelj (grounded):** F6.1 je već proveo `mandate_id` kroz sve trace zapise
(`core_types.py:418/:624/:488/:696`), F6.0 je dao `MandateScope.client_id` + `budget_cents`
(`mandate/mandate.py:36–42`), ledger već broji sve metrike po runu (`budget.py` per_run:
estimated_cost_cents, substantiated vs. estimate-only). P5 daje receipt + fail-closed verifikaciju
(`trace.py:728–757`, `:520–545`) i `TraceVerificationReceipt` (verified samo iz PASS). **Fali pivot i
omotač.**

**Attribution lanac:** charge site (runtime zna `card.mandate_id`) → `per_mandate[M]` bucket (additive)
→ `CostAttributionView` pivot M → job (JobRecord.mandate_ids) → client (MandateScope.client_id,
cross-check s CorpRegistry) → rollup s poštenim substantiated/estimate-only splitom. Trace
`BudgetDecisionRecord.mandate_id` služi kao audit cross-check da pivot ne laže (test uspoređuje).

**Vault lanac:** `EvidenceVaultQuery` filtrira replay po mandate_id (svi zapisi ga nose) →
deterministički sortiran rezultat s entry_hash referencama → `export_receipt_bundle` slaže {receipt,
chain head, zapisi, verification receipt (samo PASS)} u jedan JSON — **Output Passport**: za posao J
možeš klijentu (ili sebi za audit) dati samostalan, integritetom vezan dokaz što je napravljeno, tko je
odobrio, koliko je koštalo. Tamper na bundleu ⇒ chain hash mismatch ⇒ fail-closed.

**Seal proširenja:** pivot == trace cross-check; default mandate_id ⇒ ledger byte-identičan; bundle
verified samo uz PASS; klijent nula rollup točan na north-star runu.

---

**One-line pickup:** _"Čitaj `AUREL_PLAN_08_F7_CORP_DISPATCH.md`; kreni F7.0 (Corp domena: Client/Job +
klijent nula) na grani `feat/f7-corp` per §3, walking-skeleton redoslijedom §4 (okostnica F7.0→F7.1→F7.5,
Watchtower flip F7.3); killer razrade u §8 (Watchtower) i §9 (Cost Attribution + Evidence Vault)."_
