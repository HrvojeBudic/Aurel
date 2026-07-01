import type { WebShellEvidenceRefDTO } from "../types";
import { TruthLabelBadge } from "./TruthLabelBadge";

interface Props {
  evidenceRefs: WebShellEvidenceRefDTO[];
}

export function EvidenceRefsPanel({ evidenceRefs }: Props) {
  return (
    <section className="panel">
      <h3>Evidence refs</h3>
      <ul className="evidence-list">
        {evidenceRefs.map((ref) => (
          <li key={ref.ref_id}>
            <strong>{ref.label}</strong> — <code>{ref.path}</code>{" "}
            <TruthLabelBadge label={ref.truth_label} />
          </li>
        ))}
      </ul>
    </section>
  );
}
