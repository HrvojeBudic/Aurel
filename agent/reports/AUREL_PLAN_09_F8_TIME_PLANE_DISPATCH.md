# AUREL PLAN 09 — F8 Time Plane: Chronos + System ekran (dispatch plan)

**Datum:** 2026-07-11
**Status:** LIVE dispatch plan — F8 razložen na samostalne slajseve (F8.0→F8.6)
**Izvor:** `AUREL_PLAN_02_ADE_PLATFORM_ENFORCEMENT_I_LOOP.md` §F8 (linije 151–157); F7 exit seal carried seam `library_time_travel` → F8
**Ulazno stanje:** F7 (Corp/Business Plane + 3 seam veze) zapečaćen i mergean u `master` (`2067ded`), pushano. Sljedeća grana: `feat/f8-time-plane`.
**Ključni nalaz istraživanja (file:line grounded):** F8 je ~65 % **spajanje postojeće mašinerije**, ~35 % novo. Fork/merge/checkout (`worldline.py`), CAS (`state_store.py`), replay (`trace.py`), P5 verifikacija + causal graph + integrity + receipts (`aurel_trace/`), speculative preflight = sim-gate (`dual_kernel/`), bitemporal as-of (`memory_asof.py`), i **SYSTEM surface već u closed-world enumu** (`surface_registry.py:65`, truth owner `OPERATOR_SYSTEM_ROOT_CONTROL_PLANE`, read-model relacija `system_read_model`) — sve postoji. Novo: Chronos CLI/engine, irreversibility klasifikacija + fork-gate (evidence, ne authority), System read-modeli, library as-of flip, succession drill.

---

## 0. Kako koristiti (svaka sesija)

- Svaki slajs (F8.x) je **samostalna dispatch jedinica**: novi/izmijenjeni fajlovi, flag, seal test,
  no-collapse invarijante, paste-ready dispatch prompt.
- Radi **jedan slajs odjednom**, redoslijedom §4. Nakon svakog: `ruff` + `mypy` na dodirnutim modulima,
  seal test slajsa, fokusirani regres; **puni suite** prije merge-a grane.
- **Zakon svakog slajsa** (§5): additive-behind-flags (default OFF ⇒ **byte-identičan** F7 svijet),
  **Chronos je read-only forenzika + simulacija — nikad drugi izvršni put**; **fork verdikt = evidence za
  HITL, nikad ovlast** (može samo tražiti fork/approval, nikad dopustiti/spustiti rizik); **SYSTEM je
  operator-only** (agenti zabranjeni, `boundaries.py:8`); trace = jedini izvor istine; jedna vrata ostaje.
- **North star** cijele faze (§7): operator pokrene run → prije **nepovratne** akcije (mail/plaćanje/
  deploy/objava) Chronos **forka** stanje i simulira → sim verdikt kao evidence u HITL-u → approve →
  izvršenje za stvarno → sve u System.Forensics replayabilno; `aurel chronos replay/fork/diff` radi;
  succession drill (restore → verify → replay uzorka) prolazi; Library pokazuje memoriju "kakva je bila u
  trenutku T".

---

## 1. Utemeljeno stanje (ground truth, s file:line)

**Postoji (zrelo, F8 spaja):**
- **Fork/merge/checkout:** `worldline.py` — `WorldLineForest` (`:292`), `fork` (`:415`), `checkout`
  (`:337`, read-only rekonstrukcija stanja), `merge` (`:512`), `ForkRef`/`ForkResult`/`MergeRef`/
  `MergeResult`/`MergeConflict` (`:96–233`); tamper-evident lineage, child genesis = `sha(GENESIS, fork_hash)`.
- **CAS:** `state_store.py` — `StateStore.put/has/materialize`; dedup po `_tree_hash` (dijeli s sandboxom),
  keyan na trace `before_state_hash`/`after_state_hash`; atomic `.tmp-*` rename.
- **Replay + P5 verifikacija:** `trace.py` (`replay()`, `PersistentTraceLedger`, `receipt.json` `:728–757`);
  `aurel_trace/golden_thread.py` (`GoldenThreadGraph`, causal DAG, `CausalEdgeKind`/`CausalNodeKind`),
  `trace_query.py` (`TraceRunSummary`/`TraceEventSummary` deterministički filteri), `trace_resolver.py`
  (`TraceVerificationDecision` ladder), `persistent_integrity.py` (brzi + puni integrity check),
  `replay_readiness.py` (`assess_replay_readiness` — je li run replayabilan), `trace_export.py`
  (`TraceExportManifest`, retention labeli), `trace_receipts.py` (`TraceVerificationReceipt`, koji F7.4 već
  koristi). **Sve read-only, zapečaćeno.**
