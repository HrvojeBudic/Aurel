# Attic

Parked modules with zero importers (verified by `scripts/reverse_deps.py`).
Nothing here is packaged or imported; restore by moving back under
`src/agentic_runtime/` if a phase actually needs it.

| Module | Parked | Why |
|---|---|---|
| `heretic/` | 2026-07-08 (F0.3) | Docstring-only placeholder; zero importers. The G5 "HERETIC" governance level in `governance/profile.py` is unrelated to this package and unaffected. |

Remaining zero-importer candidates (left in place deliberately — referenced by
planned phases): `autonomy`, `compliance`, `identity.persona_manifest`,
`metacognition`.
