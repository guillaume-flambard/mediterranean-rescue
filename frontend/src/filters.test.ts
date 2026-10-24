import { describe, it, expect } from "vitest";
import { makeFilter, dateLabel } from "./filters";
describe("REST filter inputs", () => {
  it("omits unspecified values rather than sending fake zeros", () => {
    expect(makeFilter("", "", "")).toEqual({});
    expect(makeFilter("2024-01-01", "", "rescue")).toEqual({
      start: "2024-01-01",
      kind: "rescue",
    });
  });
  it("formats dates without local timezone drift", () => {
    expect(dateLabel("2024-02-29")).toContain("29");
  });
});
