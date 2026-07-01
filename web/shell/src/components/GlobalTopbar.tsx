import type { WebShellSurfaceViewDTO } from "../types";

interface Props {
  surfaces: WebShellSurfaceViewDTO[];
  activeSurfaceId: string;
  onSelect: (surfaceId: string) => void;
}

export function SurfaceSelector({
  surfaces,
  activeSurfaceId,
  onSelect,
}: Props) {
  const selectorSurfaces = surfaces.filter((s) => s.in_surface_selector);
  const rightSurfaces = surfaces.filter((s) => s.in_topbar_right);

  return (
    <header className="global-topbar">
      <div className="topbar-left">
        <strong className="shell-title">Aurel Shell</strong>
        <nav className="surface-selector" aria-label="Surface selector">
          {selectorSurfaces.map((surface) => (
            <button
              key={surface.surface_id}
              type="button"
              className={
                surface.surface_id === activeSurfaceId
                  ? "surface-btn active"
                  : "surface-btn"
              }
              onClick={() => onSelect(surface.surface_id)}
              disabled={!surface.available}
            >
              {surface.surface_label}
            </button>
          ))}
        </nav>
      </div>
      <div className="topbar-right">
        {rightSurfaces.map((surface) => (
          <button
            key={surface.surface_id}
            type="button"
            className={
              surface.surface_id === activeSurfaceId
                ? "surface-btn active"
                : "surface-btn"
            }
            onClick={() => onSelect(surface.surface_id)}
            disabled={!surface.available}
          >
            {surface.surface_label}
          </button>
        ))}
      </div>
    </header>
  );
}
