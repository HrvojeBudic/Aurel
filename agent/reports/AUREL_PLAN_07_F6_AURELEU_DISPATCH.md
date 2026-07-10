# AUREL PLAN 07 — F6 AurelEU Dispatcher + Constitution + Mandati (dispatch plan)

**Datum:** 2026-07-10
**Status:** LIVE dispatch plan — F6 razložen na samostalne slajseve (F6.0→F6.10)
**Izvor:** `AUREL_PLAN_02_ADE_PLATFORM_ENFORCEMENT_I_LOOP.md` §F6 (linije 132–138); doktrina identiteta iz `identity/__init__.py`
**Ulazno stanje:** F5 zapečaćen i mergean u `master` (`2b806aa`); grana `feat/f5-front-v1`. Sljedeća grana: `feat/f6-aureleu`.
**Ključni nalaz istraživanja:** F6 je ~70 % **spajanje postojeće mašinerije** (persona compiler, policy_cards, dual_kernel) + ~30 % novo (Mandate objekt, scope-enforcement gate, delegacijski prozori, mandate_id u traceu). Nije greenfield.

---

## 0. Kako koristiti (svaka sesija)

- Svaki slajs (F6.x) je **samostalna dispatch jedinica**: novi/izmijenjeni fajlovi, flag, seal test,
  no-collapse invarijante i paste-ready dispatch prompt.
- Radi **jedan slajs odjednom**, redoslijedom §4. Nakon svakog: `ruff` + `mypy` na dodirnutim modulima,
  seal test slajsa, fokusirani regres; **puni suite** (`AGENTIC_SKIP_RECURSIVE_SMOKE=1 .venv/bin/python -m
  pytest -q -p no:cacheprovider`, background) prije merge-a grane.
- **Zakon svakog slajsa** (§5): additive-behind-flags (default OFF ⇒ **byte-identičan** off put — pada
  natrag na F5 "jedna default persona"), **Identity ≠ authority** (persona = izraz, mandat = ovlast),
  mandat **putuje s agentom** i enforcea se **fail-closed** u `runtime.submit`, trace = jedini izvor
  istine, **jedna vrata** ostaje (AurelEU živi UNUTAR dispečera, ne pored njega).
- **North star** cijele faze (§7): operator u Signalu pod mandatom ("klijent X, repo Y, budget Z, EU-data")
  zada zadatak → AurelEU resolvira personu (role-fluid) + mandat + citira delegaciju → dispečira pod-agenta →
  akcija izvan mandata **DENY**, u opsegu prolazi → approval → izvršenje → `mandate_id` u **svakom** trace
  zapisu → sve replayabilno; dvo-personalne opcije u Boardu; `aurel panic` bi zaustavio na G0.

---

## 1. Utemeljeno stanje (ground truth, s file:line)

**Postoji (zrelo, F6 spaja):**
- **Identity kernel + persona (P1.4), izraz-only, hashiran/validiran:** `identity/kernel.py`
  (`AurelIdentityKernel`, immutables `self_escalation_allowed=false`, `operator_final_authority=true`),
  `identity/persona.py:160–181` (`AurelPersonaManifest` — izraz, NE ovlast), `config/aurel/*.yaml`
  (kernel/persona/operator_contract/communication_modes/identity_prompt_compiler/self_model_policy).
- **`identity_prompt_compiler` VEĆ kompajlira identitet → siguran system prompt:**
  `prompts/identity_context_compiler.py` (`compile_identity_prompt_context()`, cross-layer contradiction
  detekcija CTR-001..024, dominance kernel>contract>persona>mode), `prompts/identity_context.py:30–44`
  (`IdentityPromptContext`). **Ovo je motor "role-fluid persona switch-a" — već postoji.**
- **Communication modes (7):** `identity/communication_modes.py:114–122` (FOCUS/DEBUG/DEPLOY/SHADOW/EVOLVE/
  CHANNEL/HERETIC; global boundaries svi `false` — "mode can shape the mind, not move the hand").
- **Operator contract s praznim delegacijskim placeholderima:** `identity/operator_contract.py:93–97`
  (`OperatorFuturePlaceholders`: `autonomy_session_ref`, `delegation_grant_ref`, `approval_workbench_ref`,
  `non_repudiation_attestation_ref` — **svi null; F6 ih puni**).
- **Autonomy scale engine (A0–A7):** `identity/autonomy_scale_engine.py:29–39` (A7 = DENIED), +
  `identity/operator_consent.py` (request/record/decision data model), `identity/authority_delta.py`.
- **Policy cards sustav VEĆ postoji:** `policy_cards/models.py:189–212` (`PolicyCard` frozen: kind/scope/
  risk_binding/authority_binding), `policy_cards/registry.py:93–190` (`PolicyCardRegistry`,
  `canonical_hash()`), `policy_cards/resolver.py` (Custos shadow-mode resolver), `conflict_algebra.py`
  (strictest-wins). **Zakon: "policy card nikad ne dodjeljuje ovlast samim postojanjem."**
