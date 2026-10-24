# Design system and user experience

The design specification uses **React + TypeScript + Base UI1.9.0**, grounded in the observed SOS MEDITERRANEE France identity. Data work remains the current priority. The documents and reference tokens are prepared; project wrappers, private APIs and new screens are not implemented by this design task.

## Read in this order

1. [Design system specification](docs/design/system.md): foundations, hierarchy, spacing, states and responsive rules.
2. [Component contracts](docs/design/components.md):26 proposed controls/patterns, Base UI composition and accessibility behavior.
3. [Concrete user journeys](docs/design/user-flows.md): screens, routes, actions, failure/recovery and implementation order.
4. [UX references and usability test plan](docs/design/ux-references.md): source-grounded decisions and measurable tasks.
5. [Observed SOS visual identity](docs/design/sos-visual-reference.md): observed colors and typography versus project proposals.

## Reusable references

- [JSON tokens](docs/design/tokens.json) and [CSS variables](docs/design/tokens.css), not currently imported into the app.
- [Design-system board](docs/design/assets/design-system.png) and [workflow board](docs/design/assets/user-flows.png): static design references using synthetic content, not working components or validated screenshots.
- [Scope and evidence](docs/design/integration.md) and [design-document status](docs/design/status.json).

## Decisions to preserve

Use the SOS navy/orange-red/white identity with Raleway as the proposed primary font. Use Base UI public exports and thin project wrappers; do not add a second control library. Never copy the old map prototype's CSS as the final design direction.

Make reviewing data clear: show source and interpretation together, keep list context while inspecting, name the effect of each action and explain errors where they occur. Selection does not approve an identity; approving an identity does not publish an event. Public exploration remains usable without the map.

Follow AGENTS.md: English product copy by default, translation catalogs, French as the first translation. French design documents describe proposed behavior and are not hard-coded product strings.

The reference CSS does not load fonts. Its semantic roles, state colors and darker action orange are project proposals, distinct from colors observed on the website. Breakpoints remain JSON-only and require static CSS media-query conditions. The first UI scope is the light theme; dark mode needs a separate implementation and review.

The next coding agent should start with UI0 (catalog and foundations), then UI1 (private review). Read the API dependency table before building screens: existing backend services are not yet private frontend endpoints. Validate real rendered interactions, keyboard behavior and usability with representative volunteers before claiming the experience is intuitive.
