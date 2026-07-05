# Deployment Guide — Production Sandbox Setup

This guide covers running **Agentic Runtime** with hard isolation for governed
`--apply` workflows (repository tasks, demo harness).

## Prerequisites

- Python 3.11+
- Linux host (recommended for Bubblewrap)
- Optional: Docker daemon for container isolation

Install the package:

```bash
pip install -e ".[dev]"
```

## Sandbox tiers

| Profile | Isolation | Use case |
|---------|-----------|----------|
| `bubblewrap` | Hard (preferred) | Production `--apply` on Linux with `bwrap` |
| `docker` | Hard | Production `--apply` when Docker is available |
| `restricted_local` | Soft | Fallback when hard backends unavailable |
| `no_exec_readonly` | Soft | Plan-only / dry-run inspection |
| `unsafe_local_demo` | None | Local demos only — **not a security boundary** |

## Install hard isolation

### Bubblewrap (recommended on Linux)

```bash
# Debian/Ubuntu
sudo apt-get install bubblewrap

# Fedora
sudo dnf install bubblewrap

# Verify
bwrap --version
python -m agentic_runtime.cli sandbox-status --profile bubblewrap
```

### Docker

```bash
# Ensure daemon is running
docker info

python -m agentic_runtime.cli sandbox-status --profile docker
```

## Apply workflows

When you pass `--apply` without `--sandbox`, the CLI auto-selects:

1. `bubblewrap` if `bwrap` is available
2. else `docker` if the daemon is available
3. else `restricted_local` with a warning in the JSON output

### Repository task

```bash
# Plan only (default sandbox: restricted_local)
python -m agentic_runtime.cli repo-task "fix failing test in src/foo.py"

# Apply with auto hard sandbox
python -m agentic_runtime.cli repo-task "fix failing test in src/foo.py" --apply

# Explicit profile
python -m agentic_runtime.cli repo-task "objective" --apply --sandbox bubblewrap
```

### Demo harness

```bash
python -m agentic_runtime.cli demo-harness buggy_calculator --apply
python -m agentic_runtime.cli demo-harness buggy_calculator --apply --sandbox docker
```

## Verify deployment

```bash
python -m compileall src tests
python -m agentic_runtime.cli verify
python -m agentic_runtime.cli alpha-seal
python -m agentic_runtime.cli sandbox-status --json
```

Expected `sandbox-status` for production apply:

- `hard_isolated: true` when using `bubblewrap` or `docker`
- `unsafe: false`

## CI / restricted environments

Some CI sandboxes block nested subprocess execution. Timeout-related tests may
skip automatically; the full suite should pass on a normal Linux runner with
`bubblewrap` installed.

GitHub Actions workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

## Environment variables (optional LLM providers)

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI structured planning |
| `ANTHROPIC_API_KEY` | Anthropic structured planning |
| `AUREL_RUN_OLLAMA_TESTS=1` | Enable Ollama integration tests |

Runtime execution does not require API keys; mock provider is the default.

## Operational checklist

1. Install `bubblewrap` or enable Docker on the apply host
2. Run `alpha-seal` before promoting a release
3. Never use `unsafe_local_demo` for mutating production tasks
4. Review `approval_summary` and `trace_summary` in task JSON output
5. Store evidence artifacts (`--evidence-dir`) for audited coding-agent runs
