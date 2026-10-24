import { describe, expect, it } from "vitest";
import { en } from "./en";
import { DEFAULT_LOCALE, formatDate, formatMessage } from "./format";
import { fr } from "./fr";
import { DEV_MESSAGES } from "../dev/messages";
import { createI18n } from "./I18nProvider";

const placeholders = (message: unknown): string[] => {
  const text = typeof message === "string" ? message : Object.values(message as object).join(" ");
  return [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1] ?? "").sort();
};

describe("catalogs", () => {
  it("defaults to English", () => {
    expect(DEFAULT_LOCALE).toBe("en");
  });

  it("French has exactly the English keys, placeholders and plural shapes", () => {
    expect(Object.keys(fr).sort()).toEqual(Object.keys(en).sort());
    for (const key of Object.keys(en) as (keyof typeof en)[]) {
      expect(placeholders(fr[key]), key).toEqual(placeholders(en[key]));
      expect(typeof fr[key], key).toBe(typeof en[key]);
      const text = typeof fr[key] === "string" ? fr[key] : Object.values(fr[key]).join("");
      expect(text.trim(), key).not.toBe("");
    }
  });

  it("uses no em or en dash in product copy", () => {
    for (const catalog of [en, fr]) {
      expect(JSON.stringify(catalog)).not.toMatch(/[\u2013\u2014]/);
    }
  });
});

describe("formatMessage", () => {
  it("selects plural forms with the locale rules", () => {
    expect(formatMessage("en", en["events.count"], { count: 0 })).toBe("0 events");
    expect(formatMessage("en", en["events.count"], { count: 1 })).toBe("1 event");
    // French treats 0 as singular.
    expect(formatMessage("fr", fr["events.count"], { count: 0 })).toBe("0 événement");
    expect(formatMessage("fr", fr["events.count"], { count: 2 })).toBe("2 événements");
  });

  it("formats numbers per locale and keeps unknown placeholders visible", () => {
    expect(formatMessage("en", "{count} rows", { count: 1234 })).toBe("1,234 rows");
    expect(formatMessage("fr", "{count} lignes", { count: 1234 })).toBe("1 234 lignes");
    expect(formatMessage("en", "Hello {name}")).toBe("Hello {name}");
  });

  it("refuses a plural message without a count", () => {
    expect(() => formatMessage("en", en["events.count"])).toThrow();
  });
});

describe("formatDate", () => {
  it("keeps calendar dates on their day whatever the time zone", () => {
    expect(formatDate("en", "2024-02-29")).toBe("Feb 29, 2024");
    expect(formatDate("fr", "2024-01-01", "long")).toBe("1er janvier 2024");
  });
});


describe("fallbacks and development texts", () => {
  it("shows an unknown key instead of crashing", () => {
    const t = createI18n("fr").t as (key: string) => string;
    expect(t("kind.new_server_value")).toBe("kind.new_server_value");
  });

  it("keeps the development catalog out of the product catalogs, with both languages", () => {
    expect(Object.keys(en).some((key) => key.startsWith("catalog."))).toBe(false);
    expect(Object.keys(DEV_MESSAGES.fr).sort()).toEqual(Object.keys(DEV_MESSAGES.en).sort());
  });
});
