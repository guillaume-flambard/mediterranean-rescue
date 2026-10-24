import type { I18n } from "../i18n/I18nProvider";

type Key = Parameters<I18n["t"]>[0];

const MATERIALS: Record<string, string> = {
  rubber: "rubber",
  wooden: "wooden",
  woodent: "wooden",
  wood: "wooden",
  fiberglass: "fiberglass",
  fibreglass: "fiberglass",
  fiber: "fiberglass",
  fibre: "fiberglass",
  fibber: "fiberglass",
  steel: "metal",
  iron: "metal",
  metal: "metal",
  pleasure: "pleasure",
  multi: "multi",
};
const COLOURS: Record<string, string> = {
  white: "white",
  grey: "grey",
  gray: "grey",
  black: "black",
  blue: "blue",
  green: "green",
  red: "red",
  yellow: "yellow",
  orange: "orange",
  brown: "brown",
};
// Words that only complete a material ("fiber glass", "pleasure craft", "multi-type").
const FILLERS: Record<string, string> = { glass: "fiberglass", craft: "pleasure", type: "multi" };

export interface Boat {
  count: number;
  material: string;
  size: "small" | "medium" | null;
  colours: string[];
}

/** Reads the sheet's free text ("Rubber boat (white & black)", "2 Rubber Boats", "Blue wooden
 * boat"). Returns null as soon as one word is not understood: the text is then shown as written. */
export function parseBoat(text: string): Boat | null {
  const words = text.toLowerCase().replace(/&/g, " and ").split(/[\s()/,-]+/).filter(Boolean);
  const boat: Boat = { count: 1, material: "", size: null, colours: [] };
  const fillers: string[] = [];
  for (const [index, word] of words.entries()) {
    if (index === 0 && /^\d{1,2}$/.test(word)) boat.count = Number(word);
    else if (word === "small" || word === "medium") boat.size = word;
    else if (MATERIALS[word]) {
      // "Steel / Iron boat" names one material twice; two different ones are not one boat type.
      if (boat.material && boat.material !== MATERIALS[word]) return null;
      boat.material = MATERIALS[word];
    }
    else if (COLOURS[word]) {
      if (!boat.colours.includes(COLOURS[word])) boat.colours.push(COLOURS[word]);
    } else if (FILLERS[word]) fillers.push(FILLERS[word]);
    else if (word !== "boat" && word !== "boats" && word !== "and") return null;
  }
  if (!boat.material || fillers.some((material) => material !== boat.material)) return null;
  return boat;
}

/** The boat in the reader's language; the text as written when it cannot be read with certainty. */
export function boatLabel(i18n: I18n, text: string | null | undefined): string | null {
  if (!text) return null;
  const boat = parseBoat(text);
  if (!boat) return text;
  const { t } = i18n;
  const count = boat.count;
  let label = t(`boat.${boat.material}` as Key, { count });
  if (boat.size) label = t(`boat.size.${boat.size}` as Key, { boat: label });
  if (count > 1) label = t("boat.count", { count, boat: label });
  if (boat.colours.length && boat.material !== "multi") {
    const colours = boat.colours.map((colour) => t(`boat.colour.${colour}` as Key, { count }));
    const joined = colours.length > 1 ? `${colours.slice(0, -1).join(", ")} ${t("boat.and")} ${colours.at(-1)}` : colours[0]!;
    label = t("boat.colours", { boat: label, colours: joined });
  }
  return label.charAt(0).toUpperCase() + label.slice(1);
}
