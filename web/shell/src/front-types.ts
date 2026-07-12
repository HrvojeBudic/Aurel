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
  options?: Array<{ option_id: string; persona: string; proposed_tool: string; title: string }>;
}

export interface DelegationDTO {
  delegation_id: string;
  granted_by: string;
  autonomy_ceiling: string;
  valid_from: number;
  valid_until: number;
  action_categories: string[];
  consent_ref: string;
}

export interface AurelEUDTO {
  model: string;
  live: boolean;
  mandates: string[];
  delegations: DelegationDTO[];
  persona_switches: Array<{ room_id: string; from: string; to: string; context_hash: string }>;
  dn: { dual_kernel_enabled: boolean; verifier_veto: string } & Record<string, unknown>;
  claims_aureleu_dispatcher_live: boolean;
}

// -- Corp / Business Plane (F7) ---------------------------------------------- //

export interface CorpJobDTO {
  job_id: string;
  title: string;
  status: string;
  mandate_ids: string[];
  repos: string[];
  runs: Array<Record<string, unknown>>;
  cost: Record<string, number> | null;
}

export interface CorpClientDTO {
  client_id: string;
  name: string;
  jobs: CorpJobDTO[];
  cost: Record<string, number> | null;
}

export interface CorpPortfolioDTO {
  model: string;
  live: boolean;
  clients: CorpClientDTO[];
  unassigned: Array<Record<string, unknown>>;
  cost: SeamDTO & Record<string, unknown>;
  alerts: SeamDTO & { count?: number };
  budget_governance: SeamDTO & Record<string, unknown>;
  claims_alerts_live: boolean;
  claims_budget_governance_live: boolean;
}

export interface CorpKpiDTO {
  model: string;
  live: boolean;
  reflex: SeamDTO & Record<string, unknown>;
  cost_per_task: SeamDTO & Record<string, unknown>;
}

// -- System / Time Plane (F8) ----------------------------------------------- //

export interface SystemBaseDTO {
  model: string;
  live: boolean;
  available: boolean;
  status?: string;
  truth_label?: string;
  operator_only?: boolean;
  reason?: string;
}

export interface SystemAuditDTO extends SystemBaseDTO {
  count?: number;
  total?: number;
  events: Array<Record<string, unknown>>;
  truncated?: boolean;
}

export interface SystemUsageDTO extends SystemBaseDTO {
  snapshot?: Record<string, unknown>;
  run_usage?: Record<string, unknown>;
  policy_remaining?: Record<string, unknown>;
  by_mandate?: Array<Record<string, unknown>>;
  by_agent?: Array<Record<string, unknown>>;
}

export interface SystemModelRoutingDTO extends SystemBaseDTO {
  profiles?: Record<string, unknown>;
  providers?: Record<string, unknown>;
  health?: Record<string, unknown>;
  promotion_gates?: Record<string, unknown>;
}

export interface SystemPoliciesDTO extends SystemBaseDTO {
  registry_bound?: boolean;
  cards?: Array<Record<string, unknown>>;
  registry_canonical_hash?: string;
  grants_authority?: boolean;
}

export interface SystemArchiveDTO extends SystemBaseDTO {
  persistence?: Record<string, unknown>;
  integrity?: SeamDTO & Record<string, unknown>;
  export_manifest?: SeamDTO & Record<string, unknown>;
  receipt_backlog?: Record<string, unknown>;
}
