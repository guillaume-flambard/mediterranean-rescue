---
name: Mediterranean Rescue
description: Documented actions at sea, read as a feed of self-proving event cards beside a quiet map, in the SOS MEDITERRANEE identity.
colors:
  sos-navy: "#1B2747"
  sos-orange: "#E83E1B"
  orange-text: "#C53215"
  orange-hover: "#AB2A11"
  white: "#FFFFFF"
  ground: "#EEEDF2"
  canvas: "#F7F8FA"
  water: "#DFE3EE"
  land: "#FBFBFD"
  coast: "#C3C7D6"
  slate: "#404D6D"
  muted: "#596579"
  border: "#D5DAE3"
  text-selection: "#FFD9CF"
  preview-tint: "#FBEEE9"
  kind-rescue: "#2563A8"
  kind-transfer: "#404D6D"
  kind-medevac: "#17634A"
  kind-incident: "#B7791F"
  kind-shipwreck: "#9F2534"
  kind-dead-missing: "#1B2747"
  warning-text: "#7A4A00"
  warning-surface: "#FFF4D6"
  warning-dot: "#C98A13"
  error: "#9F2534"
  error-surface: "#FDEFF1"
  success: "#17634A"
  success-surface: "#EAF5EF"
typography:
  display:
    fontFamily: "Raleway Variable, Raleway, system-ui, sans-serif"
    fontSize: "clamp(26px, 2.4vw + 14px, 38px)"
    fontWeight: 800
    lineHeight: 1.12
    letterSpacing: "-0.025em"
  brand:
    fontFamily: "Raleway Variable, Raleway, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 800
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Raleway Variable, Raleway, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 800
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  figure:
    fontFamily: "Raleway Variable, Raleway, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 800
    fontFeature: "\"lnum\", \"tnum\""
  body:
    fontFamily: "Raleway Variable, Raleway, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 500
    lineHeight: 1.55
    fontFeature: "\"lnum\""
  fact:
    fontFamily: "Raleway Variable, Raleway, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    fontFeature: "\"lnum\", \"tnum\""
  label:
    fontFamily: "Raleway Variable, Raleway, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
  caption:
    fontFamily: "Raleway Variable, Raleway, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.5
rounded:
  small: "4px"
  medium: "8px"
  large: "12px"
  inset: "14px"
  field: "18px"
  card: "20px"
  map: "22px"
  composer: "24px"
  pill: "999px"
spacing:
  space-1: "4px"
  space-2: "8px"
  space-3: "12px"
  space-4: "16px"
  space-5: "20px"
  space-6: "24px"
  space-8: "32px"
  space-10: "40px"
  space-12: "48px"
  space-16: "64px"
components:
  top-bar:
    backgroundColor: "{colors.sos-navy}"
    textColor: "{colors.white}"
    height: "60px"
  composer:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.composer}"
    padding: "8px 8px 12px"
  composer-search:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.sos-navy}"
    rounded: "{rounded.field}"
    height: "48px"
    padding: "0 44px"
  chip:
    backgroundColor: "{colors.white}"
    textColor: "{colors.sos-navy}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    height: "36px"
    padding: "0 14px"
  chip-pressed:
    backgroundColor: "{colors.sos-navy}"
    textColor: "{colors.white}"
    rounded: "{rounded.pill}"
  segmented-option-pressed:
    backgroundColor: "{colors.white}"
    textColor: "{colors.sos-navy}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    height: "36px"
  view-option:
    textColor: "{colors.slate}"
    rounded: "{rounded.large}"
    height: "40px"
    padding: "0 12px"
  view-option-pressed:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.sos-navy}"
    rounded: "{rounded.large}"
  event-card:
    backgroundColor: "{colors.white}"
    textColor: "{colors.sos-navy}"
    rounded: "{rounded.card}"
    padding: "16px 16px 12px 20px"
  card-locator:
    backgroundColor: "{colors.water}"
    rounded: "{rounded.inset}"
    width: "96px"
    height: "76px"
  button-primary:
    backgroundColor: "{colors.orange-text}"
    textColor: "{colors.white}"
    rounded: "{rounded.pill}"
    height: "44px"
    padding: "0 20px"
  button-primary-hover:
    backgroundColor: "{colors.orange-hover}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.sos-navy}"
    rounded: "{rounded.pill}"
    height: "44px"
    padding: "0 20px"
  button-quiet:
    textColor: "{colors.sos-navy}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    height: "36px"
    padding: "0 12px"
  map-card:
    backgroundColor: "{colors.water}"
    rounded: "{rounded.map}"
  status-to-review:
    backgroundColor: "{colors.warning-surface}"
    textColor: "{colors.warning-text}"
    rounded: "{rounded.pill}"
    height: "24px"
    padding: "0 10px"
