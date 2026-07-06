# AUREL-REPAIR-02 — M0 Sandbox Attestation Tamper-Detection

**Date:** 2026-07-06
**Task ID:** AUREL-REPAIR-02
**Type:** RCA repair (test-integrity / tamper-evidence coverage) — not a roadmap feature
**Risk tier:** HIGH (touches an M0 security-integrity invariant)
**Status:** DONE (target test green; focused validation green; full pytest seal UNVERIFIED — see §8)

---

## 1. Purpose

Close the gap flagged as REPAIR-01's next task: `test_attestation_tamper_breaks_chain`
failed on the clean tree, appearing to show that a forged sandbox attestation was
**not** detected by trace chain verification. The mission was to root-cause why
tampering wasn't caught and repair it so a modified attestation genuinely breaks
verification — without weakening any security/governance check and without gaming
the test.

## 2. RCA — how the investigation ran

1. **Reproduced** the failure on `HEAD = 3a7ea8d` (REPAIR-01):
   `assert not rep["ok"]` → `AssertionError: assert not True` — verification
   reported the tampered ledger as OK.
2. **Traced the verification path.** `PersistentTraceLedger.verify_persisted()` →
   `_verify_events()`. For each on-disk event it recomputes
   `expected = _entry_hash(event)` and compares it to the stored `entry_hash`.
   `_entry_hash(event) = sha(canonical_json(body))` over the **entire event body
   minus `entry_hash`** — which **includes the raw `payload`** (there is no
   separate trusted `payload_hash` field on disk; the whole payload is bound).
3. **Inspected the real on-disk event.** The persisted sandbox-attestation event
   embeds the full attestation under `payload`
   (`available`, `hard_isolated`, `backend`, `reason`, `probe`, `host`), covered by
   `_entry_hash`.
4. **Empirically tested genuine tampering** (recorded baseline → mutate one field →
   re-verify):

   | Mutation | `verify_persisted` result |
   |----------|---------------------------|
   | `available=True, hard_isolated=True` (the test's forge, **on this host**) | `ok=True` (not detected) |
   | `hard_isolated: True→False` | `ok=False` — "entry hash mismatch" |
   | `reason` changed | `ok=False` — "entry hash mismatch" |
   | `available: True→False` | `ok=False` — "entry hash mismatch" |

   Every **genuine** payload change is detected. Only the test's specific forge
   was undetected.

## 3. Root cause

**Not a verification hole — a host-dependent test.** The chain verification already
provides full tamper-evidence over the attestation payload (proven in §2). The test
recorded the **live** `probe_backend(SandboxMode.BUBBLEWRAP)` result and then
"forged a stronger claim" by setting `available=True, hard_isolated=True`.

- On the CI host it was written for, bwrap is **non-functional** → the probe records
  `available=False, hard_isolated=False`, so the forge is a real mutation → detected
  → test passes.
- On a host where **bwrap actually isolates** (this machine: `/usr/bin/bwrap`
  functional probe ok), the probe already records `available=True,
  hard_isolated=True`, so the forge re-asserts the values already on disk → the
  `payload` is unchanged → `entry_hash` is unchanged → verification **correctly**
  reports OK → `assert not rep["ok"]` fails.

The test proved nothing on capable hosts: its tamper was a no-op. The verification
code was sound the whole time.

## 4. Files changed

- `tests/test_m0_sandbox_attestation.py` — rewrote `test_attestation_tamper_breaks_chain`
  to record a **deterministic weak baseline** attestation
  (`available=False, hard_isolated=False`, `backend=bubblewrap`, real
  `host_fingerprint()`), independent of this host's live probe, then forge the
  stronger claim (`True/True`). This makes the tamper a genuine payload mutation on
  **every** host. Added two guardrails: a pre-tamper assertion that the recorded
  baseline really is weak on disk (`available is False`) so the test can never again
  silently regress to a no-op forge, and a post-verify assertion that the failure
  reason is specifically a chain/hash break (`"hash" in rep["reason"]`).

**No source/production file was changed.** The verification code already enforced
the invariant correctly; changing it was neither necessary nor correct (re-probing
or re-signing historical attestations would be scope creep and semantically wrong).

## 5. Fix — why this is honest, not gaming

- The security property under test — *a persisted attestation cannot be silently
  rewritten without breaking chain verification* — **genuinely holds** (§2 table).
- The change **strengthens** the test (real host-independent tamper + explicit
  detection-reason assertion + anti-regression baseline check); it does **not**
  weaken an assertion or assert something trivially true.
- No security/governance check was relaxed; `verify_persisted`, `_verify_events`,
  `_entry_hash`, checkpoints, receipt, and the M2 anchor path are all untouched.

## 6. Tests added/updated

- Updated `tests/test_m0_sandbox_attestation.py::test_attestation_tamper_breaks_chain`
  (deterministic weak baseline; genuine forge; reason + baseline assertions).

## 7. Validation commands and exact results

Run via `.venv/bin/python` (the TESTS.md-authoritative interpreter). This host has a
functional bwrap hard sandbox.

| Command | Result |
|---------|--------|
| `pytest tests/test_m0_sandbox_attestation.py::test_attestation_tamper_breaks_chain` | **1 passed** |
| `pytest tests/test_m0_sandbox_attestation.py` | **8 passed** |
| `pytest tests/aurel_trace tests/test_sandbox*.py tests/test_m0_sandbox_attestation.py tests/test_state_store_m0.py` | **324 passed** |
| `pytest tests/test_trace.py tests/test_trace_merkle_integrity.py tests/test_trace_persistence_p06.py tests/test_integrity_p04.py` | **24 passed** |
| `pytest tests/spine` | **61 passed** |
| `ruff check tests/test_m0_sandbox_attestation.py` | All checks passed |
| `mypy tests/test_m0_sandbox_attestation.py` | Success: no issues (1 file) |

## 8. Validation not run

| Command | Reason |
|---------|--------|
| `pytest -q` (full suite) | Times out > 10 min in this environment (documented in REPAIR-01) → reported UNVERIFIED. The change is a single test-body edit with no source/runtime impact, so blast radius is nil. |
| `pytest --cov` / `bandit` | Optional seal set; not run this pass. |

## 9. What was deliberately not implemented

- **No source change to `trace.py` / `sandbox.py` / `core_types.py`** — the
  verification already detects tampering; changing it would be unnecessary and, in
  the case of re-probing/re-signing historical attestations, wrong and scope-creep.
- **No new crypto/signing layer, no new attestation format, no new enums/surfaces,
  no roadmap systems (P6+).**
- **No broad refactor.**

## 10. Remaining risks

- The verification's tamper-evidence is hash-chain based (plus optional M2 external
  anchor). A **full re-forge** (rewrite events + checkpoints + receipt so the
  internal chain re-verifies) is only caught when an external anchor exists for the
  run — this is the existing, documented M2 design, unchanged here.
- Full pytest suite remains UNVERIFIED in this environment (time-bounded), as in
  REPAIR-01. One follow-up: seal the full suite on a longer-running host.

## 11. Next recommended task

1. Seal the full pytest suite in a longer-running environment to discharge the
   audit's standing "full pytest not sealed" item.
2. (Optional hardening, separate task) add a focused test asserting the M2 anchor
   catches a full re-forge, if not already covered, to document that property
   explicitly.

## 12. Truth labels used

`TRACE_VERIFIED` / tamper-evidence semantics only: verification reports `ok=True`
**only** when the chain is genuinely intact, and `ok=False` with a specific reason
when any recorded byte changes. No new labels introduced.
