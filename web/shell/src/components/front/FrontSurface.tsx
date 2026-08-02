/**
 * FrontSurface.tsx — the live Front v1 surfaces (F5.8).
 *
 * Every panel reads through `frontClient` (GET /read/*) and mutates ONLY through
 * `frontClient.propose` (POST /proposals). No panel touches fetch/WebSocket
 * directly — the client is the one door. In fixture mode all compose/approve
 * actions are disabled and an honest banner says so.
 */
import { useCallback, useEffect, useState } from "react";
import type { FrontClient, FrontMode } from "../../frontClient";
import { SystemPanel } from "./SystemPanel";
import type {
  AurelEUDTO,
  BoardJournalDTO,
  CorpKpiDTO,
  CorpPortfolioDTO,
  HqCommandDTO,
  LibraryDTO,
  RoomHistoryDTO,
  WorkOpsTasksDTO,
} from "../../front-types";

interface SurfaceProps {
  surfaceId: string;
  client: FrontClient;
  mode: FrontMode;
}

/**
 * Run an async read/propose and keep its failure visible.
 *
 * Every panel used to fire `void client.x().then(setY)`, so a rejected read left
 * the panel showing stale or empty content with nothing to explain it — the same
 * silence that made a dropped chat message look like a delivered one. `run`
 * clears the message on success, so a recovered surface stops complaining.
 */
function useLastError(): [string, (fn: () => Promise<unknown>) => Promise<void>] {
  const [error, setError] = useState("");
  const run = useCallback(async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);
  return [error, run];
}

function ErrorBanner({ message }: { message: string }) {
  if (!message) return null;
  return (
    <p className="front-error" role="alert">
      {message}
    </p>
  );
}

/** A chat panel shared by Signal and WorkOPS — same conversation engine, one door. */
function ChatPanel({
  client,
  mode,
  room,
  label,
}: {
  client: FrontClient;
  mode: FrontMode;
  room: string;
  label: string;
}) {
  const [entries, setEntries] = useState<RoomHistoryDTO["entries"]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, run] = useLastError();
  const live = mode === "live";

  const refresh = useCallback(async () => {
    if (!live) return;
    const isWorkops = room.startsWith("workops:");
    const hist = isWorkops
      ? await client.workopsHistory(room.slice("workops:".length))
      : await client.signalHistory(room);
    setEntries(hist.entries);
  }, [client, live, room]);

  useEffect(() => {
    void run(refresh);
  }, [refresh, run]);

  async function send() {
    if (!draft.trim() || busy) return;
    setBusy(true);
    const text = draft;
    await run(async () => {
      const result = await client.propose({
        kind: "converse",
        room_id: room,
        operator_identity: "operator",
        role: "operator",
        mandate_id: "default",
        text,
      });
      // `wired: false` is a 200 for a proposal that was accepted and then
      // dropped — the server has no conversation engine bound. Keep the draft so
      // the message is not lost, and say why nothing happened.
      if (result.wired === false) {
        throw new Error(
          "the Front server accepted this but has no conversation engine bound — nothing was sent",
        );
      }
      setDraft("");
      await refresh();
    });
    setBusy(false);
  }

  return (
    <section className="front-panel chat-panel">
      <h3>{label}</h3>
      <p className="room-id">room: {room}</p>
      <ul className="chat-log">
        {entries.map((e) => (
          <li key={e.turn_id + e.role} className={`msg msg-${e.role}`}>
            <span className="msg-role">{e.role}</span>
            <span className="msg-text">{e.text}</span>
            {e.context_ref ? (
              <span className="ctx-ref" title="ContextLoom ref">
                ⧉ {e.context_ref.slice(0, 10)}
              </span>
            ) : null}
          </li>
        ))}
        {entries.length === 0 ? <li className="msg empty">No messages yet.</li> : null}
      </ul>
      <div className="composer">
        <input
          value={draft}
          onChange={(ev) => setDraft(ev.target.value)}
          onKeyDown={(ev) => {
            if (ev.key === "Enter") void send();
          }}
          placeholder={live ? "Message Aurel…" : "read-only fixture mode"}
          disabled={!live || busy}
        />
        <button onClick={() => void send()} disabled={!live || busy}>
          Send
        </button>
      </div>
      <ErrorBanner message={error} />
    </section>
  );
}

function HqPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [hq, setHq] = useState<HqCommandDTO | null>(null);
  const [error, run] = useLastError();
  const live = mode === "live";

  const refresh = useCallback(async () => {
    if (live) setHq(await client.hqCommand());
  }, [client, live]);
  useEffect(() => {
    void run(refresh);
  }, [refresh, run]);

  async function decide(requestId: string, approve: boolean) {
    await run(async () => {
      const result = await client.decide(requestId, approve);
      // Refresh before reporting: a refused decision leaves the item parked, so
      // the list must reflect the server either way rather than going stale
      // behind an error message.
      await refresh();
      // A decision can be refused for a reason the operator must see — most
      // often a parked item whose authority envelope changed across a restart.
      if (result.status && result.status !== "executed" && result.status !== "denied") {
        throw new Error(
          `${result.status}${result.reason ? `: ${result.reason}` : ""}`,
        );
      }
    });
  }

  if (!hq) return <section className="front-panel">HQ.Command — no live data.</section>;
  return (
    <section className="front-panel hq-panel">
      <h3>HQ.Command</h3>
      <h4>Runs</h4>
      <ul>
        {hq.runs.map((r) => (
          <li key={r.run_id}>
            <code>{r.run_id}</code> → <strong>{r.status}</strong> ({r.reason_code})
          </li>
        ))}
        {hq.runs.length === 0 ? <li className="empty">No runs.</li> : null}
      </ul>
      <h4>Approval inbox</h4>
      <ul className="pending-list">
        {hq.approvals.pending.map((p, i) => (
          // Show WHAT is being approved. A bare request id asks the operator to
          // authorise an action they cannot see; the tool, its risk class and
          // the proposer's own expected effect are what the decision is about.
          <li key={p.request_id || i} className="pending-item">
            <div className="pending-what">
              <span className={`risk risk-${p.risk}`}>{p.risk}</span>
              <code>{p.tool}</code>
              <span className="pending-summary">{p.summary}</span>
            </div>
            <div className="pending-meta">
              <code title="request id">{p.request_id}</code>
              <span title="issuing agent card">{p.issuer}</span>
              {p.mandate_id ? <span title="mandate">{p.mandate_id}</span> : null}
            </div>
            <div className="pending-actions">
              <button onClick={() => void decide(p.request_id, true)} disabled={!live}>
                Approve
              </button>
              <button onClick={() => void decide(p.request_id, false)} disabled={!live}>
                Deny
              </button>
            </div>
          </li>
        ))}
        {hq.approvals.pending.length === 0 ? (
          <li className="empty">
            No pending approvals ({hq.approvals.pending_source}).
          </li>
        ) : null}
      </ul>
      <ErrorBanner message={error} />
      <p className="seam">
        Budget: {String(hq.budget.status)} · Watchtower: {hq.watchtower.status} (
        {hq.watchtower.owner})
      </p>
    </section>
  );
}

function LibraryPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [lib, setLib] = useState<LibraryDTO | null>(null);
  const [error, run] = useLastError();
  useEffect(() => {
    if (mode === "live") void run(async () => setLib(await client.library()));
  }, [client, mode, run]);
  if (!lib) return <section className="front-panel">Library — no live data.</section>;
  return (
    <section className="front-panel library-panel">
      <h3>Library</h3>
      <p>
        min truth: <strong>{lib.min_truth_state ?? "—"}</strong> · manifest:{" "}
        {lib.manifest.status} · time-travel: {String(lib.claims_time_travel)}
      </p>
      <h4>Assets</h4>
      <ul>
        {lib.assets.map((a) => (
          <li key={a.doc_id}>
            {a.exists ? "present" : "missing"} <code>{a.doc_id}</code> — {a.path}
          </li>
        ))}
      </ul>
      <ErrorBanner message={error} />
    </section>
  );
}

function BoardPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [board, setBoard] = useState<BoardJournalDTO | null>(null);
  const [error, run] = useLastError();
  useEffect(() => {
    if (mode === "live") void run(async () => setBoard(await client.board()));
  }, [client, mode, run]);
  if (!board) return null;
  return (
    <section className="front-panel board-panel">
      <h3>Board journal</h3>
      <ul>
        {board.decisions.map((d) => (
          <li key={d.decision_id}>
            <strong>{d.title}</strong> — {d.proposed_tool} ({d.decided_by})
          </li>
        ))}
        {board.decisions.length === 0 ? <li className="empty">No decisions.</li> : null}
      </ul>
      <ErrorBanner message={error} />
    </section>
  );
}

function WorkOpsPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [tasks, setTasks] = useState<WorkOpsTasksDTO["tasks"]>([]);
  const [active, setActive] = useState<string>("task-1");
  const [error, run] = useLastError();
  useEffect(() => {
    if (mode === "live")
      void run(async () => {
        const t = await client.workopsTasks();
        setTasks(t.tasks);
        if (t.tasks[0]) setActive(t.tasks[0].task_id);
      });
  }, [client, mode, run]);
  return (
    <div className="workops">
      <ErrorBanner message={error} />
      <div className="task-list">
        <h4>Tasks</h4>
        <ul>
          {tasks.map((t) => (
            <li key={t.task_id}>
              <button onClick={() => setActive(t.task_id)}>
                {t.task_id} ({t.message_count})
              </button>
            </li>
          ))}
        </ul>
      </div>
      <ChatPanel
        client={client}
        mode={mode}
        room={`workops:${active}`}
        label={`WorkOPS — ${active}`}
      />
    </div>
  );
}

function AurelEUPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [au, setAu] = useState<AurelEUDTO | null>(null);
  const [error, run] = useLastError();
  useEffect(() => {
    if (mode === "live") void run(async () => setAu(await client.aureleu()));
  }, [client, mode, run]);
  if (!au) return null;
  return (
    <section className="front-panel aureleu-panel">
      <h3>AurelEU</h3>
      <p className="seam">
        dispatcher live: {String(au.claims_aureleu_dispatcher_live)} · verifier veto:{" "}
        {au.dn.verifier_veto} · dual-kernel: {String(au.dn.dual_kernel_enabled)}
      </p>
      <h4>Mandates</h4>
      <ul>
        {au.mandates.map((m) => (
          <li key={m}>
            <code>{m}</code>
          </li>
        ))}
        {au.mandates.length === 0 ? <li className="empty">No mandates bound.</li> : null}
      </ul>
      <h4>Delegation windows</h4>
      <ul>
        {au.delegations.map((d) => (
          <li key={d.delegation_id}>
            <code>{d.autonomy_ceiling}</code> by {d.granted_by}
          </li>
        ))}
        {au.delegations.length === 0 ? <li className="empty">No delegations.</li> : null}
      </ul>
      <ErrorBanner message={error} />
      {au.persona_switches.length ? (
        <p className="seam">
          persona: {au.persona_switches[au.persona_switches.length - 1].to}
        </p>
      ) : null}
    </section>
  );
}

/** CORP — the Business Plane: portfolio tree, cost/budget, alerts seam, KPIs. */
function CorpPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [pf, setPf] = useState<CorpPortfolioDTO | null>(null);
  const [kpi, setKpi] = useState<CorpKpiDTO | null>(null);
  const [error, run] = useLastError();
  useEffect(() => {
    if (mode === "live")
      void run(async () => {
        setPf(await client.corpPortfolio());
        setKpi(await client.corpKpi());
      });
  }, [client, mode, run]);

  if (!pf) return <section className="front-panel">Corp — no live data.</section>;
  return (
    <section className="front-panel corp-panel">
      <h3>Corp — Business Plane</h3>
      <p className="seam">
        cost: {String(pf.cost.status)} · budget-gov: {String(pf.budget_governance.status)} ·
        alerts: {pf.alerts.status}
        {typeof pf.alerts.count === "number" ? ` (${pf.alerts.count})` : ""}
      </p>
      <h4>Portfolio</h4>
      <ul className="corp-portfolio">
        {pf.clients.map((c) => (
          <li key={c.client_id}>
            <strong>{c.name}</strong> <code>{c.client_id}</code>
            <ul>
              {c.jobs.map((j) => (
                <li key={j.job_id}>
                  <code>{j.job_id}</code> — {j.title || "(untitled)"} [{j.status}] ·{" "}
                  {j.runs.length} run(s)
                </li>
              ))}
              {c.jobs.length === 0 ? <li className="empty">No jobs.</li> : null}
            </ul>
          </li>
        ))}
        {pf.clients.length === 0 ? <li className="empty">No clients.</li> : null}
      </ul>
      <ErrorBanner message={error} />
      {pf.unassigned.length ? (
        <p className="seam">unassigned runs: {pf.unassigned.length}</p>
      ) : null}
      <h4>Reflex Flywheel KPIs</h4>
      {kpi ? (
        <ul className="corp-kpi">
          <li>
            reflex hit rate:{" "}
            {kpi.reflex.status === "AVAILABLE" ? (
              <strong>{String((kpi.reflex as { rate?: number }).rate ?? "—")}</strong>
            ) : (
              <em>UNAVAILABLE ({String(kpi.reflex.reason ?? "")})</em>
            )}
          </li>
          <li>
            cost per task:{" "}
            {kpi.cost_per_task.status === "AVAILABLE" ? (
              <strong>
                {String((kpi.cost_per_task as { avg_cost_cents?: number }).avg_cost_cents ?? "—")}¢
                avg
              </strong>
            ) : (
              <em>UNAVAILABLE ({String(kpi.cost_per_task.reason ?? "")})</em>
            )}
          </li>
        </ul>
      ) : (
        <p className="empty">KPIs — no live data.</p>
      )}
    </section>
  );
}

export function FrontSurface({ surfaceId, client, mode }: SurfaceProps) {
  switch (surfaceId) {
    case "aurel_cro":
      return (
        <>
          <AurelEUPanel client={client} mode={mode} />
          <ChatPanel client={client} mode={mode} room="signal:main" label="Signal" />
        </>
      );
    case "ide":
      return <WorkOpsPanel client={client} mode={mode} />;
    case "hq":
      return (
        <>
          <HqPanel client={client} mode={mode} />
          <BoardPanel client={client} mode={mode} />
        </>
      );
    case "hub":
      return <LibraryPanel client={client} mode={mode} />;
    case "corp":
      return <CorpPanel client={client} mode={mode} />;
    case "system":
      return <SystemPanel client={client} mode={mode} />;
    default:
      return null;
  }
}