- **Sim-gate (speculative preflight):** `dual_kernel/kernel.py` (`DualKernelRuntime`, flag
  `AUREL_DUAL_KERNEL`; GOVERNED ruta = spekulativni preflight u efemernoj kopiji → `merge_gate.py`
  `MergeGate.evaluate` → `MergeVerdict` ladder → samo PASS izvršava za stvarno), `AUREL_DK_MATERIALIZE`
  (persistent fork checkout). **Ovo JE "sim verdikt = evidence" mehanizam; F8 ga primjenjuje na nepovratne
  akcije.**
- **Rizik + side-effect model:** `core_types.py:58–63` (`RiskLevel`: HIGH = "destruktivno/nepovratno/
  network/secrets"), `ToolSideEffectType`; `runtime.py` submit pipeline (identity → sandbox-backend gate →
  policy `:270` → policy-resolver `:297` → **mandate F6.2 `:319`** → approval `:333` → izvršenje).
- **SYSTEM surface:** `aurel_shell/surface_registry.py:65` (`AurelSurfaceKind.SYSTEM`),
  `aurel_shell/boundaries.py:62` (truth owner `OPERATOR_SYSTEM_ROOT_CONTROL_PLANE`), `:72`
  (`operator_root_control_projection`), `:82` (`system_read_model`), `:8` (SYSTEM operator-only, agenti
  zabranjeni). **Deklariran, read-model ne postoji — F8 ga puni** (isto kao CORP prije F7).
- **System-screen izvori:** `model_router.py` (`ModelRouter.complete`, routing po namjeni), `model_config.py`
  (`ProviderProfile`/`ModelProfile`); `policy_cards/registry.py` (`PolicyCardRegistry`, `canonical_hash`,
  deterministički sort); trace + `trace_query.py` (audit); `budget.py` (`BudgetLedger.snapshot()`,
  per_run/per_mandate/per_agent — F7.1 dodao per_mandate); `trace_export.py` + `persistent_integrity.py`
  (archive/retention status).
- **Library as-of:** `memory_asof.py` (`AsOfView.as_of(valid_time, transaction_time)`, bitemporal,
  clock-free — Track A A0); `front_server/library.py` (`LibraryReadModel.from_trace` + `provenance_chain`);
  seam `CLAIMS_LIBRARY_TIME_TRAVEL` hard-wired False (`front_server/library.py`, carried u f7_seal).
- **Derived-seal + CLI + flag uzorak:** `f6_seal.py`/`f7_seal.py` (slice = importabilan modul AND report;
  flipped seams; UNAVAILABLE registry; overclaim guardovi), `cli_modules/f7_commands.py` +
  `cli.py` `corp` subparser (`aurel corp seal/status`), flag helper `flag_enabled()` po modulu.

**NE postoji (F8 gradi):**
1. **Chronos engine + CLI** — `aurel chronos replay/fork/diff` (read-only forenzika/simulacija nad
   worldline+trace+state_store).
2. **Irreversibility klasifikacija + fork-gate** — označi HIGH/nepovratne alate; forkaj+simuliraj prije
   stvarnog izvršenja; sim verdikt = evidence za HITL (nikad ovlast).
3. **System surface boundary + read-modeli** — `system_read_model` + 5 projekcija (model-routing, policy
   browser, audit log, usage/kvote, archive status) na `/read/system/*`.
4. **Library time-travel** — flip `CLAIMS_LIBRARY_TIME_TRAVEL`; `LibraryReadModel.as_of(T)` preko
   `memory_asof`.
5. **Succession drill** — `aurel drill succession` (export → restore → verify → replay uzorka → report).
6. **System React panel + F8 derived exit seal + projekcija**.

**Zaključak:** vremenska jezgra (fork/replay/CAS/verifikacija/sim-gate) je zrela i zapečaćena; F8 = tanki
Chronos sloj koji je surfacea + primjenjuje na nepovratne akcije + System ekran kao read-only kontrolna
ploča. Nema drugog izvršnog puta; sve je forenzika, simulacija (evidence), ili read-only projekcija.

