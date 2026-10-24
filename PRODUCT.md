# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Primary (main screen): the public.** Visitors, journalists and teachers who want to understand a period of actions at sea in the Mediterranean and cite a source. They arrive on a phone as often as on a laptop. Confirmed by Guillaume on 24 October 2026: the main screen is designed for the public first.
- **The data team (private layer).** Volunteers who import the Google Sheets exports, check rows, read port names and prepare drafts. On the main screen they get a private preview of the latest export; their work happens in the private workspace (`/workspace`).
- **Editorial lead.** Decides what becomes public, with a reason; can correct or withdraw.
- These audiences are hypotheses to confirm with SOS MEDITERRANEE and Data for Good, not interview results.

## Product Purpose
Make actions in the Mediterranean understandable from documented events: place them, filter them, read their context and reach their sources. Every number and position must be explainable. Success is a complete path: an authorised source enters, its anomalies are reviewed, an event is published, the public reads it, and a lead can correct or withdraw it.

## Positioning
An independent, open-source interface (fork of Data for Good's `mediterranean-rescue`) that treats provenance as the product: each event traces back to the exact row of the exact export it came from, and nothing is published without a human decision. The existing SOS map (map.sosmediterranee.org, CartONG) reads the sheets directly; this project adds review, history and explainable numbers.

## Operating Context
- Data comes from three Google Sheets tabs (Data_operations, Other_data, Data_ports), downloaded as CSV and staged privately. Real data stays on the local machine and private network; it is never committed or published without approval.
- Counts describe events, not unique people. Unknown stays unknown, never zero.
- Guillaume follows the work from his phone through a private tunnel; mobile is a first-class context.

## Capabilities and Constraints
- Stack: Django 5.2 + DRF + PostGIS, React 19 + TypeScript + Base UI 1.9 + MapLibre, TanStack Query, OpenAPI-generated types. No second component library.
- English product copy by default with English URLs; French is the first translation; every user-facing string goes through the catalogs.
- The list must remain a complete path when the WebGL map fails.
- Publication is a transactional service with permission and reason; no switch publishes instantly.
- Not decided: hosting, official logo use, final scope agreed with the associations.

## Brand Commitments
- Stay close to the SOS MEDITERRANEE identity (confirmed by Guillaume on 24 October 2026): deep navy #1B2747, orange-red accent #E83E1B (darker #C53215 for small text), white, Raleway. More character and strength than the current implementation, still recognisably the same world.
- Do not redraw or alter the official logo; do not use generated portraits of rescued people.
- Tone: direct, committed, documentary.
- Components: modern and interactive, in the spirit of current conversational apps such as ChatGPT or Claude (soft rounded surfaces, floating panels and sheets, a prominent search or composer input, suggestion chips, fluid transitions), while colours and identity stay SOS MEDITERRANEE (confirmed by Guillaume on 24 October 2026).

## Evidence on Hand
- Observed identity: `docs/design/sos-visual-reference.md`, palette board `docs/design/assets/palette-sos.png`.
- Real export of 24 October 2026, private and local only (`data/local/`, ignored by Git): 370 operations, 9 other events, 24 ports.
- No photography, testimonies or press assets are cleared for use yet; none may be invented.

## Product Principles
1. Provenance before polish: every figure shows where it comes from.
2. Unknown is shown as unknown, never filled.
3. Nothing becomes public without a named human decision.
4. Plain language first, technical terms only as help.
5. Works on a phone as well as on a desk, and without the map.

## Accessibility & Inclusion
WCAG 2.2 AA as the working target: contrast, keyboard paths, visible focus, 16 px minimum body text, zoom preserved, reduced motion respected, map never the only path to the data.
