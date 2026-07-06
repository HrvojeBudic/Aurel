# Aurel — Deployment

This document describes what can be deployed today, the host requirements for
governed execution, and the explicit gates that must pass before any part of
the system crosses a trust boundary. It is written to the *observed* state of
the runtime, not aspirationally.

## What runs today

The core runtime — policy → approval → sandbox boundary → verifier → hash-chained
trace — executes as claimed. Read-only tool execution (`read_file`, `list_dir`,
`search_text`, `git_status`) plus the persistent trace ledger is the smallest
safe slice suitable for a localhost deployment.

The local web console (`agentic-runtime spine-serve`, module
`agentic_runtime.spine.webui`) is stdlib-only, binds `127.0.0.1` by default, and
drives every write through the governed runtime (policy, approval, the
hard-isolation gate, and the trace). Any provider API key is read from the
server environment and never sent to the browser.

## Host requirements for governed execution

Mutating execution requires a **functionally verified** hard sandbox. Run:

```
agentic-runtime doctor
```

`doctor` executes the real isolation probes (not a `--version`/`info` check) and
reports which governance levels (G0–G5) are physically achievable on the host.
It exits non-zero when no hard sandbox is functional.

### Bubblewrap (preferred, lightweight)

Bubblewrap needs unprivileged user namespaces. On kernels with the AppArmor
userns restriction enabled, `bwrap --unshare-net` fails with
`loopback: Failed RTM_NEWADDR: Operation not permitted`. Enable unprivileged
userns:

```
echo 'kernel.apparmor_restrict_unprivileged_userns=0' | sudo tee /etc/sysctl.d/99-aurel-userns.conf
sudo sysctl --system
```

Verify: `bwrap --unshare-all --dev-bind / / /bin/true` exits 0.

### Docker (fallback, stronger isolation)

The runtime runs containers with `--cap-drop ALL --security-opt no-new-privileges
--read-only --network none`. The snap distribution of Docker breaks `exec` under
`no-new-privileges` (`exec ...: operation not permitted`). Install `docker-ce`
from the official repository instead of the snap, and add your user to the
`docker` group.

Verify: `docker run --rm --cap-drop ALL --security-opt no-new-privileges
--read-only python:3.12-slim python3 -c "print('ok')"` prints `ok`.

## Sandbox attestation

At runtime construction, a hard-sandbox backend writes a **SandboxAttestation**
record into the trace: the functional probe result, the reason on failure, and a
host fingerprint (kernel release, userns sysctl). This makes the isolation
posture a run executed under part of the tamper-evident record — a false
"available" is structurally impossible because availability is only claimed
after a real sandboxed execution.

## Partial-deployment gates

Do **not** promote a mutating slice to any deployment until all three pass:

* **G-A — Isolation attested.** `doctor` reports a functional hard sandbox on the
  target host (a real namespace/container exec, not a version check).
* **G-B — Single-writer trace.** The ledger append path is serialized (in-process
  lock + cross-process file lock); concurrent writers fail closed rather than
  interleaving. Regression: `tests/aurel_trace/test_concurrent_append.py`.
* **G-C — External anchor.** The trace merkle root is anchored outside the agent's
  own write domain, so a full chain re-forge is detectable across the trust
  boundary. Without this, HERETIC-level (G5) operation is refused.

## Communication boundaries

* **In-proc** — full trust, trivial ordering (single writer, enforced by G-B).
* **IPC (same host)** — crash isolation for worker processes; the ledger must be
  owned by a single writer (lock or writer daemon).
* **Network** — implicit trust is gone. Requires signed events (cryptographic
  binding of `issuer_card_id`), an ordering owner/sequencer, idempotency via the
  existing `command_hash`, and the external anchor of G-C. Until those exist,
  network execution is out of scope.

## Determinism / replay limits

Replay reconstructs state from the recorded trace and a model cassette (recorded
model I/O), reproducing a run without network access. State-hash equivalence is
the success criterion. Non-deterministic tool output (`run_shell`/`run_tests`
stdout) is compared at the state-hash level, not byte-for-byte; wall-clock and
RNG seed capture are out of scope for the first replay version.