---

## 2. Arhitektonska kičma: Chronos je vrijeme kao read-only forenzika + fork-evidence

Chronos ne uvodi novi izvršni kanal — on je **vremenska leća** nad postojećom istinom (trace + state_store
+ worldline):

- **Replay (forenzika):** deterministički ponovi run iz persistent tracea + `state_store` checkout;
  usporedi rekonstruirano stanje s zapisanim `after_state_hash` (`replay_readiness` prvo provjeri je li
  run replayabilan). Read-only, nula mutacija.
- **Fork (simulacija):** `worldline.fork()` mintne child run iz roditeljskog stanja na tranziciji N; akcija
  se izvrši u efemernoj kopiji (reuse dual_kernel preflight); rezultat = **evidence**, nikad commit.
- **Diff (usporedba):** dva `GoldenThreadGraph`-a → causal diff (što se promijenilo između runa A i B).
- **Irreversibility gate:** u `runtime.submit`, kad je akcija HIGH/nepovratna i `AUREL_CHRONOS_FORK_GATE`
  ON, prije stvarnog izvršenja se forka+simulira; sim verdikt se prilaže HITL-u kao evidence. **Escalation-
  only:** može samo tražiti fork/approval, nikad dopustiti ili spustiti rizik (isti zakon kao Track C
  `influence_is_escalation_only`).
- **System ekran:** čiste read-only projekcije nad governance stanjem (model router, policy cards, trace
  audit, budget, archive). Operator-only.

**Master flagovi:** `AUREL_CHRONOS` (engine + CLI + reads; OFF ⇒ Chronos reads UNAVAILABLE),
`AUREL_CHRONOS_FORK_GATE` (fork-before-irreversible; OFF ⇒ `runtime.submit` byte-identičan), `AUREL_SYSTEM`
(System read-modeli; OFF ⇒ `/read/system/*` UNAVAILABLE). Reuse `AUREL_DUAL_KERNEL`/`AUREL_DK_MATERIALIZE`
za fork izvršenje. Svi default OFF.

---

## 3. Per-slajs dispatch specifikacije

> Legenda: **Files** = novo / izmijenjeno. **Flag** default OFF. **Seal** = pytest fajl. **NC** = no-collapse.

### F8.0 — Chronos foundation: replay / fork / diff engine + CLI (flag `AUREL_CHRONOS`)
- **Files:** novo `chronos/replay.py` (`ChronosReplay.from_run(trace_dir, run_id)` → deterministički replay
  preko `replay_readiness` + `state_store` checkout; vrati `ReplayResult{replayable, checked, mismatch_at,
  final_hash}` — read-only, PASS iff rekonstruirano == zapisano), `chronos/fork.py`
  (`ChronosFork.fork_at(run_id, transition_n)` → `worldline.fork()` child run iz roditeljskog stanja;
  vrati `ForkResult` + child run_id; efemerno osim `AUREL_DK_MATERIALIZE`), `chronos/diff.py`
  (`ChronosDiff.compare(run_a, run_b)` → dva `GoldenThreadGraph`-a → deterministički causal diff
  `{added, removed, changed}` sortiran), `chronos/__init__.py` (flag helper), CLI
  `cli_modules/chronos_commands.py` (`aurel chronos replay/fork/diff [--json]`) + `cli.py` registracija.
- **NC:** sve **read-only nad traceom/state_storeom** (nula mutacija originala; fork mintaneov je child
  run, ne mijenja roditelja); replay deterministički (isti trace ⇒ isti rezultat); ne-replayabilan run ⇒
  `replayable=False` s razlogom (nikad lažni PASS); diff deterministički (sorted, bez `hash()`); flag OFF ⇒
  CLI honestly UNAVAILABLE.
- **Seal:** `test_p6f8_0_chronos.py` — replay poznatog runa PASS; tamperan run ⇒ mismatch_at; fork mintaneov
  child run iz stanja N (roditelj netaknut); diff dva runa deterministički; ne-replayabilan ⇒ pošteno False.
- **Dispatch prompt:** _"Implementiraj F8.0: `chronos/{replay,fork,diff}.py` (read-only nad
  worldline+trace+state_store, reuse replay_readiness/golden_thread), CLI `aurel chronos replay/fork/diff`.
  Flag `AUREL_CHRONOS`. Seal `test_p6f8_0_chronos.py`."_