- **Memory zone VEĆ postoje (14):** `policy_cards/memory_write.py:64–77` (SCRATCHPAD…CANON_MEMORY/
  POLICY_MEMORY/FORBIDDEN, `_check_zone_protection()`) — ali **NISU mandat-particionirane**.
- **`runtime.submit` pipeline s točnim hookom:** `runtime.py:202–510`; policy verdict (`:265–285`),
  policy resolver influence (`:292–307`), **approval (`:309`)**. Mandate scope-check ide **između :307 i :309**.
- **AgentCard/AuthorityScope:** `core_types.py:143–187` (`AuthorityScope`: write_paths/read_paths/max_risk/
  allow_network/allow_secrets; `AgentCard`: allowed_tools/denied_tools/`memory_scope="project-local"`).
- **DN mašinerija (dual_kernel) VEĆ postoji:** `dual_kernel/kernel.py:66–126` (`DualKernelRuntime`, flag
  `AUREL_DUAL_KERNEL`), `sigma.py` (`SigmaGovernor` — graduated autonomy/track-record), `merge_gate.py`
  (`MergeGate` — ponderirani merge verdikt), `praxis.py` (advisory eventi). **F6 ovo surfacea, ne gradi.**
- **Governance G0–G5 profili:** `governance/profile.py:30–150` (standard=G2, ENFORCE_FAIL_CLOSED),
  `governance/enforcement_profiles.py`. "Violation → G0" = pad na najgovernaniji nivo.
- **F5 Front (jedna vrata):** `front_server/proposal_dispatcher.py:56–74` (`_dispatch_converse` — **točka
  gdje AurelEU resolvira**), `conversation.py:37–41` (statični `CHAT_SYSTEM` — F6 ga zamjenjuje kompajliranim
  identitetom), `ConversationTurn.mandate_id`/`role` (`:67–68`, danas pass-through).

**NE postoji (F6 gradi):**
1. **`Mandate` objekt + registry** — verzionirani snop {policy_cards + persona/mode + memory-zone rules +
   authority_overrides + scope (repo/paths/klijent/budget) + expiry}; `mandate_id` se **resolvira**.
2. **Mandate scope-enforcement gate** u `runtime.submit` (fail-closed, izvan opsega ⇒ DENY).
3. **`mandate_id` u trace zapisima** — `PraxisEventRecord`/`ApprovalReceiptRecord`/`RuntimeStatusTransition`/
   `MemoryGovernanceRecord`/`BudgetDecisionRecord` ga danas NEMAJU.
4. **Delegacijski prozori** (Constitution) — strukturirani, s citiranjem po autonomnoj akciji, violation → G0.
5. **AurelEU dispečer** — role-fluid persona switch (eksplicitna trace-ana tranzicija) UNUTAR jedne vrata.
6. **DN dopune:** challenger pass, anti-stagnation tripwire, `aurel panic` (postojeći σ/MergeGate se samo spoje).
7. **AUREL_CRO surface** kao dom AurelEU-a (read-modeli + React).

**Zaključak:** identitet, policy_cards i dual_kernel su zreli ali **nespojeni kao orkestrator**. F6 = AurelEU
kao tanki resolucijsko-enforcement sloj koji spaja personu (compiler) + mandat (novi objekt + gate) +
delegaciju (operator_contract placeholderi) + DN (dual_kernel) — sve iza jedne vrata.

---

## 2. Arhitektonska kičma: AurelEU je sloj UNUTAR jedne vrata

AurelEU nije novi izvršni put — on je **resolucijsko-enforcement sloj** koji se ubacuje u dvije postojeće
točke, bez drugog državnog kanala:

- **Resolucija (ulaz):** u `proposal_dispatcher._dispatch_converse/_dispatch_act`, prije `ConversationEngine`/
  `runtime.submit`: `(role, mandate_id, context)` → `resolve_persona()` (mode/persona → `identity_prompt_
  compiler` → kompajlirani system prompt) + `resolve_mandate()` (`mandate_id` → `Mandate` objekt). Persona
  switch = **eksplicitna trace-ana tranzicija** (`persona_switch` event).
- **Enforcement (izvršenje):** u `runtime.submit` između policy-resolvera (`:307`) i approvala (`:309`):
  `_evaluate_mandate_scope_check(cmd, card)` — fail-closed. Mandat pooštrava `card.authority` (strictest-wins
  nad svojim policy_cards + scope: paths/tools/risk/budget/memory-zone). Izvan opsega ⇒ `MandateCheckRecord`
  + BLOCKED, ništa se ne izvrši.

