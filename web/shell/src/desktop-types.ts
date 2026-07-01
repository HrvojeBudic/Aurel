/** Desktop wrapper DTOs consumed from Python-owned desktop-shell-read-model.json */

import type { ShellTruthLabel, WebShellReadModelDTO } from "./types";

export interface DesktopShellClientStatusDTO {
  active_client: string;
  wrapped_client_kind: string;
  client_truth_label: ShellTruthLabel;
  wrapper_truth_label: ShellTruthLabel;
  desktop_run_mode: string;
  locally_runnable: boolean;
  launch_command: string;
  build_command: string;
  launch_working_directory: string;
  tauri_config_path: string;
  evidence_refs: string[];
  limitations: string[];
  status_hash: string;
}

export interface DesktopShellWrappedWebShellStatusDTO {
  source_read_model_ref: string;
  source_read_model_hash: string;
  web_client_truth_label: ShellTruthLabel;
  web_local_run_mode: string;
  web_locally_runnable: boolean;
  evidence_refs: string[];
  limitations: string[];
  status_hash: string;
}

export interface DesktopShellCapabilityEntryDTO {
  capability: string;
  status: string;
  evidence_refs: string[];
  limitations: string[];
  entry_hash: string;
}

export interface DesktopShellCapabilityBoundaryDTO {
  client_kind: string;
  allowed_capabilities: DesktopShellCapabilityEntryDTO[];
  disabled_capabilities: DesktopShellCapabilityEntryDTO[];
  future_gated_capabilities: DesktopShellCapabilityEntryDTO[];
  unavailable_capabilities: DesktopShellCapabilityEntryDTO[];
  evidence_refs: string[];
  limitations: string[];
  no_overclaim_boundaries: string[];
  boundary_hash: string;
}

export interface DesktopShellReadModelDTO {
  pack_id: string;
  title: string;
  desktop_client_status: DesktopShellClientStatusDTO;
  wrapped_web_shell_status: DesktopShellWrappedWebShellStatusDTO;
  available_surfaces: string[];
  surface_availability: string[];
  truth_label_summary: ShellTruthLabel[];
  evidence_refs: string[];
  desktop_run_mode: string;
  capability_boundary: DesktopShellCapabilityBoundaryDTO;
  limitations: string[];
  p2_vslice_status: ShellTruthLabel;
  next_pack_pointer: string;
  p210d_not_started: boolean;
  p210e_not_started: boolean;
  fixture_rel_path: string;
  read_model_hash: string;
}

export interface DesktopShellViewDTO {
  desktop: DesktopShellReadModelDTO;
  web: WebShellReadModelDTO;
}
