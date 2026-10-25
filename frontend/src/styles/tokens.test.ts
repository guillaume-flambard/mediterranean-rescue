import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const read = (relative: string) => readFileSync(fileURLToPath(new URL(relative, import.meta.url)), "utf8");
const declarations = (css: string) => css.split("\n").filter((line) => /^\s*--[\w-]+:/.test(line)).map((line) => line.trim());

describe("design tokens", () => {
  it("are the reference tokens of docs/design, unchanged", () => {
    const app = declarations(read("./tokens.css"));
    const reference = declarations(read("../../../docs/design/tokens.css"));
    expect(app.length).toBeGreaterThan(100);
    expect(app).toEqual(reference);
  });
});
