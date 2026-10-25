#!/usr/bin/env python3
"""Rebuild the operations missing from the SOS MEDITERRANEE map from the association's own public
logbook, and write them as files for review (the parsing lives in backend/catalog/logbook.py).

Writes to data/local/backfill (ignored by Git; the data belongs to SOS MEDITERRANEE):
- Data_operations-backfill.csv: rows in the exact column order of the map's sheet;
- backfill-provenance.csv: for every row, the page, entry and quote, and what to check;
- backfill-rotations.csv: each rotation's stated total next to the sum of its rows;
- backfill-gaps.csv: French-site posts that are not rescues (left to a person);
- backfill-other-events.csv: events that are not rows of the sheet (transfers off the ship).

Usage: python3 scripts/logbook_backfill.py [--after 2024-02-06] [--out data/local/backfill]
"""

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from catalog.logbook import Fetcher, extract, rows_csv  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--after", default="2024-02-06", help="last date already in the sheet")
    parser.add_argument("--out", default=str(ROOT / "data/local/backfill"))
    parser.add_argument(
        "--refresh", action="store_true", help="fetch again instead of using the cache"
    )
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fetcher = Fetcher(ROOT / "data/local/logbook-cache", args.refresh)
    result = extract(fetcher.get, date.fromisoformat(args.after))

    (out / "Data_operations-backfill.csv").write_bytes(rows_csv(result.sheet_rows))
    write(
        out / "backfill-provenance.csv",
        ["row", "rotation", "source_url", "entry", "quote", "to_check"],
        result.provenance,
    )
    write(
        out / "backfill-rotations.csv",
        list(result.summary[0]) if result.summary else ["rotation"],
        result.summary,
    )
    write(
        out / "backfill-other-events.csv",
        ["date", "what", "people", "rotation", "source_url", "quote"],
        result.others,
    )
    write(
        out / "backfill-gaps.csv",
        ["published", "title", "source_url"],
        result.gaps,
    )
    matching = sum(1 for item in result.summary if item["matches"] == "yes")
    print(
        f"rotations read: {len(result.summary)}, rows: {len(result.sheet_rows)} ({len(result.rescues)} rescues)"
    )
    print(f"people in rescue rows: {sum(int(row['nb_survivor'] or 0) for row in result.rescues)}")
    print(f"rotations whose rows match the stated total: {matching}/{len(result.summary)}")
    print(
        f"rows to check: {sum(1 for p in result.provenance if p['to_check'])}, "
        f"French posts that are not rescues: {len(result.gaps)}"
    )
    print(f"written to {out}")
    return 0


def write(path: Path, header, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    sys.exit(main())
