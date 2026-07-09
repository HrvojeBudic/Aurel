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
import type {
  BoardJournalDTO,
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
    void refresh();
  }, [refresh]);

  async function send() {
    if (!draft.trim() || busy) return;
    setBusy(true);
    try {
      await client.propose({
        kind: "converse",
        room_id: room,
        operator_identity: "operator",
        role: "operator",
        mandate_id: "default",
        text: draft,
      });
      setDraft("");
      await refresh();
    } finally {
      setBusy(false);
    }
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
    </section>
  );
}

function HqPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [hq, setHq] = useState<HqCommandDTO | null>(null);
  const live = mode === "live";

  const refresh = useCallback(async () => {
    if (live) setHq(await client.hqCommand());
  }, [client, live]);
  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function decide(requestId: string, approve: boolean) {
    await client.decide(requestId, approve);
    await refresh();
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
      <ul>
        {hq.approvals.pending.map((p, i) => {
          const rid = String((p as { request_id?: string }).request_id ?? "");
          return (
            <li key={rid || i}>
              <code>{rid}</code>
              <button onClick={() => void decide(rid, true)} disabled={!live}>
                Approve
              </button>
              <button onClick={() => void decide(rid, false)} disabled={!live}>
                Deny
              </button>
            </li>
          );
        })}
        {hq.approvals.pending.length === 0 ? (
          <li className="empty">
            No pending approvals ({hq.approvals.pending_source}).
          </li>
        ) : null}
      </ul>
      <p className="seam">
        Budget: {String(hq.budget.status)} · Watchtower: {hq.watchtower.status} (
        {hq.watchtower.owner})
      </p>
    </section>
  );
}

function LibraryPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [lib, setLib] = useState<LibraryDTO | null>(null);
  useEffect(() => {
    if (mode === "live") void client.library().then(setLib);
  }, [client, mode]);
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
    </section>
  );
}

function BoardPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [board, setBoard] = useState<BoardJournalDTO | null>(null);
  useEffect(() => {
    if (mode === "live") void client.board().then(setBoard);
  }, [client, mode]);
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
    </section>
  );
}

function WorkOpsPanel({ client, mode }: { client: FrontClient; mode: FrontMode }) {
  const [tasks, setTasks] = useState<WorkOpsTasksDTO["tasks"]>([]);
  const [active, setActive] = useState<string>("task-1");
  useEffect(() => {
    if (mode === "live")
      void client.workopsTasks().then((t) => {
        setTasks(t.tasks);
        if (t.tasks[0]) setActive(t.tasks[0].task_id);
      });
  }, [client, mode]);
  return (
    <div className="workops">
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

export function FrontSurface({ surfaceId, client, mode }: SurfaceProps) {
  switch (surfaceId) {
    case "aurel_cro":
      return <ChatPanel client={client} mode={mode} room="signal:main" label="Signal" />;
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
    default:
      return null;
  }
}
