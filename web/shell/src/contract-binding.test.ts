import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { WebShellReadModelDTO } from "./types";
import { SURFACE_SELECTOR_IDS, TOPBAR_RIGHT_IDS } from "./types";

const FIXTURE_PATH = resolve(
  import.meta.dirname,
  "../public/web-shell-read-model.json",
);

function loadFixture(): WebShellReadModelDTO {
  return JSON.parse(readFileSync(FIXTURE_PATH, "utf-8")) as WebShellReadModelDTO;
}

describe("web shell contract binding", () => {
  it("loads Python-generated fixture", () => {
    const model = loadFixture();
    expect(model.pack_id).toBe("P2.10-B");
    expect(model.client_status.active_client).toBe("WEB");
  });

  it("preserves seven canonical surfaces from contract", () => {
    const model = loadFixture();
    expect(model.surfaces).toHaveLength(7);
    const ids = model.surfaces.map((s) => s.surface_id).sort();
    expect(ids).toEqual([
      "aurel_cro",
      "corp",
      "hq",
      "hub",
      "ide",
      "settings",
      "system",
    ]);
  });

  it("maps surface selector and topbar-right slots from contract", () => {
    const model = loadFixture();
    const selector = model.surfaces
      .filter((s) => s.in_surface_selector)
      .map((s) => s.surface_id);
    const right = model.surfaces
      .filter((s) => s.in_topbar_right)
      .map((s) => s.surface_id);
    expect(selector).toEqual([...SURFACE_SELECTOR_IDS]);
    expect(right).toEqual([...TOPBAR_RIGHT_IDS]);
  });

  it("keeps P2.VSLICE-A and command palette PREFLIGHT_ONLY", () => {
    const model = loadFixture();
    expect(model.p2_vslice_a_status).toBe("PREFLIGHT_ONLY");
    expect(model.command_palette_availability).toBe("PREFLIGHT_ONLY");
  });

  it("does not claim Shell LIVE or command execution", () => {
    const model = loadFixture();
    expect(model.truth_labels).not.toContain("LIVE");
    const forbidden = model.no_overclaim_boundaries.map((b) => b.forbidden_claim);
    expect(forbidden).toContain("Shell LIVE");
    expect(forbidden).toContain("arbitrary command execution");
  });

  it("points next pack to P2.10-C", () => {
    const model = loadFixture();
    expect(model.next_pack).toBe("P2.10-C");
    expect(model.p210c_not_started).toBe(true);
    expect(model.p210d_not_started).toBe(true);
  });
});
