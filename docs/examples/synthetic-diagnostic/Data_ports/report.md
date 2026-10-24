# Diagnostic of sheet Data_ports

> **Synthetic data.** Fictitious file written for tests: this report says nothing about the quality of the real dataset.

- Snapshot SHA-256: `12eb3acc1b8041e1cdae65aebaad3a66a91bdf56f001d0041e71aaadad6e8bbc` (95 bytes, UTF-8 BOM: yes)
- Contract: `sheets-observed-v1` (observed_not_association_approved)
- CSV reading: complete: the whole file was read and ends with a line ending
- Normalization: blocked by at least one error
- Identities: unresolved; a line number locates the snapshot, not an event
- Publication: disabled; this tool creates no event and no draft

| Records read | Rows diagnosed | Blank rows skipped | File errors | Rows with errors | Rows with warnings | Errors | Warnings |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 3 | 0 | 0 | 1 | 0 | 1 | 0 |

## Checks triggered

| Code | Occurrences | Meaning |
| --- | ---: | --- |
| `missing_cells` | 1 | Fewer cells than headers; row not normalized. |

## Locations

Physical start line in the snapshot; columns numbered from 1.

| Level | Line | Column | Contract field | Code |
| --- | ---: | ---: | --- | --- |
| error | 4 |  |  | `missing_cells` |

## Limits

- The contract comes from the CartONG code and the export of 24 October 2026; it is not approved by the association.
- A missing hemisphere is only inferred when a single reading falls inside the contract region; this rule is a proposal to validate.
- Units, count definitions and unknown markers remain to be validated.
- Original cells are in `diagnostic.json` and `snapshot.csv`, both private.
