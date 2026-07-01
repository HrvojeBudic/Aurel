import { describe, expect, it } from "vitest";
import desktopFixture from "../public/desktop-shell-read-model.json";
import webFixture from "../public/web-shell-read-model.json";
import type { DesktopShellReadModelDTO } from "./desktop-types";

const desktop = desktopFixture as DesktopShellReadModelDTO;

describe("P2.10-C desktop contract binding", () => {
  it("uses DESKTOP_TAURI as active client", () => {
    expect(desktop.desktop_client_status.active_client).toBe("DESKTOP_TAURI");
    expect(desktop.desktop_client_status.wrapped_client_kind).toBe("WEB");
  });

  it("wraps the P2.10-B web read model hash", () => {
    expect(desktop.wrapped_web_shell_status.source_read_model_hash).toBe(
      webFixture.read_model_hash,
    );
  });

  it("points next pack to P2.10-D", () => {
    expect(desktop.next_pack_pointer).toBe("P2.10-D");
    expect(desktop.p210d_not_started).toBe(true);
  });

  it("keeps P2.VSLICE-A preflight-only", () => {
    expect(desktop.p2_vslice_status).toBe("PREFLIGHT_ONLY");
  });

  it("disables native file and shell capabilities", () => {
    const disabled = desktop.capability_boundary.disabled_capabilities.map(
      (entry) => entry.capability,
    );
    expect(disabled).toContain("NATIVE_FILE_READ");
    expect(disabled).toContain("NATIVE_SHELL_EXEC");
  });
});
