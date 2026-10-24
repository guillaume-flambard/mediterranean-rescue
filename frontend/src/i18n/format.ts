// Message formatting without a runtime dependency: `{name}` placeholders and plural forms
// selected with Intl.PluralRules. Catalog values are plain data so translators can edit them.

export type PluralForms = { readonly one: string; readonly other: string; readonly zero?: string };
export type Message = string | PluralForms;
export type Params = Readonly<Record<string, string | number>>;

export const LOCALES = ["en", "fr"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && (LOCALES as readonly string[]).includes(value);
}

export function formatMessage(locale: Locale, message: Message, params: Params = {}): string {
  let template: string;
  if (typeof message === "string") {
    template = message;
  } else {
    const count = Number(params.count);
    if (!Number.isFinite(count)) throw new Error("Plural message needs a numeric count");
    const category = new Intl.PluralRules(locale).select(count);
    template =
      count === 0 && message.zero !== undefined
        ? message.zero
        : category === "one"
          ? message.one
          : message.other;
  }
  return template.replace(/\{(\w+)\}/g, (match, name: string) => {
    const value = params[name];
    if (value === undefined) return match;
    return typeof value === "number" ? new Intl.NumberFormat(locale).format(value) : value;
  });
}

// Dates without time ("YYYY-MM-DD") are calendar dates: format them in UTC so the local
// time zone can never move them to the previous or next day.
export function formatDate(locale: Locale, isoDate: string, style: "medium" | "long" = "medium") {
  return new Intl.DateTimeFormat(locale, { dateStyle: style, timeZone: "UTC" }).format(
    new Date(`${isoDate}T00:00:00Z`),
  );
}