---

# Design System: Mediterranean Rescue

Detailed French specifications remain in `docs/design/`: [system.md](docs/design/system.md), [components.md](docs/design/components.md), [user-flows.md](docs/design/user-flows.md), [ux-references.md](docs/design/ux-references.md), [sos-visual-reference.md](docs/design/sos-visual-reference.md), and the reference tokens ([tokens.json](docs/design/tokens.json), [tokens.css](docs/design/tokens.css), mirrored in `frontend/src/styles/tokens.css` and checked by `tokens.test.ts`). This file records the system as shipped in the main screen (`frontend/src/explore/`, `frontend/src/styles/explore.css`). Where the two disagree, the shipped build is the reference for new surfaces and the French documents describe intent.

## Overview

**Creative North Star: "The Logbook Feed"**

Events read like a conversation you scroll. Each one is a soft white card on a cool lavender-grey ground that proves itself at a glance: a heavy date, the kind of action with its colour dot, the people reported, the port, a small locator map of where it happened and the line of the source it came from. The card opens in place into the full record. Beside the feed on a desk, and above it on a phone, a quiet map in pale water and near-white land holds the same events as navy points and clusters.

The identity is SOS MEDITERRANEE kept intact: deep navy for the shell and every pressed state, orange-red held back for the one thing that is selected and the one action that matters, Raleway for everything. The component language comes from current conversational apps: a floating rounded composer for search and filters, pill chips, segmented switches, generous radii, soft navy-tinted shadows and short eased transitions. Density stays moderate; two cards fit in the first phone screen under the map strip and composer.

Provenance is visual, not decorative: the origin line on every card, lining and tabular numerals on every figure, and an unknown value shown as unknown. Nothing in the surface is ornamental; there is no photography, no illustration and no gradient beyond the loading shimmer.

**Key Characteristics:**
- Navy shell, lavender-grey ground, white cards with 20px corners and a soft navy-tinted shadow.
- Orange-red reserved for selection and the single primary action.
- Kind colours appear only as small dots, shared by chips, cards and map points.
- Raleway 800 for dates, kinds and figures; 500 for running text; lining numerals everywhere, tabular where figures align.
- A floating composer (view switcher, search, chips) that stays reachable under the bar below 960px.
- The list is a complete path without the map.

## Colors

A restrained navy-and-grey field where one hot colour marks what is selected and what to do next.

### Primary
- **SOS Navy** (sos-navy): the top bar, all body text, pressed chips, the text of every pressed switch, map clusters, the locator dot at rest, and the 3px focus outline on light surfaces. It is the brand voice and the "on" state.
- **SOS Orange-Red** (sos-orange): selection only. The ringed active point and halo on the large map, the locator dot of the open card, the soft inset ring of the open card, the text caret.
- **Action Orange** (orange-text): the darker orange that carries white text. Fill of the one primary pill per open card (go to the source, or open the row in the workspace) and the colour of small-text links in the footer. **Action Orange Hover** (orange-hover) darkens it on hover.

### Neutral
- **Lavender-Grey Ground** (ground): the page behind cards, and the fill of the pressed view option inside the composer.
- **Paper White** (white): cards, composer, chips, secondary pills, the pressed segmented option.
- **Field Canvas** (canvas): the recessed fill of the search field and period inputs; hover fill of secondary pills.
- **Water** (water), **Land** (land), **Coast** (coast): the map palette, shared by the large map and the card locator so both read as one place.
- **Slate** (slate): secondary text (dates, facts line, descriptions, unpressed view options).
- **Muted** (muted): icons, captions, origin lines, placeholders, field labels; also the hover border of chips.
- **Hairline** (border): chip and secondary pill borders, period input borders, the divider above an open card body.
- **Selection Wash** (text-selection) for selected text, and **Preview Tint** (preview-tint) for the reviewers' private-preview notice block.

