# AGENTS.md

Conventions for anyone, human or agent, contributing to this repository.

## Languages
- Code, identifiers, comments, docstrings, commit messages, log and error messages: **English**, so the code can be shared with contributors from any country.
- Specifications, decision records (`docs/decisions`), project notes (`docs/`, `.agent/project`) may be written in French.
- Product language: **English by default**, with English URLs and route names. French is the first translation. Every user-facing text goes through a translation catalog; never hard-code French strings in new code.
- Existing French labels in the foundation (model choices, admin actions, current UI) are legacy; they move to translation catalogs when the React application is built.

## Data rules
- Never commit real source data. Real exports live only under `data/local/` (ignored by Git) and are never redistributed.
- Unknown stays `null`, never zero. No identity, position or count is invented. Imports create staging or drafts, never publications.
- Tests use synthetic fixtures labelled as fictitious.

## Workflow
- Read `README.md`, `docs/PROJECT.md` and the latest decision records before changing the model or a contract; record a short ADR for such changes.
- Backend tests run on PostGIS through Docker Compose (see README); the offline Sheets diagnostic tests also run on the host with `cd backend && python3 -m unittest catalog.tests.test_sheets`.
- No pull request to the fork or to Data for Good until Guillaume decides to show the work (decision of 24 October 2026). Work on branches and push them.
