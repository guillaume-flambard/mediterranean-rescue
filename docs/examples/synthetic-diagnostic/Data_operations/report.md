# Diagnostic of sheet Data_operations

> **Synthetic data.** Fictitious file written for tests: this report says nothing about the quality of the real dataset.

- Snapshot SHA-256: `ac7e593d2071491bf742a8243d6b65b8538ed33b8cfc360941f4eb0e7a4cca65` (1096 bytes, UTF-8 BOM: no)
- Contract: `sheets-observed-v1` (observed_not_association_approved)
- CSV reading: complete: the whole file was read and ends with a line ending
- Normalization: blocked by at least one error
- Identities: unresolved; a line number locates the snapshot, not an event
- Publication: disabled; this tool creates no event and no draft

| Records read | Rows diagnosed | Blank rows skipped | File errors | Rows with errors | Rows with warnings | Errors | Warnings |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 7 | 1 | 0 | 4 | 3 | 11 | 4 |

## Checks triggered

| Code | Occurrences | Meaning |
| --- | ---: | --- |
| `coordinate_minutes_out_of_range` | 1 | Arc minutes equal to or above 60. |
| `coordinate_out_of_range` | 1 | Coordinate out of bounds, compared exactly before conversion. |
| `coordinate_pair_incomplete` | 1 | Only one of the two coordinates is known. |
| `date_format_of_other_sheet` | 1 | Date in the other sheet's format; not converted. |
| `exact_duplicate_row` | 1 | Row identical to an earlier row; reported, never merged. |
| `fractional_count` | 1 | Non-integer count. |
| `impossible_date` | 1 | Date that does not exist in the calendar. |
| `missing_position` | 1 | Unknown position; no replacement point. |
| `negative_count` | 1 | Negative count. |
| `subpopulation_exceeds_total` | 2 | Subpopulation above its total; to review, nothing is corrected. |
| `testimony_lists_misaligned` | 1 | Testimony lists of different lengths; no pair guessed. |
| `unknown_kind` | 1 | Category outside the contract; source value kept. |
| `unsafe_url_scheme` | 1 | Link outside http/https refused. |
| `url_with_credentials` | 1 | Link holding credentials refused. |

## Locations

Physical start line in the snapshot; columns numbered from 1.

| Level | Line | Column | Contract field | Code |
| --- | ---: | ---: | --- | --- |
| error | 4 | 1 | date | `impossible_date` |
| warning | 4 | 11 | latitude | `missing_position` |
| error | 5 | 3 | nb_ops | `negative_count` |
| error | 5 | 4 | nb_survivor | `fractional_count` |
| error | 5 | 20 | image_src | `unsafe_url_scheme` |
| error | 5 | 23 | testimony_src | `testimony_lists_misaligned` |
| error | 5 | 11 | latitude | `coordinate_out_of_range` |
| warning | 5 | 8 | under_18_unacc | `subpopulation_exceeds_total` |
| warning | 5 | 9 | under_5 | `subpopulation_exceeds_total` |
| error | 6 | 1 | date | `date_format_of_other_sheet` |
| error | 6 | 2 | type_ops | `unknown_kind` |
| error | 6 | 20 | image_src | `url_with_credentials` |
| error | 6 | 11 | latitude | `coordinate_minutes_out_of_range` |
| warning | 7 |  |  | `exact_duplicate_row` |
| error | 9 | 12 | longitude | `coordinate_pair_incomplete` |

## Limits

- The contract comes from the CartONG code and the export of 24 October 2026; it is not approved by the association.
- A missing hemisphere is only inferred when a single reading falls inside the contract region; this rule is a proposal to validate.
- Units, count definitions and unknown markers remain to be validated.
- Original cells are in `diagnostic.json` and `snapshot.csv`, both private.