### Kind colours
One colour per event kind, always as an 8 to 10px dot (chip dot, card kind dot, 6px map point with a white stroke): rescue (kind-rescue, sea blue), transfer (kind-transfer, slate), medical evacuation (kind-medevac, green), incident (kind-incident, ochre), shipwreck (kind-shipwreck, deep red), dead and missing (kind-dead-missing, navy, given a thin white ring on chips so it separates from a pressed navy chip).

### State colours
Review status pills pair a pale surface with a dark text and a 7px dot: to review (warning-surface, warning-text, warning-dot), blocked (error-surface, error), checked (success-surface, success). Error text and inline warnings use error.

### Named Rules
**The Orange Reservation Rule.** Orange-red marks exactly two things: what is selected (open card, active map point, its locator dot) and the one primary action of an open card. Never a kind colour, a chip, a heading, a badge or decoration. Small text in orange always uses Action Orange.

**The Dot-Only Kind Rule.** Kind colours are identification dots, never text, fills or borders. The same kind keeps the same colour on chips, cards and the map.

**The Navy Is On Rule.** A pressed chip is filled navy with white text; a pressed switch option lifts to white (or ground inside the composer). Pressed never means orange.

## Typography

**Display Font:** Raleway (variable, self-hosted through `@fontsource-variable/raleway`, with system-ui, sans-serif)
**Body Font:** Raleway, same family
**Label/Mono Font:** none distinct; one family carries every role.

**Character:** a single geometric humanist sans used at two poles: extra-bold for anything you scan (dates, kinds, figures, titles) and medium for anything you read. All numerals are lining; figures that line up are also tabular.

### Hierarchy
- **Display** (800, clamp(26px, 2.4vw + 14px, 38px), 1.12, -0.025em, balanced wrap): the main screen's single heading. Visually hidden on phones, where the map and cards lead.
- **Brand** (800, 17px, 15px on phones, -0.01em): the product name in the navy bar.
- **Title** (800, 19px, 17px on phones, 1.25, -0.01em): the event kind on each card, next to its colour dot. Empty-state headings use 800 at 18px.
- **Figure** (800, 14px, lining and tabular): card dates, in slate.
- **Fact** (700, 15px, lining and tabular): people reported on the card (in navy against the slate facts line) and values in the opened record.
- **Body** (500, 16px, 1.55, max 65ch): the event summary in the open card and intro prose. Facts line at 15px (14px on phones).
- **Label** (600, 14px): chips, switches, quiet buttons, bar actions. Pills use 700 at 15px; view options and counts use 700.
- **Caption** (600, 13px): origin line under the facts (12px on phones), field labels in the period panel, fact terms; provenance notes use 500 at 13px, 1.5.

### Named Rules
**The Two Weights Rule.** Scan at 800, read at 500. Middle weights (600, 700) are for controls and figures only, never for running text.

**The Lining Figures Rule.** Every number on the surface is lining (`font-variant-numeric: lining-nums` is set on the whole screen); counts, dates and facts add `tabular-nums` so they align.

## Layout

Mobile first, one column, with two breakpoints.

- **Below 640px (phone):** gutters 16px, bar 60px with brand, language select and the workspace as a 36px round icon (its label kept for assistive tech). The visible order is fixed by CSS order: map strip (170px, foldable), sticky composer, results line with the map toggle, private preview strip (reviewers only), pinned card, feed or logbook, load more, footer. In timeline view the timeline comes right after the composer and the map strip grows to 46vh. The display heading and the notice body are visually hidden so two cards fit under the composer. Card summaries tighten (12px and 16px padding, 76 by 60px locator).
- **640px to 959px:** bar padding 24px, the inline map strip grows to 240px, the locator to 128 by 96px. The composer is still sticky.
- **960px and up (desk):** bar 64px with the tagline. The body becomes two columns: a feed column `minmax(420px, 620px)` with 32px leading padding, and a map that is sticky under the bar at full viewport height minus the bar, inset by 24px. The inline map strip and its toggle disappear; chips wrap instead of scrolling.

Spacing follows a 4px base (space-1 to space-16). The feed stacks cards 12px apart inside a 16px-gap column; a card summary is a two-column grid, text on the left and the locator over the chevron on the right.

**The Composer Stays Rule.** Below 960px the composer is sticky 8px under the bar and carries a 12px ring of ground colour in its shadow so cards never show through around it. A card scrolled into view keeps a top margin clearing the bar plus the composer (210px, 270px on desk). In logbook view it is the map that stays: below 960px the composer scrolls away and the 150px map strip sticks under the bar, so the point of the entry being read stays in sight.

