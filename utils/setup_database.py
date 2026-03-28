"""
Jednym poleceniem: tworzy tabele + wypełnia danymi demo (10 firm).

  python utils/setup_database.py

Bucket (obrazki): osobno → python utils/upload_c_logos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_UTILS = Path(__file__).resolve().parent
for p in (_ROOT, _UTILS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import models  # noqa: F401, E402
from create_tables import main as create_tables_main
from seed_demo_data import run_seed


def main() -> None:
    create_tables_main()
    run_seed(truncate=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Błąd: {e}", file=sys.stderr)
        raise SystemExit(1) from e