**Master flag:** `AUREL_AURELEU` (dispečer se ne konstruira kad je OFF ⇒ pada na F5 "jedna default persona",
byte-identično). Pod-flagovi: `AUREL_MANDATE` (mandat+gate), `AUREL_CONSTITUTION` (delegacije), `AUREL_DN`
(challenger/tripwire/panic), reuse `AUREL_DUAL_KERNEL` (σ/merge). Svi default OFF.

**Zakon P1.4 se ne krši:** persona ostaje izraz (ne dodjeljuje ovlast); mandat je ovlast; kernel immutables
(`self_escalation_allowed=false`, `operator_final_authority=true`) su konstitucijski pod i F6 ih ne dira.

---

## 3. Per-slajs dispatch specifikacije

> Legenda: **Files** = novo / izmijenjeno. **Flag** default OFF. **Seal** = pytest fajl. **NC** = no-collapse.

### F6.0 — Mandate objekt + registry (flag `AUREL_MANDATE`)
- **Files:** novo `mandate/mandate.py` (`Mandate` frozen: `mandate_id`, `version`, `persona_ref`,
  `policy_card_ids: tuple`, `memory_zone_rules: dict`, `authority_overrides: Optional[AuthorityScope]`,
  `scope: MandateScope{repos, paths, client_id, budget}`, `expires_at`; **nekonstruktibilan bez scope-a**;
  `content_hash` = sha256 kanonskog JSON-a), `mandate/registry.py` (`MandateRegistry.from_mandates`,
  `resolve(mandate_id) → Mandate`, reuse `PolicyCardRegistry` za policy snop), `mandate/default.py`
  (jedan default mandat = trenutno F5 ponašanje, da off-put ostane isti).
- **NC:** mandat je **verzioniran + hashiran** (isti sadržaj ⇒ isti hash); `mandate_id` se resolvira u pravi
  objekt; nekonstruktibilan bez scope-a (no-overclaim); registry deterministički sortiran; policy snop je
  **referenca na postojeći `PolicyCardRegistry`**, ne nova kopija.
- **Seal:** `test_p6f6_0_mandate.py` — mandat hashiran/verzioniran; `resolve("default")` vraća default;
  nepoznat `mandate_id` ⇒ fail-closed; scope obavezan.
- **Dispatch prompt:** _"Implementiraj F6.0: `mandate/mandate.py` (`Mandate` frozen, versioned+hashed,
  scope obavezan, authority_overrides opcionalan, policy_card_ids referenca), `mandate/registry.py`
  (resolve iz mandate_id, reuse PolicyCardRegistry), default mandat. Flag `AUREL_MANDATE`. Seal
  `test_p6f6_0_mandate.py`."_

### F6.1 — `mandate_id` propagacija u trace (flag `AUREL_MANDATE`)
- **Files:** edit `core_types.py` — dodaj `mandate_id: str = ""` (additive, default "") na `PraxisEventRecord`
  (`:662–706`), `ApprovalReceiptRecord` (`:590–658`), `RuntimeStatusTransitionRecord` (`:329–396`),
  `MemoryGovernanceRecord` (`:459–531`), `BudgetDecisionRecord` (`:400–455`) + njihove `payload_hash`/replay
  yield (`trace.py`); edit `front_server/conversation.py:229–237` (`_record` prosljeđuje `turn.mandate_id`).
- **NC:** dodavanje polja je **additive** (default "" ⇒ off-put byte-identičan, postojeći hash stabilan kad je
  prazno — provjeri da payload_hash ne mijenja bytes za `mandate_id=""`); `mandate_id` preživi replay; svaki
  mandat-relevantan zapis ga nosi.
- **Seal:** `test_p6f6_1_mandate_trace.py` — `mandate_id` u PraxisEvent/Approval/StatusTransition; replay ga
  vraća; prazan default ⇒ postojeći seali zeleni (no-collapse).
- **Dispatch prompt:** _"Implementiraj F6.1: additive `mandate_id: str=''` na PraxisEventRecord/
  ApprovalReceiptRecord/RuntimeStatusTransitionRecord/MemoryGovernanceRecord/BudgetDecisionRecord (+replay/
  payload_hash), conversation `_record` prosljeđuje turn.mandate_id. Prazan default = byte-identičan.
  Seal `test_p6f6_1_mandate_trace.py`."_

### F6.2 — Mandate scope-enforcement gate (flag `AUREL_MANDATE`)
- **Files:** edit `core_types.py` (`AgentCard.mandate_id: str = ""` additive, ili binding map u
  `mandate/binding.py`), novo `mandate/enforcement.py` (`evaluate_mandate_scope_check(cmd, card, mandate) →
  MandateCheckResult{should_block, reason}` — strictest-wins nad mandate.policy_cards + scope check:
  write_path ⊆ mandate.scope.paths, tool ∈ dopušteni, risk ≤ mandate ceiling, budget ≤ mandate.budget,
  memory-zone dopuštena), edit `runtime.py` (novi `_evaluate_mandate_scope_check` gate **između :307 i :309**,
  fail-closed), novo `MandateCheckRecord` (`core_types.py`, mirror `SandboxViolationRecord`).