**The Map Is Optional Rule.** The map can fold away on phones and may fail entirely; the feed, filters and open records must remain a complete path without it.

## Elevation & Depth

Soft and ambient. Depth comes from white surfaces floating on a tinted ground, with navy-tinted shadows, never grey or black ones. There are no borders around cards.

### Shadow Vocabulary
- **Card** (`0 1px 2px rgb(27 39 71 / 0.06), 0 10px 28px -14px rgb(27 39 71 / 0.22)`): cards at rest, the composer, the map card, empty states.
- **Card raised** (`0 2px 4px rgb(27 39 71 / 0.08), 0 18px 40px -18px rgb(27 39 71 / 0.32)`): card hover and the open card.
- **Open ring** (`inset 0 0 0 2px rgb(232 62 27 / 0.55)`, added to Card raised): the selected card.
- **Pressed lift** (`0 1px 3px rgb(27 39 71 / 0.16)`): the pressed option of a segmented or view switch on ground.
- **Popup / dialog** (`0 8px 24px rgb(27 39 71 / 0.12)` / `0 16px 48px rgb(27 39 71 / 0.18)`): inherited tokens for floating menus and the sign-in card.

**The Navy Tint Rule.** Every shadow is navy (27 39 71) at low alpha with a negative spread, so it reads as lift rather than outline. Hard offset shadows have no place here.

## Shapes

Generously rounded and nested: the larger the surface, the larger the corner, and an inner element always has a smaller radius than its container. Composer 24px, map card 22px, cards and empty states 20px, search field and notice block 18px, locator and period inputs 14px, view options and map notes 12px, chips, pills, segmented switches, status pills and counts fully round. Round controls (search clear, icon buttons) are circles. The team space header follows the same scale (a 20px navy band, round icon buttons and fully round navigation pills); only the older workspace forms and tables keep the tighter 4, 8 and 12px scale from `tokens.css`.

Icons are one authored set on a 24px grid, 1.75 stroke, round caps and joins, drawn in currentColor at 16 to 20px (`frontend/src/ui/Icon.tsx`).

## Components

### Buttons
- **Shape:** full pill (999px), 44px tall, 20px side padding, 700 at 15px.
- **Primary:** Action Orange fill, white text, no border. At most one per open card. Hover to Action Orange Hover; press scales to 0.98.
- **Secondary:** white with a hairline border, navy text; hover to field canvas. Used for further sources, retry, clear filters, load more.
- **Quiet:** transparent pill, 36px, 600 at 14px; hover adds a 6% navy wash. Used for "clear" and the map toggle beside the results line.
- **Icon button:** 40px circle, transparent, the same 6% navy wash on hover.
- **Focus:** a 3px navy outline 2px out on light surfaces, white inside the navy bar.

### Chips
- **Style:** white pills 36px tall, hairline border, 600 at 14px, 14px side padding, an 8px kind dot before the label.
- **State:** pressed is navy fill and white text; hover deepens the border to muted. They scroll horizontally with a fade mask and snap on phones and wrap from 960px. The period chip opens a two-field panel inside the composer by animating its row height.

### Segmented switch and view switcher
- **Segmented** (two options, e.g. private preview or published): a pill track of 8% navy, 3px padding, options 36px tall at 600 14px; the pressed option lifts to white with the pressed shadow.
- **View switcher** (feed, logbook, timeline at the top of the composer): 40px options with 12px corners, slate text at 700 14px, an icon before the label; the pressed option takes the ground fill. All three views are built; the choice lives in the address (`?view=logbook`, `?view=timeline`).

### Composer (signature)
A floating white panel (24px corners, card shadow) that gathers the view switcher, the search field and the chip row. The search field is 48px tall on field canvas with 18px corners, a leading search icon and a round clear button; on focus it turns white with an inset 2px navy ring. Search text is 16px so phones do not zoom.

