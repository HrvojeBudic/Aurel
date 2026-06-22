# Tool Manifest Files

Declarative tool/plugin manifests describe what tools *claim* to be. They do not grant authority, register runtime capabilities, or execute anything.

## Scope (P1.3.2)

The manifest loader (`agentic_runtime.tool_manifest.loader`) can:

- Read local `.json` manifest files (primary format)
- Parse optional `.yaml` / `.yml` via the repository's minimal YAML parser
- Compute SHA-256 content hashes
- Parse into `PluginManifest` + `ToolManifest` domain objects
- Validate metadata using P1.3.1 rules plus bundle consistency checks
- Return structured `ManifestLoadResult` outcomes

The loader does **not**:

- Activate tools into a runtime capability registry
- Register Tool Bus handlers
- Execute tools or invoke side effects
- Grant permissions or authority

**Manifest loading is not registry activation.**

## File format

Root JSON object:

```json
{
  "plugin": { "...PluginManifest fields..." },
  "tools": [ "...ToolManifest objects..." ]
}
```

See `tests/fixtures/tool_manifests/valid_builtin_repo.json` for a complete example.

Enum fields use string values matching P1.3.0 enums (for example `"origin": "builtin"`, `"risk_class": "R1"`). Invalid enum values produce `parse_error` or `invalid` results — they are not silently coerced.

## Key types

| Type | Role |
|------|------|
| `ManifestBundle` | Parsed plugin + declared tools + validation issues |
| `ManifestLoadResult` | Structured outcome for one file load |
| `ManifestLoadStatus` | `loaded`, `loaded_with_warnings`, `invalid`, `parse_error`, `not_found`, `unsupported_format` |
| `ManifestSource` | Provenance record for a discovered manifest path |

## Loading API

```python
from pathlib import Path
from agentic_runtime.tool_manifest import load_manifest_file, load_manifest_directory

result = load_manifest_file(Path("manifests/builtin_repo.json"))
if result.status == ManifestLoadStatus.LOADED:
    plugin = result.plugin_manifest
    tools = result.tool_manifests
```

Directory loading scans `*.json`, `*.yaml`, and `*.yml` in sorted order (non-recursive). One bad file does not prevent other manifests from loading.

## Validation

`validate_manifest_bundle()` reuses P1.3.1 validators and adds bundle rules:

- Tool `plugin_id` must match plugin `plugin_id`
- `plugin.tools` must reference tools present in the bundle
- Every bundled tool must appear in `plugin.tools` when that list is non-empty
- No duplicate `tool_id` values
- Empty `tools` list is blocking

Blocking issues (`error` / `critical`) yield `ManifestLoadStatus.INVALID`. Warnings/info only yield `loaded_with_warnings`.

## Tool registry (P1.3.3)

The tool registry (`agentic_runtime.tool_manifest.registry`) catalogs validated `ToolCapability` objects normalized from manifest files.

```python
from agentic_runtime.tool_manifest import ToolRegistry, load_manifest_file

registry = ToolRegistry()
result = load_manifest_file("manifests/builtin_repo.json")
registry.register_manifest_result(result)

active = registry.list_active_tools()  # metadata only — not execution rights
```

The registry can:

- Accept `ManifestLoadResult` / `ManifestBundle` from the loader
- Reject invalid manifests and duplicate `tool_id` values
- Normalize valid `ToolManifest` objects into `ToolCapability` entries
- List, query, disable, and enable catalog entries
- Expose high-risk and approval-required helpers (metadata only)

The registry does **not**:

- Execute tools or invoke Tool Bus handlers
- Grant authority or permissions
- Perform autonomous tool selection

**Registry visibility is not permission.** Disabled, invalid, quarantined, deprecated, experimental, and R6 tools are stored as records but excluded from `list_active_tools()`.

Capability role tags (`perception`, `cognition`, `action`, `verification`, `memory`, `environment`) are derived metadata for queries only — not agent selection logic.

## Quarantine (P1.3.4)

The quarantine layer (`agentic_runtime.tool_manifest.quarantine`) classifies validation issues, decides isolation actions, and stores quarantine records in memory.

```python
from agentic_runtime.tool_manifest import (
    classify_validation_issues,
    decide_quarantine_for_tool,
    QuarantineStore,
)

report = classify_validation_issues(issues, subject_id="tool.id", subject_type="tool")
decision = decide_quarantine_for_tool(tool, plugin, issues)
```

Quarantine law:

- **Quarantine is isolation, not deletion.** Records preserve reasons, validation issues, source path, and manifest hash.
- **Quarantine is not approval workflow.** It does not grant or deny runtime authority.
- **Critical/high-risk unsafe metadata** leads to quarantine or reject decisions.
- **Warning-only manifests** remain inspectable and do not auto-quarantine unless provenance/risk rules require it.