### F8.1 — Irreversibility gate: fork-before-irreversible kao evidence (flag `AUREL_CHRONOS_FORK_GATE`)
- **Files:** novo `chronos/irreversibility.py` (`classify_irreversibility(cmd, tool_spec) →
  IrreversibilityClass{reversible|guarded|irreversible, reason}` — deterministička taksonomija: HIGH risk +
  side-effect ∈ {network, deploy, publish, payment, mail, secrets} ⇒ irreversible; **nekonstruktibilna
  klasa bez razloga**), novo `chronos/fork_gate.py` (`evaluate_fork_gate(cmd, card, runtime) →
  ForkGateEvidence{simulated, verdict, outcome_preview, fork_run_id}` — forkaj+simuliraj u efemernoj kopiji
  reuse `dual_kernel` preflight; **escalation-only**: `influence_is_escalation_only` forbid-False — može
  samo tražiti approval/fork, nikad permit/lower-risk), edit `runtime.py` (gate **između mandate `:319` i
  approval `:333`**: kad flag ON i akcija irreversible ⇒ priloži ForkGateEvidence u approval kontekst;
  fail-closed ako fork UNAVAILABLE na nepovratnoj akciji).
- **NC:** fork verdikt je **evidence za HITL, nikad ovlast** (ne blokira, ne dopušta, ne mijenja rizik —
  samo informira approval); flag OFF ⇒ `runtime.submit` **byte-identičan** (gate se ne evaluira);
  UNAVAILABLE twin na nepovratnoj akciji ⇒ fail-closed (ne izvršava naslijepo); simulacija je efemerna
  (roditeljsko stanje netaknuto); reuse dual_kernel (ne gradi drugi fork engine).
- **Seal:** `test_p6f8_1_irreversibility.py` — nepovratna akcija klasificirana; fork gate priloži evidence u
  approval; evidence ne može permitirati (escalation-only); UNAVAILABLE twin ⇒ fail-closed; flag OFF ⇒
  byte-identičan submit; reverzibilna akcija ⇒ nema forka.
- **Dispatch prompt:** _"Implementiraj F8.1: `chronos/irreversibility.py` (taksonomija, klasa
  nekonstruktibilna bez razloga), `chronos/fork_gate.py` (fork+simuliraj reuse dual_kernel, escalation-
  only), gate u runtime.submit između :319 i :333 (evidence za HITL, fail-closed na UNAVAILABLE twin,
  byte-identičan off). Flag `AUREL_CHRONOS_FORK_GATE`. Seal `test_p6f8_1_irreversibility.py`."_

### F8.2 — System surface skeleton + audit-log + usage read-modeli (flag `AUREL_SYSTEM`)
- **Files:** edit `aurel_shell/boundaries.py` (definiraj SYSTEM projekcije: `system_read_model` truth =
  governance state), novo `front_server/system_read_model.py` (`SystemReadModel`: **audit log** — trace
  query filtriran po kind/mandate_id/agent/vrijeme, deterministički sortiran + paginacija reuse
  `aurel_trace.trace_query`; **usage/kvote** — `budget.snapshot()` + remaining vs. policy cap po
  mandate/agent), edit `front_server/read_models.py` (registriraj `system/audit`, `system/usage`).
- **NC:** čista read-only projekcija (zero-write); **SYSTEM operator-only** — read modeli ne izlažu agent-
  dohvatljive mutacije; prazan filter = prazan (ne UNAVAILABLE); truth labeli propagiraju; flag OFF ⇒
  `/read/system/*` UNAVAILABLE s razlogom.
- **Seal:** `test_p6f8_2_system_audit_usage.py` — audit filtrira po kind/mandate/vrijeme deterministički;
  usage iz živog ledgera + remaining točan; zero-write; `/read/system/audit` + `/read/system/usage` živi
  kad flag ON, UNAVAILABLE off.
- **Dispatch prompt:** _"Implementiraj F8.2: `SystemReadModel` (audit log preko trace_query filtri +
  paginacija; usage/kvote iz budget.snapshot + remaining), boundaries SYSTEM projekcije, registracija
  system/audit + system/usage. Flag `AUREL_SYSTEM`, operator-only, zero-write. Seal
  `test_p6f8_2_system_audit_usage.py`."_

