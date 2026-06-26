# Agent Operating Guide

This repository implements a **governed agentic runtime**, not a chatbot wrapper.
An **Entity** proposes `CommandEnvelope` actions; the **Runtime** disposes through
policy, authority, HITL, budget, sandbox, verifier, trace, and governed memory.

## Before changing code

1. Read `ACTIVE_TASK.md` — current objective and acceptance criteria.
2. Read `STATE.md` — what works today and known limits.
3. Read `ARCHITECTURE.md` — module map and execution pipeline.
4. Read `TESTS.md` — canonical compile and test commands.

## CodeOps

This repository uses `agent/CODEOPS.md` as the upstream development protocol.

Before planning or coding significant work, follow:

1. Intake / Current Canon Snapshot
2. Brainstorm
3. Plan
4. Prompt Contract
5. Agent Report
6. OMNI Review

Templates live in `agent/templates/`.

CodeOps does not replace this guide. It extends the existing `agent/` governance layer.

Do not create duplicate state, decision, validation, or evidence systems.

## While working

- Keep changes **minimal and targeted**. No broad refactors unless explicitly tasked.
- Do **not** weaken tests, policy, sandbox, verifier, or governance to make tasks pass.
- Do **not** delete `.venv`, `.pytest_cache`, or `__pycache__` as cleanup unless tracked and required.
- Do **not** rename core architecture concepts (`Entity`, `Runtime`, `CommandEnvelope`, etc.).
- Preserve demo behavior unless the task explicitly changes it.

## After completing work

1. Update `ACTIVE_TASK.md` status if you finished the active task.
2. Append decisions to `DECISIONS.md` when you make non-obvious choices.
3. Add a report under `agent/reports/` and link it from `REPORTS.md`.
4. Run compile + tests documented in `TESTS.md` and record results in your report.

## Entrypoints

| Command | Purpose |
|---------|---------|
| `python -m agentic_runtime.cli status` | Runtime wiring + sandbox mode |
| `python -m agentic_runtime.cli demo` | End-to-end governed demo |
| `python -m agentic_runtime.cli verify` | Run pytest suite |
| `python -m agentic_runtime.demo` | Same as `cli demo` |

Package source: `src/agentic_runtime/`. Tests: `tests/`.
