# PROMPT PACK — {{PACK_ID}} {{TITLE}}

Human-orchestrated multi-prompt work pack.

---

## Mission Overview

{{MISSION_OVERVIEW}}

---

## Why This Requires Multiple Prompts

{{REASON_FOR_MULTIPLE_PROMPTS}}

---

## Scope Separation

| Prompt | Scope | Files | Depends on |
|---|---|---|---|
| Prompt A | {{SCOPE_A}} | {{FILES_A}} | — |
| Prompt B | {{SCOPE_B}} | {{FILES_B}} | Prompt A |
| Review Prompt | Review only | — | A, B |
| Integration Prompt | Merge/integrate | {{FILES_INTEGRATION}} | A, B, Review |
| Seal Prompt | Exit seal | agent/reports/ | Integration |

---

## Dispatch Order

1. Prompt A — {{PROMPT_A_TITLE}}
2. Prompt B — {{PROMPT_B_TITLE}}
3. Review Prompt — adversarial review of A + B
4. Integration Prompt — resolve conflicts, wire together
5. Seal Criteria check — exit seal if applicable

Do not run prompts out of order unless explicitly planned.

---

## Prompt A

**Title:** {{PROMPT_A_TITLE}}

**Mission:** {{PROMPT_A_MISSION}}

**Files:** {{PROMPT_A_FILES}}

**Acceptance:** {{PROMPT_A_ACCEPTANCE}}

(Full prompt body or reference to saved prompt contract)

---

## Prompt B

**Title:** {{PROMPT_B_TITLE}}

**Mission:** {{PROMPT_B_MISSION}}

**Files:** {{PROMPT_B_FILES}}

**Acceptance:** {{PROMPT_B_ACCEPTANCE}}

(Full prompt body or reference to saved prompt contract)

---

## Review Prompt

Use `agent/templates/REVIEW_PROMPT_TEMPLATE.md`.

Review scope: Prompt A + Prompt B outputs.

Check: scope, wrong files, fake done, fake live, test quality, validation, evidence, git hygiene.

---

## Integration Prompt

**Mission:** {{INTEGRATION_MISSION}}

Wire outputs from A and B. Resolve conflicts. Run integration validation.

Files: {{INTEGRATION_FILES}}

---

## Seal Criteria

- [ ] All prompts completed
- [ ] Review passed or repairs done
- [ ] Integration validated
- [ ] Reports linked
- [ ] agent/ canon updated
- [ ] Final git clean
- [ ] No fake LIVE / TRACE_VERIFIED

Use `agent/templates/SEAL_TEMPLATE.md` for final seal.

---

## Warning

**Use only when file/module scope separation is real.**

**Do not run parallel prompts over the same files unless explicitly planned.**

Operator selects tool/model for each dispatch. CodeOps does not route models.