- **NC:** akcija **izvan mandata** ⇒ DENY (fail-closed) prije approvala/sandboxa/budžeta; mandat **pooštrava**,
  nikad ne proširuje `card.authority`; enforcement samo na G0–G3 (ENFORCE_FAIL_CLOSED) — na G4/G5 advisory;
  flag OFF ⇒ gate se ne evaluira (byte-identično); `MandateCheckRecord` nosi `mandate_id`.
- **Seal:** `test_p6f6_2_mandate_enforcement.py` — write izvan `scope.paths` ⇒ blocked; tool izvan snopa ⇒
  blocked; u opsegu ⇒ prolazi; mandat ne može proširiti ovlast preko card.authority; block record ima
  mandate_id; flag-off byte-identičan.
- **Dispatch prompt:** _"Implementiraj F6.2: `AgentCard.mandate_id` (additive), `mandate/enforcement.py`
  (scope+strictest-wins check), `_evaluate_mandate_scope_check` gate u runtime.submit između :307 i :309
  (fail-closed, samo G0–G3), `MandateCheckRecord`. Mandat pooštrava a ne proširuje. Seal
  `test_p6f6_2_mandate_enforcement.py`."_

### F6.3 — Constitution: delegacijski prozori (flag `AUREL_CONSTITUTION`)
- **Files:** novo `constitution/delegation.py` (`DelegationWindow` frozen: `delegation_id`, `scope`,
  `autonomy_ceiling: AutonomyLevel` (A0–A6), `valid_from`/`valid_until`, `consent_ref` → reuse
  `operator_consent`; `is_active(now)`, `covers(action)`), novo `constitution/contract.py` (puni
  `operator_contract` placeholdere `delegation_grant_ref`/`autonomy_session_ref`), projekcija delegacija iz
  tracea. Reuse `autonomy_scale_engine` (A0–A7).
- **NC:** svaka **autonomna** akcija (bez operatera u petlji) mora **citirati** aktivnu delegaciju; izvan
  prozora/isteklo ⇒ **fail-closed** (tretira se kao denied) + **pad na G0** + notification zapis; delegacija je
  governed record (ne efemerna); ne može podići autonomiju iznad kernel immutablea (self-escalation ostaje A7).
- **Seal:** `test_p6f6_3_delegation.py` — autonomna akcija bez citirane delegacije ⇒ blocked; izvan prozora ⇒
  G0 + notification; istekla delegacija fail-closed; delegacija ne nadjačava kernel self-escalation zabranu.
- **Dispatch prompt:** _"Implementiraj F6.3: `DelegationWindow` (scope, autonomy_ceiling A0–A6, valid_from/until,
  consent_ref), puni operator_contract delegation placeholdere, projekcija iz tracea. Autonomna akcija citira
  delegaciju; izvan prozora ⇒ G0 + notification (fail-closed). Reuse autonomy_scale_engine. Seal
  `test_p6f6_3_delegation.py`."_

### F6.4 — AurelEU dispečer: role-fluid persona switch (flag `AUREL_AURELEU`)
- **Files:** novo `front_server/aureleu.py` (`AurelEUDispatcher`: `resolve_persona(role, mandate) → mode/persona
  → identity_prompt_compiler.compile_identity_prompt_context() → system_prompt`; `switch_persona()` = eksplicitna
  trace-ana `persona_switch` tranzicija; drži trenutnu personu po `room_id`), edit `conversation.py`
  (`ConversationEngine` prima **kompajlirani** system prompt umjesto statičnog `CHAT_SYSTEM`), edit
  `proposal_dispatcher.py:56–74` (`_dispatch_converse` ruta kroz `AurelEUDispatcher` kad je flag ON, inače F5
  default persona).
- **NC:** persona switch = **eksplicitna, trace-ana** tranzicija (ne tiha); kompajlirani prompt je hash-bound
  (reuse `IdentityPromptContext.context_hash`); persona **ne dodjeljuje ovlast** (ovlast je mandat, F6.2); flag
  OFF ⇒ statični `CHAT_SYSTEM` (F5, byte-identično); **flipa F5 seam** `claims_aureleu_dispatcher_live` False→True.
- **Seal:** `test_p6f6_4_aureleu_persona.py` — `(role,mandate)` → kompajlirani persona prompt; switch je traceana
  tranzicija; persona ne mijenja authority; flag-off ⇒ CHAT_SYSTEM identičan; contradiction u compileru ⇒ fail-closed.
