import { describe, expect, it } from "vitest";
import { createI18n } from "../i18n/I18nProvider";
import { formatPosition } from "./geo";

describe("formatPosition", () => {
  it("derives the hemisphere from the sign", () => {
    expect(formatPosition(createI18n("en"), 39.4387, -0.3098)).toBe("39.439° N, 0.310° W");
    expect(formatPosition(createI18n("fr"), -12.5, 14.25)).toBe("12,500° S, 14,250° E");
    expect(formatPosition(createI18n("fr"), 39.4387, -0.3098)).toBe("39,439° N, 0,310° O");
  });
});