### Event card (signature)
- **Corner Style:** 20px, overflow clipped.
- **Background:** white on ground, card shadow; raised on hover.
- **Summary:** the whole summary is one button. Left: date (figure) with an optional status pill, kind title with its dot, facts line (people icon and count in navy, anchor icon and port), origin line in caption. Right: the locator, a static SVG of the same coastline in land and water with a navy point and soft halo, above a chevron that rotates 180 degrees when open.
- **Open:** raised shadow plus the orange inset ring; the locator point and halo turn orange; the body appears below a hairline with a 6px rise and fade (0.35s). It holds the summary text, a grid of facts (13px muted terms, 15px 700 values), warnings, provenance and source pills.
- **Pinned:** a record opened from the map that is not in the loaded feed sits above it with a small heading and a close icon button.
- **Loading:** 124px skeleton cards with a slow white shimmer.

### Map
MapLibre on a self-contained style: water background, near-white land, a 0.7px coast line, no basemap labels. Clusters are navy circles with a white 2px stroke, 13, 17 or 22px radius by size; single events are 6px kind-coloured points with a white stroke; the hovered or open event sits above all in a 22px orange halo and a 9px orange point with a 3px white stroke. Opening a card eases the map to it over 700ms (instant with reduced motion). The camera moves only when the event to show changes, never on a data refresh. In the logbook, the entry crossing the middle of the screen lights its point, and the map pans 500ms only when that point is off screen; dragging the map stops this following until an event is opened. When the timeline floats over the map, the map's bottom padding equals the timeline's height so centring happens above it. The map sits in a card with 22px corners; a translucent white note at its foot reports truncation; a failure shows a notice and leaves the list intact.

### By month (view B)
Events grouped by month in white 20px cards. The month heading (19px 800, sticky under the bar on desk) carries a totals line in 13px 700 slate: the event count and the people rescued, added up for rescues only so a person rescued then transferred never counts twice; "where given" when some rescues lack a number, "more below" while the month is not fully loaded, "in this period" for the first and last months when a period is chosen. Each entry is one button on a 2px rail: day (13px 800 figures), a 12px dot in the kind colour, then the kind and people line (16px 800), the port line with the status pill, and the origin line in caption, as on the cards. The open entry takes a pale orange wash and an orange dot with a soft ring.

### Timeline (view C)
A white 20px card: title, the selected period in 14px 600 slate with tabular figures, a "Whole period" quiet button when narrowed, and a muted line for events without a date, which never sit on the bars. Month bars (72px tall, empty months as 2px stubs) in pale navy; the chosen months turn navy and a 2px navy window frames them. No window is drawn on the whole period. A chosen period is a filter, so it is navy like a pressed chip, never orange. Two native range inputs give the handles (26px white circles with a 3px navy border); bars, window and year labels are inset by half a handle so they line up with it. A period set elsewhere that is not whole months reads "Period chosen by dates". In the column below 960px; from 960px it floats over the bottom of the map with a deeper shadow.

### Team space header
A navy band with 20px corners: the project's mark (28px) and the brand in white 800 with "Team space" in 70% white (hidden below 640px so the brand never truncates), round icon buttons for the public site and sign-out, then a scrolling row of pill links in the order of the work (Home, Latest data, Verify events, Publish, Port names, Manual update); the current section is a white pill with navy text. The team's data page sits on the same ground as the public screen.

### Identity mark
The project's own mark, drawn for this site (`frontend/src/ui/BrandMark.tsx`, `public/favicon.svg`): a documented point above the sea. An orange-red point with a 3px white ring and a 2.5px orange outer ring at 70%, above two white waves (the lower one at 55%). On navy bars it is drawn without its tile at 26 to 30px; the tile version (navy, 15px corners on a 64 grid) is the favicon; PNG icons (180, 192, 512) are full-bleed navy squares with the mark in the safe zone; the social image (1200 by 630) sets the mark, "Operations at sea, documented." in 800 white with the second line in light orange, a short sentence and the coastline faded in from the right. It is never the SOS MEDITERRANEE logo, which needs the association's written consent; the association's name appears in text only.

### First-visit card and About page
The first-visit card is a navy 20px card at the top of the public feed (first on phones, above the map): a 17px heading, three short facts with orange markers, an underlined link to the About page, a close button remembered per browser. The About page (`/about`) is one 760px column on the ground: an orange eyebrow, a 30 to 44px navy title, an 18px lead, a tinted note that the site is independent, the one primary pill back to the map, then white 20px cards in the order a newcomer asks (what you should know, how to read the map with drawn legend samples, what the words mean in a two-column grid of tinted definition tiles with kind dots, the four numbered steps from the sea to the page, a navy card on dignity, citing and other sources).