### F8.3 — System: model-routing + policy-browser + archive-status read-modeli (flag `AUREL_SYSTEM`)
- **Files:** edit `front_server/system_read_model.py` (**model & routing** — `ModelRouter` profili +
  promotion gates iz `evaluation/` (read-only, promocija = evidence, ne izvršenje); **policy card browser**
  — `PolicyCardRegistry` enumeracija + `canonical_hash`, secrets maskiran; **archive status** —
  `TraceExportManifest` retention + `persistent_integrity` status + receipt backlog), edit `read_models.py`
  (registriraj `system/model_routing`, `system/policies`, `system/archive`).
- **NC:** read-only enumeracija; **secrets uvijek maskiran** (sha[:8] fingerprint, nikad plaintext — F2
  redakcija disciplina); policy card **ne dodjeljuje ovlast prikazom** (P1.6 zakon); promotion gate =
  evidence prikaz, ne trigger; archive status pošten (UNAVAILABLE dio bez izvora).
- **Seal:** `test_p6f8_3_system_model_policy_archive.py` — model profili + promotion gates enumerirani;
  policy cards s canonical_hash, secrets maskiran; archive retention/integrity status; zero-write.
- **Dispatch prompt:** _"Implementiraj F8.3: dopuni `SystemReadModel` s model-routing (profili + promotion
  gates read-only), policy-card browser (registry + canonical_hash, secrets maskiran), archive-status
  (export manifest + integrity + receipt backlog); registriraj system/model_routing + system/policies +
  system/archive. Seal `test_p6f8_3_system_model_policy_archive.py`."_

### F8.4 — Library time-travel: as-of preko memory_asof (flag `AUREL_SYSTEM`; flipa `library_time_travel`)
- **Files:** edit `front_server/library.py` (`LibraryReadModel.as_of(valid_time, transaction_time)` reuse
  `memory_asof.AsOfView` + trace as-of; flipa `CLAIMS_LIBRARY_TIME_TRAVEL` na **izveden** —
  `bool(memory_asof_available)`), edit `read_models.py` (`/read/library?as_of=T`).
- **NC:** as-of je čista projekcija (bitemporal, clock-free — `memory_asof` A0); prazan T ⇒ `current()`
  (byte-identičan postojećem Library); nikad ne fabricira povijest (as-of vraća samo zapise s otvorenim/
  poklapajućim intervalom); **flipa** `library_time_travel` seam (F7-carried).
- **Seal:** `test_p6f8_4_library_time_travel.py` — as-of(T) vraća memoriju "kakva je bila u T"; prazan T ⇒
  current identičan; `claims_library_time_travel` True kad as-of dostupan; flip dokazan.
- **Dispatch prompt:** _"Implementiraj F8.4: `LibraryReadModel.as_of(T)` reuse memory_asof.AsOfView,
  `/read/library?as_of=`, flip `CLAIMS_LIBRARY_TIME_TRAVEL` izveden. Prazan T ⇒ current byte-identičan.
  Seal `test_p6f8_4_library_time_travel.py`."_

### F8.5 — Succession drill + System React panel (flag `AUREL_SYSTEM`)
- **Files:** novo `cli_modules/drill_commands.py` (`aurel drill succession [--sample N] [--out PATH]` →
  export (`trace_export`) → restore checkout (`state_store` + `worldline.checkout`) → verify
  (`persistent_integrity`) → replay uzorka N runova (`chronos.replay`) → `SuccessionDrillReport{exported,
  restored, verified, replayed, discrepancies}`) + `cli.py` registracija; novo
  `web/shell/src/components/front/SystemPanel.tsx` (audit log, usage/kvote, model routing, policy cards,
  archive status; wire u `FrontSurface` za `system`), edit `frontClient.ts` (system read builderi) +
  `front-types.ts` (System DTO-i).
- **NC:** drill je **read-only nad kopijom** (ne dira live trace; restore ide u izolirani checkout);
  discrepancy ⇒ pošteno prijavljen (nikad tihi PASS); React panel zero direktnih poziva (sve kroz
  `frontClient` `/read/system/*`); server OFF ⇒ fixture mode (F5.8 disciplina); SYSTEM operator-only u UI-ju.
- **Seal:** `test_p6f8_5_succession_drill.py` (+vitest) — drill export→restore→verify→replay prolazi na
  demo traceu; discrepancy detektiran na tamperu; `/read/system/*` živ; UI zero direktnih poziva.
