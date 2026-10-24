import type { EventFilter, Kind } from "./api/client";
export const kinds: readonly { value: Kind; label: string }[] = [
  { value: "rescue", label: "Sauvetages" },
  { value: "transfer", label: "Transferts" },
  { value: "medevac", label: "Évacuations médicales" },
  { value: "incident", label: "Incidents" },
  { value: "shipwreck", label: "Naufrages" },
  { value: "dead_missing", label: "Décès et disparitions" },
];
export function kindLabel(value: Kind) {
  return kinds.find((k) => k.value === value)?.label ?? value;
}
export function makeFilter(
  start: string,
  end: string,
  kind: Kind | "",
): EventFilter {
  return {
    ...(start ? { start } : {}),
    ...(end ? { end } : {}),
    ...(kind ? { kind } : {}),
  };
}
export function dateLabel(value: string) {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(new Date(value + "T00:00:00Z"));
}
