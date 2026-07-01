import type { ShellTruthLabel } from "../types";

const LABEL_CLASS: Record<ShellTruthLabel, string> = {
  LIVE: "label-live",
  TRACE_VERIFIED: "label-trace",
  PREFLIGHT_ONLY: "label-preflight",
  READ_ONLY: "label-readonly",
  CONTRACT_ONLY: "label-contract",
  DEV_FIXTURE: "label-fixture",
  UNAVAILABLE: "label-unavailable",
  ERROR: "label-error",
  NOT_STARTED: "label-not-started",
};

interface Props {
  label: ShellTruthLabel;
}

export function TruthLabelBadge({ label }: Props) {
  return (
    <span className={`truth-badge ${LABEL_CLASS[label] ?? "label-contract"}`}>
      {label}
    </span>
  );
}
