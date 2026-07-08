# AUREL F2 — Providers, Secrets, Redaction, Model-Swap Drill

**Status:** COMPLETE on branch `feat/f2-continue` (cut from `79e95c1`). **Not merged to master, not pushed.**
**Date:** 2026-07-08
**Author:** CODEOPS (recovery/continuation session)

F2 gives Aurel real, swappable model providers with an honest secret boundary:
thin OpenAI-compatible adapters (Qwen, Kimi), live model profiles with honest-fail
failover, a layered `SecretStore`, an operator CLI, central secret redaction proven
by a per-provider sentinel, and a model-swap behavioral drill.

## Branch lineage

F2 (a)–(d) were implemented and committed on `feat/f2-providers-secrets`. A follow-on
session then WEDGED implementing the (e) CLI seal — a `getpass`/stdin read blocked
forever on an interactive terminal. That worktree was left dirty. Per instruction,
(e)–(g) were finished on a **fresh branch `feat/f2-continue` cut at `79e95c1`** (the
tip of the (a)–(d) work); the original branch's committed history was left untouched.

```
b003eb6  merge: F0 honesty + F1 enforcement gradation into master        (base)
8cb613e  feat(providers): F2 Qwen adapter (DashScope, OpenAI-compat)      (a)
e588058  feat(providers): F2 Kimi adapter (Moonshot, OpenAI-compat)       (b)
613fa64  feat(models):    F2 live model profiles + honest-fail failover   (c)
79e95c1  feat(secrets):   F2 SecretStore (env→keyring→file-0600)           (d)   ← feat/f2-continue cut here
5eeec21  feat(cli):       F2 aurel secrets set/status                      (e)
ab26db2  feat(security):  F2 central secret redaction + sentinel seal      (f)
329708b  feat(drill):     F2 model-swap behavioral diff                   (g)   ← feat/f2-continue tip
```

## The getpass wedge — root cause + fix

**Root cause:** `getpass.getpass()` reads a passphrase with terminal echo disabled.
Under an interactive/non-mocked run (a manual `aurel secrets set qwen`, or a test that
calls `cmd_secrets_set` without stubbing `getpass`) it blocks on stdin indefinitely —
there is no prompt to answer in an automated context, so the process hangs forever.

**Fix / guardrail:** every test that touches `secrets set` MUST `monkeypatch.setattr(
"getpass.getpass", lambda prompt="": "<sentinel>")` so the no-echo read returns a fixed
value and never blocks. The unknown-provider path returns **before** reaching `getpass`
(the provider name is validated first), so it is hang-free by construction. All pytest
runs in this session were `timeout`-bounded (`timeout 60 .venv/bin/python -m pytest …`)
so a regression of this class fails fast instead of wedging. The (e) seal now passes in
~1.3 s.

## Deliverables

### (a) Qwen adapter — `model_providers/qwen_provider.py`  [8cb613e]
Thin OpenAI-compatible adapter for Alibaba DashScope (`qwen-max`, `qwen-plus`,
`qwen3-coder`). JSON-object response mode (DashScope lacks strict `json_schema`), env-only
key (`DASHSCOPE_API_KEY`), real token-usage extraction, typed errors — a deliberate clone
of `deepseek_provider.py` (the F2 pattern: OpenAI-compat providers differ only in constants).

### (b) Kimi adapter — `model_providers/kimi_provider.py`  [e588058]
Same thin pattern for Moonshot (`MOONSHOT_API_KEY`), OpenAI-compatible chat.

### (c) Live model profiles + honest-fail failover — `model_config.py`, `model_router.py`, `config/live/*`  [613fa64]
Live provider/model config; ranked failover down a profile's client list. A provider
refusal (missing key, HTTP failure) fails over to the next ranked link; the last link's
refusal is returned **honestly**. Silent mock fallback is refused in profiles that set
`AUREL_ALLOW_MOCK_FALLBACK=0` (an operator who explicitly chose mock still gets mock).

### (d) SecretStore — `secrets_store.py`  [79e95c1]
Per-provider key resolution/storage over an honest backend chain **env → OS keyring →
file-0600**. Keyring via native CLI (`secret-tool`/`security`); Windows keyring is HONESTLY
unavailable (no `cmdkey` read path) rather than faked. File backend is plaintext at
`chmod 0600` with an honest `file-0600` label — **no home-rolled crypto pretending to be
security**. `status()` exposes only a masked `sha256[:8]` fingerprint, never the value;
every resolved value is registered with the central redactor.

