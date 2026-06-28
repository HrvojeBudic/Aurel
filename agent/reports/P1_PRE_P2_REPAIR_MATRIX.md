# P1-PRE-P2 Repair Matrix

_Date: 2026-06-28_

| ID | Severity | Area | Problem | Evidence | Required repair pack | Blocks P2? |
| -- | -------: | --- | --- | --- | --- | --- |
| R1 | critical | output_passport/seal | P1.9-D exit seal is PARTIAL, not SEALED | `agent/reports/P1_9_D_INTEGRATION_TAIL_PACK.md` section 25 records `Exit seal decision: PARTIAL` and `P2 readiness: NOT_READY_FOR_P2` | P1.9.30-SEAL-REPAIR | yes |
| R2 | critical | validation | Full pre-P2 validation sweep was not run because the prompt stop condition fired | `agent/reports/P1_PRE_P2_FULL_AUDIT_AND_SEAL.md` sections 14-16 | P1-PRE-P2-REPAIR | yes |
| R3 | medium | truth labels | Broad repo truth-label adjudication incomplete after seal stop condition | Truth-label search started, but full adjudication stopped once P1.9-D PARTIAL seal was confirmed | TRUTH-LABEL-REPAIR | maybe |

## Recommended Next Prompt

`P1.9.30-SEAL-REPAIR - exit seal focused repair`

Secondary follow-up after seal repair:

`P1-PRE-P2-AUDIT - rerun full audit, validation, truth-label review, and P2 readiness decision`