- **Dispatch prompt:** _"Implementiraj F6.4: `AurelEUDispatcher.resolve_persona` (role+mandate → compiler →
  system prompt), persona switch = traceana tranzicija, ConversationEngine prima kompajlirani prompt,
  proposal_dispatcher ruta kroz AurelEU kad flag ON. Persona ≠ ovlast. Flipa claims_aureleu_dispatcher_live.
  Seal `test_p6f6_4_aureleu_persona.py`."_

### F6.5 — Constitution enforcement wiring (delegacija ↔ dispatch) (flag `AUREL_AURELEU`)
- **Files:** edit `front_server/aureleu.py` (prije dispečiranja pod-agenta pod mandatom, provjeri
  `DelegationWindow.covers(action)` i `mandate` scope; violation ⇒ G0 + notification), edit `mandate/
  enforcement.py` (poveži delegaciju u gate). Veže F6.2 + F6.3 + F6.4.
- **NC:** dispečiranje pod-agenta traži i **mandat** (ovlast) i **citiranu delegaciju** (autonomija); bilo koji
  izostanak ⇒ fail-closed; sve trace-ano s `mandate_id` + `delegation_id`.
- **Seal:** `test_p6f6_5_constitution_wiring.py` — dispatch pod mandatom+delegacijom prolazi; bez delegacije ⇒
  G0; izvan mandata ⇒ DENY; lanac vidljiv u traceu.
- **Dispatch prompt:** _"Implementiraj F6.5: AurelEU prije dispečiranja provjeri DelegationWindow.covers +
  mandate scope; violation ⇒ G0 + notification. Veže F6.2/6.3/6.4. Seal `test_p6f6_5_constitution_wiring.py`."_

### F6.6 — DN (a): graduated autonomy + ponderirani merge verdikt (reuse flag `AUREL_DUAL_KERNEL`)
- **Files:** edit `front_server/aureleu.py` + `front_server/hq_command.py` (surfacea `SigmaGovernor`
  track-record → graduated autonomy i `MergeGate` ponderirani verdikt kroz AurelEU; **verifier veto apsolutan**);
  read-model `GET /read/aureleu/dn` (status σ/merge). Većinom **wiring postojećeg dual_kernela**.
- **NC:** verifier veto je **apsolutan** (nijedan ponder ga ne nadjačava); σ track-record gejtira autonomiju
  (gradualno); ne mijenja se default kad je `AUREL_DUAL_KERNEL` OFF.
- **Seal:** `test_p6f6_6_dn_autonomy_merge.py` — verifier veto blokira unatoč pozitivnom ponderu; σ track-record
  diže/spušta ceiling; merge verdikt deterministički.
- **Dispatch prompt:** _"Implementiraj F6.6: surfacea SigmaGovernor graduated autonomy + MergeGate ponderirani
  verdikt (verifier veto apsolutan) kroz AurelEU + HQ.Command; /read/aureleu/dn. Reuse dual_kernel. Seal
  `test_p6f6_6_dn_autonomy_merge.py`."_

### F6.7 — DN (b): challenger pass + anti-stagnation tripwire + `aurel panic` (flag `AUREL_DN`)
- **Files:** novo `dn/challenger.py` (drugi-mišljenje prolaz na rizičnim prijedlozima — jeftiniji/različiti
  profil kroz F2 router; surface dissent), `dn/tripwire.py` (anti-stagnation: detektira petlju/nula-napredak iz
  tracea ⇒ eskalira), `dn/panic.py` (`aurel panic` → immediate halt na G0), CLI `aurel aureleu panic`.
- **NC:** challenger je **advisory** (ne izvršava, samo iznosi dissent u prijedlog); tripwire fail-closed
  (eskalira, ne nastavlja tiho); `panic` je **kill-switch** — spušta na G0/halt, governed record, nikad tihi.
- **Seal:** `test_p6f6_7_dn_challenger_panic.py` — challenger iznosi dissent bez izvršenja; tripwire okida na
  stagnaciji; panic zaustavlja na G0 (traceano).
- **Dispatch prompt:** _"Implementiraj F6.7: `dn/challenger.py` (advisory drugi-mišljenje kroz F2),
  `dn/tripwire.py` (anti-stagnation iz tracea), `dn/panic.py` + `aurel aureleu panic` (halt na G0). Sve
  fail-closed/advisory. Seal `test_p6f6_7_dn_challenger_panic.py`."_

### F6.8 — Dvo-personalno planiranje → Board generator opcija (reuse flag `AUREL_FRONT_BOARD`)
- **Files:** edit `front_server/board.py` (AurelEU generira 2 persona-različite opcije za poslovnu odluku →
  `BoardOption` zapisi; svaka `convert_to_proposal` kroz jedna vrata), edit `aureleu.py` (dvo-persona generator).
- **NC:** opcije su **generator**, ne izvršenje; svaka opcija ide kroz istu jednu vrata (F5.6); dvije persone su
  eksplicitne (npr. risk-first vs. opportunity-first), traceane.
