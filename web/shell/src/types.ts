/** Contract DTOs consumed from Python-owned web-shell-read-model.json */

export type ShellTruthLabel =
  | "LIVE"
  | "TRACE_VERIFIED"
  | "PREFLIGHT_ONLY"
  | "READ_ONLY"
  | "CONTRACT_ONLY"
  | "DEV_FIXTURE"
  | "UNAVAILABLE"
  | "ERROR"
  | "NOT_STARTED";

export interface WebShellEvidenceRefDTO {
  ref_id: string;
  label: string;
  path: string;
  truth_label: ShellTruthLabel;
  ref_hash: string;
}

export interface WebShellSurfaceViewDTO {
  surface_id: string;
  surface_label: string;
  available: boolean;
  truth_label: ShellTruthLabel;
  in_surface_selector: boolean;
  in_topbar_right: boolean;
  left_nav_owned_by_surface: boolean;
  right_inspector_owned_by_surface: boolean;
  evidence_refs: string[];
  limitations: string[];
  view_hash: string;
}

export interface WebShellClientStatusDTO {
  active_client: string;
  available_clients: string[];
  client_truth_label: ShellTruthLabel;
  local_run_mode: string;
  locally_runnable: boolean;
  launch_command: string;
  launch_working_directory: string;
  skeleton_truth_label: ShellTruthLabel;
  evidence_refs: string[];
  limitations: string[];
  status_hash: string;
}

export interface WebShellNoOverclaimViewDTO {
  boundary_id: string;
  forbidden_claim: string;
  reason: string;
  active: boolean;
  evidence_refs: string[];
  view_hash: string;
}

export interface WebShellReadModelDTO {
  pack_id: string;
  title: string;
  client_status: WebShellClientStatusDTO;
  surfaces: WebShellSurfaceViewDTO[];
  truth_labels: ShellTruthLabel[];
  evidence_refs: WebShellEvidenceRefDTO[];
  command_palette_availability: ShellTruthLabel;
  p2_vslice_a_status: ShellTruthLabel;
  local_run_mode: string;
  limitations: string[];
  no_overclaim_boundaries: WebShellNoOverclaimViewDTO[];
  next_pack: string;
  p210c_not_started: boolean;
  p210d_not_started: boolean;
  p210e_not_started: boolean;
  fixture_rel_path: string;
  read_model_hash: string;
}

export const SURFACE_SELECTOR_IDS = [
  "aurel_cro",
  "hq",
  "corp",
  "hub",
  "ide",
] as const;

export const TOPBAR_RIGHT_IDS = ["system", "settings"] as const;
