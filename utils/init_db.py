"""Alias: uruchamia utils/create_tables.py."""

from __future__ import annotations

import sys
from pathlib import Path

_UTILS = Path(__file__).resolve().parent
_ROOT = _UTILS.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_UTILS) not in sys.path:
    sys.path.insert(0, str(_UTILS))

from create_tables import main

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Błąd: {e}")
        raise SystemExit(1) from e