### (e) CLI — `aurel secrets set/status`  [5eeec21]
`cli_modules/secrets_commands.py` + parser wiring in `cli.py` + `aurel` console-script alias.
`secrets set <provider>` reads the key with `getpass` (no echo) and stores it via the
SecretStore chain, printing only backend + fingerprint. `secrets status` prints per-provider
presence + backend + masked fingerprint (+ deterministic `--json`), all through
`SecretRedactor` defensively. Unknown provider fails closed (rc=1) before any read.
**Seal `test_p6f2_secrets_cli.py` — 4 passed** (getpass MOCKED): set stores + masks; status
masks and never echoes the value; unknown provider rc=1; subcommands wired into the main parser.

### (f) Central redaction + sentinel seal  [ab26db2]
The redaction boundary already covered provider/router errors (`post_json` emits typed codes
that never carry the URL/headers/key; `ModelRouter` redacts failover errors). The **one gap**
was the model cassette, which persisted the raw completion verbatim — a key that ever leaked
into model output would land on disk. `ModelCassette.record()` now redacts **exact registered
secret values** before persisting, via a new `SecretRedactor.redact_known()` (exact-match only;
the heuristic `sk-`/high-entropy patterns would corrupt legitimate long token-like completions
and break replay determinism). **Seal `test_p6f2_redaction_sentinel.py` — 5 passed:** a UNIQUE
low-entropy sentinel per provider (only exact-match registry redaction can catch it) is injected
and every leak surface exercised — cassette file bytes, provider error, router failover error,
trace replay, log lines — and asserted to contain NO sentinel; a control token proves legitimate
content is preserved (no over-redaction).

### (g) Model Swap Drill — `aurel drill model-swap`  [329708b]
`model_swap_drill.py` + `cli_modules/drill_commands.py` + parser wiring. Replays an
operator-curated `DrillCorpus` (JSONL of `(system, user, baseline_response)` VERBATIM —
deliberately unlike `ModelCassette`, which hashes prompts so a run cassette never leaks
prompt content and thus cannot be replayed against a new provider) against a candidate model
profile and prints a **deterministic** behavioral diff: `same_behavior` / `divergent` /
`candidate_refused` per entry + aggregate counts. `classify_response` reduces a response to a
signature (plan/refusal/invalid + tool sequence + step count). Honest: a keyless candidate is
counted as `candidate_refused`, never a fabricated comparison; a missing/empty corpus fails
closed. **Seal `test_p6f2_model_swap_drill.py` — 6 passed:** corpus round-trip + dedup;
classify kinds; diff verdicts; byte-identical determinism; keyless-candidate honesty; CLI
end-to-end with fail-closed on missing corpus.

## Invariants held
- **Honest fail** — no silent mock in standard/hardened; keyless candidate → `candidate_refused`.
- **No fake crypto** — file backend is plaintext-0600, labeled honestly; keyring only when real.
- **Secrets never logged/traced** — proven by the per-provider sentinel across trace/cassette/logs/errors.
- **Thin OpenAI-compat adapters** — Qwen/Kimi differ from DeepSeek only in constants.
- **Deterministic where testable** — drill report is byte-identical for a fixed corpus + candidate.

## Validation (focused-first; full suite NOT run — deferred)
- **compileall + ruff + mypy** — clean on all touched files (`cli.py`, `secrets_commands.py`,
  `secrets.py`, `model_cassette.py`, `drill_commands.py`, `model_swap_drill.py`, and the three seals).
- **F2 seals:** (e) 4 passed · (f) 5 passed · (g) 6 passed.
- **Focused regression battery** — `test_model_providers_p12`, `test_model_config_p11`,
  `test_p6f2_providers`, `test_p6f2_models_live_failover`, `test_p6f2_secrets_store`, all F2 seals,
  and `spine/test_replay_cassette` (guards the cassette redaction change):
  **76 passed, 2 skipped** (skips are honest — providers needing real keys).

## Next
Merge `feat/f2-continue` → master when ready (F2 currently lives on its branch only).
