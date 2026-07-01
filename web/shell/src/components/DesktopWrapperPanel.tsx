import type { DesktopShellReadModelDTO } from "../desktop-types";
import { TruthLabelBadge } from "./TruthLabelBadge";

interface Props {
  desktop: DesktopShellReadModelDTO;
}

export function DesktopWrapperPanel({ desktop }: Props) {
  const status = desktop.desktop_client_status;
  const wrapped = desktop.wrapped_web_shell_status;
  const boundary = desktop.capability_boundary;

  return (
    <section className="panel desktop-wrapper-panel">
      <h2>Desktop Wrapper (P2.10-C)</h2>
      <p className="muted">
        Tauri boundary — contract only, not Shell LIVE or full desktop app
      </p>
      <dl className="status-grid">
        <dt>Active client</dt>
        <dd>{status.active_client}</dd>
        <dt>Wrapped client</dt>
        <dd>{status.wrapped_client_kind}</dd>
        <dt>Desktop run mode</dt>
        <dd>{status.desktop_run_mode}</dd>
        <dt>Wrapper truth</dt>
        <dd>
          <TruthLabelBadge label={status.wrapper_truth_label} />
        </dd>
        <dt>Locally runnable</dt>
        <dd>{status.locally_runnable ? "yes (wrapper only)" : "no"}</dd>
        <dt>Launch command</dt>
        <dd>{status.launch_command || "—"}</dd>
        <dt>Wrapped web read model</dt>
        <dd>{wrapped.source_read_model_ref}</dd>
        <dt>Web read model hash</dt>
        <dd className="mono">{wrapped.source_read_model_hash.slice(0, 16)}…</dd>
        <dt>Next pack</dt>
        <dd>{desktop.next_pack_pointer}</dd>
      </dl>
      <div className="capability-boundary">
        <h3>Capability boundary</h3>
        <p>
          Allowed minimal:{" "}
          {boundary.allowed_capabilities.map((c) => c.capability).join(", ")}
        </p>
        <p>
          Disabled native:{" "}
          {boundary.disabled_capabilities.map((c) => c.capability).join(", ")}
        </p>
        <p>
          Future-gated:{" "}
          {boundary.future_gated_capabilities.map((c) => c.capability).join(", ")}
        </p>
      </div>
      <ul className="limitations">
        {desktop.limitations.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
