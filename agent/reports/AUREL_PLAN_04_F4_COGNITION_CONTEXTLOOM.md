# AUREL PLAN 04 — F4: Kognicija (interaktivni loop + ContextLoom)

_Cut: 2026-07-09, branch `feat/f4-cognition-contextloom` (from the F3 tip). Follows F3 (external executors)._

## 0. Što F4 je (iz `AUREL_PLAN_02` §4.F4)

> ReAct loop (`entity_loop.py`) kroz `runtime.submit`; router po namjeni; cassette by default.
> **ContextLoom** = governed sastavljanje konteksta (provenance + taint + budget-aware kompresija + hash
> u trace). Front veza: Signalovi `context_refs` (Library hashevi uz svaku poruku) su točno ContextLoom
> reference — ista stvar, jedan mehanizam.

Dvije komponente:
- **ContextLoom** — governed sastavljanje konteksta. Nadograđuje današnji `memory.assemble_context`
  (plain string concat, bez porijekla/tainta/budžeta/hash-a) u: **provenance** (svaki item nosi izvor),
  **taint** (reuse F3.0 — vanjski itemi su DATA-only, instruction-ineligible), **budget-aware kompresija**
  (deterministički stane pod token-budžet, ništa se tiho ne gubi), **hash u trace** (`context_ref` = Signal hash).
- **Interaktivni ReAct loop** — nadograđuje postojeći `AgenticEntity.plan()/run()` (već ide kroz
  `runtime.submit`, router po namjeni, reasoning scheduler) u eksplicitni observe→think→act loop koji
  svaki krug sastavlja kontekst preko ContextLooma; cassette by default.

**F4 je i dom smjera B (MCP client bridge)** — kad Aurel zove VAN, tainted output vanjskih MCP alata
ima disciplinirani slivnik: ContextLoom (DATA-only, provenance, budget). (Odgođeno iz F3 po odluci operatora.)

## 1. Invarijante (NC)

1. **Additive & flag-gated.** Sve iza `AUREL_CONTEXTLOOM` / `AUREL_ENTITY_LOOP`; OFF ⇒ `assemble_context` i
   postojeći `AgenticEntity` **byte-identični**.
2. **Provenance forbids instruction (reuse F3.0).** Vanjski context item (`source_kind ∈ EXTERNAL_ORIGIN_KINDS`)
   je u bundleu **DATA-only** i pri renderu jasno ograđen kao untrusted — nikad instrukcija.
3. **No silent loss.** Budget-kompresija bilježi što je izbačeno/skraćeno; nikad tiha tišina.
4. **Deterministic & hashed.** Sastavljanje je determinističko (stable sort, bez RNG/`hash()`); bundle nosi
   `context_ref` (sadržajni hash) za trace/replay.
5. **Cassette by default.** Loop determinističan pod kasetom; živi model samo eksplicitno.
6. **Governance layered on, never around.** Loop ide isključivo kroz `runtime.submit` (kao i danas).

## 2. Dekompozicija (sealed slice-ovi)

| Slice | Naslov | Novi moduli | NC fokus | Seal |
|---|---|---|---|---|
| **F4.0** | ContextLoom foundation | `context_loom/{context_item,loom}.py` | NC-2 taint DATA-only, NC-3 no-silent-loss (drop), NC-4 hash | `test_p6f4_0_context_loom.py` |
| **F4.1** | Budget-aware kompresija | `context_loom/compression.py` | NC-3 deterministička kompresija/skraćivanje s evidencijom | `test_p6f4_1_context_compression.py` |
| **F4.2** | Trace binding — `context_ref` u trace | `context_loom/context_trace.py` | NC-4 svaki assemble → auditabilan/replayabilan event | `test_p6f4_2_context_trace.py` |
| **F4.3** | Interaktivni ReAct loop | `entity_loom_loop.py` (ili proširenje `entity.py`) | NC-1 byte-identical OFF, NC-6 kroz submit, NC-5 cassette | `test_p6f4_3_entity_loop.py` |
| **F4.4** | Projection + CLI + F4 exit seal | `f4_seal.py`, `f4_projection.py`, `cli_modules/f4_commands.py` | derived seal, read-only | `test_p6f4_4_f4_exit_seal.py` |

F4.0 (ContextLoom) nema ovisnosti osim F3.0 taint — ide prva.

## 3. Flagovi

- `AUREL_CONTEXTLOOM` — F4.0 definira; load-bearing kad loop/assemble počne rutati kroz Loom.
- `AUREL_ENTITY_LOOP` — F4.3 definira; interaktivni loop opt-in.

## 4. Reuse (ne graditi nanovo)

- **F3.0 `external_ingress`** — `SourceKind`/`TaintLabel`/`make_tainted`/`SanitizationCrossing` (provenance+taint).
- `memory.assemble_context` / `hybrid_retrieve` (A6) — izvor memorijskih context itema.
- `budget.py` — token/estimate računica; `estimated_tokens` cap.
- `AgenticEntity.plan()/run()` + `reasoning_scheduler` + `PlanValidator` — postojeći kognitivni put.
- `trace` — `context_ref` event (kao P5 evidence).

## 5. Status

- [ ] **F4.0** — ContextLoom foundation (ovaj slice, u tijeku).
- [ ] F4.1 … F4.4.