- **Dispatch prompt:** _"Implementiraj F8.5: `aurel drill succession` (export→restore→verify→replay uzorka,
  read-only nad kopijom, discrepancy pošteno), `SystemPanel.tsx` (audit/usage/model/policy/archive) +
  frontClient system readovi + fixture mode. Seal `test_p6f8_5_succession_drill.py` + vitest."_

### F8.6 — Derived exit seal + F8 north-star projekcija + CLI + merge (seal je izveden)
- **Files:** novo `f8_seal.py` (**derived** po uzoru `f7_seal.py`: svaki F8.0→F8.6 slajs importabilan AND
  report prisutan; **flipa** seam `library_time_travel` na live (True iff SEALED); novi UNAVAILABLE
  registry: `chronos_ui_forge` (Lab.Simulation UI — F9), `distributed_replay` (SCI-FI),
  `hsm_key_ceremony` (SCI-FI), `threat_detection_engine` (LATER), `policy_editor` (LATER — browser je
  read-only), `automated_succession_restore` (LATER — drill je poluautomatski); overclaim guardovi: SCI-FI
  hard-wired False, flip True iff SEALED), `f8_projection.py` (`F8RunProjection` — north-star §7: run →
  fork-before-irreversible evidence → System.Forensics replay view), CLI `aurel chronos seal/status` u
  `cli_modules/chronos_commands.py`.
- **NC:** seal je **izveden**, nikad self-assigned; missing modul/report ⇒ BLOCKED deterministički; flip
  dokazan (library as-of live); odgođeno eksplicitno; north-star §7 prolazi **prije** merge-a.
- **Seal:** `test_p6f8_6_f8_exit_seal.py` — north-star §7 end-to-end; SEALED kad je sve prisutno; BLOCKED na
  missing; flip True; SCI-FI guardovi False; `aurel chronos seal` ispisuje SEALED.
- **Dispatch prompt:** _"Implementiraj F8.6: `f8_seal.py` derived (svi slajsevi + reporti; flipa
  library_time_travel; UNAVAILABLE za LATER/SCI-FI), `f8_projection.py` (north-star), `aurel chronos
  seal/status`. Seal `test_p6f8_6_f8_exit_seal.py` vozi §7. Potom puni suite + merge `feat/f8-time-plane`
  → master."_

---

## 4. Preporučeni redoslijed (walking skeleton prvo)

1. **Chronos okostnica:** F8.0 (replay/fork/diff + CLI) — najmanji rez koji dokazuje "vrijeme kao read-only
   forenzika/simulacija". Sve ostalo visi o forku/replayu.
2. **Nepovratno:** F8.1 (irreversibility gate) — killer modul; fork-before-irreversible kao evidence u
   `runtime.submit` (shadow-first, byte-identičan off). Kritičan put i najveći rizik (hot path).
3. **System ekran:** F8.2 (audit + usage) → F8.3 (model/policy/archive) — read-only kontrolna ploča.
4. **Vrijeme u Library:** F8.4 (as-of, flipa carried seam).
5. **Otpornost + UI:** F8.5 (succession drill + System React panel).
6. **Pečat:** F8.6 — north-star, derived exit seal, report, puni suite, merge → master.

Kritičan put je F8.0 (Chronos jezgra) i F8.1 (irreversibility gate). System ekran (F8.2/3) je paralelizabilan.

---

## 5. Cross-cutting invarijante (svaki slajs mora držati)

- **Chronos je read-only forenzika + simulacija.** Replay/diff nula mutacija; fork mintaneov child run, ne
  dira roditelja; nema drugog izvršnog puta.
- **Fork verdikt = evidence, nikad ovlast.** Escalation-only (`influence_is_escalation_only` forbid-False):
  može tražiti fork/approval, nikad dopustiti/spustiti rizik. UNAVAILABLE twin na nepovratnoj akciji ⇒
  fail-closed.
- **SYSTEM je operator-only.** Read modeli ne izlažu agent-dohvatljive mutacije; secrets uvijek maskiran;
  policy card ne dodjeljuje ovlast prikazom.
- **Trace = jedini izvor istine.** Replay/fork/diff/System/Library su projekcije/simulacije nad traceom +
  state_store + worldline; nijedan ne uvodi drugi store.
