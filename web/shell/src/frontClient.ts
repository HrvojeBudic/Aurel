/**
 * frontClient.ts — the ONE door between the React UI and the Aurel backend (F5.8).
 *
 * This is the ONLY module in `web/shell/src` allowed to touch `fetch` or
 * `WebSocket`. Every read is `GET /read/{model}` (a pure projection); every
 * mutation — a Signal/WorkOPS message, an approve/deny, a Board convert — is a
 * `ProposalEnvelope` POSTed to `/proposals` (the single mutation route). The
 * WebSocket is a stream, not a second door: what it carries is the same envelope.
 *
 * Honesty: when the Front server is unreachable the client enters read-only
 * FIXTURE mode — it serves the static dev fixture and DISABLES every proposal
 * action. It never fakes a successful submit offline.
 */
import type {
  ApprovalsDTO,
  AurelEUDTO,
  BoardJournalDTO,
  CorpKpiDTO,
  CorpPortfolioDTO,
  HqCommandDTO,
  LibraryDTO,
  ProposalEnvelope,
  ProposalResult,
  RoomHistoryDTO,
  SystemArchiveDTO,
  SystemAuditDTO,
  SystemModelRoutingDTO,
  SystemPoliciesDTO,
  SystemUsageDTO,
  WorkOpsTasksDTO,
} from "./front-types";

const DEFAULT_BASE = "http://127.0.0.1:8787";

function baseUrl(): string {
  const env = (import.meta as { env?: Record<string, string> }).env;
  return env?.VITE_AUREL_FRONT_BASE ?? DEFAULT_BASE;
}

export type FrontMode = "live" | "fixture";

export class FrontClient {
  private mode: FrontMode = "fixture";
  private readonly base: string;

  constructor(base: string = baseUrl()) {
    this.base = base;
  }

  /** Probe the server. Success ⇒ live mode; failure ⇒ read-only fixture mode. */
  async connect(): Promise<FrontMode> {
    try {
      const res = await fetch(`${this.base}/health`, { method: "GET" });
      this.mode = res.ok ? "live" : "fixture";
    } catch {
      this.mode = "fixture";
    }
    return this.mode;
  }

  get currentMode(): FrontMode {
    return this.mode;
  }

  get isLive(): boolean {
    return this.mode === "live";
  }

  // -- reads: pure projections ------------------------------------------------ //
  private async read<T>(model: string, params?: Record<string, string>): Promise<T> {
    const qs = params ? `?${new URLSearchParams(params).toString()}` : "";
    const res = await fetch(`${this.base}/read/${model}${qs}`, { method: "GET" });
    if (!res.ok) throw new Error(`read ${model} failed: ${res.status}`);
    return (await res.json()) as T;
  }

  signalHistory(room = "signal:main"): Promise<RoomHistoryDTO> {
    return this.read<RoomHistoryDTO>("signal/history", { room });
  }
  workopsTasks(): Promise<WorkOpsTasksDTO> {
    return this.read<WorkOpsTasksDTO>("workops/tasks");
  }
  workopsHistory(task: string): Promise<RoomHistoryDTO> {
    return this.read<RoomHistoryDTO>("workops/history", { task });
  }
  approvals(): Promise<ApprovalsDTO> {
    return this.read<ApprovalsDTO>("approvals");
  }
  library(): Promise<LibraryDTO> {
    return this.read<LibraryDTO>("library");
  }
  hqCommand(): Promise<HqCommandDTO> {
    return this.read<HqCommandDTO>("hq/command");
  }
  board(): Promise<BoardJournalDTO> {
    return this.read<BoardJournalDTO>("board");
  }
  aureleu(): Promise<AurelEUDTO> {
    return this.read<AurelEUDTO>("aureleu");
  }
  corpPortfolio(): Promise<CorpPortfolioDTO> {
    return this.read<CorpPortfolioDTO>("corp/portfolio");
  }
  corpKpi(): Promise<CorpKpiDTO> {
    return this.read<CorpKpiDTO>("corp/kpi");
  }
  systemAudit(params?: { limit?: string }): Promise<SystemAuditDTO> {
    return this.read<SystemAuditDTO>("system/audit", params);
  }
  systemUsage(): Promise<SystemUsageDTO> {
    return this.read<SystemUsageDTO>("system/usage");
  }
  systemModelRouting(): Promise<SystemModelRoutingDTO> {
    return this.read<SystemModelRoutingDTO>("system/model_routing");
  }
  systemPolicies(): Promise<SystemPoliciesDTO> {
    return this.read<SystemPoliciesDTO>("system/policies");
  }
  systemArchive(): Promise<SystemArchiveDTO> {
    return this.read<SystemArchiveDTO>("system/archive");
  }

  // -- the single mutation door ---------------------------------------------- //
  /** POST a ProposalEnvelope to the one mutation route. Blocked in fixture mode. */
  async propose(envelope: ProposalEnvelope): Promise<ProposalResult> {
    if (!this.isLive) {
      throw new Error(
        "read-only fixture mode: the Front server is unreachable; proposals are disabled",
      );
    }
    const res = await fetch(`${this.base}/proposals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(envelope),
    });
    const body = (await res.json()) as ProposalResult;
    if (!res.ok) throw new Error((body as { error?: string }).error ?? "proposal rejected");
    return body;
  }

  /** Approve/deny a pending approval — a `decide` proposal through the same door. */
  decide(requestId: string, approve: boolean): Promise<ProposalResult> {
    return this.propose({ kind: "decide", request_id: requestId, approve });
  }

  // -- the WebSocket stream (not a second door) ------------------------------ //
  /** Open the `/ws` stream. Inbound proposals reduce through the same dispatcher. */
  openStream(onMessage: (data: ProposalResult) => void): WebSocket | null {
    if (!this.isLive) return null;
    const wsBase = this.base.replace(/^http/, "ws");
    const ws = new WebSocket(`${wsBase}/ws`);
    ws.onmessage = (ev: MessageEvent) => {
      try {
        onMessage(JSON.parse(String(ev.data)) as ProposalResult);
      } catch {
        /* ignore malformed frame */
      }
    };
    return ws;
  }
}

export const frontClient = new FrontClient();