### Team home and publishing
The team home (`/workspace`) greets the person, shows a dismissible navy welcome that ends with a bold reassurance, then a numbered To do list of white 20px cards in the order of the work. Each card: a 36px number disc (navy to do, green with a check when done, pale when it cannot start), a 17px title, one sentence on why it matters, a state pill in words (To do, Done, Cannot start yet) with the live detail, and one pill button; only the next step's button is orange. Below: three link tiles for occasional tasks, and a tinted card listing the person's role with checks and crosses. The publish page repeats the head, shows an amber lock block when a source's publication is not agreed (saying who unlocks it), then two step cards with an orange "Step n" eyebrow: prepare (big navy count, plain counts of what waits or needs fixing, reason field, one button) and publish or withdraw (navy segmented tabs with counts, a table with a checkbox per event, a reason, and a confirmation dialog whose button names the outcome, "Publish 3 events").

### Logbook card and rebuilt records (team space)
On the team's data page, the logbook card comes first, a white 20px card that states the problem in one line: an orange eyebrow ("Bring the SOS map up to date"), a 20px navy title with the sheet's last date, a lead in slate with the rebuilt operations and people, then a tinted year check (for each year, people in the sheet plus people rebuilt against the figure in SOS's annual report, with a link to the reports), three numbered steps (verify, download, paste into the SOS sheet) with live counts, and two pills: the one orange action "Verify N operations", which opens the verify screen on that update, and a quiet "See them on the map". The download sits under the steps with its icon; with nothing verified it is disabled and says "Nothing to download yet: verify first". A chip "Rebuilt from the logbook" with an anchor icon filters the team view to those operations; pressed, it is navy like the other chips. In a rebuilt record, the logbook sentence sits in a tinted 16px block: a small slate label with the entry time, the quote with a 3px navy rule on its left (a quotation, not a status), the notes to check under an amber alert line, then the provenance and a bold link to the logbook page. On the verify screen the same block comes first, followed by a short "What to check" list (the date, the number of people, the place), the sheet's columns folded under a disclosure, and the primary action "It matches: mark as verified". A row entered twice in the sheet shows an amber note naming the row it copies and offers no decision. Strips that scroll sideways (filter chips, view switches, publish tabs, team navigation) fade only on the side where more is hidden. The view of events month by month is called "By month" so it is never confused with SOS's logbook.

### Status pills and counts
24px pills with a 7px dot and 700 at 12px, in the state colours. Counts in the private preview notice are white 26px pills with a dot and tabular figures.

### Navigation
The navy top bar is sticky; the brand is a text link in white 800. Bar controls are outlined or 10% white pills (language select, private workspace link), lightening to 18% white on hover.

### Motion
Transitions run 0.2 to 0.35s on `cubic-bezier(0.16, 1, 0.3, 1)`, an ease-out with a long tail: chip and switch colour, card shadow, chevron rotation, height reveals of the period panel and the map strip (grid rows from 0fr to 1fr), the card body rise. Under `prefers-reduced-motion` all animation and transition durations collapse.

## Do's and Don'ts

### Do:
- **Do** keep orange-red for the selected event and the single primary action; use Action Orange for any orange text or filled button.
- **Do** mark event kinds with a dot in the shared kind colour, on chips, cards and map alike.
- **Do** set every figure in lining numerals and add tabular figures where numbers align.
- **Do** float white surfaces on the lavender-grey ground with the navy-tinted card shadow, and nest radii from 24px down to 12px.
- **Do** show a pressed state as navy fill (chips) or a white lift (switches).
- **Do** give every card its origin line and keep unknown values written as unknown.
- **Do** keep the phone order: map strip, composer, results, preview strip, pinned card, feed or logbook, load more, footer.

### Don't:
- **Don't** use orange-red for a kind, a chip, a heading or decoration.
- **Don't** put kind colours on text or large fills.
- **Don't** mark a notice or a selected row with a coloured side rule; use a tinted block or the inset ring instead.
- **Don't** use grey or black shadows, borders around cards, or hard offset shadows.
- **Don't** make the map the only way to reach an event.
- **Don't** use the SOS MEDITERRANEE logo or photos, or generated pictures of people; the project mark and text attribution only.
- **Don't** show two orange buttons on one screen: in a list of steps, only the next one is primary.
