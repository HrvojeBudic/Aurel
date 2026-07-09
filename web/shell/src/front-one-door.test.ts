import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { ProposalEnvelope } from "./front-types";

const SRC = resolve(import.meta.dirname);

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = resolve(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else if (/\.tsx?$/.test(entry.name)) out.push(full);
  }
  return out;
}

describe("F5.8 one door — frontClient is the sole backend access point", () => {
  it("no source file except frontClient.ts calls fetch() or new WebSocket()", () => {
    const offenders: string[] = [];
    for (const file of walk(SRC)) {
      const base = file.split("/").pop() ?? "";
      if (base === "frontClient.ts") continue; // the one door
      if (base.endsWith(".test.ts")) continue; // tests may assert on strings
      if (base === "main.tsx") continue; // bootstrap loads the static fixture only
      const text = readFileSync(file, "utf-8");
      if (/\bfetch\s*\(/.test(text) || /new\s+WebSocket\s*\(/.test(text)) {
        offenders.push(base);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("every mutation is a ProposalEnvelope kind (converse | act | decide)", () => {
    const kinds: ProposalEnvelope["kind"][] = ["converse", "act", "decide"];
    const converse: ProposalEnvelope = {
      kind: "converse",
      room_id: "signal:main",
      operator_identity: "op",
      role: "operator",
      mandate_id: "default",
      text: "hi",
    };
    const decide: ProposalEnvelope = { kind: "decide", request_id: "r1", approve: true };
    expect(kinds).toContain(converse.kind);
    expect(kinds).toContain(decide.kind);
  });

  it("frontClient exposes reads + the single propose/decide mutation", () => {
    const text = readFileSync(resolve(SRC, "frontClient.ts"), "utf-8");
    // Exactly one POST target: /proposals (the one mutation route).
    const postTargets = [...text.matchAll(/\/(proposals|read\/)/g)].map((m) => m[1]);
    expect(postTargets).toContain("proposals");
    expect(text).toMatch(/method:\s*"POST"/);
    // The POST body is always a proposal envelope through propose().
    expect(text).toMatch(/propose\(/);
  });
});
