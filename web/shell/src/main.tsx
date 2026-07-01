import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AppShell } from "./App";
import { DesktopAppShell } from "./DesktopApp";
import type { DesktopShellReadModelDTO } from "./desktop-types";
import type { WebShellReadModelDTO } from "./types";
import "./styles.css";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function loadDesktopView(): Promise<{
  desktop: DesktopShellReadModelDTO;
  web: WebShellReadModelDTO;
} | null> {
  try {
    const desktop = await fetchJson<DesktopShellReadModelDTO>(
      "/desktop-shell-read-model.json",
    );
    const web = await fetchJson<WebShellReadModelDTO>(
      "/web-shell-read-model.json",
    );
    return { desktop, web };
  } catch {
    return null;
  }
}

async function loadWebModel(): Promise<WebShellReadModelDTO> {
  return fetchJson<WebShellReadModelDTO>("/web-shell-read-model.json");
}

function renderApp(node: HTMLElement, content: React.ReactNode) {
  createRoot(node).render(<StrictMode>{content}</StrictMode>);
}

function isTauriRuntime(): boolean {
  return "__TAURI_INTERNALS__" in window;
}

async function bootstrap() {
  const root = document.getElementById("root");
  if (!root) {
    throw new Error("Missing #root element");
  }

  const params = new URLSearchParams(window.location.search);
  const desktopMode = params.get("desktop") === "1" || isTauriRuntime();

  if (desktopMode) {
    const view = await loadDesktopView();
    if (view) {
      renderApp(root, <DesktopAppShell view={view} />);
      return;
    }
  }

  const webModel = await loadWebModel();
  renderApp(root, <AppShell model={webModel} />);
}

bootstrap().catch((error: unknown) => {
  const root = document.getElementById("root");
  if (root) {
    root.textContent =
      error instanceof Error ? error.message : "Failed to load read model";
  }
});
