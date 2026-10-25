import type { I18n } from "../i18n/I18nProvider";

export type Key = Parameters<I18n["t"]>[0];

/** "110 people rescued", "3 people evacuated": the count says what happened to the people. */
export function peopleText(i18n: I18n, kind: string | null, people: number | null) {
  if (people === null) return i18n.t("explore.people.unknown");
  const verb = ["rescue", "transfer", "medevac"].includes(kind ?? "") ? kind : "other";
  return i18n.t(`explore.people.${verb}` as Key, { count: people });
}

/** Which Google Sheets tab a record comes from, in words. */
export function sheetName(i18n: I18n, sheet: string) {
  const key = `explore.sheet.${sheet}` as Key;
  const label = i18n.t(key);
  return label === key ? sheet : label;
}

/** The singular name of one event's kind ("Rescue"), as opposed to the plural filter label. */
export function kindName(i18n: I18n, kind: string | null) {
  if (!kind) return i18n.t("review.unknown");
  const key = `kindOne.${kind}` as Key;
  const label = i18n.t(key);
  return label === key ? kind : label;
}

export function kindLabel(i18n: I18n, kind: string | null) {
  if (!kind) return i18n.t("review.unknown");
  const key = `kind.${kind}` as Key;
  const label = i18n.t(key);
  return label === key ? kind : label;
}