`ToolRegistry` integrates quarantine via `registry.quarantine_store` and excludes quarantined subjects from `list_active_tools()`.

## Tool invocation drafts (P1.3.5)

The invocation draft layer (`agentic_runtime.tool_manifest.invocation`) builds structured tool-use **proposals** from active registry capabilities.

```python
from agentic_runtime.tool_manifest import (
    ToolInvocationContext,
    ToolRegistry,
    create_tool_invocation_draft,
    load_manifest_file,
)

registry = ToolRegistry()
registry.register_manifest_result(load_manifest_file("manifests/builtin_repo.json"))

result = create_tool_invocation_draft(
    registry,
    "builtin.repo_scan",
    {"root_path": "."},
    ToolInvocationContext(
        requested_by="operator",
        purpose="Inspect repository layout",
        request_source="cli",
    ),
)
# result.draft is a proposal — not an executed tool call
```

Draft creation can:

- Validate input payloads against `ToolCapability.input_contract` (minimal JSON schema)
- Reject missing, disabled, quarantined, invalid, deprecated, or non-active tools
- Copy risk, reversibility, approval, predicted effect, and evidence-plan metadata
- Return `ToolInvocationDraftResult` with statuses such as `created`, `invalid_input`, `tool_not_found`, `tool_quarantined`, `requires_approval`

Draft creation does **not**:

- Execute, invoke, or dispatch tools
- Grant authority or bypass quarantine
- Implement approval workflow or policy enforcement

**Draft status values (P1.3.5):**

| Status | Meaning |
|--------|---------|
| `draft` | Initial proposal shell |
| `invalid` | Input validation failed |
| `blocked` | Tool inactive or unsafe (e.g. R6) |
| `requires_approval` | High-risk/sensitive; needs future approval path |
| `ready_for_policy` | Valid proposal awaiting future policy gate — **not executable** |

`evidence_plan` is a seed string describing what a future execution audit should capture — it is not evidence itself.

## Tool lifecycle trace events (P1.3.6)

The lifecycle event layer (`agentic_runtime.tool_manifest.events`) records manifest → registry → quarantine → draft transitions as serializable events.

```python
from agentic_runtime.tool_manifest import (
    ToolLifecycleEventRecorder,
    build_manifest_loaded_event,
    build_tool_registered_event,
    build_invocation_draft_event,
    create_tool_invocation_draft,
    load_manifest_file,
    ToolRegistry,
)

recorder = ToolLifecycleEventRecorder()
load = load_manifest_file("manifests/builtin_repo.json")
recorder.record(build_manifest_loaded_event(load))

registry = ToolRegistry()
for result in registry.register_manifest_result(load):
    recorder.record(build_tool_registered_event(result))

draft = create_tool_invocation_draft(registry, "builtin.repo_scan", {"root_path": "."}, context)
recorder.record(build_invocation_draft_event(draft))
```

Trace events are:

- **Lifecycle records** — who/what/when for manifest, registry, quarantine, and draft state
- **Not execution** — building or recording an event does not run a tool
- **Not verified evidence** — evidence requires validated execution/result support in later phases
- **Composable** — pure builder functions; no hidden side effects in loader/registry paths

Quarantine events preserve reasons, severity, suggested action, manifest hash, and optional `threat_surface` metadata as an immune-system trace seed.

Invocation draft events preserve `predicted_effect`, `evidence_plan`, and simulation/dry-run capability flags where available — preparing future world-model / planning loops without running simulation now.

## Research-inspired metadata (P1.3.7)

Optional schema fields prepare future world-model, simulation, governance, and learning layers without executing any of them.

```python
from agentic_runtime.tool_manifest import (
    derive_tool_roles,
    derive_default_state_delta_contract,
    ToolRole,
    StateDeltaType,
)
```

**New types:** `ToolRole`, `StateDeltaType`, `DriftRisk`, `ExternalityLevel`, `StateDeltaContract`, `SimulationProfile`, `ToolSafetySurface`, `ToolLearningProfile`

**Derivation helpers:** `derive_tool_roles`, `derive_state_delta_type`, `derive_default_state_delta_contract`, `derive_default_simulation_profile`, `derive_safety_surface`, `derive_learning_profile`

**Law:**

- **Metadata is not permission** — research fields describe intent and readiness only.
- **Derived metadata is a seed, not final truth** — explicit manifest fields preferred for high-risk tools.
- **SimulationProfile does not execute simulation** — strategies are declarative placeholders.
- **LearningProfile does not trigger learning** — hints for future skill/procedure pipelines only.
- **Prediction fields are not calibrated prediction** — quality/observable flags are seeds for future JEPA/world-model loops.

