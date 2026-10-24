import { describe, expect, it } from "vitest";
import { createI18n } from "../i18n/I18nProvider";
import { boatLabel, parseBoat } from "./boat";

const fr = createI18n("fr");
const en = createI18n("en");

describe("boat types", () => {
  it("says the sheet's wordings in French, with agreement", () => {
    expect(boatLabel(fr, "Rubber Boat")).toBe("Embarcation pneumatique");
    expect(boatLabel(fr, "Rubber boat (white & black)")).toBe("Embarcation pneumatique blanche et noire");
    expect(boatLabel(fr, "Blue wooden boat")).toBe("Embarcation en bois bleue");
    expect(boatLabel(fr, "Fiber glass boat (white)")).toBe("Embarcation en fibre de verre blanche");
    expect(boatLabel(fr, "Steel / Iron boat")).toBe("Embarcation métallique");
    expect(boatLabel(fr, "Small wooden boat")).toBe("Petite embarcation en bois");
    expect(boatLabel(fr, "2 Rubber Boats")).toBe("2 embarcations pneumatiques");
    expect(boatLabel(fr, "Pleasure craft")).toBe("Bateau de plaisance");
  });

  it("keeps English readable and consistent", () => {
    expect(boatLabel(en, "Rubber Boat (black)")).toBe("Rubber boat (black)");
    expect(boatLabel(en, "Woodent boat (Blue)")).toBe("Wooden boat (blue)");
  });

  it("never guesses: a word it does not know leaves the text as written", () => {
    expect(parseBoat("Wooden Boat (Small - white)")).toEqual({ count: 1, material: "wooden", size: "small", colours: ["white"] });
    expect(boatLabel(fr, "Rubber boat towed by a fishing vessel")).toBe("Rubber boat towed by a fishing vessel");
    expect(boatLabel(fr, "Fiber glass rubber boat")).toBe("Fiber glass rubber boat");
    expect(boatLabel(fr, "")).toBeNull();
  });
});
