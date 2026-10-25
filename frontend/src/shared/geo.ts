import type { I18n } from "../i18n/I18nProvider";

// The hemisphere comes from the sign: a negative longitude is west of Greenwich.
export function formatPosition(i18n: Pick<I18n, "t" | "locale">, latitude: number, longitude: number): string {
  const decimals = (value: number) =>
    new Intl.NumberFormat(i18n.locale, { minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(Math.abs(value));
  const lat = i18n.t(latitude < 0 ? "geo.south" : "geo.north", { value: decimals(latitude) });
  const lon = i18n.t(longitude < 0 ? "geo.west" : "geo.east", { value: decimals(longitude) });
  return `${lat}, ${lon}`;
}