- **Seal:** `test_p6f6_8_two_persona_board.py` — dvije persona-opcije zabilježene; convert-to-proposal po opciji
  reducira na runtime.submit; nema drugog puta.
- **Dispatch prompt:** _"Implementiraj F6.8: AurelEU dvo-personalni generator opcija → BoardOption zapisi,
  convert-to-proposal po opciji kroz F5.6 vrata. Generator, ne izvršenje. Seal `test_p6f6_8_two_persona_board.py`."_

### F6.9 — AUREL_CRO surface (dom AurelEU) + read-modeli + React (flag `AUREL_AURELEU`)
- **Files:** novo `front_server/aureleu_read_model.py` (`AurelEUReadModel`: aktivni mandat + persona/role +
  delegacijski prozori + DN status; sve žive trace projekcije), edit `read_models.py` (`/read/aureleu`), novo
  `web/shell/src/components/front/AurelEUPanel.tsx` + wire u `FrontSurface` (`aurel_cro`), `frontClient.ts`
  (aureleu read).
- **NC:** čista projekcija (zero-write); jedna vrata očuvana (nema direktnog izvršenja iz AUREL_CRO); truth
  labeli propagiraju; server-OFF ⇒ fixture mode (F5.8 disciplina).
- **Seal:** `test_p6f6_9_aureleu_surface.py` (+vitest) — `/read/aureleu` živ; UI čin ⇒ proposal; nula direktnih poziva.
- **Dispatch prompt:** _"Implementiraj F6.9: `AurelEUReadModel` (aktivni mandat/persona/delegacije/DN),
  `/read/aureleu`, `AurelEUPanel.tsx` na AUREL_CRO, frontClient wire. Zero-write, jedna vrata. Seal
  `test_p6f6_9_aureleu_surface.py` + vitest."_

### F6.10 — Derived exit seal + CLI + merge (flag n/a, seal je izveden)
- **Files:** novo `f6_seal.py` (**derived**: svaki F6.0→F6.9 slajs importabilan AND report prisutan; **flipa** F5
  UNAVAILABLE seamove `aureleu_role_fluid_dispatcher` i mandate na SEALED; novi UNAVAILABLE registry: multi-
  jurisdikcijski suvereni (SCI-FI), zero-knowledge federacija (SCI-FI), non-repudiation kripto-ledger (P1.8/P2.2),
  puni approval workbench (F7); overclaim guardovi), `f6_projection.py` (north-star run), CLI `aurel aureleu
  seal/status/panic`.
- **NC:** seal je **izveden**, nikad self-assigned; missing modul/report ⇒ BLOCKED; F5 flipovi dokazani (mandat
  enforcement + role-fluid live); odgođeno ostaje eksplicitno.
- **Seal:** `test_p6f6_10_f6_exit_seal.py` — north-star §7 end-to-end; SEALED kad su svi prisutni; BLOCKED na
  missing; F5 seamovi flipani; SCI-FI parkirano.
- **Dispatch prompt:** _"Implementiraj F6.10: `f6_seal.py` derived (svi slajsevi + reporti; flipa F5
  aureleu/mandate seamove na SEALED; novi UNAVAILABLE za SCI-FI/ledger/workbench), `f6_projection.py`,
  `aurel aureleu seal/status/panic`. Seal `test_p6f6_10_f6_exit_seal.py` vozi §7."_

---

## 4. Preporučeni redoslijed (walking skeleton prvo)

1. **Mandat okostnica:** F6.0 → F6.1 → F6.2 → dovoljno za: mandat resolvira, `mandate_id` u traceu, izvan
   opsega DENY. Najmanji rez koji dokazuje "mandat enforcean, fail-closed". Ovo zatvara N5 seam.
2. **AurelEU jezgra:** F6.4 (persona switch) → F6.3 (delegacije) → F6.5 (wiring). Role-fluid + Constitution žive.
3. **DN sloj:** F6.6 (reuse dual_kernel) → F6.7 (challenger/tripwire/panic).
4. **Front:** F6.8 (Board dvo-persona) → F6.9 (AUREL_CRO surface + React).
5. **Pečat:** F6.10 derived exit seal + report; puni suite; merge `feat/f6-aureleu` → master.

Kritičan put je F6.0→F6.2 (mandat enforcement) i F6.4 (AurelEU). Sve ostalo visi o njima.

---

## 5. Cross-cutting invarijante (svaki slajs mora držati)

- **Identity ≠ authority.** Persona/mode = izraz (P1.4 zakon); ovlast je **mandat** enforcean u `runtime.submit`.
  Persona nikad ne dodjeljuje pravo na alat/put.
- **Mandat putuje s agentom i enforcea se fail-closed.** Pooštrava, nikad ne proširuje `card.authority`. Izvan
  opsega ⇒ DENY prije izvršenja. Enforcement na G0–G3.
