import type { WebShellClientStatusDTO } from "../types";
import { TruthLabelBadge } from "./TruthLabelBadge";

interface Props {
  status: WebShellClientStatusDTO;
}

export function ClientStatusPanel({ status }: Props) {
  return (
    <section className="panel">
      <h3>Client status</h3>
      <dl className="kv">
        <dt>Active client</dt>
        <dd>{status.active_client}</dd>
        <dt>Client truth</dt>
        <dd>
          <TruthLabelBadge label={status.client_truth_label} />
        </dd>
        <dt>Skeleton truth</dt>
        <dd>
          <TruthLabelBadge label={status.skeleton_truth_label} />
        </dd>
        <dt>Local run mode</dt>
        <dd>{status.local_run_mode}</dd>
        <dt>Locally runnable</dt>
        <dd>{String(status.locally_runnable)}</dd>
        {status.launch_command ? (
          <>
            <dt>Launch command</dt>
            <dd>
              <code>{status.launch_command}</code>
            </dd>
          </>
        ) : null}
      </dl>
      <p className="available-clients">
        Available clients: {status.available_clients.join(", ")}
      </p>
    </section>
  );
}