- **Additive-behind-flags.** `AUREL_CHRONOS`/`_CHRONOS_FORK_GATE`/`_SYSTEM` default OFF; off-put byte-
  identičan F7 (osobito `runtime.submit` — dokaži flag-off test + puni suite).
- **No-overclaim (strukturno).** Ne-replayabilan run = pošteno False (nikad lažni PASS); as-of ne fabricira
  povijest; irreversibility klasa nekonstruktibilna bez razloga; SCI-FI guardovi hard-wired False;
  `verified` samo iz stvarne P5 verifikacije (F7.4 zakon).
- **Reuse, ne gradi ispočetka.** Fork = `worldline`; sim = `dual_kernel` preflight; verifikacija =
  `aurel_trace`; as-of = `memory_asof`. F8 spaja, ne duplicira.

---

## 6. Odgođeni seamovi / UNAVAILABLE registry (F8)

| Seam | Status u F8 | Vlasnik / kada |
|---|---|---|
| Library time-travel (F7-carried) | **ŽIVO** (flipa se) | F8.4 |
| Chronos/Simulation UI forge (Lab.Simulation) | UNAVAILABLE | F9 (Lab ekran) |
| Policy editor (browser je read-only) | UNAVAILABLE | LATER |
| Threat detection engine | UNAVAILABLE | LATER |
| Automated succession restore (drill je poluautomatski) | PARTIAL | LATER |
| Distribuirani/paralelni replay | UNAVAILABLE (SCI-FI) | — |
| HSM key ceremony | UNAVAILABLE (SCI-FI) | — |
| wss/TLS remote transport (carried) | UNAVAILABLE | Tauri-Rust |

---

## 7. F8 exit seal — north-star scenarij (F8.6 test)

Automatizirani end-to-end koji je definicija uspjeha F8:

1. Operator pokrene run pod mandatom (F6/F7); pod-agent predloži **nepovratnu** akciju (npr. `deploy` ili
   `send_mail`) kroz jedna vrata.
2. `AUREL_CHRONOS_FORK_GATE` ON: `runtime.submit` klasificira akciju kao **irreversible** (F8.1) → **forka**
   stanje i **simulira** u efemernoj kopiji (reuse dual_kernel) → `ForkGateEvidence{outcome_preview,
   verdict}`.
3. Sim verdikt se prilaže **HITL approvalu** kao evidence (nikad ovlast — operater i dalje odlučuje).
   Approve ⇒ akcija se izvrši za stvarno; deny ⇒ ništa (fork bio samo simulacija).
4. Cijeli run je **replayabilan** iz System.Forensics: `aurel chronos replay <run_id>` PASS; `aurel chronos
   diff <sim_run> <real_run>` pokaže razliku simulacije i stvarnosti.
5. **System ekran** (operator-only): audit log akcije + budget usage + model routing + policy cards +
   archive status — sve read-only projekcije.
6. **Library** pokaže memoriju "kakva je bila u trenutku T" (as-of, F8.4).
7. **Succession drill** (`aurel drill succession`) prođe: export → restore → verify → replay uzorka bez
   discrepancy.
8. Flag OFF ⇒ byte-identičan F7 svijet; overclaim guardovi (distributed replay, HSM) False; `verified`
   samo iz P5 PASS.

---

## 8. Dubinska razrada — Irreversibility gate (killer modul)

**Postojeći temelj (grounded):** `dual_kernel/kernel.py` VEĆ radi spekulativni preflight u efemernoj kopiji
→ `merge_gate.py` `MergeGate.evaluate` → verdikt gejtira stvarno izvršenje (flag `AUREL_DUAL_KERNEL`).
`core_types.py:58–63` VEĆ ima `RiskLevel.HIGH` = "destruktivno/nepovratno/network/secrets". `runtime.py`
submit pipeline ima točan hook između mandate gate (`:319`) i approval (`:333`). **Fali klasifikator +
tanki gate koji ovo veže na HITL.**

**`classify_irreversibility(cmd, tool_spec)` (`chronos/irreversibility.py`):** deterministička taksonomija
→ `IrreversibilityClass{reversible|guarded|irreversible, reason}`. `irreversible` iff
`cmd.declared_risk == HIGH` I `tool_spec.side_effect ∈ {network, deploy, publish, payment, mail, secrets}`.
`__post_init__` odbija klasu bez razloga (no-overclaim).

