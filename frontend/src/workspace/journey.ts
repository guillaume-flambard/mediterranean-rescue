// A volunteer's first steps, remembered on this browser only: a convenience, never a record. The
// real progress (decisions recorded) comes from the server.
const KEYS = {
  intro: "team-intro-dismissed",
  practice: "team-practice-done",
  publishGuide: "team-publish-guide-seen",
} as const;

export type JourneyKey = keyof typeof KEYS;

export function journeyDone(key: JourneyKey) {
  try {
    return window.localStorage.getItem(KEYS[key]) === "1";
  } catch {
    return false;
  }
}

export function markJourney(key: JourneyKey) {
  try {
    window.localStorage.setItem(KEYS[key], "1");
  } catch {
    // Blocked storage: the step simply shows as not done yet.
  }
}