High-risk (R5+), external, and secret-access tools require explicit `state_delta_contract` and/or `safety_surface` or validation emits blocking errors. Low-risk read-only tools remain valid without new fields.

## Built-in seed manifests (P1.3.8)

Production built-in tool manifests ship under `src/agentic_runtime/tool_manifest/manifests/`. They are **declarative capability seeds only** — no Tool Bus handlers, no filesystem writes, no test execution, no model calls, and no memory promotion.

```python
from agentic_runtime.tool_manifest import (
    get_builtin_manifest_directory,
    load_builtin_tool_manifests,
    ToolRegistry,
)

for result in load_builtin_tool_manifests():
    print(result.source_path, result.status.value)

registry = ToolRegistry()
for result in load_builtin_tool_manifests():
    if result.status.value in {"loaded", "loaded_with_warnings"}:
        registry.register_manifest_result(result)
```

**Helpers:** `get_builtin_manifest_directory()` → shipped manifests path; `load_builtin_tool_manifests()` → list of `ManifestLoadResult`.

### Shipped built-in tools

| Tool ID | Plugin | Role(s) | Risk | State delta | Simulation | Safety |
|---------|--------|---------|------|-------------|------------|--------|
| `builtin.repo_scan` | `builtin.repo` | perception, cognition | R1 | read_only_observation | read_only_probe | local_only |
| `builtin.read_project_file` | `builtin.filesystem` | perception | R1 | read_only_observation | read_only_probe | local_only |
| `builtin.write_file_draft` | `builtin.filesystem` | action | R2 | local_state_change (draft diff) | draft_only / diff_preview | operator attention |
| `builtin.run_tests_draft` | `builtin.test` | verification | R3 | environment_state_change | command_preview / sandbox_run | action + environment |
| `builtin.create_evidence_record` | `builtin.evidence` | verification, memory, governance | R2 | governance_state_change | draft_only | memory + policy |
| `builtin.create_memory_candidate` | `builtin.memory` | memory, cognition | R2 | memory_state_change (candidate only) | draft_only | memory + provenance |
| `builtin.model_complete_structured` | `builtin.model` | cognition | R2 | read_only_observation (structured proposal) | manual_review | cognition + policy |

**Law:**

- **Built-in manifest is declaration, not implementation.**
- **Built-in registry visibility does not grant authority.**
- **Built-in invocation draft does not execute.**
- **Memory candidate creation is not memory canonization.**
- **Model manifest is local/mock-safe metadata — it does not call cloud providers.**

Integration path:

```
manifest file → load_builtin_tool_manifests → validation → quarantine → registry → invocation draft → lifecycle event
```

Test manifests remain under `tests/fixtures/tool_manifests/` (invalid/edge-case fixtures only).

## Declarative manifest vs executable runtime tool

Two tool concepts coexist and must not be merged in P1.3:

| Concept | Location | Purpose |
|---------|----------|---------|
| Manifest catalog | `tool_manifest/` | Declare, validate, quarantine, catalog, draft, trace |
| Tool Bus | `tools.py`, `runtime.py` | Execute handlers inside sandbox after policy/HITL |

Manifest registration does **not** register Tool Bus handlers. Invocation drafts do **not** execute.

## No-execution invariant

P1.3 must never:

- call `runtime.submit` or `ToolRuntime.dispatch`
- create `CommandEnvelope` from drafts
- run shell, network, model provider, or file-write side effects
- grant authority or bypass P2 policy/approval layers

Seal proof: `tests/test_p13_tool_manifest_layer_seal.py::test_p13_manifest_layer_has_no_execution_power`

## Future bridge (not implemented)

Planned after authority/command layer exists (likely P6 Governed Tool Bus Expansion):

```
ManifestToolCatalog → ToolInvocationDraft → Authority/Policy → CommandEnvelope → runtime.submit → ToolRuntime
```

Do not implement this bridge in P1.3.

## P1.3.9 seal verification

```bash
PYTHONPATH=src:. pytest tests/test_p13_tool_manifest_layer_seal.py -q
```

## Fixtures

Test manifests live under `tests/fixtures/tool_manifests/`.

## Related docs

- `agent/ARCHITECTURE.md` — P1.3.0–P1.3.9 tool manifest sections and sealed boundary
- `agent/reports/P1.3_TOOL_PLUGIN_MANIFEST_REPORT.md` — phase report and seal outcome
- `tests/test_p13_tool_manifest_layer_seal.py` — P1.3.9 seal tests
