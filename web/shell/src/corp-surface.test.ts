import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = resolve(import.meta.dirname);

describe("F7.9 CORP surface — reads through the one door, honest seams", () => {
  it("frontClient exposes corp read builders (corp/portfolio + corp/kpi)", () => {
    const text = readFileSync(resolve(SRC, "frontClient.ts"), "utf-8");
    expect(text).toMatch(/corpPortfolio\(/);
    expect(text).toMatch(/corpKpi\(/);
    expect(text).toMatch(/"corp\/portfolio"/);
    expect(text).toMatch(/"corp\/kpi"/);
  });

  it("CorpPanel reads only through frontClient (no direct fetch/WebSocket)", () => {
    const text = readFileSync(resolve(SRC, "components/front/FrontSurface.tsx"), "utf-8");
    expect(text).toMatch(/function CorpPanel/);
    expect(text).toMatch(/client\.corpPortfolio\(/);
    expect(text).toMatch(/client\.corpKpi\(/);
    // the one-door law: the surface never touches fetch or WebSocket itself
    expect(/\bfetch\s*\(/.test(text)).toBe(false);
    expect(/new\s+WebSocket\s*\(/.test(text)).toBe(false);
  });

  it("CorpPanel is wired for the corp surface and shows UNAVAILABLE seams honestly", () => {
    const text = readFileSync(resolve(SRC, "components/front/FrontSurface.tsx"), "utf-8");
    expect(text).toMatch(/case "corp":/);
    // KPIs render UNAVAILABLE when the backend reports it — never a faked value
    expect(text).toMatch(/UNAVAILABLE/);
  });
});
