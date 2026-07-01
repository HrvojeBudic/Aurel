import { DesktopWrapperPanel } from "./components/DesktopWrapperPanel";
import { AppShell } from "./App";
import type { DesktopShellViewDTO } from "./desktop-types";

interface Props {
  view: DesktopShellViewDTO;
}

export function DesktopAppShell({ view }: Props) {
  return (
    <div className="desktop-app-shell">
      <DesktopWrapperPanel desktop={view.desktop} />
      <AppShell model={view.web} />
    </div>
  );
}
