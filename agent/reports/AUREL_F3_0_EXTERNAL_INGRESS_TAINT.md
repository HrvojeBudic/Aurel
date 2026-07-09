# AUREL F3.0 — External Ingress: Taint & Injection Defense (Track D / D0)

_2026-07-09, branch `feat/f3-external-executors` (from `master` @ post-F2 merge). First F3 slice._

## What shipped

The dependency-free security foundation every F3 external-executor surface rests on
(gate-check, MCP gateway, MCP client bridge, A2A). New pure-library package
`src/agentic_runtime/external_ingress/` — stdlib-only, deterministic, no runtime wiring:

- **`taint.py`** — `SourceKind` (closed-world), `EXTERNAL_ORIGIN_KINDS` /
  `TRUSTED_ORIGIN_KINDS` frozen sets, `TaintLabel` (TRUSTED/UNTRUSTED/QUARANTINED),
  frozen `TaintedContent`, `make_tainted`. **`instruction_eligible` is a computed
  property, never a stored field** — external origin ⇒ always False; QUARANTINED ⇒
  always False. `make_tainted` takes **no label argument** (label derived from
  provenance alone), so there is no API path to forge TRUSTED onto external content.
- **`injection_detector.py`** — deterministic, case-insensitive stdlib regex
  signatures (`InstructionOverride`, `RoleHijack`, `SystemPromptProbe`, `SecretExfil`,
  `ToolInjection`, `PolicyOverride`), severity-ranked. `scan_for_injection` is
  **advisory only**, sorts findings by `(start, signature)`, and **never raises**
  (non-str fails closed to empty).
- **`sanitization.py`** — `SanitizationCrossing`: the single audited seam where
  tainted content is admitted **as inert data only**. `crosses_as_instruction` is
  hard-wired False; QUARANTINED ⇒ `data_view()` returns None (fail closed); the
  injection scan rides along as evidence but **never decides admission** (provenance
  does).

Flag `AUREL_EXTERNAL_INGRESS` defined-not-gating (A0-style): pure library, opt-in by
call; becomes load-bearing when F3.1+ wires ingress into gate/gateway paths.

## Doctrine sealed (the point of the slice)

**Instruction-eligibility is forbidden by PROVENANCE, not by scanning.** A heuristic
that could *permit* is one an attacker can defeat; a structural forbid cannot be
talked around. Proven both directions: a dirty scan on operator content does NOT
downgrade it (stays instruction-eligible); a clean scan on external content does NOT
upgrade it (stays ineligible). The detector annotates; provenance gates.

## Evidence

- Seal `tests/test_p6f3_0_external_ingress_taint.py` — **18 passed** (structural taint
  across all external kinds; internal eligibility; unknown fails closed; quarantine
  only narrows; no-forge; scan-is-advisory both directions; signature fires/quiet/
  deterministic/never-raises; data-only crossing; quarantine fail-closed; flag default
  OFF; content-hash determinism).
- ruff clean; mypy clean (4 source files); compileall OK.
- **Purely additive** — no existing file modified, so byte-identical OFF is structural.
  Package imports clean, flag reads False by default.

## Next

**F3.1 — gate-check foundation.** `aurel gate check`: run a proposed (tool, args) from
an external executor through governance (policy + contract) **read-only, no execute**,
return allow/deny + reason. Reuse `runtime.submit` governance path; external payloads
enter as `make_tainted(..., EXTERNAL_EXECUTOR)`. Seal `test_p6f3_1_gate_check.py`.
