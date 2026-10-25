import { describe, expect, it } from "vitest";
import { makeFilter } from "./filters";

describe("REST filter inputs", () => {
  it("omits unspecified values rather than sending fake zeros", () => {
    expect(makeFilter("", "", "")).toEqual({});
    expect(makeFilter("2024-01-01", "", "rescue")).toEqual({ start: "2024-01-01", kind: "rescue" });
  });
});
