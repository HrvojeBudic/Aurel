/**
 * front-types.ts — DTOs mirroring the Python Front read models + proposals (F5.8).
 *
 * Each interface zeroes in on one Python `to_dict()` / read-model body. These are
 * the only shapes the UI consumes; every mutation is a `ProposalEnvelope`.
 */

// -- proposals (the one mutation door) --------------------------------------- //
export interface ConverseProposal {
  kind: "converse";
  room_id: string;
  operator_identity: string;
  role: string;
  mandate_id: string;
  context_refs?: string[];
  text: string;
}

export interface ActProposal {
  kind: "act";
  tool: string;
  args?: Record<string, unknown>;
  risk?: string;
  rationale?: string;
  expected_effect?: string;
}

export interface DecideProposal {
  kind: "decide";
  request_id: string;
  approve: boolean;
}

export type ProposalEnvelope = ConverseProposal | ActProposal | DecideProposal;

export interface ConversationReplyDTO {
  mode: "answer" | "propose" | "unavailable";
  text: string;
  context_ref: string;
  source_refs: string[];
  truth_label: string;
  profile_used: string;
  usage_substantiated: boolean;
  proposal: ActProposal | null;
}

export interface ProposalResult {
  accepted?: boolean;
  kind?: string;
  wired?: boolean;
  turn_id?: string;
  reply?: ConversationReplyDTO;
  status?: string;
  request_id?: string;
  error?: string;
}

// -- read-model bodies ------------------------------------------------------- //
export interface HistoryEntryDTO {
  role: string;
  text: string;
  context_ref: string;
  turn_id: string;
}

export interface RoomHistoryDTO {
  model: string;
  live: boolean;
  room?: string;
  task?: string;
  entries: HistoryEntryDTO[];
}

export interface WorkOpsTaskDTO {
  task_id: string;
  room_id: string;
  message_count: number;
  last_text: string;
}

export interface WorkOpsTasksDTO {
  model: string;
  live: boolean;
  tasks: WorkOpsTaskDTO[];
}

export interface ApprovalsDTO {
  model: string;
  live: boolean;
  audit: Array<{
    tool: string | null;
    outcome: string | null;
    risk_class: string | null;
    decided_by: string | null;
    reason: string | null;
  }>;
}

export interface SeamDTO {
  status: string;
  reason?: string;
  owner?: string;
  alerts?: unknown[];
}

export interface LibraryAssetDTO {
  doc_id: string;
  path: string;
  exists: boolean;
}

export interface LibraryDTO {
  model: string;
  live: boolean;
  assets: LibraryAssetDTO[];
  memory_by_tier: Record<string, string[]>;
  rejected: Array<Record<string, string>>;
  min_truth_state: string | null;
  manifest: SeamDTO & Record<string, unknown>;
  claims_time_travel: boolean;
}

export interface HqRunDTO {
  run_id: string;
  status: string;
  reason_code: string;
  issuer: string;
  transitions: number;
}

export interface HqCommandDTO {
  model: string;
  live: boolean;
  runs: HqRunDTO[];
  approvals: {
    audit: ApprovalsDTO["audit"];
    pending: Array<Record<string, unknown>>;
    pending_source: string;
  };
  budget: SeamDTO & Record<string, unknown>;
  watchtower: SeamDTO;
  predictive: SeamDTO;
  claims_watchtower_live: boolean;
}

export interface BoardDecisionDTO {
  decision_id: string;
  decided_by: string;
  proposed_tool: string;
  title: string;
}

export interface BoardJournalDTO {
  model: string;
  live: boolean;
  decisions: BoardDecisionDTO[];
}
