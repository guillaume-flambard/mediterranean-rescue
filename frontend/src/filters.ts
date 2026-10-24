import type { EventFilter, Kind } from "./gql/graphql";
export const kinds: readonly { value: Kind; label: string }[] = [
  { value: "RESCUE", label: "Sauvetages" },
  { value: "TRANSFER", label: "Transferts" },
  { value: "MEDEVAC", label: "Évacuations médicales" },
  { value: "INCIDENT", label: "Incidents" },
  { value: "SHIPWRECK", label: "Naufrages" },
  { value: "DEAD_MISSING", label: "Décès et disparitions" },
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
