"""Diagnose one local Sheets CSV export offline: no database, network or publication.

Usage: python3 scripts/diagnose_sheets.py --sheet Data_operations --input FILE --output-dir DIR
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from catalog.sheets import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