- **Constitutional floor je nedodirljiv.** Kernel immutables (`self_escalation_allowed=false`,
  `operator_final_authority=true`) ostaju; nijedan mandat/delegacija/persona ih ne podiže (self-escalation = A7).
- **Jedna vrata.** AurelEU živi UNUTAR dispečera; nema drugog izvršnog puta. Autonomna akcija citira delegaciju;
  violation ⇒ G0 + notification.
- **Trace = jedini izvor istine.** `mandate_id` + `delegation_id` + `persona_switch` su governed zapisi; svaki
  mandat-relevantan zapis nosi `mandate_id`.
- **Additive-behind-flags.** `AUREL_AURELEU`/`_MANDATE`/`_CONSTITUTION`/`_DN` default OFF; off-put byte-identičan
  (pada na F5 jedna-persona). Dokaz: flag-off test + puni suite.
- **No-overclaim (strukturno).** `Mandate` nekonstruktibilan bez scope-a; challenger je advisory; verifier veto
  apsolutan; overclaim guardovi za odgođeno hard-wired False.

---

## 6. Odgođeni seamovi / UNAVAILABLE registry (F6)

| Seam | Status u F6 | Vlasnik / kada |
|---|---|---|
| AurelEU role-fluid dispatcher | **ŽIVO** (flipa F5 seam) | F6.4 |
| Mandat rezolucija + enforcement (N5) | **ŽIVO** (flipa F5 seam) | F6.0–F6.2 |
| Multi-jurisdikcijski suvereni (AurelGer/AurelUS) | UNAVAILABLE (SCI-FI, parkirano) | — |
| Zero-knowledge federacija suvereni | UNAVAILABLE (SCI-FI) | — |
| Non-repudiation kripto-ledger (potpisi) | UNAVAILABLE | P1.8 / P2.2 |
| Puni approval workbench UI | PARTIAL (F5.2 inbox live; workbench refinement) | F7 |
| Watchtower alert feed | UNAVAILABLE (F5.5 seam) | F7 |
| Library time-travel | UNAVAILABLE | F8 |
| WorkOPS Code / AI-editor | UNAVAILABLE | poslije F7 |
| wss/TLS remote transport | UNAVAILABLE | Tauri-Rust |

---

## 7. F6 exit seal — north-star scenarij (F6.10 test)

Automatizirani end-to-end koji je definicija uspjeha F6:

1. Operator u **Signalu** pod mandatom `M = {klijent X, repo Y, paths Y/**, budget Z, EU-data zone rules}` zada
   poslovni intent (`SignalMessage` s `mandate_id=M`).
2. **AurelEU** resolvira: `role` → persona/mode → `identity_prompt_compiler` → system prompt (traceana
   `persona_switch` tranzicija); `mandate_id` → `Mandate` objekt.
3. AurelEU citira aktivnu **delegaciju** (autonomy ceiling A4); dispečira pod-agenta pod mandatom M.
4. Pod-agent pokuša write **izvan** `repo Y` ⇒ `_evaluate_mandate_scope_check` **DENY** (`MandateCheckRecord`,
   ništa se ne izvrši).
5. Pod-agent write **unutar** `Y/**` ⇒ prolazi policy → approval u **HQ.Command** → operator approve → izvršenje.
6. **Svaki** trace zapis (praxis/approval/status/budget/memory) nosi `mandate_id=M`.
7. Board prikaže **dvije persona-opcije** za odluku; `aurel panic` bi u bilo kojem trenu spustio na G0.
8. Cijeli lanac **replayabilan**; nula direktnih poziva iz UI-ja (jedna vrata); pod `standard` (G2), bez ključa
   u artefaktima (F2 redakcija); overclaim guardovi za SCI-FI/ledger = False.

---

## 8. Dubinska razrada — Mandate objekt + enforcement (killer modul)

**Postojeći temelj (grounded):** `policy_cards/` je zreo — `PolicyCard` (`models.py:189–212`),
`PolicyCardRegistry` (`registry.py:93–190`, `canonical_hash`), `resolver.py` (Custos shadow-mode),
`conflict_algebra.py` (strictest-wins). `AuthorityScope`/`AgentCard` (`core_types.py:143–187`). `runtime.submit`
policy resolver influence (`runtime.py:292–307`). **Fali samo omotač koji ovo veže u mandat + gate.**

**`Mandate` (frozen, `mandate/mandate.py`):** `{mandate_id, version, persona_ref, policy_card_ids: tuple,
memory_zone_rules: dict, authority_overrides: Optional[AuthorityScope], scope: MandateScope{repos, paths,
client_id, budget}, expires_at}`. `__post_init__` odbija prazan scope (no-overclaim). `content_hash` =
sha256 kanonskog JSON-a (verzioniranje). Policy snop je **referenca** (`policy_card_ids`) na postojeći
`PolicyCardRegistry`, ne kopija.

