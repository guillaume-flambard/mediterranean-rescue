# Diagnostic of sheet Other_data

> **Synthetic data.** Fictitious file written for tests: this report says nothing about the quality of the real dataset.

- Snapshot SHA-256: `dd7049bc2b43fe58956dcb32863513a4ca14a4f84ce0f0b12d6376f7ac4d6b9f` (414 bytes, UTF-8 BOM: no)
- Contract: `sheets-observed-v1` (observed_not_association_approved)
- CSV reading: complete: the whole file was read and ends with a line ending
- Normalization: blocked by at least one error
- Identities: unresolved; a line number locates the snapshot, not an event
- Publication: disabled; this tool creates no event and no draft

| Records read | Rows diagnosed | Blank rows skipped | File errors | Rows with errors | Rows with warnings | Errors | Warnings |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 4 | 0 | 0 | 2 | 1 | 4 | 2 |

## Checks triggered

| Code | Occurrences | Meaning |
| --- | ---: | --- |
| `coordinate_out_of_range` | 2 | Coordinate out of bounds, compared exactly before conversion. |
| `date_format_of_other_sheet` | 1 | Date in the other sheet's format; not converted. |
| `impossible_date` | 1 | Date that does not exist in the calendar. |
| `missing_position` | 1 | Unknown position; no replacement point. |
| `unnamed_column_has_value` | 1 | Column without header holding values (kept raw, outside the contract). |

## Locations

Physical start line in the snapshot; columns numbered from 1.

| Level | Line | Column | Contract field | Code |
| --- | ---: | ---: | --- | --- |
| warning | 4 | 3 | latitude | `missing_position` |
| error | 5 | 1 | date | `date_format_of_other_sheet` |
| error | 6 | 1 | date | `impossible_date` |
| error | 6 | 3 | latitude | `coordinate_out_of_range` |
| error | 6 | 4 | longitude | `coordinate_out_of_range` |
| warning | file | 16 |  | `unnamed_column_has_value` |

## Limits

- The contract comes from the CartONG code and the export of 24 October 2026; it is not approved by the association.
- A missing hemisphere is only inferred when a single reading falls inside the contract region; this rule is a proposal to validate.
- Units, count definitions and unknown markers remain to be validated.
- Original cells are in `diagnostic.json` and `snapshot.csv`, both private.
