import type { EventFilter, Kind } from "./api/client";

export const kinds: readonly Kind[] = ["rescue", "transfer", "medevac", "incident", "shipwreck", "dead_missing"];

export function makeFilter(start: string, end: string, kind: Kind | ""): EventFilter {
  return {
    ...(start ? { start } : {}),
    ...(end ? { end } : {}),
    ...(kind ? { kind } : {}),
  };
}