**Enforcement (`mandate/enforcement.py`, gate u `runtime.py` između :307 i :309):**
`evaluate_mandate_scope_check(cmd, card, mandate)`:
1. Ako `card.mandate_id == ""` ili flag OFF ⇒ passthrough (byte-identično).
2. Resolvira `mandate` iz `card.mandate_id`; istekao ⇒ **DENY** (fail-closed).
3. **Scope check (strictest-wins, pooštrava):** `cmd.target write_path ⊆ mandate.scope.paths`;
   `cmd.tool` dopušten mandatom; `cmd.declared_risk ≤ mandate ceiling`; budget ≤ `mandate.scope.budget`;
   memory-zone iz `policy_cards/memory_write.py` dopuštena `mandate.memory_zone_rules`.
4. Aggregira `mandate.policy_card_ids` kroz postojeći resolver (conflict_algebra strictest-wins).
5. DENY/CONFLICT ⇒ `MandateCheckResult(should_block=True, reason, mandate_id)` ⇒ `MandateCheckRecord` + BLOCKED.
6. **Mandat NIKAD ne proširuje** `card.authority` — samo presijeca (min). Enforcement samo G0–G3.

**Zašto tu:** policy engine je već validirao `card.authority` (baseline); mandat dodaje **dodatna** ograničenja
(persona snop + memory scope + klijent/repo/budget) prije HITL-a, pa approval može referencirati mandat.

**Seal proširenja (`test_p6f6_2_mandate_enforcement.py`):** write izvan scope ⇒ blocked; tool izvan snopa ⇒
blocked; risk iznad ceiling ⇒ blocked; u opsegu ⇒ prolazi; pokušaj proširenja ovlasti preko card.authority ⇒
i dalje presječeno na card baseline; `MandateCheckRecord` nosi mandate_id; flag-off byte-identičan.

---

## 9. Dubinska razrada — AurelEU role-fluid persona switch

**Postojeći temelj (grounded):** `identity_prompt_compiler.compile_identity_prompt_context()`
(`prompts/identity_context_compiler.py`) **već** kompajlira kernel+persona+operator_contract+mode u
hash-bound `IdentityPromptContext` (`prompts/identity_context.py:30–44`) s cross-layer contradiction detekcijom
i dominance pravilima (kernel > contract > persona > mode). 7 modova (`communication_modes.py:114–122`). Danas
`ConversationEngine` koristi **statični** `CHAT_SYSTEM` (`conversation.py:37–41`) za sve — ignorira `role`.

**`AurelEUDispatcher` (`front_server/aureleu.py`):**
- `resolve_persona(role, mandate, room_id) → system_prompt`: mapira `(role, mandate.persona_ref)` na
  `communication_mode` + persona manifest → poziva `compile_identity_prompt_context()` → vraća kompajlirani,
  hash-bound system prompt (reuse `IdentityPromptContext.context_hash`).
- `switch_persona(room_id, new_role)`: ako se persona mijenja, emitira **eksplicitni** `persona_switch` praxis
  event (from_persona → to_persona, context_hash) — nikad tiha tranzicija.
- Drži trenutnu personu po `room_id` (operational, ne store — trace je istina).

**Wiring:** `proposal_dispatcher._dispatch_converse` (`:56–74`) kad je `AUREL_AURELEU` ON: prije
`ConversationEngine.respond`, `dispatcher.resolve_persona(...)` → proslijedi kompajlirani prompt u engine
(`ConversationEngine` dobiva `system` parametar per-turn umjesto konstruktorskog `CHAT_SYSTEM`). Flag OFF ⇒
statični `CHAT_SYSTEM` (F5, byte-identično).

**No-overclaim / P1.4 zakon:** persona **ne dodjeljuje ovlast** — ovlast je mandat (F6.2). Compiler već blokira
kontradikcije (npr. persona koja tvrdi da može podići autonomiju ⇒ CTR fail). Kernel immutables ostaju pod.
Flipa F5 `claims_aureleu_dispatcher_live` False→True tek kad switch živi i traceano radi.

**Seal proširenja (`test_p6f6_4_aureleu_persona.py`):** `(role, mandate)` → kompajlirani persona prompt
(različit od CHAT_SYSTEM); persona switch = traceani `persona_switch` event; persona ne mijenja `card.authority`;
compiler contradiction ⇒ fail-closed; flag-off ⇒ CHAT_SYSTEM byte-identičan.

---

**One-line pickup:** _"Čitaj `AUREL_PLAN_07_F6_AURELEU_DISPATCH.md`; kreni F6.0 (Mandate objekt) na grani
`feat/f6-aureleu` per §3, walking-skeleton redoslijedom §4 (mandat okostnica F6.0→F6.2 zatvara N5); killer
razrade u §8 (mandate enforcement) i §9 (AurelEU persona switch)."_
