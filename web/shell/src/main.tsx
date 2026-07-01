import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AppShell } from "./App";
import type { WebShellReadModelDTO } from "./types";
import "./styles.css";

async function loadReadModel(): Promise<WebShellReadModelDTO> {
  const response = await fetch("/web-shell-read-model.json");
  if (!response.ok) {
    throw new Error(
      `Failed to load web-shell-read-model.json: ${response.status}`,
    );
  }
  return response.json() as Promise<WebShellReadModelDTO>;
}

loadReadModel()
  .then((model) => {
    const root = document.getElementById("root");
    if (!root) {
      throw new Error("Missing #root element");
    }
    createRoot(root).render(
      <StrictMode>
        <AppShell model={model} />
      </StrictMode>,
    );
  })
  .catch((error: unknown) => {
    const root = document.getElementById("root");
    if (root) {
      root.textContent =
        error instanceof Error ? error.message : "Failed to load read model";
    }
  });
