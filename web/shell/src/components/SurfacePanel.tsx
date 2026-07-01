import type { WebShellSurfaceViewDTO } from "../types";
import { TruthLabelBadge } from "./TruthLabelBadge";

interface Props {
  surface: WebShellSurfaceViewDTO;
}

export function SurfacePanel({ surface }: Props) {
  return (
    <section className="surface-panel">
      <h2>{surface.surface_label}</h2>
      <p className="surface-id">surface_id: {surface.surface_id}</p>
      <TruthLabelBadge label={surface.truth_label} />
      <p className="placeholder">
        Active surface placeholder — contract-bound skeleton only. No full surface
        UI, route execution, or command actions.
      </p>
      <ul className="meta-list">
        <li>Left nav owned by surface: {String(surface.left_nav_owned_by_surface)}</li>
        <li>
          Right inspector owned by surface:{" "}
          {String(surface.right_inspector_owned_by_surface)}
        </li>
      </ul>
    </section>
  );
}
