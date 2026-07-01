import type { WebShellNoOverclaimViewDTO, ShellTruthLabel } from "../types";
import { TruthLabelBadge } from "./TruthLabelBadge";

interface Props {
  boundaries: WebShellNoOverclaimViewDTO[];
  truthLabels: ShellTruthLabel[];
  commandPaletteAvailability: ShellTruthLabel;
  p2VsliceAStatus: ShellTruthLabel;
  limitations: string[];
  nextPack: string;
}

export function NoOverclaimPanel({
  boundaries,
  truthLabels,
  commandPaletteAvailability,
  p2VsliceAStatus,
  limitations,
  nextPack,
}: Props) {
  return (
    <section className="panel no-overclaim">
      <h3>Limitations / no-overclaim boundaries</h3>
      <div className="truth-row">
        <span>Command palette:</span>
        <TruthLabelBadge label={commandPaletteAvailability} />
        <span>P2.VSLICE-A:</span>
        <TruthLabelBadge label={p2VsliceAStatus} />
      </div>
      <div className="truth-row">
        <span>Truth labels:</span>
        {truthLabels.map((label) => (
          <TruthLabelBadge key={label} label={label} />
        ))}
      </div>
      <p>
        <strong>Next pack:</strong> {nextPack}
      </p>
      <ul className="limitations">
        {limitations.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <ul className="boundaries">
        {boundaries.map((b) => (
          <li key={b.boundary_id}>
            <strong>{b.forbidden_claim}</strong> — {b.reason}
          </li>
        ))}
      </ul>
    </section>
  );
}
