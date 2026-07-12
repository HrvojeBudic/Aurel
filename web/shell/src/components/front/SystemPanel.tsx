/**
 * SystemPanel.tsx — operator System surface (F8.5).
 *
 * Reads audit, usage, model routing, policy browser, and archive status through
 * frontClient only. Zero direct fetch/WebSocket. Fixture mode ⇒ honest empty state.
 */
import { useEffect, useState } from "react";
import type { FrontClient, FrontMode } from "../../frontClient";
import type {
  SystemArchiveDTO,
  SystemAuditDTO,
  SystemModelRoutingDTO,
  SystemPoliciesDTO,
  SystemUsageDTO,
} from "../../front-types";

interface Props {
  client: FrontClient;
  mode: FrontMode;
}

function Unavailable({ label, reason }: { label: string; reason?: string }) {
  return (
    <p className="seam">
      {label}: <em>UNAVAILABLE{reason ? ` (${reason})` : ""}</em>
    </p>
  );
}

export function SystemPanel({ client, mode }: Props) {
  const [audit, setAudit] = useState<SystemAuditDTO | null>(null);
  const [usage, setUsage] = useState<SystemUsageDTO | null>(null);
  const [routing, setRouting] = useState<SystemModelRoutingDTO | null>(null);
  const [policies, setPolicies] = useState<SystemPoliciesDTO | null>(null);
  const [archive, setArchive] = useState<SystemArchiveDTO | null>(null);
  const live = mode === "live";

  useEffect(() => {
    if (!live) return;
    void Promise.all([
      client.systemAudit({ limit: "20" }),
      client.systemUsage(),
      client.systemModelRouting(),
      client.systemPolicies(),
      client.systemArchive(),
    ]).then(([a, u, r, p, ar]) => {
      setAudit(a);
      setUsage(u);
      setRouting(r);
      setPolicies(p);
      setArchive(ar);
    });
  }, [client, live]);

  if (!live || !audit) {
    return <section className="front-panel">System — no live data.</section>;
  }

  return (
    <section className="front-panel system-panel">
      <h3>System — operator forensics</h3>
      <p className="seam">operator-only · read-only · zero writes</p>

      <h4>Audit log</h4>
      {audit.available ? (
        <ul className="system-audit">
          {audit.events.slice(0, 10).map((ev, i) => (
            <li key={String((ev as { entry_hash?: string }).entry_hash ?? i)}>
              <code>{String((ev as { kind?: string }).kind ?? "event")}</code>{" "}
              {String((ev as { action?: string }).action ?? "")}
            </li>
          ))}
          {(audit.events?.length ?? 0) === 0 ? (
            <li className="empty">No audit events.</li>
          ) : null}
        </ul>
      ) : (
        <Unavailable label="Audit" reason={audit.reason} />
      )}

      <h4>Usage / quotas</h4>
      {usage?.available ? (
        <p className="seam">
          mandates tracked: {usage.by_mandate?.length ?? 0} · agents:{" "}
          {usage.by_agent?.length ?? 0}
        </p>
      ) : (
        <Unavailable label="Usage" reason={usage?.reason} />
      )}

      <h4>Model routing</h4>
      {routing?.available ? (
        <p className="seam">
          profiles: {Object.keys(routing.profiles ?? {}).length} · promotion gates:{" "}
          {String(routing.promotion_gates?.grants_authority ?? false) === "false"
            ? "evidence-only"
            : "—"}
        </p>
      ) : (
        <Unavailable label="Model routing" reason={routing?.reason} />
      )}

      <h4>Policy cards</h4>
      {policies?.available ? (
        <ul className="system-policies">
          {(policies.cards ?? []).map((c, i) => (
            <li key={String(c.card_id ?? i)}>
              <code>{String(c.card_id ?? "card")}</code>{" "}
              {String(c.canonical_hash ?? "").slice(0, 12)}…
            </li>
          ))}
          {(policies.cards?.length ?? 0) === 0 ? (
            <li className="empty">No policy cards bound.</li>
          ) : null}
        </ul>
      ) : (
        <Unavailable label="Policies" reason={policies?.reason} />
      )}

      <h4>Archive status</h4>
      {archive?.available ? (
        <p className="seam">
          persistence: {String(archive.persistence?.ok ?? "—")} · integrity:{" "}
          {String(archive.integrity?.status ?? "UNAVAILABLE")} · export manifest:{" "}
          {String(archive.export_manifest?.status ?? archive.export_manifest?.available ?? "—")}
        </p>
      ) : (
        <Unavailable label="Archive" reason={archive?.reason} />
      )}
    </section>
  );
}