**`evaluate_fork_gate(cmd, card, runtime)` (`chronos/fork_gate.py`):** kad flag ON i klasa `irreversible`:
`worldline.fork()` child run → izvrši akciju u efemernoj kopiji (reuse dual_kernel preflight) →
`ForkGateEvidence{simulated, verdict, outcome_preview, fork_run_id}`. **Escalation-only** —
`influence_is_escalation_only` forbid-False: evidence može samo tražiti approval/fork, nikad permitirati ili
spustiti rizik. UNAVAILABLE twin (fork se ne može konstruirati) na nepovratnoj akciji ⇒ **fail-closed**
(ne izvršava naslijepo).

**Gate u `runtime.py` (između :319 i :333):** kad flag OFF ⇒ gate se ne evaluira (byte-identično). Kad ON i
akcija irreversible ⇒ `ForkGateEvidence` se priloži approval kontekstu (HITL ga vidi kao "simulirani
ishod"); approval ostaje jedini odlučitelj. Fork verdikt **nikad** ne blokira/dopušta sam — samo informira.

**Zašto tu:** mandate je već potvrdio ovlast (`:319`); approval je HITL točka (`:333`); fork-before-
irreversible sjedne točno između — simulira odobrenu-ali-nepovratnu akciju pa approval ima evidence.
Zakon "sim = evidence, ne authority" (isti kao Track C) je strukturno očuvan.

**Seal proširenja (`test_p6f8_1_irreversibility.py`):** nepovratna akcija klasificirana s razlogom; fork
gate priloži evidence; evidence ne može permitirati (escalation-only test); UNAVAILABLE twin ⇒ fail-closed;
flag-off ⇒ submit byte-identičan; reverzibilna akcija ⇒ nema forka.

---

## 9. Dubinska razrada — Chronos replay/fork/diff

**Postojeći temelj (grounded):** `worldline.py` (`fork`/`checkout`/`merge`, tamper-evident lineage),
`state_store.py` (CAS checkout stanja), `trace.py` (`replay()` + persistent JSONL + `receipt.json`),
`aurel_trace/replay_readiness.py` (`assess_replay_readiness`), `aurel_trace/golden_thread.py`
(`GoldenThreadGraph` causal DAG), `aurel_trace/persistent_integrity.py`. **Fali orkestracija u tri glagola.**

**`ChronosReplay.from_run(trace_dir, run_id)`:** prvo `assess_replay_readiness` (svi evidence refovi +
state_store nodovi prisutni?); ako da, deterministički ponovi tranzicije, `state_store.checkout` svakog
stanja, usporedi rekonstruirani `_tree_hash` s zapisanim `after_state_hash`. `ReplayResult{replayable,
checked_count, mismatch_at, final_hash}`. Ne-replayabilan ⇒ `replayable=False` s razlogom (nikad lažni PASS).

**`ChronosFork.fork_at(run_id, transition_n)`:** `worldline.fork()` iz roditeljskog stanja na tranziciji N →
child run (genesis = `sha(GENESIS, fork_hash)`); efemerno (tmpdir) osim `AUREL_DK_MATERIALIZE`. Roditelj
netaknut. Vrati `ForkResult` + child_run_id.

**`ChronosDiff.compare(run_a, run_b)`:** izgradi `GoldenThreadGraph` za oba → causal diff `{added, removed,
changed}` (čvorovi po `canonical_event_id`), deterministički sortiran. Read-only.

**CLI:** `aurel chronos replay <run_id>` / `fork <run_id> --at N` / `diff <run_a> <run_b>` `[--json]`; flag
OFF ⇒ honestly UNAVAILABLE (kao `aurel corp` disciplina).

**Seal proširenja (`test_p6f8_0_chronos.py`):** replay poznatog runa PASS; tamperan trace ⇒ `mismatch_at`
postavljen; fork mintaneov child (roditelj netaknut, provjeri hasheve); diff dva runa deterministički;
ne-replayabilan run ⇒ pošteno False s razlogom.

---

**One-line pickup:** _"Čitaj `AUREL_PLAN_09_F8_TIME_PLANE_DISPATCH.md`; kreni F8.0 (Chronos replay/fork/diff
+ CLI) na grani `feat/f8-time-plane` per §3, walking-skeleton redoslijedom §4 (Chronos jezgra F8.0 →
irreversibility gate F8.1); killer razrade u §8 (irreversibility gate) i §9 (Chronos engine)."_
