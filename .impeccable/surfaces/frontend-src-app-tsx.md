---
version: 1
slug: "frontend-src-app-tsx"
primary_target: "frontend/src/App.tsx"
related_targets: ["frontend/src/preview/PreviewDetail.tsx"]
---

# Main screen (public explorer, with the reviewers' private preview)

Scope: `/`, the screen everyone lands on. Visitor mode: Operate. Audience: the public first (visitors, journalists, teachers on a phone or a laptop); signed-in reviewers see the latest private export in the same screen. Job: find events of a period, read one, reach its source. Constraints: the list works without the map; unknown counts stay unknown; nothing private reaches a visitor.

Unresolved: official logo use; real photography (none cleared); per-event source links for preview rows.

## Direction contract

THESIS: Events read as a feed of self-contained cards, like a conversation you scroll: each card proves itself (date, type, people, port, a mini-map of where it happened, its source line) and opens in place into the full record. It refuses the category default of a giant map with a cramped side list.

OWN-WORLD: SOS navy #1B2747 shell and active states, orange-red #E83E1B reserved for selection and the one primary action (#C53215 for small text), a lavender-grey #EEEDF2 ground, white cards with 20px radius and a soft navy-tinted shadow, Raleway 800 for dates and figures, 500 for text, tabular numbers, pill chips, a floating rounded search composer.

STORY: The visitor sees right away that these are documented actions at sea, narrows them with chips (type, year) or the search composer, opens one card and reads where the numbers come from.

FIRST VIEWPORT: Phone 390: navy top bar (name, language, sign-in), a 200px map strip with clustered points that folds away, a sticky composer plus chip row, then the first two cards. Desktop 1440: navy top bar, a 640px feed column on the left with the composer and chips at its top, a sticky full-height map on the right that lights the point of the card under the pointer or opened.

FORM: feed of event cards, position 7 on the ordered list, seed d27f0847.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
