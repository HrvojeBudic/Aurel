import { useEffect, useMemo, useState } from "react";
import type { WebShellReadModelDTO } from "./types";
import { SurfaceSelector } from "./components/GlobalTopbar";
import { SurfacePanel } from "./components/SurfacePanel";
import { ClientStatusPanel } from "./components/ClientStatusPanel";
import { EvidenceRefsPanel } from "./components/EvidenceRefsPanel";
import { NoOverclaimPanel } from "./components/NoOverclaimPanel";
import { FrontSurface } from "./components/front/FrontSurface";
import { frontClient, type FrontMode } from "./frontClient";

interface Props {
  model: WebShellReadModelDTO;
}

export function AppShell({ model }: Props) {
  const [frontMode, setFrontMode] = useState<FrontMode>("fixture");
  useEffect(() => {
    void frontClient.connect().then(setFrontMode);
  }, []);
  const defaultSurface =
    model.surfaces.find((s) => s.in_surface_selector)?.surface_id ??
    model.surfaces[0]?.surface_id ??
    "aurel_cro";
  const [activeSurfaceId, setActiveSurfaceId] = useState(defaultSurface);

  const activeSurface = useMemo(
    () =>
      model.surfaces.find((s) => s.surface_id === activeSurfaceId) ??
      model.surfaces[0],
    [model.surfaces, activeSurfaceId],
  );

  if (!activeSurface) {
    return <p>No surfaces in contract read model.</p>;
  }

  return (
    <div className="app-shell">
      <header className="page-header">
        <h1>{model.title}</h1>
        <p className="pack-id">
          {model.pack_id} — contract-bound read model (not Shell LIVE)
        </p>
        <p className={`front-mode front-mode-${frontMode}`}>
          Front server:{" "}
          {frontMode === "live"
            ? "LIVE (one door)"
            : "read-only fixture mode — proposals disabled"}
        </p>
      </header>

      <SurfaceSelector
        surfaces={model.surfaces}
        activeSurfaceId={activeSurfaceId}
        onSelect={setActiveSurfaceId}
      />

      <main className="shell-main">
        <aside className="shell-left stub">
          <p>Per-surface left nav stub (contract only)</p>
        </aside>

        <div className="shell-center">
          <SurfacePanel surface={activeSurface} />
          <FrontSurface
            surfaceId={activeSurface.surface_id}
            client={frontClient}
            mode={frontMode}
          />
          <ClientStatusPanel status={model.client_status} />
        </div>

        <aside className="shell-right">
          <EvidenceRefsPanel evidenceRefs={model.evidence_refs} />
          <NoOverclaimPanel
            boundaries={model.no_overclaim_boundaries}
            truthLabels={model.truth_labels}
            commandPaletteAvailability={model.command_palette_availability}
            p2VsliceAStatus={model.p2_vslice_a_status}
            limitations={model.limitations}
            nextPack={model.next_pack}
          />
        </aside>
      </main>
    </div>
  );
}
