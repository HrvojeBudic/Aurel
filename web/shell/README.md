# P2.10-B local web Shell skeleton

Contract-bound local web Shell skeleton consuming Python-owned `WebShellReadModel` JSON.

**Not Shell LIVE. Not full local app. Not command execution.**

## Prerequisites

Generate the read model fixture from Python (repo root):

```bash
.venv/bin/python -c "from agentic_runtime.aurel_shell.web_shell_read_model import export_web_shell_read_model_fixture; export_web_shell_read_model_fixture()"
```

## Commands

```bash
cd web/shell
npm install
npm run dev
npm run typecheck
npm test
npm run build
```

## Truth

- Python owns Aurel truth (`src/agentic_runtime/aurel_shell/web_shell_read_model.py`)
- TypeScript renders `public/web-shell-read-model.json` only
- P2.VSLICE-A remains `PREFLIGHT_ONLY`
- Next pack: P2.10-C (Tauri desktop shell)
