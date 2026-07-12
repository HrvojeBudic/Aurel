import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = resolve(import.meta.dirname);

describe("F8.5 System surface — reads through the one door, honest seams", () => {
  it("frontClient exposes system read builders", () => {
    const text = readFileSync(resolve(SRC, "frontClient.ts"), "utf-8");
    expect(text).toMatch(/systemAudit\(/);
    expect(text).toMatch(/systemUsage\(/);
    expect(text).toMatch(/systemModelRouting\(/);
    expect(text).toMatch(/systemPolicies\(/);
    expect(text).toMatch(/systemArchive\(/);
    expect(text).toMatch(/"system\/audit"/);
    expect(text).toMatch(/"system\/archive"/);
  });

  it("SystemPanel reads only through frontClient (no direct fetch/WebSocket)", () => {
    const panel = readFileSync(resolve(SRC, "components/front/SystemPanel.tsx"), "utf-8");
    expect(panel).toMatch(/client\.systemAudit\(/);
    expect(panel).toMatch(/client\.systemUsage\(/);
    expect(panel).toMatch(/client\.systemArchive\(/);
    expect(/\bfetch\s*\(/.test(panel)).toBe(false);
    expect(/new\s+WebSocket\s*\(/.test(panel)).toBe(false);
  });

  it("SystemPanel is wired for the system surface", () => {
    const surface = readFileSync(resolve(SRC, "components/front/FrontSurface.tsx"), "utf-8");
    expect(surface).toMatch(/case "system":/);
    expect(surface).toMatch(/SystemPanel/);
    expect(surface).toMatch(/UNAVAILABLE/);
  });
});
